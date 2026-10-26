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

def glow_mask(shape,rois):
    h,w=shape[:2]; mask=np.zeros((h,w),np.float32)
    for x,y,rx,ry in rois:
        cv2.ellipse(mask,(round(x*w),round(y*h)),(max(1,round(rx*w)),max(1,round(ry*h))),0,0,360,1.,-1)
    return np.clip(cv2.GaussianBlur(mask,(0,0),sigmaX=16,sigmaY=16),0,1)[...,None]

def face_mask(shape):
    h,w=shape[:2]; mask=np.zeros((h,w),np.float32)
    for x,y in ((.45,.33),(.72,.29)):
        cv2.ellipse(mask,(round(x*w),round(y*h)),(round(.08*w),round(.17*h)),0,0,360,1.,-1)
    return np.clip(cv2.GaussianBlur(mask,(0,0),9),0,1)[...,None]

def blend(a,b,alpha):
    if np.isscalar(alpha): return cv2.addWeighted(a,1-float(alpha),b,float(alpha),0)
    return np.clip(a.astype(np.float32)*(1-alpha)+b.astype(np.float32)*alpha,0,255).astype(np.uint8)

def load_stills(manifest,root):
    out={}
    for s in manifest["selected_stills"]:
        p=Path(root)/s["file"]
        if not p.is_file() or sha(p)!=s["sha256"]: raise RuntimeError("B05 source mismatch "+s["id"])
        im=cv2.imread(str(p))
        if im is None: raise RuntimeError("cannot decode "+str(p))
        out[s["id"]]=resize(im)
    return out

def still_frame(fx,im,idx,total,camera,rois,subtle=False):
    ctx=FXContext(t=idx/24,duration=max(total/24,1/24),frame_index=idx,fps=24,energy=.38 if not subtle else .12,transient=.04)
    fr=im if subtle else fx.apply_frame("FX2-CAMERA-023",im,ctx,params=camera)
    mask=glow_mask(fr.shape,rois)
    if not subtle:
        motion=fx.apply_frame("FX2-MOTION-002",fr,ctx)
        fr=blend(fr,motion,mask*.37)
    if rois:
        x,y,*_=rois[0]
        lit=fx.apply_frame("FX2-LIGHT-002",fr,ctx,params={"origin":[x,y],"strength":.16 if not subtle else .07})
        fr=blend(fr,lit,mask*(.57 if not subtle else .13))
    if not subtle:
        graded=fx.apply_frame("FX2-LIGHT-025",fr,ctx)
        fr=cv2.addWeighted(fr,.962,graded,.038,0)
    return fr

def read_video_frames(path,start,count,crop):
    cap=cv2.VideoCapture(str(path))
    if not cap.isOpened():raise RuntimeError("cannot open canonical Gemini B")
    fps=cap.get(cv2.CAP_PROP_FPS)
    if abs(fps-24)>0.02:raise RuntimeError(f"wrong canonical cadence {fps}")
    cap.set(cv2.CAP_PROP_POS_FRAMES,round(float(start)*fps))
    x1,y1,x2,y2=crop
    out=[]
    for i in range(count):
        ok,fr=cap.read()
        if not ok:raise RuntimeError(f"B05 source motion bridge ended at {i}")
        h,w=fr.shape[:2]
        rect=fr[int(y1*h):int(y2*h),int(x1*w):int(x2*w)]
        if rect.size==0:raise RuntimeError("invalid source-crop bounding box")
        out.append(resize(rect))
    cap.release()
    return out

def transition_frames(fx,a,b,rois,count):
    # RC3: source-orb-centred reveal. Every subject pixel comes from one
    # original source or the other; never double-expose faces or alter geometry.
    h,w=a.shape[:2]
    cx,cy=(rois[0][0],rois[0][1]) if rois else (.30,.49)
    yy,xx=np.ogrid[:h,:w]
    radius_map=np.sqrt((xx-cx*w)**2+(yy-cy*h)**2)
    maximum=max(np.hypot(x-cx*w,y-cy*h) for x,y in ((0,0),(w,0),(w,h),(0,h)))
    glow=glow_mask(a.shape,rois)
    faces=face_mask(a.shape)
    out=[]
    for i in range(count):
        p=ease((i+1)/(count+1))
        ctx=FXContext(t=i/24,duration=count/24,frame_index=i,fps=24,energy=.24,transient=.08)
        registered=fx.apply_transition("FX2-TRANS-025",a,b,p,ctx)
        r=p*(maximum+45)-20
        reveal=np.clip((r-radius_map+8)/16,0,1).astype(np.float32)[...,None]
        # Clean expansion out of the authored orb; 16px feather solely at
        # the moving reveal edge. Faces never receive a blended double image.
        base=blend(a,b,reveal)
        memory_region=glow*(1-faces)*(.11*np.sin(np.pi*p)**2)
        out.append(blend(base,registered,memory_region))
    return out

