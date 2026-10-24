#!/usr/bin/env python3
import argparse,hashlib,json,math,runpy,subprocess,sys
from pathlib import Path
import cv2,numpy as np
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from general.reusable.fx_v2.executor import FXExecutor
from general.reusable.fx_v2.runtime import FXContext
from general.reusable.fx_v2.living_still_fx import cloud_drift,star_field
P=runpy.run_path(str(ROOT/'general/reusable/painterly-motion/hybrid_painterly_fx.py'))
H=runpy.run_path(str(ROOT/'general/reusable/depth-parallax-25d/depth_parallax_25d.py'))
S=runpy.run_path(str(ROOT/'general/reusable/generative-engine/spatial/living_parallax.py'))
DIRECT={'FX2-ATM-005':'general/reusable/fx_v2/living_still_fx.py','FX2-ATM-006':'general/reusable/fx_v2/living_still_fx.py','FX2-MOTION-001':'general/reusable/painterly-motion/hybrid_painterly_fx.py','FX2-SPATIAL-001':'general/reusable/depth-parallax-25d/depth_parallax_25d.py','FX2-SPATIAL-004':'general/reusable/generative-engine/spatial/living_parallax.py'}
APPROVED={'FX2-LIGHT-002','FX2-ATM-021','FX2-LIGHT-025','FX2-TRANS-025'}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def gitsha(): return subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
def within(root,rel):
 root=Path(root).resolve();p=(root/rel).resolve()
 if p==root or root not in p.parents: raise ValueError(rel)
 return p
def mask(shape,box,blur=18):
 h,w=shape[:2];x0,y0,x1,y1=box;m=np.zeros((h,w),np.float32);m[max(0,int(y0*h)):min(h,int(y1*h)),max(0,int(x0*w)):min(w,int(x1*w))]=1
 return np.clip(cv2.GaussianBlur(m,(0,0),blur),0,1)
def blend(a,b,m):
 m=np.clip(m,0,1).astype(np.float32)[...,None];return np.clip(a.astype(np.float32)*(1-m)+b.astype(np.float32)*m,0,255).astype(np.uint8)
def authority(path):
 a=json.loads(Path(path).read_text());reg=json.loads((ROOT/'general/reusable/fx_v2/registry.json').read_text())['effects'];seen=set()
 for r in a['authorized_existing_fx']:
  e=r['id'];seen.add(e)
  if reg[e]['gate_status']!='proof_required' or reg[e]['name']!=r['name']:raise RuntimeError('authority mismatch '+e)
  if not (ROOT/r['implementation'].split('::')[0]).is_file():raise RuntimeError('missing '+e)
 if seen!=set(DIRECT):raise RuntimeError('authority set mismatch')
 return a
def load_manifest(path,root):
 d=json.loads(Path(path).read_text());assert d['schema']=='godrender.production.v1' and len(d['shots'])==10 and sum(int(s['frames']) for s in d['shots'])==480
 for s in d['shots']:
  p=within(root,s['image']['path']);assert p.is_file() and sha(p)==s['image']['sha256']
  if s.get('next_image'):
   q=within(root,s['next_image']['path']);assert q.is_file() and sha(q)==s['next_image']['sha256']
  unknown=set(s.get('fx_ids',[]))-set(DIRECT)-APPROVED
  if unknown:raise RuntimeError('unknown FX '+str(sorted(unknown)))
 return d
def prepare(src,s):
 prot=mask(src.shape,s['protect_box'],16);env=np.clip(mask(src.shape,s['sky_roi'],22)*(1-prot),0,1);z={'env':env}
 if s['depth_mode']=='old_depth_parallax':z['depth']=P['depth_proxy'](src)
 elif s['depth_mode']=='streaming_living_parallax':z['depth'],z['depth_label']=S['load_depth'](None,*src.shape[:2])
 elif s['depth_mode']=='hybrid_25d':
  h,w=src.shape[:2];x0,y0,x1,y1=s['protect_box'];rect=(max(1,int(x0*w)),max(1,int(y0*h)),max(4,int((x1-x0)*w)),max(4,int((y1-y0)*h)));rect=(rect[0],rect[1],min(rect[2],w-rect[0]-1),min(rect[3],h-rect[1]-1))
  try:sm=H['grabcut_subject'](src,rect)
  except Exception:sm=(prot*255).astype(np.uint8)
  if np.count_nonzero(sm)<500:sm=(prot*255).astype(np.uint8)
  z['alpha']=H['signed_distance_alpha'](sm,6);z['background']=H['inpaint_background'](src,sm);z['depth']=H['make_depth_field'](src,horizon=.48,left_foreground=False)
 return z
