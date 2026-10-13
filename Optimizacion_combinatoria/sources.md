# Fuentes y criterios de los datos

Documento vivo: complétenlo y consérvenlo con el reporte final. Cada dato debe tener
fuente y **fecha de consulta**. Estado actual de cada bloque entre corchetes.

## Ciudades y coordenadas [PENDIENTE DE VERIFICAR]

- `cities.csv`: las 47 capitales de provincia de la España peninsular (50 provincias menos
  Palma, Las Palmas de Gran Canaria y Santa Cruz de Tenerife; Ceuta y Melilla no son provincias).
- Las coordenadas (WGS84, 4 decimales) se escribieron **de memoria del asistente de IA**, sin
  consultar una fuente. Hay que contrastarlas con una fuente primaria (p. ej. IGN, INE o el
  Ayuntamiento de cada capital) y anotar aquí fuente y fecha. Criterio a documentar: punto
  representativo del casco urbano.
- Control de cordura ya automatizado (`tests/test_cost_matrix.py`): 47 nombres únicos, rangos
  geográficos y cuatro distancias en línea recta desde Madrid dentro de ±5 % de valores
  aproximados. **No sustituye la verificación.**

## Distancias y tiempos [PENDIENTE: requiere ejecutar `build_data.py` con Internet]

- Motor: OSRM, Table API (`/table/v1/driving`), perfil `driving`.
- Endpoint por defecto: https://router.project-osrm.org (servicio público con límites de uso).
- Documentación: https://project-osrm.org/docs/v5.24.0/api/ (enlace tomado del script original; verifíquenlo).
- Se guardan `distances.csv` (km) y `travel_times.csv` (h), y `osrm_metadata.json` con endpoint y
  fecha de consulta.
- OSRM devuelve la ruta **más rápida** según el perfil: no necesariamente la de menor distancia ni
  la de menor costo. La matriz puede ser asimétrica (A→B ≠ B→A).
- Para máxima reproducibilidad: instancia OSRM propia con una instantánea de OpenStreetMap
  identificada por fecha.

## Peajes [PENDIENTE: 2162 pares dirigidos por verificar]

- `toll_costs.csv` tiene una fila por par dirigido (47 × 46) con `toll_status =
  pending_official_verification`. `main.py` **se niega a ejecutar** con datos reales mientras
  quede alguno sin importe, estado `verified`, `source_url` y `consultation_date`.
- Un peaje vacío nunca se interpreta como cero. Cero solo es válido si se verificó que el trayecto
  no paga peaje, con `toll_status=verified` y una fuente que lo justifique.
- Método a documentar: identificar los tramos de peaje del itinerario devuelto por OSRM y sumar las
  tarifas oficiales de cada concesionaria para la clase de vehículo elegida (turismo, clase 1).
  La red de autopistas de peaje ha cambiado mucho en los últimos años: anoten la fecha de cada
  tarifa y vuelvan a comprobarla antes de publicar.
- Fuente general indicada en el script original (verifíquenla):
  https://administracion.gob.es/tu-espacio-europeo/derechos-obligaciones/ciudadanos/vehiculos/normas-trafico-viales/peajes-vinetas
- Detección automática (`toll_tools.py`), método `geometry`: ruta completa de OSRM Route API
  (`overview=full`) cruzada con la geometría de las vías `toll=yes` (motorway/trunk/primary/secondary/tertiary y
  enlaces) descargada de Overpass (`out geom`); método alternativo `classes` (clase `toll` de OSRM). Inventario
  opcional de casetas y pórticos (`barrier=toll_booth`, `highway=toll_gantry`). Fuente de los datos: © OpenStreetMap contributors (ODbL). Fecha de consulta en
  `toll_detection.jsonl` y `osm_toll_metadata.json`. Ambas dependen de las mismas etiquetas, no son
  validación independiente. Estados `derived_osrm_no_toll` y `estimated_per_km` NO son importes oficiales.
- Tarifas por km: `data/toll_rates.csv` (cada fila con fuente y fecha). La fila `*` es una tarifa media
  (mediana 0.105 EUR/km de la tabla de https://www.autofacil.es/pejaes-cuesta-kilometro/, que cita a
  Automovilistas Europeos Asociados, datos de 2019, consultada el 2026-10-13): APROXIMACIÓN, sin clase de vehículo
  especificada ni actualización; importes exactos: `data/toll_overrides.csv`.
- Las fuentes por tramo (URL de cada concesionaria) van en la columna `source_url`.

## Combustible y vehículo [PENDIENTE]

- Vehículo (modelo, motorización), consumo homologado y fuente (ficha técnica del fabricante o
  base oficial de homologación): por elegir. Se registran en `config/experiment.json`
  (`vehicle`); ahí hay valores de ejemplo con `documented: false`.
- Precio del combustible, fuente y fecha de consulta: por completar en el mismo bloque.
- Fórmula: `distancia_km × consumo_L/100km / 100 × precio_EUR/L`.

## Valor de la hora

- Parámetro experimental en EUR/h, no un dato de carretera. `python main.py sweep` estudia a partir
  de qué valor cambia la ruta; registren en el reporte los valores ensayados.

## Silueta de España (opcional) [PENDIENTE]

- Para dibujar el contorno en las figuras y GIF, guarden un GeoJSON de España peninsular (sin islas)
  en `data/spain_peninsular.geojson`; `main.py` lo usa automáticamente. Sin él, la ruta se dibuja sobre
  el plano longitud/latitud y se emite una advertencia.
- Posible fuente: Natural Earth (dominio público, https://www.naturalearthdata.com/), filtrando los
  polígonos de España continental. Anoten la fuente y la fecha.

## Datos sintéticos de demostración

- `data/demo/` contiene datos **inventados** (distancia en línea recta × 1.25 con ruido, peajes
  aleatorios) generados con `python build_data.py --demo`. Sirven para probar el código sin Internet.
  **No se pueden citar en el reporte.** Toda ejecución con ellos imprime un aviso.
