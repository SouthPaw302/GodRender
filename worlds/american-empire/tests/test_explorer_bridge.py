"""P4 tests: verified data bridge, source isolation and deterministic Godot payload."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "tools" / "build_explorer_bundle.py"
spec = importlib.util.spec_from_file_location("ae_p4_bridge", BRIDGE)
bridge = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(bridge)


class ExplorerBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = bridge.build_bundle()

    def test_version_and_explicit_authority_boundary(self):
        b = self.bundle
        self.assertEqual(b["schema"], "american-empire.godot-explorer-bundle.v1")
        self.assertTrue(b["sources_read_only"])
        self.assertEqual(b["classification"], "interactive schematic, not a geographic map")
        self.assertEqual(b["source"]["matrix_blob_sha1"], "575e8c1b20bc6e9bf5c61ac32e32536256abcab0")
        self.assertEqual(b["source"]["canon_commit"], "d768ee1684ebddd06af249f3a366181c929bc80c")
        self.assertNotIn("Paris", json.dumps(b["nodes"]))

    def test_every_node_has_canonical_source(self):
        b = self.bundle
        self.assertEqual(len(b["nodes"]), 16)
        self.assertEqual(sum(x["kind"] == "actor" for x in b["nodes"]), 10)
        self.assertEqual(sum(x["kind"] == "system" for x in b["nodes"]), 6)
        self.assertEqual(len(b["people"]), 5)
        self.assertEqual(len(b["variables"]), 7)
        for x in b["nodes"] + b["people"] + b["variables"]:
            self.assertEqual(x["source"]["authority_layer"], "established")
            self.assertTrue(x["source"]["json_pointer"].startswith("/"))
            self.assertEqual(x["source"]["git_blob_sha1"], b["source"]["matrix_blob_sha1"])
        ids = {x["id"] for x in b["nodes"]}
        self.assertTrue(all(x["from"] in ids and x["to"] in ids for x in b["edges"]))

    def test_timeline_is_written_history_not_simulation(self):
        self.assertEqual([x["year"] for x in self.bundle["years"]], list(range(2026, 2038)))
        self.assertEqual(self.bundle["years"][1]["title"], "Dollar Night")
        self.assertEqual(self.bundle["years"][11]["title"], "World Accession")
        self.assertTrue(all(x["source"]["authority_layer"] == "established" for x in self.bundle["years"]))

    def test_all_scenario_snapshots_are_model_only(self):
        self.assertEqual([x["id"] for x in self.bundle["scenarios"]],
                         ["baseline", "independent-corridor", "high-integration"])
        source = self.bundle["source"]
        for item in self.bundle["scenarios"]:
            self.assertEqual(item["authority_layer"], "scenario_only")
            self.assertEqual(item["source_world_sha256"], source["world_graph_sha256"])
            self.assertEqual(item["model_sha256"], source["simulation_model_sha256"])
            self.assertEqual([p["year"] for p in item["snapshots"]], list(range(2026, 2038)))
            self.assertTrue(all(len(p["snapshot_sha256"]) == 64 for p in item["snapshots"]))
            self.assertTrue(all(len(p["state"]) == 7 for p in item["snapshots"]))

    def test_bridge_hash_is_reproducible(self):
        source = {k:v for k,v in self.bundle.items() if k != "bundle_sha256"}
        self.assertEqual(self.bundle["bundle_sha256"], bridge.digest(source))
        self.assertEqual(bridge.build_bundle(), self.bundle)
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "world_bundle.json"
            one = bridge.write_bundle(file)
            first = file.read_bytes()
            two = bridge.write_bundle(file)
            self.assertEqual(first, file.read_bytes())
            self.assertEqual(one["bundle_sha256"], two["bundle_sha256"])
            self.assertGreater(len(first), 10000)
            self.assertTrue(json.loads(first)["sources_read_only"])

    def test_bridge_refuses_to_change_canon(self):
        with self.assertRaises(ValueError):
            bridge.write_bundle(ROOT / "archive" / "new_canon.json")
        invalid = copy.deepcopy(self.bundle)
        invalid["scenarios"][0]["authority_layer"] = "established"
        with self.assertRaises(ValueError):
            bridge.validate_bundle(invalid)
        invalid = copy.deepcopy(self.bundle)
        invalid["years"][2]["year"] = 2035
        with self.assertRaises(ValueError):
            bridge.validate_bundle(invalid)
        invalid = copy.deepcopy(self.bundle)
        invalid["nodes"].pop()
        with self.assertRaises(ValueError):
            bridge.validate_bundle(invalid)

    def test_cli_real_generation_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "world_bundle.json"
            proc = subprocess.run(
                [sys.executable, str(BRIDGE), "--output", str(output),
                 "--check-reproducible"], capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            generated = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(generated["bundle_sha256"], self.bundle["bundle_sha256"])

    def test_source_tamper_blocks_bridge(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for dirname in ("archive", "tools", "engine", "scenarios"):
                shutil.copytree(ROOT / dirname, root / dirname)
            shutil.copy2(ROOT / "CANON_LOCK.json", root / "CANON_LOCK.json")
            shutil.copy2(ROOT / "P3_MODEL.json", root / "P3_MODEL.json")
            src = root / "archive" / "01_CANON_SOURCE" / "REALITY_MATRIX.json"
            src.write_bytes(src.read_bytes() + b" ")
            with self.assertRaises(Exception):
                bridge.build_bundle(root)


if __name__ == "__main__":
    unittest.main()
