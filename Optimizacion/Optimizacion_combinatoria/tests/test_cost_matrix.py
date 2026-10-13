"""Pruebas de los datos, el cargador, la matriz de costos y el estudio del valor de la hora."""
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build_data  # noqa: E402
import main  # noqa: E402
import tsp_data  # noqa: E402

CITIES_CSV = ROOT / "data" / "cities.csv"


class CitiesTest(unittest.TestCase):
    def test_47_unique_peninsular_capitals(self):
        cities = pd.read_csv(CITIES_CSV)
        self.assertEqual(len(cities), 47)
        self.assertEqual(cities["city"].nunique(), 47)
        self.assertTrue(cities["longitude"].between(-10, 5).all())
        self.assertTrue(cities["latitude"].between(34, 45).all())
        for excluded in ("Palma", "Las Palmas de Gran Canaria", "Santa Cruz de Tenerife",
                         "Ceuta", "Melilla"):
            self.assertNotIn(excluded, set(cities["city"]))

    def test_known_straight_line_distances(self):
        """Control cruzado de coordenadas: distancias en línea recta conocidas (±5 %)."""
        cities = pd.read_csv(CITIES_CSV).set_index("city")
        straight = build_data.haversine_km(cities["longitude"].to_numpy(),
                                           cities["latitude"].to_numpy())
        index = {name: i for i, name in enumerate(cities.index)}
        known_km = {("Madrid", "Barcelona"): 505, ("Madrid", "Sevilla"): 390,
                    ("Madrid", "Valencia"): 302, ("Madrid", "Bilbao"): 322}
        for (a, b), expected in known_km.items():
            self.assertAlmostEqual(straight[index[a], index[b]] / expected, 1.0, delta=0.05,
                                   msg=f"{a}-{b}")


class DemoDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls._tmp.name)
        build_data.build_demo_data(CITIES_CSV, cls.dir)
        cls.components = tsp_data.load_components(cls.dir, allow_synthetic=True)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_shapes_and_properties(self):
        for key in ("time_h", "distance_km", "toll_eur"):
            matrix = self.components[key]
            self.assertEqual(matrix.shape, (47, 47))
            self.assertTrue(np.allclose(np.diag(matrix), 0))
            self.assertTrue((matrix >= 0).all())
        self.assertFalse(np.allclose(self.components["distance_km"],
                                     self.components["distance_km"].T),
                         "la matriz debe poder ser asimétrica")

    def test_cost_is_time_plus_toll_plus_fuel(self):
        c = self.components
        cost = tsp_data.build_cost_matrix(c, 25.0, 6.0, 1.60)
        i, j = 3, 17
        expected = (25.0 * c["time_h"][i, j] + c["toll_eur"][i, j]
                    + c["distance_km"][i, j] * 6.0 / 100 * 1.60)
        self.assertAlmostEqual(cost[i, j], expected)
        self.assertEqual(cost[i, i], 0.0)

    def test_cost_is_linear_in_hourly_value(self):
        c = self.components
        low = tsp_data.build_cost_matrix(c, 10.0, 6.0, 1.60)
        high = tsp_data.build_cost_matrix(c, 30.0, 6.0, 1.60)
        self.assertTrue(np.allclose(high - low, 20.0 * c["time_h"]))

    def test_cost_matrix_csv_matches_recomputation(self):
        written = pd.read_csv(self.dir / "cost_matrix.csv", index_col=0).to_numpy()
        recomputed = tsp_data.build_cost_matrix(self.components, 20.0, 6.0, 1.60)
        self.assertTrue(np.allclose(written, recomputed))

    def test_route_breakdown_matches_sum_of_legs(self):
        c = self.components
        cost = tsp_data.build_cost_matrix(c, 20.0, 6.0, 1.60)
        order = list(range(47))
        legs = sum(cost[order[k], order[(k + 1) % 47]] for k in range(47))
        breakdown = tsp_data.route_breakdown(order + [0], c, 20.0, 6.0, 1.60)
        self.assertAlmostEqual(breakdown["total_cost_eur"], legs, places=6)
        self.assertAlmostEqual(breakdown["total_cost_eur"], breakdown["time_cost_eur"]
                               + breakdown["toll_eur"] + breakdown["fuel_eur"])

    def test_route_breakdown_rejects_non_permutation(self):
        with self.assertRaises(ValueError):
            tsp_data.route_breakdown([0, 1, 1] + list(range(3, 47)), self.components, 20, 6, 1.6)

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            tsp_data.build_cost_matrix(self.components, -1.0, 6.0, 1.6)
        with self.assertRaises(ValueError):
            tsp_data.build_cost_matrix(self.components, 20.0, 0.0, 1.6)


