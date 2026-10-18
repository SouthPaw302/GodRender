#!/usr/bin/env python3
"""GodRender agent entry: fail-closed GitHub-first canonical AIVideoEdit boot."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "studio"))
from core_adapter import CORE  # noqa: E402

def main() -> int:
    parser = argparse.ArgumentParser(description="Boot canonical AIVideoEdit OS before GodRender production")
    parser.add_argument("--offline", action="store_true", help="only with AIVE_CORE_LOCAL_REPO")
    args = parser.parse_args()
    result = CORE.bootstrap(offline=args.offline)
    ok = bool(result.get("bootstrapped")) and bool(result.get("ok"))
    stdout = str(result.get("stdout") or "")
    if "AIVideoEdit OS BOOTSTRAP: PASS" not in stdout:
        ok = False
    public = {k: result.get(k) for k in ("phase","returncode","bootstrapped","main_commit","session_id","host_repo","core_repo","error")}
    public["boot_stdout_pass"] = "AIVideoEdit OS BOOTSTRAP: PASS" in stdout
    print(json.dumps(public, indent=2))
    if not ok:
        print("GodRender boot gate FAIL: missing validated GitHub main/OS attestation", file=sys.stderr)
        if stdout:
            print(stdout[-1600:], file=sys.stderr)
        if result.get("stderr"):
            print(str(result["stderr"])[-1600:], file=sys.stderr)
        return 1
    print("GODRENDER BOOT PASS: canonical main attested; Drive is lookup-only.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
