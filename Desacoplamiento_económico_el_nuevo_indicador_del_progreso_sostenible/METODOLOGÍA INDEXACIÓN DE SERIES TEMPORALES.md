# METODOLOGÍA: INDEXACIÓN DE SERIES TEMPORALES

## 1. INTRODUCCIÓN

El presente análisis comparativo requiere la evaluación simultánea de tres variables macroeconómicas con unidades de medida y magnitudes radicalmente diferentes:

- **Índice de mercado bursátil** (NAFTRAC, VTI, etc.): Medido en unidades monetarias locales o dólares estadounidenses
- **Emisiones de CO₂**: Medidas en millones de toneladas métricas (Mt)
- **Producto Interno Bruto (PIB)**: Medido en dólares estadounidenses corrientes (USD)

Dada la heterogeneidad dimensional de estas variables, la visualización y comparación directa de sus valores absolutos resulta técnicamente inviable. Para superar esta limitación metodológica, se implementó una **técnica de indexación a año base**, método estándar utilizado por organismos internacionales como el Fondo Monetario Internacional (FMI), la Organización para la Cooperación y el Desarrollo Económicos (OCDE) y el Banco Mundial.

---

## 2. FUNDAMENTO TEÓRICO

### 2.1 Definición de Indexación

La indexación es una transformación matemática que convierte una serie temporal absoluta en una serie relativa, expresando todos los valores como porcentajes relativos a un período de referencia (año base). Este método preserva las proporciones y tasas de cambio de la serie original mientras estandariza la escala de medición.

### 2.2 Formulación Matemática

Sea $X_t$ una serie temporal donde $t$ representa el tiempo (años), y sea $t_0$ el año base. El índice $I_t$ para cada período se calcula como:

$$I_t = \frac{X_t}{X_{t_0}} \times 100$$

Donde:
- $I_t$ = Índice en el año $t$
- $X_t$ = Valor observado en el año $t$
- $X_{t_0}$ = Valor observado en el año base
- $100$ = Factor de escala convencional

Por construcción, el índice en el año base siempre es igual a 100:

$$I_{t_0} = \frac{X_{t_0}}{X_{t_0}} \times 100 = 100$$

---

## 3. IMPLEMENTACIÓN EN EL ESTUDIO

### 3.1 Selección del Año Base

**Año base seleccionado:** 2004

**Justificación:**
- Disponibilidad de datos completos para las tres variables en todos los países analizados
- Período previo a la crisis financiera global de 2008, permitiendo capturar ciclos económicos completos
- Suficiente distancia temporal para observar cambios estructurales significativos
- Coincide con el inicio de reportes sistemáticos de emisiones de CO₂ en la base de datos utilizada

### 3.2 Variables Indexadas

Para cada país analizado, se generaron tres series indexadas:

#### a) **Índice del Mercado Bursátil** ($I^M_t$)

$$I^M_t = \frac{P_t}{P_{2004}} \times 100$$

Donde $P_t$ representa el precio de cierre anual del instrumento bursátil correspondiente:
- México: NAFTRAC ISHRS (índice IPC)
- Estados Unidos: VTI (Vanguard Total Stock Market ETF)
- China: FXI (iShares China Large-Cap ETF)
- [Otros según tabla de configuración]

#### b) **Índice de Emisiones de CO₂** ($I^{CO_2}_t$)

$$I^{CO_2}_t = \frac{E_t}{E_{2004}} \times 100$$

Donde $E_t$ representa las emisiones totales de CO₂ en millones de toneladas métricas en el año $t$.

**Fuente de datos:** Archivo CSV "emision-anual-co2-por-pais.csv", basado en datos de Global Carbon Project / Our World in Data.

**Transformación aplicada:**
```
Emisiones (Mt) = Emisiones (toneladas) / 1,000,000
```

#### c) **Índice del PIB** ($I^{PIB}_t$)

$$I^{PIB}_t = \frac{GDP_t}{GDP_{2004}} \times 100$$

Donde $GDP_t$ representa el Producto Interno Bruto en dólares estadounidenses corrientes en el año $t$.

**Fuente de datos:** Banco Mundial, indicador NY.GDP.MKTP.CD (PIB a precios corrientes en USD), obtenido mediante la API `pandas_datareader`.

---

## 4. PROPIEDADES MATEMÁTICAS Y VENTAJAS

### 4.1 Preservación de Proporciones

La indexación preserva las relaciones proporcionales entre períodos:

$$\frac{I_t}{I_s} = \frac{X_t/X_{t_0}}{X_s/X_{t_0}} = \frac{X_t}{X_s}$$

Esto significa que las razones entre valores indexados son idénticas a las razones entre valores absolutos.

### 4.2 Interpretación Intuitiva del Crecimiento

El cambio porcentual desde el año base se calcula directamente:

$$\text{Crecimiento desde año base} = I_t - 100$$

**Ejemplos:**
- $I_t = 150$ → Crecimiento del 50% respecto a 2004
- $I_t = 80$ → Decrecimiento del 20% respecto a 2004
- $I_t = 100$ → Sin cambio respecto a 2004

