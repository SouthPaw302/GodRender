"""P2 tests: queries are traceable, reproducible and cannot promote candidates."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from world_matrix import CanonIntegrityError, UnknownEntityError, WorldMatrix  # noqa: E402


class WorldMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = WorldMatrix()

    def test_graph_uses_original_p1_matrix(self):
        self.assertEqual(self.world.export()["source"]["matrix_git_blob_sha1"],
                         "575e8c1b20bc6e9bf5c61ac32e32536256abcab0")
        self.assertEqual(self.world.export()["source"]["commit"],
                         "d768ee1684ebddd06af249f3a366181c929bc80c")
        self.assertEqual(self.world.export()["stage"], "P2_QUERY_ONLY")

    def test_full_matrix_was_indexed(self):
        counts = self.world.counts()
        self.assertEqual(counts["nodes"], 52)
        self.assertEqual(counts["edges"], 48)
        self.assertEqual(counts["kinds"]["actor"], 10)
        self.assertEqual(counts["kinds"]["system"], 6)
        self.assertEqual(counts["kinds"]["person"], 5)
        self.assertEqual(counts["kinds"]["event"], 19)
        self.assertEqual(counts["kinds"]["variable"], 7)
        self.assertEqual(counts["kinds"]["reality_anchor"], 4)
        self.assertEqual(counts["kinds"]["institution"], 1)

    def test_all_edges_resolve_and_carry_pinned_provenance(self):
        export = self.world.export()
        ids = {n["id"] for n in export["nodes"]}
        self.assertEqual(len(ids), len(export["nodes"]))
        self.assertEqual(len({x["id"] for x in export["edges"]}), len(export["edges"]))
        for item in export["nodes"] + export["edges"]:
            self.assertTrue(item["source"]["path"].startswith("archive/"))
            self.assertEqual(item["source"]["git_blob_sha1"],
                             "575e8c1b20bc6e9bf5c61ac32e32536256abcab0")
            self.assertEqual(item["layer"], "established")
        for edge in export["edges"]:
            self.assertIn(edge["from"], ids)
            self.assertIn(edge["to"], ids)

    def test_atlas_relationships_and_prerequisites(self):
        related = self.world.relations("system:S1", direction="outgoing")
        self.assertTrue(any(x["to"] == "actor:A8" and x["strength"] == -5
                            for x in related))
        self.assertEqual(
            {x["to"] for x in related if x["kind"] == "prerequisite"},
            {"system:S2", "system:S3", "system:S4"}
        )
        self.assertTrue(all("json_pointer" in x["source"] for x in related))
        with self.assertRaises(UnknownEntityError):
            self.world.relations("system:nonexistent")

    def test_canonical_timeline_is_not_interpolated(self):
        self.assertEqual([x["attributes"]["year"] for x in self.world.timeline()],
                         [str(x) for x in range(2026, 2038)])
        self.assertEqual([x["attributes"]["year"] for x in self.world.timeline(year=2030)],
                         ["2030"])
        self.assertEqual(len(self.world.timeline(year=2030, through=True)), 5)
        with self.assertRaises(ValueError):
            self.world.timeline(year=2040)

    def test_proposed_chronicle_additions_are_not_facts(self):
        proposals = self.world.proposals()
        self.assertEqual(len(proposals), 3)
        self.assertTrue(all(x["status"] == "candidate_unapproved" for x in proposals))
        self.assertTrue(all(x["source"]["authority_layer"] == "proposal" for x in proposals))
        self.assertTrue(self.world.search("Winter Bridge Compact", layer="proposal"))
        self.assertFalse(self.world.search("Winter Bridge Compact", layer="established"))
        self.assertFalse(self.world.search("Paris", layer="adaptation"))
        self.assertFalse(self.world.search("Dollar Night", layer="scenario"))
        self.assertEqual(len(self.world.documents()), 3)

    def test_public_api_results_are_defensive_copies(self):
        original = self.world.entity("actor:A1")
        edited = self.world.entity("actor:A1")
        edited["name"] = "FAKE"
        edited["attributes"]["goal"] = "INVENTED"
        self.assertEqual(original, self.world.entity("actor:A1"))
        edited = self.world.export()
        edited["nodes"].clear()
        edited["edges"].clear()
        self.assertEqual(self.world.counts()["nodes"], 52)
        self.assertEqual(self.world.counts()["edges"], 48)

    def test_deterministic_snapshot_fingerprint(self):
        other = WorldMatrix()
        self.assertEqual(other.digest, self.world.digest)
        self.assertEqual(other.export(), self.world.export())
        self.assertEqual(len(self.world.digest), 64)

    def test_rejects_archive_drift(self):
        import shutil
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            shutil.copytree(ROOT / "archive", target / "archive")
            shutil.copytree(ROOT / "tools", target / "tools")
            shutil.copy2(ROOT / "CANON_LOCK.json", target / "CANON_LOCK.json")
            source = target / "archive/01_CANON_SOURCE/REALITY_MATRIX.json"
            source.write_bytes(source.read_bytes() + b" ")
            with self.assertRaises(CanonIntegrityError):
                WorldMatrix(root=target)

    def test_command_line_outputs_machine_readable_json(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools/world.py"), "show", "person:P3"],
            text=True, capture_output=True, check=True,
        )
        item = json.loads(proc.stdout)
        self.assertEqual(item["name"], "Dr. Neda Farzan")
        self.assertEqual(item["source"]["json_pointer"], "/point_of_view_characters/2")

    def test_export_does_not_write_to_source_archive(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools/world.py"), "export", "--output",
             str(ROOT / "archive/attempted-export.json")],
            text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Refusing to write", proc.stderr)
        self.assertFalse((ROOT / "archive/attempted-export.json").exists())


if __name__ == "__main__":
    unittest.main()
