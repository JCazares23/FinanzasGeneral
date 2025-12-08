# Optimización Tradicional vs. Heurística en Portafolios de Inversión

Este proyecto realiza una comparativa técnica entre métodos de **Optimización Matemática Convexa** (Teoría Moderna de Portafolios - MPT) e **Inteligencia Artificial** (Metaheurísticas) para la asignación de activos financieros.

El objetivo es construir un portafolio de inversión óptimo seleccionando entre 20 activos del S&P 500, sujeto a restricciones de perfil de riesgo (Conservador, Moderado, Agresivo).

## 📋 Descripción del Proyecto

El problema de optimización de portafolios implica encontrar la mejor combinación de pesos para un conjunto de activos que maximice el rendimiento ajustado al riesgo (Ratio de Sharpe).

Este repositorio implementa y compara tres enfoques para resolver este problema utilizando datos históricos reales:

1.  **Muestreo Aleatorio (Monte Carlo):** Como línea base (*benchmark*) estadística.
2.  **Metaheurísticas (IA):**
    * **Algoritmos Genéticos (GA):** Evolución biológica simulada para encontrar pesos óptimos.
    * **Temple Simulado (Simulated Annealing):** Algoritmo probabilístico inspirado en la termodinámica.
3.  **Método Exacto (MPT):**
    * Uso de **Solvers Matemáticos** (`scipy.optimize`) para calcular la Frontera Eficiente de Markowitz.

## 🚀 Características

* **Perfilamiento Interactivo:** Cuestionario de consola para definir las restricciones de riesgo del usuario.
* **Datos Reales:** Descarga automática de precios ajustados usando la API de Yahoo Finance (`yfinance`).
* **Múltiples Estrategias:** Comparación directa entre Max Sharpe, Mínima Volatilidad y Pesos Iguales.
* **Backtesting:** Simulación histórica del rendimiento acumulado para validar las estrategias.
* **Visualización:** Gráficos de la Frontera Eficiente, Convergencia del Algoritmo Genético y Distribución de Activos.

## 🛠️ Estructura del Repositorio

```text
optimizacion_tradicional_vs_heuristica_en_portafolios/
│
├── data/                   # Datos descargados (CSV) de precios y mercado
├── notebooks/
│   ├── metodo_MPT.ipynb    # Implementación matemática (Markowitz/Scipy)
│   └── metodo_heuristico.ipynb      # Implementación heurística (Algoritmos Genéticos)
│
├── src/
│   └── optimizacion_portafolios.py  # Script principal con toda la lógica y clases
│
├── assets/                 # Imágenes para el cuestionario de perfilamiento
├── requirements.txt        # Dependencias del proyecto
└── README.md               # Documentación del proyecto