def depth(src,s,z,p):
 env=z['env'];mode=s['depth_mode']
 if mode=='old_depth_parallax':return blend(src,P['depth_parallax'](src,z['depth'],p,float(s.get('depth_amount',3))),env*.62)
 if mode=='streaming_living_parallax':
  rgb=cv2.cvtColor(src,cv2.COLOR_BGR2RGB).astype(np.float32)/255;ang=p*math.tau;wr=S['warp'](rgb,z['depth'],math.sin(ang)*.52,math.sin(ang*2)*.18,float(s.get('streaming_strength',.014)));w=cv2.cvtColor(np.clip(wr*255,0,255).astype(np.uint8),cv2.COLOR_RGB2BGR);return blend(src,w,env*.72)
 if mode=='hybrid_25d':
  a=float(s.get('hybrid_amplitude',4));ang=p*math.tau;bg=H['warp_depth'](z['background'],z['depth'],a*math.sin(ang),a*.3*math.cos(ang),1.006+.001*(1-math.cos(ang)));al=z['alpha'][...,None];return np.clip(src.astype(np.float32)*al+bg.astype(np.float32)*(1-al),0,255).astype(np.uint8)
 raise RuntimeError(mode)
def render(manifest,root,sid,out,auth):
 authority(auth);d=load_manifest(manifest,root);s=next(x for x in d['shots'] if x['id']==sid);src=cv2.resize(cv2.imread(str(within(root,s['image']['path']))),(1280,720),interpolation=cv2.INTER_LANCZOS4);nxt=None
 if s.get('next_image'):nxt=cv2.resize(cv2.imread(str(within(root,s['next_image']['path']))),(1280,720),interpolation=cv2.INTER_LANCZOS4)
 z=prepare(src,s);fx=FXExecutor(consumer='nordic_b01_brainfx');out=Path(out);out.mkdir(parents=True,exist_ok=True);video=out/(sid+'.mp4');cmd=['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-f','rawvideo','-pix_fmt','bgr24','-s','1280x720','-r','24','-i','-','-an','-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-movflags','+faststart',str(video)];proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE);first=None;moving=0;total=int(s['frames'])
 try:
  for i in range(total):
   ctx=FXContext(t=i/24,duration=total/24,frame_index=i,fps=24,energy=float(s['energy']),transient=float(s['transient']));fr=depth(src,s,z,i/max(total,1))
   if float(s.get('cloud_strength',0))>0:fr=blend(fr,cloud_drift(fr,ctx,roi=tuple(s['sky_roi']),strength=float(s['cloud_strength']),seed=302+int(sid[-3:])),z['env'])
   if float(s.get('star_strength',0))>0:fr=blend(fr,star_field(fr,ctx,roi=tuple(s['sky_roi']),strength=float(s['star_strength']),count=max(36,int(70+55*float(s['star_strength']))),seed=802+int(sid[-3:])),z['env'])
   ids=set(s.get('fx_ids',[]))
   if 'FX2-LIGHT-002' in ids:fr=fx.apply_frame('FX2-LIGHT-002',fr,ctx,params={'origin':s.get('light_origin',[.66,.18]),'strength':float(s.get('light_strength',.25))})
   if 'FX2-ATM-021' in ids:fr=blend(fr,fx.apply_frame('FX2-ATM-021',fr,ctx),z['env']*.18)
   if 'FX2-LIGHT-025' in ids:fr=cv2.addWeighted(fr,.88,fx.apply_frame('FX2-LIGHT-025',fr,ctx),.12,0)
   if 'FX2-TRANS-025' in ids and nxt is not None:
    frac=float(s.get('transition_fraction',0));start=int(round(total*(1-frac)))
    if frac>0 and i>=start:
     p=(i-start)/max(1,total-start-1);fr=cv2.addWeighted(fr,.76,fx.apply_transition('FX2-TRANS-025',fr,nxt,p,ctx),.24,0)
     if i>=total-3:q=(i-(total-3)+1)/3;fr=cv2.addWeighted(fr,1-q,nxt,q,0)
   if first is None:first=fr.copy()
   elif np.mean(cv2.absdiff(first,fr))>.25:moving+=1
   proc.stdin.write(fr.astype(np.uint8).tobytes())
  proc.stdin.close();err=proc.stderr.read().decode();rc=proc.wait()
  if rc:raise RuntimeError(err[-1000:])
 except Exception:
  if proc.stdin and not proc.stdin.closed:proc.stdin.close()
  proc.kill();proc.wait();raise
 if moving==0:raise RuntimeError('static shard')
 direct=[e for e in s['fx_ids'] if e in DIRECT];approved=[e for e in s['fx_ids'] if e in APPROVED];rec={'schema':'godrender.nordic-b01-brainfx-shot.v1','status':'TECHNICAL_RENDER_PASS_VISUAL_REVIEW_PENDING','human_approval':False,'shot':sid,'frames':total,'source_sha256':s['image']['sha256'],'depth_mode':s['depth_mode'],'direct_fx_authorized':direct,'canonical_fxexecutor':approved,'director_authority_sha256':sha(auth),'implementation_sha256':{DIRECT[e]:sha(ROOT/DIRECT[e]) for e in direct},'source_commit':gitsha(),'video_sha256':sha(video),'video':video.name,'nonidentical_frames':moving}
 if s['depth_mode']=='streaming_living_parallax':rec['depth_mode_evidence']='synthetic_radial_fallback image-space 2.5D; not metric depth'
 (out/(sid+'.receipt.json')).write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec))
