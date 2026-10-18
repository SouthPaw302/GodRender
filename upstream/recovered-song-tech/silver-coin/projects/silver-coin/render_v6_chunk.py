import cv2, numpy as np, wave, math, json, subprocess, time, hashlib
from pathlib import Path
from scipy.signal import find_peaks

OUT=Path('/mnt/data/silver_coin_v6_motion'); OUT.mkdir(exist_ok=True)
RW,RH,FPS=960,540,12
DW,DH=1280,720
DUR=207.44
AUDIO=Path('/mnt/data/Silver Coin  (Remastered).wav')
G=Path('/mnt/data/ghostwriter_images/generated')
P={
 'forest':Path('/mnt/data/enchanted_woodland_coin_portrait.png'),
 'path':Path('/mnt/data/golden_path_to_the_village.png'),
 'workers':Path('/mnt/data/golden_haired_maiden_at_sunset.png'),
 'inn':Path('/mnt/data/twilight_inn_beneath_the_flower_crown.png'),
 'toast':G/'a_warm_detailed_painterly_scene_in_a_rustic_medi_1_batch_1.png',
 'dance':G/'a_warm_golden_cinematic_medieval_renaissance_tav_4_batch_4.png',
 'fiddle':G/'a_warm_golden_cinematic_medieval_tavern_interior_3_batch_3.png',
 'clap':G/'a_richly_detailed_warm_golden_lit_medieval_folkl_2_batch_2.png',
}
SCENES=[
 (0.0,10.0,'forest','verse','forest_coin'),
 (10.0,20.0,'path','verse','path_reveal'),
 (20.0,30.0,'workers','verse','work_end'),
 (30.0,39.3,'inn','verse','threshold'),
 (39.3,50.0,'toast','chorus','toast'),
 (50.0,61.5,'clap','chorus','clap'),
 (61.5,72.2,'fiddle','chorus','fiddle'),
 (72.2,82.7,'dance','chorus','dance'),
 (82.7,93.0,'toast','verse2','merchant_view'),
 (93.0,103.7,'forest','verse2','coin_memory'),
 (103.7,115.0,'toast','chorus','toast_return'),
 (115.0,127.0,'dance','chorus','dance_return'),
 (127.0,138.2,'fiddle','chorus','fiddle_return'),
 (138.2,150.5,'inn','bridge','night_threshold'),
 (150.5,163.5,'workers','bridge','village_lives'),
 (163.5,176.5,'path','bridge','night_walk'),
 (176.5,188.0,'forest','bridge','coin_reflection'),
 (188.0,199.5,'dance','final','final_dance'),
 (199.5,207.44,'forest','final','return_forest'),
]

with wave.open(str(AUDIO),'rb') as w:
 sr=w.getframerate(); ch=w.getnchannels(); raw=w.readframes(w.getnframes())
x=np.frombuffer(raw,dtype='<i2').reshape(-1,ch).mean(1).astype(np.float32)/32768
hop=1024
en=np.array([np.mean(np.abs(x[i:i+hop])) for i in range(0,len(x)-hop,hop)],np.float32)
zc=np.array([np.mean(np.abs(np.diff(np.signbit(x[i:i+hop]).astype(np.int8)))) for i in range(0,len(x)-hop,hop)],np.float32)
flux=np.maximum(0,np.diff(en,prepend=en[0])); flux=np.convolve(flux,np.ones(5)/5,'same')
pk,_=find_peaks(flux,distance=max(1,int(.25*sr/hop)),prominence=np.std(flux)*.48)
pt=pk*hop/sr; pv=flux[pk]; m=pt<DUR+.5; pt,pv=pt[m],pv[m]
if len(pv): pv=(pv-pv.min())/(pv.max()-pv.min()+1e-9)

def sample(arr,t,r=3):
 i=min(len(arr)-1,max(0,int(t*sr/hop))); return float(np.mean(arr[max(0,i-r):min(len(arr),i+r+1)]))
en_lo,en_hi=np.quantile(en,[.08,.96]); z_lo,z_hi=np.quantile(zc,[.08,.96])
def energy(t): return float(np.clip((sample(en,t)-en_lo)/(en_hi-en_lo+1e-8),0,1))
def bright(t): return float(np.clip((sample(zc,t)-z_lo)/(z_hi-z_lo+1e-8),0,1))
def pulse(t):
 if not len(pt): return 0.
 d=np.abs(pt-t); return float(np.max(np.exp(-(d/.15)**2)*(.28+.72*pv)))

BASEW,BASEH=1120,630
bases={}
for key,p in P.items():
 im=cv2.imread(str(p))
 if im is None: raise FileNotFoundError(p)
 ih,iw=im.shape[:2]; s=max(BASEW/iw,BASEH/ih)
 r=cv2.resize(im,(int(iw*s),int(ih*s)),interpolation=cv2.INTER_AREA if s<1 else cv2.INTER_LANCZOS4)
 y=(r.shape[0]-BASEH)//2; x0=(r.shape[1]-BASEW)//2; bases[key]=r[y:y+BASEH,x0:x0+BASEW]

