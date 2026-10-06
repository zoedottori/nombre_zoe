# Diccionario de Datasets Maestros Oficiales (`datasets_maestros/`)

> **BeyondGrid AI & CircuitDNA**  
> Directorio central de tablas maestras unificadas para el entrenamiento de modelos, cálculo de patrones empíricos y alimentación de la plataforma web.  
> Cobertura: **Era Moderna de Fórmula 1 (2018–2025, 8 temporadas completas, 173 Grandes Premios, 31 circuitos)**.

---

## 🏛️ Las Tablas Maestras Consolidadas

| Archivo CSV | Granularidad | Registros | Dimensiones | Rol en el Sistema |
| :--- | :--- | :---: | :---: | :--- |
| **`tabla_maestra_carreras_pilotos.csv`** | 1 fila por Piloto por Gran Premio | 3.458 | 45 columnas | **La Tabla Reina:** Cruce de rendimiento deportivo, clasificación del sábado, clima, paradas, ritmo y consistencia en vueltas limpias. |
| **`tabla_maestra_stints_estrategia.csv`** | 1 fila por Tanda de Neumático (Stint) | 9.035 | 21 columnas | **La Tabla de Estrategia:** Desglose de neumáticos, duración de stint, compuestos reales, asfalto y columna inferida de `motivo_parada`. |
| **`tabla_maestra_circuitos_carreras.csv`**| 1 fila por Gran Premio / Circuito | 173 | 34 columnas | **La Tabla Macro:** Análisis de circuitos, correlación de predictibilidad qualy-carrera y promedios colectivos por evento. |
| **`fichas_circuitos_demo.csv`** | 1 fila por Circuito Seleccionado | 6 | 16 columnas | **La Tabla de Producto (Demo UI):** Fichas para la pantalla de la app (Mónaco, Interlagos, Silverstone, Monza, Marina Bay, Spa). |

---

## 📋 1. `tabla_maestra_carreras_pilotos.csv` (⭐ Tabla Principal)
* **Clave Primaria:** `[temporada, ronda, id_piloto]`
* **Uso:** Alimenta las métricas deportivas y de condiciones ambientales:
  1. *Capa Pilotos:* Rendimiento Esperado vs. Real (reducción del error medio absoluto a 2.47 posiciones vs. 2.91 en datos no vistos).
  2. *Capa Condiciones:* Impacto de lluvia y Safety Car en la probabilidad de ganar +5 posiciones.
  3. *Capa Pista:* Correlación de predictibilidad largada-llegada según trazado.

### Columnas Incluidas:
* **Identificación del Evento:** `temporada`, `ronda`, `fecha`, `id_circuito`, `nombre_circuito`, `pais`, `nombre_carrera`, `arquetipo_pista`.
* **Identificación del Competidor:** `id_piloto`, `nombre_piloto`, `constructor`.
* **Desempeño Deportivo:** `posicion_qualy`, `posicion_largada`, `posicion_final`, `puestos_ganados`, `puntos_obtenidos`, `vueltas_completadas`, `estado_carrera`, `posicion_sprint`, `puntos_sprint`.
* **Estrategia y Boxes:** `total_paradas_boxes`, `primera_vuelta_parada`, `duracion_promedio_boxes_seg`, `secuencia_compuestos` (ej. `MEDIUM -> HARD`), `stint_mas_largo_vueltas`.
* **Condiciones Ambientales:** `temp_aire_c`, `temp_pista_c`, `humedad_pct`, `hubo_lluvia`, `condicion_clima`.
* **Geometría de Trazado:** `longitud_km`, `cantidad_curvas`, `densidad_curvas_por_km`.
* **Telemetría de Ritmo:** `vueltas_limpias_analizadas`, `ritmo_mediana_seg`, `consistencia_ritmo_seg`, `mejor_vuelta_seg`, `velocidad_media_estimada_kmh`.
* **Asignación Pirelli:** `compuesto_duro`, `compuesto_medio`, `compuesto_blando`.
* **Neutralizaciones:** `despliegues_safety_car`, `despliegues_vsc`, `hubo_bandera_roja`.
* **Trazabilidad:** `fuente`.

---

## 🛞 2. `tabla_maestra_stints_estrategia.csv` (Degradación y Paradas)
* **Clave Primaria:** `[temporada, ronda, id_piloto, numero_stint]`
* **Uso:** Alimenta el análisis de duración de compuestos (Blando 14, Medio 19, Duro 24 vueltas de mediana descriptiva en 2023–2025).

