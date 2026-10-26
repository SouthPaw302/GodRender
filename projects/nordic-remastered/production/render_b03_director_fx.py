#!/usr/bin/env python3
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
import cv2,numpy as np
ROOT=Path.cwd(); sys.path.insert(0,str(ROOT))
from general.reusable.fx_v2.executor import FXExecutor
from general.reusable.fx_v2.runtime import FXContext

def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def ease(x):
    x=max(0.0,min(1.0,float(x)))
    return 0.5-0.5*np.cos(np.pi*x)

def resize(im): return cv2.resize(im,(1280,720),interpolation=cv2.INTER_LANCZOS4)

def sky_mask(shape):
    h,w=shape[:2]; m=np.zeros((h,w),np.float32); m[:int(h*.77),:]=1.0
    return np.clip(cv2.GaussianBlur(m,(0,0),24),0,1)[...,None]

def blend(a,b,alpha):
    if np.isscalar(alpha): return cv2.addWeighted(a,1-float(alpha),b,float(alpha),0)
    return np.clip(a.astype(np.float32)*(1-alpha)+b.astype(np.float32)*alpha,0,255).astype(np.uint8)

def load_stills(manifest,root):
    out={}
    for s in manifest["selected_stills"]:
        p=Path(root)/s["file"]
        if not p.is_file() or sha(p)!=s["sha256"]: raise RuntimeError("B03 source mismatch "+s["id"])
        im=cv2.imread(str(p))
        if im is None: raise RuntimeError("cannot decode "+str(p))
        out[s["id"]]=resize(im)
    return out

def still_frame(fx,im,idx,total,camera,extra):
    ctx=FXContext(t=idx/24,duration=max(total/24,1/24),frame_index=idx,fps=24,energy=.18,transient=.04)
    fr=fx.apply_frame("FX2-CAMERA-023",im,ctx,params=camera)
    m=sky_mask(fr.shape)
    lit=fx.apply_frame("FX2-LIGHT-002",fr,ctx,params={"origin":[.62,.19],"strength":.26})
    fr=blend(fr,lit,m*.34)
    fog=fx.apply_frame("FX2-ATM-021",fr,ctx); fr=blend(fr,fog,m*.08)
    grade=fx.apply_frame("FX2-LIGHT-025",fr,ctx); fr=cv2.addWeighted(fr,.92,grade,.08,0)
    if "FX2-LIGHT-024" in (extra or []):
        shafts=fx.apply_frame("FX2-LIGHT-024",fr,ctx); fr=cv2.addWeighted(fr,.82,shafts,.18,0)
    return fr

def read_video_frames(path,start,end,count):
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened(): raise RuntimeError("cannot open source video A")
    frames=[]
    for i in range(count):
        p=i/max(count-1,1); t=start+(end-start)*p
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000.0)
        ok,fr=cap.read()
        if not ok: raise RuntimeError(f"video bridge decode failed at {t:.3f}")
        frames.append(resize(fr))
    cap.release(); return frames

def transition_frames(fx,a,b,effect,count):
    out=[]
    for i in range(count):
        p=ease((i+1)/(count+1))
        ctx=FXContext(t=i/24,duration=count/24,frame_index=i,fps=24,energy=.32,transient=.12)
        tr=fx.apply_transition(effect,a,b,p,ctx)
        tr=cv2.addWeighted(tr,.78,blend(a,b,p),.22,0)
        out.append(tr)
    return out

def render(args):
    manifest=json.loads(Path(args.manifest).read_text())
    if manifest["schema"]!="godrender.nordic-b03-director-edit-fx.v1": raise RuntimeError("wrong manifest")
    if sum(int(x["frames"]) for x in manifest["timeline"])!=452: raise RuntimeError("timeline must be 452 frames")
    stills=load_stills(manifest,args.input_root); fx=FXExecutor(consumer="nordic_b03_director_edit_fx"); frames=[]
    for seg in manifest["timeline"]:
        n=int(seg["frames"])
        if seg["type"]=="still":
            im=stills[seg["id"]]
            frames += [still_frame(fx,im,i,n,seg["camera"],seg.get("fx",[])) for i in range(n)]
        elif seg["type"]=="source_video_bridge":
            frames += read_video_frames(args.video_b,float(seg["source_start"]),float(seg["source_end"]),n)
        elif seg["type"]=="transition":
            frames += transition_frames(fx,stills[seg["from"]],stills[seg["to"]],seg["fx"],n)
        else: raise RuntimeError("unknown segment "+seg["type"])
    if len(frames)!=452: raise RuntimeError(f"render frame count {len(frames)}")
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True); silent=out/"b03_silent.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-f","rawvideo","-pix_fmt","bgr24","-s","1280x720","-r","24","-i","-","-an","-c:v","libx264","-preset","fast","-crf","17","-pix_fmt","yuv420p","-movflags","+faststart",str(silent)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for fr in frames: proc.stdin.write(fr.astype(np.uint8).tobytes())
    proc.stdin.close(); err=proc.stderr.read().decode(); rc=proc.wait()
    if rc: raise RuntimeError(err[-2000:])
    final=out/"NORDIC_B03_DIRECTOR_EDIT_FX_720p.mp4"; dur=452/24
    mux=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-i",str(silent),"-ss",str(manifest["audio"]["offset_seconds"]),"-i",str(args.audio),"-map","0:v:0","-map","1:a:0","-t",f"{dur:.9f}","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",str(final)],capture_output=True,text=True)
    if mux.returncode: raise RuntimeError(mux.stderr[-2000:])
    rec={"schema":"godrender.nordic-b03-director-edit-fx.receipt.v1","status":"TECHNICAL_RENDER_PASS_DIRECTOR_REVIEW_REQUIRED","batch":"B03","frames":452,"fps":24,"duration_seconds":dur,"selected_stills":[x["id"] for x in manifest["selected_stills"]],"source_video_bridges":[],"transition_fx":["FX2-TRANS-026","FX2-TRANS-027"],"camera_fx":"FX2-CAMERA-023","film_sha256":sha(final),"film_bytes":final.stat().st_size}
    (out/"render_receipt.json").write_text(json.dumps(rec,indent=2)+"\n"); print(json.dumps(rec))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for x in ["--manifest","--input-root","--audio","--out"]: ap.add_argument(x,required=True)
    ap.add_argument("--video-b",required=False)
    render(ap.parse_args())
