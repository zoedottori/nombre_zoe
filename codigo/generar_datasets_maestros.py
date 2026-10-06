"""
Generador de las Tres Tablas Maestras Oficiales para BeyondGrid AI & CircuitDNA
Ubicación de salida: datasets_procesados/datasets_maestros/

Estructura de las 3 Tablas Maestras:
1. tabla_maestra_carreras_pilotos.csv  (Granularidad: Piloto x Carrera - 3.458 filas)
   -> La tabla reina para los 3 patrones de la Entrega 1 (Pista vs Auto, Clima vs Grilla, Consistencia Metronómica).
2. tabla_maestra_stints_estrategia.csv (Granularidad: Tanda de Neumático - 9.035 filas)
   -> La tabla de estrategia con 'motivo_parada' empírico (SC, VSC, Lluvia, Vuelta Rápida, Daño, Degradación).
3. tabla_maestra_circuitos_carreras.csv (Granularidad: Gran Premio / Circuito - 173 filas)
   -> La tabla macro para el mapa de circuitos, clusters de pistas gemelas y predictibilidad.
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

def clasificar_arquetipo_pista(densidad):
    if densidad >= 3.5:
        return 'Alta Densidad / Trabado'
    elif densidad <= 2.8:
        return 'Baja Densidad / Rapido'
    else:
        return 'Media Densidad / Equilibrado'

def generar_maestros():
    print("=" * 80)
    print("🚀 GENERACIÓN DE LAS TRES TABLAS MAESTRAS EN datasets_maestros/")
    print("=" * 80)

    out_dir = 'datasets_procesados/datasets_maestros'
    os.makedirs(out_dir, exist_ok=True)

    # 1. Carga de datos procesados base
    print("📥 Cargando datasets procesados oficiales...")
    tm_base = pd.read_csv('datasets_procesados/tabla_maestra_confiable.csv')
    stints_base = pd.read_csv('datasets_procesados/tyre_stints_procesado.csv')
    qualy = pd.read_csv('datasets_procesados/qualifying_results_procesado.csv')
    nom = pd.read_csv('datasets_procesados/pirelli_nominations_procesado.csv')
    sc = pd.read_csv('datasets_procesados/safety_cars_procesado.csv')
    vsc = pd.read_csv('datasets_procesados/virtual_safety_cars_procesado.csv')
    rf = pd.read_csv('datasets_procesados/red_flags_procesado.csv')
    sprint = pd.read_csv('datasets_procesados/sprint_results_procesado.csv')
    races = pd.read_csv('datasets_procesados/races_procesado.csv')

    # Llaves de carrera para cruces de incidentes
    races['clave_carrera'] = races['temporada'].astype(str) + ' ' + races['nombre_carrera'].astype(str)
    race_to_key = {(int(r['temporada']), int(r['ronda'])): r['clave_carrera'] for _, r in races.iterrows()}

    # Incidentes agregados por carrera
    sc_counts = sc['carrera'].value_counts().to_dict()
    vsc_counts = vsc['carrera'].value_counts().to_dict()
    rf_counts = rf['carrera'].value_counts().to_dict()

    # Intervalos de SC y VSC para motivo_parada
    sc_intervals = {}
    for _, row in sc.iterrows():
        rk = str(row['carrera']).strip()
        if pd.notna(row['vuelta_despliegue']):
            dep = float(row['vuelta_despliegue'])
            ret = float(row['vuelta_reingreso']) if pd.notna(row['vuelta_reingreso']) else dep + float(row['vueltas_completas'] or 3)
            sc_intervals.setdefault(rk, []).append((dep, ret))

    vsc_intervals = {}
    for _, row in vsc.iterrows():
        rk = str(row['carrera']).strip()
        if pd.notna(row['vuelta_despliegue']):
            dep = float(row['vuelta_despliegue'])
            ret = float(row['vuelta_reingreso']) if pd.notna(row['vuelta_reingreso']) else dep + float(row['vueltas_completas'] or 2)
            vsc_intervals.setdefault(rk, []).append((dep, ret))

    # -------------------------------------------------------------------------
    # TABLA MAESTRA 1: tabla_maestra_carreras_pilotos.csv
    # -------------------------------------------------------------------------
    print("\n🏆 1/3 Construyendo tabla_maestra_carreras_pilotos.csv...")

    # Resumen de compuestos de stints por piloto en cada carrera
    stints_sorted = stints_base.sort_values(['temporada', 'ronda', 'id_piloto', 'numero_stint'])
    
    # Agrupar stints en secuencias
    stint_seq_map = {}
    stint_max_len_map = {}
    for (s, r, d), group in stints_sorted.groupby(['temporada', 'ronda', 'id_piloto']):
        comps = [c for c in group['compuesto'] if pd.notna(c) and str(c).strip() != '']
        stint_seq_map[(s, r, d)] = ' -> '.join(comps) if comps else ''
        stint_max_len_map[(s, r, d)] = int(group['duracion_stint_vueltas'].max())

    # Qualy merge
    q_sub = qualy[['temporada', 'ronda', 'id_piloto', 'posicion', 'q3']].rename(columns={
        'posicion': 'posicion_qualy',
        'q3': 'tiempo_q3'
    })

    # Nominaciones Pirelli
    nom_sub = nom[['temporada', 'ronda', 'compuesto_duro', 'compuesto_medio', 'compuesto_blando']]

    # Sprints
    sp_sub = sprint[['temporada', 'ronda', 'id_piloto', 'posicion', 'puntos']].rename(columns={
        'posicion': 'posicion_sprint',
        'puntos': 'puntos_sprint'
    })

    m1 = tm_base.copy()
    m1 = m1.merge(q_sub, on=['temporada', 'ronda', 'id_piloto'], how='left')
    m1['posicion_qualy'] = m1['posicion_qualy'].fillna(m1['posicion_largada']).astype(int)
    m1['tiempo_q3'] = m1['tiempo_q3'].fillna('')

    m1 = m1.merge(nom_sub, on=['temporada', 'ronda'], how='left')
    m1['compuesto_duro'] = m1['compuesto_duro'].fillna('')
    m1['compuesto_medio'] = m1['compuesto_medio'].fillna('')
    m1['compuesto_blando'] = m1['compuesto_blando'].fillna('')

    # Mapear secuencia de compuestos
    m1['secuencia_compuestos'] = [stint_seq_map.get((int(r['temporada']), int(r['ronda']), str(r['id_piloto'])), '') for _, r in m1.iterrows()]
    m1['stint_mas_largo_vueltas'] = [stint_max_len_map.get((int(r['temporada']), int(r['ronda']), str(r['id_piloto'])), 0) for _, r in m1.iterrows()]

    # Mapear incidentes del GP
    m1['clave_carrera'] = [race_to_key.get((int(r['temporada']), int(r['ronda'])), '') for _, r in m1.iterrows()]
    m1['despliegues_safety_car'] = m1['clave_carrera'].map(sc_counts).fillna(0).astype(int)
    m1['despliegues_vsc'] = m1['clave_carrera'].map(vsc_counts).fillna(0).astype(int)
    m1['hubo_bandera_roja'] = (m1['clave_carrera'].map(rf_counts).fillna(0) > 0).astype(int)

    # Sprint merge
    m1 = m1.merge(sp_sub, on=['temporada', 'ronda', 'id_piloto'], how='left')
    m1['posicion_sprint'] = m1['posicion_sprint'].fillna(0).astype(int)
    m1['puntos_sprint'] = m1['puntos_sprint'].fillna(0.0).round(1)

    m1['arquetipo_pista'] = m1['densidad_curvas_por_km'].apply(clasificar_arquetipo_pista)
    m1['fuente'] = "BeyondGrid AI Tabla Maestra / FIA Timing & Ergast & OpenF1"

    cols_m1 = [
        'temporada', 'ronda', 'fecha', 'id_circuito', 'nombre_circuito', 'pais', 'nombre_carrera', 'arquetipo_pista',
        'id_piloto', 'nombre_piloto', 'constructor',
        'posicion_qualy', 'posicion_largada', 'posicion_final', 'puestos_ganados', 'puntos_obtenidos',
        'vueltas_completadas', 'estado_carrera',
        'posicion_sprint', 'puntos_sprint',
        'total_paradas_boxes', 'primera_vuelta_parada', 'duracion_promedio_boxes_seg',
        'secuencia_compuestos', 'stint_mas_largo_vueltas',
        'temp_aire_c', 'temp_pista_c', 'humedad_pct', 'hubo_lluvia', 'condicion_clima',
        'longitud_km', 'cantidad_curvas', 'densidad_curvas_por_km',
        'vueltas_limpias_analizadas', 'ritmo_mediana_seg', 'consistencia_ritmo_seg', 'mejor_vuelta_seg', 'velocidad_media_estimada_kmh',
        'compuesto_duro', 'compuesto_medio', 'compuesto_blando',
        'despliegues_safety_car', 'despliegues_vsc', 'hubo_bandera_roja',
        'fuente'
    ]
    m1_final = m1[cols_m1].sort_values(['temporada', 'ronda', 'posicion_final'])
    p1_path = f"{out_dir}/tabla_maestra_carreras_pilotos.csv"
    m1_final.to_csv(p1_path, index=False)
    print(f"   ✓ {p1_path} guardado ({len(m1_final)} filas x {len(cols_m1)} columnas).")

    # -------------------------------------------------------------------------
    # TABLA MAESTRA 2: tabla_maestra_stints_estrategia.csv
    # -------------------------------------------------------------------------
    print("\n🛞 2/3 Construyendo tabla_maestra_stints_estrategia.csv...")

    tot_laps_map = m1_final.groupby(['temporada', 'ronda'])['vueltas_completadas'].max().to_dict()
    max_stint_map = stints_base.groupby(['temporada', 'ronda', 'id_piloto'])['numero_stint'].max().to_dict()

    m2 = stints_base.copy()
    m2['clave_carrera'] = [race_to_key.get((int(r['temporada']), int(r['ronda'])), '') for _, r in m2.iterrows()]

    # Calcular motivo_parada
    motivos = []
    for _, row in m2.iterrows():
        s = int(row['temporada'])
        r = int(row['ronda'])
        d = str(row['id_piloto'])
        num_st = int(row['numero_stint'])
        max_st = max_stint_map.get((s, r, d), 1)

        if num_st == max_st:
            motivos.append('Fin de Carrera')
            continue

        pit_lap = float(row['vuelta_fin'])
        rk = row['clave_carrera']

        in_sc = any((dep - 1) <= pit_lap <= (ret + 1) for dep, ret in sc_intervals.get(rk, []))
        in_vsc = any((dep - 1) <= pit_lap <= (ret + 1) for dep, ret in vsc_intervals.get(rk, []))
        race_laps = tot_laps_map.get((s, r), 55)
        pit_dur = float(row['duracion_parada_seg']) if pd.notna(row['duracion_parada_seg']) else 0.0

        if in_sc:
            motivos.append('Cheap Pit Stop (Safety Car)')
        elif in_vsc:
            motivos.append('Cheap Pit Stop (Virtual Safety Car)')
        elif pit_lap >= (race_laps - 4) and row['compuesto'] in ['SOFT', '']:
            motivos.append('Caza de Vuelta Rapida')
        elif (pit_dur > 32.0 and pit_dur > 0) or (pit_lap <= 4 and not in_sc):
            motivos.append('Dano / Pinchadura / Imprevisto')
        else:
            motivos.append('Degradacion Regular')

    m2['motivo_parada'] = motivos

    # Enriquecer con clima y trazado
    weather_info = pd.read_csv('datasets_procesados/race_weather_procesado.csv')[['temporada', 'ronda', 'temp_pista_c', 'temp_aire_c', 'hubo_lluvia', 'condicion_clima']]
    circuit_info = pd.read_csv('datasets_procesados/circuit_characteristics_procesado.csv')[['id_circuito', 'longitud_km', 'cantidad_curvas', 'densidad_curvas_por_km']]

    m2 = m2.merge(weather_info, on=['temporada', 'ronda'], how='left')
    m2 = m2.merge(circuit_info, on='id_circuito', how='left')
    m2 = m2.merge(nom_sub, on=['temporada', 'ronda'], how='left')

    # Identificar rol de compuesto si hay telemetría (DURO, MEDIO, BLANDO)
    def asignar_rol_compuesto(row):
        cmp = str(row['compuesto']).upper()
        if not cmp or cmp in ['UNKNOWN', 'NAN']:
            return 'No Instrumentado'
        if cmp in ['INTERMEDIATE', 'WET']:
            return cmp
        if cmp == row['compuesto_duro']:
            return 'DURO'
        elif cmp == row['compuesto_medio']:
            return 'MEDIO'
        elif cmp == row['compuesto_blando']:
            return 'BLANDO'
        return cmp

    m2['rol_compuesto_pirelli'] = m2.apply(asignar_rol_compuesto, axis=1)

    cols_m2 = [
        'temporada', 'ronda', 'id_circuito', 'id_piloto', 'nombre_piloto', 'constructor',
        'numero_stint', 'vuelta_inicio', 'vuelta_fin', 'duracion_stint_vueltas',
        'compuesto', 'rol_compuesto_pirelli', 'duracion_parada_seg', 'motivo_parada',
        'temp_pista_c', 'temp_aire_c', 'hubo_lluvia', 'condicion_clima',
        'densidad_curvas_por_km', 'longitud_km',
        'fuente'
    ]
    m2_final = m2[cols_m2].sort_values(['temporada', 'ronda', 'id_piloto', 'numero_stint'])
    p2_path = f"{out_dir}/tabla_maestra_stints_estrategia.csv"
    m2_final.to_csv(p2_path, index=False)
    print(f"   ✓ {p2_path} guardado ({len(m2_final)} filas x {len(cols_m2)} columnas).")

    # -------------------------------------------------------------------------
    # TABLA MAESTRA 3: tabla_maestra_circuitos_carreras.csv
    # -------------------------------------------------------------------------
    print("\n🏁 3/3 Construyendo tabla_maestra_circuitos_carreras.csv...")

    gp_rows = []
    for (s, r), g in m1_final.groupby(['temporada', 'ronda']):
        row0 = g.iloc[0]
        
        # Ganador
        p1_driver = g[g['posicion_final'] == 1]
        ganador_piloto = p1_driver['nombre_piloto'].values[0] if len(p1_driver) > 0 else ''
        ganador_constructor = p1_driver['constructor'].values[0] if len(p1_driver) > 0 else ''
        
        # Poleman
        pole_driver = g[g['posicion_qualy'] == 1]
        pole_piloto = pole_driver['nombre_piloto'].values[0] if len(pole_driver) > 0 else ''
        pole_constructor = pole_driver['constructor'].values[0] if len(pole_driver) > 0 else ''
        
        # Vuelta rápida
        g_laps = g[g['mejor_vuelta_seg'] > 0]
        if len(g_laps) > 0:
            fastest_row = g_laps.sort_values('mejor_vuelta_seg').iloc[0]
            fl_driver = fastest_row['nombre_piloto']
            fl_time = fastest_row['mejor_vuelta_seg']
        else:
            fl_driver = ''
            fl_time = 0.0

        # Predictibilidad: correlación Pearson qualy vs final
        valid_corr = g[(g['posicion_largada'] > 0) & (g['posicion_final'] > 0)]
        if len(valid_corr) >= 10:
            r_corr = round(valid_corr['posicion_largada'].corr(valid_corr['posicion_final']), 3)
        else:
            r_corr = np.nan

        # Volatilidad media de posiciones
        volatilidad = round(g['puestos_ganados'].abs().mean(), 2)
        prom_paradas = round(g['total_paradas_boxes'].mean(), 2)
        total_paradas = int(g['total_paradas_boxes'].sum())
        total_abandonos = int(((g['estado_carrera'] != 'FINISHED') & (~g['estado_carrera'].str.startswith('+'))).sum())

        gp_rows.append({
            'temporada': s,
            'ronda': r,
            'fecha': row0['fecha'],
            'id_circuito': row0['id_circuito'],
            'nombre_circuito': row0['nombre_circuito'],
            'pais': row0['pais'],
            'nombre_carrera': row0['nombre_carrera'],
            'arquetipo_pista': row0['arquetipo_pista'],
            'longitud_km': row0['longitud_km'],
            'cantidad_curvas': row0['cantidad_curvas'],
            'densidad_curvas_por_km': row0['densidad_curvas_por_km'],
            'temp_aire_c': row0['temp_aire_c'],
            'temp_pista_c': row0['temp_pista_c'],
            'humedad_pct': row0['humedad_pct'],
            'hubo_lluvia': row0['hubo_lluvia'],
            'condicion_clima': row0['condicion_clima'],
            'piloto_ganador': ganador_piloto,
            'constructor_ganador': ganador_constructor,
            'piloto_pole': pole_piloto,
            'constructor_pole': pole_constructor,
            'piloto_vuelta_rapida': fl_driver,
            'tiempo_vuelta_rapida_seg': fl_time,
            'promedio_paradas_carrera': prom_paradas,
            'total_paradas_carrera': total_paradas,
            'total_abandonos': total_abandonos,
            'volatilidad_puestos_promedio': volatilidad,
            'correlacion_qualy_carrera': r_corr,
            'compuesto_duro': row0['compuesto_duro'],
            'compuesto_medio': row0['compuesto_medio'],
            'compuesto_blando': row0['compuesto_blando'],
            'despliegues_safety_car': row0['despliegues_safety_car'],
            'despliegues_vsc': row0['despliegues_vsc'],
            'hubo_bandera_roja': row0['hubo_bandera_roja'],
            'fuente': "BeyondGrid AI Resumen de Gran Premio / FIA Official Data"
        })

    m3_final = pd.DataFrame(gp_rows).sort_values(['temporada', 'ronda'])
    p3_path = f"{out_dir}/tabla_maestra_circuitos_carreras.csv"
    m3_final.to_csv(p3_path, index=False)
    print(f"   ✓ {p3_path} guardado ({len(m3_final)} filas x {len(m3_final.columns)} columnas).")

    print("\n" + "=" * 80)
    print("✨ ¡LAS TRES TABLAS MAESTRAS FUERON CREADAS CON ÉXITO EN datasets_maestros/!")
    print("=" * 80)

if __name__ == '__main__':
    generar_maestros()
