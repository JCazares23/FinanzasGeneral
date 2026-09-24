# %% [markdown]
# # Que modelo de clustering usar: K-means vs DBSCAN vs jerarquico, aplicado a acciones
# Se agrupan 48 acciones del S&P 500 (6 sectores x 8) por como se mueven, sin decirle al modelo su sector.
# Despues se compara el resultado contra el sector oficial con el indice de Rand ajustado (ARI):
# 1.0 = mismos grupos que el sector, 0 = lo que saldria por azar.
# Se prueba en dos versiones de los datos: rendimientos crudos y residuos (sin el factor mercado).

# %%
import warnings

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

warnings.filterwarnings("ignore")

# %% [markdown]
# ## 1. Datos
# Sector de cada emisora segun GICS, escrito a mano: es la referencia contra la que se compara, no un insumo del modelo.

# %%
SECTORES = {
    "Tecnologia": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "ADBE", "CRM", "CSCO"],
    "Financiero": ["JPM", "BAC", "WFC", "GS", "MS", "C", "AXP", "BLK"],
    "Energia": ["XOM", "CVX", "COP", "EOG", "SLB", "OXY", "PSX", "MPC"],
    "Salud": ["JNJ", "PFE", "MRK", "ABBV", "LLY", "UNH", "TMO", "ABT"],
    "Consumo basico": ["PG", "KO", "PEP", "WMT", "COST", "CL", "MDLZ", "PM"],
    "Servicios publicos": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL"],
}
etiqueta = {t: s for s, ts in SECTORES.items() for t in ts}
tickers = list(etiqueta)

px = yf.download(tickers, start="2023-09-20", end="2026-09-19", auto_adjust=True, progress=False)["Close"]
px = px[tickers].dropna(axis=1, how="any")
rend = np.log(px).diff().dropna()
verdad = pd.Categorical([etiqueta[t] for t in rend.columns]).codes
K = len(SECTORES)
print(rend.shape[1], "acciones,", rend.shape[0], "sesiones,", rend.index[0].date(), "->", rend.index[-1].date())

# %% [markdown]
# ## 2. Dos versiones de los datos
# **Crudos:** rendimientos diarios estandarizados.
# **Residuos:** a cada accion se le resta lo que explica el mercado (el promedio de todas). Sin este paso, casi todo
# correlaciona con todo y el primer grupo que sale es "el mercado".

# %%
def residuos(r):
    m = r.mean(axis=1)
    out = {}
    for c in r.columns:
        beta, alfa = np.polyfit(m, r[c], 1)
        out[c] = r[c] - (alfa + beta * m)
    return pd.DataFrame(out)


def estandarizar(r):
    return (r - r.mean()) / r.std()


def distancia_mantegna(z):
    rho = np.clip(np.corrcoef(z.T.values), -1, 1)
    d = np.sqrt(2 * (1 - rho))
    np.fill_diagonal(d, 0)
    return d


# %% [markdown]
# ## 3. Los tres modelos
# - **K-means:** k = 6, sobre las series estandarizadas.
# - **Jerarquico (Ward):** corta el arbol en 6 grupos, sobre la distancia sqrt(2(1-rho)) de Mantegna.
# - **DBSCAN:** no pide k, pide un radio (eps). Se reporta con eps fijo por regla del vecino mas cercano y se barre eps.

# %%
def kmeans(z, k=K):
    return KMeans(n_clusters=k, n_init=20, random_state=0).fit_predict(z.T.values)


def jerarquico(z, k=K):
    d = distancia_mantegna(z)
    return fcluster(linkage(squareform(d, checks=False), "ward"), k, "maxclust")


def dbscan(z, eps, min_samples=3):
    d = distancia_mantegna(z)
    return DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed").fit_predict(d)


def eps_regla(z, k=3):
    d = distancia_mantegna(z)
    return float(np.median(np.sort(d, axis=1)[:, k]))


def evaluar(etiquetas, z):
    n_ruido = int((etiquetas == -1).sum())
    n_grupos = len(set(etiquetas)) - (1 if n_ruido else 0)
    ari = adjusted_rand_score(verdad, etiquetas)
    if n_grupos >= 2 and len(set(etiquetas)) < len(etiquetas):
        sil = silhouette_score(distancia_mantegna(z), etiquetas, metric="precomputed")
    else:
        sil = np.nan
    return dict(grupos=n_grupos, ruido=n_ruido, ARI_vs_sector=round(ari, 3), silueta=round(sil, 3))


# %% [markdown]
# ## 4. Resultado sobre toda la ventana

# %%
versiones = {"Crudos": estandarizar(rend), "Residuos": estandarizar(residuos(rend))}
filas = []
for vname, z in versiones.items():
    eps = eps_regla(z)
    for mname, et in [("K-means", kmeans(z)), ("Jerarquico (Ward)", jerarquico(z)), (f"DBSCAN (eps={eps:.2f})", dbscan(z, eps))]:
        filas.append(dict(datos=vname, modelo=mname, **evaluar(et, z)))
res = pd.DataFrame(filas)
print(res.to_string(index=False))

# %% [markdown]
# ## 5. Sensibilidad: DBSCAN segun eps, y estabilidad por ventana de un ano
# DBSCAN cambia mucho con eps. Y cualquier modelo puede cambiar de una ventana a otra:
# se repite el ejercicio en tres ventanas de un ano y se reporta el rango del ARI.

# %%
z = versiones["Residuos"]
barrido = []
for eps in np.round(np.arange(0.9, 1.5, 0.1), 2):
    et = dbscan(z, eps)
    barrido.append(dict(eps=eps, **evaluar(et, z)))
barrido = pd.DataFrame(barrido)
print(barrido.to_string(index=False))

ventanas = [(rend.index[0], rend.index[251]), (rend.index[252], rend.index[503]), (rend.index[504], rend.index[-1])]
est = []
for a, b in ventanas:
    r = rend.loc[a:b]
    zc, zr = estandarizar(r), estandarizar(residuos(r))
    for vname, zz in [("Crudos", zc), ("Residuos", zr)]:
        est.append(dict(ventana=f"{a.date()} a {b.date()}", datos=vname,
                        **{"K-means": adjusted_rand_score(verdad, kmeans(zz)),
                           "Jerarquico (Ward)": adjusted_rand_score(verdad, jerarquico(zz)),
                           "DBSCAN": adjusted_rand_score(verdad, dbscan(zz, eps_regla(zz)))}))
est = pd.DataFrame(est)
print(est.round(3).to_string(index=False))
resumen = est.groupby("datos")[["K-means", "Jerarquico (Ward)", "DBSCAN"]].agg(["min", "max"]).round(3)
print(resumen)

# %% [markdown]
# ## 6. Guardar resultados

# %%
res.to_csv("resultados_clustering.csv", index=False)
barrido.to_csv("barrido_dbscan.csv", index=False)
est.round(3).to_csv("estabilidad_ventanas.csv", index=False)
