# Trabajo 1: optimización numérica, metaheurística y combinatoria

Redes neuronales y algoritmos bioinspirados, Universidad Nacional de Colombia, semestre 2026-02.

```
optimizacion/
├── Optimizacion_heuristica/        descenso por gradiente vs. AG, PSO y evolución diferencial
└── Optimizacion_combinatoria/             TSP de las 47 capitales peninsulares: ACO y algoritmo genético
requirements.txt        entorno único, versiones fijas
README.md               este archivo
```

Cada parte tiene su propio README con todos los comandos y opciones.

## Instalación (una sola vez)

Python 3.11 o superior (probado con 3.13).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Inicio rápido

Los comandos se ejecutan **desde la carpeta de cada parte**.

```bash
# Parte 1: comparación de 30 corridas y un GIF (sin Internet)
cd Optimizacion_heuristica
python main.py compare
python main.py animate --method pso --function rastrigin --seed 3

# Parte 2: demostración con datos sintéticos (sin Internet) y pruebas
cd Optimizacion_combinatoria
python main.py run --demo
python -m unittest discover -s tests
```

Detalles: [`Optimizacion_heuristica/README.md`](Optimizacion_heuristica/README.md) y [`Optimizacion_combinatoria/README.md`](Optimizacion_combinatoria/README.md).

## Reproducibilidad

- Semillas fijas y documentadas: parte 1, base 12345; parte 2, base 42 (`Optimizacion_combinatoria/config/experiment.json`).
  En ambas, la corrida *i* usa `semilla_base + i`.
- Los parámetros se cambian por línea de comandos o por un JSON, sin editar el código.
- Figuras y GIF se regeneran desde el código.
- Los datos del TSP viven en `Optimizacion_combinatoria/data/`; una vez generados, la ejecución no necesita Internet.
