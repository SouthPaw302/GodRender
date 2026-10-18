#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, subprocess, zipfile
from pathlib import Path
import cv2
import numpy as np

FPS=24.0
W,H=1280,720
DURATION=244.68
EXPECTED_AUDIO_SHA='76679c5e0d0c905635e80904ff67ba03b52c11893d3a71f09433e17feff0f962'
SECTIONS=[(0,18),(18,42),(42,77),(77,95),(95,110),(110,122),(122,137),(137,167),(167,187),(187,210),(210,233),(233,DURATION)]
TRANS_FRAMES=[18,18,18,18,18,18,18,18,18,4,4]


def smooth(x):
    x=max(0.0,min(1.0,float(x))); return x*x*(3-2*x)

def sha256(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def reconstruct_audio(parts:Path,out:Path):
    files=sorted(parts.glob('part-*'))
    if len(files)!=66: raise RuntimeError(f'expected 66 audio parts, found {len(files)}')
    with out.open('wb') as w:
        for p in files: w.write(p.read_bytes())
    got=sha256(out)
    if got!=EXPECTED_AUDIO_SHA: raise RuntimeError(f'audio sha mismatch {got}')

def load_frames(media_zip:Path,work:Path):
    with zipfile.ZipFile(media_zip) as z: z.extractall(work)
    imgs=[]
    for i in range(1,13):
        candidates=list(work.rglob(f'still_{i:02d}_moved.jpg'))
        if not candidates: raise RuntimeError(f'missing still {i:02d}')
        im=cv2.imread(str(candidates[0]))
        if im is None: raise RuntimeError(f'unreadable {candidates[0]}')
        if im.shape[1]!=W or im.shape[0]!=H: im=cv2.resize(im,(W,H),interpolation=cv2.INTER_CUBIC)
        imgs.append(im)
    return imgs

def motion(im,phase,idx):
    # Deterministic, bounded Ken-Burns style movement. No topology warping.
    p=smooth(phase)
    z0,z1=((1.018,1.065) if idx%2==0 else (1.06,1.022))
    z=z0+(z1-z0)*p
    nw,nh=int(W*z),int(H*z)
    big=cv2.resize(im,(nw,nh),interpolation=cv2.INTER_CUBIC)
    maxx,maxy=nw-W,nh-H
    dirs=[(-1,-.2),(1,.15),(.3,-1),(-.4,1),(1,-.5),(-1,.5)]
    dx,dy=dirs[idx%len(dirs)]
    cx=maxx/2 + dx*maxx*.30*(2*p-1)
    cy=maxy/2 + dy*maxy*.26*(2*p-1)
    x=int(max(0,min(maxx,cx))); y=int(max(0,min(maxy,cy)))
    fr=big[y:y+H,x:x+W].copy()
    # Very mild breathing exposure and vignette; identity remains unchanged.
    gain=0.985+0.025*math.sin((p*math.pi*2)+(idx*.73))
    fr=np.clip(fr.astype(np.float32)*gain,0,255).astype(np.uint8)
    yy,xx=np.mgrid[0:H,0:W]
    r=((xx-W/2)/(W*.72))**2+((yy-H/2)/(H*.78))**2
    mask=np.clip(1.0-0.10*r,0.88,1.0).astype(np.float32)[...,None]
    return np.clip(fr.astype(np.float32)*mask,0,255).astype(np.uint8)

def frame_at(imgs,t):
    idx=11
    for i,(a,b) in enumerate(SECTIONS):
        if a<=t<b or (i==11 and t<=b): idx=i; break
    a,b=SECTIONS[idx]; phase=(t-a)/max(.001,b-a)
    cur=motion(imgs[idx],phase,idx)
    if idx<11:
        ntrans=TRANS_FRAMES[idx]; td=ntrans/FPS
        if t>=b-td:
            q=(t-(b-td))/td
            nxt=motion(imgs[idx+1],q,idx+1)
            q=smooth(q)
            cur=cv2.addWeighted(cur,1-q,nxt,q,0)
    return cur

def render(imgs,silent:Path):
    total=round(DURATION*FPS)
    cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r','24','-i','-','-an','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(silent)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for n in range(total):
        fr=frame_at(imgs,n/FPS)
        p.stdin.write(fr.tobytes())
    p.stdin.close(); rc=p.wait()
    if rc: raise RuntimeError(f'ffmpeg video encode failed {rc}')

def mux(silent:Path,audio:Path,final:Path):
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(silent),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','320k','-t',f'{DURATION:.3f}','-movflags','+faststart',str(final)],check=True)

def probe(p:Path):
    raw=subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)])
    return json.loads(raw)

def contact(final:Path,out:Path):
    reps=[2,22,56,77,103,115,123,149,167,196,216,240]
    thumbs=[]
    cap=cv2.VideoCapture(str(final))
    for t in reps:
        cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,fr=cap.read()
        if not ok: raise RuntimeError(f'contact read failed at {t}s')
        fr=cv2.resize(fr,(320,180)); cv2.putText(fr,f'{t}s',(8,22),cv2.FONT_HERSHEY_SIMPLEX,.65,(255,255,255),2,cv2.LINE_AA); thumbs.append(fr)
    cap.release()
    sheet=np.vstack([np.hstack(thumbs[i:i+4]) for i in range(0,12,4)])
    cv2.imwrite(str(out),sheet,[int(cv2.IMWRITE_JPEG_QUALITY),90])

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--project',type=Path,default=Path('projects/ironflame-cleanroom')); ap.add_argument('--out-dir',type=Path,default=Path('render_out')); args=ap.parse_args()
    pr=args.project; out=args.out_dir; out.mkdir(parents=True,exist_ok=True)
    audio=out/'Ironflame-master.wav'; reconstruct_audio(pr/'assets/audio/canonical-wav.parts',audio)
    work=out/'media'; work.mkdir(exist_ok=True)
    imgs=load_frames(pr/'assets/visual/reference_movement_pack.zip',work)
    silent=out/'ironflame_silent.mp4'; final=out/'IronFlame-reference-cut.mp4'
    render(imgs,silent); mux(silent,audio,final)
    info=probe(final)
    dur=float(info['format']['duration']); streams=info['streams']
    vs=next(s for s in streams if s['codec_type']=='video'); au=next(s for s in streams if s['codec_type']=='audio')
    qc={'schema':'aivideoedit.final-qc.v1','result':'PASS','duration_seconds':dur,'expected_duration_seconds':DURATION,'duration_delta':abs(dur-DURATION),'video':{'codec':vs['codec_name'],'width':vs['width'],'height':vs['height'],'r_frame_rate':vs['r_frame_rate']},'audio':{'codec':au['codec_name'],'sample_rate':au.get('sample_rate')},'source_audio_sha256':sha256(audio),'final_sha256':sha256(final),'visual_sections':12,'reference_timing_authority':'movement-variant manifest / source reference'}
    if abs(dur-DURATION)>.20 or vs['width']!=W or vs['height']!=H or vs['r_frame_rate']!='24/1': qc['result']='FAIL'; (out/'qc.json').write_text(json.dumps(qc,indent=2)); raise RuntimeError('QC failed')
    (out/'qc.json').write_text(json.dumps(qc,indent=2)); contact(final,out/'contact_sheet.jpg')
    (out/'SHA256SUMS.txt').write_text(f"{sha256(final)}  {final.name}\n{sha256(out/'contact_sheet.jpg')}  contact_sheet.jpg\n{sha256(out/'qc.json')}  qc.json\n")
    print(json.dumps(qc,indent=2))
if __name__=='__main__': main()
