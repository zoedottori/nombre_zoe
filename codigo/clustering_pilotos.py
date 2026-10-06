"""
clustering_pilotos.py — CircuitDNA
==================================
Construye perfiles de comportamiento de pilotos a partir de los datos
y los cruza con los tipos de pista (familias genéticas de circuitos).

Flujo:
  1. Feature engineering: variables de comportamiento + nivel absoluto
  2. K-Means con pesos diferenciados (numpy puro)
  3. Cruce perfil_piloto × familia_circuito
  4. Hallazgos no obvios: ¿qué tipo de pista favorece a cada perfil?

Ajuste v2:
  - Agrega rendimiento absoluto (pos. final mediana y puestos ganados prom)
    para separar élite de midfield dentro del mismo estilo de conducción.
  - Usa K=5 para capturar la granularidad real de la grilla de F1.
  - Ponderación de features: performance nivel x2 para que domine la separación.
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ── Cargar datos ───────────────────────────────────────────────────────────────
carreras = pd.read_csv('datasets_procesados/datasets_maestros/tabla_maestra_carreras_pilotos.csv')
stints   = pd.read_csv('datasets_procesados/datasets_maestros/tabla_maestra_stints_estrategia.csv')
char     = pd.read_csv('datasets/circuit_characteristics.csv')

# Asignar familia genética de circuito (resultado del K-Means de pistas)
familia_map = {
    'spa': 0, 'silverstone': 0, 'catalunya': 0, 'suzuka': 0,
    'jeddah': 0, 'zandvoort': 0, 'losail': 0, 'mugello': 0,
    'monza': 1, 'red_bull_ring': 1, 'albert_park': 1, 'yas_marina': 1,
    'miami': 1, 'vegas': 1, 'villeneuve': 1, 'hockenheimring': 1,
    'interlagos': 2, 'bahrain': 2, 'americas': 2, 'imola': 2,
    'shanghai': 2, 'ricard': 2, 'nurburgring': 2, 'portimao': 2, 'istanbul': 2,
    'monaco': 3, 'baku': 3, 'hungaroring': 3, 'marina_bay': 3,
    'rodriguez': 3, 'sochi': 3,
}
familia_nombre = {
    0: 'Carga Lateral Extrema',
    1: 'Stop-and-Go',
    2: 'Mixtos y Técnicos',
    3: 'Laberintos Urbanos',
}

df_full = carreras.copy()
df_full['familia_circuito'] = df_full['id_circuito'].map(familia_map)
df = df_full[df_full['estado_carrera'].isin(['FINISHED', '+1 LAP', '+2 LAPS'])].copy()

print("=" * 72)
print("  CLUSTERING DE PILOTOS v2 — CircuitDNA")
print("=" * 72)

# ══════════════════════════════════════════════════════════════════════════════
# PASO 1: Feature Engineering
# ══════════════════════════════════════════════════════════════════════════════
print("\n[PASO 1] Construyendo features de comportamiento + nivel absoluto...")

conteo = df.groupby('id_piloto').size()
pilotos_validos = conteo[conteo >= 10].index
df = df[df['id_piloto'].isin(pilotos_validos)].copy()

# ── Features de COMPORTAMIENTO (estilo de pilotaje) ──────────────────────────

# B1: Agresividad de parada (primera vuelta en boxes / total vueltas)
df['primera_parada_norm'] = (
    df['primera_vuelta_parada'] / df['vueltas_completadas'].replace(0, np.nan)
)

# B2: Número de paradas por carrera
df['paradas_clip'] = df['total_paradas_boxes'].clip(0, 4)

# B3: Consistencia de ritmo (desviación estándar en seg — menor = más consistente)
df['consistencia'] = df['consistencia_ritmo_seg']

# B4: Gestión de gomas (stint más largo / total vueltas → >0.5 = piloto conservador)
df['gestion_gomas'] = (
    df['stint_mas_largo_vueltas'] / df['vueltas_completadas'].replace(0, np.nan)
)

# B5: Delta rendimiento en lluvia (puestos ganados en mojado vs seco)
lluvia_perf  = df[df['hubo_lluvia'] == 1].groupby('id_piloto')['puestos_ganados'].mean()
seco_perf    = df[df['hubo_lluvia'] == 0].groupby('id_piloto')['puestos_ganados'].mean()
delta_lluvia = (lluvia_perf - seco_perf).rename('delta_lluvia')

# B6: Delta rendimiento con Safety Car (caos) vs carrera limpia
sc_perf    = df[df['despliegues_safety_car'] > 0].groupby('id_piloto')['puestos_ganados'].mean()
clean_perf = df[df['despliegues_safety_car'] == 0].groupby('id_piloto')['puestos_ganados'].mean()
delta_sc   = (sc_perf - clean_perf).rename('delta_sc')

# B7: Varianza de posición final (¿piloto consistente o errático?)
var_pos = df.groupby('id_piloto')['posicion_final'].std().rename('varianza_posicion')

# ── Features de NIVEL ABSOLUTO (para separar élite de midfield) ──────────────

# P1: Posición final mediana (menor = mejor piloto)
pos_mediana = df.groupby('id_piloto')['posicion_final'].median().rename('pos_mediana')

# P2: Puestos ganados promedio (qué tanto supera su grilla de salida)
puestos_prom = df.groupby('id_piloto')['puestos_ganados'].mean().rename('puestos_prom')

# P3: Porcentaje de carreras en puntos (Top 10)
puntos_pct = df.groupby('id_piloto').apply(
    lambda x: (x['posicion_final'] <= 10).mean()
).rename('pct_en_puntos')

# ── Agrupar todas las features ────────────────────────────────────────────────
feat = df.groupby('id_piloto').agg(
    nombre        = ('nombre_piloto', 'first'),
    constructor   = ('constructor', lambda x: x.mode()[0]),
    n_carreras    = ('posicion_final', 'count'),
    paradas_prom  = ('paradas_clip', 'mean'),
    primera_parada= ('primera_parada_norm', 'mean'),
    consistencia  = ('consistencia', 'mean'),
    gestion_gomas = ('gestion_gomas', 'mean'),
).join(delta_lluvia, how='left') \
 .join(delta_sc, how='left') \
 .join(var_pos, how='left') \
 .join(pos_mediana, how='left') \
 .join(puestos_prom, how='left') \
 .join(puntos_pct, how='left')

feat = feat[feat['n_carreras'] >= 10].copy()
feat = feat.fillna(feat.mean(numeric_only=True))

print(f"  Pilotos con datos suficientes: {len(feat)}")
print(f"  Features de comportamiento (B): paradas_prom, primera_parada,")
print(f"                                  consistencia, gestion_gomas,")
print(f"                                  delta_lluvia, delta_sc, varianza_posicion")
print(f"  Features de nivel absoluto (P): pos_mediana, puestos_prom, pct_en_puntos")

# ══════════════════════════════════════════════════════════════════════════════
# PASO 2: K-Means con pesos diferenciados
# ══════════════════════════════════════════════════════════════════════════════
print("\n[PASO 2] K-Means con ponderación (nivel x2 para separar élite/midfield)...")

# Columnas de comportamiento (peso 1x) y de nivel (peso 2x)
behavior_cols = ['paradas_prom', 'primera_parada', 'consistencia',
                 'gestion_gomas', 'delta_lluvia', 'delta_sc', 'varianza_posicion']
level_cols    = ['pos_mediana', 'puestos_prom', 'pct_en_puntos']

X_behavior = feat[behavior_cols].values.astype(np.float64)
X_level    = feat[level_cols].values.astype(np.float64)

# Normalización Z-score por separado
def zscore(X):
    mu, sd = X.mean(axis=0), X.std(axis=0)
    sd[sd == 0] = 1
    return (X - mu) / sd, mu, sd

Xb, _, _ = zscore(X_behavior)
Xl, _, _ = zscore(X_level)

# Concatenar con peso doble para las features de nivel
X = np.hstack([Xb, Xl * 2.0])

def kmeans_np(X, k, n_init=15, max_iter=300, seed=42):
    rng = np.random.default_rng(seed)
    best_inertia, best_labels, best_centers = np.inf, None, None
    for _ in range(n_init):
        idx     = rng.choice(len(X), k, replace=False)
        centers = X[idx].copy()
        for _ in range(max_iter):
            dists  = np.linalg.norm(X[:, None] - centers[None, :], axis=2)
            labels = dists.argmin(axis=1)
            new_c  = np.array([
                X[labels == j].mean(axis=0) if (labels == j).any() else centers[j]
                for j in range(k)
            ])
            if np.allclose(centers, new_c, atol=1e-6):
                break
            centers = new_c
        inertia = sum(
            np.linalg.norm(X[labels == j] - centers[j], axis=1).sum()
            for j in range(k)
        )
        if inertia < best_inertia:
            best_inertia, best_labels, best_centers = inertia, labels, centers
    return best_labels, best_centers, best_inertia

print("  Barrido de K:")
for k in [3, 4, 5, 6]:
    _, _, inercia = kmeans_np(X, k)
    print(f"    K = {k}: Inercia = {inercia:.2f}")

K = 5
labels, centers, _ = kmeans_np(X, K)
feat['perfil_id'] = labels

# ══════════════════════════════════════════════════════════════════════════════
# PASO 3: Nombrar perfiles basado en las medias reales
# ══════════════════════════════════════════════════════════════════════════════
print("\n[PASO 3] Caracterizando perfiles...")

pm = feat.groupby('perfil_id').agg(
    n              = ('n_carreras', 'count'),
    paradas        = ('paradas_prom', 'mean'),
    primera        = ('primera_parada', 'mean'),
    consist        = ('consistencia', 'mean'),
    gestion        = ('gestion_gomas', 'mean'),
    lluvia         = ('delta_lluvia', 'mean'),
    sc             = ('delta_sc', 'mean'),
    var_pos        = ('varianza_posicion', 'mean'),
    pos_med        = ('pos_mediana', 'mean'),
    puestos        = ('puestos_prom', 'mean'),
    pct_pts        = ('pct_en_puntos', 'mean'),
)

# Regla de naming basada en dos ejes: nivel (pos_med) + estilo (paradas, lluvia, etc.)
def nombre_perfil(row, pm):
    es_elite   = row['pos_med'] <= pm['pos_med'].quantile(0.30)
    es_top      = row['pos_med'] <= pm['pos_med'].quantile(0.55)
    ama_lluvia  = row['lluvia']  >= pm['lluvia'].quantile(0.70)
    ama_sc      = row['sc']      >= pm['sc'].quantile(0.70)
    muy_consist = row['consist'] <= pm['consist'].quantile(0.35)
    para_rapido = row['primera'] <= pm['primera'].quantile(0.35)

    if es_elite and muy_consist:
        return 'Élite Metronómico'        # Hamiltons, Verstappens: rápido + consistente
    elif es_elite:
        return 'Élite Agresivo'           # Rápido pero más errático / arriesgado
    elif es_top and ama_lluvia:
        return 'Piloto de Lluvia'         # Midfield top que destaca en mojado
    elif es_top and ama_sc:
        return 'Oportunista de Caos'      # Midfield que escala con SC y bandera roja
    elif es_top:
        return 'Gestor de Midfield'       # Midfield sólido, sin ventaja especial
    else:
        return 'Fondista'                 # Fondo de tabla, acumula kilómetros

pm['nombre'] = pm.apply(lambda r: nombre_perfil(r, pm), axis=1)
feat['nombre_perfil'] = feat['perfil_id'].map(pm['nombre'])

# ── Imprimir resumen de perfiles ──────────────────────────────────────────────
print("\n" + "=" * 72)
print("  PERFILES DE PILOTOS (construidos desde los datos)")
print("=" * 72)

for pid in sorted(feat['perfil_id'].unique()):
    sub    = feat[feat['perfil_id'] == pid].sort_values('pos_mediana')
    nombre = pm.loc[pid, 'nombre']
    datos  = pm.loc[pid]
    print(f"\n  ── Perfil {pid}: {nombre} ({len(sub)} pilotos) ──")
    print(f"     Pos. mediana: {datos['pos_med']:.1f}  |  "
          f"Puestos ganados: {datos['puestos']:+.2f}  |  "
          f"En puntos: {datos['pct_pts']*100:.0f}%")
    print(f"     Consistencia: {datos['consist']:.2f}s  |  "
          f"Paradas/carrera: {datos['paradas']:.1f}  |  "
          f"Delta lluvia: {datos['lluvia']:+.2f}  |  "
          f"Delta SC: {datos['sc']:+.2f}")
    pilotos_str = ' · '.join(sub['nombre'].head(8).tolist())
    print(f"     Pilotos: {pilotos_str}")

# ══════════════════════════════════════════════════════════════════════════════
# PASO 4: Cruce Perfil × Familia de Circuito
# ══════════════════════════════════════════════════════════════════════════════
print("\n\n" + "=" * 72)
print("  CRUCE: PERFIL DE PILOTO × FAMILIA DE CIRCUITO")
print("=" * 72)

perfil_map  = feat['perfil_id'].to_dict()
nombre_map  = feat['nombre_perfil'].to_dict()
df['perfil_id']     = df['id_piloto'].map(perfil_map)
df['nombre_perfil'] = df['id_piloto'].map(nombre_map)
df['familia_circuito'] = df['id_circuito'].map(familia_map)
df['familia_nombre']   = df['familia_circuito'].map(familia_nombre)

df_cruce = df.dropna(subset=['perfil_id', 'familia_circuito']).copy()

# Tabla cruzada: media de puestos ganados
pivot = df_cruce.groupby(['nombre_perfil', 'familia_nombre'])['puestos_ganados'].mean().unstack()
orden_familias = ['Carga Lateral Extrema', 'Stop-and-Go', 'Mixtos y Técnicos', 'Laberintos Urbanos']
orden_familias = [f for f in orden_familias if f in pivot.columns]
pivot = pivot[orden_familias]

print("\n  Puestos ganados promedio (+ = sube en carrera respecto a la grilla):\n")
print(pivot.round(2).to_string())

# ══════════════════════════════════════════════════════════════════════════════
# PASO 5: Patrones no obvios del cruce
# ══════════════════════════════════════════════════════════════════════════════
print("\n\n" + "=" * 72)
print("  PATRONES NO OBVIOS — PISTA + PERFIL DE PILOTO")
print("=" * 72)

# Para cada familia: ¿qué perfil SORPRENDE (sube más de lo esperado)?
print()
for fam_id, fam_nombre_str in familia_nombre.items():
    sub_fam = df_cruce[df_cruce['familia_circuito'] == fam_id]
    if len(sub_fam) < 30:
        continue

    por_perfil = (sub_fam.groupby('nombre_perfil')['puestos_ganados']
                  .agg(['mean', 'count'])
                  .rename(columns={'mean': 'media', 'count': 'n'}))
    por_perfil = por_perfil[por_perfil['n'] >= 15].sort_values('media', ascending=False)

    print(f"📍 {fam_nombre_str}:")
    for pname, row in por_perfil.iterrows():
        bar    = '▓' * max(1, int(abs(row['media'])))
        signo  = '↑' if row['media'] >= 0 else '↓'
        marca  = '  ← 🔥 MATCH' if row.name == por_perfil.index[0] else \
                 ('  ← ⚠️  MISMATCH' if row.name == por_perfil.index[-1] else '')
        print(f"   {pname:28s}: {row['media']:+.2f} {bar}{signo}  (n={int(row['n'])}){marca}")
    print()

# ══════════════════════════════════════════════════════════════════════════════
# PASO 6: Hallazgos estrella — combinaciones extremas
# ══════════════════════════════════════════════════════════════════════════════
print("=" * 72)
print("  HALLAZGOS ESTRELLA")
print("=" * 72)

todas = (df_cruce.groupby(['nombre_perfil', 'familia_nombre'])['puestos_ganados']
         .agg(['mean', 'count'])
         .reset_index())
todas.columns = ['perfil', 'familia', 'media', 'n']
todas = todas[todas['n'] >= 20]

mejor = todas.nlargest(5, 'media')
peor  = todas.nsmallest(5, 'media')

print("\n✅ TOP 5 — Combinaciones MATCH (perfil + circuito = máximo rendimiento):")
for _, row in mejor.iterrows():
    print(f"   {row['perfil']:30s} × {row['familia']:25s} → {row['media']:+.2f} puestos  (n={row['n']})")

print("\n❌ TOP 5 — Combinaciones MISMATCH (perfil + circuito = hundimiento):")
for _, row in peor.iterrows():
    print(f"   {row['perfil']:30s} × {row['familia']:25s} → {row['media']:+.2f} puestos  (n={row['n']})")

# ══════════════════════════════════════════════════════════════════════════════
# PASO 7: Hallazgo de "gemelos de circuito" validado por rendimiento de pilotos
# ══════════════════════════════════════════════════════════════════════════════
print("\n\n" + "=" * 72)
print("  GEMELOS DE CIRCUITO (validado por quién rinde en cada uno)")
print("=" * 72)

pivot_pilotos = df_cruce.pivot_table(
    index='id_piloto', columns='id_circuito',
    values='posicion_final', aggfunc='mean'
)
pivot_pilotos = pivot_pilotos.dropna(thresh=15, axis=1).dropna(thresh=8, axis=0)

corr_mat = pivot_pilotos.corr()
cols     = corr_mat.columns.tolist()
pairs    = [(cols[i], cols[j], corr_mat.iloc[i, j])
            for i in range(len(cols)) for j in range(i+1, len(cols))
            if not np.isnan(corr_mat.iloc[i, j])]
pairs_df = pd.DataFrame(pairs, columns=['circ_a', 'circ_b', 'r'])

pais = dict(zip(char['circuitId'], char['country']))

top = pairs_df.nlargest(10, 'r')
print("\n  Top pares con ADN compartido (mismos pilotos rinden igual en ambos):\n")
for _, row in top.iterrows():
    fam_a = familia_map.get(row['circ_a'], '?')
    fam_b = familia_map.get(row['circ_b'], '?')
    misma = '✓ misma familia' if fam_a == fam_b else '★ distinta familia!'
    pa    = pais.get(row['circ_a'], '?')
    pb    = pais.get(row['circ_b'], '?')
    print(f"   {row['circ_a']:18s}({pa:15s}) ↔ {row['circ_b']:18s}({pb:12s})  r={row['r']:.3f}  {misma}")

print("\n" + "=" * 72)
print("  Clustering de Pilotos v2 — completado.")
print("=" * 72)
