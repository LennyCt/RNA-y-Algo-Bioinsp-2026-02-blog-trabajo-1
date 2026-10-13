"""Punto de entrada del TSP de las 47 capitales peninsulares (ACO y algoritmo genético).

Todo se controla por línea de comandos o por config/experiment.json; no hace falta
editar el código. La línea de comandos tiene prioridad sobre el JSON.

  python main.py validate                       # revisa los datos y la matriz de costos
  python main.py run                            # ACO y AG con los datos reales de data/
  python main.py run --demo                     # datos SINTÉTICOS de data/demo (para probar)
  python main.py run --algorithms ga --runs 10 --hourly-value 35
  python main.py run --param aco.evaporation_rate=0.5 --param genetic_algorithm.generations=800
  python main.py sweep --demo --runs 1          # ¿cambia la ruta al variar el valor de la hora?
  python main.py sweep --algorithms aco ga --hourly-values 0 10 20 40 80 160
  python main.py -h | run -h | sweep -h

Parámetros por algoritmo: --param aco.nombre=valor | --param genetic_algorithm.nombre=valor
(aliases: ga.nombre=valor). La semilla de la corrida i es `seed + i`.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import tsp_data
import tsp_visualizacion as viz
from aco import ant_colony_optimization
from algoritmo_genetico import genetic_algorithm

ALGORITHMS = {"aco": ant_colony_optimization, "ga": genetic_algorithm}
FOLDER = {"aco": "aco", "ga": "genetic_algorithm"}
ALIAS = {"aco": "aco", "ga": "ga", "genetic_algorithm": "ga"}

DEFAULT_CONFIG = Path("config/experiment.json")
DEFAULT_GEOJSON = Path("data/spain_peninsular.geojson")
BUILTIN = {"seed": 42, "runs": 5, "hourly_value_eur": 20.0,
           "consumption_l_per_100km": 6.0, "fuel_price_eur_per_liter": 1.60}


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
def parse_params(items: list[str] | None) -> dict[str, dict]:
    """--param aco.alpha=2 --param ga.generations=300  ->  {'aco': {...}, 'ga': {...}}."""
    params: dict[str, dict] = {key: {} for key in ALGORITHMS}
    for item in items or []:
        if "=" not in item or "." not in item.split("=", 1)[0]:
            raise SystemExit(f"--param '{item}': use el formato algoritmo.nombre=valor")
        key, value = item.split("=", 1)
        algorithm, name = key.split(".", 1)
        if algorithm not in ALIAS:
            raise SystemExit(f"--param '{item}': algoritmo desconocido (use aco o genetic_algorithm)")
        try:
            value = json.loads(value)   # 50, 0.35, true, null...
        except json.JSONDecodeError:
            pass                        # se queda como texto
        params[ALIAS[algorithm]][name] = value
    return params


def load_config(path: Path | None) -> dict:
    if path is None:
        path = DEFAULT_CONFIG
    if not path.exists():
        if path != DEFAULT_CONFIG:
            raise SystemExit(f"No existe el archivo de configuración: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def validate_param_names(algorithm: str, params: dict) -> None:
    allowed = set(inspect.signature(ALGORITHMS[algorithm]).parameters) - {"cost_matrix", "city_names", "seed"}
    unknown = set(params) - allowed
    if unknown:
        raise SystemExit(f"Parámetros desconocidos para {algorithm}: {sorted(unknown)}. "
                         f"Permitidos: {sorted(allowed)}")


def resolve_settings(args) -> dict:
    """Combina valores integrados < config JSON < línea de comandos."""
    config = load_config(args.config)
    vehicle = config.get("vehicle", {})

    def pick(cli_value, *config_values, builtin):
        if cli_value is not None:
            return cli_value
        for value in config_values:
            if value is not None:
                return value
        return builtin

    cli_params = parse_params(args.param)
    params = {}
    for algorithm in ALGORITHMS:
        section = dict(config.get(FOLDER[algorithm], {}))
        section.update(cli_params[algorithm])
        validate_param_names(algorithm, section)
        params[algorithm] = section

    return {
        "seed": pick(args.seed, config.get("seed"), builtin=BUILTIN["seed"]),
        "runs": pick(getattr(args, "runs", None), config.get("runs"), builtin=BUILTIN["runs"]),
        "hourly_value_eur": pick(getattr(args, "hourly_value", None), config.get("hourly_value_eur"),
                                 builtin=BUILTIN["hourly_value_eur"]),
        "consumption_l_per_100km": pick(args.consumption, vehicle.get("consumption_l_per_100km"),
                                        builtin=BUILTIN["consumption_l_per_100km"]),
        "fuel_price_eur_per_liter": pick(args.fuel_price, vehicle.get("fuel_price_eur_per_liter"),
                                         builtin=BUILTIN["fuel_price_eur_per_liter"]),
        "vehicle_documented": bool(vehicle.get("documented", False)),
        "vehicle": vehicle,
        "params": params,
    }


def load_data(args, settings: dict) -> tuple[dict, Path]:
    """Carga componentes de costo (reales o demo) y devuelve la carpeta de resultados."""
    if args.demo:
        data_dir, synthetic = Path("data/demo"), True
        print("=" * 72)
        print("AVISO: DATOS SINTÉTICOS DE DEMOSTRACIÓN (data/demo). No usar en el reporte.")
        print("=" * 72)
    else:
        data_dir, synthetic = Path(args.data_dir), False
        if not settings["vehicle_documented"]:
            warnings.warn("config/experiment.json: el vehículo y el precio del combustible NO están "
                          "documentados (vehicle.documented=false); se usan valores de ejemplo.",
                          stacklevel=2)
    try:
        components = tsp_data.load_components(data_dir, allow_synthetic=synthetic)
    except (FileNotFoundError, ValueError) as error:
        hint = ("\nGenere los datos reales con:  python build_data.py  (necesita Internet una vez)\n"
                "o pruebe el código con datos sintéticos:  python main.py run --demo")
        raise SystemExit(f"No se pudieron cargar los datos de {data_dir}: {error}{hint}")
    output = Path(args.output) / ("demo" if args.demo else "")
    return components, output


# ---------------------------------------------------------------------------
# Ejecución de los algoritmos
# ---------------------------------------------------------------------------
def run_algorithm(algorithm: str, cost: np.ndarray, names: list[str], seed: int,
                  runs: int, params: dict) -> list[dict]:
    """Ejecuta `runs` corridas independientes (semillas seed, seed+1, ...)."""
    results = []
    for i in range(runs):
        started = time.perf_counter()
        result = ALGORITHMS[algorithm](cost, names, seed=seed + i, **params)
        results.append({"run": i, "seed": seed + i, "result": result,
                        "seconds": time.perf_counter() - started})
    return results


def best_of(runs: list[dict]) -> dict:
    return min(runs, key=lambda item: item["result"]["cost"])


def route_signature(route: list[str]) -> str:
    return hashlib.md5("->".join(route).encode("utf-8")).hexdigest()[:8]


def cost_inputs(settings: dict, hourly_value: float | None = None):
    return (settings["hourly_value_eur"] if hourly_value is None else hourly_value,
            settings["consumption_l_per_100km"], settings["fuel_price_eur_per_liter"])


def cmd_validate(args) -> None:
    settings = resolve_settings(args)
    components, _ = load_data(args, settings)
    cost = tsp_data.build_cost_matrix(components, *cost_inputs(settings))
    names = components["names"]
    print(f"Ciudades: {len(names)} | matrices {cost.shape} | "
          f"asimétrica: {not np.allclose(cost, cost.T)}")
    off_diagonal = cost[~np.eye(len(names), dtype=bool)]
    print(f"Costo por tramo (EUR): mín {off_diagonal.min():.2f}, mediana "
          f"{np.median(off_diagonal):.2f}, máx {off_diagonal.max():.2f}")
    print(f"Parámetros: valor hora {settings['hourly_value_eur']} EUR/h, "
          f"{settings['consumption_l_per_100km']} L/100 km, "
          f"{settings['fuel_price_eur_per_liter']} EUR/L")
    print("Datos válidos.")


def cmd_run(args) -> None:
    settings = resolve_settings(args)
    components, output = load_data(args, settings)
    names, cities = components["names"], components["cities"]
    hourly, consumption, fuel_price = cost_inputs(settings)
    cost = tsp_data.build_cost_matrix(components, hourly, consumption, fuel_price)
    geojson = Path(args.geojson) if args.geojson else (DEFAULT_GEOJSON if DEFAULT_GEOJSON.exists() else None)

    print(f"Valor de la hora: {hourly} EUR/h | consumo {consumption} L/100 km | "
          f"combustible {fuel_price} EUR/L | semilla base {settings['seed']} | "
          f"corridas {settings['runs']}")
    rows = []
    for algorithm in args.algorithms:
        params = settings["params"][algorithm]
        print(f"\n[{algorithm.upper()}] {settings['runs']} corridas, parámetros: "
              f"{params or 'por defecto'}")
        runs = run_algorithm(algorithm, cost, names, settings["seed"], settings["runs"], params)
        best = best_of(runs)
        result = best["result"]
        folder = output / FOLDER[algorithm]
        folder.mkdir(parents=True, exist_ok=True)

        pd.DataFrame([{"run": r["run"], "seed": r["seed"], "final_cost_eur": r["result"]["cost"],
                       "seconds": round(r["seconds"], 3)} for r in runs]
                     ).to_csv(folder / "runs.csv", index=False)
        viz.save_best_solution_history(result["history"], folder / "best_history.csv")
        viz.plot_best_route(cities, result, folder / "best_route.png", geojson,
                            title=f"Mejor recorrido ({algorithm.upper()}, semilla {best['seed']})")
        if not args.no_animate:
            viz.animate_tsp_evolution(cities, result["history"], folder / "evolution.gif", geojson,
                                      title=f"Evolución de la mejor ruta ({algorithm.upper()})")

        breakdown = tsp_data.route_breakdown(result["route"], components, hourly, consumption, fuel_price)
        (folder / "best_route.json").write_text(json.dumps({
            "algorithm": result["algorithm"], "seed": best["seed"], "hourly_value_eur": hourly,
            "consumption_l_per_100km": consumption, "fuel_price_eur_per_liter": fuel_price,
            "params": params, "route": result["route"], "breakdown": breakdown,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        costs = np.array([r["result"]["cost"] for r in runs])
        rows.append({
            "algorithm": result["algorithm"], "runs": len(runs), "hourly_value_eur": hourly,
            "best_cost_eur": costs.min(), "mean_cost_eur": costs.mean(),
            "std_cost_eur": costs.std(ddof=1) if len(costs) > 1 else 0.0,
            "worst_cost_eur": costs.max(),
            "mean_seconds": float(np.mean([r["seconds"] for r in runs])),
            **{key: breakdown[key] for key in ("distance_km", "time_h", "time_cost_eur",
                                               "toll_eur", "fuel_eur")},
            "best_route": " -> ".join(result["route"]),
        })

    comparison = pd.DataFrame(rows)
    output.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(output / "comparison.csv", index=False)
    pd.set_option("display.width", 200)
    print("\n" + comparison.drop(columns="best_route").to_string(
        index=False, float_format=lambda value: f"{value:,.2f}"))
    print(f"\nResultados en {output}/")


# ---------------------------------------------------------------------------
# Estudio del valor de la hora
# ---------------------------------------------------------------------------
def lower_envelope(routes: list[dict]) -> list[dict]:
    """Envolvente inferior de costo(h) = h * T + M sobre un conjunto de rutas, para h >= 0.

    Para una ruta fija el costo es lineal en el valor de la hora h (T = horas de viaje,
    M = peajes + combustible). La mejor ruta de un conjunto cambia exactamente en los
    vértices de la envolvente inferior de esas rectas, que se calculan de forma exacta:
    desde h = 0 se elige la ruta más barata en dinero y, mientras haya rutas más rápidas,
    se pasa a la que la supera antes (cruce h* = (M_b - M_a) / (T_a - T_b)).
    Devuelve segmentos con from_h y to_h (to_h = None significa "sin límite superior").
    """
    current = min(routes, key=lambda r: (r["money_eur"], r["time_h"]))
    segments, start = [], 0.0
    while True:
        faster = [r for r in routes if r["time_h"] < current["time_h"] - 1e-12]
        crossings = [((r["money_eur"] - current["money_eur"]) / (current["time_h"] - r["time_h"]), r)
                     for r in faster]
        crossings = [(h, r) for h, r in crossings if h >= start - 1e-9]
        if not crossings:
            segments.append({**current, "from_h": start, "to_h": None})
            return segments
        h_next = min(h for h, _ in crossings)
        winner = min((r for h, r in crossings if abs(h - h_next) < 1e-9), key=lambda r: r["time_h"])
        segments.append({**current, "from_h": start, "to_h": h_next})
        current, start = winner, h_next


def route_record(route: list[str], components: dict, consumption: float, fuel_price: float,
                 found_by: str) -> dict:
    """Componentes del costo de una ruta que no dependen del valor de la hora."""
    breakdown = tsp_data.route_breakdown(route, components, 0.0, consumption, fuel_price)
    return {"route_id": route_signature(route), "route": " -> ".join(route),
            "time_h": breakdown["time_h"], "distance_km": breakdown["distance_km"],
            "toll_eur": breakdown["toll_eur"], "fuel_eur": breakdown["fuel_eur"],
            "money_eur": breakdown["toll_eur"] + breakdown["fuel_eur"], "found_by": found_by}


def cmd_sweep(args) -> None:
    """Estudia cómo cambia la mejor ruta con el valor de la hora.

    Los heurísticos son estocásticos: comparar solo la ruta final de cada valor de la hora
    mezcla el ruido del algoritmo con cambios reales. Por eso se reúnen TODAS las rutas
    encontradas (en todas las corridas y valores) y se calcula su envolvente inferior exacta.
    """
    settings = resolve_settings(args)
    components, output = load_data(args, settings)
    names = components["names"]
    _, consumption, fuel_price = cost_inputs(settings)
    hourly_values = sorted(set(args.hourly_values))

    pool: dict[str, dict] = {}
    raw_rows = []
    for algorithm in args.algorithms:
        for hourly in hourly_values:
            cost = tsp_data.build_cost_matrix(components, hourly, consumption, fuel_price)
            runs = run_algorithm(algorithm, cost, names, settings["seed"], settings["runs"],
                                 settings["params"][algorithm])
            for item in runs:  # cada ruta final entra al conjunto de candidatas
                record = route_record(item["result"]["route"], components, consumption, fuel_price,
                                      f"{algorithm}@{hourly:g}")
                pool.setdefault(record["route_id"], record)
            result = best_of(runs)["result"]
            breakdown = tsp_data.route_breakdown(result["route"], components, hourly,
                                                 consumption, fuel_price)
            raw_rows.append({"algorithm": result["algorithm"], "hourly_value_eur": hourly,
                             "best_cost_eur": result["cost"], **breakdown,
                             "route_id": route_signature(result["route"])})
            print(f"[{algorithm.upper()}] h={hourly:>7.2f} EUR/h  costo {result['cost']:>10.2f}  "
                  f"{breakdown['time_h']:.2f} h  peajes {breakdown['toll_eur']:.2f}")

    segments = lower_envelope(list(pool.values()))
    sweep = pd.DataFrame(raw_rows)
    best_known = [min(s["money_eur"] + h * s["time_h"] for s in segments) for h in sweep["hourly_value_eur"]]
    sweep["best_known_cost_eur"] = best_known
    sweep["gap_vs_best_known_eur"] = sweep["best_cost_eur"] - sweep["best_known_cost_eur"]

    output.mkdir(parents=True, exist_ok=True)
    sweep.to_csv(output / "hourly_sweep.csv", index=False)
    pd.DataFrame(segments).to_csv(output / "hourly_sweep_envelope.csv", index=False)
    plot_sweep(sweep, segments, output / "hourly_sweep.png")

    print(f"\nRutas distintas encontradas: {len(pool)} | tramos de la envolvente inferior: {len(segments)}")
    print("Mejor ruta conocida según el valor de la hora (cambia en cada 'desde'):")
    for segment in segments:
        upper = "∞" if segment["to_h"] is None else f"{segment['to_h']:.2f}"
        print(f"  h en [{segment['from_h']:.2f}, {upper}) EUR/h -> ruta {segment['route_id']}: "
              f"{segment['time_h']:.2f} h, peajes {segment['toll_eur']:.2f} EUR, "
              f"{segment['distance_km']:.0f} km (hallada por {segment['found_by']})")
    if len(segments) == 1:
        print("  La ruta no cambió en ningún valor de la hora (h >= 0).")
    worst_gap = sweep["gap_vs_best_known_eur"].max()
    print(f"Máximo sobrecosto de la mejor corrida frente a la mejor ruta conocida: {worst_gap:.2f} EUR "
          "(si es > 0, el heurístico no encontró la mejor ruta conocida en algún valor de la hora).")
    print("Los cambios son los de las rutas encontradas: son una cota superior de los óptimos reales.")
    print(f"\nResultados en {output}/")


def plot_sweep(sweep: pd.DataFrame, segments: list[dict], output_path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    h_max = max(sweep["hourly_value_eur"].max(), segments[-1]["from_h"] * 1.5, 1.0)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, key, label in ((axes[0], "time_h", "Horas totales de viaje"),
                           (axes[1], "money_eur", "Peajes + combustible (EUR)")):
        for segment in segments:  # mejor ruta conocida: función escalonada
            end = h_max if segment["to_h"] is None else segment["to_h"]
            ax.hlines(segment[key], segment["from_h"], end, color="black", linewidth=2.5,
                      label="Mejor ruta conocida" if segment is segments[0] else None)
            if segment["from_h"] > 0:
                ax.axvline(segment["from_h"], color="gray", linestyle=":", alpha=0.6)
        for algorithm, group in sweep.groupby("algorithm"):
            values = group["toll_eur"] + group["fuel_eur"] if key == "money_eur" else group[key]
            ax.scatter(group["hourly_value_eur"], values, label=f"{algorithm}: mejor corrida", zorder=3)
        ax.set_ylabel(label)
        ax.set_xlabel("Valor de la hora (EUR/h)")
        ax.set_xscale("symlog", linthresh=1.0)
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.suptitle("Ruta vs. valor de la hora (líneas punteadas: la mejor ruta conocida cambia)")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Línea de comandos
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--config", type=Path, help=f"JSON de configuración (por defecto {DEFAULT_CONFIG})")
        p.add_argument("--demo", action="store_true", help="usar datos SINTÉTICOS de data/demo")
        p.add_argument("--data-dir", default="data", help="carpeta con los datos reales")
        p.add_argument("--output", default="results", help="carpeta de resultados")
        p.add_argument("--seed", type=int, help="semilla base (corrida i usa seed+i)")
        p.add_argument("--consumption", type=float, help="consumo, L/100 km")
        p.add_argument("--fuel-price", type=float, help="precio del combustible, EUR/L")
        p.add_argument("--param", action="append", metavar="algoritmo.nombre=valor",
                       help="hiperparámetro de un algoritmo (se puede repetir)")

    def algorithms(p: argparse.ArgumentParser, default: list[str]) -> None:
        p.add_argument("--algorithms", nargs="+", default=default, choices=list(ALGORITHMS),
                       help="aco, ga")
        p.add_argument("--runs", type=int, help="corridas independientes por configuración")

    check = sub.add_parser("validate", help="revisa los datos y la matriz de costos")
    common(check)
    check.add_argument("--hourly-value", type=float, help="valor de la hora, EUR/h")

    run = sub.add_parser("run", help="ejecuta ACO y/o AG y guarda tablas, figuras y GIF")
    common(run)
    algorithms(run, list(ALGORITHMS))
    run.add_argument("--hourly-value", type=float, help="valor de la hora, EUR/h")
    run.add_argument("--no-animate", action="store_true", help="no generar el GIF")
    run.add_argument("--geojson", help="GeoJSON con la silueta de España peninsular")

    sweep = sub.add_parser("sweep", help="¿cambia la ruta al variar el valor de la hora?")
    common(sweep)
    algorithms(sweep, ["aco"])
    sweep.add_argument("--hourly-values", nargs="+", type=float,
                       default=[0, 10, 20, 40, 80, 160],
                       help="valores de la hora a estudiar, EUR/h")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    {"validate": cmd_validate, "run": cmd_run, "sweep": cmd_sweep}[args.command](args)


if __name__ == "__main__":
    main()