def render(args):
    manifest=json.loads(Path(args.manifest).read_text())
    if manifest["schema"]!="godrender.nordic-b05-director-edit-fx.v1": raise RuntimeError("wrong manifest")
    if sum(int(x["frames"]) for x in manifest["timeline"])!=503: raise RuntimeError("timeline must be 503 frames")
    if sha(args.video_b)!=manifest["source_video_b"]["sha256"]: raise RuntimeError("B05 original Gemini B video SHA mismatch")
    if sha(args.storyboard_zip)!=manifest["source_zip"]["sha256"]:raise RuntimeError("B05 storyboard source hash mismatch")
    stills=load_stills(manifest,args.input_root); fx=FXExecutor(consumer="nordic_b05_director_edit_fx"); frames=[]
    roi={s["id"]:s["glow"] for s in manifest["selected_stills"]}
    crop_by_id={}
    with __import__("zipfile").ZipFile(args.storyboard_zip) as z:
        source_manifest=json.loads(z.read("manifest.json"))
        for s in source_manifest["frames"]:
            crop_by_id[s["id"]]=s["crop_fraction_xyxy"]
    for k,seg in enumerate(manifest["timeline"]):
        n=int(seg["frames"])
        t=seg["type"]
        if t=="still":
            sid=seg["id"]; image=stills[sid]
            frames.extend(still_frame(fx,image,i,n,seg["camera"],roi[sid]) for i in range(n))
        elif t=="source_video_bridge":
            src=read_video_frames(args.video_b,seg["source_start"],n,crop_by_id[seg["crop_to"]])
            if frames:
                anchor=frames[-1].copy()
                for i in range(min(6,n)):
                    src[i]=blend(anchor,src[i],ease((i+1)/6))
            frames.extend(src)
        elif t=="transition":
            if not frames or k+1>=len(manifest["timeline"]):raise RuntimeError("unbound FX transition")
            next_seg=manifest["timeline"][k+1]
            if next_seg["type"]!="still" or next_seg["id"]!=seg["to"]:raise RuntimeError("wrong transition destination")
            sid=seg["to"]
            incoming=still_frame(fx,stills[sid],0,int(next_seg["frames"]),next_seg["camera"],roi[sid])
            frames.extend(transition_frames(fx,frames[-1],incoming,roi[sid],n))
        elif t=="cut":
            sid=seg["to"]
            next_seg=manifest["timeline"][k+1]
            if next_seg["type"]!="still" or next_seg["id"]!=sid or n!=1:raise RuntimeError("cut mismatch")
            frames.append(still_frame(fx,stills[sid],0,int(next_seg["frames"]),next_seg["camera"],roi[sid]))
        elif t=="quiet_breath":
            sid=seg["id"]
            for i in range(n):
                frames.append(still_frame(fx,stills[sid],i,n,None,roi[sid],subtle=True))
        else:raise RuntimeError("unknown segment "+str(t))
    if len(frames)!=503: raise RuntimeError(f"render frame count {len(frames)}")
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True); silent=out/"b05_silent.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-f","rawvideo","-pix_fmt","bgr24","-s","1280x720","-r","24","-i","-","-an","-c:v","libx264","-preset","fast","-crf","17","-pix_fmt","yuv420p","-movflags","+faststart",str(silent)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for fr in frames: proc.stdin.write(fr.astype(np.uint8).tobytes())
    proc.stdin.close(); err=proc.stderr.read().decode(); rc=proc.wait()
    if rc: raise RuntimeError(err[-2000:])
    final=out/"NORDIC_B05_DIRECTOR_EDIT_FX_720p.mp4"; dur=503/24
    mux=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-i",str(silent),"-ss",str(manifest["audio"]["offset_seconds"]),"-i",str(args.audio),"-map","0:v:0","-map","1:a:0","-t",f"{dur:.9f}","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",str(final)],capture_output=True,text=True)
    if mux.returncode: raise RuntimeError(mux.stderr[-2000:])
    rec={"schema":"godrender.nordic-b05-director-edit-fx.receipt.v1","status":"TECHNICAL_RENDER_PASS_DIRECTOR_REVIEW_REQUIRED","batch":"B05","frames":503,"fps":24,"duration_seconds":dur,"selected_stills":[x["id"] for x in manifest["selected_stills"]],"source_video_bridges":[[8.4,9],[8.833333,11]],"transition_fx":["FX2-TRANS-025"],"localized_motion_fx":"FX2-MOTION-002","interface_only":True,"camera_fx":["FX2-CAMERA-023"],"second_breath_at_batch_frame":377,"film_sha256":sha(final),"film_bytes":final.stat().st_size,"director_rc":"RC3_ORB_LOCAL_REVEAL_FACE_SAFE","source_boundary_easing_frames":6}
    (out/"render_receipt.json").write_text(json.dumps(rec,indent=2)+"\n"); print(json.dumps(rec))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for x in ["--manifest","--input-root","--audio","--out"]: ap.add_argument(x,required=True)
    ap.add_argument("--video-b",required=True)
    ap.add_argument("--storyboard-zip",required=True)
    render(ap.parse_args())
