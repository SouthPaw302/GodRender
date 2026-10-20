"""Regression tests for the byte-locked recovered AM canon."""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("american_empire_verify_canon", HERE / "tools" / "verify_canon.py")
GUARD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(GUARD)


class CanonLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(HERE / "archive", self.root / "archive")
        shutil.copy2(HERE / "CANON_LOCK.json", self.root / "CANON_LOCK.json")

    def test_verbatim_archive_passes(self):
        self.assertEqual(GUARD.verify(self.root), [])

    def test_modifying_a_single_byte_fails(self):
        f = self.root / "archive" / "01_CANON_SOURCE" / "UNIVERSE_BIBLE.md"
        f.write_bytes(f.read_bytes() + b"\n")
        self.assertTrue(any("BYTES DIFFER" in err for err in GUARD.verify(self.root)))

    def test_adaptation_cannot_become_authority(self):
        p = self.root / "CANON_LOCK.json"
        lock = json.loads(p.read_text())
        lock["policy"]["adaptation_authority"] = "source_canon"
        p.write_text(json.dumps(lock))
        self.assertTrue(any("Adaptation boundary" in err for err in GUARD.verify(self.root)))

    def test_unpinned_file_fails(self):
        (self.root / "archive" / "01_CANON_SOURCE" / "NEW_SCENE.md").write_text("no", encoding="utf-8")
        self.assertTrue(any("Unpinned" in err for err in GUARD.verify(self.root)))

    def test_proposed_addition_not_auto_accepted(self):
        p = self.root / "CANON_LOCK.json"
        lock = json.loads(p.read_text())
        lock["policy"]["proposals_auto_promoted"] = True
        p.write_text(json.dumps(lock))
        self.assertTrue(any("Proposal promotion" in err for err in GUARD.verify(self.root)))


if __name__ == "__main__":
    unittest.main()
