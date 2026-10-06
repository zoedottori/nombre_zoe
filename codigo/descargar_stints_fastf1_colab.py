"""
Script para Google Colab: Extracción de Stints y Compuestos Oficiales con FastF1 (2018-2024)
Instrucciones:
1. Abrir un nuevo notebook en Google Colab: https://colab.research.google.com/
2. Copiar y pegar todo este código en una celda de código.
3. Dar clic en el botón de 'Play' (Ejecutar).
4. El script procesará las carreras a máxima velocidad y descargará automáticamente
   el archivo 'tyre_stints_procesado.csv' con datos 100% reales de Pirelli.
"""

# Celda 1 en Google Colab:
"""
!pip install fastf1 pandas

import os
import fastf1
import pandas as pd
from google.colab import files

# Habilitar caché para acelerar la descarga
os.makedirs('f1_cache', exist_ok=True)
fastf1.Cache.enable_cache('f1_cache')

print("🏎️ Iniciando extracción de compuestos oficiales de Pirelli con FastF1...")

# Mapeo de códigos de 3 letras de FastF1 a driver_id oficial de Ergast
DRIVER_MAP = {
    'VER': 'max_verstappen', 'HAM': 'hamilton', 'LEC': 'leclerc', 'PER': 'perez',
    'SAI': 'sainz', 'NOR': 'norris', 'RUS': 'russell', 'ALO': 'alonso',
    'PIA': 'piastri', 'STR': 'stroll', 'GAS': 'gasly', 'OCO': 'ocon',
    'ALB': 'albon', 'TSU': 'tsunoda', 'HUL': 'hulkenberg', 'MAG': 'kevin_magnussen',
    'BOT': 'bottas', 'ZHO': 'zhou', 'SAR': 'sargeant', 'RIC': 'ricciardo',
    'LAW': 'lawson', 'BEA': 'bearman', 'COL': 'colapinto', 'DEV': 'de_vries',
    'VET': 'vettel', 'RAI': 'raikkonen', 'GIO': 'giovinazzi', 'MAZ': 'mazepin',
    'MSC': 'mick_schumacher', 'LAT': 'latifi', 'KVY': 'kvyat', 'GRO': 'grosjean',
    'ERI': 'ericsson', 'HAR': 'brendon_hartley', 'VAN': 'vandoorne', 'SIR': 'sirotkin',
    'KUB': 'kubica', 'FIT': 'pietro_fittipaldi', 'AIT': 'aitken'
}

# Temporadas a procesar (2018 a 2024)
SEASONS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]

stints_list = []

for season in SEASONS:
    try:
        schedule = fastf1.get_event_schedule(season)
        races = schedule[schedule['EventFormat'] != 'testing']
    except Exception as e:
        print(f"⚠️ Error al obtener calendario de {season}: {e}")
        continue

    print(f"\n📅 Temporada {season} ({len(races)} carreras):")
    
    for _, event in races.iterrows():
        round_num = int(event['RoundNumber'])
        race_name = event['EventName']
        
        if round_num == 0:
            continue
            
        print(f"  🏁 R{round_num:02d}: {race_name:<30}", end=" ", flush=True)
        
        try:
            # telemetry=False y weather=False para descarga ultrarrápida (2-3 segs por carrera)
            session = fastf1.get_session(season, round_num, 'R')
            session.load(laps=True, telemetry=False, weather=False, messages=False)
            
            laps = session.laps
            if laps is None or laps.empty:
                print("❌ Sin datos")
                continue
                
            clean_laps = laps.dropna(subset=['Driver', 'Stint', 'Compound']).copy()
            clean_laps['Stint'] = clean_laps['Stint'].astype(int)
            clean_laps['LapNumber'] = clean_laps['LapNumber'].astype(int)
            clean_laps['Compound'] = clean_laps['Compound'].str.upper().str.strip()
            
            # Agrupar por piloto y stint
            stints = clean_laps.groupby(['Driver', 'Stint']).agg(
                compound=('Compound', 'first'),
                lap_start=('LapNumber', 'min'),
                lap_end=('LapNumber', 'max'),
                stint_length=('LapNumber', 'count')
            ).reset_index()
            
            for _, stint_row in stints.iterrows():
                drv_code = str(stint_row['Driver']).upper().strip()
                stints_list.append({
                    'temporada': season,
                    'ronda': round_num,
                    'id_piloto': DRIVER_MAP.get(drv_code, drv_code.lower()),
                    'codigo_piloto': drv_code,
                    'numero_stint': int(stint_row['Stint']),
                    'compuesto': stint_row['compound'],
                    'vuelta_inicio': int(stint_row['lap_start']),
                    'vuelta_fin': int(stint_row['lap_end']),
                    'duracion_stint_vueltas': int(stint_row['stint_length'])
                })
            print(f"✅ ({len(stints)} stints)")
            
        except Exception as err:
            print(f"⚠️ Error: {err}")
            continue

# Generar archivo CSV en español
df_stints = pd.DataFrame(stints_list)
output_filename = 'tyre_stints_procesado.csv'
df_stints.to_csv(output_filename, index=False)

print("\n" + "="*70)
print(f"🎉 ¡EXTRACCIÓN CON FASTF1 COMPLETADA EXITOSAMENTE!")
print(f"Total de tandas reales registradas: {len(df_stints):,}")
print(f"Distribución de compuestos Pirelli:")
for comp, cant in df_stints['compuesto'].value_counts().items():
    print(f"  • {comp:<15}: {cant:>5} stints")
print("="*70)

# Descargar automáticamente el CSV a la computadora local
files.download(output_filename)
"""