class TollVerificationTest(unittest.TestCase):
    def test_pending_template_is_rejected(self):
        """Un peaje vacío NUNCA se interpreta como cero."""
        cities = pd.read_csv(CITIES_CSV)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "toll_costs.csv"
            build_data.create_toll_template(cities, path)
            template = pd.read_csv(path, keep_default_na=False)
            self.assertEqual(len(template), 47 * 47)
            with self.assertRaises(ValueError):
                tsp_data.read_toll_matrix(path, cities["city"].tolist())

    def test_synthetic_status_only_accepted_when_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_data.build_demo_data(CITIES_CSV, Path(tmp))
            names = pd.read_csv(CITIES_CSV)["city"].tolist()
            with self.assertRaises(ValueError):
                tsp_data.read_toll_matrix(Path(tmp) / "toll_costs.csv", names, allow_synthetic=False)
            matrix = tsp_data.read_toll_matrix(Path(tmp) / "toll_costs.csv", names, allow_synthetic=True)
            self.assertEqual(matrix.shape, (47, 47))

    def test_verified_zero_is_accepted(self):
        names = ["A", "B"]
        rows = [{"origin": o, "destination": d, "toll_eur": 0.0,
                 "toll_status": "verified" if o != d else "not_applicable",
                 "source_url": "https://example.org", "consultation_date": "2026-01-01"}
                for o in names for d in names]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "toll_costs.csv"
            pd.DataFrame(rows).to_csv(path, index=False)
            self.assertTrue((tsp_data.read_toll_matrix(path, names) == 0).all())

    def test_missing_pairs_are_rejected(self):
        names = ["A", "B", "C"]
        rows = [{"origin": "A", "destination": "B", "toll_eur": 1.0, "toll_status": "verified",
                 "source_url": "x", "consultation_date": "2026-01-01"}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "toll_costs.csv"
            pd.DataFrame(rows).to_csv(path, index=False)
            with self.assertRaises(ValueError):
                tsp_data.read_toll_matrix(path, names)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


class FakeSession:
    """Imita OSRM Table: distancia = 1000*(i+1)*(j+2) m, duración = 10*(i+3)*(j+1) s."""

    def __init__(self):
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append(params)
        sources = [int(x) for x in params["sources"].split(";")]
        destinations = [int(x) for x in params["destinations"].split(";")]
        return FakeResponse({
            "code": "Ok",
            "distances": [[1000.0 * (i + 1) * (j + 2) for j in destinations] for i in sources],
            "durations": [[10.0 * (i + 3) * (j + 1) for j in destinations] for i in sources],
        })


class OsrmTableTest(unittest.TestCase):
    def test_batches_are_assembled_in_the_right_rows(self):
        cities = pd.read_csv(CITIES_CSV)
        session = FakeSession()
        distance, duration = build_data.osrm_table(cities, "http://fake", source_batch_size=8,
                                                   pause_seconds=0.0, session=session)
        self.assertEqual(len(session.calls), math.ceil(47 / 8))
        self.assertEqual(distance.shape, (47, 47))
        self.assertEqual(distance.iloc[5, 9], 1000.0 * 6 * 11)
        self.assertEqual(duration.iloc[40, 2], 10.0 * 43 * 3)
        self.assertTrue(np.allclose(np.diag(distance), 0))
        self.assertEqual(list(distance.index), cities["city"].tolist())


class LowerEnvelopeTest(unittest.TestCase):
    @staticmethod
    def line(route_id, time_h, money):
        return {"route_id": route_id, "time_h": time_h, "money_eur": money}

    def test_breakpoints_are_exact(self):
        a, b, c = self.line("A", 10, 0), self.line("B", 5, 20), self.line("C", 1, 100)
        dominated = self.line("D", 6, 200)  # peor que B en tiempo y en dinero
        segments = main.lower_envelope([dominated, c, a, b])
        self.assertEqual([s["route_id"] for s in segments], ["A", "B", "C"])
        self.assertAlmostEqual(segments[0]["to_h"], 4.0)    # A y B cuestan igual en h = 20/5
        self.assertAlmostEqual(segments[1]["to_h"], 20.0)   # B y C: (100-20)/(5-1)
        self.assertIsNone(segments[2]["to_h"])

    def test_single_route_has_one_segment(self):
        segments = main.lower_envelope([self.line("A", 3, 10)])
        self.assertEqual(len(segments), 1)
        self.assertIsNone(segments[0]["to_h"])

    def test_envelope_is_the_pointwise_minimum(self):
        rng = np.random.default_rng(0)
        routes = [self.line(str(k), rng.uniform(1, 50), rng.uniform(0, 500)) for k in range(30)]
        segments = main.lower_envelope(routes)
        for h in np.linspace(0, 200, 81):
            segment = next(s for s in segments
                           if s["from_h"] <= h and (s["to_h"] is None or h < s["to_h"]))
            best = min(r["money_eur"] + h * r["time_h"] for r in routes)
            self.assertAlmostEqual(segment["money_eur"] + h * segment["time_h"], best, places=6)


if __name__ == "__main__":
    unittest.main()
