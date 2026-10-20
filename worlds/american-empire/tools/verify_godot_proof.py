#!/usr/bin/env python3
"""P4: fail-closed checks for actual Godot/GL captured interface proof frames."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"
SIZE = (1440, 900)
FRAMES = 48
FPS = 24


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_geometry(path: Path) -> tuple[int, int]:
    with path.open("rb") as f:
        header = f.read(24)
    if header[:8] != PNG_SIG or header[12:16] != b"IHDR":
        raise ValueError(f"Invalid PNG frame: {path.name}")
    return struct.unpack(">II", header[16:24])


def verify(root: Path, source_sha: str) -> dict:
    frames = sorted(root.glob("proof[0-9]*.png"))
    if len(frames) != FRAMES:
        raise ValueError(f"Expected {FRAMES} actual Godot frames, found {len(frames)}")
    if [p.name for p in frames] != [f"proof{i:08d}.png" for i in range(FRAMES)]:
        raise ValueError("Missing or duplicate numbered frames")
    samples = [frames[i] for i in (0, 15, 29, 43, 47)]
    for p in samples:
        if image_geometry(p) != SIZE:
            raise ValueError(f"Wrong Godot view geometry in {p}")
        if p.stat().st_size < 10_000:
            raise ValueError(f"UI frame too small to be a useful proof: {p}")
    fingerprints = [sha(p) for p in samples]
    if len(set(fingerprints)) < 3:
        raise ValueError("UI did not visibly change enough across selected years/scenarios")
    log = (root / "godot.log").read_text(encoding="utf-8")
    required = (
        "AMERICAN EMPIRE P4 READY:",
        "AE_P4_VIEW year=2027 scenario=baseline",
        "AE_P4_VIEW year=2029 scenario=baseline",
        "AE_P4_VIEW year=2029 scenario=independent-corridor",
        "AE_P4_VIEW year=2033 scenario=independent-corridor",
    )
    if any(marker not in log for marker in required):
        raise ValueError("Actual interactive year/scenario control evidence missing")
    if any(term in log for term in ("SCRIPT ERROR", "Parse Error", "Invalid call", "ERROR:")):
        raise ValueError("Godot runtime errors in log")
    proof = root / "proof.mp4"
    if not proof.is_file() or proof.stat().st_size < 30_000:
        raise ValueError("Godot-based movie proof missing or too small")
    tool = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
         str(proof)], check=True, capture_output=True, text=True
    )
    ff = json.loads(tool.stdout)
    video = [s for s in ff["streams"] if s["codec_type"] == "video"]
    if len(video) != 1 or (video[0]["width"], video[0]["height"]) != SIZE:
        raise ValueError("Captured MP4 video geometry is incorrect")
    if video[0].get("nb_frames") and int(video[0]["nb_frames"]) != FRAMES:
        raise ValueError("Captured MP4 frame count incorrect")
    duration = float(ff["format"]["duration"])
    if not 1.8 <= duration <= 2.25:
        raise ValueError(f"Captured movie duration implausible: {duration}")
    report = {
        "schema": "american-empire.p4.godot-proof.v1",
        "status": "TECHNICAL_EXPLORER_PASS",
        "godot_executed": True,
        "proof": "actual Xvfb/Mesa rendered interactive canvas, not headless dummy rendering",
        "canon_authority": "P1 and P2 unchanged",
        "scenario_status": "P3 values are hypothetical",
        "scene": "res://scenes/world_explorer.tscn",
        "source_commit": source_sha,
        "resolution": list(SIZE),
        "frame_count": len(frames),
        "fps": FPS,
        "sample_frame_sha256": fingerprints,
        "movie_sha256": sha(proof),
        "movie_duration_seconds": duration,
        "web_deployed": False,
        "production_approved": False,
        "geographic_simulation": False,
    }
    (root / "verification.json").write_text(json.dumps(report, indent=2) + "\n",
                                             encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source-sha", required=True)
    args = p.parse_args()
    try:
        verify(args.root, args.source_sha)
    except (ValueError, OSError, subprocess.CalledProcessError) as e:
        print(f"P4 GODOT PROOF FAILED: {e}", file=sys.stderr)
        sys.exit(2)