Y,X=np.mgrid[0:RH,0:RW].astype(np.float32)
rad=np.sqrt(((X-RW/2)/(RW/2))**2+((Y-RH/2)/(RH/2))**2)
vign=np.clip(1-.13*np.maximum(0,rad-.45),.82,1)[...,None]
LW,LH=120,68; ly,lx=np.mgrid[0:LH,0:LW].astype(np.float32); rng=np.random.default_rng(302)
gauss=[(rng.uniform(.02,.98),rng.uniform(.03,.95),rng.uniform(.035,.12),rng.uniform(.05,.20),rng.uniform(0,6.28),rng.uniform(.07,.21)) for _ in range(14)]

def gaussian_field(t,phase=0):
 f=np.zeros((LH,LW),np.float32)
 for px,py,sig,a,ph,sp in gauss:
  px2=px+.025*math.sin(sp*t+ph+phase); py2=py+.018*math.cos(sp*.77*t+ph*.7+phase)
  xx=lx/LW-px2; yy=ly/LH-py2; f += a*np.exp(-(xx*xx+yy*yy)/(2*sig*sig))
 f/=f.max()+1e-6
 return cv2.resize(f,(RW,RH),interpolation=cv2.INTER_LINEAR)

def camera(base,scale,dx,dy,angle):
 M=cv2.getRotationMatrix2D((BASEW/2,BASEH/2),angle,scale); M[0,2]+=dx*48; M[1,2]+=dy*30
 w=cv2.warpAffine(base,M,(BASEW,BASEH),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
 x=(BASEW-RW)//2; y=(BASEH-RH)//2; return w[y:y+RH,x:x+RW]

def cam_params(kind,u,p,e):
 q={
 'forest_coin':(1.024+.026*u,-.60+.55*u,.12*math.sin(math.pi*u),-.30+.45*u),
 'path_reveal':(1.04-.008*u,-.65+1.15*u,.15-.22*u,.40-.65*u),
 'work_end':(1.045-.015*u,.30-.55*u,.04*math.sin(2*math.pi*u),-.18+.22*u),
 'threshold':(1.035+.022*u,-.30+.60*u,-.08+.12*u,.28-.40*u),
 'toast':(1.035+.030*u,-.28+.52*u,.02*math.sin(math.pi*u),-.18+.28*u),
 'clap':(1.045+.020*math.sin(math.pi*u),.45-.90*u,.04*math.sin(2*math.pi*u),.35-.65*u),
 'fiddle':(1.05+.018*u,-.45+.80*u,.06-.10*u,-.35+.55*u),
 'dance':(1.035+.030*u,-.55+1.05*u,.10*math.sin(math.pi*u),.45-.75*u),
 'merchant_view':(1.06+.018*u,.42-.52*u,.02,.30-.35*u),
 'coin_memory':(1.055+.030*u,-.20+.30*u,-.02,-.12+.18*u),
 'toast_return':(1.04+.026*u,.30-.58*u,.03,-.22+.32*u),
 'dance_return':(1.03+.038*u,.48-.95*u,.08*math.sin(math.pi*u),-.40+.72*u),
 'fiddle_return':(1.065+.025*u,.15-.55*u,-.04,.25-.40*u),
 'night_threshold':(1.035+.012*u,-.48+.75*u,-.05+.08*u,.32-.44*u),
 'village_lives':(1.05-.010*u,.38-.68*u,.03,.15-.28*u),
 'night_walk':(1.055+.012*u,-.62+1.18*u,.11-.18*u,.35-.55*u),
 'coin_reflection':(1.06+.026*u,.20-.42*u,-.02,-.22+.32*u),
 'final_dance':(1.025+.045*u,-.62+1.20*u,.10*math.sin(math.pi*u),.55-.95*u),
 'return_forest':(1.055-.020*u,.18-.32*u,.04-.06*u,.15-.22*u),
 }[kind]
 sc,dx,dy,a=q
 intensity={'verse':.0025,'verse2':.003,'chorus':.006,'bridge':.0025,'final':.007}
 return sc+intensity.get('verse',.003)*p*(.5+.5*e),dx,dy,a

def apply_loops(fr,t,section,kind,e,p,b):
 f=fr.astype(np.float32)/255
 g=gaussian_field(t,phase={'verse':0,'chorus':1.3,'verse2':2.1,'bridge':3.1,'final':4.0}.get(section,0))
 if section in ('chorus','final'):
  tint=np.array([.04,.17,.32],np.float32); amp=.045+.055*e+.018*p
 elif section=='bridge':
  tint=np.array([.16,.12,.07],np.float32); amp=.035+.035*e
 else:
  tint=np.array([.10,.19,.26],np.float32); amp=.035+.035*e+.012*p
 f += g[...,None]*tint*amp
 if kind in ('toast','clap','fiddle','dance','merchant_view','toast_return','dance_return','fiddle_return','final_dance'):
  flick=.012*math.sin(t*4.2)+.007*math.sin(t*7.1+1.4)+.010*p
  f *= 1 + max(-.012,min(.035,flick))
 if kind in ('threshold','night_threshold'):
  h0=int(RH*.69); roi=f[h0:]; hh=roi.shape[0]; yy,xx=np.mgrid[0:hh,0:RW].astype(np.float32)
  sh=(1.5*np.sin(yy*.13+t*2.0)*(0.22+.78*e)).astype(np.float32)
  wa=cv2.remap(roi,xx+sh,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101); al=((yy/hh)**1.7)[...,None]*.09
  f[h0:]=roi*(1-al)+wa*al
 if section=='bridge': f *= np.array([1.00,.985,.955],np.float32)
 if section=='final': f *= np.array([.995,1.01,1.025],np.float32)
 f *= 1+.010*e+.006*p+.004*b
 f*=vign
 return np.clip(f*255,0,255).astype(np.uint8)

def scene(i,t):
 st,en_,key,section,kind=SCENES[i]; u=float(np.clip((t-st)/(en_-st),0,1)); p=pulse(t); e=energy(t); b=bright(t)
 sc,dx,dy,a=cam_params(kind,u,p,e); fr=camera(bases[key],sc,dx,dy,a)
 return apply_loops(fr,t,section,kind,e,p,b)

TRANS={39.3:'candle',82.7:'pigment',103.7:'candle',138.2:'shadow',176.5:'fog',188.0:'lift',199.5:'fog'}
def trans(a,b,t,bound,style,w=.34):
 q=float(np.clip((t-(bound-w))/(2*w),0,1)); s=q*q*(3-2*q)
 aa=cv2.resize(a,(480,270)); bb=cv2.resize(b,(480,270))
 if style=='pigment':
  aa=cv2.GaussianBlur(aa,(0,0),.6+1.4*s); bb=cv2.GaussianBlur(bb,(0,0),2.0-1.4*s); mix=cv2.addWeighted(aa,1-s,bb,s,0)
  veil=np.array([26,52,88],np.float32); mid=math.sin(math.pi*s)**2; mix=np.clip(mix*(1-.07*mid)+veil*.07*mid,0,255)
 elif style=='candle':
  mix=cv2.addWeighted(aa,1-s,bb,s,0).astype(np.float32); mid=math.sin(math.pi*s)**6; mix=np.clip(mix+np.array([18,70,125],np.float32)*mid,0,255)
 elif style=='shadow':
  H,W=aa.shape[:2]; yy,xx=np.mgrid[0:H,0:W]; mask=np.clip((s*1.45-(xx/W*.75+yy/H*.25))/.18,0,1)[...,None].astype(np.float32); mix=aa*(1-mask)+bb*mask
 elif style=='fog':
  aa=cv2.GaussianBlur(aa,(0,0),.4+1.5*s); bb=cv2.GaussianBlur(bb,(0,0),1.9-1.4*s); mix=cv2.addWeighted(aa,1-s,bb,s,0).astype(np.float32); mid=math.sin(math.pi*s)**2; mix=np.clip(mix+235*mid*.10,0,255)
 else:
  mix=cv2.addWeighted(aa,1-s,bb,s,0).astype(np.float32); mid=math.sin(math.pi*s)**4; mix=np.clip(mix*(1+.08*mid),0,255)
 return cv2.resize(mix.astype(np.uint8),(RW,RH),interpolation=cv2.INTER_LINEAR)

import sys
n0=int(sys.argv[1]); n1=int(sys.argv[2]); idx=int(sys.argv[3])
out=OUT/f'v6_chunk_{idx:02d}.mp4'
writer=cv2.VideoWriter(str(out),cv2.VideoWriter_fourcc(*'mp4v'),FPS,(RW,RH))
bounds=[x[0] for x in SCENES[1:]]
started=time.time()
for n in range(n0,n1):
 t=n/FPS
 i=max(j for j,s in enumerate(SCENES) if s[0]<=t); fr=scene(i,t)
 for k,bound in enumerate(bounds):
  w=.34
  if abs(t-bound)<=w:
   prev=k; nxt=k+1; style=TRANS.get(round(bound,1),'clean')
   if style=='clean':
    q=float(np.clip((t-(bound-w))/(2*w),0,1)); s=q*q*(3-2*q); fr=cv2.addWeighted(scene(prev,t),1-s,scene(nxt,t),s,0)
   else: fr=trans(scene(prev,t),scene(nxt,t),t,bound,style,w)
   break
 writer.write(fr)
writer.release()
print(json.dumps({'chunk':idx,'n0':n0,'n1':n1,'frames':n1-n0,'seconds':round(time.time()-started,2),'file':str(out)}))