### 4.3 Comparabilidad Internacional

Al utilizar el mismo año base para todos los países, los índices se vuelven directamente comparables:

Si $I^{PIB}_{MEX,2023} = 233$ e $I^{PIB}_{USA,2023} = 180$, se puede concluir que el PIB mexicano creció 53 puntos porcentuales más que el estadounidense desde 2004 (en términos relativos al tamaño de cada economía en 2004).

### 4.4 Ventajas sobre Normalización Min-Max

Comparación con normalización 0-100 (min-max scaling):

| Característica | Indexación (Base 100) | Normalización 0-100 |
|----------------|----------------------|---------------------|
| **Interpretación** | Crecimiento % desde año base | Posición entre mínimo y máximo |
| **Comparabilidad entre países** | ✅ Sí | ❌ No |
| **Sensibilidad a outliers** | Moderada | Alta |
| **Uso en literatura económica** | Estándar | Raro |
| **Significado del valor 100** | Año base | Máximo del período |
| **Permite comparar tasas de cambio** | ✅ Sí | ❌ No |

---

## 5. MÉTRICAS DERIVADAS

A partir de las series indexadas, se calcularon métricas analíticas adicionales:

### 5.1 Intensidad de Carbono del PIB

$$IC_t = \frac{E_t}{GDP_t / 10^{12}}$$

Expresada en millones de toneladas de CO₂ por trillón de dólares (Mt/$T).

**Interpretación:** Mide cuántas emisiones genera la economía por unidad de producción. Una reducción de $IC_t$ indica mejora en eficiencia ambiental o transición hacia una economía menos intensiva en carbono.

### 5.2 Elasticidad CO₂-PIB

$$\epsilon_{CO_2, PIB} = \frac{\%\Delta CO_2}{\%\Delta PIB} = \frac{(I^{CO_2}_t - 100)}{(I^{PIB}_t - 100)}$$

Mide el cambio porcentual en emisiones por cada punto porcentual de cambio en el PIB.

**Interpretación:**
- $\epsilon > 1$: Las emisiones crecen más rápido que el PIB (acoplamiento fuerte)
- $0 < \epsilon < 1$: Desacoplamiento relativo (emisiones crecen más lento que PIB)
- $\epsilon < 0$: Desacoplamiento absoluto (emisiones bajan mientras PIB sube)

### 5.3 Correlaciones entre Variables Indexadas

Se calcularon coeficientes de correlación de Pearson entre las series indexadas:

$$r_{X,Y} = \frac{\sum_{t}(I^X_t - \bar{I}^X)(I^Y_t - \bar{I}^Y)}{\sqrt{\sum_{t}(I^X_t - \bar{I}^X)^2}\sqrt{\sum_{t}(I^Y_t - \bar{I}^Y)^2}}$$

Donde $X, Y \in \{\text{Mercado}, CO_2, PIB\}$

**Interpretación de correlaciones clave:**

- **r(Mercado, PIB) > r(Mercado, CO₂)**: El mercado bursátil sigue más la dinámica económica general que la actividad industrial (economía de servicios/financiera)
- **r(Mercado, CO₂) > r(Mercado, PIB)**: El mercado está más vinculado a sectores intensivos en emisiones (economía extractiva/industrial)
- **r(PIB, CO₂) < 0**: Desacoplamiento absoluto confirmado estadísticamente

---

## 6. CONSIDERACIONES METODOLÓGICAS

### 6.1 Supuestos del Método

1. **Linealidad temporal:** Se asume continuidad en las series anuales sin ajustes por estacionalidad (datos ya agregados anualmente)
2. **Homogeneidad de medición:** Se asume consistencia metodológica en la recopilación de datos entre años
3. **Comparabilidad monetaria:** El PIB en dólares corrientes no está ajustado por inflación (se usa deflactor implícito del año)

### 6.2 Limitaciones

1. **Efecto del año base:** La elección del año base puede influir en la percepción visual de la magnitud de cambios. Se seleccionó 2004 por disponibilidad de datos, no por representatividad económica particular.

2. **Inflación no ajustada:** El PIB en dólares corrientes incluye efectos inflacionarios. Para análisis de crecimiento real, sería preferible usar PIB en dólares constantes (NY.GDP.MKTP.KD), pero esto limitaría la comparabilidad internacional debido a diferentes años base de deflactores.

3. **Composición variable del mercado:** Los índices bursátiles cambian su composición con el tiempo (empresas que entran/salen), lo que puede afectar la continuidad de la serie.

4. **Agregación de CO₂:** Las emisiones incluyen todas las fuentes (energía, transporte, industrial, etc.), sin desagregación sectorial.

### 6.3 Validación Técnica

Para cada serie indexada se verificó:

**Propiedad de año base:**
```python
assert df['Variable_Index'].iloc[0] == 100
```

**Monotonía en el signo del cambio:**
```python
# Si X_t > X_t-1, entonces I_t > I_t-1
assert all(df['Variable'].diff().sign() == df['Variable_Index'].diff().sign())
```

