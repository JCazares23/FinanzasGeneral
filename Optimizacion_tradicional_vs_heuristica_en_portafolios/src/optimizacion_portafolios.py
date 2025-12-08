"""
Modulo de Optimizacion de Portafolios
Optimizacion de Carteras mediante Metaheuristicas GA y SA
"""

import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys
from IPython.display import display, Image
import random

# Directorio de datos
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# CONFIGURACION Y CONSTANTES
# ============================================================================

TICKERS = [
    'NVDA', 'MSFT', 'AAPL', 'GOOGL', 'META', 'TSLA', 'AVGO', 'ORCL',  # Tecnologia
    'WMT', 'COST', 'PG', 'KO',                                      # Consumo
    'JPM', 'V', 'MA', 'BRK-B',                                      # Financiero
    'LLY', 'JNJ', 'UNH', 'ABBV'                                     # Salud
]

SECTORES = {
    'Tecnologia': ['NVDA', 'MSFT', 'AAPL', 'GOOGL', 'META', 'TSLA', 'AVGO', 'ORCL'],
    'Consumo': ['WMT', 'COST', 'PG', 'KO'],
    'Financiero': ['JPM', 'V', 'MA', 'BRK-B'],
    'Salud': ['LLY', 'JNJ', 'UNH', 'ABBV']
}

BENCHMARK = '^GSPC'  # S&P 500
RF_TICKER = '^TNX'   # Treasury 10Y

PERFILES = {
    'Conservador': {
        'volatilidad_max': 0.142,
        'peso_sector_max': 0.20,
        'peso_activo_max': 0.35,
        'aversion_riesgo': 6.0,
        'retorno_minimo': 0.1,
        'descripcion': 'Prioriza estabilidad sobre rendimiento'
    },
    'Moderado': {
        'volatilidad_max': 0.25,
        'peso_sector_max': 0.50,
        'peso_activo_max': 0.30,
        'aversion_riesgo': 2.0,
        'retorno_minimo': 0.14,
        'descripcion': 'Balance entre riesgo y rendimiento'
    },
    'Agresivo': {
        'volatilidad_max': 0.45,
        'peso_sector_max': 0.70,
        'peso_activo_max': 0.60,
        'aversion_riesgo': 0.5,
        'retorno_minimo': 0.20,
        'descripcion': 'Maximiza rendimiento aceptando alto riesgo'
    }
}

# ============================================================================
# GESTION DE DATOS
# ============================================================================

def descargar_datos_historicos(tickers=TICKERS, benchmark=BENCHMARK,risk_free_ticker=RF_TICKER, years=10, data_dir=DATA_DIR):
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    print(f"Descargando datos historicos de {years} anos...")
    
    try:
        data = yf.download(tickers, start=start_date, end=end_date,progress=True, auto_adjust=True)
        
        if isinstance(data.columns, pd.MultiIndex):
            if 'Close' in data.columns.get_level_values(0):
                precios = data['Close']
            else:
                precios = data
        else:
            precios = data['Close'] if 'Close' in data.columns else data

        tickers_disponibles = [t for t in tickers if t in precios.columns]
        precios = precios[tickers_disponibles]
        
    except Exception as e:
        print(f"Error descargando tickers: {e}")
        return None

    mercado_data = yf.download(benchmark, start=start_date, end=end_date,progress=False, auto_adjust=True)
    mercado = mercado_data['Close'] if 'Close' in mercado_data.columns else mercado_data
    
    rf_data = yf.download(risk_free_ticker, start=start_date, end=end_date,progress=False, auto_adjust=False)
    
    if 'Close' in rf_data.columns:
        tasa_libre_riesgo = rf_data['Close']
    else:
        tasa_libre_riesgo = rf_data
        
    precios.to_csv(data_dir / 'precios_historicos.csv')
    mercado.to_csv(data_dir / 'mercado_sp500.csv')
    tasa_libre_riesgo.to_csv(data_dir / 'tasa_libre_riesgo.csv')
    
    return {'precios': precios, 'mercado': mercado, 'tasa_libre_riesgo': tasa_libre_riesgo}


