#!/usr/bin/env python3
"""Verify source Git blob content identity, not production/visual acceptance."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/verified_import_manifest.json"

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def main() -> int:
    doc = json.loads(MANIFEST.read_text(encoding="utf-8"))
    problems = []
    counts = {}
    for item in doc["files"]:
        p = ROOT / item["path"]
        role = item["role"]
        counts[role] = counts.get(role,0)+1
        if not p.is_file():
            problems.append("missing: " + item["path"])
            continue
        got = git_blob_sha(p.read_bytes())
        if got != item["git_blob_sha"]:
            problems.append("content mismatch: " + item["path"])
        upstream = item.get("upstream_blob_sha")
        if upstream and got != upstream and not item.get("delta"):
            problems.append("unexplained upstream change: " + item["path"])
    report = {"schema":"godrender.import-verification.v1","files_checked":len(doc["files"]),"roles":counts,"passed":not problems,"errors":problems[:50],"production_boot":"NOT_CHECKED","visual_approval":"NOT_GRANTED"}
    print(json.dumps(report, indent=2))
    return 0 if not problems else 1

if __name__ == "__main__":
    raise SystemExit(main())
