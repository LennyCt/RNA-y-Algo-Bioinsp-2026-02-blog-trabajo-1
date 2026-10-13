"""Carga de datos del TSP y construcción de la matriz de costos.

Los datos viven en un directorio con estos archivos (todos guardados en el
repositorio, así que la ejecución no depende de Internet):

    cities.csv        city, longitude, latitude
    distances.csv     matriz cuadrada, kilómetros (índice y columnas = ciudades)
    travel_times.csv  matriz cuadrada, horas
    toll_costs.csv    formato largo: origin, destination, toll_eur, toll_status,
                      source_url, consultation_date, ...
    fuel_costs.csv    matriz cuadrada, euros (derivada de distances.csv)
    cost_matrix.csv   matriz cuadrada, euros (derivada, valor de la hora de referencia)

Costo de ir de i a j (en euros):

    cost[i, j] = hourly_value * time_h[i, j] + toll_eur[i, j]
                 + distance_km[i, j] * consumption / 100 * fuel_price
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_CITY_COLUMNS = ("city", "longitude", "latitude")
STATUS_VERIFIED = "verified"
STATUS_SYNTHETIC = "synthetic_demo"  # solo para datos de demostración


def load_cities(data_dir: str | Path) -> pd.DataFrame:
    """Lee cities.csv y comprueba que sea consistente."""
    cities = pd.read_csv(Path(data_dir) / "cities.csv")
    missing = set(REQUIRED_CITY_COLUMNS) - set(cities.columns)
    if missing:
        raise ValueError(f"Faltan columnas en cities.csv: {sorted(missing)}")
    if cities["city"].duplicated().any():
        raise ValueError("Hay nombres de ciudad duplicados en cities.csv.")
    if cities[["longitude", "latitude"]].isna().any().any():
        raise ValueError("Hay coordenadas vacías en cities.csv.")
    return cities.reset_index(drop=True)


def read_matrix(path: str | Path, names: list[str]) -> np.ndarray:
    """Lee una matriz cuadrada con índice/columnas = ciudades, en el orden de `names`."""
    frame = pd.read_csv(path, index_col=0)
    try:
        frame = frame.loc[names, names]
    except KeyError as error:
        raise ValueError(f"{path}: las ciudades no coinciden con cities.csv ({error}).") from error
    matrix = frame.to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        raise ValueError(f"{path}: contiene valores vacíos o no finitos.")
    if (matrix < 0).any():
        raise ValueError(f"{path}: contiene valores negativos.")
    return matrix


def read_toll_matrix(path: str | Path, names: list[str],
                     allow_synthetic: bool = False) -> np.ndarray:
    """Convierte toll_costs.csv (formato largo) en matriz.

    Exige, para cada par dirigido, importe, estado verificado, fuente y fecha.
    No se acepta ningún par pendiente: un peaje vacío NO se interpreta como cero.
    """
    tolls = pd.read_csv(path, keep_default_na=False)
    required = {"origin", "destination", "toll_eur", "toll_status",
                "source_url", "consultation_date"}
    missing = required - set(tolls.columns)
    if missing:
        raise ValueError(f"{path}: faltan columnas {sorted(missing)}")

    allowed = {STATUS_VERIFIED} | ({STATUS_SYNTHETIC} if allow_synthetic else set())
    pairs = tolls[tolls["origin"] != tolls["destination"]]
    expected = len(names) * (len(names) - 1)
    if len(pairs) != expected:
        raise ValueError(f"{path}: se esperaban {expected} pares dirigidos y hay {len(pairs)}.")

    bad = pairs[
        ~pairs["toll_status"].isin(allowed)
        | (pairs["toll_eur"].astype(str).str.strip() == "")
        | (pairs["source_url"].astype(str).str.strip() == "")
        | (pairs["consultation_date"].astype(str).str.strip() == "")
    ]
    if not bad.empty:
        raise ValueError(
            f"{path}: {len(bad)} pares sin peaje verificado, fuente y fecha "
            f"(estados permitidos: {sorted(allowed)}). Complete toll_costs.csv."
        )

    values = pd.to_numeric(pairs["toll_eur"], errors="raise")
    if (values < 0).any():
        raise ValueError(f"{path}: hay peajes negativos.")
    matrix = pd.DataFrame(0.0, index=names, columns=names)
    for origin, destination, value in zip(pairs["origin"], pairs["destination"], values):
        matrix.loc[origin, destination] = float(value)
    return matrix.to_numpy(dtype=float)


def load_components(data_dir: str | Path, allow_synthetic: bool = False) -> dict:
    """Carga los componentes del costo: tiempo (h), distancia (km) y peajes (EUR)."""
    data_dir = Path(data_dir)
    cities = load_cities(data_dir)
    names = cities["city"].tolist()
    return {
        "cities": cities,
        "names": names,
        "time_h": read_matrix(data_dir / "travel_times.csv", names),
        "distance_km": read_matrix(data_dir / "distances.csv", names),
        "toll_eur": read_toll_matrix(data_dir / "toll_costs.csv", names, allow_synthetic),
    }


def fuel_matrix(distance_km: np.ndarray, consumption_l_per_100km: float,
                fuel_price_eur_per_liter: float) -> np.ndarray:
    """Costo de combustible: km * (L/100 km) / 100 * (EUR/L)."""
    if consumption_l_per_100km <= 0 or fuel_price_eur_per_liter <= 0:
        raise ValueError("Consumo y precio del combustible deben ser positivos.")
    return distance_km * consumption_l_per_100km / 100.0 * fuel_price_eur_per_liter


def build_cost_matrix(components: dict, hourly_value_eur: float,
                      consumption_l_per_100km: float,
                      fuel_price_eur_per_liter: float) -> np.ndarray:
    """cost = valor_hora * horas + peajes + combustible (matriz en euros)."""
    if hourly_value_eur < 0:
        raise ValueError("El valor de la hora no puede ser negativo.")
    fuel = fuel_matrix(components["distance_km"], consumption_l_per_100km,
                       fuel_price_eur_per_liter)
    cost = hourly_value_eur * components["time_h"] + components["toll_eur"] + fuel
    np.fill_diagonal(cost, 0.0)
    return cost


def route_breakdown(route: list, components: dict, hourly_value_eur: float,
                    consumption_l_per_100km: float,
                    fuel_price_eur_per_liter: float) -> dict:
    """Desglosa un circuito cerrado en distancia, tiempo y las tres partes del costo.

    `route` puede ser una lista de nombres o de índices; si repite la ciudad
    inicial al final, se ignora esa repetición.
    """
    names = components["names"]
    index_of = {name: i for i, name in enumerate(names)}
    indices = [index_of[item] if isinstance(item, str) else int(item) for item in route]
    if len(indices) > 1 and indices[0] == indices[-1]:
        indices = indices[:-1]
    if sorted(indices) != list(range(len(names))):
        raise ValueError("La ruta debe visitar cada ciudad exactamente una vez.")

    legs = [(indices[k], indices[(k + 1) % len(indices)]) for k in range(len(indices))]
    distance = sum(components["distance_km"][a, b] for a, b in legs)
    time_h = sum(components["time_h"][a, b] for a, b in legs)
    tolls = sum(components["toll_eur"][a, b] for a, b in legs)
    fuel = fuel_matrix(np.array([[distance]]), consumption_l_per_100km,
                       fuel_price_eur_per_liter)[0, 0]
    time_cost = hourly_value_eur * time_h
    return {
        "distance_km": float(distance),
        "time_h": float(time_h),
        "time_cost_eur": float(time_cost),
        "toll_eur": float(tolls),
        "fuel_eur": float(fuel),
        "total_cost_eur": float(time_cost + tolls + fuel),
    }
