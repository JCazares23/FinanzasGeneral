# Que modelo de forecasting usar: comparacion con RMSE

Compara promedio movil, ARIMA, Prophet y XGBoost, mas un modelo naive de referencia, sobre dos series con naturaleza distinta.

## Series
| Serie | Fuente | Periodo | Horizonte | Origenes | Puntos evaluados |
|---|---|---|---|---|---|
| S&P 500 diario (cierre) | Yahoo Finance (`yfinance`) | 2021-09-20 a 2026-09-18 | 21 dias habiles | 6 | 126 |
| Ventas minoristas y de servicios de alimentos de EE. UU., mensual, sin ajuste estacional | FRED, serie `RSXFSN` | 2010-01 a 2026-08 | 12 meses | 3 | 36 |

## Que es el modelo naive (la referencia)
El modelo **naive** es el pronostico mas simple posible: repetir el ultimo valor observado. Si hoy el S&P 500 cerro en X, el pronostico para todos los dias siguientes es X. No aprende nada y no tiene parametros.

Sirve como vara de medir. Si un modelo mas complejo no le gana, la complejidad extra no esta aportando nada. Por eso todos los modelos se comparan contra el en la columna `vs_naive_%` del resultado (negativo = mejor que naive, positivo = peor).

En series con estacionalidad se usa **seasonal naive**: el pronostico de cada mes es el valor del mismo mes del ano anterior. Es el mismo modelo adaptado a la estacionalidad, no otro distinto.

En `resultados_rmse.csv` aparece como `Naive (referencia)` en la serie diaria y `Seasonal naive (referencia)` en la mensual.

## Metodologia
Evaluacion walk-forward: se entrena con el pasado, se pronostica un horizonte fijo y se repite moviendo el origen hacia adelante. El RMSE se calcula sobre todos los puntos pronosticados, en unidades originales de cada serie.

- **Naive (referencia):** ultimo valor en la serie diaria. En la mensual, seasonal naive (mismo mes del ano anterior).
- **Promedio movil:** promedio de las ultimas 20 observaciones (diario) o 12 (mensual), como pronostico plano.
- **ARIMA:** ARIMA(1,1,1) en la serie diaria y SARIMA(1,1,1)(0,1,1,12) en la mensual. Ordenes fijos, sin busqueda.
- **Prophet:** configuracion por defecto con estacionalidad anual (sin semanal ni diaria).
- **XGBoost:** 200 arboles, profundidad 3. Modela el cambio logaritmico contra s periodos atras (retorno diario o variacion anual) con 3 rezagos y el mes como variable. Pronostico recursivo.

## Como reproducirlo
```
pip install -r requirements.txt
python forecasting.py
```
O abre `libreta_forecasting.ipynb`. Los resultados quedan en `resultados_rmse.csv`. Con los mismos datos, dos corridas dan resultados identicos.

## Resultados
Ver `resultados_rmse.csv`. La columna `vs_naive_%` compara cada modelo contra el modelo naive de su serie.

## Limitaciones
- Pocos origenes de evaluacion, sobre todo en la serie mensual (36 puntos). Los rankings pueden cambiar con otra ventana.
- Ordenes de ARIMA e hiperparametros de XGBoost fijos, sin optimizar. Prophet va con configuracion por defecto. Un ajuste fino podria cambiar el orden.
- El promedio movil como pronostico plano no captura estacionalidad por construccion.
- Los datos de Yahoo Finance pueden cambiar ligeramente si se descargan en otra fecha.
- Es un ejercicio educativo, no una recomendacion de inversion.
