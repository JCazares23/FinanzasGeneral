# %% [markdown]
# # Que modelo de forecasting usar: comparacion con RMSE
# Cuatro modelos (promedio movil, ARIMA, Prophet, XGBoost) y un modelo naive de referencia,
# sobre dos series con naturaleza distinta:
# 1. S&P 500 diario (sin estacionalidad clara, casi ruido)
# 2. Ventas minoristas de EE. UU. mensuales, sin ajuste estacional (estacionalidad fuerte)
#
# Evaluacion walk-forward: se entrena con el pasado, se pronostica un horizonte fijo y se repite
# con origenes cada vez mas recientes. El RMSE se calcula sobre todos los puntos pronosticados.

# %%
import logging
import warnings

import numpy as np
import pandas as pd
import yfinance as yf
from prophet import Prophet
from statsmodels.tsa.statespace.sarimax import SARIMAX
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")
for nombre_log in ("cmdstanpy", "prophet"):
    lg = logging.getLogger(nombre_log)
    lg.addHandler(logging.NullHandler())
    lg.propagate = False
    lg.setLevel(logging.CRITICAL)

# %% [markdown]
# ## 1. Que es el modelo naive (la referencia)
# El modelo **naive** es el pronostico mas simple posible: repetir el ultimo valor observado.
# Si hoy el S&P 500 cerro en X, el pronostico para todos los dias siguientes es X.
# No aprende nada ni tiene parametros. Sirve de vara de medir: si un modelo mas complejo no le gana,
# la complejidad extra no esta aportando.
#
# En series con estacionalidad se usa la version **seasonal naive**: el pronostico de cada mes es el
# valor del mismo mes del ano anterior. Es el mismo modelo, adaptado a la estacionalidad.
# En los resultados aparece como `Naive (referencia)` en la serie diaria y `Seasonal naive (referencia)` en la mensual.
# Los demas modelos se comparan contra el en la columna `vs_naive_%` (negativo = mejor que naive).

# %% [markdown]
# ## 2. Datos

# %%
sp = yf.download("^GSPC", start="2021-09-20", end="2026-09-19", auto_adjust=True, progress=False)["Close"]
sp = sp.squeeze().dropna()
sp.index = pd.to_datetime(sp.index)

url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=RSXFSN"  # ventas minoristas y de servicios de alimentos, mensual, sin ajuste estacional
retail = pd.read_csv(url, parse_dates=[0], index_col=0).squeeze()
retail = retail[retail.index >= "2010-01-01"].astype(float)

series = {
    "S&P 500 diario": dict(y=sp, h=21, origenes=6, s=1, freq="B"),
    "Ventas minoristas EE. UU. mensual": dict(y=retail, h=12, origenes=3, s=12, freq="MS"),
}
for nombre, c in series.items():
    print(nombre, len(c["y"]), c["y"].index[0].date(), "->", c["y"].index[-1].date())


# %% [markdown]
# ## 3. Modelos
# Cada funcion recibe la serie de entrenamiento, el horizonte y la configuracion, y devuelve `h` pronosticos.

# %%
def naive(train, h, s, **_):
    """Naive: repite el ultimo valor (s=1, diario).
    Seasonal naive: repite el valor del mismo periodo del ano anterior (s=12, mensual)."""
    if s == 1:
        return np.repeat(train.iloc[-1], h)
    return train.iloc[-s:].values[:h]


def promedio_movil(train, h, s, **_):
    """Promedio de las ultimas k observaciones como pronostico plano: k=20 dias o k=12 meses."""
    k = 20 if s == 1 else 12
    return np.repeat(train.iloc[-k:].mean(), h)


def arima(train, h, s, **_):
    """ARIMA(1,1,1) diario; SARIMA(1,1,1)(0,1,1,12) mensual. Ordenes fijos, sin busqueda."""
    if s == 1:
        m = SARIMAX(train.values, order=(1, 1, 1)).fit(disp=False)
    else:
        m = SARIMAX(train.values, order=(1, 1, 1), seasonal_order=(0, 1, 1, 12)).fit(disp=False)
    return m.forecast(h)


def prophet(train, h, s, freq, **_):
    df = pd.DataFrame({"ds": train.index, "y": train.values})
    m = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=True)
    m.fit(df)
    futuro = pd.date_range(train.index[-1], periods=h + 1, freq=freq)[1:]
    return m.predict(pd.DataFrame({"ds": futuro}))["yhat"].values


def xgboost(train, h, s, freq, **_):
    """XGBoost sobre el cambio logaritmico contra s periodos atras (retorno diario o variacion anual),
    con 3 rezagos y el mes como variable. Pronostico recursivo."""
    lags = 3
    y = np.log(train.values)
    z = y[s:] - y[:-s]
    fechas = train.index[s:]
    X = np.column_stack([z[i : len(z) - lags + i] for i in range(lags)] + [fechas.month.values[lags:]])
    t = z[lags:]
    m = XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, verbosity=0).fit(X, t)
    hist = list(y)
    zs = list(z)
    futuro = pd.date_range(train.index[-1], periods=h + 1, freq=freq)[1:]
    for f in futuro:
        x = np.array(zs[-lags:] + [f.month]).reshape(1, -1)
        zh = m.predict(x)[0]
        hist.append(hist[-s] + zh)
        zs.append(zh)
    return np.exp(hist[-h:])


modelos = {
    "Naive (referencia)": naive,
    "Promedio movil": promedio_movil,
    "ARIMA": arima,
    "Prophet": prophet,
    "XGBoost": xgboost,
}


# %% [markdown]
# ## 4. Evaluacion walk-forward

# %%
filas = []
for nombre, c in series.items():
    y, h, n, s, freq = c["y"], c["h"], c["origenes"], c["s"], c["freq"]
    errores = {m: [] for m in modelos}
    for i in range(n, 0, -1):
        corte = len(y) - h * i
        train, test = y.iloc[:corte], y.iloc[corte : corte + h]
        for m, f in modelos.items():
            pred = np.asarray(f(train, len(test), s=s, freq=freq))
            errores[m].append(pred - test.values)
    for m, e in errores.items():
        e = np.concatenate(e)
        if m.startswith("Naive") and s > 1:
            m = "Seasonal naive (referencia)"
        filas.append({"serie": nombre, "modelo": m, "RMSE": np.sqrt((e**2).mean()), "puntos": len(e)})

res = pd.DataFrame(filas)
res["vs_naive_%"] = res.groupby("serie")["RMSE"].transform(lambda r: (r / r.iloc[0] - 1) * 100)
res["ranking"] = res.groupby("serie")["RMSE"].rank().astype(int)
print(res.round(2).to_string(index=False))

# %% [markdown]
# ## 5. Guardar resultados

# %%
res.round(2).to_csv("resultados_rmse.csv", index=False)
sp.rename("sp500_cierre").to_csv("sp500_diario.csv")
retail.rename("ventas_minoristas_usa").to_csv("ventas_minoristas_mensual.csv")