> [!WARNING]
> **Aclaración sobre `motivo_parada`:**  
> Esta columna es una **clasificación heurística inferida** basada en reglas de cruce temporal (ventanas de SC, vueltas finales, transiciones de lluvia o detenciones prolongadas). No constituye un sensor directo de telemetría ni una declaración oficial de los equipos.

### Columnas Incluidas:
* `temporada`, `ronda`, `id_circuito`, `id_piloto`, `nombre_piloto`, `constructor`.
* `numero_stint`, `vuelta_inicio`, `vuelta_fin`, `duracion_stint_vueltas`.
* `compuesto`: Compuesto real homologado (SOFT, MEDIUM, HARD, INTERMEDIATE, WET en 2023–2025; vacío documentado en 2018–2022).
* `rol_compuesto_pirelli`: Clasificación relativa de dureza (`DURO`, `MEDIO`, `BLANDO` o `No Instrumentado`).
* `duracion_parada_seg`: Tiempo de detención en boxes.
* **`motivo_parada` (Heurística Inferida):**
  * `Cheap Pit Stop (Safety Car)`: Parada en ventana neutralizada bajo Auto de Seguridad (ahorro de ~10 segundos de pit loss).
  * `Cheap Pit Stop (Virtual Safety Car)`: Parada bajo VSC.
  * `Transición Climática`: Parada motivada por lluvia o secado de pista.
  * `Caza de Vuelta Rápida`: Parada en las últimas 4 vueltas de carrera para calzar compuesto blando nuevo y buscar el récord.
  * `Daño / Pinchadura / Imprevisto`: Parada prematura (vueltas 1–4) o detención prolongada (>32s) por reemplazo de alerón.
  * `Degradación Regular`: Detención estándar por desgaste térmico programado.
  * `Fin de Carrera`: Tanda final con la que el monoplaza cruza la meta.
* `temp_pista_c`, `temp_aire_c`, `hubo_lluvia`, `condicion_clima`.
* `densidad_curvas_por_km`, `longitud_km`.
* `fuente`.

---

## 🏁 3. `tabla_maestra_circuitos_carreras.csv` (Nivel Gran Premio)
* **Clave Primaria:** `[temporada, ronda]`
* **Uso:** Alimenta la comparación de carreras por circuito, costos de parada históricos y correlaciones qualy-carrera.

### Columnas Incluidas:
* `temporada`, `ronda`, `fecha`, `id_circuito`, `nombre_circuito`, `pais`, `nombre_carrera`.
* `arquetipo_pista`: Clasificación objetiva (`Alta Densidad / Trabado`, `Media Densidad / Equilibrado`, `Baja Densidad / Rápido`).
* `longitud_km`, `cantidad_curvas`, `densidad_curvas_por_km`.
* `temp_aire_c`, `temp_pista_c`, `humedad_pct`, `hubo_lluvia`, `condicion_clima`.
* `piloto_ganador`, `constructor_ganador`, `piloto_pole`, `constructor_pole`.
* `piloto_vuelta_rapida`, `tiempo_vuelta_rapida_seg`.
* `promedio_paradas_carrera`, `total_paradas_carrera`, `total_abandonos`, `volatilidad_puestos_promedio`.
* `correlacion_qualy_carrera`: Coeficiente de Pearson ($r$) que mide qué tan predecible fue el domingo a partir del sábado en esa pista.
* `compuesto_duro`, `compuesto_medio`, `compuesto_blando`.
* `despliegues_safety_car`, `despliegues_vsc`, `hubo_bandera_roja`.
* `fuente`.

---

## 📱 4. `fichas_circuitos_demo.csv` (La Pantalla de la Aplicación)
* **Granularidad:** 1 fila por circuito (6 circuitos clave: Mónaco, Interlagos, Silverstone, Monza, Marina Bay y Spa).
* **Columnas:** `id_circuito`, `nombre_circuito`, `ciudad_pais`, `longitud_km`, `cantidad_curvas`, `tipo_trazado`, `carreras_analizadas`, `costo_parar_mediana_seg`, `pct_carreras_con_sc`, `pct_carreras_con_lluvia`, `correlacion_largada_llegada`, `pct_sorpresas_mas_5`, `stint_mediana_blando_vueltas`, `stint_mediana_medio_vueltas`, `stint_mediana_duro_vueltas`, `stints_analizados_2023_2025`, `rol_en_demo`.
* **Cautela metodológica:** Muestra descriptiva (6 a 9 carreras por circuito; 5 a 40 stints por compuesto). No concluyente.
