#!/usr/bin/env python3
"""Nordic B01 Brain/repo-driven Director FX render.

This file contains project choreography only. It does not implement new FX.
It calls existing GodRender FX modules and records the exact implementations used.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from general.reusable.fx_v2.executor import FXExecutor
from general.reusable.fx_v2.runtime import FXContext
from general.reusable.fx_v2 import living_still_fx

PLAN_DEFAULT = REPO / "projects/nordic-remastered/production/B01_BRAIN_FX_RENDER_PLAN.json"
HYBRID_PATH = REPO / "general/reusable/painterly-motion/hybrid_painterly_fx.py"
STREAMING_PATH = REPO / "general/reusable/generative-engine/spatial/living_parallax.py"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


HYBRID = load_module(HYBRID_PATH, "nordic_b01_hybrid_fx")
STREAMING = load_module(STREAMING_PATH, "nordic_b01_streaming_parallax")


def read_image(path: Path, width: int, height: int) -> np.ndarray:
    im = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if im is None:
        raise RuntimeError(f"cannot read image: {path}")
    if (im.shape[1], im.shape[0]) != (width, height):
        im = cv2.resize(im, (width, height), interpolation=cv2.INTER_LANCZOS4)
    return im


def masks(shape):
    h, w = shape[:2]
    protect = np.zeros((h, w), np.float32)
    # Observer, raised hand and cliff are intentionally conservative.
    cv2.ellipse(protect, (int(w * .245), int(h * .66)), (int(w * .245), int(h * .43)), 0, 0, 360, 1.0, -1)
    cv2.rectangle(protect, (0, int(h * .69)), (int(w * .47), h - 1), 1.0, -1)
    protect = cv2.GaussianBlur(protect, (0, 0), 22)
    protect = np.clip(protect, 0, 1)
    env = 1.0 - protect

    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    sky_band = np.clip((.82 - yy) / .18, 0, 1)
    sky = np.clip(env * sky_band, 0, 1)
    return env, sky, protect


def blend(a: np.ndarray, b: np.ndarray, mask: np.ndarray, amount: float = 1.0) -> np.ndarray:
    m = np.clip(mask * float(amount), 0, 1).astype(np.float32)[..., None]
    return np.clip(a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m, 0, 255).astype(np.uint8)


def apply_old_depth(frame: np.ndarray, phase: float, amount: float, env_mask: np.ndarray) -> np.ndarray:
    depth = HYBRID.depth_proxy(frame)
    warped = HYBRID.depth_parallax(frame, depth, phase, amount=float(amount))
    return blend(frame, warped, env_mask, .92)


def apply_streaming_depth(frame: np.ndarray, phase: float, strength: float, env_mask: np.ndarray) -> np.ndarray:
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    h, w = frame.shape[:2]
    depth, mode = STREAMING.load_depth(None, h, w)
    if mode != "synthetic_radial_fallback":
        raise RuntimeError(f"unexpected streaming parallax depth mode: {mode}")
    angle = phase * math.tau
    warped_rgb = STREAMING.warp(
        rgb,
        depth,
        dx=math.sin(angle) * .72,
        dy=math.sin(angle * 2.0) * .26,
        strength=float(strength),
    )
    warped = cv2.cvtColor(np.uint8(np.clip(warped_rgb * 255.0, 0, 255)), cv2.COLOR_RGB2BGR)
    return blend(frame, warped, env_mask, .90)


def ffprobe(path: Path) -> dict:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-count_frames",
        "-show_entries", "format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate,nb_read_frames",
        "-of", "json", str(path)
    ], text=True)
    return json.loads(out)


def render(plan_path: Path, input_root: Path, audio_path: Path, out_dir: Path) -> tuple[Path, Path]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    fps = int(plan["fps"])
    width = int(plan["width"])
    height = int(plan["height"])
    if sum(int(s["frames"]) for s in plan["shots"]) != int(plan["total_frames"]):
        raise RuntimeError("shot frames do not equal total_frames")
    if sha256_file(audio_path) != plan["audio_sha256"]:
        raise RuntimeError("master audio SHA mismatch")

    shots = plan["shots"]
    images = []
    for shot in shots:
        p = input_root / shot["file"]
        actual = sha256_file(p)
        if actual != shot["sha256"]:
            raise RuntimeError(f"source hash mismatch: {shot['id']} {actual}")
        images.append(read_image(p, width, height))

    out_dir.mkdir(parents=True, exist_ok=True)
    silent = out_dir / "b01_brain_fx_silent.mp4"
    final = out_dir / "NORDIC_B01_BRAIN_FX_PROOF03_720p.mp4"
    receipt_path = out_dir / "NORDIC_B01_BRAIN_FX_PROOF03_RECEIPT.json"
    ledger = out_dir / "fx_execution_ledger.jsonl"
    fx = FXExecutor(seed=302, ledger_path=str(ledger), consumer="nordic_b01_brain_fx")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent)
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    if proc.stdin is None:
        raise RuntimeError("ffmpeg stdin unavailable")

    global_frame = 0
    used_legacy = set()
    used_approved = set()
    per_shot = []

    try:
        for si, shot in enumerate(shots):
            src = images[si]
            nxt = images[si + 1] if si + 1 < len(images) else None
            env_mask, sky_mask, _ = masks(src.shape)
            nframes = int(shot["frames"])
            transition_n = int(shot.get("transition_frames", 0)) if shot.get("transition") == "ghost" else 0
            shot_used = set()

            for li in range(nframes):
                phase = li / max(nframes - 1, 1)
                ctx = FXContext(
                    t=li / fps,
                    duration=nframes / fps,
                    frame_index=global_frame,
                    fps=fps,
                    energy=.15 + .16 * (global_frame / max(plan["total_frames"] - 1, 1)),
                    transient=.02 + .05 * (global_frame / max(plan["total_frames"] - 1, 1)),
                    brightness=.28,
                )
                frame = src.copy()

                # Brain-selected legacy/proven atmosphere, Director-authorized for Nordic B01.
                if float(shot.get("cloud", 0)) > 0:
                    candidate = living_still_fx.cloud_drift(
                        frame, ctx, roi=(.24, .05, 1.0, .76),
                        strength=float(shot["cloud"]), seed=302
                    )
                    frame = blend(frame, candidate, sky_mask, .95)
                    used_legacy.add("FX2-ATM-005"); shot_used.add("FX2-ATM-005")

                if float(shot.get("stars", 0)) > 0:
                    candidate = living_still_fx.star_field(
                        frame, ctx, roi=(0.0, .0, 1.0, .76),
                        strength=float(shot["stars"]), count=72, seed=302
                    )
                    frame = blend(frame, candidate, sky_mask, 1.0)
                    used_legacy.add("FX2-ATM-006"); shot_used.add("FX2-ATM-006")

                if shot.get("depth") == "old":
                    frame = apply_old_depth(frame, phase, float(shot.get("depth_amount", 1.5)), env_mask)
                    used_legacy.add("FX2-MOTION-001"); shot_used.add("FX2-MOTION-001")
                elif shot.get("depth") == "streaming":
                    frame = apply_streaming_depth(frame, phase, float(shot.get("depth_amount", .006)), env_mask)
                    used_legacy.add("FX2-SPATIAL-004"); shot_used.add("FX2-SPATIAL-004")

                # Canonical production-approved GodRender FX.
                if float(shot.get("fog", 0)) > 0:
                    candidate = fx.apply_frame("FX2-ATM-021", frame, ctx)
                    frame = blend(frame, candidate, env_mask, float(shot["fog"]))
                    used_approved.add("FX2-ATM-021"); shot_used.add("FX2-ATM-021")

                if float(shot.get("light", 0)) > 0:
                    candidate = fx.apply_frame(
                        "FX2-LIGHT-002", frame, ctx,
                        params={"origin": [.72, .16], "strength": float(shot["light"])}
                    )
                    frame = blend(frame, candidate, sky_mask, .95)
                    used_approved.add("FX2-LIGHT-002"); shot_used.add("FX2-LIGHT-002")

                if float(shot.get("grade", 0)) > 0:
                    candidate = fx.apply_frame("FX2-LIGHT-025", frame, ctx)
                    frame = blend(frame, candidate, env_mask, float(shot["grade"]))
                    used_approved.add("FX2-LIGHT-025"); shot_used.add("FX2-LIGHT-025")

                if bool(shot.get("camera")):
                    frame = fx.apply_frame(
                        "FX2-CAMERA-023", frame, ctx,
                        params={
                            "zoom_start": 1.0,
                            "zoom_end": float(shot.get("zoom_end", 1.008)),
                            "center_start": [.50, .50],
                            "center_end": [.503, .497],
                            "easing": "cosine",
                            "zoom_cap": 1.02,
                        },
                    )
                    used_approved.add("FX2-CAMERA-023"); shot_used.add("FX2-CAMERA-023")

                # Brain memory transition is deliberately sky/environment biased;
                # Observer geometry does not double-expose.
                if transition_n and nxt is not None and li >= nframes - transition_n:
                    p = (li - (nframes - transition_n)) / max(transition_n - 1, 1)
                    ghost = fx.apply_transition("FX2-TRANS-025", frame, nxt, p, ctx)
                    frame = blend(frame, ghost, env_mask, .84)
                    used_approved.add("FX2-TRANS-025"); shot_used.add("FX2-TRANS-025")

                proc.stdin.write(np.ascontiguousarray(frame).tobytes())
                global_frame += 1

            per_shot.append({
                "id": shot["id"],
                "frames": nframes,
                "source_sha256": shot["sha256"],
                "fx_ids": sorted(shot_used),
                "transition": shot.get("transition", "none"),
            })
    finally:
        proc.stdin.close()

    if proc.wait() != 0:
        raise RuntimeError("silent video encode failed")
    if global_frame != int(plan["total_frames"]):
        raise RuntimeError(f"rendered frame count {global_frame} != {plan['total_frames']}")

    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(silent), "-i", str(audio_path),
        "-t", "20.000", "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(final)
    ], check=True)

    probe = ffprobe(final)
    streams = probe.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    decoded = int(video_stream.get("nb_read_frames") or 0)
    if decoded != int(plan["total_frames"]):
        raise RuntimeError(f"decoded frame QC failed: {decoded}")
    duration = float(probe.get("format", {}).get("duration", 0))
    if abs(duration - 20.0) > .05:
        raise RuntimeError(f"duration QC failed: {duration}")

    impl_paths = {
        "FX2-ATM-005": REPO / "general/reusable/fx_v2/living_still_fx.py",
        "FX2-ATM-006": REPO / "general/reusable/fx_v2/living_still_fx.py",
        "FX2-MOTION-001": HYBRID_PATH,
        "FX2-SPATIAL-004": STREAMING_PATH,
        "approved_executor": REPO / "general/reusable/fx_v2/executor.py",
        "promoted_effects": REPO / "general/reusable/fx_v2/promoted_effects.py",
    }
    receipt = {
        "schema": "godrender.nordic-b01-brain-fx-receipt.v1",
        "project": plan["project"],
        "branch": plan["branch"],
        "git_sha": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "technical_state": "TECHNICAL_RENDER_PASS_VISUAL_REVIEW_PENDING",
        "director_authorization": {
            "scope": "Nordic B01",
            "legacy_proven_ids": [x["id"] for x in plan["director_authorized_proven_fx"]],
            "registry_globally_modified": False,
        },
        "source_media": {
            "still_count": len(shots),
            "all_ten_used": len(shots) == 10 and all(x["frames"] > 0 for x in shots),
            "master_audio_sha256": plan["audio_sha256"],
        },
        "timeline": {
            "fps": fps,
            "width": width,
            "height": height,
            "frames": global_frame,
            "duration_seconds": global_frame / fps,
            "frame_boundaries": plan["frame_boundaries"],
        },
        "used_legacy_direct_source_fx": sorted(used_legacy),
        "used_production_approved_fx": sorted(used_approved),
        "authorized_but_not_used": ["FX2-SPATIAL-001"],
        "hybrid_25d_not_used_reason": "unnecessary subject segmentation/inpainting risk on protected Observer plates",
        "streaming_living_parallax_depth_mode": "synthetic_radial_fallback_labeled",
        "implementation_sha256": {k: sha256_file(v) for k, v in impl_paths.items()},
        "render_plan_sha256": sha256_file(plan_path),
        "per_shot": per_shot,
        "output": {
            "file": final.name,
            "sha256": sha256_file(final),
            "bytes": final.stat().st_size,
            "ffprobe": probe,
        },
        "qc": {
            "decoded_frames": decoded,
            "expected_frames": int(plan["total_frames"]),
            "duration_seconds": duration,
            "exact_20s_frame_timeline": decoded == 480,
            "human_visual_approval": False,
        },
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    silent.unlink(missing_ok=True)
    return final, receipt_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, default=PLAN_DEFAULT)
    ap.add_argument("--input-root", type=Path, required=True)
    ap.add_argument("--audio", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    final, receipt = render(args.plan, args.input_root, args.audio, args.out)
    print(final)
    print(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
