# Diccionario de Datos Oficial y Metodología (datasets_procesados/)

Este directorio contiene los **datasets depurados, verificados empíricamente y en español** para el proyecto **BeyondGrid AI & CircuitDNA**.  
Todos los datos abarcan la **Era Moderna de Fórmula 1 (2018–2025)**, cubriendo **31 circuitos oficiales, 173 Grandes Premios y más de 187.000 vueltas de carrera limpias**.

---

## 🏛️ 1. Confirmación de Fuentes Primarias y Trazabilidad

Todas las tablas procesadas y maestras cuentan con trazabilidad explícita y están libres de imputaciones sintéticas arbitrarias:

1. **Ergast Motor Racing Database (FIA Official Timing):**  
   Base relacional histórica oficial de la FIA. Aporta los registros oficiales de: `races`, `race_results`, `qualifying_results`, `lap_times`, `pitstops`, `drivers`, `constructors`, `status`, `seasons`.
2. **OpenF1 Real-Time Telemetry API (api.openf1.org):**  
   Telemetría oficial de la FIA y Fórmula 1 en tiempo real. Provee los compuestos exactos de neumáticos (`SOFT`, `MEDIUM`, `HARD`, etc.) para 2023–2025, cronometraje de pits y sesiones climáticas.
3. **Pirelli Motorsport Press Archive & FIA Event Notes:**  
   Nominaciones oficiales de compuestos secos C1 a C5 por Gran Premio (`pirelli_nominations_procesado.csv`).
4. **FIA Official Circuit Homologation Sheets & F1DB:**  
   Parámetros geométricos oficiales: longitud del trazado en km (`length_km`), cantidad de curvas (`turns`) y tipo de circuito (urbano/callejero vs. permanente).
5. **TracingInsights RaceData Archive:**  
   Registros históricos de Safety Car, Virtual Safety Car y banderas rojas.

> [!NOTE]
> **Decisión de Transparencia y Trazabilidad:**  
> Cada archivo en `datasets_procesados/` y `datasets_maestros/` cuenta con una columna obligatoria `fuente` que certifica la procedencia de cada registro.  
> En las tandas de neumáticos (`tyre_stints_procesado.csv`), las temporadas 2023–2025 contienen el compuesto exacto medido por telemetría OpenF1, mientras que el período 2018–2022 preserva las vueltas y paradas reales pero mantiene el compuesto vacío con indicación explícita de fuente, garantizando **cero datos inventados o sintéticos**.

---

## ⚠️ 2. Cautelas Metodológicas y Aclaraciones Técnicas Esenciales

### A. Explicación del Desfasaje del ~8% entre Stints y Paradas en Boxes
En el análisis cruzado de paradas (`pitstops_procesado.csv`) y tandas de neumáticos (`tyre_stints_procesado.csv`), se observa un desfasaje estructural del ~8%. Esto **no representa un error de datos**, sino la física y el reglamento deportivo de la Fórmula 1:
1. **La Condición de Largada:** Todo piloto que toma la partida inicia en el *Stint 1* sin haber realizado ninguna parada previa. Por definición:  
   $$\text{Stints Totales} \approx \text{Pilotos Largados} + \text{Total de Paradas}$$
2. **Penalizaciones cumplidas en Pits (Stop & Go / 5s Penalty):** Ocurren cuando un piloto entra al pitlane para cumplir una penalización impuesta por los comisarios sin cambiar neumáticos. Ergast registra el paso por boxes, pero no se genera un nuevo juego de gomas en la telemetría.
3. **Abandonos en el Pitlane:** Monoplazas que entran al garaje para retirarse. La entrada a boxes queda computada en los tiempos de pitlane, pero el piloto jamás vuelve a pista a completar un stint.
4. **Cambios de Neumático en Grilla bajo Bandera Roja:** Bajo suspensión de carrera (Red Flag), el reglamento permite cambiar compuestos en la recta principal sin transitar por el carril de boxes, sumando un stint sin parada de pitlane registrada.
5. **Límites de Transpondedores:** Discrepancias residuales menores de transpondedores de cronometraje bajo congestión de pitlane en la base Ergast.

