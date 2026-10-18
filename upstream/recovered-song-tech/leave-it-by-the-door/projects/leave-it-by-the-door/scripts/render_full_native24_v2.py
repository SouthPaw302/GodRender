import cv2, numpy as np, math, subprocess, json, wave, time, os, sys, hashlib
from pathlib import Path

ROOT=Path('/mnt/data/Leave_It_By_The_Door_COMPLETE_HANDOFF')
BASE=ROOT/'Leave_It_By_The_Door_COMPLETE_HANDOFF_OPT'
HERO=BASE/'04_GENERATED_HERO_STILLS_NAMED'
AUDIO=BASE/'01_SOURCE_AUDIO/Leave it by the door. (Remastered) (1).wav'
SHOTMAP=ROOT/'work/analysis/FULL_V1_SHOT_MAP.json'
REF_A=Path('/mnt/data/imagine-f9c3e46d.mp4')
REF_B=Path('/mnt/data/imagine-1fb7bb42.mp4')
OUT=Path('/mnt/data/leaveit_native24_full'); SHOTS=OUT/'shots'; SHOTS.mkdir(parents=True,exist_ok=True)
W,H,FPS=1280,720,24
shots=json.loads(SHOTMAP.read_text())
TOTAL_FRAMES=round(shots[-1]['end']*FPS)
DUR=TOTAL_FRAMES/FPS

Y,X=np.mgrid[0:H,0:W].astype(np.float32)
def smoothstep(u): u=np.clip(u,0,1); return u*u*(3-2*u)
def softrect_norm(r, blur=24):
    x0,y0,x1,y1=r; m=np.zeros((H,W),np.float32)
    m[int(y0*H):int(y1*H),int(x0*W):int(x1*W)]=1
    return cv2.GaussianBlur(m,(0,0),blur)
def ell_norm(cx,cy,rx,ry,blur=18):
    m=((((X-cx*W)/(rx*W))**2+((Y-cy*H)/(ry*H))**2)<=1).astype(np.float32)
    return cv2.GaussianBlur(m,(0,0),blur)