def cargar_datos_historicos(data_dir=None):
    if data_dir is None:
        data_dir = DATA_DIR
    else:
        data_dir = Path(data_dir)

    if not (data_dir / 'precios_historicos.csv').exists():
        raise FileNotFoundError("No existen archivos CSV en el directorio data.")

    precios = pd.read_csv(data_dir / 'precios_historicos.csv', index_col=0, parse_dates=True)
    mercado = pd.read_csv(data_dir / 'mercado_sp500.csv', index_col=0, parse_dates=True)
    tasa_libre_riesgo = pd.read_csv(data_dir / 'tasa_libre_riesgo.csv', index_col=0, parse_dates=True)
    
    if isinstance(mercado, pd.DataFrame): mercado = mercado.iloc[:, 0]
    if isinstance(tasa_libre_riesgo, pd.DataFrame): tasa_libre_riesgo = tasa_libre_riesgo.iloc[:, 0]
    
    return {'precios': precios, 'mercado': mercado, 'tasa_libre_riesgo': tasa_libre_riesgo}

# ============================================================================
# CALCULOS FINANCIEROS
# ============================================================================

def calcular_rendimientos_diarios(precios):
    return np.log(precios / precios.shift(1)).dropna()

def calcular_matriz_covarianza(rendimientos, anualizar=True):
    cov = rendimientos.cov()
    return cov * 252 if anualizar else cov

def calcular_rendimientos_esperados_historicos(rendimientos_diarios):
    return rendimientos_diarios.mean() * 252

def calcular_betas(rendimientos, rendimientos_mercado):
    # Alinear índices
    common_index = rendimientos.index.intersection(rendimientos_mercado.index)
    r_aligned = rendimientos.loc[common_index]
    rm_aligned = rendimientos_mercado.loc[common_index].squeeze()  # <- clave
    
    # Varianza del mercado
    var_mercado = rm_aligned.var()
    if isinstance(var_mercado, (pd.Series, np.ndarray)):
        if hasattr(var_mercado, 'item'):
            var_mercado = var_mercado.item()
        else:
            var_mercado = float(var_mercado)
    
    # Caso degenerado
    if var_mercado == 0:
        return pd.Series(1, index=rendimientos.columns)
    
    # Calcular betas
    betas = {}
    for ticker in r_aligned.columns:
        cov = r_aligned[ticker].cov(rm_aligned)
        betas[ticker] = cov / var_mercado
    
    return pd.Series(betas)


def calcular_rendimientos_esperados_capm(betas, rf, rm):
    prima_riesgo = rm - rf
    return rf + betas * prima_riesgo

def calcular_metricas_cartera(pesos, rendimientos_esperados, matriz_covarianza,tasa_libre_riesgo, rendimientos_diarios_np=None):
    rendimiento = np.dot(pesos, rendimientos_esperados)
    varianza = np.dot(pesos, np.dot(matriz_covarianza, pesos))
    volatilidad = np.sqrt(varianza)
    
    sharpe = (rendimiento - tasa_libre_riesgo) / volatilidad if volatilidad > 0 else 0
    
    sortino = 0.0
    if rendimientos_diarios_np is not None:
        retornos_cartera_diarios = rendimientos_diarios_np.dot(pesos)
        rf_diario = tasa_libre_riesgo / 252
        downside_returns = retornos_cartera_diarios - rf_diario
        downside_returns = downside_returns[downside_returns < 0]
        
        if len(downside_returns) > 0:
            downside_deviation = np.sqrt(np.mean(downside_returns**2)) * np.sqrt(252)
            if downside_deviation > 0:
                sortino = (rendimiento - tasa_libre_riesgo) / downside_deviation
        else:
            sortino = 5.0
    
    return {
        'rendimiento': rendimiento, 'volatilidad': volatilidad, 'varianza': varianza,
        'sharpe': sharpe, 'sortino': sortino
    }

# ============================================================================
# RESTRICCIONES Y FITNESS
# ============================================================================

