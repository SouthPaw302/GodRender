#!/usr/bin/env python3
"""Leave It by the Door — V3 refinement renderer.

Consumes the accepted native-24 V2 *shot* renders as source plates, suppresses
high-frequency whole-frame wobble, then applies approved canonical FX V2
layers by scene family.  It does not use optical-flow interpolation and it
preserves native 24 fps cadence.

Typical use:
  python projects/leave-it-by-the-door/scripts/render_v3_refinement.py \
    --v2-dir /path/to/leaveit_native24_full/shots \
    --audio '/path/to/Leave it by the door. (Remastered) (1).wav' \
    --out-dir /path/to/leaveit_v3

The renderer fails closed unless V3_FX_LOCK.json verifies immediately before
render. Run the precompile gate first if the lock is stale.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

FPS = 24.0
SHOT_RE = re.compile(r"shot_(\d+)_([^.]*)\.mp4$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_runtime(root: Path):
    p = root / "general/reusable/fx_v2/runtime.py"
    spec = importlib.util.spec_from_file_location("aivideoedit_fx_v2", p)
    if not spec or not spec.loader:
        raise RuntimeError(f"Cannot load canonical FX runtime: {p}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def verify_fx_lock(root: Path, manifest: Path, lock: Path) -> None:
    gate = root / "general/reusable/fx_v2/precompile_gate.py"
    cmd = [sys.executable, str(gate), "--manifest", str(manifest), "--verify-lock", str(lock)]
    print("VERIFY FX LOCK", flush=True)
    subprocess.run(cmd, cwd=root, check=True)


def smoothstep(x: float) -> float:
    x = float(np.clip(x, 0.0, 1.0))
    return x * x * (3.0 - 2.0 * x)


def shot_kind(path: Path) -> tuple[int, str]:
    m = SHOT_RE.search(path.name)
    if not m:
        raise ValueError(f"Unexpected V2 shot filename: {path.name}")
    return int(m.group(1)), m.group(2)


def classify(kind: str) -> str:
    k = kind.lower()
    if any(x in k for x in ("dawn", "exit")):
        return "dawn"
    if any(x in k for x in ("dance", "celebration", "banjo", "fiddle", "community", "room_for_all")):
        return "celebration"
    if any(x in k for x in ("burden", "one_hand", "comfort", "breath", "coffee", "companions")):
        return "burden"
    if any(x in k for x in ("threshold", "arrival", "welcome")):
        return "storm"
    return "interior"


def family_effects(family: str):
    # ROIs are intentionally broad-but-localized defaults. V2 already contains
    # the song-specific composition; V3 adds motion without re-authoring faces.
    if family == "storm":
        return [
            {"id":"FX2-ATM-002","roi":[0.0,0.0,1.0,1.0],"strength":0.48},
            {"id":"FX2-ATM-001","roi":[0.0,0.0,1.0,0.74],"strength":0.45},
            {"id":"FX2-MOTION-003","roi":[0.42,0.56,1.0,1.0],"strength":0.54,"reflect":True},
            {"id":"FX2-LIGHT-002","strength":0.42,"origin":[0.78,0.18]},
            {"id":"FX2-SURFACE-001","strength":0.42,"key":"leaveit-v3-storm"},
        ]
    if family == "celebration":
        return [
            {"id":"FX2-MOTION-002","roi":[0.0,0.12,1.0,1.0],"strength":0.45},
            {"id":"FX2-FIRE-001","roi":[0.03,0.38,0.42,0.98],"strength":0.78},
            {"id":"FX2-FIRE-002","roi":[0.0,0.16,0.72,1.0],"strength":0.52},
            {"id":"FX2-LIGHT-001","roi":[0.0,0.0,1.0,1.0],"strength":0.70},
            {"id":"FX2-ATM-001","roi":[0.0,0.0,0.74,0.76],"strength":0.28},
            {"id":"FX2-SURFACE-001","strength":0.46,"key":"leaveit-v3-warm"},
        ]
    if family == "burden":
        return [
            {"id":"FX2-MOTION-002","roi":[0.0,0.16,1.0,1.0],"strength":0.28},
            {"id":"FX2-ATM-001","roi":[0.0,0.0,1.0,0.82],"strength":0.36},
            {"id":"FX2-FIRE-001","roi":[0.03,0.40,0.43,0.98],"strength":0.62},
            {"id":"FX2-FIRE-002","roi":[0.0,0.24,0.66,1.0],"strength":0.34},
            {"id":"FX2-LIGHT-001","strength":0.52},
            {"id":"FX2-SURFACE-001","strength":0.48,"key":"leaveit-v3-burden"},
        ]
    if family == "dawn":
        return [
            {"id":"FX2-MOTION-003","roi":[0.42,0.58,1.0,1.0],"strength":0.42,"reflect":True},
            {"id":"FX2-ATM-001","roi":[0.0,0.0,1.0,0.70],"strength":0.20},
            {"id":"FX2-LIGHT-002","strength":0.48,"origin":[0.78,0.16]},
            {"id":"FX2-SURFACE-001","strength":0.44,"key":"leaveit-v3-dawn"},
        ]
    return [
        {"id":"FX2-MOTION-002","roi":[0.0,0.18,1.0,1.0],"strength":0.30},
        {"id":"FX2-FIRE-001","roi":[0.03,0.40,0.43,0.98],"strength":0.68},
        {"id":"FX2-LIGHT-001","strength":0.58},
        {"id":"FX2-ATM-001","roi":[0.0,0.0,0.78,0.72],"strength":0.24},
        {"id":"FX2-SURFACE-001","strength":0.46,"key":"leaveit-v3-interior"},
    ]


def protect_mask(frame: np.ndarray) -> np.ndarray:
    """Conservative central identity protection for broad living-flow warps.

    V2's source paintings vary by shot, so this deliberately protects the
    center portrait/instrument zone rather than trying to hallucinate a face
    detector. Fire/rain/light layers are unaffected.
    """
    h, w = frame.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g1 = np.exp(-0.5 * (((xx-w*.48)/(w*.19))**2 + ((yy-h*.43)/(h*.30))**2))
    g2 = np.exp(-0.5 * (((xx-w*.68)/(w*.16))**2 + ((yy-h*.47)/(h*.28))**2))
    return np.clip(np.maximum(g1, g2) * .86, 0, 1).astype(np.float32)


class JitterReducer:
    """Damps only fast global translation; preserves slow intended travel."""
    def __init__(self, max_correction=2.2, alpha=.12):
        self.prev = None
        self.low = np.zeros(2, np.float32)
        self.max_correction = float(max_correction)
        self.alpha = float(alpha)

    def apply(self, frame: np.ndarray) -> np.ndarray:
        small = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (320,180), interpolation=cv2.INTER_AREA)
        small = small.astype(np.float32)
        if self.prev is None:
            self.prev = small
            return frame
        (dx,dy), response = cv2.phaseCorrelate(self.prev, small)
        self.prev = small
        if not np.isfinite(dx+dy) or response < .08:
            return frame
        delta = np.array([dx*frame.shape[1]/320.0, dy*frame.shape[0]/180.0], np.float32)
        delta = np.clip(delta, -6.0, 6.0)
        self.low = (1.0-self.alpha)*self.low + self.alpha*delta
        correction = np.clip(self.low-delta, -self.max_correction, self.max_correction)
        M = np.float32([[1,0,correction[0]],[0,1,correction[1]]])
        return cv2.warpAffine(frame, M, (frame.shape[1],frame.shape[0]), flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REFLECT_101)


def title_card(base: np.ndarray, text: str, sub: str, t: float, dur: float) -> np.ndarray:
    h,w=base.shape[:2]
    blur=cv2.GaussianBlur(base,(0,0),2.2)
    veil=np.zeros_like(blur)
    out=cv2.addWeighted(blur,.72,veil,.28,0)
    a=smoothstep(min(t/.8,(dur-t)/.8))
    font=cv2.FONT_HERSHEY_DUPLEX
    scale=max(.7,w/1280*1.22)
    th=max(1,round(w/1280*2))
    (tw,tht),_=cv2.getTextSize(text,font,scale,th)
    cv2.putText(out,text,((w-tw)//2,int(h*.48)),font,scale,(int(232*a),int(235*a),int(238*a)),th,cv2.LINE_AA)
    if sub:
        s2=scale*.48; (sw,_),_=cv2.getTextSize(sub,font,s2,1)
        cv2.putText(out,sub,((w-sw)//2,int(h*.56)),font,s2,(int(188*a),int(193*a),int(199*a)),1,cv2.LINE_AA)
    return out


def encode_shot(src: Path, dst: Path, runtime, fxmod, family: str) -> tuple[int, tuple[int,int]]:
    cap=cv2.VideoCapture(str(src))
    fps=cap.get(cv2.CAP_PROP_FPS)
    if abs(fps-FPS)>.05:
        raise RuntimeError(f"{src.name}: expected native 24 fps, got {fps}")
    count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if count < 1 or w < 1 or h < 1:
        raise RuntimeError(f"Unreadable source shot: {src}")
    dst.parent.mkdir(parents=True,exist_ok=True)
    cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-f","rawvideo","-pix_fmt","bgr24","-s",f"{w}x{h}","-r","24","-i","-","-an","-c:v","libx264","-preset","fast","-crf","16","-pix_fmt","yuv420p","-movflags","+faststart",str(dst)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    reducer=JitterReducer(); protect=None
    effects=family_effects(family)
    for n in range(count):
        ok,fr=cap.read()
        if not ok: raise RuntimeError(f"Early EOF {src.name} at frame {n}/{count}")
        if protect is None: protect=protect_mask(fr)
        fr=reducer.apply(fr)
        ctx=fxmod.FXContext(t=n/FPS,duration=count/FPS,frame_index=n,fps=FPS,energy=.35+.15*math.sin(n/FPS*.71),transient=.08)
        for eff in effects:
            fr=runtime.apply(fr,eff,ctx,protect=protect if eff["id"]=="FX2-MOTION-002" else None)
        proc.stdin.write(fr.tobytes())
    cap.release(); proc.stdin.close(); rc=proc.wait()
    if rc: raise RuntimeError(f"ffmpeg failed for {src.name}: {rc}")
    return count,(w,h)


def make_card_from_frame(frame: np.ndarray, out: Path, seconds: float, title: str, sub: str, runtime, fxmod, family="dawn"):
    h,w=frame.shape[:2]; frames=round(seconds*FPS)
    cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-f","rawvideo","-pix_fmt","bgr24","-s",f"{w}x{h}","-r","24","-i","-","-an","-c:v","libx264","-preset","fast","-crf","16","-pix_fmt","yuv420p",str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for n in range(frames):
        ctx=fxmod.FXContext(t=n/FPS,duration=seconds,frame_index=n,fps=FPS,energy=.22,transient=0)
        fr=frame.copy()
        for eff in family_effects(family):
            if eff["id"] in ("FX2-LIGHT-002","FX2-ATM-001","FX2-SURFACE-001","FX2-MOTION-003"):
                fr=runtime.apply(fr,eff,ctx)
        fr=title_card(fr,title,sub,n/FPS,seconds)
        proc.stdin.write(fr.tobytes())
    proc.stdin.close(); rc=proc.wait()
    if rc: raise RuntimeError("title card encode failed")


def read_edge_frame(path: Path, last=False) -> np.ndarray:
    cap=cv2.VideoCapture(str(path))
    if last:
        n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.set(cv2.CAP_PROP_POS_FRAMES,max(0,n-1))
    ok,fr=cap.read(); cap.release()
    if not ok: raise RuntimeError(f"Cannot read edge frame: {path}")
    return fr


def main():
    root=repo_root(); project=root/"projects/leave-it-by-the-door"
    ap=argparse.ArgumentParser()
    ap.add_argument("--v2-dir",type=Path,required=True,help="accepted V2 shot directory")
    ap.add_argument("--audio",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    ap.add_argument("--manifest",type=Path,default=project/"V3_FX_MANIFEST.json")
    ap.add_argument("--lock",type=Path,default=project/"V3_FX_LOCK.json")
    ap.add_argument("--intro",type=float,default=4.0)
    ap.add_argument("--outro",type=float,default=6.0)
    args=ap.parse_args()

    verify_fx_lock(root,args.manifest,args.lock)
    fxmod=load_runtime(root); runtime=fxmod.FXRuntime(seed=302)
    shots=sorted(args.v2_dir.glob("shot_*.mp4"),key=lambda p: shot_kind(p)[0])
    if len(shots)!=25:
        raise RuntimeError(f"Expected 25 accepted V2 shots, found {len(shots)} in {args.v2_dir}")
    args.out_dir.mkdir(parents=True,exist_ok=True); shot_out=args.out_dir/"shots"; shot_out.mkdir(exist_ok=True)
    report={"fps":24,"source":"accepted-native24-v2-shots","shots":[],"started":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    for src in shots:
        sid,kind=shot_kind(src); family=classify(kind); dst=shot_out/f"shot_{sid:02d}_{kind}_v3.mp4"
        t0=time.time(); count,size=encode_shot(src,dst,runtime,fxmod,family)
        report["shots"].append({"id":sid,"kind":kind,"family":family,"frames":count,"size":size,"file":dst.name})
        print(f"DONE {sid:02d} {kind} family={family} frames={count} sec={time.time()-t0:.1f}",flush=True)

    first=read_edge_frame(shot_out/report["shots"][0]["file"])
    last=read_edge_frame(shot_out/report["shots"][-1]["file"],last=True)
    intro=args.out_dir/"00_intro.mp4"; outro=args.out_dir/"99_outro.mp4"
    make_card_from_frame(first,intro,args.intro,"LEAVE IT BY THE DOOR","Mountainnoir",runtime,fxmod,"storm")
    make_card_from_frame(last,outro,args.outro,"MOUNTAINNOIR","Thanks for watching",runtime,fxmod,"dawn")

    # Artistic master: song only, no pre-roll; preserve source audio runtime.
    concat_art=args.out_dir/"concat_artistic.txt"
    concat_art.write_text("\n".join([f"file '{(shot_out/s['file']).as_posix()}'" for s in report["shots"]])+"\n")
    silent_art=args.out_dir/"Leave_It_By_The_Door_V3_ARTISTIC_silent.mp4"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(concat_art),"-c","copy",str(silent_art)],check=True)
    artistic=args.out_dir/"Leave_It_By_The_Door_V3_ARTISTIC_720p24.mp4"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(silent_art),"-i",str(args.audio),"-map","0:v:0","-map","1:a:0","-shortest","-c:v","copy","-c:a","aac","-b:a","320k","-ar","48000","-movflags","+faststart",str(artistic)],check=True)

    # YouTube master: 4 s pre-roll + song + 6 s post-roll. Delay song audio by intro.
    concat_yt=args.out_dir/"concat_youtube.txt"
    concat_yt.write_text("\n".join([f"file '{intro.as_posix()}'"]+[f"file '{(shot_out/s['file']).as_posix()}'" for s in report["shots"]]+[f"file '{outro.as_posix()}'"])+"\n")
    silent_yt=args.out_dir/"Leave_It_By_The_Door_V3_YOUTUBE_silent.mp4"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(concat_yt),"-c","copy",str(silent_yt)],check=True)
    youtube=args.out_dir/"Leave_It_By_The_Door_V3_YOUTUBE_720p24.mp4"
    delay=round(args.intro*1000)
    filt=f"[1:a]adelay={delay}|{delay}[a]"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(silent_yt),"-i",str(args.audio),"-filter_complex",filt,"-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","320k","-ar","48000","-movflags","+faststart",str(youtube)],check=True)

    report.update({"artistic_master":artistic.name,"youtube_master":youtube.name,"intro_seconds":args.intro,"outro_seconds":args.outro,"finished":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
    (args.out_dir/"V3_RENDER_REPORT.json").write_text(json.dumps(report,indent=2)+"\n")
    print("ARTISTIC",artistic,flush=True); print("YOUTUBE",youtube,flush=True)

if __name__=="__main__":
    main()