def gauss(cx,cy,sx,sy): return np.exp(-.5*(((X-cx)/sx)**2+((Y-cy)/sy)**2)).astype(np.float32)
def blend(a,b,m): return np.clip(a.astype(np.float32)*(1-m[...,None])+b.astype(np.float32)*m[...,None],0,255).astype(np.uint8)
def fit(fn):
    im=cv2.imread(str(HERO/fn),cv2.IMREAD_COLOR)
    if im is None: raise FileNotFoundError(fn)
    ih,iw=im.shape[:2]; s=max(W/iw,H/ih)
    r=cv2.resize(im,(round(iw*s),round(ih*s)),interpolation=cv2.INTER_LANCZOS4)
    x0=max(0,(r.shape[1]-W)//2); y0=max(0,(r.shape[0]-H)//2)
    return r[y0:y0+H,x0:x0+W].copy()
def warp(im,dx=0,dy=0,angle=0,scale=1.0,center=None):
    if center is None: center=(W/2,H/2)
    M=cv2.getRotationMatrix2D(center,angle,scale); M[0,2]+=dx; M[1,2]+=dy
    return cv2.warpAffine(im,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)

def ref_sig(path, size=96):
    cap=cv2.VideoCapture(str(path)); prev=None; rows=[]; lums=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        f=cv2.resize(f,(size,size),interpolation=cv2.INTER_AREA)
        g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY); lums.append(float(g.mean()))
        if prev is None:
            rows.append([0,0,0,0,0,0,0]); prev=g; continue
        fl=cv2.calcOpticalFlowFarneback(prev,g,None,.5,2,11,2,5,1.1,0)
        med=np.median(fl.reshape(-1,2),axis=0); fl=fl-med
        top=fl[:size//2]; bot=fl[size//2:]
        mag=np.linalg.norm(fl,axis=2)
        rows.append([float(mag.mean()),float(top[...,0].mean()),float(top[...,1].mean()),float(bot[...,0].mean()),float(bot[...,1].mean()),float(np.percentile(mag,85)),float(np.percentile(mag,95))])
        prev=g
    cap.release(); a=np.array(rows,np.float32); lum=np.array(lums,np.float32)
    for c in range(a.shape[1]):
        sc=np.percentile(np.abs(a[:,c]),90)+1e-6; a[:,c]=np.clip(a[:,c]/sc,-2,2)
    lum=(lum-lum.mean())/(lum.std()+1e-6)
    return a,lum
SIG_A,LUM_A=ref_sig(REF_A); SIG_B,LUM_B=ref_sig(REF_B)

with wave.open(str(AUDIO),'rb') as wf:
    sr=wf.getframerate(); ch=wf.getnchannels(); raw=wf.readframes(wf.getnframes())
x=np.frombuffer(raw,dtype='<i2').reshape(-1,ch).mean(1).astype(np.float32)/32768.0
hop=512
rms=np.array([np.sqrt(np.mean(x[i:i+hop]**2)+1e-10) for i in range(0,len(x)-hop,hop)],np.float32)
flux=np.maximum(0,np.diff(rms,prepend=rms[0])); flux=cv2.GaussianBlur(flux.reshape(1,-1),(0,0),1.0).ravel()
rlo,rhi=np.percentile(rms,[8,96]); fhi=np.percentile(flux,98)+1e-8
def energy(t):
    i=min(len(rms)-1,max(0,int(t*sr/hop))); return float(np.clip((rms[i]-rlo)/(rhi-rlo+1e-8),0,1))
def pulse(t):
    i=min(len(flux)-1,max(0,int(t*sr/hop))); return float(np.clip(flux[i]/fhi,0,1))

rng=np.random.default_rng(302)
coarse=rng.normal(0,1,(48,84)).astype(np.float32); coarse=cv2.resize(coarse,(W,H),interpolation=cv2.INTER_CUBIC); coarse=cv2.GaussianBlur(coarse,(0,0),2.0)
coarse=(coarse-coarse.mean())/(coarse.std()+1e-6)
pig=rng.random((90,160)).astype(np.float32); pig=cv2.GaussianBlur(pig,(0,0),8); pig=cv2.resize(pig,(W,H)); pig=(pig-pig.min())/(pig.max()-pig.min()+1e-6)
rain_pts=np.array([(rng.uniform(0,W),rng.uniform(-H,H),rng.uniform(.7,1.5),rng.uniform(10,24),rng.uniform(0,1)) for _ in range(165)],np.float32)
embers=np.array([(rng.uniform(0,W),rng.uniform(H*.25,H*.98),rng.uniform(.25,.8),rng.uniform(0,6.28)) for _ in range(64)],np.float32)
spray=np.array([(rng.uniform(.52*W,.97*W),rng.uniform(.42*H,.94*H),rng.uniform(.55,1.4),rng.uniform(0,6.28)) for _ in range(76)],np.float32)
birds=np.array([(rng.uniform(.55*W,.95*W),rng.uniform(.08*H,.38*H),rng.uniform(.6,1.3),rng.uniform(0,6.28)) for _ in range(7)],np.float32)
lightning_times=np.array([4.15,11.65,24.3,42.2,69.15,81.6,103.8,126.0,164.0],np.float32)

BASES={fn:fit(fn) for fn in sorted(set(s['file'] for s in shots))}
WARMS={}
for fn,b in BASES.items():
    bb,gg,rr=cv2.split(b.astype(np.float32)); m=((rr>gg*1.03)&(rr>bb*1.16)&(rr>82)).astype(np.float32)
    WARMS[fn]=cv2.GaussianBlur(m,(0,0),11)

INTERIOR_KINDS={'celebration','banjo','young_stands','fiddle_lift','dance','community','room_for_all','final_celebration','burden_fire'}
DAWN_KINDS={'dawn_rain','dawn_fire','dawn_exit'}
ARRIVAL_KINDS={'threshold','arrival','young_arrival','welcome_home'}
SOFT_KINDS={'companions','companions_close','coffee','breath','comfort','one_hand'}
BURDEN_KINDS={'burden','burden2','final_burden','burden_fire'}

MASK_CACHE={}
for sc in shots:
    ext=softrect_norm(sc['ext'],22)
    sky=ext*np.clip((.58-Y/H)/.28,0,1)
    sea=ext*np.clip((Y/H-.36)/.30,0,1)
    locals_cached=[]
    for (cx,cy,rx,ry,amount) in sc['local']:
        m=ell_norm(cx,cy,rx,ry,16)
        face=ell_norm(cx,cy-ry*.36,rx*.42,ry*.28,10)
        locals_cached.append((np.clip(m*(1-face*.78),0,1),float(amount)))
    fmask=np.clip(gauss(W*.17,H*.55,W*.20,H*.36)+.70*gauss(W*.42,H*.30,W*.13,H*.23),0,1)*(1-ext*.80)
    shaft=gauss(W*.20,H*.08,W*.15,H*.46)*(1-ext*.65)
    MASK_CACHE[sc['index']]={'ext':ext,'sky':sky,'sea':sea,'locals':locals_cached,'fmask':fmask,'shaft':shaft}

def frame_for(sc, local_frame, count, next_sc=None):
    t_global=(round(sc['start']*FPS)+local_frame)/FPS
    u=local_frame/max(1,count-1); e=energy(t_global); p=pulse(t_global); kind=sc['kind']; storm=float(sc['storm'])
    b=BASES[sc['file']]; fr=b.copy()
    mc=MASK_CACHE[sc['index']]; ext=mc['ext']; sky=mc['sky']; sea=mc['sea']; warm=WARMS[sc['file']]
    ia=(round(t_global*FPS)+sc['index']*13)%len(SIG_A); ib=(round(t_global*FPS)+sc['index']*31)%len(SIG_B)
    A=SIG_A[ia]; B=SIG_B[ib]; la=float(LUM_A[ia]); lb=float(LUM_B[ib])
    if storm>0.05:
        dx=(2.0+5.5*storm+2.0*e)*(0.25*A[1]+.45*math.sin(t_global*.72+sc['index']))
        dy=(1.0+2.5*storm)*(0.20*A[2]+.35*math.cos(t_global*.58))
        wx=warp(b,dx=dx,dy=dy,angle=.11*storm*math.sin(t_global*.37),scale=1.0+.002*storm*math.sin(t_global*.31))
        fr=blend(fr,wx,np.clip(sky*.72+sea*.60,0,1))
    for j,(m,amount) in enumerate(mc['locals']):
        amp=float(amount)*(1+.35*e+.25*p)
        dx=amp*(3.0*math.sin(t_global*(1.15+.08*j)+j*1.7)+1.2*B[3])
        dy=amp*(1.25*math.cos(t_global*(.86+.05*j)+j*.8)+.55*B[4])
        ang=amp*(.10*math.sin(t_global*(.75+.04*j)+j))
        if kind in ('dance','banjo','fiddle_lift','final_celebration','celebration'): dx*=1.45; dy*=1.25; ang*=1.8
        moved=warp(b,dx=dx,dy=dy,angle=ang,scale=1.0+.0018*amp*math.sin(t_global*1.25+j))
        fr=blend(fr,moved,m*.62)
    if storm>.08:
        ov=fr.copy()
        for k in range(5):
            xs=np.arange(int(W*.50),int(W*.98),8,dtype=np.int32)
            yy=(H*(.54+.065*k)+ (5+9*storm)*np.sin(xs/(48+6*k)+t_global*(1.3+.17*k)+k)).astype(np.int32)
            pts=np.stack([xs,yy],axis=1).reshape(-1,1,2)
            cv2.polylines(ov,[pts],False,(178+7*k,191+6*k,199+5*k),1,cv2.LINE_AA)
        fr=blend(fr,ov,sea*.22*storm)
        shimmer=(.5+.5*np.sin(X*.033+t_global*3.2)+.25*np.sin(Y*.086-t_global*2.1)).astype(np.float32)
        sa=np.clip(sea*np.maximum(shimmer-.68,0)*(.10+.14*storm),0,.18)
        fr=np.clip(fr.astype(np.float32)+sa[...,None]*np.array([48,45,36],np.float32),0,255).astype(np.uint8)
    rollx=int(42*math.sin(t_global*.12)); rolly=int(22*math.cos(t_global*.09)); fog=np.roll(np.roll(coarse,rollx,1),rolly,0)
    fog=np.clip((fog-.15)*.035,0,.075)
    if kind in INTERIOR_KINDS: fog*=np.clip((1-ext*.55),0,1)*(1.0+.25*e)
    elif kind in BURDEN_KINDS: fog*=np.clip(.45+.8*ext,0,1)
    else: fog*=ext*(.6+.8*storm)
    tint=np.array([105,110,116],np.float32)
    fr=np.clip(fr.astype(np.float32)*(1-fog[...,None])+tint*fog[...,None],0,255).astype(np.uint8)
    warm_gain=.020+.018*e+.010*max(0,lb)+.010*p
    if kind in INTERIOR_KINDS: warm_gain*=1.65
    fr=np.clip(fr.astype(np.float32)+warm[...,None]*warm_gain*np.array([5,35,85],np.float32)+ext[...,None]*(.008+.006*la)*np.array([34,24,10],np.float32),0,255).astype(np.uint8)
    if kind in INTERIOR_KINDS or kind in SOFT_KINDS or kind in BURDEN_KINDS:
        flick=max(0,.60+.22*math.sin(t_global*7.4)+.10*math.sin(t_global*16.7+1.2)+.08*p)
        fmask=mc['fmask']
        fr=np.clip(fr.astype(np.float32)+fmask[...,None]*flick*np.array([4,25,64],np.float32),0,255).astype(np.uint8)
        shaft=mc['shaft']; shaft_gain=(.025+.022*e)*(.88+.18*math.sin(t_global*.31)+.10*max(0,lb))
        fr=np.clip(fr.astype(np.float32)+shaft[...,None]*shaft_gain*np.array([10,45,92],np.float32),0,255).astype(np.uint8)
    ov=fr.copy()
    if storm>.08:
        density=max(.15,storm); step=max(1,int(1/max(.18,density)))
        for q,(x0,y0,sp,L,phase) in enumerate(rain_pts):
            if q%step: continue
            yy=(y0+t_global*(210+60*e)*sp)%(H+80)-40; xx=(x0+t_global*(10+18*storm)*sp)%W
            xi,yi=int(xx),int(yy)
            if 0<=xi<W and 0<=yi<H and ext[yi,xi]>.20:
                c=int(160+45*phase); cv2.line(ov,(xi,yi),(max(0,xi-4),min(H-1,yi+int(L))),(c,c+6,c+11),1,cv2.LINE_AA)
        if kind in ARRIVAL_KINDS or storm>.78:
            for x0,y0,sp,ph in spray:
                xx=x0+26*math.sin(t_global*1.35+ph)+t_global*10*sp; yy=y0-((t_global*48*sp+18*math.sin(t_global*2+ph))%190)
                if W*.50<xx<W*.99 and H*.35<yy<H*.96: cv2.circle(ov,(int(xx),int(yy)),1,(205,216,226),-1,cv2.LINE_AA)
    if kind in INTERIOR_KINDS or kind=='burden_fire':
        for x0,y0,sp,ph in embers:
            xx=x0+9*math.sin(t_global*1.7+ph); yy=y0-((t_global*(18+18*e)*sp)%150); a=max(0,math.sin(t_global*2.8+ph))**5
            if a>.06 and 0<xx<W and 0<yy<H and ext[int(yy),int(xx)]<.35: cv2.circle(ov,(int(xx),int(yy)),1 if a<.6 else 2,(25,int(95+70*a),int(205+45*a)),-1,cv2.LINE_AA)
    if kind in BURDEN_KINDS:
        for j in range(24):
            ph=j*.83; xx=W*(.44+.13*math.sin(t_global*.23+ph)); yy=H*(.83-((t_global*.035+j*.031)% .38))
            cv2.circle(ov,(int(xx),int(yy)),1,(55,59,63),-1,cv2.LINE_AA)
    if kind in DAWN_KINDS:
        for x0,y0,sp,ph in birds:
            xx=(x0+t_global*18*sp)%W; yy=y0+9*math.sin(t_global*.6+ph)
            if xx>W*.48:
                cv2.line(ov,(int(xx-5),int(yy)),(int(xx),int(yy-2)),(65,68,70),1,cv2.LINE_AA); cv2.line(ov,(int(xx),int(yy-2)),(int(xx+5),int(yy)),(65,68,70),1,cv2.LINE_AA)
    fr=cv2.addWeighted(fr,.56,ov,.44,0)
    if storm>.35:
        d=float(np.min(np.abs(lightning_times-t_global))); li=math.exp(-((d/.055)**2))*storm
        if li>.01:
            flash=np.clip(sky*.52+sea*.16,0,1)*li
            fr=np.clip(fr.astype(np.float32)+flash[...,None]*np.array([130,125,112],np.float32),0,255).astype(np.uint8)
    if kind in DAWN_KINDS:
        gold=smoothstep((t_global-180.0)/18.5)
        fr=np.clip(fr.astype(np.float32)+gold*np.array([0,8,20],np.float32),0,255).astype(np.uint8)
    fr=np.clip(fr.astype(np.float32)+coarse[...,None]*.34,0,255).astype(np.uint8)
    trans_frames=9
    if next_sc is not None and local_frame>=count-trans_frames:
        q=(local_frame-(count-trans_frames))/max(1,trans_frames-1); q=smoothstep(q)
        nb=BASES[next_sc['file']]; shift=np.roll(pig,int(55*math.sin(t_global*.7)),axis=1)
        mask=np.clip((q*1.55-.25-shift)*3.7+.5,0,1); mask=cv2.GaussianBlur(mask,(0,0),4.5)
        mid=math.sin(math.pi*q)**2; veil=np.array([104,109,111],np.float32)
        mix=fr.astype(np.float32)*(1-mask[...,None])+nb.astype(np.float32)*mask[...,None]
        fr=np.clip(mix*(1-.075*mid)+veil*.075*mid,0,255).astype(np.uint8)
    c=sc['cam']; s0,s1,dx0,dx1,dy0,dy1=c; qq=smoothstep(u)
    scale=s0+(s1-s0)*qq+.0018*p; dx=dx0+(dx1-dx0)*qq; dy=dy0+(dy1-dy0)*qq
    return warp(fr,dx=dx,dy=dy,angle=.07*math.sin(t_global*.43+sc['index']*.2),scale=scale)

def parse_shot_ids(spec):
    if not spec: return None
    out=set()
    for part in spec.split(','):
        part=part.strip()
        if not part: continue
        if '-' in part:
            a,b=part.split('-',1); out.update(range(int(a),int(b)+1))
        else: out.add(int(part))
    return out
SELECTED_SHOTS=parse_shot_ids(os.environ.get('SHOT_IDS',''))
state_path=OUT/'render_state.json'
state={'width':W,'height':H,'fps':FPS,'total_frames':TOTAL_FRAMES,'duration':DUR,'completed':[],'started':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
if state_path.exists():
    try: state.update(json.loads(state_path.read_text()))
    except Exception: pass
for idx,sc in enumerate(shots):
    if SELECTED_SHOTS is not None and sc['index'] not in SELECTED_SHOTS: continue
    startf=round(sc['start']*FPS); endf=round(sc['end']*FPS) if idx<len(shots)-1 else TOTAL_FRAMES; count=endf-startf
    out=SHOTS/f"shot_{sc['index']:02d}_{sc['kind']}.mp4"
    if out.exists():
        cap=cv2.VideoCapture(str(out)); n=int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); cap.release()
        if n==count and n>0:
            print(f"SKIP {out.name} frames={n}",flush=True); continue
        out.unlink(missing_ok=True)
    cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','bgr24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE); t0=time.time(); next_sc=shots[idx+1] if idx+1<len(shots) else None
    for n in range(count): proc.stdin.write(frame_for(sc,n,count,next_sc).tobytes())
    proc.stdin.close(); rc=proc.wait()
    if rc!=0: raise RuntimeError(f'ffmpeg shot encode failed rc={rc}')
    print(f"DONE shot {sc['index']:02d}/{len(shots)} {sc['kind']} frames={count} sec={time.time()-t0:.1f}",flush=True)
if SELECTED_SHOTS is not None: sys.exit(0)
concat=OUT/'concat.txt'; concat.write_text('\n'.join(["file '"+(SHOTS/f"shot_{s['index']:02d}_{s['kind']}.mp4").as_posix()+"'" for s in shots])+'\n')
silent=OUT/'Leave_It_By_The_Door_NATIVE24_FULL_V2_silent.mp4'
subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(silent)],check=True)
final=OUT/'Leave_It_By_The_Door_NATIVE24_FULL_V2_720p24.mp4'
subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(silent),'-i',str(AUDIO),'-map','0:v:0','-map','1:a:0','-t',f'{DUR:.6f}','-c:v','copy','-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart',str(final)],check=True)
print('FINAL',final,flush=True)
