import cv2, numpy as np, math, subprocess, json
from pathlib import Path

# Leave It by the Door — native 24 fps living-image proof engine.
# This is the exact motion approach adopted after comparison against the two
# user-supplied 24 fps reference clips. Adapt input paths to the active workspace.
W,H,FPS=1280,720,24
DUR=6.0
N=int(DUR*FPS)

HERO=Path('/mnt/data/Leave_It_By_The_Door_COMPLETE_HANDOFF/Leave_It_By_The_Door_COMPLETE_HANDOFF_OPT/04_GENERATED_HERO_STILLS_NAMED/a_warm_welcome_through_the_storm.png')
REF_A=Path('/mnt/data/imagine-f9c3e46d.mp4')
REF_B=Path('/mnt/data/imagine-1fb7bb42.mp4')
AUDIO=Path('/mnt/data/Leave_It_By_The_Door_COMPLETE_HANDOFF/Leave_It_By_The_Door_COMPLETE_HANDOFF_OPT/01_SOURCE_AUDIO/Leave it by the door. (Remastered) (1).wav')
OUT=Path('/mnt/data/leaveit_native24_proof')
OUT.mkdir(parents=True,exist_ok=True)

im=cv2.imread(str(HERO)); ih,iw=im.shape[:2]
s=max(W/iw,H/ih)
r=cv2.resize(im,(round(iw*s),round(ih*s)),interpolation=cv2.INTER_LANCZOS4)
x0=(r.shape[1]-W)//2; y0=(r.shape[0]-H)//2
base=r[y0:y0+H,x0:x0+W].copy()
Y,X=np.mgrid[0:H,0:W].astype(np.float32)

def softrect(x0,y0,x1,y1,b=25):
    m=np.zeros((H,W),np.float32); m[y0:y1,x0:x1]=1
    return cv2.GaussianBlur(m,(0,0),b)

def ellipse(cx,cy,rx,ry,b=18):
    m=((((X-cx)/rx)**2+((Y-cy)/ry)**2)<=1).astype(np.float32)
    return cv2.GaussianBlur(m,(0,0),b)

def gauss(cx,cy,sx,sy):
    return np.exp(-.5*(((X-cx)/sx)**2+((Y-cy)/sy)**2)).astype(np.float32)

# Local semantic masks: identity stays stable while environment/hair/fabric move.
ext=softrect(645,35,1210,680,24)*(1-ellipse(885,370,168,322,17)*.97)
cloud=ext*softrect(650,20,1210,350,32)
sea=ext*softrect(650,280,1220,690,24)
hair=softrect(275,85,620,370,25)*(1-ellipse(548,220,82,108,12))*(1-ellipse(555,350,110,150,18)*.7)
skirt=softrect(240,335,700,710,32)*np.clip((Y-330)/180,0,1)*(1-ellipse(555,360,105,135,18)*.85)
crowd=softrect(0,150,420,620,42)
reflection=ext*softrect(650,520,1220,715,18)
warm=softrect(0,0,650,720,38)
fire=np.clip(gauss(120,280,220,240)+.7*gauss(365,215,120,160)+.5*gauss(405,420,120,160),0,1)

def ref_flows(path,size=144):
    cap=cv2.VideoCapture(str(path)); gs=[]; lum=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        f=cv2.resize(f,(size,size),interpolation=cv2.INTER_AREA)
        g=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
        gs.append(g); lum.append(g.mean())
    cap.release()
    flows=[np.zeros((size,size,2),np.float32)]
    for a,b in zip(gs,gs[1:]):
        fl=cv2.calcOpticalFlowFarneback(a,b,None,.5,2,13,2,5,1.1,0)
        fl-=np.median(fl.reshape(-1,2),axis=0)
        fl=cv2.GaussianBlur(fl,(0,0),1.2)
        flows.append(fl)
    lum=np.array(lum,np.float32)
    lum=(lum-lum.mean())/(lum.std()+1e-6)
    return flows,lum

flowsA,lumA=ref_flows(REF_A)
flowsB,lumB=ref_flows(REF_B)

def flow_res(fl):
    fh,fw=fl.shape[:2]
    return (cv2.resize(fl[:,:,0],(W,H),interpolation=cv2.INTER_LINEAR)*(W/fw),
            cv2.resize(fl[:,:,1],(W,H),interpolation=cv2.INTER_LINEAR)*(H/fh))

def smooth_flow(arr,i):
    ids=[(i+d)%len(arr) for d in (-1,0,1)]
    return (arr[ids[0]]+2*arr[ids[1]]+arr[ids[2]])*.25

rng=np.random.default_rng(302)
rain=np.array([(rng.uniform(650,1210),rng.uniform(-80,H),rng.uniform(.75,1.45),rng.uniform(11,21)) for _ in range(145)],np.float32)
spray=np.array([(rng.uniform(690,1180),rng.uniform(350,650),rng.uniform(.65,1.35),rng.uniform(0,6.28)) for _ in range(70)],np.float32)
embers=np.array([(rng.uniform(20,610),rng.uniform(180,630),rng.uniform(.25,.8),rng.uniform(0,6.28)) for _ in range(45)],np.float32)
texrng=np.random.default_rng(991)
coarse=texrng.normal(0,1,(40,72)).astype(np.float32)
coarse=cv2.resize(coarse,(W,H),interpolation=cv2.INTER_CUBIC)
coarse=cv2.GaussianBlur(coarse,(0,0),1.4)

