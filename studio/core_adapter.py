#!/usr/bin/env python3
"""Adapter between the workstation stack and the canonical AIVideoEdit OS.

The workstation is not a production branch and must never pretend to be one.
This adapter installs a clean current `main` checkout into the runtime cache,
boots/attests that checkout as `main`, and reads canonical contracts,
capabilities and effects from its `.aivideoedit/os` snapshot.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
HOST_REPO = HERE.parent
CANONICAL_REMOTE = "https://github.com/SouthPaw302/AIVideoEdit-MainV2-Lab.git"
RUNTIME = Path(os.environ.get("AIVE_RUNTIME", str(HERE / ".runtime"))).resolve()
CORE_HOME = RUNTIME / "core"
CORE_REPO = CORE_HOME / "repo"
SESSION_ROOT = CORE_REPO / ".aivideoedit"
OS_ROOT = SESSION_ROOT / "os"
SESSION_FILE = SESSION_ROOT / "session.json"
CONTRACT = Path("general/reusable/PRODUCTION_CONTRACT.json")
CAPABILITY_MATRIX = Path("general/reusable/MEDIA_CAPABILITY_MATRIX.json")
FX_REGISTRY = Path("general/reusable/fx_v2/registry.json")


def _core_ref() -> str:
    value = os.environ.get("AIVE_CORE_REF", "main").strip()
    return value or "main"


@lru_cache(maxsize=64)
def _read_json_at_version(path: str, mtime_ns: int, size: int, inode: int) -> Any:
    """Reuse unmodified registry/config JSON across frequent Studio polls."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_json(path: Path, default: Any) -> Any:
    try:
        stamp = path.stat()
        return _read_json_at_version(str(path), stamp.st_mtime_ns, stamp.st_size, stamp.st_ino)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return default


@lru_cache(maxsize=1)
def _host_branch() -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(HOST_REPO), "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except Exception:
        pass
    return "unknown"


def _run(cmd: list[str], cwd: Path, timeout: int = 300, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env=env,
    )