**Equivalencia de cambios porcentuales:**
```python
pct_change_original = (df['Variable'].iloc[-1] / df['Variable'].iloc[0]) - 1
pct_change_indexed = (df['Variable_Index'].iloc[-1] / 100) - 1
assert abs(pct_change_original - pct_change_indexed) < 1e-10
```

---

## 7. PRECEDENTES EN LA LITERATURA

Esta metodología es consistente con prácticas estándar en:

1. **Análisis macroeconómico:** 
   - OECD Economic Outlook (índices de producción industrial base 2015=100)
   - IMF World Economic Outlook (índices de precios de commodities)

2. **Estudios de desacoplamiento ambiental:**
   - Tapio, P. (2005). "Towards a theory of decoupling." *Ecological Economics*, 52(1), 103-119.
   - OECD (2002). "Indicators to measure decoupling of environmental pressure from economic growth."

3. **Análisis de mercados financieros:**
   - Indices MSCI (base 100 en fecha de lanzamiento)
   - S&P 500 (originalmente base 10 en 1941-1943)

---

## 8. CÓDIGO DE IMPLEMENTACIÓN

### Función de Indexación
```python
def index_to_base_100(series):
    """
    Indexa una serie temporal a base 100.
    
    Parámetros:
    -----------
    series : pandas.Series
        Serie temporal con valores numéricos ordenados cronológicamente
    
    Retorna:
    --------
    pandas.Series
        Serie indexada donde el primer valor = 100
    
    Fórmula:
    --------
    I_t = (X_t / X_0) * 100
    """
    if len(series) == 0 or series.iloc[0] == 0:
        return pd.Series([100] * len(series), index=series.index)
    return (series / series.iloc[0]) * 100
```

### Aplicación a las Variables
```python
# Año base: primer año con datos completos
base_year = df_merged['Año'].iloc[0]

# Indexación de las tres variables
df_merged['Mercado_Index'] = index_to_base_100(df_merged['Mercado'])
df_merged['CO2_Index'] = index_to_base_100(df_merged['CO2_Mt'])
df_merged['PIB_Index'] = index_to_base_100(df_merged['PIB'])
```

---

## 9. INTERPRETACIÓN DE RESULTADOS

### Guía de Lectura de Índices

| Valor del Índice | Interpretación | Ejemplo |
|------------------|----------------|---------|
| $I_t = 100$ | Sin cambio respecto al año base | Economía estancada |
| $100 < I_t < 150$ | Crecimiento moderado | Economía madura desarrollada |
| $I_t \geq 150$ | Crecimiento significativo | Economía emergente en expansión |
| $I_t < 100$ | Decrecimiento | Recesión o contracción estructural |

### Análisis de Divergencias entre Variables

**Caso 1: $I^{PIB}_t > I^{CO_2}_t$**
- Desacoplamiento relativo
- La economía crece con menor intensidad de emisiones
- Transición hacia servicios o mejora en eficiencia energética

**Caso 2: $I^{Mercado}_t >> I^{PIB}_t$**
- Expansión de múltiplos bursátiles (P/E ratios)
- Posible sobrevaloración o expectativas de crecimiento futuro
- Influencia de liquidez global o flujos de capital especulativos

**Caso 3: $I^{CO_2}_t$ alcanza máximo y luego declina**
- "Peak Carbon" alcanzado
- Cambio estructural en la matriz energética
- Políticas ambientales efectivas o desindustrialización

---

## 10. CONCLUSIÓN METODOLÓGICA

La indexación a año base constituye el método más apropiado para este análisis comparativo por las siguientes razones:

1. **Rigor metodológico:** Es el estándar internacional en análisis macroeconómico
2. **Interpretabilidad:** Permite comunicar cambios porcentuales de forma directa
3. **Comparabilidad:** Facilita la comparación entre países con economías de diferentes tamaños
4. **Trazabilidad:** Los cálculos son transparentes y replicables
5. **Validación:** Preserva propiedades matemáticas esenciales de las series originales

Este enfoque permite responder la pregunta central del estudio: **¿El crecimiento del mercado bursátil está acoplado al crecimiento económico (PIB) o a la intensidad ambiental (emisiones de CO₂)?**, proporcionando evidencia cuantitativa robusta para el análisis del "trilema" entre desarrollo económico, desempeño financiero y sostenibilidad ambiental.

---

## REFERENCIAS

1. Banco Mundial (2024). *World Development Indicators*. Indicador NY.GDP.MKTP.CD.
2. Global Carbon Project (2023). *Global Carbon Budget 2023*. doi:10.18160/gcp-2023
3. OECD (2002). *Indicators to Measure Decoupling of Environmental Pressure from Economic Growth*. SG/SD(2002)1/FINAL.
4. Tapio, P. (2005). Towards a theory of decoupling: degrees of decoupling in the EU and the case of road traffic in Finland between 1970 and 2001. *Transport Policy*, 12(2), 137-151.
5. IMF (2024). *World Economic Outlook Database*. https://www.imf.org/en/Publications/WEO
6. Ritchie, H., Roser, M., & Rosado, P. (2020). CO₂ and Greenhouse Gas Emissions. *Our World in Data*. https://ourworldindata.org/co2-emissions