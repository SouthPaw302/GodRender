#!/usr/bin/env python3
"""Nordic B06 source-locked Director edit — native FX runner."""
import argparse, hashlib, json, subprocess, sys, zipfile
from pathlib import Path
import cv2
import numpy as np

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
from general.reusable.fx_v2.executor import FXExecutor
from general.reusable.fx_v2.runtime import FXContext

FPS, W, H = 24, 1280, 720

def sha256(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def verify(p, expected):
    if sha256(p) != expected:
        raise RuntimeError("SOURCE HASH MISMATCH: " + str(p))

def source_light(frame, sid, progress):
    """Illuminate only original bright source pixels; never replace identities."""
    if sid == "B06_05":
        return frame
    yy, xx = np.ogrid[:H, :W]
    if sid in ("B06_03", "B06_04"):
        cx, cy, rx, ry = .70, .39, .33, .38
    else:
        cx, cy, rx, ry = .52, .49, .39, .49
    roi = (((xx-W*cx)/(W*rx))**2 + ((yy-H*cy)/(H*ry))**2 < 1).astype(np.float32)
    luminance = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY).astype(np.float32)
    m = cv2.GaussianBlur(np.clip((luminance-170)/65,0,1)*roi,(0,0),6)
    m *= (.048+.012*np.sin(2*np.pi*progress))
    return np.uint8(np.clip(frame.astype(np.float32)*(1+m[:,:,None]),0,255))

def run(args):
    m = json.loads(Path(args.manifest).read_text())
    if m["schema"] != "godrender.nordic-b06-director-edit-fx.v1":
        raise RuntimeError("invalid B06 manifest")
    if m["total_frames"] != 567 or sum(int(x["frames"]) for x in m["timeline"]) != 567:
        raise RuntimeError("bad 567 frame timeline")
    if sum(int(x["frames"]) for x in m["timeline"][:-1]) != 376:
        raise RuntimeError("wrong outro boundary")
    verify(args.storyboard_zip,m["source_zip"]["sha256"])
    verify(args.video_b,m["source_video_b"]["sha256"])
    verify(args.audio,m["audio"]["sha256"])
    with zipfile.ZipFile(args.storyboard_zip) as z:
        source_manifest=json.loads(z.read("manifest.json"))
        if len(source_manifest["shots"]) != 10:
            raise RuntimeError("wrong canonical source still count")
        for s in m["selected_stills"]:
            if hashlib.sha256(z.read(s["file"])).hexdigest() != s["sha256"]:
                raise RuntimeError("B06 ZIP still SHA mismatch: "+s["id"])
    stills={}
    for s in m["selected_stills"]:
        p=Path(args.input_root)/s["file"]
        if not p.is_file():
            raise RuntimeError("missing still: "+str(p))
        verify(p,s["sha256"])
        img=cv2.imread(str(p))
        if img is None or img.shape[:2]!=(H,W):
            raise RuntimeError("bad still dimensions: "+s["id"])
        stills[s["id"]]=img
    fx=FXExecutor(consumer="nordic_b06_director_edit_fx")
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    silent=out/"b06_silent.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y","-f","rawvideo",
         "-pix_fmt","bgr24","-s",f"{W}x{H}","-r","24","-i","-","-an",
         "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p",
         "-movflags","+faststart",str(silent)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    count=0
    cuts=[]
    bridge_sources=[]
    try:
        for segment in m["timeline"]:
            typ,sid,n=segment["type"],segment["id"],int(segment["frames"])
            if typ in ("still","quiet_hold"):
                img=stills[sid]
                for i in range(n):
                    progress=(i+1)/max(n,1)
                    ctx=FXContext(t=i/24,duration=n/24,frame_index=i,fps=24,
                                  energy=.10 if typ=="quiet_hold" else .43,transient=.03)
                    frame=fx.apply_frame("FX2-CAMERA-023",img,ctx,params=segment["camera"])
                    frame=source_light(frame,sid,progress)
                    if i==0 and count: cuts.append(count)
                    proc.stdin.write(np.ascontiguousarray(frame).tobytes())
                    count+=1
            elif typ=="source_video_bridge":
                cap=cv2.VideoCapture(str(args.video_b))
                native_fps=cap.get(cv2.CAP_PROP_FPS)
                if abs(native_fps-FPS)>.02:
                    raise RuntimeError("Gemini video source cadence is not 24fps")
                t=float(segment["source_start_seconds"])
                cap.set(cv2.CAP_PROP_POS_FRAMES,round(t*FPS))
                for i in range(n):
                    ok,frame=cap.read()
                    if not ok or frame.shape[:2]!=(H,W):
                        raise RuntimeError("source bridge ended or shape changed")
                    if i==0: cuts.append(count)
                    proc.stdin.write(np.ascontiguousarray(frame).tobytes())
                    count+=1
                cap.release()
                bridge_sources.append({"source_time":t,"frames":n,"natural_speed":True})
            else:
                raise RuntimeError("unknown B06 timeline segment "+typ)
        proc.stdin.close()
        err=proc.stderr.read().decode()
        status=proc.wait()
        if status:
            raise RuntimeError("FFmpeg failed: "+err[-2000:])
    finally:
        if proc.poll() is None:
            if not proc.stdin.closed: proc.stdin.close()
            proc.wait()
    if count!=567:
        raise RuntimeError("B06 decoded frame count mismatch "+str(count))
    final=out/"NORDIC_B06_DIRECTOR_EDIT_FX_720p.mp4"
    duration=567/24
    mux=subprocess.run([
        "ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
        "-i",str(silent),"-ss",str(m["audio"]["offset_seconds"]),"-i",str(args.audio),
        "-map","0:v:0","-map","1:a:0","-t",f"{duration:.9f}",
        "-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",str(final)
    ],capture_output=True,text=True)
    if mux.returncode:
        raise RuntimeError("audio mux failed: "+mux.stderr[-2500:])
    receipt={
        "schema":"godrender.nordic-b06-director-edit-fx.receipt.v1",
        "status":"TECHNICAL_RENDER_PASS_DIRECTOR_REVIEW_REQUIRED",
        "project":m["project"],"batch":"B06","editorial_cut":m["editorial_cut"],
        "frames":count,"fps":24,"duration_seconds":duration,
        "source_zip_sha256":m["source_zip"]["sha256"],
        "source_video_b_sha256":m["source_video_b"]["sha256"],
        "audio_sha256":m["audio"]["sha256"],
        "selected_stills":[s["id"] for s in m["selected_stills"]],
        "natural_speed_video_bridges":bridge_sources,
        "outro_starts_local_frame":376,"camera_fx":"FX2-CAMERA-023",
        "localized_light":"source_luminance_only","cut_frames":cuts,
        "film_sha256":sha256(final),"film_bytes":final.stat().st_size,
        "master_fx":"DEFERRED"
    }
    (out/"render_receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for arg in ("manifest","input-root","storyboard-zip","video-b","audio","out"):
        p.add_argument("--"+arg,required=True)
    run(p.parse_args())
