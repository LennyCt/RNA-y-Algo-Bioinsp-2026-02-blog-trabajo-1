"""Construye los datos del TSP de las 47 capitales peninsulares.

Dos modos:

1) Datos reales (requiere Internet SOLO esta vez):
       python build_data.py --cities data/cities.csv --output data
   Consulta OSRM (Table API) y guarda distances.csv (km), travel_times.csv (h) y
   osrm_metadata.json (fecha, endpoint). Crea la plantilla toll_costs.csv, que
   hay que completar con tarifas oficiales verificadas (OSRM no da precios).
   Cuando todos los peajes estén verificados genera fuel_costs.csv y cost_matrix.csv.

       python build_data.py --output data --skip-osrm      # recalcular sin consultar OSRM

2) Datos SINTÉTICOS de demostración (sin Internet):
       python build_data.py --demo
   Escribe en data/demo/. Son datos inventados (distancia en línea recta por un
   factor, peajes aleatorios) para probar el código. NO sirven para el reporte.

El servicio público de OSRM tiene límites de uso: no lo ejecuten repetidamente ni en
paralelo. Para una recopilación reproducible, usen una instancia propia con una
instantánea fija de OpenStreetMap y registren su fecha.
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import tsp_data

DEFAULT_ENDPOINT = "https://router.project-osrm.org"
EXPECTED_CITIES = 47


def load_cities(path: Path) -> pd.DataFrame:
    """Lee cities.csv y valida que sean las 47 capitales peninsulares."""
    cities = tsp_data.load_cities(path.parent) if path.name == "cities.csv" else pd.read_csv(path)
    if len(cities) != EXPECTED_CITIES:
        raise ValueError(f"Se esperaban {EXPECTED_CITIES} ciudades y hay {len(cities)}.")
    if not cities["longitude"].between(-10, 5).all():
        raise ValueError("Hay longitudes fuera del rango esperado para España peninsular.")
    if not cities["latitude"].between(34, 45).all():
        raise ValueError("Hay latitudes fuera del rango esperado para España peninsular.")
    return cities


def osrm_table(cities: pd.DataFrame, endpoint: str, source_batch_size: int = 8,
               pause_seconds: float = 1.0, session: Any = None
               ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pide a OSRM las matrices de distancia (m) y duración (s), por lotes de orígenes."""
    if session is None:
        import requests  # import tardío: solo se necesita al consultar OSRM
        session = requests.Session()
        session.headers.update({"User-Agent": "TSP-47-capitales-academic-project/1.0"})

    coords = ";".join(f"{row.longitude:.6f},{row.latitude:.6f}"
                      for row in cities.itertuples(index=False))
    count = len(cities)
    distance_matrix: list[Any] = [None] * count
    duration_matrix: list[Any] = [None] * count

    for start in range(0, count, source_batch_size):
        source_indices = list(range(start, min(start + source_batch_size, count)))
        url = f"{endpoint.rstrip('/')}/table/v1/driving/{coords}"
        params = {
            "sources": ";".join(map(str, source_indices)),
            "destinations": ";".join(map(str, range(count))),
            "annotations": "distance,duration",
        }
        response = session.get(url, params=params, timeout=120)
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") != "Ok":
            raise RuntimeError(f"OSRM no devolvió Ok: {payload.get('code')} - {payload}")
        batch_distances = payload.get("distances")
        batch_durations = payload.get("durations")
        if batch_distances is None or batch_durations is None:
            raise RuntimeError("OSRM no devolvió ambas matrices; revise el endpoint.")
        for local_row, source_index in enumerate(source_indices):
            distance_matrix[source_index] = batch_distances[local_row]
            duration_matrix[source_index] = batch_durations[local_row]
        if start + source_batch_size < count:
            time.sleep(pause_seconds)

    names = cities["city"].tolist()
    distance_df = pd.DataFrame(distance_matrix, index=names, columns=names, dtype=float)
    duration_df = pd.DataFrame(duration_matrix, index=names, columns=names, dtype=float)
    if distance_df.isna().any().any() or duration_df.isna().any().any():
        raise RuntimeError("OSRM devolvió pares sin ruta (valores nulos).")
    for name in names:  # la diagonal es exacta, no depende del servicio
        distance_df.loc[name, name] = 0.0
        duration_df.loc[name, name] = 0.0
    distance_df.index.name = duration_df.index.name = "city"
    return distance_df, duration_df


