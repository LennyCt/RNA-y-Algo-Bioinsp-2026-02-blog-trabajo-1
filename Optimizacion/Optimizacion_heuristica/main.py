"""
Punto de entrada. Todo se controla por línea de comandos o por un JSON.

  python main.py check
  python main.py compare --functions rosenbrock rastrigin --dims 2 3 --runs 30
  python main.py compare --param ga.pop_size=80 --param gd.line_search=fixed --param gd.lr=1e-3
  python main.py animate --method gd  --function rosenbrock --seed 3
  python main.py animate --method pso --function rastrigin  --seed 3
  python main.py curves --runs 30                     (PNG de convergencia en resultados/graficas)
  python main.py compare --config config.json      (las claves son los mismos flags)

Parámetros por método: --param method.name=value  (method in gd, ga, pso, de)
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from problemas import PROBLEMS, check_gradients
from experimentos import METHODS, run_series, summarize, run_once

BASE_SEED = 12345   # semilla por defecto, documentada en el README


def parse_params(items):
    params = {m: {} for m in METHODS}
    for item in items or []:
        key, value = item.split("=", 1)
        method, name = key.split(".", 1)
        try:
            value = json.loads(value)          # 1e-3, 50, true...
        except json.JSONDecodeError:
            pass                               # se queda como string ("fixed")
        params[method][name] = value
    return params


def cmd_compare(a):
    params = parse_params(a.param)
    all_results = []
    for fn in a.functions:
        for dim in a.dims:
            budget = a.budget_per_dim * dim
            for m in a.methods:
                all_results.append(run_series(m, fn, dim, a.runs, a.seed, budget,
                                   params.get(m)))
    df = pd.concat(all_results, ignore_index=True)
    table = summarize(df, a.threshold)

    output = Path(a.output)
    output.mkdir(parents=True, exist_ok=True)
    df.to_csv(output / "runs.csv", index=False)
    table.to_csv(output / "summary.csv", index=False)
    pd.set_option("display.width", 200, "display.float_format", "{:.3e}".format)
    print(f"\nUmbral de éxito: f < {a.threshold}  |  corridas: {a.runs}  |  "
          f"semilla base: {a.seed}  |  presupuesto: {a.budget_per_dim}*dim "
          "(en evaluaciones de f equivalentes; 1 gradiente = 2*dim evaluaciones)\n")
    print(table.to_string(index=False))
    print(f"\nGuardado en {output}/")


def subsample(df, max_frames, population):
    """Reduce el número de fotogramas (cada uno redibuja la superficie 3D, es lento).
    Siempre conserva el primer y el último fotograma."""
    if population:
        gens = sorted(df["generation"].unique())
        if len(gens) <= max_frames:
            return df
        chosen = {gens[i] for i in np.linspace(0, len(gens) - 1, max_frames).astype(int)}
        return df[df["generation"].isin(chosen)]
    if len(df) <= max_frames:
        return df
    return df.iloc[np.linspace(0, len(df) - 1, max_frames).astype(int)].reset_index(drop=True)


def cmd_animate(a):
    import visualizacion as vz           # import tardío: evita cargar matplotlib sin necesidad
    params = parse_params(a.param)
    res = run_once(a.method, a.function, 2, a.seed, a.budget_per_dim * 2,
                   params.get(a.method), record=True)
    df = pd.DataFrame(res["trajectory"])
    df = subsample(df, a.max_frames, population=a.method != "gd")
    p = PROBLEMS[a.function]
    ranges = (p["bounds"], p["bounds"])
    f = p["f"]
    name = f"{a.function}_{a.method}_s{a.seed}.gif"
    if a.method == "gd":
        vz.create_3d_animation(f, df, *ranges, output_filename=name,
                               title=f"Descenso por gradiente - {a.function}")
    else:
        vz.create_population_animation(f, df, *ranges, output_filename=name,
                                       title=f"{a.method.upper()} - {a.function}")
    print(f"f final = {res['best_f']:.3e}")


def cmd_curves(a):
    from curvas import plot_convergence
    params = parse_params(a.param)
    for fn in a.functions:
        for dim in a.dims:
            path = plot_convergence(fn, dim, a.runs, a.seed, a.budget_per_dim * dim,
                                    a.output, params)
            print("Guardado", path)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="Compara gradientes analíticos con diferencias centrales")

    def add_common(p):
        p.add_argument("--config", help="JSON con valores para estos flags")
        p.add_argument("--seed", type=int, default=BASE_SEED)
        p.add_argument("--budget-per-dim", type=int, default=5000,
                       help="presupuesto = este valor * dim (evaluaciones de f equivalentes)")
        p.add_argument("--param", action="append", metavar="method.name=value")

    pc = sub.add_parser("compare", help="Corridas independientes y estadísticas")
    add_common(pc)
    pc.add_argument("--functions", nargs="+", default=["rosenbrock", "rastrigin"],
                    choices=PROBLEMS)
    pc.add_argument("--dims", nargs="+", type=int, default=[2, 3])
    pc.add_argument("--methods", nargs="+", default=list(METHODS), choices=METHODS)
    pc.add_argument("--runs", type=int, default=30)
    pc.add_argument("--threshold", type=float, default=1e-3)
    pc.add_argument("--output", default="resultados/tablas")

    pv = sub.add_parser("curves", help="PNG de convergencia (mediana de las corridas)")
    add_common(pv)
    pv.add_argument("--functions", nargs="+", default=["rosenbrock", "rastrigin"],
                    choices=PROBLEMS)
    pv.add_argument("--dims", nargs="+", type=int, default=[2, 3])
    pv.add_argument("--runs", type=int, default=30)
    pv.add_argument("--output", default="resultados/graficas")

    pn = sub.add_parser("animate", help="GIF de una corrida en 2D")
    add_common(pn)
    pn.add_argument("--method", required=True, choices=METHODS)
    pn.add_argument("--function", required=True, choices=PROBLEMS)
    pn.add_argument("--max-frames", type=int, default=40,
                    help="máximo de fotogramas del GIF (se submuestrea la corrida)")

    # Segunda pasada: valores del JSON como nuevos defaults (la línea de comandos manda)
    pre_args, _ = parser.parse_known_args()
    if getattr(pre_args, "config", None):
        cfg = json.loads(Path(pre_args.config).read_text())
        for sp in sub.choices.values():
            sp.set_defaults(**cfg)
    a = parser.parse_args()

    if a.cmd == "check":
        check_gradients(2); check_gradients(3)
    elif a.cmd == "compare":
        cmd_compare(a)
    elif a.cmd == "curves":
        cmd_curves(a)
    else:
        cmd_animate(a)


if __name__ == "__main__":
    main()
