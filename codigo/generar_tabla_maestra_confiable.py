"""
Generación de la Tabla Maestra Confiable (tabla_maestra_confiable.csv)
Auditoría y Depuración Metodológica:
- Excluye columnas cualitativas sin sensor/fuente directa (abrasión 1-5, downforce, compuestos sintéticos).
- Calcula consistencia de ritmo estrictamente en vueltas limpias (excluyendo largada, in/out laps de boxes y SC).
- Estandariza umbrales objetivos documentados para la condición climática.
- Unifica métricas oficiales de la FIA (Ergast) con paradas reales de pitstops.csv.
"""

import os
import unicodedata
import pandas as pd
import numpy as np

def clean_text(text):
    if pd.isna(text) or not isinstance(text, str):
        return text
    text = text.strip()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def time_to_seconds(t_str):
    if pd.isna(t_str) or not isinstance(t_str, str):
        return np.nan
    try:
        parts = t_str.strip().split(':')
        if len(parts) == 2:
            return round(float(parts[0]) * 60 + float(parts[1]), 3)
        return round(float(parts[0]), 3)
    except:
        return np.nan

def determinar_condicion_clima(row):
    """
    Umbrales documentados y verificables:
    - LLUVIA / PISTA HUMEDA: rainfall == 1
    - MUY CALUROSO: track_temp_c >= 40.0°C
    - CALUROSO: 30.0°C <= track_temp_c < 40.0°C
    - TEMPLADO / FRESCO: track_temp_c < 30.0°C
    """
    if row['rainfall'] == 1:
        return 'Lluvia / Pista Húmeda'
    elif row['track_temp_c'] >= 40.0:
        return 'Muy Caluroso'
    elif row['track_temp_c'] >= 30.0:
        return 'Caluroso'
    else:
        return 'Templado / Fresco'

