"""Corridas independientes, estadísticas y tasa de éxito."""
import numpy as np
import pandas as pd

from problemas import Objective
from descenso_gradiente import gradient_descent
from algoritmo_genetico import genetic_algorithm
from pso import pso
from evolucion_diferencial import differential_evolution

METHODS = {
    "gd": gradient_descent,
    "ga": genetic_algorithm,
    "pso": pso,
    "de": differential_evolution,
}


def run_once(method, function, dim, seed, budget, params=None, record=False):
    """Una corrida. Devuelve el diccionario del algoritmo + conteos de evaluaciones."""
    obj = Objective(function, dim)
    rng = np.random.default_rng(seed)
    res = METHODS[method](obj, rng, budget=budget, record=record,
                          **(params or {}))
    res.update(n_f=obj.n_f, n_grad=obj.n_grad, eq_cost=obj.equivalent_cost,
               x_error=float(np.linalg.norm(res["best_x"] - obj.x_opt)))
    return res


def run_series(method, function, dim, runs=30, base_seed=0, budget=10000,
          params=None):
    """`corridas` corridas independientes (semillas semilla_base ... +corridas-1).
    Las mismas semillas se usan para todos los métodos."""
    rows = []
    for i in range(runs):
        r = run_once(method, function, dim, base_seed + i, budget, params)
        rows.append(dict(method=method, function=function, dim=dim, seed=base_seed + i,
                          f_final=r["best_f"], n_f=r["n_f"], n_grad=r["n_grad"],
                          eq_cost=r["eq_cost"], x_error=r["x_error"]))
    return pd.DataFrame(rows)


def summarize(df, threshold):
    """Estadísticas por (función, dim, método)."""
    def agg(g):
        return pd.Series(dict(
            mean=g.f_final.mean(), std=g.f_final.std(ddof=1),
            best=g.f_final.min(), worst=g.f_final.max(),
            success_pct=100 * (g.f_final < threshold).mean(),
            n_f_mean=g.n_f.mean(), n_grad_mean=g.n_grad.mean(),
            eq_cost_mean=g.eq_cost.mean()))
    return (df.groupby(["function", "dim", "method"], sort=False)
              .apply(agg, include_groups=False).reset_index())
