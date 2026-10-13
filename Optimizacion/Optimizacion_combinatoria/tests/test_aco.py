"""Pruebas de la colonia de hormigas (ACO) para el TSP."""
import itertools
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_data  # noqa: E402
import tsp_data  # noqa: E402
from aco import ant_colony_optimization  # noqa: E402


def random_instance(n: int, seed: int) -> np.ndarray:
    """Matriz de costos asimétrica, positiva, con diagonal cero."""
    rng = np.random.default_rng(seed)
    costs = rng.uniform(1.0, 100.0, (n, n))
    np.fill_diagonal(costs, 0.0)
    return costs


def tour_cost(order, costs) -> float:
    return float(sum(costs[order[k], order[(k + 1) % len(order)]] for k in range(len(order))))


def brute_force_optimum(costs: np.ndarray, start: int = 0) -> float:
    others = [c for c in range(len(costs)) if c != start]
    return min(tour_cost([start, *perm], costs) for perm in itertools.permutations(others))


class AcoCorrectnessTest(unittest.TestCase):
    def setUp(self):
        self.costs = random_instance(7, seed=1)
        self.names = [f"C{i}" for i in range(7)]

    def test_route_is_a_valid_closed_tour_with_correct_cost(self):
        result = ant_colony_optimization(self.costs, self.names, iterations=30, seed=3)
        route = result["route"]
        self.assertEqual(route[0], route[-1])
        self.assertEqual(sorted(route[:-1]), sorted(self.names))
        indices = [self.names.index(name) for name in route[:-1]]
        self.assertAlmostEqual(result["cost"], tour_cost(indices, self.costs))

    def test_finds_optimum_on_small_instance_with_pheromone_floor(self):
        """Con la cota de feromona, alguna semilla alcanza el óptimo exacto (verificado por fuerza bruta).

        Sin cota (comportamiento por defecto) esta instancia se estanca ~4-11 % por encima del
        óptimo con 0/10 semillas, y más iteraciones no cambian el resultado: ver README.
        """
        optimum = brute_force_optimum(self.costs)
        best = min(ant_colony_optimization(self.costs, self.names, iterations=300, seed=s,
                                           min_pheromone_fraction=0.1)["cost"] for s in range(5))
        self.assertAlmostEqual(best, optimum, places=6)

    def test_default_never_beats_the_optimum(self):
        optimum = brute_force_optimum(self.costs)
        for seed in range(3):
            cost = ant_colony_optimization(self.costs, self.names, iterations=40, seed=seed)["cost"]
            self.assertGreaterEqual(cost, optimum - 1e-9)

    def test_history_is_monotone_and_complete(self):
        result = ant_colony_optimization(self.costs, self.names, iterations=25, seed=0)
        costs = [entry["cost"] for entry in result["history"]]
        self.assertEqual(len(costs), 26)
        self.assertTrue(all(b <= a + 1e-12 for a, b in zip(costs, costs[1:])))
        self.assertAlmostEqual(costs[-1], result["cost"])

    def test_same_seed_same_result(self):
        a = ant_colony_optimization(self.costs, self.names, iterations=20, seed=9)
        b = ant_colony_optimization(self.costs, self.names, iterations=20, seed=9)
        self.assertEqual(a["route"], b["route"])
        self.assertEqual(a["cost"], b["cost"])

    def test_start_city_is_respected(self):
        result = ant_colony_optimization(self.costs, self.names, iterations=10, seed=0, start_city=4)
        self.assertEqual(result["route"][0], "C4")

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            ant_colony_optimization(np.ones((3, 4)))
        with self.assertRaises(ValueError):
            ant_colony_optimization(-self.costs)
        bad_diagonal = self.costs.copy()
        bad_diagonal[0, 0] = 5.0
        with self.assertRaises(ValueError):
            ant_colony_optimization(bad_diagonal)
        with self.assertRaises(ValueError):
            ant_colony_optimization(self.costs, evaporation_rate=1.0)
        with self.assertRaises(ValueError):
            ant_colony_optimization(self.costs, iterations=0)
        with self.assertRaises(ValueError):
            ant_colony_optimization(self.costs, min_pheromone_fraction=1.0)


class AcoOn47CitiesTest(unittest.TestCase):
    def test_beats_random_tours_by_a_wide_margin(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_data.build_demo_data(ROOT / "data" / "cities.csv", Path(tmp))
            components = tsp_data.load_components(tmp, allow_synthetic=True)
        costs = tsp_data.build_cost_matrix(components, 20.0, 6.0, 1.60)
        rng = np.random.default_rng(0)
        random_costs = [tour_cost([0, *rng.permutation(np.arange(1, 47))], costs) for _ in range(200)]
        result = ant_colony_optimization(costs, components["names"], iterations=15, seed=0)
        self.assertLess(result["cost"], 0.5 * float(np.mean(random_costs)))


if __name__ == "__main__":
    unittest.main()
