#!/usr/bin/env python3
"""Nordic Remastered: NEW source-canon 60-shot Director's Cut.
GodRender native FXExecutor, one prior ONNX timing map, original source media only.
No accepted batch workprints, no regeneration, no direct Drive access.
"""
import argparse,hashlib,json,subprocess,sys,zipfile
from pathlib import Path
import cv2,numpy as np
sys.path.insert(0,str(Path.cwd()))
from general.reusable.fx_v2.executor import FXExecutor
from general.reusable.fx_v2.runtime import FXContext
W,H,FPS=1280,720,24
P=Path("projects/nordic-remastered")
def digest(b): return hashlib.sha256(b).hexdigest()
def hashfile(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def require(p,sha):
 assert Path(p).is_file(),p
 got=hashfile(p)
 if got!=sha:raise RuntimeError(f"HASH_LOCK_FAILURE {p}: {got} != {sha}")
def resize(im):return im if im.shape[:2]==(H,W) else cv2.resize(im,(W,H),interpolation=cv2.INTER_LANCZOS4)
def shots_from_zip(path,batch,expected):
 require(path,expected)
 d={};hashes={}
 with zipfile.ZipFile(path) as z:
  man=json.loads(z.read("manifest.json") if "manifest.json" in z.namelist() else z.read("batch-01/manifest.json"))
  rows=man.get("shots") or man.get("frames")
  if len(rows)!=10:raise RuntimeError(f"{batch} not ten stills")
  for i,row in enumerate(rows):
   n=row.get("file") or row.get("frame") or row.get("filename")
   fn=n if n in z.namelist() else "batch-01/"+n
   binary=z.read(fn)
   if digest(binary)!=row["sha256"]:raise RuntimeError(f"{batch} still mismatch {fn}")
   im=cv2.imdecode(np.frombuffer(binary,np.uint8),cv2.IMREAD_COLOR)
   if im is None:raise RuntimeError(f"bad decoded frame {fn}")
   key=f"{batch}_{i+1:02d}";d[key]=resize(im);hashes[key]=row["sha256"]
 return d,hashes
def load_stills(m,source_dir):
 out={};hashes={}
 lin=json.loads((P/"media/b01_gemini_extractions/SOURCE_LINEAGE.json").read_text())
 for i,s in enumerate(lin["frames"]):
  f=P/"runner_sources/batch-01"/s["frame"]
  require(f,s["sha256"])
  im=cv2.imread(str(f))
  if im is None:raise RuntimeError("invalid B01 source image")
  key=f"B01_{i+1:02d}";out[key]=resize(im);hashes[key]=s["sha256"]
 for batch in ["B02","B03","B04","B05","B06"]:
  p=Path(source_dir)/(batch+".zip")
  ims,locks=shots_from_zip(p,batch,m["storyboard_zip_sha256"][batch])
  out.update(ims);hashes.update(locks)
 assert len(out)==60 and len(hashes)==60
 return out,hashes
def ctx(i,n,energy):return FXContext(t=i/FPS,duration=n/FPS,frame_index=i,fps=FPS,energy=energy,transient=.04)
def mask_ellipse(shape,origin,radii):
 h,w=shape[:2];yy,xx=np.ogrid[:h,:w]
 return np.float32((((xx-origin[0]*w)/(radii[0]*w))**2+((yy-origin[1]*h)/(radii[1]*h))**2)<=1)
def blend(a,b,m):
 return np.uint8(np.clip(a.astype(np.float32)*(1-m[:,:,None])+b.astype(np.float32)*m[:,:,None],0,255))
def profile_roi(profile):
 return {"night_sky":(0.15,0.03,1.0,0.66),"threshold":(0.35,0.03,1.0,0.68),
 "architecture":(.04,.05,.95,.65),"interface":(.10,.24,.49,.74),
 "recollection":(.25,.03,1.0,.65),"ending":(.60,.08,.98,.48)}[profile]
def frame_fx(fx,im,shot,i,n,energy):
 profile=shot["fx_profile"];p=i/max(1,n-1);ident=shot["id"]
 # Camera language: no routine zoom on the final observer, faces protected by max 3% reframe.
 if profile=="ending":frame=im.copy()
 else:
  z0=1.012+(int(ident[-2:])%3)*.005
  z1=z0+(.016 if profile in ("architecture","threshold") else .009)
  direction=-1 if int(ident[-2:])%2 else 1
  pars={"zoom_start":z0,"zoom_end":z1,"zoom_cap":1.14,
        "center_start":[.5,.5],"center_end":[.5+direction*.009,.5-.004],
        "easing":"smoothstep"}
  frame=fx.apply_frame("FX2-CAMERA-023",im,ctx(i,n,energy),params=pars)
 # Protected-subject, source-aware internal motion only on actual luminous environment/interface.
 if profile!="ending":
  region=profile_roi(profile)
  if profile in ("night_sky","recollection","interface") and (int(ident[-2:])%2==0):
   moving=fx.apply_frame("FX2-MOTION-002",frame,ctx(i,n,energy),params={"roi":region,"strength":.28})
   roi=np.zeros((H,W),np.float32)
   x1,y1,x2,y2=region
   roi[int(y1*H):int(y2*H),int(x1*W):int(x2*W)]=1
   roi=cv2.GaussianBlur(roi,(0,0),15)
   if profile=="interface":roi*=mask_ellipse(frame.shape,(.29,.49),(.19,.22))
   frame=blend(frame,moving,np.clip(roi*.36,0,.36))
  if profile in ("night_sky","threshold","recollection","interface") and int(ident[-2:])%3==0:
   origin=(.70,.21) if profile!="interface" else (.30,.46)
   light=fx.apply_frame("FX2-LIGHT-002",frame,ctx(i,n,energy),params={"origin":origin,"strength":.58})
   roi=mask_ellipse(frame.shape,origin,(.42,.40) if profile!="interface" else (.20,.24))
   frame=blend(frame,light,roi*.30)
  if profile=="night_sky" and int(ident[-2:]) in (1,6):
   fog=fx.apply_frame("FX2-ATM-021",frame,ctx(i,n,energy))
   roi=np.zeros((H,W),np.float32);roi[int(.35*H):int(.72*H),:]=.065
   frame=blend(frame,fog,roi)
  if profile in ("threshold","architecture") and int(ident[-2:])==7:
   grade=fx.apply_frame("FX2-LIGHT-025",frame,ctx(i,n,energy))
   frame=cv2.addWeighted(frame,.965,grade,.035,0)
 return frame
def portal_transition(fx,a,b,index,length,energy):
 p=(index+1)/(length+1)
 # Native object-portal computed from actual source pair, then clipped to a source-derived iris.
 native=fx.apply_transition("FX2-TRANS-027",a,b,p,ctx(index,length,energy))
 yy,xx=np.ogrid[:H,:W];cx,cy=.7*W,.47*H
 dist=np.sqrt((xx-cx)**2+(yy-cy)**2).astype(np.float32)
 maxd=np.max(dist)
 radius=p*(maxd+20)
 iris=np.clip((radius-dist+4)/8,0,1)
 base=blend(a,b,iris)
 roi=mask_ellipse(a.shape,(.7,.47),(.30,.37))
 return blend(base,native,np.clip(roi*.075*np.sin(np.pi*p)**2,0,.075))
def countsource(path):
 cap=cv2.VideoCapture(str(path))
 if not cap.isOpened():raise RuntimeError(f"Cannot open {path}")
 if abs(cap.get(cv2.CAP_PROP_FPS)-24)>.02:raise RuntimeError("original source speed mismatch")
 if int(cap.get(cv2.CAP_PROP_FRAME_COUNT))!=240:raise RuntimeError("original clip not 240 frames")
 return cap
def render(args):
 m=json.loads(Path(args.manifest).read_text())
 if m["schema"]!="godrender.nordic-director-cut-new.v1":raise RuntimeError("wrong director cut manifest")
 if m["frames"]!=3311 or sum(x["total"] for x in m["sections"])!=3311:raise RuntimeError("wrong timeline frame count")
 require(args.audio,m["audio_sha256"]);require(args.video_a,m["video_a_sha256"]);require(args.video_b,m["video_b_sha256"])
 imgs,hashes=load_stills(m,args.media)
 timeline=[k["id"] for sec in m["sections"] for k in sec.get("shots",[])]
 if len(timeline)!=60 or len(set(timeline))!=60 or set(timeline)!=set(imgs):raise RuntimeError("not all 60 original stills used")
 out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
 silent=out/"new_directors_cut_silent.mp4"
 proc=subprocess.Popen(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-f","rawvideo",
 "-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264",
 "-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-movflags","+faststart",str(silent)],
 stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 fx=FXExecutor(consumer="nordic_new_60_shot_director_cut",ledger_path=str(out/"fx_execution_ledger.jsonl"))
 total=0;applied={};previous=None;sequence=[]
 try:
  for sec in m["sections"]:
   if "shots" not in sec:
    cap=countsource(args.video_a if sec["batch"]=="A" else args.video_b)
    for j in range(sec["total"]):
     ok,frame=cap.read()
     if not ok:raise RuntimeError("moving source unexpectedly short")
     proc.stdin.write(np.ascontiguousarray(frame).tobytes());total+=1
    cap.release();previous=frame.copy();sequence.append({"clip":sec["batch"],"frames":sec["total"],"natural_speed":True})
   else:
    for k,shot in enumerate(sec["shots"]):
     n=shot["frames"];im=imgs[shot["id"]]
     # Cut progression follows ONNX chapter boundaries; only specific source-portal handoffs use an iris.
     portal=(sec["batch"]=="B02" and k==9) or (sec["batch"]=="B03" and k==0) or (sec["batch"]=="B06" and k==4)
     for i in range(n):
      frame=frame_fx(fx,im,shot,i,n,sec["chapter_energy"])
      if portal and previous is not None and i<7:
       frame=portal_transition(fx,previous,frame,i,7,sec["chapter_energy"])
       applied["FX2-TRANS-027"]=applied.get("FX2-TRANS-027",0)+1
      proc.stdin.write(np.ascontiguousarray(frame).tobytes());total+=1
     previous=frame.copy();sequence.append({"shot":shot["id"],"frames":n,"profile":shot["fx_profile"]})
   if total!=sec["end_frame"]:raise RuntimeError(f"section boundary drift {sec['chapter']}: {total} != {sec['end_frame']}")
  proc.stdin.close()
  error=proc.stderr.read().decode()
  if proc.wait():raise RuntimeError("ffmpeg encode error "+error[-2000:])
 except BaseException:
  try: proc.kill()
  except Exception:pass
  raise
 if total!=3311:raise RuntimeError("total frame mismatch")
 film=out/"NORDIC_NEW_DIRECTORS_CUT_NATIVE_FX_720p.mp4"
 mux=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-i",str(silent),
 "-i",str(args.audio),"-map","0:v:0","-map","1:a:0","-t",f"{3311/FPS:.9f}",
 "-c:v","copy","-c:a","aac","-b:a","256k","-ar","48000","-ac","2","-movflags","+faststart",str(film)],
 capture_output=True,text=True)
 if mux.returncode:raise RuntimeError(mux.stderr[-3000:])
 proof={"schema":"godrender.nordic.new-directors-cut.native-proof.v1",
 "status":"TECHNICAL_RENDER_COMPLETE_DIRECTOR_REVIEW_REQUIRED","frames":total,"fps":FPS,
 "duration_seconds":total/FPS,"stills_used":len(hashes),"shot_order":timeline,
 "input_sha256":hashes,"original_video_a_sha256":m["video_a_sha256"],"original_video_b_sha256":m["video_b_sha256"],
 "original_song_sha256":m["audio_sha256"],"registered_portal_transition_frames":applied.get("FX2-TRANS-027",0),
 "film_sha256":hashfile(film),"film_bytes":film.stat().st_size,"master_film_release_pass":False,
 "native_fx_ledger":str(out/"fx_execution_ledger.jsonl")}
 (out/"new_directors_cut_receipt.json").write_text(json.dumps(proof,indent=2)+"\n")
 (out/"director_shot_execution.json").write_text(json.dumps(sequence,indent=2)+"\n")
 print(json.dumps({k:v for k,v in proof.items() if k not in ("shot_order","input_sha256")},indent=2))
if __name__=="__main__":
 p=argparse.ArgumentParser()
 for opt in ("manifest","media","video-a","video-b","audio","out"):p.add_argument("--"+opt,required=True)
 a=p.parse_args()
 a.video_a=getattr(a,"video_a");a.video_b=getattr(a,"video_b")
 render(a)
