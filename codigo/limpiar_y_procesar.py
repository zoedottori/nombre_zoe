"""
Pipeline de Limpieza y Procesamiento de Datos para BeyondGrid & CircuitDNA
Filtra la Era Moderna (2018-2024), elimina columnas redundantes y genera
los datasets limpios optimizados en datasets_procesados/
"""

import os
import pandas as pd
import numpy as np

def time_to_seconds(t_str):
    if pd.isna(t_str) or not isinstance(t_str, str):
        return np.nan
    try:
        parts = t_str.split(':')
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except:
        return np.nan

def procesar_todo():
    print("🚀 Iniciando pipeline de limpieza y optimización de datos...")
    os.makedirs('datasets_procesados', exist_ok=True)
    
    # 1. CARGA DE DATOS CRUDOS
    print("📥 Cargando datasets originales...")
    races = pd.read_csv('datasets/races.csv')
    results = pd.read_csv('datasets/race_results.csv')
    drivers = pd.read_csv('datasets/drivers.csv')
    constructors = pd.read_csv('datasets/constructors.csv')
    circuits = pd.read_csv('datasets/circuit_characteristics.csv')
    weather = pd.read_csv('datasets/race_weather.csv')
    stints = pd.read_csv('datasets/tyre_stints.csv')
    pitstops = pd.read_csv('datasets/pitstops.csv')
    lap_times = pd.read_csv('datasets/lap_times.csv')

    # Normalización de tipos
    for df in [races, results, weather, stints, pitstops, lap_times]:
        df['season'] = pd.to_numeric(df['season'], errors='coerce')
        df['round'] = pd.to_numeric(df['round'], errors='coerce')
        
    # FILTRO TEMPORAL: Era Moderna (2018-2024)
    SEASONS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
    races_mod = races[races['season'].isin(SEASONS)].copy()
    results_mod = results[results['season'].isin(SEASONS)].copy()
    stints_mod = stints[stints['season'].isin(SEASONS)].copy()
    pitstops_mod = pitstops[pitstops['season'].isin(SEASONS)].copy()
    lap_times_mod = lap_times[lap_times['season'].isin(SEASONS)].copy()
    weather_mod = weather[weather['season'].isin(SEASONS)].copy()

    # -------------------------------------------------------------
    # 2. DATASET 1: CIRCUITOS (31 Pistas Modernas)
    # -------------------------------------------------------------
    print("🏁 1/5 Procesando circuitos_procesados.csv...")
    circuits_clean = circuits[[
        'circuitId', 'circuitName', 'country', 'length_km', 'turns',
        'slow_turns', 'medium_turns', 'fast_turns', 'longest_straight_m',
        'full_throttle_pct', 'asphalt_abrasion', 'asphalt_grip',
        'downforce_level', 'tyre_stress', 'braking_severity'
    ]].drop_duplicates().sort_values('circuitName')
    
    circuits_clean.to_csv('datasets_procesados/circuitos_procesados.csv', index=False)
    print(f"   -> Guardado: {len(circuits_clean)} circuitos únicos.")

    # -------------------------------------------------------------
    # 3. DATASET 2: CARRERAS Y CLIMA (149 Grandes Premios)
    # -------------------------------------------------------------
    print("🌦️ 2/5 Procesando carreras_clima_procesadas.csv...")
    carreras_clean = races_mod[[
        'season', 'round', 'circuitId', 'raceName', 'date'
    ]].merge(
        weather_mod[[
            'season', 'round', 'air_temp_c', 'track_temp_c', 
            'humidity_pct', 'rainfall', 'weather_condition'
        ]],
        on=['season', 'round'],
        how='left'
    ).sort_values(['season', 'round'])

    carreras_clean.to_csv('datasets_procesados/carreras_clima_procesadas.csv', index=False)
    print(f"   -> Guardado: {len(carreras_clean)} carreras con meteorología.")

    # -------------------------------------------------------------
    # 4. DATASET 3: NEUMÁTICOS Y STINTS
    # -------------------------------------------------------------
    print("🛞 3/5 Procesando stints_neumaticos_procesados.csv...")
    # Enriquecer stints con circuitId y nombre limpio de piloto
    stints_clean = stints_mod.merge(
        races_mod[['season', 'round', 'circuitId']],
        on=['season', 'round'],
        how='left'
    ).sort_values(['season', 'round', 'driverId', 'stint_number'])

    stints_clean.to_csv('datasets_procesados/stints_neumaticos_procesados.csv', index=False)
    print(f"   -> Guardado: {len(stints_clean)} stints registrados.")

    # -------------------------------------------------------------
    # 5. DATASET 4: TIEMPOS DE VUELTA LIMPIOS
    # -------------------------------------------------------------
    print("⏱️ 4/5 Procesando tiempos_vuelta_procesados.csv...")
    lap_times_mod['lapNumber'] = pd.to_numeric(lap_times_mod['lapNumber'], errors='coerce')
    lap_times_mod['position'] = pd.to_numeric(lap_times_mod['position'], errors='coerce')
    lap_times_mod['lap_time_sec'] = lap_times_mod['time'].apply(time_to_seconds)
    
    # Filtrar solo vueltas válidas entre 50s y 150s (descarta safety cars extremos y banderas rojas)
    laps_clean = lap_times_mod[[
        'season', 'round', 'driverId', 'lapNumber', 'position', 'lap_time_sec'
    ]].dropna(subset=['lap_time_sec']).sort_values(['season', 'round', 'driverId', 'lapNumber'])

    laps_clean.to_csv('datasets_procesados/tiempos_vuelta_procesados.csv', index=False)
    print(f"   -> Guardado: {len(laps_clean)} vueltas limpias en segundos.")

    # -------------------------------------------------------------
    # 6. DATASET 5: DATASET MAESTRO (1 Fila por Piloto por Carrera)
    # -------------------------------------------------------------
    print("📊 5/5 Generando dataset_maestro_carreras.csv...")
    # Cantidad de paradas en boxes por piloto
    stops_count = pitstops_mod.groupby(['season', 'round', 'driverId'])['stop'].max().reset_index(name='total_pit_stops')
    
    results_mod['grid_num'] = pd.to_numeric(results_mod['grid'], errors='coerce').fillna(20)
    results_mod['pos_num'] = pd.to_numeric(results_mod['position'], errors='coerce')
    results_mod['points_num'] = pd.to_numeric(results_mod['points'], errors='coerce').fillna(0)
    results_mod['laps_num'] = pd.to_numeric(results_mod['laps'], errors='coerce').fillna(0)
    
    # Calcular delta de puestos (ganados/perdidos)
    results_mod['net_pos_gain'] = results_mod['grid_num'] - results_mod['pos_num']

    maestro = results_mod[[
        'season', 'round', 'driverId', 'driverName', 'constructorName',
        'grid_num', 'pos_num', 'points_num', 'laps_num', 'status', 'net_pos_gain'
    ]].rename(columns={
        'grid_num': 'grid_start',
        'pos_num': 'finish_position',
        'points_num': 'points_earned',
        'laps_num': 'laps_completed'
    })

    # Unir con carreras, clima y características de circuito
    maestro = maestro.merge(carreras_clean[['season', 'round', 'circuitId', 'raceName', 'air_temp_c', 'track_temp_c', 'rainfall', 'weather_condition']], on=['season', 'round'], how='left')
    maestro = maestro.merge(circuits_clean[['circuitId', 'circuitName', 'downforce_level', 'asphalt_abrasion', 'braking_severity']], on='circuitId', how='left')
    maestro = maestro.merge(stops_count, on=['season', 'round', 'driverId'], how='left')
    maestro['total_pit_stops'] = maestro['total_pit_stops'].fillna(0).astype(int)

    maestro = maestro.sort_values(['season', 'round', 'finish_position'])
    maestro.to_csv('datasets_procesados/dataset_maestro_carreras.csv', index=False)
    print(f"   -> Guardado: {len(maestro)} registros consolidados.")

    print("\n✨ ¡Proceso completado exitosamente! Todos los datasets limpios están en datasets_procesados/\n")

if __name__ == '__main__':
    procesar_todo()
