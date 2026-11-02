#!/usr/bin/env python3
"""GodRender authenticated-source shot renderer and parallel assembly.
Technical workprints are NEVER human-approved masters.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT  # GodRender source root is sole executable FX authority
sys.path.insert(0, str(CANONICAL))
SCHEMA = "godrender.production.v1"

def current_godrender_commit():
    """Bind processing receipts to exact native GodRender execution source."""
    result=subprocess.run(["git","-C",str(ROOT),"rev-parse","HEAD"],
                          capture_output=True,text=True,timeout=10,check=False)
    sha=result.stdout.strip()
    if result.returncode != 0 or len(sha)!=40 or any(c not in "0123456789abcdef" for c in sha):
        raise RuntimeError("cannot attest GodRender source revision")
    return sha

def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()

def within(root, relative):
    root = Path(root).resolve()
    p = (root / str(relative)).resolve()
    if p == root or root not in p.parents or p.is_symlink():
        raise ValueError("path outside authorized input root")
    return p

def manifest_load(path, input_root):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError("unknown manifest schema")
    fps, w, h = int(data.get("fps", 0)), int(data.get("width", 0)), int(data.get("height", 0))
    if fps < 1 or fps > 60 or w < 32 or h < 32 or w > 1920 or h > 1080:
        raise ValueError("unsupported film dimensions/fps")
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots or len(shots) > 150:
        raise ValueError("film requires 1..150 shots")
    seen = set()
    for shot in shots:
        name = str(shot.get("id") or "")
        if not name or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in name) or name in seen:
            raise ValueError("unsafe or duplicate shot id")
        seen.add(name)
        if not 0.3 <= float(shot.get("seconds", 0)) <= 30.0:
            raise ValueError("individual shot must be 0.3..30 seconds")
        if shot.get("mode") not in {"still_fx", "video_fx", "godot"}:
            raise ValueError("unsupported shot mode; never silently substitute renderer")
        if shot["mode"] in {"still_fx", "video_fx"}:
            key = "image" if shot["mode"] == "still_fx" else "video"
            media = shot.get(key) or {}
            path = within(input_root, media.get("path", ""))
            if not path.is_file() or len(str(media.get("sha256", ""))) != 64 or sha256(path) != media["sha256"]:
                raise ValueError("missing or hash-mismatched source for " + name)
        if shot["mode"] == "godot":
            scene = str(shot.get("scene", ""))
            valid = ("upstream/mainv2-lab/lab/godot/scenes/proof_2d.tscn",
                     "upstream/mainv2-lab/lab/godot/scenes/proof_3d.tscn")
            if scene not in valid:
                raise ValueError("Godot scene must be a vetted local project scene")
        normalized_fx(shot)
        if "base_camera" in shot and not isinstance(shot.get("base_camera"), bool):
            raise ValueError("base_camera must be boolean")
    if data.get("audio"):
        rec = data["audio"]
        path = within(input_root, rec.get("path", ""))
        if not path.is_file() or sha256(path) != rec.get("sha256"):
            raise ValueError("music source hash mismatch")
    return data

def normalized_fx(shot):
    """Return validated structured FX entries while preserving fx_ids compatibility."""
    legacy = shot.get("fx_ids", [])
    structured = shot.get("fx")
    if structured is None:
        if not isinstance(legacy, list) or len(legacy) > 12 or not all(isinstance(x, str) for x in legacy):
            raise ValueError("invalid FX list")
        return [{"id": eid, "params": {}} for eid in legacy]
    if not isinstance(structured, list) or len(structured) > 12:
        raise ValueError("invalid structured FX list")
    out = []
    for raw in structured:
        if isinstance(raw, str):
            raw = {"id": raw}
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), str) or not raw["id"]:
            raise ValueError("invalid structured FX entry")
        params = raw.get("params", {})
        if not isinstance(params, dict):
            raise ValueError("FX params must be an object")
        out.append({"id": raw["id"], "params": params})
    if legacy:
        if not isinstance(legacy, list) or not all(isinstance(x, str) for x in legacy):
            raise ValueError("invalid FX list")
        if legacy != [item["id"] for item in out]:
            raise ValueError("fx_ids and structured fx disagree")
    return out

def check_fx(effects):
    from general.reusable.fx_v2.executor import FXExecutor
    fx = FXExecutor(consumer="godrender_parallel_shot")
    for item in effects:
        eid = item["id"]
        rec = fx._rec(eid)  # approved gate; refuses missing/unpromoted registry entry
        if (rec.get("implementation") or {}).get("kind") == "runtime_transition":
            raise ValueError("transition FX cannot run as per-frame FX: " + eid)
    return fx

def render_one(data, shot, input_root, out):
    import cv2
    import numpy as np
    from general.reusable.fx_v2.runtime import FXContext
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fps, width, height = int(data["fps"]), int(data["width"]), int(data["height"])
    total = max(1, round(float(shot["seconds"]) * fps))
    effects = normalized_fx(shot)
    fx = check_fx(effects)
    mode = shot["mode"]
    capture = None
    temp_godot = None
    if mode == "still_fx":
        src = within(input_root, shot["image"]["path"])
        source = cv2.imread(str(src), cv2.IMREAD_COLOR)
        if source is None:
            raise RuntimeError("cannot decode input still image")
    elif mode == "video_fx":
        src = within(input_root, shot["video"]["path"])
        capture = cv2.VideoCapture(str(src))
        if not capture.isOpened():
            raise RuntimeError("cannot decode source video")
        source = None
    else:
        if not shutil.which("godot"):
            raise RuntimeError("Godot headless binary is absent; refusing silent still fallback")
        import tempfile
        temp_godot = tempfile.TemporaryDirectory()
        scene = ROOT / shot["scene"]
        project = scene.parents[1]
        target = Path(temp_godot.name) / "godot.avi"
        cmd = ["godot", "--headless", "--path", str(project), "--write-movie", str(target),
               "--fixed-fps", str(fps), "--quit-after", str(total), str(scene)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)
        if result.returncode or not target.is_file():
            raise RuntimeError("Godot movie render failed: " + (result.stderr or result.stdout)[-1300:])
        capture = cv2.VideoCapture(str(target))
        if not capture.isOpened():
            raise RuntimeError("Godot produced unreadable movie")
        source = None
    result_path = out / f"{shot['id']}.mp4"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{height}",
           "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264",
           "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(result_path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    nonidentical = 0
    first_frame = None
    try:
        for i in range(total):
            if capture:
                read_ok, frame = capture.read()
                if not read_ok:
                    raise RuntimeError(f"missing input frame {i}/{total} from {mode}")
            else:
                frame = source.copy()
                # Legacy bounded camera movement remains the compatibility default.
                # Production shots may disable it when explicit approved camera FX are authored.
                if bool(shot.get("base_camera", True)):
                    zoom = 1.015 + 0.013 * math.sin(i / max(total, 1) * math.pi)
                    tx = 1.5 * math.sin(2 * math.pi * i / max(total, 1))
                    ty = 1.0 * math.cos(2 * math.pi * i / max(total, 1))
                    M = np.float32([[zoom, 0, tx - frame.shape[1] * (zoom - 1) / 2],
                                    [0, zoom, ty - frame.shape[0] * (zoom - 1) / 2]])
                    frame = cv2.warpAffine(frame, M, (frame.shape[1], frame.shape[0]),
                                           flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT101)
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
            ctx = FXContext(t=i/fps, duration=total/fps, frame_index=i, fps=fps,
                            energy=float(shot.get("energy", .45)), transient=float(shot.get("transient", .2)))
            for effect in effects:
                frame = fx.apply_frame(effect["id"], frame, ctx, params=effect.get("params") or {})
            if not isinstance(frame, np.ndarray) or frame.shape != (height,width,3):
                raise RuntimeError("FX returned invalid picture shape")
            if first_frame is None:
                first_frame = frame.copy()
            elif np.mean(cv2.absdiff(first_frame, frame)) > 0.25:
                nonidentical += 1
            p.stdin.write(frame.astype("uint8").tobytes())
        p.stdin.close()
        error = p.stderr.read().decode("utf-8", "replace")
        if p.wait(timeout=90) or not result_path.is_file():
            raise RuntimeError("ffmpeg encoding failed: " + error[-900:])
    except Exception:
        if p.stdin and not p.stdin.closed:
            p.stdin.close()
        p.kill()
        p.wait()
        raise
    finally:
        if capture:
            capture.release()
        if temp_godot:
            temp_godot.cleanup()
    if total > 4 and nonidentical == 0:
        raise RuntimeError("shot frames are static: moving-scene requirement failed")
    receipt = {"schema":"godrender.shot-receipt.v1","status":"TECHNICAL_RENDER_PASS_VISUAL_REVIEW_PENDING",
               "human_approval":False,"shot":shot["id"],"mode":mode,"frames":total,
               "nonidentical_frames":nonidentical,"fx_executed":[e["id"] for e in effects],
               "fx_parameters":effects,
               "base_camera":bool(shot.get("base_camera", True)),
               "video":result_path.name,"video_sha256":sha256(result_path),
               "source_sha256":(shot.get("image") or shot.get("video") or {}).get("sha256"),
               "source_main_sha":current_godrender_commit()}
    (out/f"{shot['id']}.receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    return receipt

def plan(data, output):
    chunks=[{"shot_id":shot["id"],"index":i} for i,shot in enumerate(data["shots"])]
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(json.dumps({"include":chunks},sort_keys=True)+"\n")
    return {"include":chunks}

def assemble(data, input_root, shards, target):
    shards=Path(shards); target=Path(target);target.mkdir(parents=True,exist_ok=True)
    concat=target/"concat.txt"
    lines=[]
    checked=[]
    for shot in data["shots"]:
        name=shot["id"]
        video=shards/name/(name+".mp4")
        receipt_path=shards/name/(name+".receipt.json")
        if not video.is_file() or not receipt_path.is_file():
            raise RuntimeError("missing verified shard "+name)
        rec=json.loads(receipt_path.read_text())
        if rec.get("status")!="TECHNICAL_RENDER_PASS_VISUAL_REVIEW_PENDING" or rec.get("human_approval") is not False or sha256(video)!=rec.get("video_sha256"):
            raise RuntimeError("unverified or creative-claimed shard "+name)
        lines.append("file '"+str(video.resolve()).replace("'","'\\''")+"'")
        checked.append(rec)
    concat.write_text("\n".join(lines)+"\n")
    output=target/"godrender_review.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
         "-f","concat","-safe","0","-i",str(concat)]
    if data.get("audio"):
        cmd += ["-i",str(within(input_root,data["audio"]["path"])),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-shortest"]
    else:
        cmd += ["-c:v","copy","-an"]
    cmd += ["-movflags","+faststart",str(output)]
    proc=subprocess.run(cmd,capture_output=True,text=True,timeout=120,check=False)
    if proc.returncode or not output.is_file() or output.stat().st_size < 1024:
        raise RuntimeError("film assembly failed: "+proc.stderr[-1200:])
    receipt={"schema":"godrender.film-receipt.v1","status":"TECHNICAL_RENDER_PASS_VISUAL_REVIEW_PENDING",
             "production_complete":False,"human_visual_approval":False,"source_type":"pinned_manifest",
             "sha256":sha256(output),"bytes":output.stat().st_size,
             "frames_expected":sum(r["frames"] for r in checked),
             "shards":checked,"audio_sha256":data.get("audio",{}).get("sha256")}
    (target/"render_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    (target/"BRAIN_OUTBOX.json").write_text(json.dumps({"schema":"godrender.brain-proof.v1","film_receipt":receipt,"publication":"PENDING_VERIFIED_DRIVE_CREDENTIALS"},indent=2)+"\n")
    return receipt

def fixture(root,manifest):
    """Produces synthetic *technical* media; never promote as actual song assets."""
    import cv2
    import numpy as np
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    image=np.zeros((360,640,3),dtype=np.uint8)
    for y in range(360):
        image[y,:,:]=[min(255,40+y//3),min(255,60+y//4),min(255,85+y//6)]
    cv2.circle(image,(430,90),40,(95,185,240),-1)
    cv2.rectangle(image,(100,180),(330,320),(30,115,75),-1)
    shot=root/"scene.png"
    cv2.imwrite(str(shot),image)
    audio=root/"music.wav"; rate=22050
    import struct
    with wave.open(str(audio),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate)
        f.writeframes(b"".join(struct.pack("<h",int(12000*math.sin(2*math.pi*220*i/rate))) for i in range(rate*4)))
    data={"schema":SCHEMA,"fps":24,"width":640,"height":360,
          "audio":{"path":audio.name,"sha256":sha256(audio)},
          "shots":[{"id":"s01","seconds":2,"mode":"still_fx","image":{"path":shot.name,"sha256":sha256(shot)},"fx_ids":["FX2-ATM-001"]},
                   {"id":"s02","seconds":2,"mode":"still_fx","image":{"path":shot.name,"sha256":sha256(shot)},"fx_ids":["FX2-LIGHT-001"]}],
          "human_visual_approval":False}
    Path(manifest).write_text(json.dumps(data,indent=2)+"\n")
    return data

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="command",required=True)
    f=sub.add_parser("fixture"); f.add_argument("--root",required=True);f.add_argument("--manifest",required=True)
    for name in ("plan","shot","assemble"):
        a=sub.add_parser(name);a.add_argument("--manifest",required=True);a.add_argument("--input-root",required=True)
        if name=="plan":a.add_argument("--output",required=True)
        if name=="shot":a.add_argument("--shot-id",required=True);a.add_argument("--out",required=True)
        if name=="assemble":a.add_argument("--shards",required=True);a.add_argument("--out",required=True)
    a=p.parse_args()
    if a.command=="fixture":
        result=fixture(a.root,a.manifest)
    else:
        d=manifest_load(a.manifest,a.input_root)
        if a.command=="plan":result=plan(d,a.output)
        elif a.command=="shot":
            shot=next((x for x in d["shots"] if x["id"]==a.shot_id),None)
            if shot is None:raise ValueError("unknown shot id")
            result=render_one(d,shot,a.input_root,a.out)
        else:result=assemble(d,a.input_root,a.shards,a.out)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