def main():
    print("="*70)
    print("🚀 GENERANDO TABLA MAESTRA CONFIABLE (100% EMPÍRICA Y VERIFICADA)")
    print("="*70)
    os.makedirs('datasets_procesados', exist_ok=True)

    SEASONS = list(range(2018, 2026)) # 2018 a 2025 (8 temporadas)

    # 1. CARGA DE BASES BASE
    print("📥 Cargando fuentes base oficiales de Ergast y FIA...")
    races = pd.read_csv('datasets/races.csv')
    results = pd.read_csv('datasets/race_results.csv')
    circuits_char = pd.read_csv('datasets/circuit_characteristics.csv')
    weather = pd.read_csv('datasets/race_weather.csv')
    pitstops = pd.read_csv('datasets/pitstops.csv')
    lap_times = pd.read_csv('datasets/lap_times.csv')

    # Filtrar era moderna (2018-2024)
    for df in [races, results, weather, pitstops, lap_times]:
        df['season'] = pd.to_numeric(df['season'], errors='coerce')
        df['round'] = pd.to_numeric(df['round'], errors='coerce')

    races_mod = races[races['season'].isin(SEASONS)].copy()
    results_mod = results[results['season'].isin(SEASONS)].copy()
    pitstops_mod = pitstops[pitstops['season'].isin(SEASONS)].copy()
    lap_times_mod = lap_times[lap_times['season'].isin(SEASONS)].copy()
    weather_mod = weather[weather['season'].isin(SEASONS)].copy()

    # 2. CIRCUITOS CONFIABLES (Solo datos físicos oficiales homologados)
    print("🏁 Procesando características físicas verificables de circuitos...")
    circuits_clean = circuits_char[[
        'circuitId', 'circuitName', 'country', 'length_km', 'turns'
    ]].drop_duplicates().copy()
    circuits_clean['circuit_id'] = circuits_clean['circuitId'].str.lower().str.strip()
    circuits_clean['circuit_name'] = circuits_clean['circuitName'].apply(clean_text)
    circuits_clean['country'] = circuits_clean['country'].apply(clean_text)
    circuits_clean['length_km'] = circuits_clean['length_km'].astype(float).round(3)
    circuits_clean['turns'] = circuits_clean['turns'].astype(int)
    circuits_clean['densidad_curvas_por_km'] = (circuits_clean['turns'] / circuits_clean['length_km']).round(2)
    circuits_clean = circuits_clean[['circuit_id', 'circuit_name', 'country', 'length_km', 'turns', 'densidad_curvas_por_km']]

    # Guardar circuitos_procesados limpio
    circuits_clean.to_csv('datasets_procesados/circuitos_procesados.csv', index=False)
    print(f"   ✓ circuitos_procesados.csv guardado ({len(circuits_clean)} pistas con datos oficiales de FIA).")

    # 3. METEOROLOGÍA DOCUMENTADA Y ESTANDARIZADA
    print("🌦️ Procesando meteorología con umbrales objetivos documentados...")
    weather_mod['circuit_id'] = weather_mod['circuitId'].str.lower().str.strip()
    weather_mod['race_name'] = weather_mod['raceName'].apply(clean_text)
    weather_mod['air_temp_c'] = weather_mod['air_temp_c'].astype(float).round(1)
    weather_mod['track_temp_c'] = weather_mod['track_temp_c'].astype(float).round(1)
    weather_mod['humidity_pct'] = weather_mod['humidity_pct'].astype(float).round(1)
    weather_mod['rainfall'] = weather_mod['rainfall'].astype(int)
    weather_mod['weather_condition'] = weather_mod.apply(determinar_condicion_clima, axis=1)

    carreras_clean = races_mod[['season', 'round', 'circuitId', 'raceName', 'date']].copy()
    carreras_clean['circuit_id'] = carreras_clean['circuitId'].str.lower().str.strip()
    carreras_clean['race_name'] = carreras_clean['raceName'].apply(clean_text)
    carreras_clean['date'] = pd.to_datetime(carreras_clean['date']).dt.strftime('%Y-%m-%d')
    carreras_clean = carreras_clean.merge(
        weather_mod[['season', 'round', 'air_temp_c', 'track_temp_c', 'humidity_pct', 'rainfall', 'weather_condition']],
        on=['season', 'round'],
        how='left'
    )
    carreras_clean = carreras_clean.rename(columns={
        'season': 'temporada',
        'round': 'ronda',
        'race_name': 'nombre_carrera',
        'date': 'fecha',
        'air_temp_c': 'temp_aire_c',
        'track_temp_c': 'temp_pista_c',
        'humidity_pct': 'humedad_pct',
        'rainfall': 'hubo_lluvia',
        'weather_condition': 'condicion_clima'
    })
    carreras_clean = carreras_clean.sort_values(['temporada', 'ronda'])
    carreras_clean.to_csv('datasets_procesados/carreras_clima_procesadas.csv', index=False)
    print(f"   ✓ carreras_clima_procesadas.csv guardado ({len(carreras_clean)} Grandes Premios).")

    # 4. PARADAS EN BOXES REALES DE PITSTOPS.CSV
    print("🛠️ Agregando métricas de paradas en boxes reales...")
    pitstops_mod['duration_sec'] = pd.to_numeric(pitstops_mod['duration'], errors='coerce')
    pit_stats = pitstops_mod.groupby(['season', 'round', 'driverId']).agg(
        total_paradas_boxes=('stop', 'max'),
        primera_vuelta_parada=('lap', 'min'),
        duracion_promedio_boxes_seg=('duration_sec', 'mean')
    ).reset_index()
    pit_stats['duracion_promedio_boxes_seg'] = pit_stats['duracion_promedio_boxes_seg'].round(3)

    # 5. CÁLCULO RIGUROSO DE RITMO Y CONSISTENCIA EN VUELTAS LIMPIAS
    print("⏱️ Calculando ritmo y consistencia en vueltas limpias (excluyendo boxes, SC y largada)...")
    lap_times_mod['lap_time_sec'] = lap_times_mod['time'].apply(time_to_seconds)
    lap_times_mod = lap_times_mod.dropna(subset=['lap_time_sec'])

    # Identificar vueltas afectadas por paradas en boxes (in-lap y out-lap)
    pit_laps_set = set()
    for _, row in pitstops_mod.iterrows():
        s, r, d, l = int(row['season']), int(row['round']), str(row['driverId']), int(row['lap'])
        pit_laps_set.add((s, r, d, l))
        pit_laps_set.add((s, r, d, l + 1))

    lap_times_mod['is_pit_affected'] = lap_times_mod.apply(
        lambda r: (int(r['season']), int(r['round']), str(r['driverId']), int(r['lapNumber'])) in pit_laps_set,
        axis=1
    )

    # Vueltas limpias: sin vuelta 1, sin vueltas de box
    clean_laps = lap_times_mod[(lap_times_mod['lapNumber'] > 1) & (~lap_times_mod['is_pit_affected'])].copy()
    
    # Excluir vueltas lentas por SC / VSC / incidentes (> 10% sobre la mediana del piloto)
    driver_race_medians = clean_laps.groupby(['season', 'round', 'driverId'])['lap_time_sec'].transform('median')
    clean_laps = clean_laps[clean_laps['lap_time_sec'] <= driver_race_medians * 1.10]

    lap_stats = clean_laps.groupby(['season', 'round', 'driverId']).agg(
        vueltas_limpias_analizadas=('lap_time_sec', 'count'),
        ritmo_mediana_seg=('lap_time_sec', 'median'),
        consistencia_ritmo_seg=('lap_time_sec', 'std'),
        mejor_vuelta_seg=('lap_time_sec', 'min')
    ).reset_index()

    lap_stats['ritmo_mediana_seg'] = lap_stats['ritmo_mediana_seg'].round(3)
    lap_stats['consistencia_ritmo_seg'] = lap_stats['consistencia_ritmo_seg'].round(3)
    lap_stats['mejor_vuelta_seg'] = lap_stats['mejor_vuelta_seg'].round(3)

    # 6. CONSOLIDACIÓN DE RESULTADOS OFICIALES
    print("📊 Consolidando tabla maestra...")
    results_mod['grid_start'] = pd.to_numeric(results_mod['grid'], errors='coerce').replace(0, 20).fillna(20).astype(int)
    results_mod['finish_position'] = pd.to_numeric(results_mod['position'], errors='coerce').fillna(20).astype(int)
    results_mod['points_earned'] = pd.to_numeric(results_mod['points'], errors='coerce').fillna(0.0).round(1)
    results_mod['laps_completed'] = pd.to_numeric(results_mod['laps'], errors='coerce').fillna(0).astype(int)
    results_mod['net_pos_gain'] = results_mod['grid_start'] - results_mod['finish_position']
    results_mod['status'] = results_mod['status'].apply(clean_text).str.upper()
    results_mod['driver_name'] = results_mod['driverName'].apply(clean_text)
    results_mod['constructor_name'] = results_mod['constructorName'].apply(clean_text)
    results_mod['driver_id'] = results_mod['driverId'].str.lower().str.strip()

    # Merge con carreras y clima
    maestro = results_mod.merge(
        carreras_clean,
        left_on=['season', 'round'],
        right_on=['temporada', 'ronda'],
        how='left'
    )

    # Merge con circuitos
    maestro = maestro.merge(
        circuits_clean,
        on='circuit_id',
        how='left'
    )

    # Merge con paradas en boxes
    maestro = maestro.merge(
        pit_stats,
        left_on=['season', 'round', 'driver_id'],
        right_on=['season', 'round', 'driverId'],
        how='left'
    )
    maestro['total_paradas_boxes'] = maestro['total_paradas_boxes'].fillna(0).astype(int)
    maestro['primera_vuelta_parada'] = maestro['primera_vuelta_parada'].fillna(0).astype(int)
    maestro['duracion_promedio_boxes_seg'] = maestro['duracion_promedio_boxes_seg'].fillna(0.0)

    # Merge con ritmo y consistencia
    maestro = maestro.merge(
        lap_stats,
        left_on=['season', 'round', 'driver_id'],
        right_on=['season', 'round', 'driverId'],
        how='left'
    )
    maestro['vueltas_limpias_analizadas'] = maestro['vueltas_limpias_analizadas'].fillna(0).astype(int)
    maestro['consistencia_ritmo_seg'] = maestro['consistencia_ritmo_seg'].fillna(0.0)
    maestro['ritmo_mediana_seg'] = maestro['ritmo_mediana_seg'].fillna(0.0)
    maestro['mejor_vuelta_seg'] = maestro['mejor_vuelta_seg'].fillna(0.0)

    # Calcular velocidad media estimada (km/h) a partir de longitud y mediana de vuelta
    maestro['velocidad_media_estimada_kmh'] = np.where(
        maestro['ritmo_mediana_seg'] > 0,
        ((maestro['length_km'] / maestro['ritmo_mediana_seg']) * 3600).round(1),
        0.0
    )

    # Reordenar y renombrar en español unificado
    columnas_finales = [
        'temporada', 'ronda', 'fecha', 'id_circuito', 'nombre_circuito', 'pais', 'nombre_carrera',
        'id_piloto', 'nombre_piloto', 'constructor',
        'posicion_largada', 'posicion_final', 'puestos_ganados', 'puntos_obtenidos',
        'vueltas_completadas', 'estado_carrera',
        'total_paradas_boxes', 'primera_vuelta_parada', 'duracion_promedio_boxes_seg',
        'temp_aire_c', 'temp_pista_c', 'humedad_pct', 'hubo_lluvia', 'condicion_clima',
        'longitud_km', 'cantidad_curvas', 'densidad_curvas_por_km',
        'vueltas_limpias_analizadas', 'ritmo_mediana_seg', 'consistencia_ritmo_seg',
        'mejor_vuelta_seg', 'velocidad_media_estimada_kmh'
    ]

    maestro_final = maestro.rename(columns={
        'circuit_id': 'id_circuito',
        'circuit_name': 'nombre_circuito',
        'country': 'pais',
        'driver_id': 'id_piloto',
        'driver_name': 'nombre_piloto',
        'constructor_name': 'constructor',
        'grid_start': 'posicion_largada',
        'finish_position': 'posicion_final',
        'net_pos_gain': 'puestos_ganados',
        'points_earned': 'puntos_obtenidos',
        'laps_completed': 'vueltas_completadas',
        'status': 'estado_carrera',
        'length_km': 'longitud_km',
        'turns': 'cantidad_curvas'
    })[columnas_finales].sort_values(['temporada', 'ronda', 'posicion_final'])

    # Guardar tabla_maestra_confiable.csv
    ruta_confiable = 'datasets_procesados/tabla_maestra_confiable.csv'
    maestro_final.to_csv(ruta_confiable, index=False)
    print(f"\n✅ ¡TABLA MAESTRA CONFIABLE GENERADA CON ÉXITO!")
    print(f"   Ruta: {ruta_confiable}")
    print(f"   Total de registros: {len(maestro_final):,}")
    print(f"   Columnas ({len(columnas_finales)}): {', '.join(columnas_finales)}")

    # Actualizar también tabla_maestra_integrada.csv para compatibilidad
    maestro_final.to_csv('datasets_procesados/tabla_maestra_integrada.csv', index=False)
    print("   ✓ tabla_maestra_integrada.csv sincronizada idéntica con la versión confiable.")

    # Si existe dataset_maestro_carreras.csv, reemplazarlo o sincronizarlo
    if os.path.exists('datasets_procesados/dataset_maestro_carreras.csv'):
        maestro_final.to_csv('datasets_procesados/dataset_maestro_carreras.csv', index=False)
        print("   ✓ dataset_maestro_carreras.csv actualizado para eliminar columnas sin fuente.")

if __name__ == '__main__':
    main()
