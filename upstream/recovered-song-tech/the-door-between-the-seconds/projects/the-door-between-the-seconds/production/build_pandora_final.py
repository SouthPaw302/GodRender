#!/usr/bin/env python3
from __future__ import annotations
import json, math, os, subprocess, sys, wave, hashlib
from pathlib import Path
import cv2
import numpy as np
import importlib.util

ROOT = Path('/mnt/data/AIVideoEdit_local/projects/the-door-between-the-seconds')
REPO = ROOT.parents[1]
CREATED = ROOT/'resume_payload/created_images_jpg'
REFS = ROOT/'resume_payload/reference_images_jpg'
COLD = ROOT/'resume_payload/video/gothic_window_8s_fullscreen_720p.mp4'
REPASS = ROOT/'resume_payload/video/The_Door_Between_the_Seconds_REPASS_FAST_540p.mp4'
OUTDIR = ROOT/'production/final_pandora_v2_gate'
FX_MANIFEST = ROOT/'FX_REQUIREMENTS.fx.json'
FX_LOCK = ROOT/'fx.lock.json'
FX_GATE = REPO/'general/reusable/fx_v2/precompile_gate.py'
FX_RUNTIME_PATH = REPO/'general/reusable/fx_v2/runtime.py'
# Current-main rule: no production pixels without a live-valid FX lock.
subprocess.run([sys.executable,str(FX_GATE),'--manifest',str(FX_MANIFEST),'--verify-lock',str(FX_LOCK)],check=True)
spec=importlib.util.spec_from_file_location('aivideoedit_fx_runtime',FX_RUNTIME_PATH)
if spec is None or spec.loader is None: raise RuntimeError('cannot load canonical FX runtime')
fxmod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=fxmod; spec.loader.exec_module(fxmod)
FX=fxmod.FXRuntime(seed=302)
OUTDIR.mkdir(parents=True, exist_ok=True)
W,H,FPS = 960,540,30
YY,XX=np.mgrid[0:H,0:W].astype(np.float32)
# Precomputed deterministic atmosphere seeds (avoid per-frame RNG construction).
_rng_r=np.random.default_rng(302); RAIN_X=_rng_r.integers(-W//4,W+W//4,48); RAIN_Y=_rng_r.integers(-H,H,48); RAIN_SP=_rng_r.integers(10,23,48); RAIN_LN=_rng_r.integers(12,28,48)
_rng_e=np.random.default_rng(913); EMBERS=[(int(_rng_e.uniform(0,W)),int(_rng_e.uniform(0,H)),float(_rng_e.uniform(.5,1.7)),float(_rng_e.uniform(0,6.28))) for _ in range(34)]
_rng_p=np.random.default_rng(1407); PETALS=[(float(_rng_p.uniform(0,W)),float(_rng_p.uniform(-H,H)),float(_rng_p.uniform(.6,1.3)),float(_rng_p.uniform(0,6.28))) for _ in range(18)]
SCRIPT = json.loads((ROOT/'SCRIPT.json').read_text())
TOTAL = SCRIPT['total_frames']
CHUNK_FROM=os.environ.get('CHUNK_FROM')
CHUNK_TO=os.environ.get('CHUNK_TO')
entries_all=SCRIPT['entries']
if CHUNK_FROM:
    ids=[e['shot_id'] for e in entries_all]
    a=ids.index(CHUNK_FROM); b=ids.index(CHUNK_TO or CHUNK_FROM)
    selected_entries=entries_all[a:b+1]
    CHUNK_MODE=True
else:
    selected_entries=entries_all
    CHUNK_MODE=False

SUPPORT = {
 'S04':'rainlit_gothic_aristocrat_at_the_window.jpg',
 'S07':'gothic_velvet_candlelit_chamber.jpg',
 'S13':'gothic_rainfall_by_candlelight.jpg',
 'S21':'moonlit_gothic_velvet_reverie.jpg',
 'S29':'gothic_crypt_empress_in_morning_light.jpg',
 'S30':'gothic_dawn_in_the_cathedral_of_roses.jpg',
 'S32':'moonlit_gothic_rose_chamber.jpg',
}

# Six unique-looking recovered reference stills for sub-second memory flashes.
ref_files = sorted(REFS.glob('*.jpg'))[:6]
REF_FLASH_SHOTS = {'S10':0,'S14':1,'S22':2,'S27':3,'S30':4,'S33':5}
# Shot-specific crops derived from existing media. These are not new images; they
# deliberately reveal architecture/objects so Pandora does not occupy every shot.
CUSTOM_ROI = {
 'S01':(.45,.00,1.00,.62),
 'S07':(.54,.03,.99,.96),
 'S11':(.12,.02,.96,.98),
 'S12':(.56,.00,.99,.92),
 'S16':(.50,.00,.99,.90),
 'S19':(.62,.00,.98,.68),
 'S20':(.48,.00,.99,.94),
 'S29':(.12,.00,.98,.86),
 'S30':(.40,.00,.99,.72),
 'S31':(.28,.00,.92,.82),
 'S32':(.00,.46,.58,.99),
}

AUDIO_WAV = OUTDIR/'song_audio.wav'
if not AUDIO_WAV.exists():
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(REPASS),'-vn','-ac','2','-ar','48000','-c:a','pcm_s16le',str(AUDIO_WAV)],check=True)

