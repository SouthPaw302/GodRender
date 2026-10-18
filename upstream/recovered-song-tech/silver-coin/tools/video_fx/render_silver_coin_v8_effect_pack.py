import cv2, numpy as np, math, hashlib, json
from pathlib import Path

OUT=Path('/mnt/data/silver_coin_v8_fx'); OUT.mkdir(exist_ok=True)
W,H,FPS=1280,720,24
DUR=4.0; N=int(DUR*FPS)

P={
'forest':Path('/mnt/data/enchanted_woodland_coin_portrait.png'),
'path':Path('/mnt/data/golden_path_to_the_village.png'),
'workers':Path('/mnt/data/golden_haired_maiden_at_sunset.png'),
'inn':Path('/mnt/data/twilight_inn_beneath_the_flower_crown.png'),
'toast':Path('/mnt/data/ghostwriter_images/generated/a_warm_detailed_painterly_scene_in_a_rustic_medi_1_batch_1.png'),
'dance':Path('/mnt/data/ghostwriter_images/generated/a_warm_golden_cinematic_medieval_renaissance_tav_4_batch_4.png'),
'fiddle':Path('/mnt/data/ghostwriter_images/generated/a_warm_golden_cinematic_medieval_tavern_interior_3_batch_3.png'),
'clap':Path('/mnt/data/ghostwriter_images/generated/a_richly_detailed_warm_golden_lit_medieval_folkl_2_batch_2.png'),
}

def load(k):
    im=cv2.imread(str(P[k]),cv2.IMREAD_COLOR)
    return cv2.resize(im,(W,H),interpolation=cv2.INTER_AREA)
B={k:load(k) for k in P}
Y,X=np.mgrid[0:H,0:W].astype(np.float32)

def feather_ellipse(cx,cy,rx,ry,blur=31):
    m=(((X-cx)/rx)**2+((Y-cy)/ry)**2<=1).astype(np.float32)
    return cv2.GaussianBlur(m,(0,0),blur)

def feather_rect(x0,y0,x1,y1,blur=31):
    m=np.zeros((H,W),np.float32); m[max(0,y0):min(H,y1),max(0,x0):min(W,x1)]=1
    return cv2.GaussianBlur(m,(0,0),blur)

def blend(a,b,m): return np.clip(a.astype(np.float32)*(1-m[...,None])+b.astype(np.float32)*m[...,None],0,255).astype(np.uint8)

def remap_shift(im,dx,dy):
    mapx=X+dx.astype(np.float32); mapy=Y+dy.astype(np.float32)
    return cv2.remap(im,mapx,mapy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)

def camera(im,scale=1.0,dx=0,dy=0,angle=0):
    M=cv2.getRotationMatrix2D((W/2,H/2),angle,scale); M[0,2]+=dx; M[1,2]+=dy
    return cv2.warpAffine(im,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)

def gauss(cx,cy,sx,sy=None):
    if sy is None: sy=sx
    return np.exp(-0.5*(((X-cx)/sx)**2+((Y-cy)/sy)**2)).astype(np.float32)

def add_warm(im,field,strength):
    f=field[...,None]*strength
    tint=np.array([15,65,125],np.float32)
    return np.clip(im.astype(np.float32)+f*tint,0,255).astype(np.uint8)

def write_clip(name,frames):
    temp=OUT/(name+'_temp.mp4')
    w=cv2.VideoWriter(str(temp),cv2.VideoWriter_fourcc(*'mp4v'),FPS,(W,H))
    for f in frames: w.write(f)
    w.release()
    out=OUT/(name+'.mp4')
    import subprocess
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(temp),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
    temp.unlink(missing_ok=True)
    return out

def forest_frames():
    base=B['forest']; hsv=cv2.cvtColor(base,cv2.COLOR_BGR2HSV)
    green=((hsv[...,0]>28)&(hsv[...,0]<95)&(hsv[...,1]>45)).astype(np.float32)
    green=cv2.GaussianBlur(green,(0,0),6)
    subject=feather_ellipse(600,375,335,420,20); green*=1-subject*.92
    hair=feather_ellipse(525,365,270,360,22)
    face=feather_ellipse(620,210,115,145,18); hair*=1-face
    crown=feather_ellipse(600,85,245,85,14); faceprotect=np.maximum(face,feather_ellipse(625,230,145,170,15))
    hair=np.clip(hair+crown*.7,0,1)*(1-faceprotect*.95)
    for i in range(N):
        t=i/FPS; ph=2*math.pi*t/DUR; fr=base.copy()
        dxg=3.0*np.sin(Y/55+ph)+1.3*np.sin(Y/23-ph*1.4); dyg=1.2*np.sin(X/80-ph)
        fr=blend(fr,remap_shift(base,dxg,dyg),green*.75)
        dxh=5.5*np.sin((Y-80)/180+ph)+1.5*np.sin(ph*2); dyh=2.0*np.cos((X-500)/210+ph)
        fr=blend(fr,remap_shift(base,dxh,dyh),hair*.78)
        shaft=gauss(1010+55*math.sin(ph),50,230,390)+0.7*gauss(1150+30*math.cos(ph),120,150,300)
        fr=add_warm(fr,np.clip(shaft,0,1),.16+.05*math.sin(ph))
        sc=1.035+0.018*(.5-.5*math.cos(ph)); fr=camera(fr,sc,-10+18*math.sin(ph),3*math.cos(ph),0.18*math.sin(ph))
        yield fr

