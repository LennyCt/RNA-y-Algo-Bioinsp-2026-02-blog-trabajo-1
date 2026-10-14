"""Curvas de convergencia: mejor valor hallado vs. evaluaciones equivalentes (mediana de N corridas)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from experimentos import METHODS, run_once

LABELS = {"gd": "Descenso por gradiente", "ga": "Algoritmo genético",
          "pso": "PSO", "de": "Evolución diferencial"}
COLORS = {"gd": "#7a7a7a", "ga": "#e69f00", "pso": "#009e73", "de": "#0072b2"}
FLOOR = 1e-16   # piso para poder dibujar en escala logarítmica f = 0


def best_so_far(curve, grid):
    """Valor de la curva (costo, f) en cada punto de la rejilla (escalón; el mejor hasta ese costo)."""
    cost = np.array([c for c, _ in curve])
    value = np.minimum.accumulate(np.array([v for _, v in curve]))
    index = np.searchsorted(cost, grid, side="right") - 1
    out = np.where(index >= 0, value[np.clip(index, 0, None)], np.nan)
    return out


def median_curves(function, dim, runs, base_seed, budget, params=None):
    grid = np.linspace(0, budget, 400)
    result = {}
    for method in METHODS:
        stack = []
        for i in range(runs):
            r = run_once(method, function, dim, base_seed + i, budget,
                         (params or {}).get(method))
            curve = r["curve"]
            end = curve[-1][1]                       # tras terminar, el valor final se mantiene
            curve = curve + [(budget * 2, end)]
            stack.append(best_so_far(curve, grid))
        result[method] = np.nanmedian(np.array(stack), axis=0)
    return grid, result


def plot_convergence(function, dim, runs, base_seed, budget, output, params=None):
    grid, curves = median_curves(function, dim, runs, base_seed, budget, params)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for method, values in curves.items():
        ax.plot(grid, np.maximum(values, FLOOR), label=LABELS[method], color=COLORS[method], lw=2)
    ax.set_yscale("log")
    ax.set_xlabel("Evaluaciones equivalentes de f (1 gradiente = 2·dim evaluaciones)")
    ax.set_ylabel("Mejor f hallado (mediana de %d corridas)" % runs)
    ax.set_title(f"{function.capitalize()} en {dim}D: convergencia")
    ax.grid(alpha=0.3, which="both")
    ax.legend(frameon=False)
    fig.tight_layout()
    path = Path(output) / f"convergencia_{function}_{dim}d.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