def assemble(manifest,root,shards,out,auth):
 authority(auth);d=load_manifest(manifest,root);shards=Path(shards);out=Path(out);out.mkdir(parents=True,exist_ok=True);lines=[];recs=[]
 for s in d['shots']:
  sid=s['id'];v=shards/sid/(sid+'.mp4');r=json.loads((shards/sid/(sid+'.receipt.json')).read_text());assert sha(v)==r['video_sha256'];lines.append("file '"+str(v.resolve()).replace("'","'\\''")+"'");recs.append(r)
 c=out/'concat.txt';c.write_text('\n'.join(lines)+'\n');audio=within(root,d['audio']['path']);assert sha(audio)==d['audio']['sha256'];video=out/'NORDIC_B01_BRAIN_FX_PROOF03_720p.mp4';p=subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-y','-f','concat','-safe','0','-i',str(c),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-shortest','-movflags','+faststart',str(video)],capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stderr[-1000:])
 rec={'schema':'godrender.nordic-b01-brainfx-film.v1','status':'TECHNICAL_RENDER_PASS_VISUAL_REVIEW_PENDING','human_visual_approval':False,'production_complete':False,'batch':'B01','frames_expected':480,'duration_target_seconds':20.0,'sha256':sha(video),'bytes':video.stat().st_size,'audio_sha256':d['audio']['sha256'],'director_authority_sha256':sha(auth),'source_commit':gitsha(),'shards':recs};(out/'render_receipt.json').write_text(json.dumps(rec,indent=2)+'\n');(out/'BRAIN_OUTBOX.json').write_text(json.dumps({'schema':'godrender.brain-proof.v1','publication':'PENDING_VERIFIED_DRIVE_CREDENTIALS','film_receipt':rec},indent=2)+'\n');print(json.dumps(rec))
def main():
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
 a=sp.add_parser('shot');[a.add_argument(x,required=True) for x in ['--manifest','--input-root','--shot-id','--out','--authority']]
 a=sp.add_parser('assemble');[a.add_argument(x,required=True) for x in ['--manifest','--input-root','--shards','--out','--authority']]
 x=ap.parse_args();render(x.manifest,x.input_root,x.shot_id,x.out,x.authority) if x.cmd=='shot' else assemble(x.manifest,x.input_root,x.shards,x.out,x.authority)
if __name__=='__main__':main()
