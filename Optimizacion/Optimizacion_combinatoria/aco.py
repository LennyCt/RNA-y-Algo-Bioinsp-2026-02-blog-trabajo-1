"""Ant Colony Optimization (ACO) for the Traveling Salesperson Problem (TSP)."""

from __future__ import annotations

from typing import Sequence
import numpy as np


def _validate_inputs(cost_matrix: np.ndarray, city_names: Sequence[str] | None):
    """Valida la matriz de costes y los nombres de las ciudades."""
    costs = np.asarray(cost_matrix, dtype=float)
    if costs.ndim != 2 or costs.shape[0] != costs.shape[1]:
        raise ValueError("cost_matrix debe ser una matriz cuadrada.")
    if costs.shape[0] < 2:
        raise ValueError("Se necesitan al menos dos ciudades.")
    if not np.isfinite(costs).all() or (costs < 0).any():
        raise ValueError("Los costes deben ser finitos y no negativos.")
    if not np.allclose(np.diag(costs), 0):
        raise ValueError("La diagonal de cost_matrix debe ser cero.")
    names = list(city_names) if city_names is not None else [str(i) for i in range(len(costs))]
    if len(names) != len(costs):
        raise ValueError("city_names debe tener un nombre por ciudad.")
    return costs, names


def _route_cost(route: Sequence[int], cost_matrix: np.ndarray) -> float:
    """Calcula el coste de un circuito cerrado."""
    return float(sum(cost_matrix[route[i], route[(i + 1) % len(route)]]
                     for i in range(len(route))))


def _build_route(start_city: int, pheromone: np.ndarray, heuristic: np.ndarray,
                 alpha: float, beta: float, rng: np.random.Generator) -> list[int]:
    """Construye una ruta probabilísticamente a partir de feromonas y heurística."""
    city_count = len(pheromone)
    route = [start_city]
    unvisited = set(range(city_count))
    unvisited.remove(start_city)

    while unvisited:
        current_city = route[-1]
        candidates = np.array(sorted(unvisited), dtype=int)
        pheromone_values = np.maximum(pheromone[current_city, candidates], 1e-12) ** alpha
        heuristic_values = np.maximum(heuristic[current_city, candidates], 1e-12) ** beta
        probabilities = pheromone_values * heuristic_values
        probability_sum = probabilities.sum()
        if not np.isfinite(probability_sum) or probability_sum <= 0:
            next_city = int(rng.choice(candidates))
        else:
            probabilities /= probability_sum
            next_city = int(rng.choice(candidates, p=probabilities))
        route.append(next_city)
        unvisited.remove(next_city)
    return route


def ant_colony_optimization(
    cost_matrix: np.ndarray,
    city_names: Sequence[str] | None = None,
    *,
    ant_count: int | None = None,
    iterations: int = 300,
    alpha: float = 1.0,
    beta: float = 3.0,
    evaporation_rate: float = 0.35,
    pheromone_deposit: float = 1.0,
    min_pheromone_fraction: float = 0.0,
    start_city: int = 0,
    seed: int | None = 42,
) -> dict:
    """Ejecuta ACO y devuelve la mejor ruta y el historial para animación.

    cost_matrix[i, j] debe contener el coste total de viajar de i a j.
    El historial registra el mejor resultado histórico en cada iteración.

    min_pheromone_fraction (opcional, por defecto 0 = sin cota): si es > 0, tras cada
    iteración la feromona de cada arista se limita por abajo a esa fracción de la
    feromona máxima (idea del MAX-MIN Ant System). Sin cota, la feromona de las aristas
    no usadas decae hasta ~0 y la colonia deja de explorar (estancamiento).
    """
    costs, names = _validate_inputs(cost_matrix, city_names)
    city_count = len(costs)
    if not 0 <= start_city < city_count:
        raise ValueError("start_city está fuera de rango.")
    if iterations < 1:
        raise ValueError("iterations debe ser mayor que cero.")
    if not 0 <= evaporation_rate < 1:
        raise ValueError("evaporation_rate debe estar entre 0 y 1.")
    if not 0 <= min_pheromone_fraction < 1:
        raise ValueError("min_pheromone_fraction debe estar entre 0 y 1.")
    if alpha < 0 or beta < 0 or pheromone_deposit <= 0:
        raise ValueError("alpha y beta deben ser no negativos y pheromone_deposit positivo.")

    rng = np.random.default_rng(seed)
    ant_count = ant_count or city_count
    if ant_count < 1:
        raise ValueError("ant_count debe ser mayor que cero.")

    positive_costs = costs[costs > 0]
    baseline = float(np.median(positive_costs)) if positive_costs.size else 1.0
    heuristic = np.divide(1.0, costs, out=np.zeros_like(costs), where=costs > 0)
    np.fill_diagonal(heuristic, 0.0)
    pheromone = np.full((city_count, city_count), 1.0 / max(baseline, 1e-12))
    np.fill_diagonal(pheromone, 0.0)

    best_route = list(range(city_count))
    if best_route[0] != start_city:
        best_route.remove(start_city)
        best_route.insert(0, start_city)
    best_cost = _route_cost(best_route, costs)
    history = [{
        "generation": 0,
        "cost": best_cost,
        "route": [names[i] for i in best_route] + [names[best_route[0]]],
    }]

    for iteration in range(1, iterations + 1):
        ant_routes = []
        ant_costs = []
        for _ in range(ant_count):
            route = _build_route(start_city, pheromone, heuristic, alpha, beta, rng)
            route_cost = _route_cost(route, costs)
            ant_routes.append(route)
            ant_costs.append(route_cost)
            if route_cost < best_cost:
                best_route, best_cost = route.copy(), route_cost

        pheromone *= (1.0 - evaporation_rate)
        for route, route_cost in zip(ant_routes, ant_costs):
            deposit = pheromone_deposit / max(route_cost, 1e-12)
            for index in range(city_count):
                first_city = route[index]
                second_city = route[(index + 1) % city_count]
                pheromone[first_city, second_city] += deposit
        if min_pheromone_fraction > 0:
            pheromone = np.maximum(pheromone, min_pheromone_fraction * pheromone.max())
            np.fill_diagonal(pheromone, 0.0)

        history.append({
            "generation": iteration,
            "cost": float(best_cost),
            "route": [names[i] for i in best_route] + [names[best_route[0]]],
        })

    return {
        "route": [names[i] for i in best_route] + [names[best_route[0]]],
        "cost": float(best_cost),
        "history": history,
        "algorithm": "ACO",
    }


if __name__ == "__main__":
    # Ejemplo mínimo; sustituye esta matriz por la matriz real de costes entre capitales.
    example_costs = np.array([
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ], dtype=float)
    result = ant_colony_optimization(
        example_costs, ["Madrid", "Ávila", "Burgos", "Segovia"],
        iterations=100, seed=42,
    )
    print("Mejor coste:", result["cost"])
    print("Mejor ruta:", " -> ".join(result["route"]))