temp=OUT/'proof_native24_temp.avi'
wr=cv2.VideoWriter(str(temp),cv2.VideoWriter_fourcc(*'MJPG'),FPS,(W,H))
metrics=[]; prev=None
for n in range(N):
    t=n/FPS; ia=n%len(flowsA); ib=n%len(flowsB)
    ax,ay=flow_res(smooth_flow(flowsA,ia)); bx,by=flow_res(smooth_flow(flowsB,ib))

    # One organic deformation pass, but separate reference flow sources per semantic region.
    dx=ax*(cloud*.22+sea*.44)+bx*(hair*.34+skirt*.42)+(.8*math.sin(t*1.7))*crowd*.12
    dy=ay*(cloud*.18+sea*.40)+by*(hair*.29+skirt*.34)+(.4*math.sin(t*1.3))*crowd*.12
    warped=cv2.remap(base,X-dx.astype(np.float32),Y-dy.astype(np.float32),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)
    union=np.clip(cloud+sea+hair+skirt+crowd*.25,0,1)
    fr=np.clip(base.astype(np.float32)*(1-union[...,None])+warped.astype(np.float32)*union[...,None],0,255)

    # Reference-derived light migration.
    la=float(lumA[ia]); lb=float(lumB[ib])
    fr += ext[...,None]*(0.010+0.009*la)*np.array([35,22,7],np.float32)
    fr += warm[...,None]*(0.010+0.009*lb)*np.array([0,34,76],np.float32)
    flick=max(0,.64+.20*math.sin(t*7.7)+.08*math.sin(t*17.3+1.4)+.05*math.sin(t*29.1))
    fr += fire[...,None]*flick*np.array([4,25,65],np.float32)
    fr=np.clip(fr,0,255).astype(np.uint8)

    # Wet reflection ripple.
    dxr=(2.2*np.sin(Y*.10+t*4.2)+1.0*np.sin(X*.022-t*2.0))*reflection
    dyr=.65*np.sin(X*.034+t*3.0)*reflection
    rip=cv2.remap(fr,X-dxr.astype(np.float32),Y-dyr.astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101)
    fr=np.clip(fr.astype(np.float32)*(1-(reflection*.16)[...,None])+rip.astype(np.float32)*(reflection*.16)[...,None],0,255).astype(np.uint8)

    # Motivated rain, wave spray and embers: continuous trajectories, no frame duplication.
    ov=fr.copy()
    for x,y,sp,L in rain:
        yy=(y+t*245*sp)%(H+80)-40; xx=x+t*20*sp
        if 645<xx<1220 and 0<yy<H:
            cv2.line(ov,(int(xx),int(yy)),(int(xx-4),int(yy+L)),(190,205,218),1,cv2.LINE_AA)
    fr=np.clip(fr.astype(np.float32)*.52+ov.astype(np.float32)*.48*ext[...,None]+fr.astype(np.float32)*.48*(1-ext[...,None]),0,255).astype(np.uint8)
    ov=fr.astype(np.float32)
    for x,y,sp,ph in spray:
        xx=x+26*math.sin(t*1.45+ph)+t*13*sp
        yy=y-((t*52*sp+18*math.sin(t*2+ph))%210)
        a=.25+.3*(.5+.5*math.sin(t*4+ph))
        if 650<xx<1220 and 300<yy<680:
            cv2.circle(ov,(int(xx),int(yy)),1,(235*a,245*a,255*a),-1,cv2.LINE_AA)
    for x,y,sp,ph in embers:
        xx=x+8*math.sin(t*1.8+ph); yy=y-((t*25*sp)%100)
        a=max(0,math.sin(t*3+ph))**4
        if a>.07 and 0<xx<645 and 100<yy<650:
            cv2.circle(ov,(int(xx),int(yy)),1,(20,120*a,255*a),-1,cv2.LINE_AA)
    fr=np.clip(ov+coarse[...,None]*.28,0,255).astype(np.uint8)

    # Camera motion is deliberately secondary to internal scene motion.
    u=t/DUR; sc=1.006+.022*(u*u*(3-2*u))
    M=cv2.getRotationMatrix2D((W/2,H/2),.08*math.sin(t*.8),sc)
    M[0,2]+=-3+8*u; M[1,2]+=1.5*math.sin(math.pi*u)
    fr=cv2.warpAffine(fr,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT_101)
    wr.write(fr)
    if prev is not None:
        metrics.append(float(np.mean(cv2.absdiff(fr,prev))))
    prev=fr
wr.release()

final=OUT/'Leave_It_By_The_Door_NATIVE24_LivingScene_PROOF01_720p24.mp4'
subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(temp),'-i',str(AUDIO),'-t',str(DUR),'-c:v','libx264','-preset','fast','-crf','16','-pix_fmt','yuv420p','-c:a','aac','-b:a','320k','-ar','48000','-movflags','+faststart',str(final)],check=True)

report={
    'fps':FPS,'resolution':[W,H],'duration':DUR,'frames':N,
    'mean_adjacent_frame_difference':float(np.mean(metrics)),
    'p10':float(np.percentile(metrics,10)),
    'p90':float(np.percentile(metrics,90)),
    'method':'native24 reference optical-flow transfer; localized sea/cloud/hair/skirt motion; rain/spray/embers; wet reflection; reference-derived light migration'
}
(OUT/'PROOF01_metrics.json').write_text(json.dumps(report,indent=2))
print(final)
print(json.dumps(report,indent=2))