### B. Rotulado de `motivo_parada` como Columna Inferida / Heurística
En las tablas de estrategia (`tabla_maestra_stints_estrategia.csv`), la columna `motivo_parada`:
* **ES UNA VARIABLE INFERIDA HEURÍSTICAMENTE:** No proviene de una telemetría directa ni de una declaración oficial de la escudería por radio.
* **Algoritmo de Inferencia:** Se deduce cruzando si la parada ocurrió dentro de la ventana de un Safety Car o Virtual Safety Car (`Cheap Pit Stop`), si la vuelta coincidió con la llegada de lluvia (`Transición Climática`), si se produjo a menos de 4 vueltas del final para buscar el punto extra (`Caza de Vuelta Rápida`), o si la duración fue anómala (>32s en las primeras vueltas por cambio de alerón: `Daño / Pinchadura / Imprevisto`).

### C. Cautela sobre la Tabla de Safety Cars (`safety_cars_procesado.csv`)
* La tabla histórica de Safety Cars contiene **127 despliegues cruzados con vueltas exactas de bandera** para la era moderna.
* Al ser un registro con menor frecuencia muestral que la telemetría continua de vueltas, las conclusiones sobre el Safety Car deben interpretarse como **tendencias descriptivas sólidas pero no como leyes deterministas**, reconociendo la alta componente de azar vinculada a la vuelta exacta de neutralización.

---

## 🗂️ 3. Catálogo de Datasets Procesados y sus Fuentes (20 Archivos)

| Archivo CSV | Registros | Fuente Primaria | Rol y Contenido |
| :--- | :---: | :--- | :--- |
| **`circuits_procesado.csv`** | 31 | FIA Homologation / F1DB | Geometría oficial: longitud en km, cantidad de curvas y densidad de curvas por km. |
| **`races_procesado.csv`** | 173 | Ergast FIA | Calendario oficial de Grandes Premios 2018–2025 con fechas y sedes. |
| **`race_weather_procesado.csv`** | 173 | Sensores FIA / OpenF1 | Clima oficial por sesión: temperatura de aire, pista (°C), humedad y lluvia. |
| **`pitstops_procesado.csv`** | 5.941 | Ergast FIA Timing | Paradas en boxes con número de parada, vuelta y duración total en pitlane (segundos). |
| **`lap_times_procesado.csv`** | 187.143 | Ergast FIA Timing | Cronometraje oficial vuelta a vuelta para calcular ritmo y vueltas limpias. |
| **`race_results_procesado.csv`** | 3.458 | Ergast FIA | Clasificación final de cada piloto, puesto de largada, llegada, puntos y abandonos. |
| **`tyre_stints_procesado.csv`** | 9.035 | OpenF1 (2023-25) / Ergast | Stints de carrera con compuestos de neumáticos reales y duraciones en vueltas. |
| **`pirelli_nominations_procesado.csv`** | 173 | Pirelli Motorsport Press | Asignación oficial obligatoria de compuestos secos C1 a C5 por Gran Premio. |
| **`driver_standings_procesado.csv`** | 36.193 | Ergast FIA | Tabla histórica de posiciones del campeonato de pilotos (1950–2025). |
| **`constructor_standings_procesado.csv`** | 14.036 | Ergast FIA | Tabla histórica de posiciones del campeonato de constructores (1958–2025). |
| **`safety_cars_procesado.csv`** | 375 | TracingInsights / Ergast | Despliegues de Safety Car en carrera (127 despliegues modernos con vueltas). |
| **`virtual_safety_cars_procesado.csv`** | 113 | TracingInsights / Ergast | Despliegues de Virtual Safety Car (VSC) desde 2015 a 2025. |
| **`red_flags_procesado.csv`** | 101 | FIA Incident Reports / Ergast | Banderas rojas e interrupciones de sesión con vuelta del incidente. |
| **`qualifying_results_procesado.csv`** | 3.455 | Ergast FIA | Tiempos de Q1, Q2, Q3 y posición final de clasificación del sábado. |
| **`sprint_results_procesado.csv`** | 480 | Ergast / OpenF1 | Resultados y puntos oficiales de carreras sprint del formato moderno (2021–2025). |
| **`drivers_procesado.csv`** | 864 | Ergast FIA | Padrón maestro de pilotos con código de 3 letras, número permanente y nacionalidad. |
| **`constructors_procesado.csv`** | 212 | Ergast FIA | Padrón maestro de escuderías con trazabilidad de nacionalidad y nombre de chasis. |
| **`seasons_procesado.csv`** | 76 | Ergast FIA | Registro de temporadas completadas desde 1950 hasta 2025. |
| **`status_procesado.csv`** | 137 | Ergast FIA | Diccionario oficial de códigos de finalización (mecánicos, accidentes, vueltas perdidas). |
| **`tabla_maestra_confiable.csv`** | 3.458 | Cruce Multifuente depurado | Tabla analítica integrada (Piloto x Carrera) con 32 dimensiones empíricas. |

