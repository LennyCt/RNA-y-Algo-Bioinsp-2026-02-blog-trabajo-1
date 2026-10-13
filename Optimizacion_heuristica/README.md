# Parte 1: optimización numérica (descenso por gradiente vs. metaheurísticas)

Compara descenso por gradiente, algoritmo genético, PSO y evolución diferencial sobre dos funciones
de prueba, en 2 y 3 dimensiones. El entorno es el de la raíz del repositorio; los comandos se ejecutan
desde esta carpeta (`parte1_numerica/`).

- **Funciones elegidas**: Rosenbrock (valle estrecho, mal condicionada) y Rastrigin (muchos mínimos
  locales). Dominios: Rosenbrock en [-2.048, 2.048], Rastrigin en [-5.12, 5.12]; ambas con mínimo
  global f = 0.
- **Conteo justo de evaluaciones**: se reportan `n_f` (evaluaciones de f) y `n_grad` (de ∇f) por
  separado. Equivalencia: un gradiente por diferencias centrales cuesta `2·n` evaluaciones de f en
  dimensión `n`, así que `costo_eq = n_f + 2·n·n_grad`. El presupuesto de cada método se mide en
  esa unidad. Se usa el gradiente analítico por velocidad, cobrándole ese costo.
- **Corridas**: 30 independientes por configuración, mismas semillas para todos los métodos
  (semilla base **12345**; la corrida *i* usa `12345 + i`). Se reportan media, desviación, mejor, peor y
  tasa de éxito (por defecto f < 1e-3).

## Comandos

```bash
python main.py check          # compara gradientes analíticos con diferencias finitas
python main.py compare        # 30 corridas, 2 funciones, 2D y 3D, 4 métodos 
python main.py compare --functions rastrigin --dims 2 --methods gd de --runs 10
python main.py compare --threshold 1e-2 --budget-per-dim 20000
python main.py compare --param ga.pop_size=80 --param de.F=0.8 --param gd.line_search=fixed --param gd.lr=1e-3
python main.py compare --config config.json
python main.py animate --method gd  --function rosenbrock --seed 3     
python main.py animate --method pso --function rastrigin  --seed 3 --max-frames 30
python main.py -h             # también: compare -h, animate -h
```

Salidas: `resultados/tablas/` (`runs.csv`, `summary.csv`) y `resultados/animaciones/` (GIF).
`python funciones.py` y `python visualizacion.py` son scripts de prueba sueltos (el segundo genera
una gráfica y dos GIF de ejemplo).

Hiperparámetros con `--param método.nombre=valor`: `gd` (`lr`, `line_search` = `armijo` o `fixed`, `c`, `beta`,
`max_backtrack`, `grad_tol`), `ga` (`pop_size`, `crossover_prob`, `mutation_prob`, `mutation_sigma`, `blx_alpha`,
`tournament_k`, `elitism`), `pso` (`pop_size`, `w`, `c1`, `c2`, `vmax_frac`), `de` (`pop_size`, `F`, `CR`).
