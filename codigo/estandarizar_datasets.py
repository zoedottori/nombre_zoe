"""
Script de Estandarización y Formateo Riguroso de Datasets Procesados
Aplica:
1. Formateo de Tipos de Datos (numéricos nativos, float redondeados, int).
2. Normalización de Textos y Claves (snake_case universal, remoción de acentos/tildes, mayúsculas consistentes).
3. Alineación de Fechas (ISO 8601 YYYY-MM-DD).
"""

import os
import glob
import unicodedata
import pandas as pd
import numpy as np

def clean_text(text):
    """Limpia cadenas: remueve acentos/diacríticos y espacios extra."""
    if pd.isna(text) or not isinstance(text, str):
        return text
    text = text.strip()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def time_to_seconds(t_str):
    """Convierte cadenas de tiempo '1:23.456' a float en segundos."""
    if pd.isna(t_str) or not isinstance(t_str, str):
        return np.nan
    try:
        parts = t_str.strip().split(':')
        if len(parts) == 2:
            return round(float(parts[0]) * 60 + float(parts[1]), 3)
        return round(float(parts[0]), 3)
    except:
        return np.nan

def estandarizar_todo():
    print("🧹 Iniciando Estandarización y Formateo Integral de Datasets...")
    os.makedirs('datasets_procesados', exist_ok=True)
    
    # -------------------------------------------------------------------------
    # CARGA DE FUENTES BASE
    # -------------------------------------------------------------------------
    races = pd.read_csv('datasets/races.csv')
    results = pd.read_csv('datasets/race_results.csv')
    drivers = pd.read_csv('datasets/drivers.csv')
    constructors = pd.read_csv('datasets/constructors.csv')
    circuits = pd.read_csv('datasets/circuit_characteristics.csv')
    weather = pd.read_csv('datasets/race_weather.csv')
    stints = pd.read_csv('datasets/tyre_stints.csv')
    pitstops = pd.read_csv('datasets/pitstops.csv')
    lap_times = pd.read_csv('datasets/lap_times.csv')

    # Filtrar era moderna (2018-2024)
    SEASONS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
    for df in [races, results, weather, stints, pitstops, lap_times]:
        df['season'] = pd.to_numeric(df['season'], errors='coerce')
        df['round'] = pd.to_numeric(df['round'], errors='coerce')

    races_mod = races[races['season'].isin(SEASONS)].copy()
    results_mod = results[results['season'].isin(SEASONS)].copy()
    stints_mod = stints[stints['season'].isin(SEASONS)].copy()
    pitstops_mod = pitstops[pitstops['season'].isin(SEASONS)].copy()
    lap_times_mod = lap_times[lap_times['season'].isin(SEASONS)].copy()
    weather_mod = weather[weather['season'].isin(SEASONS)].copy()

    # Mapeo de nombres de pilotos y constructores sin acentos
    driver_name_map = {}
    for _, row in results_mod[['driverId', 'driverName']].drop_duplicates().iterrows():
        driver_name_map[row['driverId']] = clean_text(row['driverName'])

    # -------------------------------------------------------------------------
    # 1. CIRCUITOS PROCESADOS
    # -------------------------------------------------------------------------
    print("🏁 1/5 Estandarizando circuitos_procesados.csv...")
    c_df = circuits.copy()
    c_df['circuitId'] = c_df['circuitId'].str.lower().str.strip()
    c_df['circuitName'] = c_df['circuitName'].apply(clean_text)
    c_df['country'] = c_df['country'].apply(clean_text)
    c_df['downforce_level'] = c_df['downforce_level'].str.upper().str.strip()

    c_df = c_df.rename(columns={
        'circuitId': 'circuit_id',
        'circuitName': 'circuit_name'
    })

    # Asegurar tipos cuantitativos
    c_df['length_km'] = c_df['length_km'].astype(float).round(3)
    int_cols_circ = ['turns', 'slow_turns', 'medium_turns', 'fast_turns', 
                     'longest_straight_m', 'full_throttle_pct', 
                     'asphalt_abrasion', 'asphalt_grip', 'tyre_stress', 'braking_severity']
    for col in int_cols_circ:
        c_df[col] = c_df[col].astype(int)

    c_df = c_df.sort_values('circuit_name')
    c_df.to_csv('datasets_procesados/circuitos_procesados.csv', index=False)
    print(f"   ✓ {len(c_df)} circuitos estandarizados.")

    # -------------------------------------------------------------------------
    # 2. CARRERAS Y CLIMA PROCESADOS
    # -------------------------------------------------------------------------
    print("🌦️ 2/5 Estandarizando carreras_clima_procesadas.csv...")
    r_df = races_mod[['season', 'round', 'circuitId', 'raceName', 'date']].copy()
    r_df['circuitId'] = r_df['circuitId'].str.lower().str.strip()
    r_df['raceName'] = r_df['raceName'].apply(clean_text)
    r_df['date'] = pd.to_datetime(r_df['date']).dt.strftime('%Y-%m-%d') # ISO 8601 estricto

    w_df = weather_mod[['season', 'round', 'air_temp_c', 'track_temp_c', 'humidity_pct', 'rainfall', 'weather_condition']].copy()
    w_df['weather_condition'] = w_df['weather_condition'].apply(clean_text).str.upper()

    carreras_clean = r_df.merge(w_df, on=['season', 'round'], how='left')
    carreras_clean = carreras_clean.rename(columns={
        'circuitId': 'circuit_id',
        'raceName': 'race_name'
    })

    # Tipos de datos numéricos
    carreras_clean['season'] = carreras_clean['season'].astype(int)
    carreras_clean['round'] = carreras_clean['round'].astype(int)
    carreras_clean['air_temp_c'] = carreras_clean['air_temp_c'].astype(float).round(1)
    carreras_clean['track_temp_c'] = carreras_clean['track_temp_c'].astype(float).round(1)
    carreras_clean['humidity_pct'] = carreras_clean['humidity_pct'].astype(float).round(1)
    carreras_clean['rainfall'] = carreras_clean['rainfall'].astype(int)

    carreras_clean = carreras_clean.sort_values(['season', 'round'])
    carreras_clean.to_csv('datasets_procesados/carreras_clima_procesadas.csv', index=False)
    print(f"   ✓ {len(carreras_clean)} carreras estandarizadas.")

    # -------------------------------------------------------------------------
    # 3. STINTS Y NEUMÁTICOS PROCESADOS
    # -------------------------------------------------------------------------
    print("🛞 3/5 Estandarizando stints_neumaticos_procesados.csv...")
    s_df = stints_mod.copy()
    if 'circuitId' not in s_df.columns:
        s_df = s_df.merge(races_mod[['season', 'round', 'circuitId']], on=['season', 'round'], how='left')
    s_df['circuitId'] = s_df['circuitId'].astype(str).str.lower().str.strip()
    
    s_df['driverId'] = s_df['driverId'].str.lower().str.strip()
    s_df['driver_name'] = s_df['driverId'].map(driver_name_map).fillna(s_df['driverId'])
    s_df['constructorName'] = s_df['constructorName'].apply(clean_text)
    s_df['compound'] = s_df['compound'].str.upper().str.strip()
    
    s_df['pit_duration'] = pd.to_numeric(s_df['pit_duration'], errors='coerce').round(3)

    s_clean = s_df[[
        'season', 'round', 'circuitId', 'driverId', 'driver_name',
        'constructorName', 'stint_number', 'compound', 'lap_start',
        'lap_end', 'stint_length', 'pit_duration'
    ]].rename(columns={
        'circuitId': 'circuit_id',
        'driverId': 'driver_id',
        'constructorName': 'constructor_name',
        'pit_duration': 'pit_duration_sec'
    })

    # Tipos
    for c in ['season', 'round', 'stint_number', 'lap_start', 'lap_end', 'stint_length']:
        s_clean[c] = s_clean[c].astype(int)

    s_clean = s_clean.sort_values(['season', 'round', 'driver_id', 'stint_number'])
    s_clean.to_csv('datasets_procesados/stints_neumaticos_procesados.csv', index=False)
    print(f"   ✓ {len(s_clean)} stints estandarizados.")

    # -------------------------------------------------------------------------
    # 4. TIEMPOS DE VUELTA PROCESADOS
    # -------------------------------------------------------------------------
    print("⏱️ 4/5 Estandarizando tiempos_vuelta_procesados.csv...")
    lt_df = lap_times_mod.merge(races_mod[['season', 'round', 'circuitId']], on=['season', 'round'], how='left')
    lt_df['circuitId'] = lt_df['circuitId'].str.lower().str.strip()
    lt_df['driverId'] = lt_df['driverId'].str.lower().str.strip()
    lt_df['lapNumber'] = pd.to_numeric(lt_df['lapNumber'], errors='coerce').astype(int)
    lt_df['position'] = pd.to_numeric(lt_df['position'], errors='coerce').astype(int)
    lt_df['lap_time_sec'] = lt_df['time'].apply(time_to_seconds)

    # Filtrar vueltas válidas entre 50 y 160 segundos
    laps_clean = lt_df[[
        'season', 'round', 'circuitId', 'driverId', 'lapNumber', 'position', 'lap_time_sec'
    ]].dropna(subset=['lap_time_sec']).query('lap_time_sec >= 50 and lap_time_sec <= 160').copy()

    laps_clean = laps_clean.rename(columns={
        'circuitId': 'circuit_id',
        'driverId': 'driver_id',
        'lapNumber': 'lap_number'
    })

    laps_clean = laps_clean.sort_values(['season', 'round', 'driver_id', 'lap_number'])
    laps_clean.to_csv('datasets_procesados/tiempos_vuelta_procesados.csv', index=False)
    print(f"   ✓ {len(laps_clean)} vueltas limpias con tiempos numéricos exactos.")

    # -------------------------------------------------------------------------
    # 5. DATASET MAESTRO CONSOLIDADO
    # -------------------------------------------------------------------------
    print("📊 5/5 Generando dataset_maestro_carreras.csv estandarizado...")
    stops_count = pitstops_mod.groupby(['season', 'round', 'driverId'])['stop'].max().reset_index(name='total_pit_stops')
    stops_count['driverId'] = stops_count['driverId'].str.lower().str.strip()

    res_df = results_mod.copy()
    res_df['driverId'] = res_df['driverId'].str.lower().str.strip()
    res_df['driver_name'] = res_df['driverId'].map(driver_name_map).fillna(res_df['driverName'].apply(clean_text))
    res_df['constructorName'] = res_df['constructorName'].apply(clean_text)
    res_df['status'] = res_df['status'].apply(clean_text).str.upper()

    res_df['grid_start'] = pd.to_numeric(res_df['grid'], errors='coerce').replace(0, 20).fillna(20).astype(int)
    res_df['finish_position'] = pd.to_numeric(res_df['position'], errors='coerce').fillna(20).astype(int)
    res_df['points_earned'] = pd.to_numeric(res_df['points'], errors='coerce').fillna(0.0).round(1)
    res_df['laps_completed'] = pd.to_numeric(res_df['laps'], errors='coerce').fillna(0).astype(int)
    res_df['net_pos_gain'] = res_df['grid_start'] - res_df['finish_position']

    # Merge con carreras_clean
    maestro = res_df[[
        'season', 'round', 'driverId', 'driver_name', 'constructorName',
        'grid_start', 'finish_position', 'points_earned', 'laps_completed',
        'status', 'net_pos_gain'
    ]].merge(
        carreras_clean[[
            'season', 'round', 'date', 'circuit_id', 'race_name',
            'air_temp_c', 'track_temp_c', 'humidity_pct', 'rainfall', 'weather_condition'
        ]],
        on=['season', 'round'],
        how='left'
    )

    # Merge con circuitos_clean
    maestro = maestro.merge(
        c_df[[
            'circuit_id', 'circuit_name', 'downforce_level', 'asphalt_abrasion',
            'braking_severity', 'full_throttle_pct', 'length_km'
        ]],
        on='circuit_id',
        how='left'
    )

    # Merge con stops_count
    maestro = maestro.merge(
        stops_count,
        left_on=['season', 'round', 'driverId'],
        right_on=['season', 'round', 'driverId'],
        how='left'
    )
    maestro['total_pit_stops'] = maestro['total_pit_stops'].fillna(0).astype(int)

    maestro = maestro.rename(columns={
        'driverId': 'driver_id',
        'constructorName': 'constructor_name'
    })

    # Reordenar columnas lógicamente
    cols_order = [
        'season', 'round', 'date', 'circuit_id', 'circuit_name', 'race_name',
        'driver_id', 'driver_name', 'constructor_name',
        'grid_start', 'finish_position', 'net_pos_gain', 'points_earned',
        'laps_completed', 'total_pit_stops', 'status',
        'air_temp_c', 'track_temp_c', 'humidity_pct', 'rainfall', 'weather_condition',
        'downforce_level', 'asphalt_abrasion', 'braking_severity', 'full_throttle_pct', 'length_km'
    ]
    maestro = maestro[cols_order].sort_values(['season', 'round', 'finish_position'])
    maestro.to_csv('datasets_procesados/dataset_maestro_carreras.csv', index=False)
    print(f"   ✓ {len(maestro)} registros consolidados en el dataset maestro.")

    # -------------------------------------------------------------------------
    # ELIMINAR ARCHIVOS OBSOLETOS / NO ESTANDARIZADOS
    # -------------------------------------------------------------------------
    obsoletos = ['datasets_procesados/driver_performance_expected.csv']
    for obs in obsoletos:
        if os.path.exists(obs):
            os.remove(obs)
            print(f"   🗑️ Archivo obsoleto eliminado: {obs}")

    print("\n✅ ¡ESTANDARIZACIÓN Y FORMATEO COMPLETADOS EXITOSAMENTE!")

if __name__ == '__main__':
    estandarizar_todo()