class CoreAdapter:
    def __init__(self) -> None:
        self.host_repo = HOST_REPO
        self.core_repo = CORE_REPO
        self.os_root = OS_ROOT
        self.session_file = SESSION_FILE
        self._boot_lock = threading.RLock()
        self._previous_core: Path | None = None

    def _session_valid(self, session: dict) -> bool:
        return (
            session.get("schema") == "aivideoedit.session.v1"
            and session.get("branch") == "main"
            and session.get("guard_result") == "PASS"
            and bool(session.get("session_id"))
            and bool(session.get("os_main_commit"))
            and session.get("os_root") == str(self.os_root)
            and self.os_root.is_dir()
            and (self.core_repo / "bootstrap.py").is_file()
        )

    def _restore_prior_core(self) -> None:
        """Rollback a candidate that failed bootstrap instead of losing the last PASS."""
        if self._previous_core is None:
            return
        if self.core_repo.exists():
            shutil.rmtree(self.core_repo)
        if self._previous_core.exists():
            self._previous_core.rename(self.core_repo)
        self._previous_core = None

    def _commit_core(self) -> None:
        if self._previous_core is not None:
            shutil.rmtree(self._previous_core, ignore_errors=True)
            self._previous_core = None

    def _install_core(self, offline: bool) -> subprocess.CompletedProcess:
        """Clone first; never destroy the known-good core when GitHub is unavailable."""
        if not shutil.which("git"):
            raise RuntimeError("git is required for canonical production boot")
        ref = _core_ref()
        if ref != "main" and os.environ.get("AIVIDEOEDIT_VALIDATION_MODE") != "1":
            raise RuntimeError("non-main core ref requires explicit validation mode")
        source = os.environ.get("AIVE_CORE_LOCAL_REPO", "").strip() if offline else CANONICAL_REMOTE
        if not source:
            raise RuntimeError("offline boot requires AIVE_CORE_LOCAL_REPO pointing to a real AIVideoEdit checkout")
        CORE_HOME.mkdir(parents=True, exist_ok=True)
        pending = CORE_HOME / (".incoming-" + uuid.uuid4().hex)
        prior = CORE_HOME / (".previous-" + uuid.uuid4().hex)
        try:
            install = _run(
                ["git", "clone", "--no-hardlinks", "--branch", ref, "--single-branch", source, str(pending)],
                HOST_REPO,
                timeout=300,
            )
            if install.returncode != 0:
                return install
            if not (pending / "bootstrap.py").is_file():
                return subprocess.CompletedProcess(
                    args=install.args, returncode=1, stdout=install.stdout,
                    stderr="cloned source lacks canonical bootstrap.py",
                )
            if CORE_REPO.exists():
                CORE_REPO.rename(prior)
            try:
                pending.rename(CORE_REPO)
            except Exception:
                if prior.exists():
                    prior.rename(CORE_REPO)
                raise
            self._previous_core = prior if prior.exists() else None
            return install
        finally:
            if pending.exists():
                shutil.rmtree(pending, ignore_errors=True)

    def bootstrap(self, offline: bool = False) -> dict:
        with self._boot_lock:
            try:
                install = self._install_core(offline)
                if install.returncode != 0:
                    snapshot = self.status()
                    return {
                        **snapshot, "ok": False, "bootstrapped": False,
                        "previous_core_available": snapshot["bootstrapped"],
                        "phase": "install",
                        "stdout": (install.stdout or "")[-4000:],
                        "stderr": (install.stderr or "")[-4000:],
                    }
                bootstrap = CORE_REPO / "bootstrap.py"
                env = dict(os.environ)
                requested_ref = _core_ref()
                if requested_ref != "main":
                    env["AIVIDEOEDIT_AUTHORITY_REF"] = requested_ref
                    env["AIVIDEOEDIT_VALIDATION_MODE"] = "1"
                cmd = [
                    sys.executable, str(bootstrap), "boot",
                    "--repo-root", str(CORE_REPO), "--branch", "main",
                ]
                if offline:
                    cmd.append("--offline")
                proc = _run(cmd, CORE_REPO, timeout=300, env=env)
                valid = (
                    proc.returncode == 0
                    and "AIVideoEdit OS BOOTSTRAP: PASS" in (proc.stdout or "")
                    and self._session_valid(_read_json(self.session_file, {}))
                )
                if not valid:
                    self._restore_prior_core()
                    snapshot = self.status()
                    return {
                        **snapshot, "ok": False, "bootstrapped": False,
                        "previous_core_available": snapshot["bootstrapped"],
                        "phase": "boot", "returncode": proc.returncode,
                        "stdout": (proc.stdout or "")[-4000:],
                        "stderr": ((proc.stderr or "") + "\\nBOOTSTRAP ATTESTATION FAILED")[-4000:],
                    }
                self._commit_core()
                return {
                    **self.status(), "ok": True, "bootstrapped": True,
                    "returncode": 0, "phase": "boot",
                    "stdout": (proc.stdout or "")[-4000:],
                    "stderr": (proc.stderr or "")[-4000:],
                }
            except Exception as exc:
                try:
                    self._restore_prior_core()
                    recovery_error = None
                except Exception as recovery:
                    recovery_error = str(recovery)
                snapshot = self.status()
                return {
                    **snapshot, "ok": False, "bootstrapped": False,
                    "previous_core_available": snapshot["bootstrapped"],
                    "phase": "exception",
                    "error": str(exc), "recovery_error": recovery_error,
                }

    def status(self) -> dict:
        with self._boot_lock:
            return self._status_unlocked()

    def _status_unlocked(self) -> dict:
        session = _read_json(self.session_file, {})
        contract = _read_json(self.os_root / CONTRACT, {}) if self.os_root.is_dir() else {}
        matrix = _read_json(self.os_root / CAPABILITY_MATRIX, {}) if self.os_root.is_dir() else {}
        fx = _read_json(self.os_root / FX_REGISTRY, {}) if self.os_root.is_dir() else {}
        capabilities = self._records(matrix, ("capabilities", "media_capabilities", "items"))
        effects = self._records(fx, ("effects", "fx", "registry", "items"))
        ref = _core_ref()
        bootstrapped = self._session_valid(session)
        return {
            "ok": True,
            "bootstrapped": bootstrapped,
            "mode": "isolated-canonical-main" if ref == "main" else "isolated-validation-ref",
            "requested_core_ref": ref,
            "host_repo": str(self.host_repo),
            "host_branch": _host_branch(),
            "core_repo": str(self.core_repo) if self.core_repo.exists() else None,
            "core_branch": session.get("branch"),
            "os_root": str(self.os_root) if bootstrapped else None,
            "main_commit": session.get("os_main_commit"),
            "session_id": session.get("session_id"),
            "guard_result": session.get("guard_result"),
            "contract_schema": contract.get("schema"),
            "production_states": contract.get("states", []),
            "capability_count": len(capabilities),
            "fx_count": len(effects),
        }

    @staticmethod
    def _records(payload: Any, keys: tuple[str, ...]) -> list:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in keys:
                value = payload.get(key)
                if isinstance(value, list):
                    return value
                if isinstance(value, dict):
                    return [dict({"id": k}, **(v if isinstance(v, dict) else {"value": v})) for k, v in value.items()]
            records = []
            for key, value in payload.items():
                if isinstance(value, dict):
                    records.append(dict({"id": key}, **value))
            if records:
                return records
        return []

    def production_contract(self) -> dict:
        return _read_json(self.os_root / CONTRACT, {})

    def capabilities(self) -> list:
        payload = _read_json(self.os_root / CAPABILITY_MATRIX, {})
        return self._records(payload, ("capabilities", "media_capabilities", "items"))

    def effects(self) -> list:
        payload = _read_json(self.os_root / FX_REGISTRY, {})
        return self._records(payload, ("effects", "fx", "registry", "items"))


CORE = CoreAdapter()