def coin_frames():
    base=B['forest']; coinx,coiny=832,350; cm=feather_ellipse(coinx,coiny,47,47,6)
    for i in range(N):
        t=i/FPS; ph=2*math.pi*t/DUR
        fr=camera(base,1.055+0.015*math.sin(ph/2),-5*math.cos(ph),0,0)
        sweep=((X-(coinx-80+160*((t*2)%2)/2))/10.0)
        gl=np.exp(-0.5*sweep**2)*np.exp(-0.5*((Y-coiny)/42)**2)
        ring=np.exp(-0.5*((np.sqrt((X-coinx)**2+(Y-coiny)**2)-40)/5)**2)
        pulse=(max(0,math.sin(ph*2))**5); f=np.clip(gl*.9+ring*.4*pulse,0,1)*cm
        yield np.clip(fr.astype(np.float32)+f[...,None]*np.array([170,190,225],np.float32),0,255).astype(np.uint8)

def tavern_frames():
    base=B['toast']; centers=[(815,648,1.0),(355,220,.55),(815,240,.55),(1080,210,.45)]
    rng=np.random.default_rng(302); noise=rng.random((90,160)).astype(np.float32); noise=cv2.GaussianBlur(noise,(0,0),9)
    garland=feather_rect(0,0,W,170,25); garland*=1-feather_ellipse(610,230,135,160,18)
    for i in range(N):
        t=i/FPS; ph=2*math.pi*t/DUR; fr=base.copy()
        dx=3.5*np.sin(Y/80+ph); fr=blend(fr,remap_shift(base,dx,np.zeros_like(dx)),garland*.55)
        field=np.zeros((H,W),np.float32)
        for j,(cx,cy,a) in enumerate(centers):
            amp=a*(.65+.35*math.sin(ph*(3+j*.11)+j*1.7)**2)
            field += gauss(cx,cy,95 if cy>500 else 75,100 if cy>500 else 90)*amp
        fr=add_warm(fr,np.clip(field,0,1),.30)
        flick=1+.18*math.sin(ph*5)+.08*math.sin(ph*11); cx,cy=815,618
        flame=np.exp(-0.5*(((X-cx)/(10*flick))**2+((Y-cy)/(22*flick))**2))
        fr=np.clip(fr.astype(np.float32)+flame[...,None]*np.array([45,130,255],np.float32)*.75,0,255).astype(np.uint8)
        sm=cv2.resize(noise,(W,H)); shx=int(50*math.sin(ph)); shy=int(-35*(1-math.cos(ph))); sm=np.roll(np.roll(sm,shx,1),shy,0)
        smoke=np.clip((sm-sm.min())/(sm.max()-sm.min()+1e-6)-.45,0,1)*.22; smoke*=gauss(800,470,360,260)
        fog=np.full_like(fr,218,dtype=np.float32); fr=np.clip(fr.astype(np.float32)*(1-smoke[...,None])+fog*smoke[...,None],0,255).astype(np.uint8)
        yield camera(fr,1.025+0.012*math.sin(ph/2),6*math.sin(ph),0,0.1*math.sin(ph))

def fiddler_frames():
    base=B['fiddle']; bow=feather_rect(655,220,1120,650,22)
    bow*=1-np.maximum(feather_ellipse(450,230,105,135,16),feather_ellipse(875,190,115,145,16))
    rng=np.random.default_rng(811); pts=np.column_stack([rng.integers(650,1180,42),rng.integers(140,620,42),rng.random(42)])
    for i in range(N):
        t=i/FPS; ph=2*math.pi*t/DUR; beat=math.sin(ph*8)
        fr=blend(base,remap_shift(base,6.0*beat*np.ones_like(X),-3.0*beat*np.ones_like(Y)),bow*.58)
        hit=max(0,math.sin(ph*8))**8
        fr=camera(fr,1.03+.025*hit+0.012*math.sin(ph/2),-5+8*math.sin(ph/2),2*math.cos(ph),0.18*math.sin(ph))
        ov=fr.astype(np.float32)
        for x0,y0,q in pts:
            a=max(0,math.sin(ph*4+q*6.28))**10
            if a>=.1: ov += gauss(float(x0),float(y0),5+5*q)[...,None]*np.array([30,110,240],np.float32)*(a*.75)
        yield np.clip(ov,0,255).astype(np.uint8)