def verificar_restricciones(pesos, matriz_covarianza, perfil='Moderado', rendimiento_actual=0):
    if isinstance(pesos, np.ndarray):
        pesos = pd.Series(pesos, index=matriz_covarianza.columns)
    
    restricciones = PERFILES[perfil]
    violaciones = {}
    
    vol = np.sqrt(np.dot(pesos, np.dot(matriz_covarianza, pesos)))
    if vol > restricciones['volatilidad_max']:
        violaciones['volatilidad'] = vol - restricciones['volatilidad_max']
    
    max_w = pesos.max()
    if max_w > restricciones['peso_activo_max']:
        violaciones['peso_activo'] = max_w - restricciones['peso_activo_max']
    
    tech_tickers = [t for t in SECTORES['Tecnologia'] if t in pesos.index]
    w_tech = pesos[tech_tickers].sum()
    if w_tech > restricciones['peso_sector_max']:
        violaciones['peso_sector'] = w_tech - restricciones['peso_sector_max']
    
    retorno_min = restricciones.get('retorno_minimo', 0)
    if rendimiento_actual < retorno_min:
        violaciones['retorno_insuficiente'] = (retorno_min - rendimiento_actual) * 2.0
    
    return violaciones

def calcular_fitness(pesos, rendimientos_esperados, matriz_covarianza,tasa_libre_riesgo, perfil='Moderado',rendimientos_diarios_np=None, factor_penalizacion=1000):
    m = calcular_metricas_cartera(pesos, rendimientos_esperados, matriz_covarianza,tasa_libre_riesgo, rendimientos_diarios_np)
    violaciones = verificar_restricciones(pesos, matriz_covarianza, perfil, m['rendimiento'])
    penalizacion = sum(v * factor_penalizacion for v in violaciones.values())
    
    fitness = 0.0
    if perfil == 'Conservador':
        aversion = PERFILES[perfil]['aversion_riesgo']
        fitness = (m['rendimiento'] - (aversion * m['varianza'])) - penalizacion
    elif perfil == 'Agresivo':
        fitness = (m['rendimiento'] * 2.0) + (m['sortino'] * 0.1) - penalizacion
    else:
        fitness = m['sharpe'] - penalizacion
    
    return fitness, m, violaciones

# ============================================================================
# GENERADORES DE SOLUCIONES
# ============================================================================

def generar_pesos_aleatorios(n):
    w = np.random.random(n)
    return w / w.sum()

def generar_semilla_concentrada(n_activos, indices_top):
    w = np.zeros(n_activos)
    pesos_top = np.random.random(len(indices_top))
    w[indices_top] = pesos_top
    w = w + (np.random.random(n_activos) * 0.05)
    return w / w.sum()

# ============================================================================
# ALGORITMOS DE OPTIMIZACION
# ============================================================================

def muestreo_aleatorio(n_muestras, tickers, rendimientos_esp, matriz_cov, rf,rendimientos_diarios, perfil='Moderado'):
    resultados = []
    n_activos = len(tickers)
    rend_diarios_np = rendimientos_diarios[tickers].values if rendimientos_diarios is not None else None
    
    print(f"Generando {n_muestras} carteras aleatorias (Perfil: {perfil})...")
    
    for _ in range(n_muestras):
        w = generar_pesos_aleatorios(n_activos)
        fit, met, viol = calcular_fitness(w, rendimientos_esp, matriz_cov, rf, 
                                          perfil, rend_diarios_np)
        resultados.append({
            'pesos': w, 'fitness': fit,
            'rendimiento': met['rendimiento'], 'volatilidad': met['volatilidad'],
            'sharpe': met['sharpe'], 'violaciones': viol
        })
    
    df = pd.DataFrame(resultados)
    idx_mejor = df['fitness'].idxmax()
    return df.loc[idx_mejor].to_dict(), df

