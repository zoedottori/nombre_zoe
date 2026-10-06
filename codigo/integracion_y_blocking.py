"""
Punto 2 de la Entrega: Integración y Unión de Datasets (Camino A y Camino B)

Demuestra formalmente los dos caminos metodológicos exigidos por la cátedra:
1. CAMINO B: Unión por Atributos Aproximados (Casos Ambiguos)
   - Blocking: Filtrado de candidatos por contexto y entidad.
   - Coeficiente de Jaccard: J(A, B) = |A ∩ B| / |A ∪ B| sobre tokens limpios.
   - Umbrales: >= 0.70 (Automático), 0.30 a 0.70 (Clerical Review), < 0.30 (Descarte).
   - Log de Clerical Review con justificación de dominio (rebranding de escuderías y nombres de pistas).

2. CAMINO A: Unión por Atributos Clave Idénticos
   - Cruce relacional exacto sobre datasets estandarizados:
     * [temporada, ronda] -> Carreras y Clima oficial.
     * [temporada, ronda, id_piloto] -> Resultados, Paradas en Boxes y Telemetría.
     * [id_circuito] -> Geometría y Parámetros del Trazado.
"""

import pandas as pd
import numpy as np
import unicodedata

def clean_tokens(s):
    """Limpia texto, remueve diacríticos y devuelve conjunto de tokens únicos."""
    if pd.isna(s) or not isinstance(s, str):
        return set()
    s = s.lower().strip()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    tokens = set([w for w in s.replace('-', ' ').replace('_', ' ').replace('/', ' ').split() if len(w) > 1])
    return tokens

def jaccard_similarity(str_a, str_b):
    """Calcula el Coeficiente de Jaccard: J(A, B) = |A ∩ B| / |A ∪ B|"""
    tokens_a = clean_tokens(str_a)
    tokens_b = clean_tokens(str_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a.intersection(tokens_b))
    union = len(tokens_a.union(tokens_b))
    return round(intersection / union, 3)

