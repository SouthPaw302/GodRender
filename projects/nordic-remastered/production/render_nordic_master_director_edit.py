#!/usr/bin/env python3
"""Nordic Remastered RC1 reproducible source-locked master editorial assembly.
This script preserves already-approved batch FX and builds bounded source-image
portal mattes at three joins. It does NOT attest a native full-master FXExecutor pass.
"""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
import cv2
import numpy as np

NAMES = {
 "B01":"NORDIC_B01_MASTER_DIRECTOR_FX01_720p.mp4",
 "B02":"NORDIC_B02_DIRECTOR_EDIT_FX_720p.mp4",
 "GEMINI_A_ORIGINAL":"gemini_generated_video_4b4db55f.mp4",
 "B03":"NORDIC_B03_DIRECTOR_EDIT_FX_720p.mp4",
 "GEMINI_B_ORIGINAL":"gemini_generated_video_e4937f10.mp4",
 "B04":"NORDIC_B04_DIRECTOR_EDIT_FX_720p.mp4",
 "B05":"NORDIC_B05_DIRECTOR_EDIT_FX_720p.mp4",
 "B06":"NORDIC_B06_DIRECTOR_EDIT_FX_720p.mp4",
}
MATTE_FRAMES={"GEMINI_A_ORIGINAL":12,"B03":10,"GEMINI_B_ORIGINAL":12}
FPS,W,H=24,1280,720

def sha256(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def portal_matte(previous,incoming,i,n):
 p=(1-math.cos(math.pi*(i+1)/(n+1)))/2
 yy,xx=np.ogrid[:H,:W]
 cx,cy=.51*W,.49*H
 r=np.sqrt((xx-cx)**2+(yy-cy)**2)
 rmax=math.hypot(cx,cy)+.48*math.hypot(W-cx,H-cy)
 threshold=-18+(rmax+180)*p
 mask=np.clip((threshold-r+3)/6,0,1).astype(np.float32)[...,None]
 return np.clip(previous.astype(np.float32)*(1-mask)+incoming.astype(np.float32)*mask,0,255).astype(np.uint8)

def run(args):
 project=Path(__file__).resolve().parents[1]
 manifest=json.loads((project/"production/MASTER_DIRECTOR_EDIT_FX_ASSEMBLY_RC1.json").read_text())
 inputs=Path(args.media_dir);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
 entries=manifest["source_sections"]
 assert sum(s["frames"] for s in entries)==3311
 assert sha256(args.song)==manifest["audio_sha256"],"source song hash mismatch"
 for e in entries:
  f=inputs/NAMES[e["name"]]
  assert f.is_file() and sha256(f)==e["sha256"],"source hash mismatch: "+e["name"]
  c=cv2.VideoCapture(str(f))
  assert c.isOpened() and int(c.get(cv2.CAP_PROP_FRAME_COUNT))==e["frames"]
  assert abs(c.get(cv2.CAP_PROP_FPS)-24)<.02
  assert int(c.get(cv2.CAP_PROP_FRAME_WIDTH))==W and int(c.get(cv2.CAP_PROP_FRAME_HEIGHT))==H
  c.release()
 silent=out/"NORDIC_MASTER_DIRECTOR_PICTURE_720p_silent.mp4"
 final=out/"NORDIC_REMASTERED_DIRECTOR_MASTER_FX_RC1_720p.mp4"
 command=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
  "-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(FPS),
  "-i","-","-an","-c:v","libx264","-preset","ultrafast","-crf","17",
  "-pix_fmt","yuv420p","-movflags","+faststart",str(silent)]
 proc=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 prior=None;count=0
 try:
  for entry in entries:
   name=entry["name"];cap=cv2.VideoCapture(str(inputs/NAMES[name]))
   for i in range(entry["frames"]):
    ok,frame=cap.read()
    if not ok:raise RuntimeError(f"short source {name}/{i}")
    if name.startswith("GEMINI_"):frame=cv2.convertScaleAbs(frame,alpha=1.012,beta=-0.8)
    if prior is not None and i<MATTE_FRAMES.get(name,0):
     frame=portal_matte(prior,frame,i,MATTE_FRAMES[name])
    proc.stdin.write(np.ascontiguousarray(frame).tobytes())
    if i==entry["frames"]-1:last=frame.copy()
    count+=1
   prior=last;cap.release()
  proc.stdin.close()
  error=proc.stderr.read().decode()
  if proc.wait():raise RuntimeError(error[-3000:])
 except BaseException:
  proc.kill()
  raise
 assert count==3311
 command=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
  "-i",str(silent),"-i",str(args.song),"-map","0:v:0","-map","1:a:0",
  "-c:v","copy","-c:a","aac","-b:a","256k","-ar","48000","-ac","2",
  "-t",f"{3311/24:.9f}","-movflags","+faststart",str(final)]
 done=subprocess.run(command,capture_output=True,text=True)
 if done.returncode:raise RuntimeError(done.stderr[-3000:])
 decoded=subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(final),
  "-map","0:v","-f","null","-","-map","0:a","-f","null","-"],
  capture_output=True,text=True)
 if decoded.returncode:raise RuntimeError(decoded.stderr[-3000:])
 receipt={"schema":"godrender.nordic-master-director-edit.v1",
  "status":"MASTER_ASSEMBLY_TECHNICAL_PASS_NOT_NATIVE_MASTER_FX_GATE",
  "frames":count,"fps":FPS,"duration_seconds":count/FPS,
  "audio_source_sha256":sha256(args.song),"film_sha256":sha256(final),
  "film_bytes":final.stat().st_size,"section_count":len(entries),
  "native_fx_executor_master_pass":False}
 (out/"master_render_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
 print(json.dumps(receipt,indent=2))

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--media-dir",required=True,help="sandbox-staged original B01/B02/Gemini A/B and accepted B03-B06 outputs")
 p.add_argument("--song",required=True)
 p.add_argument("--out",required=True)
 run(p.parse_args())
