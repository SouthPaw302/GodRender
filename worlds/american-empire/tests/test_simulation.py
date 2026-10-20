"""P3 simulation regression: canon boundaries, causal dynamics and replay receipts."""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from simulation import SCHEMA, RUN_SCHEMA, ScenarioError, Simulation, digest  # noqa: E402
from world_matrix import CanonIntegrityError  # noqa: E402


def example(name):
    return json.loads((ROOT / "scenarios" / "examples" / name).read_text(encoding="utf-8"))


class SimulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = Simulation()
        cls.baseline_spec = example("baseline.json")
        cls.alt_spec = example("independent-corridor.json")
        cls.baseline = cls.engine.run(cls.baseline_spec)
        cls.alternative = cls.engine.run(cls.alt_spec)

    def test_baseline_uses_source_seed_and_is_not_canon(self):
        run = self.baseline
        self.assertEqual(run["schema"], RUN_SCHEMA)
        self.assertEqual(run["authority_layer"], "scenario_only")
        self.assertEqual(run["source_world_sha256"], self.engine.world.digest)
        self.assertEqual(run["model_sha256"], self.engine.model_digest)
        self.assertEqual(run["initial_seed"], {
            "V1":35, "V2":44, "V3":22, "V4":70, "V5":28, "V6":86, "V7":91
        })
        self.assertEqual(run["snapshots"][0]["state"], run["initial_seed"])
        self.assertEqual(len(run["snapshots"]), 12)
        self.assertEqual([s["year"] for s in run["snapshots"]], list(range(2026, 2038)))
        self.assertEqual(run["snapshots"][0]["canon_anchor"]["title"], "The Exhaustion")
        self.assertTrue(all(s["authority_layer"] == "scenario_only" for s in run["snapshots"]))

    def test_integrated_model_reacts_to_events(self):
        original = self.baseline["snapshots"]
        alt = self.alternative["snapshots"]
        self.assertEqual([s["state"] for s in original[:4]],
                         [s["state"] for s in alt[:4]])  # before 2030
        self.assertNotEqual(original[4]["state"], alt[4]["state"])
        self.assertGreater(alt[-1]["state"]["V6"], original[-1]["state"]["V6"])
        self.assertGreater(alt[-1]["state"]["V4"], original[-1]["state"]["V4"])
        self.assertTrue(all(0 <= n <= 100 for snapshot in alt
                            for n in snapshot["state"].values()))
        self.assertEqual(len(self.alternative["event_receipts"]), 3)
        self.assertIn("dependency_gap", self.alternative["final_indicators"])

    def test_canonical_anchors_are_labels_not_simulated_facts(self):
        canon_2031 = self.engine.world.timeline(year=2031)[0]
        snapshot = self.alternative["snapshots"][5]
        self.assertEqual(snapshot["canon_anchor"]["title"], canon_2031["name"])
        self.assertTrue(snapshot["canon_anchor"]["is_historical_reference_only"])
        self.assertEqual(snapshot["authority_layer"], "scenario_only")
        self.assertEqual(self.engine.world.counts()["nodes"], 52)

    def test_annual_feedback_cannot_be_order_dependent(self):
        v = {"V1":65, "V2":29, "V3":66, "V4":70, "V5":61, "V6":19, "V7":34}
        expected = {"V1":-1, "V2":1, "V3":0, "V4":-2, "V5":1, "V6":-1, "V7":-2}
        actual = self.engine._feedback(v)
        self.assertEqual(actual, {k:x for k,x in expected.items() if x})
        new, applied = self.engine._apply(v, actual)
        self.assertEqual(new["V2"], 30)
        self.assertEqual(applied["V7"], -2)

    def test_provenance_digest_hash_chain(self):
        run = self.alternative
        snaps = run["snapshots"]
        self.assertEqual(run["run_sha256"], digest({k:v for k,v in run.items() if k != "run_sha256"}))
        for i, snap in enumerate(snaps):
            self.assertEqual(snap["sha256"], digest({k:v for k,v in snap.items() if k != "sha256"}))
            if i:
                self.assertEqual(snap["previous_sha256"], snaps[i-1]["sha256"])
        self.assertEqual(snaps[-1]["sha256"], run["final_snapshot_sha256"])
        self.assertTrue(self.engine.replay(run)["verified"])

    def test_replay_rejects_modified_state_and_forged_hash(self):
        altered = copy.deepcopy(self.alternative)
        altered["snapshots"][5]["state"]["V1"] = 99
        with self.assertRaises(ScenarioError):
            self.engine.replay(altered)
        altered = copy.deepcopy(self.alternative)
        altered["run_sha256"] = "0" * 64
        with self.assertRaises(ScenarioError):
            self.engine.replay(altered)

    def test_incoming_event_order_is_normalized(self):
        a = copy.deepcopy(self.alt_spec)
        b = copy.deepcopy(self.alt_spec)
        b["events"].reverse()
        self.assertEqual(self.engine.run(a), self.engine.run(b))

    def test_hypothetical_fork_preserves_pre_fork_state(self):
        events = example("fork-events.json")
        child = self.engine.fork(self.alt_spec, name="fork-after-2030",
                                 fork_year=2030, additional_events=events)
        self.assertEqual(child["branch"]["fork_year"], 2030)
        self.assertEqual(child["branch"]["parent_run_sha256"], self.alternative["run_sha256"])
        self.assertEqual(child["events"][-1]["year"], 2034)
        branch_run = self.engine.run(child)
        for left, right in zip(self.alternative["snapshots"], branch_run["snapshots"]):
            if left["year"] <= 2030:
                self.assertEqual(left["state"], right["state"])
        self.assertNotEqual(self.alternative["final_state"], branch_run["final_state"])
        with self.assertRaises(ScenarioError):
            self.engine.fork(self.alt_spec, name="invalid", fork_year=2030,
                             additional_events=[{"id":"past", "year":2029}])

    def test_scenario_comparison_report(self):
        result = self.engine.compare(self.baseline_spec, self.alt_spec)
        self.assertEqual(result["schema"], "american-empire.scenario-comparison.v1")
        self.assertEqual(result["authority_layer"], "scenario_only")
        self.assertEqual(result["first_divergent_year"], 2030)
        self.assertTrue(result["not_a_canon_revision"])
        self.assertEqual(result["final_variable_deltas_right_minus_left"]["V6"],
                         self.alternative["final_state"]["V6"] - self.baseline["final_state"]["V6"])
        self.assertIsNone(self.engine.compare(self.baseline_spec, self.baseline_spec)["first_divergent_year"])

    def test_invalid_event_types_ids_and_years_are_fail_closed(self):
        changes = [
            {"year": 2040},
            {"intensity": 0},
            {"intensity": True},
            {"type": "world_conquest_immediately"},
            {"subject": "person:invented"},
            {"secret_fact": "no"},
        ]
        for change in changes:
            with self.subTest(change=change):
                scenario = copy.deepcopy(self.alt_spec)
                scenario["events"][0].update(change)
                with self.assertRaises(ScenarioError):
                    self.engine.run(scenario)
        duplicate = copy.deepcopy(self.alt_spec)
        duplicate["events"][1]["id"] = duplicate["events"][0]["id"]
        with self.assertRaises(ScenarioError):
            self.engine.run(duplicate)

    def test_no_canon_overwrite_and_scoped_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            test_output = Path(tmp) / "sim-result.json"
            cli = [sys.executable, str(ROOT / "tools/simulate.py"), "run",
                   "--scenario", str(ROOT / "scenarios/examples/high-integration.json"),
                   "--output", str(test_output)]
            p = subprocess.run(cli, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, msg=p.stderr)
            self.assertEqual(json.loads(test_output.read_text())["authority_layer"], "scenario_only")
            p = subprocess.run(cli, capture_output=True, text=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("Refusing to overwrite", p.stderr)
        attempt = ROOT / "archive" / "evil.json"
        p = subprocess.run([sys.executable, str(ROOT / "tools/simulate.py"), "run",
                            "--scenario", str(ROOT / "scenarios/examples/baseline.json"),
                            "--output", str(attempt)], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse(attempt.exists())

    def test_live_command_line_run_compare_and_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / "receipt.json"
            script = str(ROOT / "tools/simulate.py")
            baseline = str(ROOT / "scenarios/examples/baseline.json")
            alternative = str(ROOT / "scenarios/examples/independent-corridor.json")
            run = subprocess.run([sys.executable, script, "run", "--scenario", alternative,
                                  "--output", str(receipt)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, msg=run.stderr)
            replay = subprocess.run([sys.executable, script, "replay", "--receipt", str(receipt)],
                                    capture_output=True, text=True)
            self.assertEqual(replay.returncode, 0, msg=replay.stderr)
            self.assertTrue(json.loads(replay.stdout)["verified"])
            comparison = subprocess.run([sys.executable, script, "compare", "--left", baseline,
                                         "--right", alternative], capture_output=True, text=True)
            self.assertEqual(comparison.returncode, 0, msg=comparison.stderr)
            self.assertEqual(json.loads(comparison.stdout)["first_divergent_year"], 2030)

    def test_fails_if_source_canon_bytes_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "archive", root / "archive")
            shutil.copytree(ROOT / "tools", root / "tools")
            shutil.copytree(ROOT / "engine", root / "engine")
            shutil.copy2(ROOT / "CANON_LOCK.json", root / "CANON_LOCK.json")
            shutil.copy2(ROOT / "P3_MODEL.json", root / "P3_MODEL.json")
            f = root / "archive/01_CANON_SOURCE/UNIVERSE_BIBLE.md"
            f.write_bytes(f.read_bytes() + b"tampered")
            with self.assertRaises(CanonIntegrityError):
                Simulation(root=root)


if __name__ == "__main__":
    unittest.main()