def create_toll_template(cities: pd.DataFrame, path: Path) -> None:
    """Una fila por par dirigido; los peajes quedan vacíos hasta verificarlos."""
    rows = []
    for origin in cities["city"]:
        for destination in cities["city"]:
            same = origin == destination
            rows.append({
                "origin": origin,
                "destination": destination,
                "toll_eur": 0.0 if same else "",
                "toll_status": "not_applicable" if same else "pending_official_verification",
                "vehicle_class": "turismo_clase_1",
                "source_url": "",
                "consultation_date": "",
                "notes": "",
            })
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8")


def write_derived(output: Path, components: dict, hourly_value: float,
                  consumption: float, fuel_price: float) -> None:
    """Escribe fuel_costs.csv y cost_matrix.csv a partir de los componentes."""
    names = components["names"]
    fuel = tsp_data.fuel_matrix(components["distance_km"], consumption, fuel_price)
    cost = tsp_data.build_cost_matrix(components, hourly_value, consumption, fuel_price)
    for filename, matrix in (("fuel_costs.csv", fuel), ("cost_matrix.csv", cost)):
        frame = pd.DataFrame(matrix, index=names, columns=names)
        frame.index.name = "city"
        frame.to_csv(output / filename, encoding="utf-8")


def haversine_km(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Distancia en línea recta entre todos los pares (km)."""
    lon_r, lat_r = np.radians(lon), np.radians(lat)
    dlon = lon_r[None, :] - lon_r[:, None]
    dlat = lat_r[None, :] - lat_r[:, None]
    a = (np.sin(dlat / 2) ** 2
         + np.cos(lat_r)[:, None] * np.cos(lat_r)[None, :] * np.sin(dlon / 2) ** 2)
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


def build_demo_data(cities_path: Path, output: Path, seed: int = 7,
                    hourly_value: float = 20.0, consumption: float = 6.0,
                    fuel_price: float = 1.60) -> None:
    """Genera datos SINTÉTICOS (inventados) para probar el código sin Internet.

    Distancia = línea recta * 1.25 con ruido por par dirigido (matriz asimétrica).
    Los pares con peaje son más rápidos (-15 % de tiempo) y cuestan 0.08 EUR/km,
    para que el valor de la hora produzca un compromiso tiempo/dinero.
    """
    cities = load_cities(cities_path)
    names = cities["city"].tolist()
    count = len(names)
    rng = np.random.default_rng(seed)

    straight = haversine_km(cities["longitude"].to_numpy(), cities["latitude"].to_numpy())
    noise = rng.uniform(-0.03, 0.03, (count, count))
    distance = straight * 1.25 * (1 + noise)

    tolled_upper = np.triu(rng.random((count, count)) < 0.5, k=1)
    tolled = tolled_upper | tolled_upper.T  # el peaje es el mismo en ambos sentidos
    speed = 70.0 + 20.0 * np.minimum(distance / 300.0, 1.0)  # km/h
    time_h = distance / speed
    time_h = np.where(tolled, time_h * 0.85, time_h)
    toll = np.where(tolled, 0.08 * distance, 0.0)
    for matrix in (distance, time_h, toll):
        np.fill_diagonal(matrix, 0.0)

    output.mkdir(parents=True, exist_ok=True)
    cities.to_csv(output / "cities.csv", index=False, encoding="utf-8")
    for filename, matrix in (("distances.csv", distance), ("travel_times.csv", time_h)):
        frame = pd.DataFrame(matrix, index=names, columns=names)
        frame.index.name = "city"
        frame.to_csv(output / filename, encoding="utf-8")

    rows = []
    today = date.today().isoformat()
    for i, origin in enumerate(names):
        for j, destination in enumerate(names):
            same = i == j
            rows.append({
                "origin": origin, "destination": destination,
                "toll_eur": 0.0 if same else round(float(toll[i, j]), 4),
                "toll_status": "not_applicable" if same else tsp_data.STATUS_SYNTHETIC,
                "vehicle_class": "demo",
                "source_url": "" if same else "synthetic://demo",
                "consultation_date": "" if same else today,
                "notes": "DATO SINTETICO DE DEMOSTRACION",
            })
    pd.DataFrame(rows).to_csv(output / "toll_costs.csv", index=False, encoding="utf-8")

    components = tsp_data.load_components(output, allow_synthetic=True)
    write_derived(output, components, hourly_value, consumption, fuel_price)
    (output / "README_DEMO.txt").write_text(
        "DATOS SINTETICOS DE DEMOSTRACION. No provienen de OSRM ni de tarifas reales.\n"
        "Sirven solo para probar el codigo; no usar en el reporte.\n", encoding="utf-8")
    print(f"Datos sintéticos de demostración escritos en {output}/")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Construye los datos del TSP (OSRM + plantilla de peajes) o datos demo.")
    parser.add_argument("--cities", type=Path, default=Path("data/cities.csv"))
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--pause", type=float, default=1.0)
    parser.add_argument("--hourly-value", type=float, default=20.0, help="EUR/h de referencia")
    parser.add_argument("--consumption", type=float, default=6.0, help="L/100 km")
    parser.add_argument("--fuel-price", type=float, default=1.60, help="EUR/L")
    parser.add_argument("--skip-osrm", action="store_true",
                        help="No consultar OSRM; reutiliza distances.csv y travel_times.csv.")
    parser.add_argument("--demo", action="store_true",
                        help="Genera datos sintéticos en data/demo (no son reales).")
    args = parser.parse_args()

    if args.demo:
        out = args.output if args.output != Path("data") else Path("data/demo")
        build_demo_data(args.cities, out, hourly_value=args.hourly_value,
                        consumption=args.consumption, fuel_price=args.fuel_price)
        return

    args.output.mkdir(parents=True, exist_ok=True)
    cities = load_cities(args.cities)
    distance_file = args.output / "distances.csv"
    time_file = args.output / "travel_times.csv"
    toll_file = args.output / "toll_costs.csv"

    if not args.skip_osrm:
        distance_df, duration_df = osrm_table(cities, args.endpoint, args.batch_size, args.pause)
        (distance_df / 1000.0).to_csv(distance_file, encoding="utf-8")      # m -> km
        (duration_df / 3600.0).to_csv(time_file, encoding="utf-8")          # s -> h
        (args.output / "osrm_metadata.json").write_text(json.dumps({
            "source": "OSRM Table API",
            "endpoint": args.endpoint,
            "retrieved_on": date.today().isoformat(),
            "routing_profile": "driving",
            "units": {"distances.csv": "km", "travel_times.csv": "h"},
            "note": "OSRM devuelve la ruta más rápida según el perfil; no necesariamente "
                    "la de menor distancia ni la de menor costo monetario.",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Distancias y tiempos guardados en {args.output}/")

    if not toll_file.exists():
        create_toll_template(cities, toll_file)
        print(f"Plantilla de peajes creada: {toll_file} (complétela con tarifas verificadas)")

    try:
        components = tsp_data.load_components(args.output)
        write_derived(args.output, components, args.hourly_value, args.consumption,
                      args.fuel_price)
        print(f"Matriz de costos creada: {args.output / 'cost_matrix.csv'}")
    except (ValueError, FileNotFoundError) as error:
        print(f"Costo final pendiente: {error}")


if __name__ == "__main__":
    main()
