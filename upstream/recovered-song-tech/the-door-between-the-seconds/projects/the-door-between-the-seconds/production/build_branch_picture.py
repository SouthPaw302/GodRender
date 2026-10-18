#!/usr/bin/env python3
from __future__ import annotations

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

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SCRIPT_PATH = ROOT / "production" / "v3_snapshot_inputs" / "SCRIPT.json"
BANK = ROOT / "production" / "generated_scene_bank"
OUT = ROOT / "production" / "branch_render"
OUT.mkdir(parents=True, exist_ok=True)
FX_MANIFEST = ROOT / "FX_REQUIREMENTS.fx.json"
FX_LOCK = ROOT / "fx.lock.json"
FX_GATE = REPO / "general" / "reusable" / "fx_v2" / "precompile_gate.py"
FX_RUNTIME_PATH = REPO / "general" / "reusable" / "fx_v2" / "runtime.py"

W, H, FPS = 960, 540, 30
SCRIPT = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
TOTAL = int(SCRIPT["total_frames"])
ENTRIES = SCRIPT["entries"]
assert TOTAL == 5074
assert len(ENTRIES) == 34

# No production pixels are emitted unless the current lock verifies against
# this renderer and its declared inputs.
subprocess.run([
    sys.executable, str(FX_GATE), "--manifest", str(FX_MANIFEST),
    "--verify-lock", str(FX_LOCK)
], check=True)

