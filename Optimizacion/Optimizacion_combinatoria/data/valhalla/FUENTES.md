# Fuentes de los datos del TSP (todas consultadas el 13 de octubre de 2026)

La ejecución NO necesita internet: todo lo descargado está guardado en esta carpeta.
Las horas son hora peninsular española salvo que se indique otra cosa.

| Archivo | Contenido | Fuente | Consulta |
|---|---|---|---|
| `capitales.csv` | 47 capitales, coordenadas (WGS84) e identificador Wikidata | Wikidata Query Service, propiedad P625 de cada municipio (https://query.wikidata.org) | 2026-10-13 |
| `rutas_valhalla.csv` | Tiempo y distancia por carretera entre cada par, con peajes permitidos (`use_tolls=1`) y evitándolos (`use_tolls=0`); km recorridos en cada vía de peaje | Servidor público de Valhalla 3.9.1 de FOSSGIS (https://valhalla1.openstreetmap.de), teselas generadas desde OpenStreetMap el 2026-10-13 11:26 UTC. Endpoints `/route` y `/trace_attributes` | 2026-10-13 |
| `peajes_2026.csv` | Tarifa de cada autopista de peaje (vehículos ligeros) | Ministerio de Transportes y Movilidad Sostenible (PDF "Peajes vigentes desde el 01/01/2026" de cada autopista), SEITT, Bidegi, Interbiak, Audenasa y prensa que cita el DOGC; detalle por fila en el propio CSV | 2026-10-13 |
| `mapa_refs_peaje.csv` | Correspondencia entre el nombre de la vía en OpenStreetMap y el grupo tarifario | Elaboración propia | — |
| `combustible_por_provincia_2026-10-13.csv` | Precio medio de Gasolina 95 E5 y Gasóleo A por provincia | API REST del Ministerio (Geoportal de gasolineras): https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/ — fecha del dato "13/10/2026 22:02:48" | 2026-10-13 |
| `spain-provinces.geojson` | Polígonos de provincias (solo para dibujar) | Repositorio click_that_hood de Code for America (GitHub) | 2026-10-13 |

## Vehículo

Dacia Sandero TCe 90 Expression (gasolina, 67 kW / 91 CV, producción 04/24–12/25):
consumo WLTP combinado **5,3 L/100 km**, CO₂ 119 g/km. Valores por tipo de vía (WLTP):
corta distancia 6,7; periurbano 4,9; carretera 4,5; autopista 5,7 L/100 km.
Fuente: ADAC Autokatalog, https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/dacia/sandero/3generation/334757 (consultado 2026-10-13).

## Combustible

Gasolina 95 E5, media simple de 10 238 estaciones de la España peninsular (se excluyen
Baleares, Las Palmas, Santa Cruz de Tenerife, Ceuta y Melilla): **1,7961 €/L**
(mediana 1,815; percentil 10: 1,679; percentil 90: 1,889).
Gasóleo A, misma muestra: 1,8930 €/L (10 627 estaciones).

## Advertencias conocidas

* **AP-68 Bilbao–Zaragoza**: la concesión termina el **10/11/2026** (Ministerio de Transportes,
  página "Peajes dependientes de la AGE"). A la fecha de consulta sigue siendo de peaje.
  Para simular la situación posterior: `--set tariff_overrides.AP-68=0`.
* **AP-7 Circunvalación de Alicante**: liberada por Acuerdo del Consejo de Ministros de 9/12/2025.
* Liberadas en años anteriores (no se cobran): AP-1 Burgos–Armiñón (30/11/2018), AP-4 y AP-7
  Tarragona–Alicante (31/12/2019), AP-7 Tarragona–La Jonquera y AP-2 (31/08/2021).
* Las tarifas usadas son las **generales de un vehículo ligero sin descuentos** (pago en efectivo
  o tarjeta en las autopistas de SEITT, y el nivel "normal"/"diurno" donde hay franjas horarias o
  niveles especiales). No se modelan bonificaciones por recurrencia ni tarifas nocturnas.
* Autopistas de peaje que **ninguna** ruta más rápida entre capitales usa (y por eso no tienen
  fila en `peajes_2026.csv`): AP-41 Madrid–Toledo, AP-46, AP-7 Alicante–Cartagena,
  AP-7 Cartagena–Vera y M-12 (también C-16 y otras autopistas autonómicas no usadas).
  Las tarifas 2026 de las cuatro primeras se consultaron en las mismas fuentes oficiales.
* Tarifa de la C-32 (Garraf y Cubelles): fuente secundaria (Diari Més, que cita la resolución
  del DOGC); no se consultó el DOGC directamente.
* Rutas por Portugal (Badajoz–Pontevedra, Huelva–Pontevedra): no se modelan peajes portugueses;
  para esos pares solo se usa la ruta sin peajes por España.
* `raw/peajes_aristas.txt` indica el método de medición de cada par: `walk` (arista exacta),
  `snap` (ajuste al mapa por trozos) o `maniobras` (respaldo para rutas de más de 1 000 km).