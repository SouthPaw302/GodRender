#!/usr/bin/env python3
"""Prepare and launch American Empire's Godot P4 viewer from locked local sources."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT_PROJECT = ROOT / "godot"
BRIDGE = ROOT / "tools" / "build_explorer_bundle.py"

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--godot-bin", help="Godot 4.x executable; else GODOT_BIN environment or PATH")
    p.add_argument("--prepare-only", action="store_true")
    args = p.parse_args()
    built = subprocess.run([sys.executable, str(BRIDGE), "--check-reproducible"])
    if built.returncode:
        return built.returncode
    if args.prepare_only:
        print("P4 viewer bundle ready. Open Godot project:", GODOT_PROJECT)
        return 0
    target = args.godot_bin or os.environ.get("GODOT_BIN") or shutil.which("godot") or shutil.which("godot4")
    if not target:
        print("Godot 4 binary not found; use --godot-bin /path/to/godot, or --prepare-only.", file=sys.stderr)
        return 2
    return subprocess.call([target, "--path", str(GODOT_PROJECT), "--rendering-method", "gl_compatibility"])

if __name__ == "__main__":
    sys.exit(main())