def dance_frames():
    base=B['dance']; protect=feather_ellipse(630,360,300,390,25); crowd=np.clip(1-protect,0,1)
    left=feather_rect(0,60,470,H,25)*crowd; right=feather_rect(800,60,W,H,25)*crowd
    for i in range(N):
        t=i/FPS; ph=2*math.pi*t/DUR; fr=base.copy(); dx1=7*np.sin(ph); dx2=-7*np.sin(ph); dy=1.8*np.sin(ph*2)
        fr=blend(fr,camera(base,1.0,dx1,dy,0),left*.68); fr=blend(fr,camera(base,1.0,dx2,-dy,0),right*.68)
        pulse=max(0,math.sin(ph*4))**5; fr=add_warm(fr,gauss(640,260,520,420),.08+.12*pulse)
        yield camera(fr,1.03+.025*math.sin(ph/2)**2,13*math.sin(ph),-4*math.cos(ph),0.35*math.sin(ph))

def lightning_frames():
    base=B['inn']; rng=np.random.default_rng(93); sky=feather_rect(0,0,900,360,24); road=feather_rect(400,400,1240,H,35); strikes=[1.05,1.18,2.75]
    paths=[]
    for sx in [760,880]:
        pts=[(sx,20)]; x=sx; y=20
        while y<310:
            x += int(rng.normal(0,18)); y += int(rng.integers(22,42)); pts.append((x,y))
        paths.append(pts)
    for i in range(N):
        t=i/FPS; ph=2*math.pi*t/DUR; fr=base.astype(np.float32); intensity=0
        for st in strikes: intensity=max(intensity,math.exp(-((t-st)/.055)**2))
        if intensity>.015:
            bolt=np.zeros((H,W),np.float32)
            for pts in paths:
                for a,b in zip(pts,pts[1:]): cv2.line(bolt,a,b,1.0,2,cv2.LINE_AA)
            flash=np.clip(cv2.GaussianBlur(bolt,(0,0),10)*2.4+sky*.32,0,1)*intensity
            fr += flash[...,None]*np.array([220,210,190],np.float32); fr += (cv2.flip(flash,0)*road*.55)[...,None]*np.array([180,145,95],np.float32)
        sh=(2.5*np.sin(Y*.095+ph*3)+1.2*np.sin(Y*.21-ph*2)).astype(np.float32)
        fr0=blend(np.clip(fr,0,255).astype(np.uint8),remap_shift(base,sh,np.zeros_like(sh)),road*.10)
        yield camera(fr0,1.025+.012*math.sin(ph/2),8*math.sin(ph/2),0,0)

def shaft_frames():
    base=B['path']
    for i in range(N):
        t=i/FPS; ph=2*math.pi*t/DUR; fr=base.copy(); field=np.zeros((H,W),np.float32)
        for j in range(4):
            cx=1000+j*90+55*math.sin(ph+j); cy=80+j*65; field += gauss(cx,cy,110,360)*(.7-.1*j)
        fr=add_warm(fr,np.clip(field,0,1),.26)
        haze=gauss(980,380,430,300)*(.08+.035*math.sin(ph)); fr=np.clip(fr.astype(np.float32)*(1-haze[...,None])+np.array([225,232,224],np.float32)*haze[...,None],0,255).astype(np.uint8)
        yield camera(fr,1.035+.018*(.5-.5*math.cos(ph)),18*math.sin(ph),-2+4*math.sin(ph),.18*math.sin(ph))

def pigment_frames():
    a=B['forest']; b=B['inn']; rng=np.random.default_rng(7); n=rng.random((90,160)).astype(np.float32); n=cv2.GaussianBlur(n,(0,0),8); n=cv2.resize(n,(W,H)); n=(n-n.min())/(n.max()-n.min()+1e-6)
    for i in range(N):
        u=i/(N-1); ph=2*math.pi*u; shift=np.roll(n,int(60*math.sin(ph)),axis=1); threshold=u*1.45-.22
        m=np.clip((threshold-shift)*3.6+.5,0,1); m=cv2.GaussianBlur(m,(0,0),7)
        fr=np.clip(a.astype(np.float32)*(1-m[...,None])+b.astype(np.float32)*m[...,None],0,255).astype(np.uint8)
        mid=math.sin(math.pi*u)**2; fog=gauss(650,380,660,400)*(.30*mid); fr=np.clip(fr.astype(np.float32)*(1-fog[...,None])+np.array([215,220,205],np.float32)*fog[...,None],0,255).astype(np.uint8)
        fr=add_warm(fr,gauss(845,350,140)*(.18*mid),.5); yield camera(fr,1.04+.02*mid,0,0,.18*math.sin(ph))

jobs=[('V8_FX01_forest_breath_hair_garland',forest_frames),('V8_FX02_coin_glint',coin_frames),('V8_FX03_tavern_firelight_smoke',tavern_frames),('V8_FX04_fiddler_impact',fiddler_frames),('V8_FX05_communal_crowd_sway',dance_frames),('V8_FX06_lightning_wet_reflection',lightning_frames),('V8_FX07_gaussian_light_shafts',shaft_frames),('V8_FX08_fog_pigment_travel',pigment_frames)]
if __name__=='__main__':
    import sys
    wanted=set(sys.argv[1:]); meta=[]
    for name,fn in jobs:
        if wanted and name not in wanted: continue
        out=write_clip(name,fn()); meta.append({'file':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'duration':DUR,'fps':FPS,'size':[W,H]})
    print(json.dumps(meta,indent=2))
