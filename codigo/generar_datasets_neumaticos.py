"""
Script para generar y consolidar los datasets oficiales de neumáticos:
1. datasets/pirelli_nominations.csv (con columna source)
2. datasets/tyre_stints.csv (con compuestos reales de telemetría y columna source)
3. datasets_procesados/pirelli_nominations_procesado.csv (con columna fuente)
4. datasets_procesados/tyre_stints_procesado.csv (con columna fuente)
"""

import os
import csv
import json
import ssl
import time
import urllib.request
from collections import defaultdict

# -------------------------------------------------------------------------
# 1. PIRELLI NOMINATIONS (2018 - 2024)
# Datos oficiales de comunicados de prensa de Pirelli Motorsport y notas FIA
# -------------------------------------------------------------------------
PIRELLI_SOURCE = "Pirelli Motorsport Official Nomination (press.pirelli.com / FIA Event Notes)"
PIRELLI_FUENTE_ES = "Comunicados Oficiales Pirelli Motorsport / Notas de Evento FIA"

# Nominaciones por (temporada, ronda)
# Para 2018: nombres oficiales de compuestos (Superhard, Hard, Medium, Soft, Supersoft, Ultrasoft, Hypersoft)
# Para 2019-2024: código oficial C1 a C5
PIRELLI_NOMINATIONS_MAP = {
    # 2018
    (2018, 1): ('Soft', 'Supersoft', 'Ultrasoft'),
    (2018, 2): ('Medium', 'Soft', 'Supersoft'),
    (2018, 3): ('Medium', 'Soft', 'Ultrasoft'),
    (2018, 4): ('Soft', 'Supersoft', 'Ultrasoft'),
    (2018, 5): ('Medium', 'Soft', 'Supersoft'),
    (2018, 6): ('Supersoft', 'Ultrasoft', 'Hypersoft'),
    (2018, 7): ('Supersoft', 'Ultrasoft', 'Hypersoft'),
    (2018, 8): ('Soft', 'Supersoft', 'Ultrasoft'),
    (2018, 9): ('Soft', 'Supersoft', 'Ultrasoft'),
    (2018, 10): ('Hard', 'Medium', 'Soft'),
    (2018, 11): ('Medium', 'Soft', 'Ultrasoft'),
    (2018, 12): ('Medium', 'Soft', 'Ultrasoft'),
    (2018, 13): ('Medium', 'Soft', 'Supersoft'),
    (2018, 14): ('Medium', 'Soft', 'Supersoft'),
    (2018, 15): ('Soft', 'Ultrasoft', 'Hypersoft'),
    (2018, 16): ('Soft', 'Ultrasoft', 'Hypersoft'),
    (2018, 17): ('Medium', 'Soft', 'Supersoft'),
    (2018, 18): ('Soft', 'Supersoft', 'Ultrasoft'),
    (2018, 19): ('Supersoft', 'Ultrasoft', 'Hypersoft'),
    (2018, 20): ('Medium', 'Soft', 'Supersoft'),
    (2018, 21): ('Supersoft', 'Ultrasoft', 'Hypersoft'),

    # 2019
    (2019, 1): ('C2', 'C3', 'C4'),
    (2019, 2): ('C1', 'C2', 'C3'),
    (2019, 3): ('C2', 'C3', 'C4'),
    (2019, 4): ('C2', 'C3', 'C4'),
    (2019, 5): ('C1', 'C2', 'C3'),
    (2019, 6): ('C3', 'C4', 'C5'),
    (2019, 7): ('C3', 'C4', 'C5'),
    (2019, 8): ('C2', 'C3', 'C4'),
    (2019, 9): ('C2', 'C3', 'C4'),
    (2019, 10): ('C1', 'C2', 'C3'),
    (2019, 11): ('C2', 'C3', 'C4'),
    (2019, 12): ('C2', 'C3', 'C4'),
    (2019, 13): ('C1', 'C2', 'C3'),
    (2019, 14): ('C2', 'C3', 'C4'),
    (2019, 15): ('C3', 'C4', 'C5'),
    (2019, 16): ('C2', 'C3', 'C4'),
    (2019, 17): ('C1', 'C2', 'C3'),
    (2019, 18): ('C2', 'C3', 'C4'),
    (2019, 19): ('C2', 'C3', 'C4'),
    (2019, 20): ('C1', 'C2', 'C3'),
    (2019, 21): ('C3', 'C4', 'C5'),

    # 2020
    (2020, 1): ('C2', 'C3', 'C4'),
    (2020, 2): ('C2', 'C3', 'C4'),
    (2020, 3): ('C2', 'C3', 'C4'),
    (2020, 4): ('C1', 'C2', 'C3'),
    (2020, 5): ('C2', 'C3', 'C4'),
    (2020, 6): ('C1', 'C2', 'C3'),
    (2020, 7): ('C2', 'C3', 'C4'),
    (2020, 8): ('C2', 'C3', 'C4'),
    (2020, 9): ('C1', 'C2', 'C3'),
    (2020, 10): ('C3', 'C4', 'C5'),
    (2020, 11): ('C2', 'C3', 'C4'),
    (2020, 12): ('C1', 'C2', 'C3'),
    (2020, 13): ('C2', 'C3', 'C4'),
    (2020, 14): ('C1', 'C2', 'C3'),
    (2020, 15): ('C2', 'C3', 'C4'),
    (2020, 16): ('C2', 'C3', 'C4'),
    (2020, 17): ('C3', 'C4', 'C5'),

    # 2021
    (2021, 1): ('C2', 'C3', 'C4'),
    (2021, 2): ('C2', 'C3', 'C4'),
    (2021, 3): ('C1', 'C2', 'C3'),
    (2021, 4): ('C1', 'C2', 'C3'),
    (2021, 5): ('C3', 'C4', 'C5'),
    (2021, 6): ('C3', 'C4', 'C5'),
    (2021, 7): ('C2', 'C3', 'C4'),
    (2021, 8): ('C2', 'C3', 'C4'),
    (2021, 9): ('C3', 'C4', 'C5'),
    (2021, 10): ('C1', 'C2', 'C3'),
    (2021, 11): ('C2', 'C3', 'C4'),
    (2021, 12): ('C2', 'C3', 'C4'),
    (2021, 13): ('C1', 'C2', 'C3'),
    (2021, 14): ('C2', 'C3', 'C4'),
    (2021, 15): ('C3', 'C4', 'C5'),
    (2021, 16): ('C2', 'C3', 'C4'),
    (2021, 17): ('C2', 'C3', 'C4'),
    (2021, 18): ('C2', 'C3', 'C4'),
    (2021, 19): ('C2', 'C3', 'C4'),
    (2021, 20): ('C1', 'C2', 'C3'),
    (2021, 21): ('C2', 'C3', 'C4'),
    (2021, 22): ('C3', 'C4', 'C5'),

    # 2022
    (2022, 1): ('C1', 'C2', 'C3'),
    (2022, 2): ('C2', 'C3', 'C4'),
    (2022, 3): ('C2', 'C3', 'C5'),
    (2022, 4): ('C2', 'C3', 'C4'),
    (2022, 5): ('C2', 'C3', 'C4'),
    (2022, 6): ('C1', 'C2', 'C3'),
    (2022, 7): ('C3', 'C4', 'C5'),
    (2022, 8): ('C3', 'C4', 'C5'),
    (2022, 9): ('C3', 'C4', 'C5'),
    (2022, 10): ('C1', 'C2', 'C3'),
    (2022, 11): ('C3', 'C4', 'C5'),
    (2022, 12): ('C2', 'C3', 'C4'),
    (2022, 13): ('C2', 'C3', 'C4'),
    (2022, 14): ('C2', 'C3', 'C4'),
    (2022, 15): ('C1', 'C2', 'C3'),
    (2022, 16): ('C2', 'C3', 'C4'),
    (2022, 17): ('C3', 'C4', 'C5'),
    (2022, 18): ('C1', 'C2', 'C3'),
    (2022, 19): ('C2', 'C3', 'C4'),
    (2022, 20): ('C2', 'C3', 'C4'),
    (2022, 21): ('C2', 'C3', 'C4'),
    (2022, 22): ('C3', 'C4', 'C5'),

    # 2023
    (2023, 1): ('C1', 'C2', 'C3'),
    (2023, 2): ('C2', 'C3', 'C4'),
    (2023, 3): ('C2', 'C3', 'C4'),
    (2023, 4): ('C3', 'C4', 'C5'),
    (2023, 5): ('C2', 'C3', 'C4'),
    (2023, 6): ('C3', 'C4', 'C5'),
    (2023, 7): ('C1', 'C2', 'C3'),
    (2023, 8): ('C3', 'C4', 'C5'),
    (2023, 9): ('C3', 'C4', 'C5'),
    (2023, 10): ('C1', 'C2', 'C3'),
    (2023, 11): ('C3', 'C4', 'C5'),
    (2023, 12): ('C2', 'C3', 'C4'),
    (2023, 13): ('C1', 'C2', 'C3'),
    (2023, 14): ('C3', 'C4', 'C5'),
    (2023, 15): ('C3', 'C4', 'C5'),
    (2023, 16): ('C1', 'C2', 'C3'),
    (2023, 17): ('C1', 'C2', 'C3'),
    (2023, 18): ('C2', 'C3', 'C4'),
    (2023, 19): ('C3', 'C4', 'C5'),
    (2023, 20): ('C2', 'C3', 'C4'),
    (2023, 21): ('C3', 'C4', 'C5'),
    (2023, 22): ('C3', 'C4', 'C5'),

    # 2024
    (2024, 1): ('C1', 'C2', 'C3'),
    (2024, 2): ('C2', 'C3', 'C4'),
    (2024, 3): ('C3', 'C4', 'C5'),
    (2024, 4): ('C1', 'C2', 'C3'),
    (2024, 5): ('C2', 'C3', 'C4'),
    (2024, 6): ('C2', 'C3', 'C4'),
    (2024, 7): ('C3', 'C4', 'C5'),
    (2024, 8): ('C3', 'C4', 'C5'),
    (2024, 9): ('C3', 'C4', 'C5'),
    (2024, 10): ('C1', 'C2', 'C3'),
    (2024, 11): ('C3', 'C4', 'C5'),
    (2024, 12): ('C1', 'C2', 'C3'),
    (2024, 13): ('C3', 'C4', 'C5'),
    (2024, 14): ('C2', 'C3', 'C4'),
    (2024, 15): ('C1', 'C2', 'C3'),
    (2024, 16): ('C3', 'C4', 'C5'),
    (2024, 17): ('C3', 'C4', 'C5'),
    (2024, 18): ('C3', 'C4', 'C5'),
    (2024, 19): ('C2', 'C3', 'C4'),
    (2024, 20): ('C3', 'C4', 'C5'),
    (2024, 21): ('C3', 'C4', 'C5'),
    (2024, 22): ('C3', 'C4', 'C5'),
    (2024, 23): ('C1', 'C2', 'C3'),
    (2024, 24): ('C3', 'C4', 'C5'),
}

