#!/usr/bin/env python3
"""GodRender entrypoint: fail-closed, versioned compatibility-engine bootstrap."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "studio"))
from core_adapter import CORE  # noqa: E402

def main() -> int:
    parser = argparse.ArgumentParser(description="Boot the verified GodRender production compatibility engine")
    parser.add_argument("--offline", action="store_true", help="use the local verified GodRender checkout")
    args = parser.parse_args()
    result = CORE.bootstrap(offline=args.offline)
    ok = bool(result.get("bootstrapped")) and bool(result.get("ok"))
    stdout = str(result.get("stdout") or "")
    if "GODRENDER OS BOOTSTRAP: PASS" not in stdout:
        ok = False
    public = {k: result.get(k) for k in ("phase","returncode","bootstrapped","main_commit","session_id","host_repo","core_repo","error")}
    public["boot_stdout_pass"] = "GODRENDER OS BOOTSTRAP: PASS" in stdout
    print(json.dumps(public, indent=2))
    if not ok:
        print("GodRender boot gate FAIL: missing validated GitHub main/OS attestation", file=sys.stderr)
        if stdout:
            print(stdout[-1600:], file=sys.stderr)
        if result.get("stderr"):
            print(str(result["stderr"])[-1600:], file=sys.stderr)
        return 1
    print("GODRENDER BOOT PASS: native production engine attested; Drive is lookup-only.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