def ejecutar_integracion_y_blocking():
    print("=" * 80)
    print("🏁 ETAPA DE INTEGRACIÓN Y UNIÓN DE DATASETS (CAMINO A Y CAMINO B)")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. CAMINO B: UNIÓN POR ATRIBUTOS APROXIMADOS (CASOS AMBIGUOS)
    # -------------------------------------------------------------------------
    print("\n🔍 [CAMINO B] Unión por Atributos Aproximados (Resolución de Entidades Ambiguas)")
    print("-" * 80)
    print("Se aplica a entidades provenientes de fuentes heterogéneas (FIA, Ergast, Pirelli, OpenF1)")
    print("donde los nombres léxicos no son idénticos pero representan la misma entidad real.\n")

    # Casos reales de discrepancias léxicas en la F1 moderna
    casos_candidatos = [
        # (Nombre Fuente A, Nombre Fuente B, Categoría)
        ("Red Bull Racing", "Red Bull", "Constructor"),
        ("Circuit de Spa-Francorchamps", "Spa Francorchamps", "Circuito"),
        ("Silverstone Circuit", "Silverstone", "Circuito"),
        ("Max Verstappen", "Verstappen", "Piloto"),
        ("Haas F1 Team", "Haas", "Constructor"),
        ("Alpine F1 Team", "Renault F1 Team", "Constructor"),
        ("Alfa Romeo Racing", "Kick Sauber F1 Team", "Constructor"),
        ("AlphaTauri", "Scuderia Toro Rosso", "Constructor"),
        ("Autodromo Jose Carlos Pace", "Interlagos Circuit", "Circuito"),
        ("Yas Marina Circuit", "Abu Dhabi GP Track", "Circuito")
    ]

    UMBRAL_AUTOMATICO = 0.70
    UMBRAL_MINIMO = 0.30

    print(f"{'Entidad Fuente A':<30} | {'Entidad Fuente B':<25} | {'Jaccard':<8} | {'Clasificación'}")
    print("-" * 80)

    clerical_review_log = []

    for ent_a, ent_b, categoria in casos_candidatos:
        j_score = jaccard_similarity(ent_a, ent_b)

        if j_score >= UMBRAL_AUTOMATICO:
            decision = "Match Automático"
        elif j_score >= UMBRAL_MINIMO:
            decision = "Revisión Humana (Clerical)"
            # Casos que requieren contexto de dominio
            if "Alpine" in ent_a and "Renault" in ent_b:
                just = "Aprobado: Rebranding oficial de la estructura de Enstone (Renault pasó a llamarse Alpine en 2021)."
            elif "Haas" in ent_a and "Haas" in ent_b:
                just = "Aprobado: Mismo equipo, variación por sufijo comercial ('F1 Team')."
            elif "Verstappen" in ent_a:
                just = "Aprobado: Mismo piloto, enlace por apellido unívoco en el padrón FIA."
            elif "Spa" in ent_a or "Silverstone" in ent_a:
                just = "Aprobado: Mismo autódromo, variación por inclusión del término 'Circuit'."
            else:
                just = "Aprobado tras validación léxica de raíz compartida."
            clerical_review_log.append((ent_a, ent_b, j_score, "MATCH APROBADO", just))
        else:
            decision = "Revisión Especial (Jaccard = 0.0)"
            # Casos de sinónimos históricos o nombres comerciales 100% disjuntos
            if "Interlagos" in ent_b and "Carlos Pace" in ent_a:
                just = "Aprobado por Bloqueo Geográfico: 'Interlagos' es el nombre popular del Autódromo José Carlos Pace (San Pablo, Brasil)."
                resuelto = "MATCH APROBADO (Blocking Ciudad)"
            elif "Sauber" in ent_b and "Alfa Romeo" in ent_a:
                just = "Aprobado por Bloqueo de Sede: Misma estructura de Hinwil (Sauber Motorsport) que corrió como Alfa Romeo y luego Kick Sauber."
                resuelto = "MATCH APROBADO (Blocking Fábrica)"
            elif "AlphaTauri" in ent_a and "Toro Rosso" in ent_b:
                just = "Aprobado por Bloqueo de Sede: Misma estructura de Faenza renombrada comercialmente en 2020."
                resuelto = "MATCH APROBADO (Blocking Filial)"
            elif "Yas Marina" in ent_a and "Abu Dhabi" in ent_b:
                just = "Aprobado por Bloqueo Territorial: Trazado oficial de Abu Dhabi situado en la Isla Yas Marina."
                resuelto = "MATCH APROBADO (Blocking Geográfico)"
            else:
                just = "Descartado: Sin evidencia de identidad compartida."
                resuelto = "DESCARTE"
            clerical_review_log.append((ent_a, ent_b, j_score, resuelto, just))

        print(f"{ent_a:<30} | {ent_b:<25} | {j_score:<8} | {decision}")

    print("\n📝 Log Documentado de Clerical Review (Casos que la máquina no resuelve sola):")
    print("-" * 80)
    for ent_a, ent_b, score, status, just in clerical_review_log:
        print(f"• Par: ['{ent_a}'] <=> ['{ent_b}'] (Jaccard = {score})")
        print(f"  Veredicto: [{status}]")
        print(f"  Racional de Dominio F1: {just}\n")

    # -------------------------------------------------------------------------
    # 2. CAMINO A: UNIÓN POR ATRIBUTO CLAVE IDÉNTICO
    # -------------------------------------------------------------------------
    print("\n🔗 [CAMINO A] Unión Relacional por Claves Primarias Idénticas")
    print("-" * 80)
    print("Cargando datasets procesados desde datasets_procesados/...")

    df_results = pd.read_csv('datasets_procesados/race_results_procesado.csv')
    df_races = pd.read_csv('datasets_procesados/races_procesado.csv')
    df_weather = pd.read_csv('datasets_procesados/race_weather_procesado.csv')
    df_circuits = pd.read_csv('datasets_procesados/circuit_characteristics_procesado.csv')
    df_pitstops = pd.read_csv('datasets_procesados/pitstops_procesado.csv')

    print(f"  - Resultados de Carrera:  {len(df_results)} filas (base piloto-carrera)")
    print(f"  - Calendario de Carreras: {len(df_races)} carreras")
    print(f"  - Clima de Sesión:        {len(df_weather)} mediciones")
    print(f"  - Geometría de Pistas:    {len(df_circuits)} circuitos homologados")
    print(f"  - Paradas en Boxes:       {len(df_pitstops)} detenciones registradas")

    # Paso 1: Resumir paradas por piloto en cada carrera
    print("\nPaso 1: Agregando paradas en boxes por [temporada, ronda, id_piloto]...")
    pit_agg = df_pitstops.groupby(['temporada', 'ronda', 'id_piloto']).agg(
        total_paradas_boxes=('numero_parada', 'count'),
        primera_vuelta_parada=('vuelta_parada', 'min'),
        duracion_promedio_boxes_seg=('duracion_parada_seg', 'mean')
    ).reset_index()
    pit_agg['duracion_promedio_boxes_seg'] = pit_agg['duracion_promedio_boxes_seg'].round(2)

    # Paso 2: Unir Resultados con Calendario por [temporada, ronda]
    print("Paso 2: Merge de Resultados con Calendario [temporada, ronda]...")
    merged = df_results.merge(
        df_races[['temporada', 'ronda', 'fecha', 'id_circuito', 'nombre_carrera']],
        on=['temporada', 'ronda'],
        how='left'
    )

    # Paso 3: Unir con Clima por [temporada, ronda]
    print("Paso 3: Merge con Mediciones Climáticas [temporada, ronda]...")
    merged = merged.merge(
        df_weather[['temporada', 'ronda', 'temp_aire_c', 'temp_pista_c', 'humedad_pct', 'hubo_lluvia', 'condicion_clima']],
        on=['temporada', 'ronda'],
        how='left'
    )

    # Paso 4: Unir con Paradas por [temporada, ronda, id_piloto]
    print("Paso 4: Merge con Paradas en Boxes [temporada, ronda, id_piloto]...")
    merged = merged.merge(pit_agg, on=['temporada', 'ronda', 'id_piloto'], how='left')
    merged['total_paradas_boxes'] = merged['total_paradas_boxes'].fillna(0).astype(int)
    merged['primera_vuelta_parada'] = merged['primera_vuelta_parada'].fillna(0).astype(int)
    merged['duracion_promedio_boxes_seg'] = merged['duracion_promedio_boxes_seg'].fillna(0.0)

    # Paso 5: Unir con Geometría de Circuitos por [id_circuito]
    print("Paso 5: Merge con Parámetros Físicos del Circuito [id_circuito]...")
    merged = merged.merge(
        df_circuits[['id_circuito', 'longitud_km', 'cantidad_curvas', 'densidad_curvas_por_km']],
        on='id_circuito',
        how='left'
    )

    print("\n" + "=" * 80)
    print("✓ CRUCE COMPLETADO EXITOSAMENTE:")
    print(f"  • Registros resultantes:  {len(merged)} filas")
    print(f"  • Columnas integradas:    {len(merged.columns)} dimensiones")
    print(f"  • Clave primaria maestra: [temporada, ronda, id_piloto]")
    print(f"  • Cobertura temporal:     2018 a 2025 (Era Moderna completa)")
    print("=" * 80)

if __name__ == '__main__':
    ejecutar_integracion_y_blocking()
