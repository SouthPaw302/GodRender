#!/usr/bin/env python3
"""Recover the accepted 25 native-24 V2 shot plates from the final V2 master.

The original V2 was stream-concatenated from 25 H.264 shot masters. Some
handoffs retained only the final master. This utility detects the 24 original
visual joins from adjacent-frame discontinuity, validates the recovered map,
and decodes the master once into 25 frame-accurate CRF16 H.264 plates.

This is a recovery/preparation step only. It does not interpolate frames or
invent new picture motion.
"""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path
import cv2
import numpy as np

FPS=24.0
EXPECTED_FRAMES=4772
EXPECTED_SHOTS=25
EXPECTED_DURATION=198.83333333333334

# Canonical recovery map derived from the accepted V2 master. These are frame
# indices at which the new source shot begins. Keeping the map here avoids
# re-running scene detection on every sandbox restore.
CANONICAL_CUT_FRAMES=[
    153,305,478,645,813,906,1162,1385,1608,1840,2039,2269,
    2518,2762,2947,3127,3291,3480,3660,3876,4107,4328,4438,4649,
]


def inspect(path:Path):
    cap=cv2.VideoCapture(str(path))
    fps=float(cap.get(cv2.CAP_PROP_FPS)); n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release(); return fps,n,w,h


def detect(path:Path,ncuts=24,min_sep=42):
    cap=cv2.VideoCapture(str(path)); n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    prev=None; scores=[]
    for _ in range(n):
        ok,f=cap.read()
        if not ok: break
        g=cv2.cvtColor(cv2.resize(f,(160,90),interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2GRAY).astype(np.float32)
        scores.append(0.0 if prev is None else float(np.mean(np.abs(g-prev)))); prev=g
    cap.release(); a=np.asarray(scores,np.float32); chosen=[]
    for fr in np.argsort(a)[::-1]:
        fr=int(fr)
        if fr<36 or fr>n-36: continue
        if all(abs(fr-x)>min_sep for x in chosen):
            chosen.append(fr)
            if len(chosen)==ncuts: break
    chosen.sort()
    return chosen,a


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('master',type=Path)
    ap.add_argument('out_dir',type=Path)
    ap.add_argument('--redetect',action='store_true',help='measure joins instead of using canonical map')
    args=ap.parse_args()
    fps,n,w,h=inspect(args.master)
    if abs(fps-FPS)>.01 or n!=EXPECTED_FRAMES:
        raise SystemExit(f'Not the accepted V2 master: fps={fps} frames={n}; expected 24/{EXPECTED_FRAMES}')
    cuts=CANONICAL_CUT_FRAMES
    scores=None
    if args.redetect:
        cuts,scores=detect(args.master)
        if cuts!=CANONICAL_CUT_FRAMES:
            raise SystemExit(f'Redetected cut map differs from canonical map:\n{cuts}')
    bounds=[0]+cuts+[n]
    if len(bounds)-1!=EXPECTED_SHOTS: raise SystemExit('shot-count recovery failure')
    args.out_dir.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(str(args.master))
    proc=None; current=-1; shot_start=0; shot_frames=[]
    try:
        for i in range(n):
            if current+1 < EXPECTED_SHOTS and i==bounds[current+1] if current>=0 else i==0:
                if proc is not None:
                    proc.stdin.close(); rc=proc.wait()
                    if rc: raise RuntimeError(f'ffmpeg shot {current+1} failed: {rc}')
                    shot_frames.append(i-shot_start)
                current+=1; shot_start=i
                out=args.out_dir/f'shot_{current+1:02d}_recovered.mp4'
                cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{w}x{h}','-r','24','-i','-','-an','-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
                proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
            ok,fr=cap.read()
            if not ok: raise RuntimeError(f'early EOF at frame {i}')
            proc.stdin.write(fr.tobytes())
        proc.stdin.close(); rc=proc.wait(); proc=None
        if rc: raise RuntimeError(f'ffmpeg shot {current+1} failed: {rc}')
        shot_frames.append(n-shot_start)
    finally:
        cap.release()
        if proc is not None:
            try: proc.stdin.close(); proc.wait(timeout=10)
            except Exception: proc.kill()
    report={
        'source':args.master.name,'fps':fps,'frames':n,'resolution':[w,h],
        'cut_frames':cuts,'cut_seconds':[round(x/FPS,6) for x in cuts],
        'shot_frame_counts':shot_frames,'shot_count':len(shot_frames),
        'total_recovered_frames':sum(shot_frames),
    }
    (args.out_dir/'RECOVERY_MAP.json').write_text(json.dumps(report,indent=2)+'\n')
    if report['shot_count']!=25 or report['total_recovered_frames']!=n:
        raise RuntimeError('recovered plate validation failed')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