# Frame-aligned RMS envelope, used only after t=6s.
with wave.open(str(AUDIO_WAV),'rb') as wf:
    sr=wf.getframerate(); ch=wf.getnchannels(); n=wf.getnframes()
    pcm=np.frombuffer(wf.readframes(n),dtype=np.int16).reshape(-1,ch).astype(np.float32)/32768.0
mono=pcm.mean(axis=1)
energy=np.zeros(TOTAL,np.float32)
for f in range(180,TOTAL):
    t=(f-180)/FPS
    a=int(t*sr); b=min(len(mono),a+int(sr/FPS))
    if b>a: energy[f]=float(np.sqrt(np.mean(mono[a:b]**2)+1e-9))
if energy.max()>0:
    lo,hi=np.percentile(energy[180:],[20,98]); energy=np.clip((energy-lo)/(hi-lo+1e-6),0,1)
# transient proxy
trans=np.zeros_like(energy); trans[1:]=np.maximum(0,energy[1:]-energy[:-1]);
if trans.max()>0: trans=np.clip(trans/(np.percentile(trans[trans>0],95)+1e-6),0,1)


def sha256(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()


def cover(im, w=W, h=H, y_bias=0.33, preserve_subject=True):
    ih,iw=im.shape[:2]
    target=w/h
    src=iw/max(1,ih)
    # For portrait/tall sources, preserve full subject height and build a full-screen
    # blurred extension background instead of over-cropping heads/legs out of frame.
    if preserve_subject and src < target*0.92:
        fg_scale=h/ih
        fg_w=max(1,int(round(iw*fg_scale)))
        fg=cv2.resize(im,(fg_w,h),interpolation=cv2.INTER_LANCZOS4 if fg_scale>1 else cv2.INTER_AREA)
        bg_scale=max(w/iw,h/ih)
        bg_w=max(w,int(round(iw*bg_scale))); bg_h=max(h,int(round(ih*bg_scale)))
        bg=cv2.resize(im,(bg_w,bg_h),interpolation=cv2.INTER_LANCZOS4 if bg_scale>1 else cv2.INTER_AREA)
        bx=max(0,(bg_w-w)//2); by=max(0,int((bg_h-h)*max(0,min(1,y_bias))))
        bg=bg[by:by+h,bx:bx+w].copy()
        bg=cv2.GaussianBlur(bg,(0,0),sigmaX=18,sigmaY=18)
        bg=(bg.astype(np.float32)*0.72).astype(np.uint8)
        x=(w-fg_w)//2
        if x>=0:
            out=bg
            out[:,x:x+fg_w]=fg
            # soften the seam between foreground and extended background
            seam=min(30,max(12,fg_w//24))
            if x>0:
                left=out[:,x:x+seam].astype(np.float32)
                left_bg=bg[:,x:x+seam].astype(np.float32)
                a=np.linspace(0.0,1.0,seam,dtype=np.float32)[None,:,None]
                out[:,x:x+seam]=np.clip(left_bg*(1-a)+left*a,0,255).astype(np.uint8)
            if x+fg_w<w:
                right=out[:,x+fg_w-seam:x+fg_w].astype(np.float32)
                right_bg=bg[:,x+fg_w-seam:x+fg_w].astype(np.float32)
                a=np.linspace(1.0,0.0,seam,dtype=np.float32)[None,:,None]
                out[:,x+fg_w-seam:x+fg_w]=np.clip(right_bg*(1-a)+right*a,0,255).astype(np.uint8)
            return out
    scale=max(w/iw,h/ih)
    nw,nh=max(w,int(round(iw*scale))),max(h,int(round(ih*scale)))
    r=cv2.resize(im,(nw,nh),interpolation=cv2.INTER_LANCZOS4 if scale>1 else cv2.INTER_AREA)
    x=max(0,(nw-w)//2)
    extra=max(0,nh-h)
    y=int(extra*max(0,min(1,y_bias)))
    return r[y:y+h,x:x+w].copy()


def load_still(name,y_bias=0.33):
    p=CREATED/name
    im=cv2.imread(str(p),cv2.IMREAD_COLOR)
    if im is None: raise FileNotFoundError(p)
    return cover(im,y_bias=y_bias,preserve_subject=True),p

def load_shot_still(e):
    p=CREATED/e['visual_media']
    im=cv2.imread(str(p),cv2.IMREAD_COLOR)
    if im is None: raise FileNotFoundError(p)
    roi=CUSTOM_ROI.get(e['shot_id'])
    if roi:
        h,w=im.shape[:2]; x0,y0,x1,y1=roi
        im=im[int(y0*h):max(int(y0*h)+1,int(y1*h)), int(x0*w):max(int(x0*w)+1,int(x1*w))]
    yb=.24 if 'portrait' in e['animation_behavior'] or 'vampire' in e['animation_behavior'] else .33
    preserve=False if roi else True
    return cover(im,y_bias=yb,preserve_subject=preserve),p


def vignette(im, amount=.20):
    x=(XX-W/2)/(W/2); y=(YY-H/2)/(H/2)
    m=np.clip(1-amount*(x*x+y*y),0.62,1)[...,None]
    return np.clip(im.astype(np.float32)*m,0,255).astype(np.uint8)


def precompose(base, profile):
    out=base.copy()
    if profile == 'mirror_corridor':
        # Keep Pandora in a real corridor; use narrow side echoes instead of cloning her body.
        out=base.copy()
        sw=max(24,W//10)
        left=cv2.flip(base[:, :sw],1)
        right=cv2.flip(base[:, -sw:],1)
        out[:, :sw]=cv2.addWeighted(out[:, :sw],.72,left,.28,0)
        out[:, -sw:]=cv2.addWeighted(out[:, -sw:],.72,right,.28,0)
    elif profile == 'hallway_repeat':
        # Source is already an architecture-only crop. Build nested depth, not side-by-side people.
        out=base.copy()
        for k,scale in enumerate((0.82,0.64,0.48),1):
            nw=max(2,int(W*scale)); nh=max(2,int(H*scale))
            small=cv2.resize(base,(nw,nh),interpolation=cv2.INTER_AREA)
            x=(W-nw)//2; y=(H-nh)//2
            alpha=0.20/(k**0.55)
            roi=out[y:y+nh,x:x+nw]
            out[y:y+nh,x:x+nw]=cv2.addWeighted(roi,1-alpha,small,alpha,0)
    elif profile in {'temporal_echo','portrait_echo','reach_echo'}:
        out=base.astype(np.float32)
        flip=cv2.flip(base,1).astype(np.float32)
        M1=np.float32([[1,0,-28],[0,1,0]])
        M2=np.float32([[1,0,30],[0,1,0]])
        a=cv2.warpAffine(base,M1,(W,H),borderMode=cv2.BORDER_REFLECT_101).astype(np.float32)
        b=cv2.warpAffine(flip,M2,(W,H),borderMode=cv2.BORDER_REFLECT_101).astype(np.float32)
        out=np.clip(out*.67+a*.19+b*.14,0,255).astype(np.uint8)
    elif profile in {'reflection_echo','rain_reflection'}:
        # vertical mirror through a narrow interior seam
        flip=cv2.flip(base,1)
        out=np.clip(base.astype(np.float32)*.76+flip.astype(np.float32)*.24,0,255).astype(np.uint8)
        cv2.line(out,(W//2,0),(W//2,H),(190,160,150),1,cv2.LINE_AA)
    elif profile in {'depth_gate','cathedral_push','cathedral_impact'}:
        # tunnel-like side repeats while preserving central image
        left=cv2.resize(base[:, :W//2],(W//5,H))
        right=cv2.flip(cv2.resize(base[:, W//2:],(W//5,H)),1)
        mid=cv2.resize(base,(W-2*(W//5),H))
        out=np.hstack([left,mid,right])
    elif profile=='gravity_flip':
        out=base
    elif profile in {'crypt_dawn','silent_light','dawn_bloom'}:
        out=base
    return vignette(out,.16)


def camera(im, q, profile, e, tr):
    # q = 0..1 inside shot. Motion profile changes amplitude and direction.
    amp=1.0
    if profile in {'final_stillness','silent_light'}: amp=max(0.08,1-q*0.88)
    if profile in {'cathedral_impact','departure_drive'}: amp=1.55
    if profile in {'shadow_breath','portrait_echo','vampire_portrait'}: amp=.72
    pan=10.5*amp
    dx=math.sin(q*math.tau + (0.8 if 'reverse' in profile else 0))*pan
    dy=math.sin(q*math.tau*0.7+1.1)*4.2*amp
    if profile=='reverse_drift': dx=16*(q-.5)
    # bounded authored impact sway derived from music transients, not random handheld shake
    impact=(tr*2.0-1.0) if tr>0 else 0.0
    if profile in {'cathedral_impact','departure_drive','rain_push','doorway_drift'}:
        dx += math.sin(q*math.pi*8.0+0.6)*2.8*tr
        dy += math.sin(q*math.pi*9.5+1.1)*2.0*tr
    wide_profiles={'cathedral_push','cathedral_impact','depth_gate','dawn_bloom','crypt_dawn','silent_light','mirror_corridor','hallway_repeat'}
    portrait_profiles={'portrait_echo','vampire_portrait','shadow_breath','soft_contact'}
    zoom=1.020 + (0.022 if profile in wide_profiles else 0.012)*math.sin(q*math.pi)**2
    if profile in portrait_profiles: zoom=1.015 + 0.010*math.sin(q*math.pi)**2
    zoom += .008*e
    angle=math.sin(q*math.tau)*.32*amp + (0.7*math.sin(q*math.pi*7.0))*tr if profile in {'cathedral_impact','departure_drive'} else math.sin(q*math.tau)*.32*amp
    if profile=='gravity_flip':
        # impossible tilt: accelerate to 12 degrees, cross through inversion impression via vflip at midpoint
        angle=12*math.sin(q*math.pi)
        if .46<q<.60: im=cv2.flip(im,-1)
    M=cv2.getRotationMatrix2D((W/2,H/2),angle,zoom)
    M[0,2]+=dx; M[1,2]+=dy
    return cv2.warpAffine(im,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)


def add_rain(im, frame, strength=.22):
    out=im.copy(); layer=np.zeros_like(out)
    for x0,y0,s,l in zip(RAIN_X,RAIN_Y,RAIN_SP,RAIN_LN):
        y=int((y0+frame*s)%(H+100)-50); x=int((x0+frame*1.4)%(W+100)-50)
        cv2.line(layer,(x,y),(x+5,y+l),(150,165,185),1,cv2.LINE_AA)
    return cv2.addWeighted(out,1,layer,strength,0)


def add_embers(im, frame, e, strength=.42):
    out=im.copy(); layer=np.zeros_like(out)
    for i,(x0,y0,sp,phase) in enumerate(EMBERS):
        y=int((y0-frame*sp*2.2) % (H+30)-15); x=int((x0+math.sin(frame*.04+phase)*18)%W)
        rad=1+(i%9==0); c=int(130+100*min(1,e+.2))
        cv2.circle(layer,(x,y),rad,(20,80,c),-1,cv2.LINE_AA)
    return cv2.addWeighted(out,1,layer,strength*(.55+.65*e),0)


def add_petals(im, frame, strength=.40):
    out=im.copy(); layer=np.zeros_like(out)
    for i,(x0,y0,sp,ph) in enumerate(PETALS):
        y=int((y0+frame*sp*1.7)%(H+40)-20); x=int((x0+math.sin(frame*.025+ph)*24)%W)
        cv2.ellipse(layer,(x,y),(3+(i%4),2),int((frame*2+i*17)%180),0,360,(24,34,145),-1,cv2.LINE_AA)
    return cv2.addWeighted(out,1,layer,strength,0)


def add_light(im, q, e, tr, profile):
    out=im.astype(np.float32)
    pulse=1.0 + .025*math.sin(q*math.tau*2.0) + .035*e + .06*tr
    if profile=='quiet_thunder':
        # sporadic silent lightning driven by deterministic narrow pulses
        flash=max(0,math.sin(q*math.pi*7))**16
        pulse += .20*flash
        out[:,:,0]*=.96; out[:,:,2]*=1.03
    if profile in {'dawn_bloom','crypt_dawn','silent_light','final_stillness'}:
        cx=W*(.78-.10*q); cy=H*.18
        dist=((XX-cx)/(W*.55))**2+((YY-cy)/(H*.8))**2
        halo=np.exp(-dist*2.2)[...,None]
        warm=np.array([20,55,115],np.float32)[None,None,:]
        gain=(.05+.16*q)*(1 if profile!='final_stillness' else .75)
        out += halo*warm*gain
    if profile=='vampire_portrait':
        out[:,:,2]*=1.04; out[:,:,0]*=.95
    return np.clip(out*pulse,0,255).astype(np.uint8)


support_cache={}
for _name in set(SUPPORT.values()):
    support_cache[_name]=load_still(_name,.25)[0]
ref_cache=[]
for _p in ref_files:
    _r=cv2.imread(str(_p)); ref_cache.append(cover(_r,y_bias=.25))



def apply_canonical_fx(im, frame, local_t, local_duration, en, tr, profile, sid):
    # Production-approved reusable layer; IDs are locked by FX_REQUIREMENTS.fx.json.
    brightness=float(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).mean()/255.0)
    ctx=fxmod.FXContext(t=float(local_t),duration=max(float(local_duration),1e-6),frame_index=int(frame),fps=FPS,energy=float(en),transient=float(tr),brightness=brightness)
    out=FX.apply(im,{"id":"FX2-MOTION-002","strength":0.32},ctx)
    if any(k in profile for k in ["rain","doorway","departure","reflection"]) or sid in {"S01","S03","S04","S05","S06","S13","S23","S24","S28"}:
        out=FX.apply(out,{"id":"FX2-ATM-002","strength":0.58},ctx)
    if profile in {"dust_memory","crypt_memory","crypt_dawn","silent_light"}:
        out=FX.apply(out,{"id":"FX2-ATM-001","strength":0.45},ctx)
    if profile in {"ember_bloom","dust_memory","cathedral_impact","crypt_memory"}:
        out=FX.apply(out,{"id":"FX2-FIRE-002","strength":0.55},ctx)
    out=FX.apply(out,{"id":"FX2-LIGHT-001","strength":0.60},ctx)
    if profile in {"cathedral_push","cathedral_impact","depth_gate","dawn_bloom","crypt_dawn","silent_light","final_stillness"}:
        out=FX.apply(out,{"id":"FX2-LIGHT-002","strength":0.55,"origin":[0.76,0.17]},ctx)
    return out

def maybe_support(primary, support_name, q, sid=None):
    if not support_name: return primary
    sup=support_cache[support_name]
    # Shot-specific progression windows to increase composition variety.
    if sid=='S11':
        if .22<=q<=.62:
            a=min(0.52,(q-.22)/.18,(.62-q)/.18)
            a=max(0,a)
            return cv2.addWeighted(primary,1-a,sup,a,0)
    if sid=='S12':
        if .46<=q<=.96:
            a=max(0,min(0.72,(q-.46)/.18))
            return cv2.addWeighted(primary,1-a,sup,a,0)
    if sid=='S29':
        if .34<=q<=1.0:
            a=max(0,min(0.68,(q-.34)/.20))
            return cv2.addWeighted(primary,1-a,sup,a,0)
    if sid=='S30':
        if .00<=q<=.42:
            a=max(0.0,min(0.48,(.42-q)/.18 if q>.18 else q/.18))
            return cv2.addWeighted(primary,1-a,sup,a,0)
    # generic authored insert near 57-74% of the shot, not a random flash.
    if .57<=q<=.74:
        a=min(1,(q-.57)/.04,(.74-q)/.04)
        a=max(0,a)
        return cv2.addWeighted(primary,1-a,sup,a,0)
    return primary


def maybe_ref_flash(im, sid, local_frame, local_len):
    idx=REF_FLASH_SHOTS.get(sid)
    if idx is None or idx>=len(ref_files): return im
    center=int(local_len*.78); d=abs(local_frame-center)
    if d>3: return im
    ref=ref_cache[idx]
    a=(4-d)/5*.42
    return cv2.addWeighted(im,1-a,ref,a,0)

# Preload and precompose primary stills.
cache={}
for e in selected_entries:
    if e['shot_id']=='S00': continue
    prof=e['animation_behavior'].split(';',1)[0]
    base,_=load_shot_still(e)
    cache[e['shot_id']]=precompose(base,prof)

# Cold-open decoder.
cold=cv2.VideoCapture(str(COLD))

raw_video=OUTDIR/(f'segment_{selected_entries[0]["shot_id"]}_{selected_entries[-1]["shot_id"]}_960x540.mp4' if CHUNK_MODE else 'pandora_picture_960x540.mp4')
cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','ultrafast','-crf','17','-pix_fmt','yuv420p',str(raw_video)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)

prev=None
written=0
# Cold open: accepted motion benchmark, 180 frames exactly when this chunk includes S00.
if selected_entries and selected_entries[0]['shot_id']=='S00':
    for f in range(180):
        ok,fr=cold.read()
        if not ok:
            cold.set(cv2.CAP_PROP_POS_FRAMES,0); ok,fr=cold.read()
        fr=cv2.resize(fr,(W,H),interpolation=cv2.INTER_AREA)
        if f<12: fr=(fr.astype(np.float32)*(f/12)).astype(np.uint8)
        proc.stdin.write(fr.tobytes()); prev=fr; written+=1
cold.release()

for e in selected_entries:
    if e['shot_id']=='S00': continue
    sid=e['shot_id']; start=e['start_frame']; end=e['end_frame']; n=end-start+1
    prof=e['animation_behavior'].split(';',1)[0]; base0=cache[sid]
    support=SUPPORT.get(sid)
    hard=sid in {'S03','S11','S16','S25','S30'}
    for j in range(n):
        f=start+j; q=j/max(1,n-1); en=float(energy[f]); tr=float(trans[f])
        base=maybe_support(base0,support,q,sid)
        fr=camera(base,q,prof,en,tr)
        # Canonical current-main reusable FX layer; project-specific petals/echo/perspective remain separately proved.
        fr=apply_canonical_fx(fr,f,j/FPS,n/FPS,en,tr,prof,sid)
        if sid in {'S14','S15','S22','S25','S29','S31','S32'}:
            fr=add_petals(fr,f,.26+.12*en)
        fr=maybe_ref_flash(fr,sid,j,n)
        # Short dissolve on lyrical transitions; industrial anchor shots hard-cut.
        if not hard and prev is not None and j<6:
            a=0.5-0.5*math.cos(math.pi*(j+1)/6)
            fr=cv2.addWeighted(prev,1-a,fr,a,0)
        if sid=='S33' and q>.87:
            a=max(0,1-(q-.87)/.13); fr=(fr.astype(np.float32)*a).astype(np.uint8)
        proc.stdin.write(fr.tobytes()); prev=fr; written+=1
    print(f'{sid}: {n} frames / total {written}/{TOTAL}',flush=True)
proc.stdin.close(); rc=proc.wait()
if rc!=0: raise SystemExit(rc)
expected_chunk=sum(e['end_frame']-e['start_frame']+1 for e in selected_entries)
if written!=expected_chunk: raise RuntimeError(f'frame count mismatch {written} vs {expected_chunk}')
if CHUNK_MODE:
    print(json.dumps({'chunk':f'{selected_entries[0]["shot_id"]}-{selected_entries[-1]["shot_id"]}','frames':written,'seconds':written/FPS,'path':str(raw_video),'sha256':sha256(raw_video)},indent=2),flush=True)
    raise SystemExit(0)

# Mux song audio at +6 seconds; no audio exists before 6s.
final540=OUTDIR/'The_Door_Between_the_Seconds_PANDORA_FINAL_540p.mp4'
subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(raw_video),'-i',str(AUDIO_WAV),'-filter_complex','[1:a]adelay=6000|6000[a]','-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','256k','-t',f'{TOTAL/FPS:.6f}','-movflags','+faststart',str(final540)],check=True)

# 1080p delivery upscale, documented as upscale from 960x540 working picture.
final1080=OUTDIR/'The_Door_Between_the_Seconds_PANDORA_FINAL_1080p.mp4'
subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(final540),'-vf','scale=1920:1080:flags=lanczos','-c:v','libx264','-preset','veryfast','-crf','19','-c:a','copy','-movflags','+faststart',str(final1080)],check=True)

meta={
 'schema':'door-seconds.pandora-render.v1','subject':'Pandora the Vampire','runtime_seconds':TOTAL/FPS,
 'fps':FPS,'working_resolution':[W,H],'delivery_resolution':[1920,1080],'delivery_is_upscale':True,
 'song_offset_seconds':6.0,'shot_count':len(SCRIPT['entries']),
 'working_sha256':sha256(final540),'delivery_sha256':sha256(final1080),
 'working_bytes':final540.stat().st_size,'delivery_bytes':final1080.stat().st_size,
 'recovered_media_rule':'retained and reassigned by lyric beat','support_inserts':SUPPORT,
 'reference_flash_shots':REF_FLASH_SHOTS,
}
(OUTDIR/'RENDER_METADATA.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta,indent=2),flush=True)
