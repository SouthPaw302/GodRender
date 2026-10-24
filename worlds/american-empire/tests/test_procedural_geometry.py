"""Mathematical world generation must remain reproducible and subordinate to P9."""
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from population_model import digest
import build_procedural_geometry as gen


def contract():
    obj = {
        "schema": "american-empire.godot-scene-contract.v1",
        "authority_layer": "scenario_only",
        "source": {"p7_snapshot_sha256": "b" * 64},
        "world": {"year": 2027, "place_id": "anderson"},
        "production": {"media_refs_embedded": False},
    }
    obj["contract_sha256"] = digest(obj)
    return obj


class ProceduralWorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = contract()
        cls.world = gen.build(cls.scene)

    def test_same_seed_replays_exactly(self):
        self.assertEqual(self.world, gen.build(self.scene))
        gen.verify_geometry(self.world, self.scene)

    def test_geometry_has_topography_rivers_towns_and_roads(self):
        self.assertEqual(self.world["grid"], 64)
        self.assertEqual(len(self.world["heights_dm"]), 64)
        self.assertGreater(len(self.world["river_cells"]), 0)
        self.assertGreaterEqual(len(self.world["settlements"]), 3)
        self.assertGreaterEqual(len(self.world["roads"]), 2)

    def test_settlement_reroll_keeps_geography(self):
        alt = gen.build(self.scene, town_variation=1)
        self.assertEqual(alt["heights_dm"], self.world["heights_dm"])
        self.assertEqual(alt["river_cells"], self.world["river_cells"])
        self.assertNotEqual(alt["settlements"], self.world["settlements"])

    def test_road_reroll_keeps_terrain_and_towns(self):
        alt = gen.build(self.scene, road_variation=1)
        self.assertEqual(alt["heights_dm"], self.world["heights_dm"])
        self.assertEqual(alt["settlements"], self.world["settlements"])
        self.assertNotEqual(alt["roads"], self.world["roads"])

    def test_protects_source_and_geometry(self):
        tampered = copy.deepcopy(self.world)
        tampered["heights_dm"][0][0] += 3
        with self.assertRaises(ValueError):
            gen.verify_geometry(tampered, self.scene)
        forged = copy.deepcopy(self.scene)
        forged["world"]["year"] = 2037
        with self.assertRaises(ValueError):
            gen.build(forged)
        other = contract()
        other["source"]["p7_snapshot_sha256"] = "a" * 64
        other["contract_sha256"] = digest({k: v for k, v in other.items() if k != "contract_sha256"})
        with self.assertRaises(ValueError):
            gen.verify_geometry(self.world, other)


if __name__ == "__main__":
    unittest.main()