def algoritmo_genetico(tickers, rendimientos_esp, matriz_cov, rf, rendimientos_diarios,perfil='Moderado', pob_size=200, generaciones=300, elitismo=0.1):
    """
    Retorna: (mejor_resultado, historial_fitness)
    """
    n_activos = len(tickers)
    n_elite = int(pob_size * elitismo)
    rend_diarios_np = rendimientos_diarios[tickers].values if rendimientos_diarios is not None else None
    indices_top_rendimiento = np.argsort(rendimientos_esp.values)[-5:]
    
    poblacion = []
    for _ in range(pob_size):
        if np.random.random() < 0.3:
            poblacion.append(generar_semilla_concentrada(n_activos, indices_top_rendimiento))
        else:
            poblacion.append(generar_pesos_aleatorios(n_activos))
    poblacion = np.array(poblacion)
    
    historial_fitness = []
    
    print(f"GA iniciado (Perfil: {perfil}). Generaciones: {generaciones}")
    
    for gen in range(generaciones):
        fitness_scores = np.array([
            calcular_fitness(ind, rendimientos_esp, matriz_cov, rf, perfil, rend_diarios_np)[0]
            for ind in poblacion
        ])

        mejor_fit_gen = fitness_scores.max()
        historial_fitness.append(mejor_fit_gen)
        
        if (gen + 1) % 20 == 0:
            print(f"  Gen {gen + 1}/{generaciones} - Mejor Fit: {mejor_fit_gen:.4f}")
        
        indices_ordenados = np.argsort(fitness_scores)
        elite = poblacion[indices_ordenados[-n_elite:]]
        nueva_poblacion = list(elite)
        
        while len(nueva_poblacion) < pob_size:
            idx = np.random.choice(pob_size, size=3, replace=False)
            p1 = poblacion[idx[np.argmax(fitness_scores[idx])]]
            idx = np.random.choice(pob_size, size=3, replace=False)
            p2 = poblacion[idx[np.argmax(fitness_scores[idx])]]
            
            corte = np.random.randint(1, n_activos - 1)
            hijo = np.concatenate((p1[:corte], p2[corte:]))
            hijo /= hijo.sum()
            
            if np.random.random() < 0.15:
                idx_m = np.random.randint(0, n_activos)
                hijo[idx_m] *= np.random.uniform(0.5, 1.5)
                hijo /= hijo.sum()
            
            nueva_poblacion.append(hijo)
        poblacion = np.array(nueva_poblacion)
    
    best_fit = -np.inf
    best_res = None
    for ind in poblacion:
        fit, met, viol = calcular_fitness(ind, rendimientos_esp, matriz_cov, rf, perfil, rend_diarios_np)
        if fit > best_fit:
            best_fit = fit
            best_res = {
                'pesos': ind, 'fitness': fit,
                'rendimiento': met['rendimiento'], 'volatilidad': met['volatilidad'],
                'sharpe': met['sharpe'], 'violaciones': viol
            }
            
    return best_res, historial_fitness

def temple_simulado(tickers, rendimientos_esp, matriz_cov, rf, rendimientos_diarios,perfil='Moderado', t_inicial=1000, t_minima=0.01, alpha=0.95):
    """
    Retorna: (mejor_resultado, historial_fitness)
    """
    n_activos = len(tickers)
    rend_diarios_np = rendimientos_diarios[tickers].values if rendimientos_diarios is not None else None
    
    actual_w = generar_pesos_aleatorios(n_activos)
    actual_fit, actual_met, actual_viol = calcular_fitness(actual_w, rendimientos_esp, matriz_cov, rf, perfil, rend_diarios_np)
    
    mejor_w = actual_w.copy()
    mejor_fit = actual_fit
    mejor_met = actual_met
    mejor_viol = actual_viol
    
    historial_fitness = []
    temp = t_inicial
    
    print(f"SA iniciado (Perfil: {perfil}).")
    
    while temp > t_minima:
        historial_fitness.append(mejor_fit)
        
        vecino_w = actual_w.copy()
        i, j = np.random.choice(n_activos, 2, replace=False)
        transfer = np.random.uniform(0.01, 0.05)
        vecino_w[i] = max(0, vecino_w[i] - transfer)
        vecino_w[j] = vecino_w[j] + transfer
        vecino_w /= vecino_w.sum()
        
        vecino_fit, _, _ = calcular_fitness(vecino_w, rendimientos_esp, matriz_cov, rf, perfil, rend_diarios_np)
        
        delta = vecino_fit - actual_fit
        if delta > 0 or np.random.random() < np.exp(delta / temp):
            actual_w = vecino_w
            actual_fit = vecino_fit
            
            if actual_fit > mejor_fit:
                _, mejor_met, mejor_viol = calcular_fitness(actual_w, rendimientos_esp, matriz_cov, rf, perfil, rend_diarios_np)
                mejor_w = actual_w.copy()
                mejor_fit = actual_fit
                mejor_met = mejor_met
                mejor_viol = mejor_viol
        
        temp *= alpha
        
    return {
        'pesos': mejor_w, 'fitness': mejor_fit,
        'rendimiento': mejor_met['rendimiento'], 'volatilidad': mejor_met['volatilidad'],
        'sharpe': mejor_met['sharpe'], 'violaciones': mejor_viol
    }, historial_fitness

