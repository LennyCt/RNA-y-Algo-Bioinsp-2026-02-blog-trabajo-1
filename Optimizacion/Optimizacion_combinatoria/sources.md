# Fuentes y criterios de los datos (Parte 2: TSP)

Todos los datos se consultaron el **13 de octubre de 2026** y están guardados en `data/`:
la ejecución no necesita Internet. El detalle técnico de cada archivo de `data/valhalla/`
(servidor, endpoints, advertencias por autopista) está en
[`data/valhalla/FUENTES.md`](data/valhalla/FUENTES.md).

## Ciudades y coordenadas

- `data/cities.csv`: las 47 capitales de provincia de la España peninsular (50 provincias menos
  Palma, Las Palmas de Gran Canaria y Santa Cruz de Tenerife; Ceuta y Melilla no son provincias).
- Coordenadas WGS84 de Wikidata (propiedad P625 de cada municipio), consultadas en
  https://query.wikidata.org. La columna `wikidata` guarda el identificador de cada ciudad para
  que cualquiera pueda verificarla.
- Versión anterior: las coordenadas originales se habían escrito de memoria con un asistente de IA,
  sin fuente. Al compararlas con Wikidata difieren como máximo 1,6 km (A Coruña), pero no eran
  citables y se reemplazaron.

## Distancias y tiempos

- Motor: **Valhalla 3.9.1**, servidor público de FOSSGIS (https://valhalla1.openstreetmap.de),
  teselas generadas desde OpenStreetMap el 2026-10-13 a las 11:26 UTC. Endpoint `/route`, perfil auto.
- Para cada par se usa la ruta más rápida con peajes permitidos (`use_tolls=1`). Distancia en km y
  tiempo en horas: `data/distances.csv` y `data/travel_times.csv`, generados por
  `python importar_valhalla.py` a partir de `data/valhalla/rutas_valhalla.csv`.
- Las rutas se calcularon en ambos sentidos y se promediaron, así que las matrices son simétricas.
- Se usa la misma ruta para el tiempo, la distancia y los peajes. Así el costo de cada tramo
  corresponde a un único viaje real.
- Excepción: si la ruta más rápida cruza Portugal (Badajoz–Pontevedra, Huelva–Pontevedra), se usa
  la ruta sin peajes por España, porque los peajes portugueses no se modelan.
- **Comparación con OSRM.** La primera versión usaba OSRM (Table API,
  https://router.project-osrm.org). Esos datos se conservan en `data/osrm/`. Frente a Valhalla, la
  diferencia relativa de distancia tiene mediana 1,7 %, percentil 95 de 16,5 % y máximo de 50 %.
  Por eso no se mezclan peajes medidos sobre una ruta con tiempos y distancias de la otra.

## Peajes

- Tarifas 2026 para vehículos ligeros, tarifa general sin descuentos: `data/valhalla/peajes_2026.csv`,
  con una fila por autopista y su URL oficial (Ministerio de Transportes y Movilidad Sostenible,
  SEITT, Bidegi, Interbiak, Audenasa).
- Km recorridos en cada autopista de peaje: medidos arista por arista sobre la ruta de Valhalla
  (`/trace_attributes`) con las vías marcadas `toll=yes` en OpenStreetMap
  (`data/valhalla/raw/peajes_aristas.txt`). El nombre de cada vía en OSM se asigna a su grupo
  tarifario con `data/valhalla/mapa_refs_peaje.csv`.
- Cálculo para el par i→j:

      tarifa_por_km(autopista) = peaje oficial de un recorrido de referencia / km de ese recorrido
      peaje(i, j) = Σ km_en_autopista × tarifa_por_km  +  cuotas fijas (túneles de Artxanda)

  Los km de referencia se miden con el mismo motor de rutas (`data/valhalla/build_rutas.py`).
- `data/toll_costs.csv` tiene una fila por par dirigido (47 × 46 = 2162). En `source_url` van las URL
  de las tarifas usadas; en `notes`, los km por autopista. Si la ruta no pasa por ninguna autopista
  de peaje, el peaje es 0 y la fuente es la propia ruta de Valhalla.
- Un peaje vacío nunca se interpreta como cero: `main.py` se niega a ejecutar si falta algún par.
- **Limitaciones** (se discuten en el reporte):
  - Prorratear por km es una aproximación: en la realidad se paga por tramo o caseta.
  - Se supone el mismo peaje en los dos sentidos.
  - No se modelan descuentos por recurrencia ni tarifas nocturnas.
- **Advertencias** (detalle en `data/valhalla/FUENTES.md`):
  - **AP-68 Bilbao–Zaragoza**: la concesión termina el **10/11/2026**. Después de esa fecha su peaje
    es 0. Para simularlo, poner `peaje_eur = 0` en la fila AP-68 de `peajes_2026.csv` y volver a
    ejecutar `python importar_valhalla.py`.
  - **AP-15**: la columna de la tabla de Audenasa se interpretó como vehículos ligeros. Pendiente de
    confirmar.
  - **C-32**: tarifa tomada de una fuente secundaria (Diari Més, que cita el DOGC).
  - **R-4 y AP-36**: el PDF se titula 2026 pero dice "En vigor desde el 1 de enero de 2025".
  - Autopistas ya liberadas, que no se cobran: AP-1 Burgos–Armiñón (2018), AP-4 y AP-7
    Tarragona–Alicante (2019), AP-7 Tarragona–La Jonquera y AP-2 (2021), AP-7 Circunvalación de
    Alicante (2025).

## Vehículo y combustible

- Vehículo: **Dacia Sandero TCe 90** (gasolina, 67 kW / 91 CV). Consumo WLTP combinado
  **5,3 L/100 km**. Fuente: ADAC Autokatalog,
  https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/dacia/sandero/3generation/334757
- Precio: **Gasolina 95 E5, 1,7961 €/L**. Es la media simple de 10 238 estaciones de la España
  peninsular (mediana 1,815; percentil 10: 1,679; percentil 90: 1,889).
  Fuente: Geoportal de Gasolineras del Ministerio para la Transición Ecológica y el Reto
  Demográfico (MITECO), API REST
  https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/,
  dato del 13/10/2026 a las 22:02:48. Medias por provincia en
  `data/valhalla/combustible_por_provincia_2026-10-13.csv`.
- Limitaciones: es una media no ponderada por ventas y corresponde a un solo día.
- Fórmula: `combustible(i, j) = km(i, j) × 5,3 / 100 × 1,7961`. Estos valores están en
  `config/experiment.json` y se pueden cambiar con `--consumption` y `--fuel-price`.

## Valor de la hora

- Es un parámetro experimental en €/h, no un dato de carretera. `python main.py sweep` estudia a
  partir de qué valor cambia la ruta. Los valores ensayados se registran en el reporte.

## Silueta de España

- Polígonos de provincias: `data/valhalla/spain-provinces.geojson`, del repositorio click_that_hood
  de Code for America (GitHub), consultado el 2026-10-13. data/spain_peninsular.geojson se genera con python preparar_mapa.py, que quita Illes Balears, Las Palmas, Santa Cruz de Tenerife, Ceuta y Melilla (quedan las 47 provincias peninsulares).

## Datos sintéticos de demostración

- `data/demo/` contiene datos **inventados** para probar el código sin Internet: distancia en línea
  recta × 1,25 con ruido y peajes aleatorios. Se generan con `python build_data.py --demo`.
  **No se pueden citar en el reporte.** Toda ejecución con ellos imprime un aviso.