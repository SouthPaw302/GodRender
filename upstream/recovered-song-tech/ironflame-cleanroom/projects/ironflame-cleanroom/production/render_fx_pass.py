#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math,subprocess,sys
from pathlib import Path
import cv2,numpy as np
PROJECT=Path(__file__).resolve().parents[1]
REPO=PROJECT.parents[1]
sys.path.insert(0,str(REPO))
from general.reusable.fx_v2.promoted_effects import apply_effect
ID_TO_NAME={"FX2-ATM-021":"atmospheric_fog","FX2-ATM-022":"forge_motion_furnace_sparks","FX2-ATM-025":"wet_road_rain_reflection","FX2-DISTORT-021":"heat_haze","FX2-LIGHT-023":"firelight_breath","FX2-LIGHT-025":"temporal_grade_shift","FX2-LIGHT-027":"volumetric_light_shafts","FX2-MOTION-024":"localized_micro_warp","FX2-SPATIAL-021":"pseudo_depth_field","FX2-CAMERA-024":"rack_focus_heat_pulse"}
load=lambda p:json.loads(Path(p).read_text())
PLAN=load(PROJECT/"production/FX_PLAN.json"); AUDIO=load(PROJECT/"analysis/audiomap.json"); DEPTH=load(PROJECT/"production/DEPTH_LOOP_SOURCE.json")
clamp=lambda x,a=0,b=1:max(a,min(b,float(x)))
def energy_at(t):
 b=AUDIO.get("energy",{}).get("buckets",[])
 return .55 if not b else clamp(b[min(max(int(t),0),len(b)-1)].get("energy",.55))
def transient_at(t):
 v=0.0
 for m in AUDIO.get("energy",{}).get("key_moments",[]):
  c=float(m.get("t",0));d=abs(float(m.get("delta",0)));v=max(v,min(1,d*3)*math.exp(-((t-c)/.20)**2))
 return clamp(v)
def active(t):
 for s in PLAN["segments"]:
  if float(s["start"])<=t<float(s["end"]) or abs(t-float(s["end"]))<1e-6:return s["effects"]
 return []
def section(t):
 for i,x in enumerate(DEPTH["items"]):
  a,b=map(float,x["source_range_seconds"])
  if a<=t<b or (i==len(DEPTH["items"])-1 and t<=b):return i
 return len(DEPTH["items"])-1
def load_fields(d):
 if d is None:return None
 out=[]
 for i in range(1,13):
  p=Path(d)/"fields"/f"flow_{i:02d}.npz"
  if not p.is_file():raise RuntimeError(f"missing {p}")
  f=np.load(p)["flow"].astype(np.float32)
  if f.shape!=(720,1280,2):raise RuntimeError(f"bad field {p}: {f.shape}")
  out.append(f)
 return out
def depth(frame,t,fields):
 if not fields:return frame
 i=section(t);a,b=map(float,DEPTH["items"][i]["source_range_seconds"]);q=math.sin(math.tau*((t-a)/2.0))*float(DEPTH["derivation"]["production_amplitude"])
 yy,xx=np.mgrid[0:720,0:1280].astype(np.float32);f=fields[i]
 return cv2.remap(frame,(xx+f[...,0]*q).astype(np.float32),(yy+f[...,1]*q).astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)
def stack(frame,t,fields):
 out=depth(frame,t,fields);e=energy_at(t);tr=transient_at(t)
 for eid,s in active(t):
  p=apply_effect(ID_TO_NAME[eid],out,t=t,duration=8.0,energy=e,transient=tr)
  out=cv2.addWeighted(out,1-clamp(s),p,clamp(s),0)
 return out
def probe(p):
 c=cv2.VideoCapture(str(p));fps=c.get(cv2.CAP_PROP_FPS);w=int(c.get(cv2.CAP_PROP_FRAME_WIDTH));h=int(c.get(cv2.CAP_PROP_FRAME_HEIGHT));n=int(c.get(cv2.CAP_PROP_FRAME_COUNT));c.release();dur=n/max(fps,1e-6)
 if abs(fps-24)>.01 or (w,h)!=(1280,720) or abs(dur-244.68)>.10:raise RuntimeError(f"source mismatch {fps} {w}x{h} {dur:.3f}")
 return fps
def render(source,start,duration,out,fields):
 fps=probe(source);c=cv2.VideoCapture(str(source));c.set(cv2.CAP_PROP_POS_MSEC,start*1000);total=round(duration*fps)
 cmd=["ffmpeg","-y","-hide_banner","-loglevel","error","-f","rawvideo","-pix_fmt","bgr24","-s","1280x720","-r","24","-i","-","-an","-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(out)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for n in range(total):
  ok,fr=c.read()
  if not ok:raise RuntimeError(f"read failed {start+n/fps:.3f}")
  p.stdin.write(stack(fr,start+n/fps,fields).tobytes())
 c.release();p.stdin.close()
 if p.wait()!=0:raise RuntimeError("encode failed")
def main():
 a=argparse.ArgumentParser();a.add_argument("--source",type=Path,required=True);a.add_argument("--out-dir",type=Path,required=True);a.add_argument("--depth-dir",type=Path);a.add_argument("--start",type=float,default=0.0);a.add_argument("--duration",type=float,default=244.68);z=a.parse_args();z.out_dir.mkdir(parents=True,exist_ok=True);fields=load_fields(z.depth_dir);out=z.out_dir/f"segment_{z.start:.3f}_{z.duration:.3f}.mp4";render(z.source,z.start,z.duration,out,fields);print(out)
if __name__=="__main__":main()