def imprimir_analisis(cartera, tickers, nombre, perfil):
    print(f"\n--- {nombre} ({perfil}) ---")
    print(f"Rendimiento: {cartera['rendimiento']*100:.2f}%")
    print(f"Volatilidad: {cartera['volatilidad']*100:.2f}%")
    print(f"Sharpe: {cartera['sharpe']:.4f}")
    if cartera['violaciones']:
        print(f"VIOLACIONES: {list(cartera['violaciones'].keys())}")
    else:
        print("Restricciones: CUMPLIDAS")

# ============================================================================
# CUESTIONARIO
# ============================================================================

def ejecutar_cuestionario_perfil():
    """
    Ejecuta un cuestionario interactivo para determinar el perfil de riesgo.
    """
    print("\n" + "="*60)
    print("CUESTIONARIO DE PERFILAMIENTO DE INVERSIONISTA")
    print("="*60)
    print("Responder ingresando el NUMERO de la opcion (1, 2 o 3).\n")

    puntaje_total = 0
    assets_dir = Path(__file__).resolve().parents[1] / 'assets'

    banco_preguntas = [
        {
            "pregunta": "1. Horizonte de inversion: ¿Cuanto tiempo planea mantener sus inversiones?",
            "opciones": [
                {"texto": "Menos de 1 ano", "puntos": 1},
                {"texto": "Entre 1 y 5 anos", "puntos": 2},
                {"texto": "Mas de 5 anos", "puntos": 3}
            ]
        },
        {
            "pregunta": "2. Reaccion ante perdidas: Si su portafolio pierde un 15% en un mes, ¿que haria?",
            "opciones": [
                {"texto": "Vender inmediatamente para evitar mas perdidas", "puntos": 1},
                {"texto": "Mantener la inversion esperando recuperacion", "puntos": 2},
                {"texto": "Comprar mas porque ve una oportunidad", "puntos": 3}
            ]
        },
        {
            "pregunta": "3. Experiencia previa: ¿Cual es su nivel de experiencia en inversiones?",
            "opciones": [
                {"texto": "Ninguna o muy basica (cuentas de ahorro)", "puntos": 1},
                {"texto": "Intermedia (fondos, CETES, ETFs)", "puntos": 2},
                {"texto": "Avanzada (acciones, derivados, cripto)", "puntos": 3}
            ]
        },
        {
            "pregunta": "4. Preferencia: ¿Que es mas importante para usted?",
            "opciones": [
                {"texto": "Seguridad y estabilidad del capital", "puntos": 1},
                {"texto": "Balance entre seguridad y crecimiento", "puntos": 2},
                {"texto": "Maximo crecimiento aunque implique alta volatilidad", "puntos": 3}
            ]
        }
    ]

    for i, item in enumerate(banco_preguntas):
        print(f"\n{item['pregunta']}")
        
        opciones_mezcladas = item['opciones'].copy()
        random.shuffle(opciones_mezcladas)
        
        for idx, opcion in enumerate(opciones_mezcladas, 1):
            print(f"   [{idx}] {opcion['texto']}")
            
        while True:
            try:
                seleccion = int(input("   Su respuesta (1-3): "))
                if 1 <= seleccion <= 3:
                    puntos_ganados = opciones_mezcladas[seleccion - 1]['puntos']
                    puntaje_total += puntos_ganados
                    break
                else:
                    print("   Por favor ingrese 1, 2 o 3.")
            except ValueError:
                print("   Entrada invalida. Ingrese un numero.")
        print("-" * 30)

    print("\n5. Ejercicio Visual: Observe los siguientes escenarios.")
    print("   Se mostraran 3 graficos. ¿Con cual se siente mas comodo?")

    opciones_visuales = [
        {"archivo": "escenario_a.png", "desc": "Escenario A", "puntos": 1},
        {"archivo": "escenario_b.png", "desc": "Escenario B", "puntos": 2},
        {"archivo": "escenario_c.png", "desc": "Escenario C", "puntos": 3}
    ]
    
    random.shuffle(opciones_visuales)
    
    try:
        for idx, op in enumerate(opciones_visuales, 1):
            display(Image(filename=assets_dir / op['archivo'], width=400))
            print(f"   [{idx}] {op['desc']}")
            
    except Exception as e:
        print(f"(No se pudieron cargar las imagenes: {e})")
        print("   Lea las descripciones y elija:")
        for idx, op in enumerate(opciones_visuales, 1):
            print(f"   [{idx}] {op['desc']}")

    while True:
        try:
            seleccion = int(input("\n   Su respuesta (1-3): "))
            if 1 <= seleccion <= 3:
                puntaje_total += opciones_visuales[seleccion - 1]['puntos']
                break
            print("   Por favor ingrese 1, 2 o 3.")
        except ValueError:
             print("   Entrada invalida.")

    print("\n" + "="*60)
    perfil = ""
    if puntaje_total <= 7:
        perfil = 'Conservador'
    elif puntaje_total <= 11:
        perfil = 'Moderado'
    else:
        perfil = 'Agresivo'
        
    print(f"PUNTAJE TOTAL: {puntaje_total}/15")
    print(f"PERFIL DETERMINADO: {perfil.upper()}")
    print("="*60 + "\n")
    
    return perfil