---

## 🏆 4. Datasets Maestros Unificados (`datasets_maestros/`)

| Archivo CSV | Filas x Cols | Granularidad | Rol en el Sistema |
| :--- | :---: | :--- | :--- |
| **`tabla_maestra_carreras_pilotos.csv`** | 3.458 x 45 | Piloto x Gran Premio | Cruce de rendimiento deportivo, clasificación del sábado, clima, paradas, ritmo y consistencia en vueltas limpias. |
| **`tabla_maestra_stints_estrategia.csv`** | 9.035 x 21 | Stint de Neumático | Desglose de neumáticos, duración de stint, compuestos reales, asfalto y columna inferida de `motivo_parada`. |
| **`tabla_maestra_circuitos_carreras.csv`**| 173 x 34 | Gran Premio / Pista | Nivel macro: arquetipos de pista, correlación de predictibilidad qualy-carrera y promedios colectivos. |
| **`fichas_circuitos_demo.csv`** | 6 x 16 | Circuito Seleccionado | Fichas de síntesis para la interfaz de la aplicación: Mónaco, Interlagos, Silverstone, Monza, Marina Bay y Spa. |

---

## 📏 5. Reglas y Umbrales Documentados

### A. Clasificación de Condición Climática (`condicion_clima`)
1. **`Lluvia / Pista Húmeda`:** `hubo_lluvia == 1` (declarada oficialmente por la FIA).
2. **`Muy Caluroso`:** `temp_pista_c >= 40.0°C` (temperatura de asfalto crítica para degradación térmica).
3. **`Caluroso`:** `30.0°C <= temp_pista_c < 40.0°C` (rango operativo estándar de F1).
4. **`Templado / Fresco`:** `temp_pista_c < 30.0°C` (asfalto frío sin precipitación).

### B. Algoritmo de Vueltas Limpias y Consistencia (`consistencia_ritmo_seg`)
* **Filtro 1 (Largada):** Se descarta la Vuelta 1 (partida detenida con aceleración inicial).
* **Filtro 2 (Paradas en Boxes):** A partir de `pitstops.csv`, se eliminan la vuelta de entrada a boxes ($L$) y la vuelta de salida ($L+1$), las cuales suman $+20$ a $+25$ segundos por el límite de velocidad en el pitlane.
* **Filtro 3 (Neutralizaciones y Despistes):** Se eliminan vueltas cuyo tiempo supere en más de un 10% a la mediana del propio piloto ($\text{tiempo} > 1.10 \times \text{mediana}$), aislando períodos de Safety Car, Virtual Safety Car o banderas amarillas.
* **Métrica Final:** $\sigma = \sqrt{\frac{1}{N-1} \sum (t_i - \bar{t})^2}$ calculada sobre las vueltas limpias restantes.
