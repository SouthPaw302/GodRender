"""Regression tests for failed OS installs and idempotent Studio media preparation."""
from __future__ import annotations
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import core_adapter
import stack


class CoreRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "core"
        self.repo = self.home / "repo"
        self.os_root = self.repo / ".aivideoedit" / "os"
        self.session = self.repo / ".aivideoedit" / "session.json"
        values = {
            "CORE_HOME": self.home,
            "CORE_REPO": self.repo,
            "SESSION_ROOT": self.repo / ".aivideoedit",
            "OS_ROOT": self.os_root,
            "SESSION_FILE": self.session,
            "HOST_REPO": self.root,
        }
        for name, value in values.items():
            p = mock.patch.object(core_adapter, name, value)
            p.start()
            self.addCleanup(p.stop)
        git = mock.patch.object(core_adapter.shutil, "which", return_value="/usr/bin/git")
        git.start()
        self.addCleanup(git.stop)
        self.adapter = core_adapter.CoreAdapter()

    def _old_good_core(self):
        self.repo.mkdir(parents=True, exist_ok=True)
        (self.repo / "bootstrap.py").write_text("pass\n", encoding="utf-8")
        (self.repo / "preserved.txt").write_text("prior-good-core", encoding="utf-8")
        self.os_root.mkdir(parents=True, exist_ok=True)
        self.session.write_text(json.dumps({
            "schema": "aivideoedit.session.v1", "branch": "main",
            "guard_result": "PASS", "session_id": "old-session",
            "os_main_commit": "a" * 40, "os_root": str(self.os_root),
        }), encoding="utf-8")

    def _runner(self, *, clone_return=0, boot_return=0, valid_session=True):
        def run(cmd, cwd, timeout=300, env=None):
            if cmd[0] == "git":
                if clone_return:
                    return subprocess.CompletedProcess(cmd, clone_return, "", "git clone failed")
                new = Path(cmd[-1])
                new.mkdir(parents=True, exist_ok=True)
                (new / "bootstrap.py").write_text("pass\n", encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, "cloned", "")
            if boot_return == 0 and valid_session:
                self.os_root.mkdir(parents=True, exist_ok=True)
                self.session.write_text(json.dumps({
                    "schema": "aivideoedit.session.v1", "branch": "main",
                    "guard_result": "PASS", "session_id": "new-session",
                    "os_main_commit": "b" * 40, "os_root": str(self.os_root),
                }), encoding="utf-8")
            return subprocess.CompletedProcess(
                cmd, boot_return,
                "AIVideoEdit OS BOOTSTRAP: PASS" if boot_return == 0 else "",
                "boot failed" if boot_return else "",
            )
        return run

    def test_clone_failure_keeps_last_good_core_and_never_reports_success(self):
        self._old_good_core()
        with mock.patch.object(core_adapter, "_run", side_effect=self._runner(clone_return=3)):
            result = self.adapter.bootstrap()
        self.assertFalse(result["ok"])
        self.assertFalse(result["bootstrapped"])
        self.assertTrue(result["previous_core_available"])
        self.assertEqual((self.repo / "preserved.txt").read_text(), "prior-good-core")
        self.assertTrue(self.adapter.status()["bootstrapped"])

    def test_failed_boot_restores_previous_core(self):
        self._old_good_core()
        with mock.patch.object(core_adapter, "_run", side_effect=self._runner(boot_return=7)):
            result = self.adapter.bootstrap()
        self.assertFalse(result["ok"])
        self.assertEqual(result["phase"], "boot")
        self.assertEqual((self.repo / "preserved.txt").read_text(), "prior-good-core")
        self.assertTrue(self.adapter.status()["bootstrapped"])

    def test_failed_first_boot_removes_untrusted_checkout(self):
        with mock.patch.object(core_adapter, "_run", side_effect=self._runner(boot_return=7)):
            result = self.adapter.bootstrap()
        self.assertFalse(result["ok"])
        self.assertFalse(self.repo.exists())

    def test_boot_pass_replaces_core_only_after_attestation(self):
        self._old_good_core()
        with mock.patch.object(core_adapter, "_run", side_effect=self._runner()):
            result = self.adapter.bootstrap()
        self.assertTrue(result["ok"])
        self.assertTrue(result["bootstrapped"])
        self.assertFalse((self.repo / "preserved.txt").exists())
        self.assertEqual(self.adapter.status()["main_commit"], "b" * 40)
        self.assertEqual(list(self.home.glob(".previous-*")), [])

    def test_missing_session_cannot_fake_successful_boot(self):
        with mock.patch.object(core_adapter, "_run", side_effect=self._runner(valid_session=False)):
            result = self.adapter.bootstrap()
        self.assertFalse(result["ok"])
        self.assertFalse(result["bootstrapped"])
        self.assertFalse(self.repo.exists())

    def test_unattested_session_cannot_fake_boot(self):
        self.repo.mkdir(parents=True)
        (self.repo / "bootstrap.py").write_text("pass\n")
        self.os_root.mkdir(parents=True)
        self.session.write_text(json.dumps({"branch": "main", "os_root": str(self.os_root)}))
        self.assertFalse(self.adapter.status()["bootstrapped"])


class StudioQueueTests(unittest.TestCase):
    def test_prepare_does_not_repeat_running_jobs(self):
        state = {
            "projects": [{"id": "p"}],
            "assets": [{
                "id": "a", "project": "p", "status": "ready",
                "metadata": {"video_codec": "h264"},
                "proxy_url": None, "review_frames": [],
                "qc": {"status": "unchecked"},
            }],
            "jobs": [{"id": "j1", "type": "make_proxy", "asset_id": "a",
                      "project": "p", "status": "running"}],
        }
        def add_job(typ, pid, asset_id):
            job = {"id": str(len(state["jobs"]) + 1), "type": typ, "project": pid,
                   "asset_id": asset_id, "status": "queued"}
            state["jobs"].append(job)
            return job
        with mock.patch.object(stack.base, "STATE", state), \
             mock.patch.object(stack.base, "add_job", side_effect=add_job), \
             mock.patch.object(stack, "dispatch_job") as dispatch:
            first = stack.prepare_project("p")
            self.assertEqual({j["type"] for j in first}, {"extract_review_frames", "qc_media"})
            self.assertEqual(stack.prepare_project("p"), [])
            self.assertEqual(dispatch.call_count, 2)

    def test_oversized_json_request_is_rejected_without_reading(self):
        reader = mock.Mock()
        h = SimpleNamespace(headers={"Content-Length": str(2 * 1024 * 1024 + 1)}, rfile=reader)
        with self.assertRaises(ValueError):
            stack._json_body(h)
        reader.read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