# ============================================================================
# MAIN
# ============================================================================

def main():
    PERFIL = 'Conservador' 
    try:
        datos = cargar_datos_historicos()
    except FileNotFoundError:
        datos = descargar_datos_historicos(years=10)
        if datos is None: return

    precios = datos['precios'][TICKERS]
    mercado = datos['mercado']
    rf_series = datos['tasa_libre_riesgo']
    
    rf_mean = rf_series.mean()
    rf_val = float(rf_mean.item()) if isinstance(rf_mean, (pd.Series, np.ndarray)) else float(rf_mean)
    if rf_val > 1: rf_val /= 100
    
    r_diarios = calcular_rendimientos_diarios(precios)
    r_mercado = calcular_rendimientos_diarios(mercado)
    matriz_cov = calcular_matriz_covarianza(r_diarios)
    
    if PERFIL == 'Agresivo':
        r_esp = calcular_rendimientos_esperados_historicos(r_diarios)
    else:
        betas = calcular_betas(r_diarios, r_mercado)
        rm = r_mercado.mean() * 252
        r_esp = calcular_rendimientos_esperados_capm(betas, rf_val, rm)
    
    print("\n" + "="*50)
    print(f"OPTIMIZACION DE PORTAFOLIO - PERFIL: {PERFIL}")
    print("="*50)
    
    # Aleatorio
    res_mc, _ = muestreo_aleatorio(1000, TICKERS, r_esp, matriz_cov, rf_val, r_diarios, PERFIL)
    imprimir_analisis(res_mc, TICKERS, "Monte Carlo", PERFIL)
    
    # Genetico
    res_ga, hist_ga = algoritmo_genetico(TICKERS, r_esp, matriz_cov, rf_val, r_diarios, PERFIL)
    imprimir_analisis(res_ga, TICKERS, "Algoritmo Genetico", PERFIL)
    print(f"Mejora GA: Inicio {hist_ga[0]:.4f} -> Fin {hist_ga[-1]:.4f}")
    
    # Temple Simulado
    res_sa, hist_sa = temple_simulado(TICKERS, r_esp, matriz_cov, rf_val, r_diarios, PERFIL)
    imprimir_analisis(res_sa, TICKERS, "Temple Simulado", PERFIL)
    print(f"Mejora SA: Inicio {hist_sa[0]:.4f} -> Fin {hist_sa[-1]:.4f}")
    
    print("\nEjecucion finalizada exitosamente.")

if __name__ == "__main__":
    main()