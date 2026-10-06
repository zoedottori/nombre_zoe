"""
Script de procesamiento de datos para BeyondGrid AI
Calcula la Posición Esperada (xP), el Delta de Rendimiento y la Comparación Intra-Equipo.
"""

import pandas as pd
import numpy as np
import os

def procesar_metricas_f1():
    print("Cargando datasets...")
    results = pd.read_csv('datasets/race_results.csv')
    races = pd.read_csv('datasets/races.csv')
    qualifying = pd.read_csv('datasets/qualifying_results.csv')
    circuits = pd.read_csv('datasets/circuits.csv')
    
    # Normalizar tipos
    for df in [results, races, qualifying]:
        df['season'] = pd.to_numeric(df['season'], errors='coerce')
        df['round'] = pd.to_numeric(df['round'], errors='coerce')
    
    results['position_num'] = pd.to_numeric(results['position'], errors='coerce')
    results['grid_num'] = pd.to_numeric(results['grid'], errors='coerce')
    results['points_num'] = pd.to_numeric(results['points'], errors='coerce')
    
    # Filtrar era moderna (2018 a 2024)
    results_mod = results[results['season'] >= 2018].copy()
    
    # Enlazar con carreras y circuitos
    races_sub = races[['season', 'round', 'raceName', 'circuitId', 'date']]
    merged = results_mod.merge(races_sub, on=['season', 'round'], how='left')
    merged = merged.merge(circuits[['circuitId', 'circuitName', 'country']], on='circuitId', how='left')
    
    # 1. Baseline de rendimiento del constructor por temporada
    constructor_baseline = merged[merged['position_num'].notna()].groupby(
        ['season', 'constructorName']
    )['position_num'].transform('mean')
    merged['constructor_baseline'] = constructor_baseline.round(2)
    
    # 2. Posición Esperada (xP)
    # Modelo base: 60% peso de la largada (grid) + 40% del nivel medio del coche en la temporada
    # Si grid es 0 (largada desde pitlane), usamos 20
    grid_imputed = merged['grid_num'].replace(0, 20).fillna(20)
    merged['expected_position'] = (0.60 * grid_imputed + 0.40 * merged['constructor_baseline']).round(2)
    
    # 3. Delta de Desempeño (Driver Impact Delta)
    # Delta positivo = el piloto terminó mejor que lo esperado por su auto/largada
    merged['driver_delta'] = (merged['expected_position'] - merged['position_num']).round(2)
    
    # 4. Clasificación de Rendimiento
    def clasificar(delta):
        if pd.isna(delta):
            return 'DNF / No clasificado'
        if delta >= 3.0:
            return 'Overperformer Sobresaliente'
        elif delta >= 1.0:
            return 'Rendimiento Superior'
        elif delta >= -1.0:
            return 'Rendimiento Esperado'
        elif delta >= -3.0:
            return 'Rendimiento Inferior'
        else:
            return 'Underperformer Severo'
            
    merged['performance_tier'] = merged['driver_delta'].apply(clasificar)
    
    # 5. Comparativa con compañero de equipo en la misma carrera
    finishers = merged[merged['position_num'].notna()].copy()
    
    def comparar_companeros(grupo):
        if len(grupo) == 2:
            d1 = grupo.iloc[0]
            d2 = grupo.iloc[1]
            diff = d1['position_num'] - d2['position_num'] # negativo = d1 terminó mejor
            grupo = grupo.copy()
            grupo.loc[grupo.index[0], 'teammate_name'] = d2['driverName']
            grupo.loc[grupo.index[0], 'teammate_pos'] = d2['position_num']
            grupo.loc[grupo.index[0], 'beat_teammate'] = diff < 0
            grupo.loc[grupo.index[0], 'teammate_gap'] = -diff
            
            grupo.loc[grupo.index[1], 'teammate_name'] = d1['driverName']
            grupo.loc[grupo.index[1], 'teammate_pos'] = d1['position_num']
            grupo.loc[grupo.index[1], 'beat_teammate'] = diff > 0
            grupo.loc[grupo.index[1], 'teammate_gap'] = diff
        else:
            grupo['teammate_name'] = np.nan
            grupo['teammate_pos'] = np.nan
            grupo['beat_teammate'] = np.nan
            grupo['teammate_gap'] = np.nan
        return grupo

    final_df = finishers.groupby(['season', 'round', 'constructorName'], as_index=False, group_keys=False).apply(comparar_companeros)
    
    final_df['beat_teammate'] = final_df['beat_teammate'].astype(float)
    
    os.makedirs('datasets_procesados', exist_ok=True)
    output_path = 'datasets_procesados/driver_performance_expected.csv'
    final_df.to_csv(output_path, index=False)
    print(f"Dataset procesado guardado exitosamente en: {output_path}")
    print(f"Total de registros analizados: {len(final_df)}")
    
    # Resumen rápido
    top_overperformers = final_df.groupby('driverName').agg(
        carreras=('position_num', 'count'),
        promedio_delta=('driver_delta', 'mean'),
        tasa_victoria_companero=('beat_teammate', 'mean'),
        brecha_media_posiciones=('teammate_gap', 'mean')
    ).query('carreras >= 30').sort_values('tasa_victoria_companero', ascending=False)
    
    print("\n--- DOMINIO FRENTE AL COMPAÑERO DE EQUIPO (2018-2024) ---")
    print(top_overperformers.head(10))

if __name__ == '__main__':
    procesar_metricas_f1()
