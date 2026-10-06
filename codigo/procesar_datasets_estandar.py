"""
Estandarización y Procesamiento Integral de Datasets - BeyondGrid AI & CircuitDNA
Aplica la regla de nomenclatura estricta y trazabilidad:
- Archivos en datasets_procesados/ con nombre: [nombre_original]_procesado.csv
- Contenido interno con encabezados y valores en español, tipos nativos numéricos y fechas ISO.
- Columna 'fuente' en cada archivo procesado para auditoría y trazabilidad académica oficial.
- Cobertura completa multi-año incluyendo la temporada 2025 (2018-2025 para analítica de telemetría y ritmo).
- Generación de tabla_maestra_confiable.csv (y alias tabla_maestra_procesada.csv) con 32 métricas.
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
        parts = str(t_str).strip().split(':')
        if len(parts) == 2:
            return round(float(parts[0]) * 60 + float(parts[1]), 3)
        return round(float(parts[0]), 3)
    except:
        return np.nan

def determinar_condicion_clima(row):
    """
    Reglas cuantitativas documentadas:
    - Lluvia / Pista Húmeda: rainfall == 1
    - Muy Caluroso: track_temp_c >= 40.0°C
    - Caluroso: 30.0°C <= track_temp_c < 40.0°C
    - Templado / Fresco: track_temp_c < 30.0°C
    """
    if row.get('rainfall', 0) == 1:
        return 'Lluvia / Pista Húmeda'
    track = row.get('track_temp_c', 25.0)
    if track >= 40.0:
        return 'Muy Caluroso'
    elif track >= 30.0:
        return 'Caluroso'
    else:
        return 'Templado / Fresco'

def procesar_todo():
    print("=" * 80)
    print("🚀 PIPELINE DE ESTANDARIZACIÓN INTEGRAL 2018-2025 [nombre_original]_procesado.csv")
    print("=" * 80)
    os.makedirs('datasets_procesados', exist_ok=True)

    SEASONS = list(range(2018, 2026)) # 2018 a 2025 inclusive (8 temporadas)

    # -------------------------------------------------------------------------
    # 1. circuits_procesado.csv (Original: circuits.csv - 77 circuitos históricos)
    # -------------------------------------------------------------------------
    print("🏁 1a/20 Generando circuits_procesado.csv...")
    c_raw = pd.read_csv('datasets/circuits.csv')
    c_proc = pd.DataFrame({
        'id_circuito': c_raw['circuitId'].str.lower().str.strip(),
        'nombre_circuito': c_raw['circuitName'].apply(clean_text),
        'localidad': c_raw['locality'].apply(clean_text),
        'pais': c_raw['country'].apply(clean_text),
        'latitud': pd.to_numeric(c_raw['lat'], errors='coerce').round(4),
        'longitud': pd.to_numeric(c_raw['long'], errors='coerce').round(4),
        'url_biografia': c_raw['url'].fillna(''),
        'fuente': "Base Oficial Ergast Motor Racing Database / Catálogo FIA de Circuitos"
    }).sort_values('nombre_circuito')
    c_proc.to_csv('datasets_procesados/circuits_procesado.csv', index=False)
    print(f"   ✓ circuits_procesado.csv guardado ({len(c_proc)} circuitos históricos 1950-2025).")

    # -------------------------------------------------------------------------
    # 1b. circuit_characteristics_procesado.csv (Original: circuit_characteristics.csv - 31 circuitos modernos)
    # -------------------------------------------------------------------------
    print("🏁 1b/20 Generando circuit_characteristics_procesado.csv...")
    c_char = pd.read_csv('datasets/circuit_characteristics.csv')
    c_char['id_circuito'] = c_char['circuitId'].str.lower().str.strip()
    c_char['nombre_circuito'] = c_char['circuitName'].apply(clean_text)
    c_char['pais'] = c_char['country'].apply(clean_text)
    c_char['longitud_km'] = c_char['length_km'].astype(float).round(3)
    c_char['cantidad_curvas'] = c_char['turns'].astype(int)
    c_char['densidad_curvas_por_km'] = (c_char['cantidad_curvas'] / c_char['longitud_km']).round(2)
    c_char['fuente'] = "Certificados Oficiales de Homologación FIA / Formula1.com"

    circuits_clean = c_char[['id_circuito', 'nombre_circuito', 'pais', 'longitud_km', 'cantidad_curvas', 'densidad_curvas_por_km', 'fuente']].sort_values('nombre_circuito')
    circuits_clean.to_csv('datasets_procesados/circuit_characteristics_procesado.csv', index=False)
    print(f"   ✓ circuit_characteristics_procesado.csv guardado ({len(circuits_clean)} circuitos oficiales).")

    # -------------------------------------------------------------------------
    # 2. races_procesado.csv (Original: races.csv)
    # -------------------------------------------------------------------------
    print("📅 2/20 Generando races_procesado.csv...")
    races_raw = pd.read_csv('datasets/races.csv')
    races_raw['season'] = pd.to_numeric(races_raw['season'], errors='coerce')
    races_raw['round'] = pd.to_numeric(races_raw['round'], errors='coerce')
    races_mod = races_raw[races_raw['season'].isin(SEASONS)].copy()
    
    r_proc = pd.DataFrame({
        'temporada': races_mod['season'].astype(int),
        'ronda': races_mod['round'].astype(int),
        'nombre_carrera': races_mod['raceName'].apply(clean_text),
        'id_circuito': races_mod['circuitId'].str.lower().str.strip(),
        'nombre_circuito': races_mod['circuitName'].apply(clean_text),
        'fecha': pd.to_datetime(races_mod['date']).dt.strftime('%Y-%m-%d'),
        'hora': races_mod['time'].fillna('14:00:00'),
        'fuente': "Calendario Oficial FIA Formula 1 World Championship"
    }).sort_values(['temporada', 'ronda'])
    r_proc.to_csv('datasets_procesados/races_procesado.csv', index=False)
    print(f"   ✓ races_procesado.csv guardado ({len(r_proc)} grandes premios 2018-2025).")

    # Mapeo de carreras para fusiones
    r_dates = r_proc[['temporada', 'ronda', 'fecha']].copy()

    # -------------------------------------------------------------------------
    # 3. race_weather_procesado.csv (Original: race_weather.csv)
    # -------------------------------------------------------------------------
    print("🌦️ 3/20 Generando race_weather_procesado.csv...")
    weather_raw = pd.read_csv('datasets/race_weather.csv')
    weather_raw['season'] = pd.to_numeric(weather_raw['season'], errors='coerce')
    weather_raw['round'] = pd.to_numeric(weather_raw['round'], errors='coerce')
    weather_mod = weather_raw[weather_raw['season'].isin(SEASONS)].copy()

    weather_mod['id_circuito'] = weather_mod['circuitId'].str.lower().str.strip()
    weather_mod['nombre_carrera'] = weather_mod['raceName'].apply(clean_text)
    weather_mod['temp_aire_c'] = weather_mod['air_temp_c'].astype(float).round(1)
    weather_mod['temp_pista_c'] = weather_mod['track_temp_c'].astype(float).round(1)
    weather_mod['humedad_pct'] = weather_mod['humidity_pct'].astype(float).round(1)
    weather_mod['hubo_lluvia'] = weather_mod['rainfall'].astype(int)
    weather_mod['condicion_clima'] = weather_mod.apply(determinar_condicion_clima, axis=1)

    w_merged = weather_mod.merge(r_dates, left_on=['season', 'round'], right_on=['temporada', 'ronda'], how='left')
    w_clean = pd.DataFrame({
        'temporada': w_merged['season'].astype(int),
        'ronda': w_merged['round'].astype(int),
        'id_circuito': w_merged['id_circuito'],
        'nombre_carrera': w_merged['nombre_carrera'],
        'fecha': w_merged['fecha'],
        'temp_aire_c': w_merged['temp_aire_c'],
        'temp_pista_c': w_merged['temp_pista_c'],
        'humedad_pct': w_merged['humedad_pct'],
        'hubo_lluvia': w_merged['hubo_lluvia'],
        'condicion_clima': w_merged['condicion_clima'],
        'fuente': "OpenF1 Session Weather API / Archivo Histórico Meteorológico de Carrera"
    }).sort_values(['temporada', 'ronda'])
    w_clean.to_csv('datasets_procesados/race_weather_procesado.csv', index=False)
    print(f"   ✓ race_weather_procesado.csv guardado ({len(w_clean)} registros climáticos).")

    # -------------------------------------------------------------------------
    # 4. pitstops_procesado.csv (Original: pitstops.csv)
    # -------------------------------------------------------------------------
    print("🛠️ 4/20 Generando pitstops_procesado.csv...")
    pit_raw = pd.read_csv('datasets/pitstops.csv')
    pit_raw['season'] = pd.to_numeric(pit_raw['season'], errors='coerce')
    pit_raw['round'] = pd.to_numeric(pit_raw['round'], errors='coerce')
    pit_mod = pit_raw[pit_raw['season'].isin(SEASONS)].copy()

    p_clean = pd.DataFrame({
        'temporada': pit_mod['season'].astype(int),
        'ronda': pit_mod['round'].astype(int),
        'id_piloto': pit_mod['driverId'].str.lower().str.strip(),
        'numero_parada': pd.to_numeric(pit_mod['stop'], errors='coerce').fillna(1).astype(int),
        'vuelta_parada': pd.to_numeric(pit_mod['lap'], errors='coerce').fillna(1).astype(int),
        'hora_parada': pit_mod['time'].fillna(''),
        'duracion_parada_seg': pd.to_numeric(pit_mod['duration'], errors='coerce').round(3),
        'fuente': "Base Oficial Ergast Motor Racing Database / FIA Timing Sheets"
    }).sort_values(['temporada', 'ronda', 'id_piloto', 'numero_parada'])
    p_clean.to_csv('datasets_procesados/pitstops_procesado.csv', index=False)
    print(f"   ✓ pitstops_procesado.csv guardado ({len(p_clean)} paradas en boxes 2018-2025).")

    # -------------------------------------------------------------------------
    # 5. lap_times_procesado.csv (Original: lap_times.csv)
    # -------------------------------------------------------------------------
    print("⏱️ 5/20 Generando lap_times_procesado.csv...")
    lt_raw = pd.read_csv('datasets/lap_times.csv')
    lt_raw['season'] = pd.to_numeric(lt_raw['season'], errors='coerce')
    lt_raw['round'] = pd.to_numeric(lt_raw['round'], errors='coerce')
    lt_mod = lt_raw[lt_raw['season'].isin(SEASONS)].copy()

    # Mapeo de circuito por temporada y ronda
    race_circuits = races_mod[['season', 'round', 'circuitId']].drop_duplicates()
    lt_mod = lt_mod.merge(race_circuits, on=['season', 'round'], how='left')

    lt_mod['tiempo_vuelta_seg'] = lt_mod['time'].apply(time_to_seconds)
    laps_filtered = lt_mod.dropna(subset=['tiempo_vuelta_seg']).query('tiempo_vuelta_seg >= 50 and tiempo_vuelta_seg <= 160').copy()

    laps_clean = pd.DataFrame({
        'temporada': laps_filtered['season'].astype(int),
        'ronda': laps_filtered['round'].astype(int),
        'id_circuito': laps_filtered['circuitId'].str.lower().str.strip(),
        'id_piloto': laps_filtered['driverId'].str.lower().str.strip(),
        'numero_vuelta': pd.to_numeric(laps_filtered['lapNumber'], errors='coerce').astype(int),
        'posicion': pd.to_numeric(laps_filtered['position'], errors='coerce').astype(int),
        'tiempo_vuelta_seg': laps_filtered['tiempo_vuelta_seg'].round(3),
        'fuente': "Base Oficial Ergast Motor Racing Database / FIA Lap Timing"
    }).sort_values(['temporada', 'ronda', 'id_piloto', 'numero_vuelta'])
    laps_clean.to_csv('datasets_procesados/lap_times_procesado.csv', index=False)
    print(f"   ✓ lap_times_procesado.csv guardado ({len(laps_clean)} vueltas limpias 2018-2025).")

    # -------------------------------------------------------------------------
    # 6. race_results_procesado.csv (Original: race_results.csv)
    # -------------------------------------------------------------------------
    print("📊 6/20 Generando race_results_procesado.csv...")
    res_raw = pd.read_csv('datasets/race_results.csv')
    res_raw['season'] = pd.to_numeric(res_raw['season'], errors='coerce')
    res_raw['round'] = pd.to_numeric(res_raw['round'], errors='coerce')
    res_mod = res_raw[res_raw['season'].isin(SEASONS)].copy()

    driver_name_map = {}
    for _, row in res_mod[['driverId', 'driverName']].drop_duplicates().iterrows():
        driver_name_map[str(row['driverId']).lower().strip()] = clean_text(row['driverName'])

    pos_grid = pd.to_numeric(res_mod['grid'], errors='coerce').replace(0, 20).fillna(20).astype(int)
    pos_fin = pd.to_numeric(res_mod['position'], errors='coerce').fillna(20).astype(int)

    res_clean = pd.DataFrame({
        'temporada': res_mod['season'].astype(int),
        'ronda': res_mod['round'].astype(int),
        'id_piloto': res_mod['driverId'].str.lower().str.strip(),
        'nombre_piloto': res_mod['driverId'].str.lower().str.strip().map(driver_name_map).fillna(res_mod['driverName'].apply(clean_text)),
        'constructor': res_mod['constructorName'].apply(clean_text),
        'posicion_largada': pos_grid,
        'posicion_final': pos_fin,
        'puestos_ganados': pos_grid - pos_fin,
        'puntos_obtenidos': pd.to_numeric(res_mod['points'], errors='coerce').fillna(0.0).round(1),
        'vueltas_completadas': pd.to_numeric(res_mod['laps'], errors='coerce').fillna(0).astype(int),
        'estado_carrera': res_mod['status'].apply(clean_text).str.upper(),
        'fuente': "Base Oficial Ergast Motor Racing Database / TracingInsights RaceData"
    }).sort_values(['temporada', 'ronda', 'posicion_final'])
    res_clean.to_csv('datasets_procesados/race_results_procesado.csv', index=False)
    print(f"   ✓ race_results_procesado.csv guardado ({len(res_clean)} clasificaciones de carrera).")

    # -------------------------------------------------------------------------
    # 7. tyre_stints_procesado.csv (Original: tyre_stints.csv)
    # -------------------------------------------------------------------------
    print("🛞 7/20 Generando tyre_stints_procesado.csv...")
    stints_raw = pd.read_csv('datasets/tyre_stints.csv')
    stints_raw['season'] = pd.to_numeric(stints_raw['season'], errors='coerce')
    stints_raw['round'] = pd.to_numeric(stints_raw['round'], errors='coerce')
    stints_mod = stints_raw[stints_raw['season'].isin(SEASONS)].merge(race_circuits, on=['season', 'round'], how='left')

    stints_clean = pd.DataFrame({
        'temporada': stints_mod['season'].astype(int),
        'ronda': stints_mod['round'].astype(int),
        'id_circuito': stints_mod['circuitId'].str.lower().str.strip(),
        'id_piloto': stints_mod['driverId'].str.lower().str.strip(),
        'nombre_piloto': stints_mod['driverId'].str.lower().str.strip().map(driver_name_map).fillna(stints_mod['driverId']),
        'constructor': stints_mod['constructorName'].apply(clean_text),
        'numero_stint': pd.to_numeric(stints_mod['stint_number'], errors='coerce').fillna(1).astype(int),
        'vuelta_inicio': pd.to_numeric(stints_mod['lap_start'], errors='coerce').fillna(1).astype(int),
        'vuelta_fin': pd.to_numeric(stints_mod['lap_end'], errors='coerce').fillna(1).astype(int),
        'duracion_stint_vueltas': pd.to_numeric(stints_mod['stint_length'], errors='coerce').fillna(1).astype(int),
        'compuesto': stints_mod['compound'].fillna('').astype(str).str.upper(),
        'duracion_parada_seg': pd.to_numeric(stints_mod['pit_duration'], errors='coerce').round(3),
        'fuente': np.where(
            stints_mod['season'] >= 2023,
            "Telemetría Oficial en Tiempo Real OpenF1 (api.openf1.org)",
            "Base Oficial Ergast (Boxes y Vueltas Reales) / Sin Telemetría Digital de Compuesto"
        )
    }).sort_values(['temporada', 'ronda', 'id_piloto', 'numero_stint'])
    stints_clean.to_csv('datasets_procesados/tyre_stints_procesado.csv', index=False)
    print(f"   ✓ tyre_stints_procesado.csv guardado ({len(stints_clean)} tandas de neumáticos).")

    # -------------------------------------------------------------------------
    # 8. pirelli_nominations_procesado.csv (Original: pirelli_nominations.csv)
    # -------------------------------------------------------------------------
    print("🎯 8/20 Generando pirelli_nominations_procesado.csv...")
    nom_raw = pd.read_csv('datasets/pirelli_nominations.csv')
    nom_raw['season'] = pd.to_numeric(nom_raw['season'], errors='coerce')
    nom_raw['round'] = pd.to_numeric(nom_raw['round'], errors='coerce')
    nom_mod = nom_raw[nom_raw['season'].isin(SEASONS)].copy()

    nom_clean = pd.DataFrame({
        'temporada': nom_mod['season'].astype(int),
        'ronda': nom_mod['round'].astype(int),
        'id_circuito': nom_mod['circuitId'].str.lower().str.strip(),
        'nombre_carrera': nom_mod['raceName'].apply(clean_text),
        'compuesto_duro': nom_mod['compound_hard'].astype(str).str.strip().str.upper(),
        'compuesto_medio': nom_mod['compound_medium'].astype(str).str.strip().str.upper(),
        'compuesto_blando': nom_mod['compound_soft'].astype(str).str.strip().str.upper(),
        'fuente': "Comunicados Oficiales Pirelli Motorsport / Notas de Evento FIA"
    }).sort_values(['temporada', 'ronda'])
    nom_clean.to_csv('datasets_procesados/pirelli_nominations_procesado.csv', index=False)
    print(f"   ✓ pirelli_nominations_procesado.csv guardado ({len(nom_clean)} nominaciones oficiales 2018-2025).")

    # -------------------------------------------------------------------------
    # 9. driver_standings_procesado.csv (Original: driver_standings.csv)
    # -------------------------------------------------------------------------
    print("🏆 9/20 Generando driver_standings_procesado.csv...")
    ds_raw = pd.read_csv('datasets/driver_standings.csv')
    ds_clean = pd.DataFrame({
        'id_posicion_piloto': pd.to_numeric(ds_raw['driverStandingsId'], errors='coerce').astype(int),
        'id_carrera': pd.to_numeric(ds_raw['raceId'], errors='coerce').astype(int),
        'id_piloto': ds_raw['driverId'].astype(str).str.lower().str.strip(),
        'puntos': pd.to_numeric(ds_raw['points'], errors='coerce').fillna(0.0).round(1),
        'posicion': pd.to_numeric(ds_raw['position'], errors='coerce').fillna(0).astype(int),
        'posicion_texto': ds_raw['positionText'].astype(str).str.strip(),
        'victorias': pd.to_numeric(ds_raw['wins'], errors='coerce').fillna(0).astype(int),
        'fuente': "Base Oficial Ergast Motor Racing Database / FIA Standings"
    }).sort_values(['id_carrera', 'posicion'])
    ds_clean.to_csv('datasets_procesados/driver_standings_procesado.csv', index=False)
    print(f"   ✓ driver_standings_procesado.csv guardado ({len(ds_clean)} registros históricos 1950-2025).")

    # -------------------------------------------------------------------------
    # 10. constructor_standings_procesado.csv (Original: constructor_standings.csv)
    # -------------------------------------------------------------------------
    print("🏎️ 10/20 Generando constructor_standings_procesado.csv...")
    cs_raw = pd.read_csv('datasets/constructor_standings.csv')
    cs_clean = pd.DataFrame({
        'id_posicion_constructor': pd.to_numeric(cs_raw['constructorStandingsId'], errors='coerce').astype(int),
        'id_carrera': pd.to_numeric(cs_raw['raceId'], errors='coerce').astype(int),
        'id_constructor': cs_raw['constructorId'].astype(str).str.lower().str.strip(),
        'puntos': pd.to_numeric(cs_raw['points'], errors='coerce').fillna(0.0).round(1),
        'posicion': pd.to_numeric(cs_raw['position'], errors='coerce').fillna(0).astype(int),
        'posicion_texto': cs_raw['positionText'].astype(str).str.strip(),
        'victorias': pd.to_numeric(cs_raw['wins'], errors='coerce').fillna(0).astype(int),
        'fuente': "Base Oficial Ergast Motor Racing Database / FIA Standings"
    }).sort_values(['id_carrera', 'posicion'])
    cs_clean.to_csv('datasets_procesados/constructor_standings_procesado.csv', index=False)
    print(f"   ✓ constructor_standings_procesado.csv guardado ({len(cs_clean)} registros históricos 1958-2025).")

    # -------------------------------------------------------------------------
    # 11. safety_cars_procesado.csv (Original: safety_cars.csv)
    # -------------------------------------------------------------------------
    print("🚨 11/20 Generando safety_cars_procesado.csv...")
    sc_raw = pd.read_csv('datasets/safety_cars.csv')
    sc_clean = pd.DataFrame({
        'carrera': sc_raw['Race'].astype(str).str.strip(),
        'causa': sc_raw['Cause'].apply(clean_text),
        'vuelta_despliegue': pd.to_numeric(sc_raw['Deployed'], errors='coerce'),
        'vuelta_reingreso': pd.to_numeric(sc_raw['Retreated'], errors='coerce'),
        'vueltas_completas': pd.to_numeric(sc_raw['FullLaps'], errors='coerce'),
        'fuente': "Archivo Histórico Oficial TracingInsights / FIA Race Director Notes"
    })
    sc_clean.to_csv('datasets_procesados/safety_cars_procesado.csv', index=False)
    print(f"   ✓ safety_cars_procesado.csv guardado ({len(sc_clean)} despliegues de Safety Car 1973-2025).")

    # -------------------------------------------------------------------------
    # 12. virtual_safety_cars_procesado.csv (Original: virtual_safety_cars.csv)
    # -------------------------------------------------------------------------
    print("⚠️ 12/20 Generando virtual_safety_cars_procesado.csv...")
    vsc_raw = pd.read_csv('datasets/virtual_safety_cars.csv')
    vsc_clean = pd.DataFrame({
        'carrera': vsc_raw['Race'].astype(str).str.strip(),
        'vuelta_despliegue': pd.to_numeric(vsc_raw['Deployed'], errors='coerce'),
        'vuelta_reingreso': pd.to_numeric(vsc_raw['Retreated'], errors='coerce'),
        'vueltas_completas': pd.to_numeric(vsc_raw['FullLaps'], errors='coerce'),
        'fuente': "Archivo Histórico Oficial TracingInsights / FIA Race Director Notes"
    })
    vsc_clean.to_csv('datasets_procesados/virtual_safety_cars_procesado.csv', index=False)
    print(f"   ✓ virtual_safety_cars_procesado.csv guardado ({len(vsc_clean)} despliegues de VSC 2015-2025).")

    # -------------------------------------------------------------------------
    # 13. red_flags_procesado.csv (Original: red_flags.csv)
    # -------------------------------------------------------------------------
    print("🚩 13/20 Generando red_flags_procesado.csv...")
    rf_raw = pd.read_csv('datasets/red_flags.csv')
    rf_clean = pd.DataFrame({
        'carrera': rf_raw['Race'].astype(str).str.strip(),
        'vuelta': pd.to_numeric(rf_raw['Lap'], errors='coerce'),
        'reanudada': rf_raw['Resumed'].astype(str).str.strip(),
        'incidente': rf_raw['Incident'].apply(clean_text),
        'pilotos_excluidos': rf_raw['Excluded'].apply(clean_text).fillna(''),
        'fuente': "Archivo Histórico Oficial TracingInsights / FIA Race Director Notes"
    })
    rf_clean.to_csv('datasets_procesados/red_flags_procesado.csv', index=False)
    print(f"   ✓ red_flags_procesado.csv guardado ({len(rf_clean)} banderas rojas históricas).")

    # -------------------------------------------------------------------------
    # 14. qualifying_results_procesado.csv (Original: qualifying_results.csv)
    # -------------------------------------------------------------------------
    print("⏱️ 14/20 Generando qualifying_results_procesado.csv...")
    q_raw = pd.read_csv('datasets/qualifying_results.csv')
    q_raw['season'] = pd.to_numeric(q_raw['season'], errors='coerce')
    q_raw['round'] = pd.to_numeric(q_raw['round'], errors='coerce')
    q_mod = q_raw[q_raw['season'].isin(SEASONS)].copy()

    q_clean = pd.DataFrame({
        'temporada': q_mod['season'].astype(int),
        'ronda': q_mod['round'].astype(int),
        'id_piloto': q_mod['driverId'].str.lower().str.strip(),
        'nombre_piloto': q_mod['driverName'].apply(clean_text),
        'constructor': q_mod['constructorName'].apply(clean_text),
        'posicion': pd.to_numeric(q_mod['position'], errors='coerce').fillna(20).astype(int),
        'q1': q_mod['Q1'].fillna(''),
        'q2': q_mod['Q2'].fillna(''),
        'q3': q_mod['Q3'].fillna(''),
        'fuente': "Base Oficial Ergast Motor Racing Database / FIA Qualifying Classification"
    }).sort_values(['temporada', 'ronda', 'posicion'])
    q_clean.to_csv('datasets_procesados/qualifying_results_procesado.csv', index=False)
    print(f"   ✓ qualifying_results_procesado.csv guardado ({len(q_clean)} resultados de clasificación 2018-2025).")

    # -------------------------------------------------------------------------
    # 15. sprint_results_procesado.csv (Original: sprint_results.csv)
    # -------------------------------------------------------------------------
    print("⚡ 15/20 Generando sprint_results_procesado.csv...")
    sp_raw = pd.read_csv('datasets/sprint_results.csv')
    sp_clean = pd.DataFrame({
        'temporada': pd.to_numeric(sp_raw['season'], errors='coerce').astype(int),
        'ronda': pd.to_numeric(sp_raw['round'], errors='coerce').astype(int),
        'id_piloto': sp_raw['driverId'].str.lower().str.strip(),
        'nombre_piloto': sp_raw['driverName'].apply(clean_text),
        'constructor': sp_raw['constructorName'].apply(clean_text),
        'posicion': pd.to_numeric(sp_raw['position'], errors='coerce').fillna(20).astype(int),
        'puntos': pd.to_numeric(sp_raw['points'], errors='coerce').fillna(0.0).round(1),
        'vueltas': pd.to_numeric(sp_raw['laps'], errors='coerce').fillna(0).astype(int),
        'estado': sp_raw['status'].apply(clean_text).str.upper(),
        'fuente': "OpenF1 Real-Time Telemetry API & Ergast Sprint Archive"
    }).sort_values(['temporada', 'ronda', 'posicion'])
    sp_clean.to_csv('datasets_procesados/sprint_results_procesado.csv', index=False)
    print(f"   ✓ sprint_results_procesado.csv guardado ({len(sp_clean)} resultados de carreras sprint 2021-2025).")

    # -------------------------------------------------------------------------
    # 16. drivers_procesado.csv (Original: drivers.csv)
    # -------------------------------------------------------------------------
    print("👤 16/20 Generando drivers_procesado.csv...")
    d_raw = pd.read_csv('datasets/drivers.csv')
    d_clean = pd.DataFrame({
        'id_piloto': d_raw['driverId'].str.lower().str.strip(),
        'nombre': d_raw['givenName'].apply(clean_text),
        'apellido': d_raw['familyName'].apply(clean_text),
        'codigo': d_raw['code'].fillna('').astype(str).str.upper(),
        'numero_permanente': pd.to_numeric(d_raw['permanentNumber'], errors='coerce'),
        'fecha_nacimiento': d_raw['dateOfBirth'].fillna(''),
        'nacionalidad': d_raw['nationality'].apply(clean_text),
        'url_biografia': d_raw['url'].fillna(''),
        'fuente': "Base Oficial Ergast Motor Racing Database / Registro Oficial FIA"
    }).sort_values('id_piloto')
    d_clean.to_csv('datasets_procesados/drivers_procesado.csv', index=False)
    print(f"   ✓ drivers_procesado.csv guardado ({len(d_clean)} pilotos registrados).")

    # -------------------------------------------------------------------------
    # 17. constructors_procesado.csv (Original: constructors.csv)
    # -------------------------------------------------------------------------
    print("🏭 17/20 Generando constructors_procesado.csv...")
    con_raw = pd.read_csv('datasets/constructors.csv')
    con_clean = pd.DataFrame({
        'id_constructor': con_raw['constructorId'].str.lower().str.strip(),
        'nombre_constructor': con_raw['constructorName'].apply(clean_text),
        'nacionalidad': con_raw['nationality'].apply(clean_text),
        'url_biografia': con_raw['url'].fillna(''),
        'fuente': "Base Oficial Ergast Motor Racing Database / Registro Oficial FIA"
    }).sort_values('id_constructor')
    con_clean.to_csv('datasets_procesados/constructors_procesado.csv', index=False)
    print(f"   ✓ constructors_procesado.csv guardado ({len(con_clean)} escuderías registradas).")

    # -------------------------------------------------------------------------
    # 18. seasons_procesado.csv (Original: seasons.csv)
    # -------------------------------------------------------------------------
    print("📖 18/20 Generando seasons_procesado.csv...")
    sea_raw = pd.read_csv('datasets/seasons.csv')
    sea_clean = pd.DataFrame({
        'temporada': pd.to_numeric(sea_raw['season'], errors='coerce').astype(int),
        'url_resumen': sea_raw['url'].fillna(''),
        'fuente': "Archivo Histórico FIA Formula 1 World Championship"
    }).sort_values('temporada', ascending=False)
    sea_clean.to_csv('datasets_procesados/seasons_procesado.csv', index=False)
    print(f"   ✓ seasons_procesado.csv guardado ({len(sea_clean)} temporadas 1950-2025).")

    # -------------------------------------------------------------------------
    # 19. status_procesado.csv (Original: status.csv)
    # -------------------------------------------------------------------------
    print("📋 19/20 Generando status_procesado.csv...")
    st_raw = pd.read_csv('datasets/status.csv')
    st_clean = pd.DataFrame({
        'id_estado': pd.to_numeric(st_raw['statusId'], errors='coerce').astype(int),
        'descripcion_estado': st_raw['status'].apply(clean_text).str.upper(),
        'fuente': "Catálogo Oficial de Clasificación y Estados de Carrera Ergast / FIA"
    }).sort_values('id_estado')
    st_clean.to_csv('datasets_procesados/status_procesado.csv', index=False)
    print(f"   ✓ status_procesado.csv guardado ({len(st_clean)} estados oficiales).")

    # -------------------------------------------------------------------------
    # 20. tabla_maestra_confiable.csv y tabla_maestra_procesada.csv
    # -------------------------------------------------------------------------
    print("⭐ 20/20 Consolidando tabla_maestra_confiable.csv y tabla_maestra_procesada.csv...")
    
    # Paradas agregadas
    pit_summary = p_clean.groupby(['temporada', 'ronda', 'id_piloto']).agg(
        total_paradas_boxes=('numero_parada', 'max'),
        primera_vuelta_parada=('vuelta_parada', 'min'),
        duracion_promedio_boxes_seg=('duracion_parada_seg', 'mean')
    ).reset_index()
    pit_summary['duracion_promedio_boxes_seg'] = pit_summary['duracion_promedio_boxes_seg'].round(3)

    # Identificación rápida de vueltas afectadas por paradas
    pit_laps_set = set()
    for _, row in p_clean.iterrows():
        s, r, d, l = int(row['temporada']), int(row['ronda']), str(row['id_piloto']), int(row['vuelta_parada'])
        pit_laps_set.add((s, r, d, l))
        pit_laps_set.add((s, r, d, l + 1))

    # Optimización de verificación de vueltas limpias (vectorizada por tuplas)
    keys = list(zip(laps_clean['temporada'].astype(int), laps_clean['ronda'].astype(int), laps_clean['id_piloto'].astype(str), laps_clean['numero_vuelta'].astype(int)))
    is_pit_affected = [k in pit_laps_set for k in keys]
    laps_for_cons = laps_clean.copy()
    laps_for_cons['is_pit_affected'] = is_pit_affected

    clean_laps = laps_for_cons[(laps_for_cons['numero_vuelta'] > 1) & (~laps_for_cons['is_pit_affected'])].copy()
    meds = clean_laps.groupby(['temporada', 'ronda', 'id_piloto'])['tiempo_vuelta_seg'].transform('median')
    clean_laps = clean_laps[clean_laps['tiempo_vuelta_seg'] <= meds * 1.10]

    lap_stats = clean_laps.groupby(['temporada', 'ronda', 'id_piloto']).agg(
        vueltas_limpias_analizadas=('tiempo_vuelta_seg', 'count'),
        ritmo_mediana_seg=('tiempo_vuelta_seg', 'median'),
        consistencia_ritmo_seg=('tiempo_vuelta_seg', 'std'),
        mejor_vuelta_seg=('tiempo_vuelta_seg', 'min')
    ).reset_index()
    lap_stats['ritmo_mediana_seg'] = lap_stats['ritmo_mediana_seg'].round(3)
    lap_stats['consistencia_ritmo_seg'] = lap_stats['consistencia_ritmo_seg'].round(3)
    lap_stats['mejor_vuelta_seg'] = lap_stats['mejor_vuelta_seg'].round(3)

    # Fusionar tabla maestra
    maestro = res_clean.merge(w_clean.drop(columns=['fuente']), on=['temporada', 'ronda'], how='left')
    maestro = maestro.merge(circuits_clean.drop(columns=['fuente']), on='id_circuito', how='left')
    maestro = maestro.merge(pit_summary, on=['temporada', 'ronda', 'id_piloto'], how='left')
    maestro['total_paradas_boxes'] = maestro['total_paradas_boxes'].fillna(0).astype(int)
    maestro['primera_vuelta_parada'] = maestro['primera_vuelta_parada'].fillna(0).astype(int)
    maestro['duracion_promedio_boxes_seg'] = maestro['duracion_promedio_boxes_seg'].fillna(0.0)

    maestro = maestro.merge(lap_stats, on=['temporada', 'ronda', 'id_piloto'], how='left')
    maestro['vueltas_limpias_analizadas'] = maestro['vueltas_limpias_analizadas'].fillna(0).astype(int)
    maestro['ritmo_mediana_seg'] = maestro['ritmo_mediana_seg'].fillna(0.0)
    maestro['consistencia_ritmo_seg'] = maestro['consistencia_ritmo_seg'].fillna(0.0)
    maestro['mejor_vuelta_seg'] = maestro['mejor_vuelta_seg'].fillna(0.0)

    maestro['velocidad_media_estimada_kmh'] = np.where(
        maestro['ritmo_mediana_seg'] > 0,
        ((maestro['longitud_km'] / maestro['ritmo_mediana_seg']) * 3600).round(1),
        0.0
    )

    columnas_orden = [
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
    maestro_final = maestro[columnas_orden].sort_values(['temporada', 'ronda', 'posicion_final'])

    maestro_final.to_csv('datasets_procesados/tabla_maestra_confiable.csv', index=False)
    maestro_final.to_csv('datasets_procesados/tabla_maestra_procesada.csv', index=False)
    print(f"   ✓ tabla_maestra_confiable.csv guardado ({len(maestro_final)} filas, 173 GGPP 2018-2025).")
    print(f"   ✓ tabla_maestra_procesada.csv guardado ({len(maestro_final)} filas, 173 GGPP 2018-2025).")

    # Limpieza de archivos obsoletos
    archivos_a_eliminar = [
        'datasets_procesados/circuitos_procesados.csv',
        'datasets_procesados/carreras_clima_procesadas.csv',
        'datasets_procesados/tiempos_vuelta_procesados.csv',
        'datasets_procesados/stints_neumaticos_procesados.csv',
        'datasets_procesados/dataset_maestro_carreras.csv',
        'datasets_procesados/tabla_maestra_integrada.csv'
    ]
    for ruta in archivos_a_eliminar:
        if os.path.exists(ruta):
            os.remove(ruta)
            print(f"   🗑️ Archivo obsoleto removido: {ruta}")

    print("\n" + "=" * 80)
    print("✨ ¡PIPELINE EXITOSO! 20 DATASETS PROCESADOS + TABLA MAESTRA EN datasets_procesados/")
    print("=" * 80)

if __name__ == '__main__':
    procesar_todo()
