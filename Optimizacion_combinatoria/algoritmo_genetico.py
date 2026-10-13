"""Genetic Algorithm (GA) for the Traveling Salesperson Problem (TSP)."""

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


def _ordered_crossover(parent_a: list[int], parent_b: list[int],
                       rng: np.random.Generator) -> list[int]:
    """Cruce OX que conserva una permutación válida de las ciudades."""
    chromosome_size = len(parent_a)
    left, right = sorted(rng.choice(chromosome_size, size=2, replace=False))
    child = [-1] * chromosome_size
    child[left:right + 1] = parent_a[left:right + 1]
    remaining = [city for city in parent_b if city not in child]
    fill_positions = [i for i, city in enumerate(child) if city == -1]
    for position, city in zip(fill_positions, remaining):
        child[position] = city
    return child


def _mutate_route(route: list[int], mutation_rate: float,
                  rng: np.random.Generator) -> list[int]:
    """Aplica mutación por intercambio sin alterar la ciudad de salida."""
    mutated = route.copy()
    if len(mutated) > 2 and rng.random() < mutation_rate:
        first, second = rng.choice(np.arange(1, len(mutated)), size=2, replace=False)
        mutated[first], mutated[second] = mutated[second], mutated[first]
    return mutated


def _tournament_selection(population: list[list[int]], fitness: np.ndarray,
                          tournament_size: int, rng: np.random.Generator) -> list[int]:
    """Selecciona el individuo de menor coste entre varios candidatos."""
    candidate_count = min(tournament_size, len(population))
    candidate_indices = rng.choice(len(population), size=candidate_count, replace=False)
    winner = min(candidate_indices, key=lambda index: fitness[index])
    return population[int(winner)].copy()


def genetic_algorithm(
    cost_matrix: np.ndarray,
    city_names: Sequence[str] | None = None,
    *,
    population_size: int = 250,
    generations: int = 500,
    mutation_rate: float = 0.15,
    crossover_rate: float = 0.9,
    elite_count: int = 4,
    tournament_size: int = 4,
    start_city: int = 0,
    seed: int | None = 42,
) -> dict:
    """Ejecuta un algoritmo genético y devuelve la mejor ruta y su historial.

    cost_matrix[i, j] debe contener el coste total de viajar de i a j.
    El historial registra el mejor resultado histórico en cada generación.
    """
    costs, names = _validate_inputs(cost_matrix, city_names)
    city_count = len(costs)
    if not 0 <= start_city < city_count:
        raise ValueError("start_city está fuera de rango.")
    if population_size < 2 or generations < 1:
        raise ValueError("population_size debe ser >= 2 y generations >= 1.")
    if not 0 <= mutation_rate <= 1 or not 0 <= crossover_rate <= 1:
        raise ValueError("mutation_rate y crossover_rate deben estar entre 0 y 1.")
    if not 1 <= elite_count < population_size:
        raise ValueError("elite_count debe estar entre 1 y population_size - 1.")
    if tournament_size < 1:
        raise ValueError("tournament_size debe ser mayor que cero.")

    rng = np.random.default_rng(seed)
    movable_cities = [city for city in range(city_count) if city != start_city]
    population = []
    for _ in range(population_size):
        chromosome = movable_cities.copy()
        rng.shuffle(chromosome)
        population.append([start_city] + chromosome)

    best_route = min(population, key=lambda route: _route_cost(route, costs)).copy()
    best_cost = _route_cost(best_route, costs)

    def format_history_entry(generation: int) -> dict:
        return {
            "generation": generation,
            "cost": float(best_cost),
            "route": [names[i] for i in best_route] + [names[best_route[0]]],
        }

    history = [format_history_entry(0)]

    for generation in range(1, generations + 1):
        fitness = np.array([_route_cost(route, costs) for route in population])
        order = np.argsort(fitness)
        next_population = [population[int(index)].copy()
                           for index in order[:elite_count]]

        while len(next_population) < population_size:
            parent_a = _tournament_selection(population, fitness, tournament_size, rng)
            parent_b = _tournament_selection(population, fitness, tournament_size, rng)
            if rng.random() < crossover_rate:
                child = _ordered_crossover(parent_a, parent_b, rng)
            else:
                child = parent_a.copy()
            child = _mutate_route(child, mutation_rate, rng)
            next_population.append(child)

        population = next_population
        generation_best = min(population, key=lambda route: _route_cost(route, costs))
        generation_cost = _route_cost(generation_best, costs)
        if generation_cost < best_cost:
            best_route, best_cost = generation_best.copy(), generation_cost

        history.append(format_history_entry(generation))

    return {
        "route": [names[i] for i in best_route] + [names[best_route[0]]],
        "cost": float(best_cost),
        "history": history,
        "algorithm": "GA",
    }


if __name__ == "__main__":
    # Ejemplo mínimo; sustituye esta matriz por la matriz real de costes entre capitales.
    example_costs = np.array([
        [0, 10, 15, 20],
        [10, 0, 35, 25],
        [15, 35, 0, 30],
        [20, 25, 30, 0],
    ], dtype=float)
    result = genetic_algorithm(
        example_costs, ["Madrid", "Ávila", "Burgos", "Segovia"],
        generations=200, seed=42,
    )
    print("Mejor coste:", result["cost"])
    print("Mejor ruta:", " -> ".join(result["route"]))
