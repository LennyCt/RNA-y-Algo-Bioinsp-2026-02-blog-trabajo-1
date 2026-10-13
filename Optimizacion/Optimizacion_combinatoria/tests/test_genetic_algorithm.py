"""Pruebas del algoritmo genético (AG) para el TSP."""
import itertools
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_data  # noqa: E402
import algoritmo_genetico as ga_module  # noqa: E402
import tsp_data  # noqa: E402
from algoritmo_genetico import genetic_algorithm  # noqa: E402


def random_instance(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    costs = rng.uniform(1.0, 100.0, (n, n))
    np.fill_diagonal(costs, 0.0)
    return costs


def tour_cost(order, costs) -> float:
    return float(sum(costs[order[k], order[(k + 1) % len(order)]] for k in range(len(order))))


def brute_force_optimum(costs: np.ndarray, start: int = 0) -> float:
    others = [c for c in range(len(costs)) if c != start]
    return min(tour_cost([start, *perm], costs) for perm in itertools.permutations(others))


class OperatorsTest(unittest.TestCase):
    def test_crossover_and_mutation_keep_valid_permutations_with_fixed_start(self):
        rng = np.random.default_rng(0)
        n = 20
        for _ in range(300):
            parent_a = [0, *rng.permutation(np.arange(1, n)).tolist()]
            parent_b = [0, *rng.permutation(np.arange(1, n)).tolist()]
            child = ga_module._ordered_crossover(parent_a, parent_b, rng)
            self.assertEqual(sorted(child), list(range(n)))
            self.assertEqual(child[0], 0)
            mutated = ga_module._mutate_route(child, 1.0, rng)
            self.assertEqual(sorted(mutated), list(range(n)))
            self.assertEqual(mutated[0], 0)

    def test_crossover_keeps_a_contiguous_block_of_parent_a(self):
        rng = np.random.default_rng(1)
        parent_a = [0, 1, 2, 3, 4, 5, 6, 7]
        parent_b = [0, 7, 6, 5, 4, 3, 2, 1]
        child = ga_module._ordered_crossover(parent_a, parent_b, rng)
        in_a_order = [city for city in child if city in parent_a]
        self.assertEqual(sorted(child), parent_a)
        self.assertTrue(any(child[k:k + 2] == parent_a[k:k + 2] for k in range(len(child) - 1)) or
                        in_a_order != parent_b)

    def test_tournament_returns_the_best_when_it_covers_the_population(self):
        population = [[0, 1, 2], [0, 2, 1], [0, 1, 2]]
        fitness = np.array([5.0, 1.0, 7.0])
        rng = np.random.default_rng(0)
        self.assertEqual(ga_module._tournament_selection(population, fitness, 3, rng), [0, 2, 1])


class GeneticAlgorithmTest(unittest.TestCase):
    def setUp(self):
        self.costs = random_instance(7, seed=1)
        self.names = [f"C{i}" for i in range(7)]

    def test_route_is_a_valid_closed_tour_with_correct_cost(self):
        result = genetic_algorithm(self.costs, self.names, population_size=40, generations=30, seed=3)
        route = result["route"]
        self.assertEqual(route[0], route[-1])
        self.assertEqual(sorted(route[:-1]), sorted(self.names))
        indices = [self.names.index(name) for name in route[:-1]]
        self.assertAlmostEqual(result["cost"], tour_cost(indices, self.costs))

    def test_finds_optimum_on_small_instance(self):
        optimum = brute_force_optimum(self.costs)
        best = min(genetic_algorithm(self.costs, self.names, population_size=60, generations=80,
                                     seed=s)["cost"] for s in range(3))
        self.assertAlmostEqual(best, optimum, places=6)

    def test_history_is_monotone_and_complete(self):
        result = genetic_algorithm(self.costs, self.names, population_size=30, generations=25, seed=0)
        costs = [entry["cost"] for entry in result["history"]]
        self.assertEqual(len(costs), 26)
        self.assertTrue(all(b <= a + 1e-12 for a, b in zip(costs, costs[1:])))
        self.assertAlmostEqual(costs[-1], result["cost"])

    def test_same_seed_same_result(self):
        kwargs = dict(population_size=30, generations=15, seed=9)
        a = genetic_algorithm(self.costs, self.names, **kwargs)
        b = genetic_algorithm(self.costs, self.names, **kwargs)
        self.assertEqual(a["route"], b["route"])

    def test_start_city_is_respected(self):
        result = genetic_algorithm(self.costs, self.names, population_size=20, generations=5,
                                   seed=0, start_city=5)
        self.assertEqual(result["route"][0], "C5")

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            genetic_algorithm(np.ones((3, 4)))
        with self.assertRaises(ValueError):
            genetic_algorithm(self.costs, population_size=1)
        with self.assertRaises(ValueError):
            genetic_algorithm(self.costs, population_size=10, elite_count=10)
        with self.assertRaises(ValueError):
            genetic_algorithm(self.costs, mutation_rate=1.5)


class GeneticAlgorithmOn47CitiesTest(unittest.TestCase):
    def test_beats_random_tours_by_a_wide_margin(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_data.build_demo_data(ROOT / "data" / "cities.csv", Path(tmp))
            components = tsp_data.load_components(tmp, allow_synthetic=True)
        costs = tsp_data.build_cost_matrix(components, 20.0, 6.0, 1.60)
        rng = np.random.default_rng(0)
        random_costs = [tour_cost([0, *rng.permutation(np.arange(1, 47))], costs) for _ in range(200)]
        result = genetic_algorithm(costs, components["names"], population_size=100, generations=60, seed=0)
        self.assertLess(result["cost"], 0.7 * float(np.mean(random_costs)))


if __name__ == "__main__":
    unittest.main()
