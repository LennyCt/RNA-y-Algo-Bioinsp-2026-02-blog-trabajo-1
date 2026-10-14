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
