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

def city_mask(shape):
    h,w=shape[:2]; m=np.zeros((h,w),np.float32)
    m[int(h*.10):int(h*.78),int(w*.24):int(w*.73)]=1.0
    return np.clip(cv2.GaussianBlur(m,(0,0),42),0,1)[...,None]

def blend(a,b,alpha):
    if np.isscalar(alpha): return cv2.addWeighted(a,1-float(alpha),b,float(alpha),0)
    return np.clip(a.astype(np.float32)*(1-alpha)+b.astype(np.float32)*alpha,0,255).astype(np.uint8)

def load_stills(manifest,root):
    out={}
    for s in manifest["selected_stills"]:
        p=Path(root)/s["file"]
        if not p.is_file() or sha(p)!=s["sha256"]: raise RuntimeError("B04 source mismatch "+s["id"])
        im=cv2.imread(str(p))
        if im is None: raise RuntimeError("cannot decode "+str(p))
        out[s["id"]]=resize(im)
    return out

def still_frame(fx,im,idx,total,camera,extra):
    ctx=FXContext(t=idx/24,duration=max(total/24,1/24),frame_index=idx,fps=24,energy=.4,transient=.05)
    fr=fx.apply_frame("FX2-CAMERA-023",im,ctx,params=camera)
    mask=city_mask(fr.shape)
    if "FX2-CAMERA-021" in (extra or []):
        pushed=fx.apply_frame("FX2-CAMERA-021",fr,ctx)
        fr=blend(fr,pushed,mask*.14)
    if "FX2-SPATIAL-021" in (extra or []):
        depth=fx.apply_frame("FX2-SPATIAL-021",fr,ctx)
        fr=blend(fr,depth,mask*.12)
    light=fx.apply_frame("FX2-LIGHT-002",fr,ctx,params={"origin":[.54,.19],"strength":.20})
    fr=blend(fr,light,mask*.23)
    grade=fx.apply_frame("FX2-LIGHT-025",fr,ctx)
    return cv2.addWeighted(fr,.96,grade,.04,0)

def read_video_frames(path,start,end,count):
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened(): raise RuntimeError("cannot open source video B")
    frames=[]
    source_fps=cap.get(cv2.CAP_PROP_FPS)
    if abs(source_fps-24)>0.02: raise RuntimeError(f"B04 source cadence {source_fps} not original 24fps")
    cap.set(cv2.CAP_PROP_POS_FRAMES,round(start*source_fps))
    for i in range(count):
        ok,fr=cap.read()
        if not ok: raise RuntimeError(f"B04 same-source video bridge decode failed at frame {i}")
        frames.append(resize(fr))
    cap.release(); return frames

def transition_frames(fx,a,b,effect,count):
    out=[]
    for i in range(count):
        p=ease((i+1)/(count+1))
        ctx=FXContext(t=i/24,duration=count/24,frame_index=i,fps=24,energy=.32,transient=.12)
        tr=fx.apply_transition(effect,a,b,p,ctx)
        baseline=blend(a,b,p)
        # Registered FX is strongest in the middle, with exact source-boundary continuity.
        fx_weight=float(.42*np.sin(np.pi*p)**2)
        out.append(blend(baseline,tr,fx_weight))
    return out

def render(args):
    manifest=json.loads(Path(args.manifest).read_text())
    if manifest["schema"]!="godrender.nordic-b04-director-edit-fx.v1": raise RuntimeError("wrong manifest")
    if sum(int(x["frames"]) for x in manifest["timeline"])!=326: raise RuntimeError("timeline must be 326 frames")
    if sha(args.video_b)!=manifest["source_video_b"]["sha256"]: raise RuntimeError("B04 original Gemini B video SHA mismatch")
    stills=load_stills(manifest,args.input_root); fx=FXExecutor(consumer="nordic_b04_director_edit_fx"); frames=[]
    for k,seg in enumerate(manifest["timeline"]):
        n=int(seg["frames"])
        if seg["type"]=="still":
            im=stills[seg["id"]]
            frames += [still_frame(fx,im,i,n,seg["camera"],seg.get("fx",[])) for i in range(n)]
        elif seg["type"]=="source_video_bridge":
            motion=read_video_frames(args.video_b,float(seg["source_start"]),float(seg["source_end"]),n)
            if frames:
                anchor=frames[-1].copy()
                for i in range(min(6,len(motion))):
                    alpha=ease((i+1)/6)
                    motion[i]=blend(anchor,motion[i],alpha)
            frames += motion
        elif seg["type"]=="clean_breath":
            # Enter the unadorned musical pivot, no registered FX.
            target=stills[seg["id"]]
            anchor=frames[-1] if frames else target
            for i in range(n):
                frames.append(blend(anchor,target,ease((i+1)/8)) if i<8 else target.copy())
        elif seg["type"]=="transition":
            if not frames or k+1>=len(manifest["timeline"]):
                raise RuntimeError("B04 transition requires adjacent source media")
            next_seg=manifest["timeline"][k+1]
            if next_seg["type"]!="still" or next_seg["id"]!=seg["to"]:
                raise RuntimeError("B04 transition target not next canonical still")
            anchor=still_frame(fx,stills[seg["to"]],0,int(next_seg["frames"]),next_seg["camera"],next_seg.get("fx",[]))
            frames += transition_frames(fx,frames[-1],anchor,seg["fx"],n)
        else: raise RuntimeError("unknown segment "+seg["type"])
    if len(frames)!=326: raise RuntimeError(f"render frame count {len(frames)}")
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True); silent=out/"b04_silent.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-f","rawvideo","-pix_fmt","bgr24","-s","1280x720","-r","24","-i","-","-an","-c:v","libx264","-preset","fast","-crf","17","-pix_fmt","yuv420p","-movflags","+faststart",str(silent)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for fr in frames: proc.stdin.write(fr.astype(np.uint8).tobytes())
    proc.stdin.close(); err=proc.stderr.read().decode(); rc=proc.wait()
    if rc: raise RuntimeError(err[-2000:])
    final=out/"NORDIC_B04_DIRECTOR_EDIT_FX_720p.mp4"; dur=326/24
    mux=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-i",str(silent),"-ss",str(manifest["audio"]["offset_seconds"]),"-i",str(args.audio),"-map","0:v:0","-map","1:a:0","-t",f"{dur:.9f}","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",str(final)],capture_output=True,text=True)
    if mux.returncode: raise RuntimeError(mux.stderr[-2000:])
    rec={"schema":"godrender.nordic-b04-director-edit-fx.receipt.v1","status":"TECHNICAL_RENDER_PASS_DIRECTOR_REVIEW_REQUIRED","batch":"B04","frames":326,"fps":24,"duration_seconds":dur,"selected_stills":[x["id"] for x in manifest["selected_stills"]],"source_video_bridges":[[5.0,5.75],[6.05,6.758333],[6.75,7.5]],"transition_fx":["FX2-TRANS-025"],"camera_fx":["FX2-CAMERA-023","FX2-CAMERA-021"],"spatial_fx":"FX2-SPATIAL-021","clean_break_at_batch_frame":263,"film_sha256":sha(final),"film_bytes":final.stat().st_size,"director_rc":"RC1_ARCHITECTURAL_REVEAL_CLEAN_BREAK","source_boundary_easing_frames":6}
    (out/"render_receipt.json").write_text(json.dumps(rec,indent=2)+"\n"); print(json.dumps(rec))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for x in ["--manifest","--input-root","--audio","--out"]: ap.add_argument(x,required=True)
    ap.add_argument("--video-b",required=True)
    render(ap.parse_args())
