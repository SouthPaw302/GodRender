#!/usr/bin/env python3
"""Reject legacy engine identifiers in active GodRender executable paths."""
from __future__ import annotations
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREFIXES = ("studio/", "general/reusable/tools/", "general/reusable/fx_v2/",
            "render/", "scripts/", ".github/workflows/")
ROOTS = {"bootstrap.py", "godrender_boot.py", "general/reusable/PRODUCTION_CONTRACT.json",
         "general/reusable/STANDARD_WORKFLOW_REGISTRY.json",
         "general/reusable/PRODUCTION_MODES.json"}
SKIP = ("/proofs/", "/tests/", "studio/static/", "studio/probes/")
PATTERN = re.compile(r"(?:aivideoedit|AIVIDEOEDIT|AIVE_|aive://|aive_|\\.aivideoedit)", re.I)

def main() -> int:
    p = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True)
    if p.returncode:
        print("NATIVE CONTRACT FAIL: cannot inspect tracked files", file=sys.stderr)
        return 1
    problems = []
    for raw in p.stdout.split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8", "surrogateescape")
        if path not in ROOTS and not path.startswith(PREFIXES):
            continue
        if (any(x in path for x in SKIP) or (path.startswith("general/reusable/fx_v2/") and path.endswith(".json")) or pathlib.Path(path).suffix not in {".py", ".json", ".yml", ".yaml", ".sh", ".js", ".ts"}):
            continue
        try:
            data = (ROOT / path).read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        for n, line in enumerate(data.splitlines(), 1):
            if PATTERN.search(line):
                problems.append(f"{path}:{n}")
    if problems:
        print("NATIVE CONTRACT FAIL: retired identifiers in active code\n" + "\n".join(problems[:100]), file=sys.stderr)
        return 1
    print("GODRENDER NATIVE CONTRACT PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
