# TSP de las 47 capitales peninsulares: colonia de hormigas y algoritmo genético

Recorrido cerrado por las 47 capitales de provincia de la España peninsular. El costo de ir de
`i` a `j` es

```
costo[i,j] = valor_hora · horas[i,j]  +  peaje[i,j]  +  km[i,j] · consumo/100 · precio_litro      (EUR)
```

Se resuelve con ACO (`aco.py`) y con un algoritmo genético (`genetic_algorithm.py`), y se estudia a
partir de qué valor de la hora cambia la ruta óptima.

## Instalación

El entorno es único para las dos partes: ver el `README.md` y el `requirements.txt` de la raíz del
repositorio. Todos los comandos de este documento se ejecutan desde la carpeta `parte2_tsp/`.

## Prueba rápida (sin Internet, datos sinteticos)

```bash
python build_data.py --demo        # genera data/demo
python main.py run --demo          # ACO + AG, 3 corridas cada uno, GIF y figuras
python main.py sweep --demo --runs 1   
python -m unittest discover -s tests   # 35 pruebas 
```

Resultados en `results/demo/`.

## Flujo con datos reales

1. **Coordenadas**: verificar `data/cities.csv` contra una fuente primaria y regístrenla en `data/sources.md`.
2. **Distancias y tiempos** (una sola vez, con Internet):
   `python build_data.py` → `data/distances.csv` (km), `data/travel_times.csv` (h), `data/osrm_metadata.json`.
   El servicio público de OSRM tiene límites: no lo ejecuten repetidamente ni en paralelo.
3. **Peajes**: completen `data/toll_costs.csv` (una fila por par dirigido): `toll_eur`, `toll_status=verified`,
   `source_url` y `consultation_date`. Un campo vacío **no** equivale a cero; `main.py` se niega a correr si
   queda algún par sin verificar.
4. `python build_data.py --skip-osrm` regenera `fuel_costs.csv` y `cost_matrix.csv`; luego
   `python main.py validate` y `python main.py run`.

## Comandos

```bash
python main.py validate                      # revisa datos y matriz de costos
python main.py run                           # ACO y AG sobre los datos reales (data/)
python main.py run --algorithms ga --runs 10 --hourly-value 35
python main.py run --param aco.evaporation_rate=0.5 --param genetic_algorithm.generations=800
python main.py run --no-animate              # sin GIF
python main.py sweep --algorithms aco ga --hourly-values 0 10 20 40 80 160
python main.py -h        # también: run -h, sweep -h
```

| Opción | Por defecto | Significado |
|---|---|---|
| `--demo` | — | usa `data/demo` (sintético) y escribe en `results/demo/` |
| `--data-dir` | `data` | carpeta de datos reales |
| `--output` | `results` | carpeta de resultados |
| `--config` | `config/experiment.json` | JSON; la línea de comandos tiene prioridad |
| `--seed` | 42 | semilla base: la corrida *i* usa `seed + i` |
| `--runs` | 3 (config) | corridas independientes |
| `--algorithms` | `aco ga` (`run`), `aco` (`sweep`) | algoritmos |
| `--hourly-value` | 20 | valor de la hora, EUR/h |
| `--consumption`, `--fuel-price` | del JSON | L/100 km y EUR/L |
| `--param algoritmo.nombre=valor` | — | hiperparámetro, repetible (`aco` o `genetic_algorithm`) |
| `--geojson` | `data/spain_peninsular.geojson` si existe | silueta de España para las figuras |
| `--hourly-values` (sweep) | `0 10 20 40 80 160` | valores de la hora a estudiar |

Hiperparámetros: ACO `ant_count, iterations, alpha, beta, evaporation_rate, pheromone_deposit,
min_pheromone_fraction, start_city`; AG `population_size, generations, mutation_rate, crossover_rate,
elite_count, tournament_size, start_city`. Los valores de `config/experiment.json` (ACO 150 iteraciones,
AG 200 individuos × 400 generaciones) están elegidos para que la demostración dure ~1 minuto; no son
valores ajustados para el reporte.

## Salidas

- `results/<algoritmo>/`: `runs.csv` (costo y tiempo por corrida), `best_history.csv`, `best_route.png`,
  `best_route.json` (ruta y desglose tiempo/peajes/combustible), `evolution.gif`.
- `results/comparison.csv`: estadísticas por algoritmo (mejor, media, desviación, peor, segundos) y desglose
  de la mejor ruta.
- `sweep`: `hourly_sweep.csv`, `hourly_sweep_envelope.csv`, `hourly_sweep.png`.

## ¿Cambia la ruta con el valor de la hora?

Para una ruta fija el costo es lineal en la hora: `costo(h) = h·T + M` (T = horas de viaje, M = peajes +
combustible). Comparar solo la ruta final de cada `h` mezcla el ruido de los heurísticos con cambios reales:
con datos sintéticos el AG llegó a dar rutas *más lentas* al subir `h`, algo imposible para un óptimo.
Por eso `sweep` reúne **todas las rutas encontradas** (todas las corridas y valores de `h`) y calcula la
envolvente inferior de sus rectas, cuyos vértices son los valores de `h` donde cambia la mejor ruta
conocida (`hourly_sweep_envelope.csv`). Esos cambios son una cota superior de los óptimos reales: un
heurístico no garantiza optimalidad. La columna `gap_vs_best_known_eur` mide cuánto se alejó cada corrida
de la mejor ruta conocida.

## Estructura

```
main.py                  interfaz de línea de comandos (validate, run, sweep)
aco.py, genetic_algorithm.py   algoritmos
tsp_data.py              carga de datos, matriz de costos, desglose de rutas
tsp_visualization.py     figuras y GIF sobre el mapa
build_data.py            OSRM -> matrices; plantilla de peajes; datos demo
config/experiment.json   semilla, corridas, vehículo, hiperparámetros
data/                    cities.csv, toll_costs.csv (plantilla), sources.md, demo/
tests/                   35 pruebas (unittest)
results/                 salidas
```

## Reproducibilidad

- Semilla base 42 (config) y corrida *i* con `seed + i`; mismas semillas, mismos resultados (hay prueba).
- Entorno con versiones fijas en el `requirements.txt` de la raíz del repositorio.
- Una vez generados los CSV de `data/`, nada depende de Internet ni de APIs externas.
- Figuras y GIF se regeneran con `main.py run`.