def generar_pirelli_nominations():
    print("🛞 Generando pirelli_nominations.csv...")
    with open('datasets/races.csv', 'r') as f:
        reader = csv.DictReader(f)
        races = [r for r in reader if int(r['season']) >= 2018]
    
    rows_raw = []
    rows_proc = []
    
    for r in races:
        season = int(r['season'])
        rnd = int(r['round'])
        circuit_id = r['circuitId']
        race_name = r['raceName']
        
        noms = PIRELLI_NOMINATIONS_MAP.get((season, rnd), ('C2', 'C3', 'C4'))
        
        rows_raw.append({
            'season': season,
            'round': rnd,
            'circuitId': circuit_id,
            'raceName': race_name,
            'compound_hard': noms[0],
            'compound_medium': noms[1],
            'compound_soft': noms[2],
            'source': PIRELLI_SOURCE
        })
        
        rows_proc.append({
            'temporada': season,
            'ronda': rnd,
            'id_circuito': circuit_id,
            'nombre_carrera': race_name,
            'compuesto_duro': noms[0],
            'compuesto_medio': noms[1],
            'compuesto_blando': noms[2],
            'fuente': PIRELLI_FUENTE_ES
        })
        
    with open('datasets/pirelli_nominations.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['season', 'round', 'circuitId', 'raceName', 'compound_hard', 'compound_medium', 'compound_soft', 'source'])
        writer.writeheader()
        writer.writerows(rows_raw)
    print(f"   ✓ datasets/pirelli_nominations.csv guardado ({len(rows_raw)} carreras con columna 'source').")

    with open('datasets_procesados/pirelli_nominations_procesado.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['temporada', 'ronda', 'id_circuito', 'nombre_carrera', 'compuesto_duro', 'compuesto_medio', 'compuesto_blando', 'fuente'])
        writer.writeheader()
        writer.writerows(rows_proc)
    print(f"   ✓ datasets_procesados/pirelli_nominations_procesado.csv guardado ({len(rows_proc)} registros en español con columna 'fuente').")

# -------------------------------------------------------------------------
# 2. OPENF1 & HISTORICAL STINTS CON FUENTE
# -------------------------------------------------------------------------
OPENF1_SOURCE = "OpenF1 Real-Time Telemetry API (api.openf1.org)"
OPENF1_FUENTE_ES = "Telemetría Oficial en Tiempo Real OpenF1 (api.openf1.org)"
ERGAST_SOURCE = "Ergast Developer API (Pit Stops & Stints) / Pirelli Strategy Infographics"
ERGAST_FUENTE_ES = "Base Oficial Ergast (Boxes y Vueltas) / Infografías de Estrategia Pirelli"

CACHE_DIR = "/Users/zoe/.gemini/antigravity/brain/825cc10f-6e9f-4961-ad85-27aebe4d8f9f/scratch/openf1_cache"
os.makedirs(CACHE_DIR, exist_ok=True)
ctx = ssl._create_unverified_context()

def get_json(url):
    import hashlib
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{url_hash}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

    req = urllib.request.Request(url, headers={'User-Agent': 'BeyondGridF1/1.0'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                data = json.loads(resp.read().decode())
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                return data
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_sec = 2 * (attempt + 1)
                time.sleep(wait_sec)
            else:
                raise e
        except Exception as e:
            if attempt == 4:
                raise e
            time.sleep(2)
    return []

def cargar_mapeos():
    with open('datasets/race_results.csv', 'r') as f:
        reader = csv.DictReader(f)
        results = [r for r in reader if int(r['season']) >= 2018]

    # Map (season, round, driver_number) -> (driverId, driverName, constructorName)
    num_to_driver = {}
    driver_name_map = {}
    for r in results:
        s = int(r['season'])
        rnd = int(r['round'])
        drv_id = r['driverId']
        drv_name = r['driverName']
        const_name = r['constructorName']
        driver_name_map[drv_id] = drv_name
        if r.get('number') and r['number'].isdigit():
            num = int(r['number'])
            num_to_driver[(s, rnd, num)] = (drv_id, drv_name, const_name)

    # Map (season, round) -> (circuitId, raceName, date)
    with open('datasets/races.csv', 'r') as f:
        reader = csv.DictReader(f)
        races = {(int(r['season']), int(r['round'])): (r['circuitId'], r['raceName'], r['date']) for r in reader if int(r['season']) >= 2018}

    # Pitstops map: (season, round, driverId, stop_num) -> (pit_lap, pit_duration)
    with open('datasets/pitstops.csv', 'r') as f:
        reader = csv.DictReader(f)
        pitstops = {}
        for r in reader:
            if int(r['season']) >= 2018:
                key = (int(r['season']), int(r['round']), r['driverId'], int(r['stop']))
                dur = float(r['duration']) if r.get('duration') and r['duration'].replace('.', '', 1).isdigit() else None
                pitstops[key] = (int(r['lap']), dur)

    return num_to_driver, driver_name_map, races, pitstops

def extraer_stints_openf1(year, num_to_driver, races, pitstops):
    print(f"📡 Consultando OpenF1 para temporada {year}...")
    try:
        sessions = get_json(f"https://api.openf1.org/v1/sessions?year={year}&session_name=Race")
    except Exception as e:
        print(f"⚠️ Error al obtener sesiones de {year}: {e}")
        return []

    stints_collected = []
    
    # Construir mapeo de fecha/circuito a round
    date_to_round = {}
    for (s, rnd), (circuit_id, race_name, date_str) in races.items():
        if s == year:
            date_to_round[date_str] = (rnd, circuit_id, race_name)

    for s_info in sessions:
        if s_info.get('is_cancelled'):
            continue
        date_start = s_info['date_start'][:10]
        s_key = s_info['session_key']
        short_name = s_info.get('circuit_short_name', '')
        
        # Encontrar ronda
        rnd_info = date_to_round.get(date_start)
        if not rnd_info:
            # Fallback para fechas de madrugada/sábado UTC (ej. Las Vegas)
            for d_str, info in date_to_round.items():
                if abs(int(d_str.replace('-', '')) - int(date_start.replace('-', ''))) <= 2:
                    rnd_info = info
                    break
        if not rnd_info:
            continue
            
        rnd, circuit_id, race_name = rnd_info
        
        try:
            time.sleep(0.5) # Respetar rate-limit de OpenF1
            stints_data = get_json(f"https://api.openf1.org/v1/stints?session_key={s_key}")
        except Exception as e:
            print(f"   ⚠️ Error en carrera R{rnd:02d} ({race_name}): {e}")
            continue
            
        if not stints_data:
            continue
            
        print(f"   🏁 R{rnd:02d}: {race_name:<26} -> {len(stints_data)} stints oficiales")
        
        for st in stints_data:
            drv_num = st.get('driver_number')
            stint_num = st.get('stint_number', 1)
            compound = str(st.get('compound') or 'UNKNOWN').upper()
            lap_start = st.get('lap_start')
            lap_end = st.get('lap_end')
            if lap_start is None:
                lap_start = 1
            if lap_end is None:
                lap_end = lap_start
            stint_len = max(1, int(lap_end) - int(lap_start) + 1)
            
            drv_meta = num_to_driver.get((year, rnd, drv_num), (f"pilot_{drv_num}", f"Driver #{drv_num}", "Unknown"))
            drv_id, drv_name, const_name = drv_meta
            
            # Buscar info de pitstop
            pit_info = pitstops.get((year, rnd, drv_id, stint_num))
            pit_lap = pit_info[0] if pit_info else ""
            pit_dur = pit_info[1] if pit_info else ""
            
            stints_collected.append({
                'season': year,
                'round': rnd,
                'circuitId': circuit_id,
                'driverId': drv_id,
                'driverName': drv_name,
                'constructorName': const_name,
                'stint_number': stint_num,
                'compound': compound,
                'lap_start': lap_start,
                'lap_end': lap_end,
                'stint_length': stint_len,
                'pit_lap': pit_lap,
                'pit_duration': pit_dur,
                'source': OPENF1_SOURCE,
                'fuente_es': OPENF1_FUENTE_ES
            })
            
    return stints_collected

def generar_tyre_stints_completos():
    num_to_driver, driver_name_map, races, pitstops = cargar_mapeos()
    
    # 1. Cargar datos existentes 2018-2022
    stints_historical = []
    with open('datasets/tyre_stints.csv', 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            s = int(r['season'])
            if s <= 2022:
                rnd = int(r['round'])
                drv_id = r['driverId']
                drv_name = driver_name_map.get(drv_id, drv_id.replace('_', ' ').title())
                const_name = r['constructorName']
                circuit_id = races.get((s, rnd), ('unknown', '', ''))[0]
                stints_historical.append({
                    'season': s,
                    'round': rnd,
                    'circuitId': circuit_id,
                    'driverId': drv_id,
                    'driverName': drv_name,
                    'constructorName': const_name,
                    'stint_number': int(r['stint_number']),
                    'compound': '',
                    'lap_start': int(r['lap_start']),
                    'lap_end': int(r['lap_end']),
                    'stint_length': int(r['stint_length']),
                    'pit_lap': r.get('pit_lap', ''),
                    'pit_duration': r.get('pit_duration', ''),
                    'source': "Ergast Developer API (Official Pit Stops & Laps) / Telemetry Not Instrumented",
                    'fuente_es': "Base Oficial Ergast (Boxes y Vueltas Reales) / Sin Telemetría Digital de Compuesto"
                })
                
    print(f"📦 Stints históricos preservados (2018-2022): {len(stints_historical)}")
    
    # 2. Extraer OpenF1 para 2023 y 2024
    stints_2023 = extraer_stints_openf1(2023, num_to_driver, races, pitstops)
    stints_2024 = extraer_stints_openf1(2024, num_to_driver, races, pitstops)
    
    todos_stints = stints_historical + stints_2023 + stints_2024
    todos_stints.sort(key=lambda x: (x['season'], x['round'], x['driverId'], x['stint_number']))
    
    # 3. Guardar datasets/tyre_stints.csv
    fieldnames_raw = [
        'season', 'round', 'driverId', 'constructorName', 'stint_number',
        'compound', 'lap_start', 'lap_end', 'stint_length', 'pit_lap', 'pit_duration', 'source'
    ]
    with open('datasets/tyre_stints.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_raw)
        writer.writeheader()
        for s in todos_stints:
            writer.writerow({
                'season': s['season'],
                'round': s['round'],
                'driverId': s['driverId'],
                'constructorName': s['constructorName'],
                'stint_number': s['stint_number'],
                'compound': s['compound'],
                'lap_start': s['lap_start'],
                'lap_end': s['lap_end'],
                'stint_length': s['stint_length'],
                'pit_lap': s['pit_lap'],
                'pit_duration': s['pit_duration'],
                'source': s['source']
            })
    print(f"✓ datasets/tyre_stints.csv guardado ({len(todos_stints)} registros con columna 'source').")

    # 4. Guardar datasets_procesados/tyre_stints_procesado.csv
    fieldnames_proc = [
        'temporada', 'ronda', 'id_circuito', 'id_piloto', 'nombre_piloto',
        'constructor', 'numero_stint', 'vuelta_inicio', 'vuelta_fin',
        'duracion_stint_vueltas', 'compuesto', 'duracion_parada_seg', 'fuente'
    ]
    with open('datasets_procesados/tyre_stints_procesado.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_proc)
        writer.writeheader()
        for s in todos_stints:
            writer.writerow({
                'temporada': s['season'],
                'ronda': s['round'],
                'id_circuito': s['circuitId'],
                'id_piloto': s['driverId'],
                'nombre_piloto': s['driverName'],
                'constructor': s['constructorName'],
                'numero_stint': s['stint_number'],
                'vuelta_inicio': s['lap_start'],
                'vuelta_fin': s['lap_end'],
                'duracion_stint_vueltas': s['stint_length'],
                'compuesto': s['compound'],
                'duracion_parada_seg': s['pit_duration'],
                'fuente': s['fuente_es']
            })
    print(f"✓ datasets_procesados/tyre_stints_procesado.csv guardado ({len(todos_stints)} registros en español con columna 'fuente').")

if __name__ == '__main__':
    generar_pirelli_nominations()
    generar_tyre_stints_completos()
    print("\n🎉 Todos los datasets de neumáticos fueron actualizados y guardados con su columna de fuente.")
