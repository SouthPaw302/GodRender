#!/usr/bin/env python3
"""Fail closed if active GodRender code reaches an external legacy video repository.

Imported upstream/ source is retained as a local archive, not an execution authority.
Compatibility filenames and serialized IDs are intentionally not banned here.
"""
from __future__ import annotations
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEGACY_REMOTE = re.compile(
    r"(?:github\.com[/:]|api\.github\.com/repos/|codeload\.github\.com/)"
    r"(?:SouthPaw302/)?(?:AIVideoEdit(?:-MainV2-Lab)?)(?:\.git|[/\x22']|$)",
    re.IGNORECASE,
)
LEGACY_CLONE = re.compile(
    r"\bgit\s+clone\b.{0,200}\b(?:AIVideoEdit|MainV2-Lab)\b",
    re.IGNORECASE,
)
EXEMPT = ("upstream/", "docs/", "tests/fixtures/", ".git/", "config/brain_source_index.json")
SUFFIX = {".py", ".sh", ".js", ".ts", ".yml", ".yaml", ".json", ".toml", ".ps1"}

def main() -> int:
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True, check=False,
    )
    if tracked.returncode:
        print("INDEPENDENCE FAIL: cannot enumerate tracked files", file=sys.stderr)
        return 1
    findings = []
    for raw in tracked.stdout.split(b"\0"):
        if not raw:
            continue
        name = raw.decode("utf-8", "surrogateescape")
        if name.startswith(EXEMPT) or pathlib.Path(name).suffix.lower() not in SUFFIX:
            continue
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            continue
        try:
            data = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        for number, line in enumerate(data.splitlines(), 1):
            if LEGACY_REMOTE.search(line) or LEGACY_CLONE.search(line):
                findings.append(f"{name}:{number}: forbidden external legacy repository reference")
    if findings:
        print("\n".join(findings), file=sys.stderr)
        print("INDEPENDENCE FAIL", file=sys.stderr)
        return 1
    print("GODRENDER INDEPENDENCE PASS: no external legacy repository references in active tracked code")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
