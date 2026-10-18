#!/usr/bin/env python3
"""Build compact deterministic browser controls from canonical AIVideoEdit audiomap."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "analysis" / "audiomap.json"
dst = Path(__file__).resolve().parent / "control-map.js"
doc = json.loads(src.read_text(encoding="utf-8"))
if doc.get("schema") != "aivideoedit.audiomap.v1":
    raise SystemExit("canonical audiomap schema mismatch")
payload = {
    "schema": "aivideoedit.browser-control-map.v1",
    "source_sha256": doc.get("source", {}).get("sha256"),
    "duration": doc.get("audio", {}).get("duration_sec"),
    "bpm": doc.get("rhythm", {}).get("bpm"),
    "energy": [
        {
            "start": x.get("start"),
            "end": x.get("end"),
            "energy": x.get("energy"),
            "level": x.get("level"),
        }
        for x in doc.get("energy", {}).get("buckets", [])
    ],
    "key_moments": doc.get("energy", {}).get("key_moments", []),
    "rolls": doc.get("rolls", []),
    "silences": doc.get("silences", []),
    "phrases": doc.get("phrase_candidates", []),
}
dst.write_text(
    "window.AIVIDEOEDIT_CONTROL_MAP=Object.freeze(" +
    json.dumps(payload, separators=(",", ":"), sort_keys=True) +
    ");\n",
    encoding="utf-8",
)
print(json.dumps({
    "output": str(dst),
    "energy_buckets": len(payload["energy"]),
    "key_moments": len(payload["key_moments"]),
    "rolls": len(payload["rolls"]),
    "phrases": len(payload["phrases"]),
}, indent=2))
