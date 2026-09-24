# Que modelo de clustering usar: K-means vs DBSCAN vs jerarquico, aplicado a acciones

Agrupa 48 acciones del S&P 500 por como se mueven, sin decirle al modelo su sector, y compara el resultado contra el sector oficial (GICS) con el indice de Rand ajustado (ARI): 1 = mismos grupos que el sector, 0 = lo que saldria por azar.

## Datos
| Universo | Fuente | Periodo | Sesiones |
|---|---|---|---|
| 48 acciones, 6 sectores x 8 (tecnologia, financiero, energia, salud, consumo basico, servicios publicos) | Yahoo Finance (`yfinance`), cierres ajustados | 2023-09-21 a 2026-09-18 | 751 |

El sector de cada accion esta escrito a mano en `clustering.py`. Es la referencia para evaluar, no un insumo del modelo.

## Modelos
- **K-means:** k = 6, sobre las series de rendimientos estandarizadas.
- **Jerarquico (Ward):** arbol sobre la distancia de Mantegna, sqrt(2(1 - rho)), cortado en 6 grupos.
- **DBSCAN:** distancia de Mantegna precalculada, min_samples = 3. eps por regla del vecino mas cercano (mediana de la distancia al 3er vecino) y barrido de eps en `barrido_dbscan.csv`.

Cada uno se corre con dos versiones de los datos: **crudos** (rendimientos diarios) y **residuos** (a cada accion se le resta lo que explica el promedio del universo, el factor mercado).

## Como reproducirlo
```
pip install -r requirements.txt
python clustering.py
```
Deja `resultados_clustering.csv`, `barrido_dbscan.csv` y `estabilidad_ventanas.csv`. Con los mismos datos el resultado es determinista (K-means con `random_state=0`).

## Resultados (ventana completa, ARI contra el sector)
| Datos | Modelo | ARI | Acciones sin grupo |
|---|---|---|---|
| Crudos | Jerarquico (Ward) | 0.948 | 0 |
| Crudos | K-means | 0.851 | 0 |
| Crudos | DBSCAN (eps=0.94) | 0.578 | 20 de 48 |
| Residuos | K-means | 1.000 | 0 |
| Residuos | Jerarquico (Ward) | 0.948 | 0 |
| Residuos | DBSCAN (eps=1.03) | 0.404 | 23 de 48 |

## Estabilidad: tres ventanas de un ano (rango del ARI)
| Datos | K-means | Jerarquico (Ward) | DBSCAN |
|---|---|---|---|
| Crudos | 0.571 - 0.892 | 0.715 - 0.948 | 0.427 - 0.641 |
| Residuos | 0.658 - 0.811 | 0.634 - 0.948 | 0.355 - 0.578 |

Detalle por ventana en `estabilidad_ventanas.csv`.

## Limitaciones
- K-means y jerarquico reciben k = 6 (el numero real de sectores). DBSCAN no recibe k, asi que la comparacion no es pareja.
- Un solo universo, seis sectores y ventanas de un ano (251 sesiones para 48 acciones). Los rankings pueden cambiar con otro universo.
- El sector oficial no siempre describe como cotiza una accion. Un ARI bajo no prueba que el modelo este mal.
- Quitar el factor mercado (residuos) no mejoro de forma consistente: ayudo a K-means en la ventana completa, pero no en las ventanas anuales del jerarquico.
- DBSCAN es muy sensible a eps: con eps = 0.9 deja 34 acciones sin grupo y con eps = 1.4 pone todas en uno solo (ver `barrido_dbscan.csv`).
- Es un ejercicio educativo, no una recomendacion de inversion.