spec = importlib.util.spec_from_file_location("door_fx_runtime", FX_RUNTIME_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load FX runtime")
fxmod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fxmod
spec.loader.exec_module(fxmod)
FX = fxmod.FXRuntime(seed=302)
FXContext = fxmod.FXContext


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_source(entry):
    if entry["shot_id"] == "S00":
        p = BANK / "gothic_vampiric_reverie_by_moonlit_window.jpg"
    else:
        p = BANK / entry["visual_media"]
    im = cv2.imread(str(p), cv2.IMREAD_COLOR)
    if im is None:
        raise FileNotFoundError(p)
    if im.shape[1] != W or im.shape[0] != H:
        im = cv2.resize(im, (W, H), interpolation=cv2.INTER_LANCZOS4)
    return im, p


def vignette(im, amount=.16):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x = (xx-W/2)/(W/2); y=(yy-H/2)/(H/2)
    m=np.clip(1-amount*(x*x+y*y),.62,1)[...,None]
    return np.clip(im.astype(np.float32)*m,0,255).astype(np.uint8)


def profile_composite(base, profile, q):
    out=base.copy()
    if profile in {"reflection_echo","rain_reflection"}:
        flip=cv2.flip(base,1)
        split=int(W*(.50+.035*math.sin(q*math.tau)))
        out[:,split:]=cv2.addWeighted(base[:,split:],.72,flip[:,split:],.28,0)
        cv2.line(out,(split,0),(split,H),(104,88,99),1,cv2.LINE_AA)
    elif profile in {"temporal_echo","portrait_echo","reach_echo"}:
        a=cv2.warpAffine(base,np.float32([[1,0,-28],[0,1,0]]),(W,H),borderMode=cv2.BORDER_REFLECT_101)
        b=cv2.warpAffine(cv2.flip(base,1),np.float32([[1,0,31],[0,1,0]]),(W,H),borderMode=cv2.BORDER_REFLECT_101)
        out=np.clip(base.astype(np.float32)*.68+a.astype(np.float32)*.18+b.astype(np.float32)*.14,0,255).astype(np.uint8)
    elif profile=="mirror_corridor":
        sw=W//9
        l=cv2.flip(base[:,:sw],1); r=cv2.flip(base[:,-sw:],1)
        out[:,:sw]=cv2.addWeighted(base[:,:sw],.67,l,.33,0)
        out[:,-sw:]=cv2.addWeighted(base[:,-sw:],.67,r,.33,0)
    elif profile=="hallway_repeat":
        for k,sc in enumerate((.82,.63,.47),1):
            nw,nh=int(W*sc),int(H*sc); small=cv2.resize(base,(nw,nh),interpolation=cv2.INTER_AREA)
            x=(W-nw)//2; y=(H-nh)//2; alpha=.19/(k**.45)
            out[y:y+nh,x:x+nw]=cv2.addWeighted(out[y:y+nh,x:x+nw],1-alpha,small,alpha,0)
    elif profile in {"depth_gate","cathedral_push","cathedral_impact"}:
        sc=.70+.10*math.sin(q*math.pi)
        nw,nh=int(W*sc),int(H*sc)
        mid=cv2.resize(base,(nw,nh),interpolation=cv2.INTER_AREA)
        x=(W-nw)//2; y=(H-nh)//2
        out[y:y+nh,x:x+nw]=cv2.addWeighted(out[y:y+nh,x:x+nw],.42,mid,.58,0)
    return vignette(out,.13)


def camera(im,q,profile,energy,transient):
    wide={"cathedral_push","cathedral_impact","depth_gate","dawn_bloom","crypt_dawn","silent_light","mirror_corridor","hallway_repeat"}
    portrait={"portrait_echo","vampire_portrait","shadow_breath","soft_contact"}
    zoom=1.018+(0.026 if profile in wide else 0.015)*math.sin(q*math.pi)**2
    if profile in portrait: zoom=1.013+.011*math.sin(q*math.pi)**2
    zoom += .007*energy
    dx=10*math.sin(q*math.tau+0.4)
    dy=4*math.sin(q*math.tau*.73+1.2)
    angle=.28*math.sin(q*math.tau)
    if profile=="reverse_drift": dx=20*(q-.5)
    if profile in {"cathedral_impact","departure_drive","rain_push","doorway_drift"}:
        dx += 3.2*transient*math.sin(q*math.pi*8+.6)
        dy += 2.1*transient*math.sin(q*math.pi*9.5+1.1)
        angle += .45*transient*math.sin(q*math.pi*7)
    if profile=="gravity_flip":
        angle=12*math.sin(q*math.pi)
        if .47<q<.59: im=cv2.flip(im,-1)
    if profile in {"final_stillness","silent_light"}:
        fade=max(.08,1-q*.88); dx*=fade; dy*=fade; angle*=fade
    M=cv2.getRotationMatrix2D((W/2,H/2),angle,zoom)
    M[0,2]+=dx; M[1,2]+=dy
    return cv2.warpAffine(im,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)


def authored_energy(global_frame,local_frame,local_len,profile):
    # Visual pacing proxy only. The true soundtrack remains a later mux input.
    q=local_frame/max(1,local_len-1)
    base=.28+.24*(.5+.5*math.sin(global_frame*.071+1.3))+ .15*math.sin(q*math.pi)
    if profile in {"cathedral_impact","departure_drive","quiet_thunder"}: base+=.20
    if profile in {"final_stillness","silent_light"}: base*=max(.22,1-q*.70)
    energy=float(np.clip(base,0,1))
    pulse=(global_frame%24)/24.0
    transient=float(max(0,1-abs(pulse-.05)*13))*min(1,energy*1.25)
    return energy,transient


def canonical_fx(fr,profile,t,duration,frame_index,energy,transient):
    ctx=FXContext(t=t,duration=duration,frame_index=frame_index,fps=FPS,energy=energy,transient=transient,brightness=float(fr.mean()/255.0))
    fr=FX.apply(fr,{"id":"FX2-MOTION-002","strength":.42,"roi":[.02,.02,.98,.98]},ctx)
    fr=FX.apply(fr,{"id":"FX2-LIGHT-001","strength":.75,"roi":[0,0,1,1]},ctx)
    if profile in {"rain_push","rain_reflection","doorway_drift","soft_contact"}:
        fr=FX.apply(fr,{"id":"FX2-ATM-002","strength":.40,"roi":[0,0,1,1]},ctx)
    elif profile in {"dust_memory","mirror_corridor","hallway_repeat","crypt_memory","crypt_dawn","final_stillness"}:
        fr=FX.apply(fr,{"id":"FX2-ATM-001","strength":.32,"roi":[0,0,1,1]},ctx)
    elif profile in {"ember_bloom","cathedral_push","cathedral_impact","vampire_portrait"}:
        fr=FX.apply(fr,{"id":"FX2-FIRE-002","strength":.38,"roi":[0,0,1,1]},ctx)
    elif profile in {"dawn_bloom","silent_light"}:
        fr=FX.apply(fr,{"id":"FX2-LIGHT-002","strength":.80,"origin":[.80,.14],"roi":[0,0,1,1]},ctx)
    return fr


def cold_open_title(fr, local_frame):
    # 6-second silent image lead. Text fades in, holds, then leaves before song frame 180.
    if local_frame<15 or local_frame>160:
        return fr
    a=min(1.0,(local_frame-15)/22.0,(160-local_frame)/22.0)
    text="OLD WORLDS DECAY, NEW ONES RISE."
    font=cv2.FONT_HERSHEY_DUPLEX; scale=.82; thick=1
    (tw,th),_=cv2.getTextSize(text,font,scale,thick)
    x=(W-tw)//2; y=int(H*.82)
    overlay=fr.copy()
    cv2.putText(overlay,text,(x,y),font,scale,(218,214,211),thick,cv2.LINE_AA)
    return cv2.addWeighted(fr,1-a,overlay,a,0)


def video_stats(path:Path):
    cap=cv2.VideoCapture(str(path)); n=0; black=0; dif=[]; prev=None; maxlow=0; low=0
    while True:
        ok,fr=cap.read()
        if not ok: break
        n+=1
        if float(fr.mean())<3.0: black+=1
        sm=cv2.resize(fr,(160,90),interpolation=cv2.INTER_AREA)
        if prev is not None:
            d=float(cv2.absdiff(sm,prev).mean()); dif.append(d)
            if d<.06: low+=1; maxlow=max(maxlow,low)
            else: low=0
        prev=sm
    cap.release()
    return {"decoded_frames":n,"black_frames_mean_lt3":black,"mean_adjacent_delta":float(np.mean(dif)) if dif else 0,"p05_adjacent_delta":float(np.percentile(dif,5)) if dif else 0,"max_near_static_run_frames":maxlow}


def contact_sheet(video:Path,out:Path):
    cap=cv2.VideoCapture(str(video)); frames=[]
    for q in np.linspace(.03,.97,12):
        cap.set(cv2.CAP_PROP_POS_FRAMES,int((TOTAL-1)*q)); ok,fr=cap.read()
        if ok:
            fr=cv2.resize(fr,(320,180),interpolation=cv2.INTER_AREA)
            cv2.putText(fr,f"{q*(TOTAL/FPS):05.1f}s",(8,172),cv2.FONT_HERSHEY_SIMPLEX,.42,(235,235,235),1,cv2.LINE_AA)
            frames.append(fr)
    cap.release()
    while len(frames)<12: frames.append(np.zeros((180,320,3),np.uint8))
    sheet=np.vstack([np.hstack(frames[i:i+4]) for i in range(0,12,4)])
    cv2.imwrite(str(out),sheet,[cv2.IMWRITE_JPEG_QUALITY,92])


# Preload sources and preserve their hashes for shot evidence.
base_cache={}; source_path={}
for e in ENTRIES:
    im,p=load_source(e); base_cache[e["shot_id"]]=im; source_path[e["shot_id"]]=p

picture=OUT/"PANDORA_BRANCH_PICTURE_960x540.mp4"
cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",str(picture)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
prev=None; written=0
for e in ENTRIES:
    sid=e["shot_id"]; start=int(e["start_frame"]); end=int(e["end_frame"]); n=end-start+1
    profile=e["animation_behavior"].split(";",1)[0]
    base=base_cache[sid]
    for j in range(n):
        q=j/max(1,n-1); f=start+j
        energy,transient=authored_energy(f,j,n,profile)
        fr=profile_composite(base,profile,q)
        fr=camera(fr,q,profile,energy,transient)
        fr=canonical_fx(fr,profile,j/FPS,n/FPS,f,energy,transient)
        if sid=="S00":
            fr=cold_open_title(fr,j)
            if j<12: fr=(fr.astype(np.float32)*(j/12.0)).astype(np.uint8)
        if prev is not None and j<7 and sid!="S00":
            a=.5-.5*math.cos(math.pi*(j+1)/7.0)
            fr=cv2.addWeighted(prev,1-a,fr,a,0)
        if sid=="S33" and q>.87:
            a=max(0,1-(q-.87)/.13); fr=(fr.astype(np.float32)*a).astype(np.uint8)
        proc.stdin.write(fr.tobytes()); prev=fr; written+=1
    print(f"{sid}: {n} frames / {written}/{TOTAL}",flush=True)
proc.stdin.close(); rc=proc.wait()
if rc!=0: raise SystemExit(rc)
if written!=TOTAL: raise RuntimeError(f"frame mismatch {written} != {TOTAL}")

stats=video_stats(picture)
contact=OUT/"PANDORA_BRANCH_PICTURE_CONTACT_SHEET.jpg"
contact_sheet(picture,contact)

# Build durable low-resolution proof clips and shot packages from the real picture.
PKG=ROOT/"shot_packages"; PKG.mkdir(exist_ok=True)
shot_results=[]
for e in ENTRIES:
    sid=e["shot_id"]; d=PKG/sid; d.mkdir(exist_ok=True)
    start=int(e["start_frame"])/FPS; dur=(int(e["end_frame"])-int(e["start_frame"])+1)/FPS
    proof=d/"proof_320x180.mp4"
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-ss",f"{start:.6f}","-i",str(picture),"-t",f"{dur:.6f}","-vf","scale=320:180:flags=lanczos","-an","-c:v","libx264","-preset","veryfast","-crf","27","-pix_fmt","yuv420p",str(proof)],check=True)
    pst=video_stats(proof)
    expected=max(1,int(round(dur*FPS)))
    # Allow final fade-to-black only in S33 and opening fade only in S00.
    allowed_black=14 if sid=="S00" else (28 if sid=="S33" else 0)
    result="PASS" if abs(pst["decoded_frames"]-expected)<=2 and pst["black_frames_mean_lt3"]<=allowed_black and pst["mean_adjacent_delta"]>.08 and pst["max_near_static_run_frames"]<30 else "FAIL"
    src=source_path[sid]
    package={
        "schema":"aivideoedit.shot-package.v1","shot_id":sid,
        "frame_span":[int(e["start_frame"]),int(e["end_frame"])],
        "seconds":[start,start+dur],"story_action":e["story_action"],"lyric_cue":e.get("lyric_cue"),
        "source":str(src.relative_to(ROOT)),"source_role":"generated branch-recovery production source",
        "motion_grammar":e["animation_behavior"],"canonical_fx_lock":"fx.lock.json",
        "proof_preview":str(proof.relative_to(ROOT)),"proof_qc":{"result":result,**pst},
        "media_evidence":[
            {"role":"primary_source","path":str(src.relative_to(ROOT)),"sha256":sha256(src),"status":"generated"},
            {"role":"proof_preview","path":str(proof.relative_to(ROOT)),"sha256":sha256(proof),"status":"derived"},
            {"role":"fx_lock","path":"fx.lock.json","sha256":sha256(FX_LOCK),"status":"accepted"}
        ],
        "notes":"Full-shot low-resolution proof derived from the 960x540 branch picture after live FX-lock verification."
    }
    (d/"package.json").write_text(json.dumps(package,indent=2)+"\n",encoding="utf-8")
    shot_results.append({"shot_id":sid,"expected_frames":expected,"result":result,"proof":str(proof.relative_to(ROOT)),"proof_sha256":sha256(proof),**pst})
    print("proof",sid,result,flush=True)

shot_qc={"schema":"aivideoedit.shot-proof-qc.v1","project":"the-door-between-the-seconds","picture_sha256":sha256(picture),"fx_lock_sha256":sha256(FX_LOCK),"shots":shot_results,"complete_shots":len(shot_results),"expected_shots":len(ENTRIES),"result":"PASS" if all(x["result"]=="PASS" for x in shot_results) else "FAIL"}
(ROOT/"proofs"/"current_gate").mkdir(parents=True,exist_ok=True)
(ROOT/"proofs"/"current_gate"/"SHOT_PROOF_QC.branch.json").write_text(json.dumps(shot_qc,indent=2)+"\n",encoding="utf-8")

qc={"schema":"door-seconds.branch-picture-qc.v1","subject":"Pandora the Vampire","picture":picture.name,"sha256":sha256(picture),"bytes":picture.stat().st_size,"runtime_seconds":TOTAL/FPS,"fps":FPS,"resolution":[W,H],"audio":"not_muxed_source_audio_binary_unavailable","cold_open_seconds":6.0,"shot_count":len(ENTRIES),"video_stats":stats,"shot_proof_result":shot_qc["result"],"status":"PICTURE_CANDIDATE" if shot_qc["result"]=="PASS" and stats["decoded_frames"]==TOTAL else "REJECTED"}
(OUT/"PANDORA_BRANCH_PICTURE_QC.json").write_text(json.dumps(qc,indent=2)+"\n",encoding="utf-8")
print(json.dumps(qc,indent=2),flush=True)
if qc["status"]!="PICTURE_CANDIDATE": raise SystemExit(2)
