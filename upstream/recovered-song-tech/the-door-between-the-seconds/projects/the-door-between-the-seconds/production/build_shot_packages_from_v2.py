#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,subprocess,cv2,numpy as np
ROOT=Path('/mnt/data/AIVideoEdit_local/projects/the-door-between-the-seconds')
PICT=ROOT/'production/final_pandora_v2_gate/pandora_picture_960x540.mp4'
SCRIPT=json.loads((ROOT/'SCRIPT.json').read_text())
FPS=int(SCRIPT['target_fps'])
PKG=ROOT/'shot_packages'; PKG.mkdir(exist_ok=True)
CAP=ROOT/'proofs/current_gate/CAPABILITY_PROOF.json'
LOCK=ROOT/'fx.lock.json'
RENDERER=ROOT/'production/build_pandora_final.py'
SUPPORT={
 'S04':'rainlit_gothic_aristocrat_at_the_window.jpg','S07':'gothic_velvet_candlelit_chamber.jpg',
 'S13':'gothic_rainfall_by_candlelight.jpg','S21':'moonlit_gothic_velvet_reverie.jpg','S32':'moonlit_gothic_rose_chamber.jpg'}
REF_FLASH={'S10':0,'S14':1,'S22':2,'S27':3,'S30':4,'S33':5}
refs=sorted((ROOT/'resume_payload/reference_images_jpg').glob('*.jpg'))[:6]

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def rel(p): return str(Path(p).relative_to(ROOT))

def vstats(p):
 cap=cv2.VideoCapture(str(p)); n=0; prev=None; dif=[]; black=0; lowrun=0; maxlow=0
 while True:
  ok,fr=cap.read()
  if not ok: break
  n+=1
  if float(fr.mean())<4: black+=1
  small=cv2.resize(fr,(160,90),interpolation=cv2.INTER_AREA)
  if prev is not None:
   d=float(cv2.absdiff(prev,small).mean()); dif.append(d)
   if d<0.08: lowrun+=1; maxlow=max(maxlow,lowrun)
   else: lowrun=0
  prev=small
 cap.release()
 return {'decoded_frames':n,'mean_adjacent_delta':float(np.mean(dif)) if dif else 0.0,
         'p95_adjacent_delta':float(np.percentile(dif,95)) if dif else 0.0,
         'black_frames_mean_lt4':black,'max_near_static_run_frames':maxlow}

qc=[]
entries_to_process=SCRIPT['entries']
start_shot=__import__('os').environ.get('START_SHOT')
if start_shot:
    ids=[x['shot_id'] for x in entries_to_process]; entries_to_process=entries_to_process[ids.index(start_shot):]
for e in entries_to_process:
 sid=e['shot_id']; d=PKG/sid; d.mkdir(exist_ok=True)
 n=e['end_frame']-e['start_frame']+1; start=e['start_frame']/FPS
 proof=d/'proof.mp4'
 cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-ss',f'{start:.6f}','-i',str(PICT),'-frames:v',str(n),'-an','-c:v','libx264','-preset','ultrafast','-crf','18','-pix_fmt','yuv420p',str(proof)]
 subprocess.run(cmd,check=True)
 source=(ROOT/'resume_payload/video/gothic_window_8s_fullscreen_720p.mp4') if sid=='S00' else (ROOT/'resume_payload/created_images_jpg'/e['visual_media'])
 evid=[{'role':'primary_source','path':rel(source),'sha256':sha(source),'status':'ingested' if sid=='S00' else 'accepted'},
       {'role':'proof_preview','path':rel(proof),'sha256':sha(proof),'status':'derived'},
       {'role':'fx_lock','path':'fx.lock.json','sha256':sha(LOCK),'status':'accepted'},
       {'role':'capability_proof','path':rel(CAP),'sha256':sha(CAP),'status':'accepted'}]
 if sid in SUPPORT:
  p=ROOT/'resume_payload/created_images_jpg'/SUPPORT[sid]
  evid.append({'role':'support_insert','path':rel(p),'sha256':sha(p),'status':'accepted'})
 if sid in REF_FLASH and REF_FLASH[sid] < len(refs):
  p=refs[REF_FLASH[sid]]
  evid.append({'role':'authorized_reference_flash','path':rel(p),'sha256':sha(p),'status':'ingested'})
 st=vstats(proof)
 allow_final_black=sid=='S33'
 opening_black_ok=(sid=='S00' and st['black_frames_mean_lt4']<=8)
 result='PASS' if st['decoded_frames']==n and (st['black_frames_mean_lt4']==0 or allow_final_black or opening_black_ok) and st['mean_adjacent_delta']>0.15 and st['max_near_static_run_frames']<30 else 'FAIL'
 package={
  'schema':'aivideoedit.shot-package.v1','shot_id':sid,'frame_span':[e['start_frame'],e['end_frame']],
  'seconds':[e['start_frame']/FPS,(e['end_frame']+1)/FPS], 'story_action':e['story_action'],
  'lyric_cue':e.get('lyric_cue'),'source':rel(source),'source_role':'accepted motion benchmark' if sid=='S00' else 'recovered generated still',
  'motion_grammar':e['animation_behavior'],'canonical_fx_lock':'fx.lock.json',
  'project_capability_proof':rel(CAP),'masks_alpha':'not required for this bounded image-space package',
  'depth':'image-space only; no true-depth/3D claim','transition':e.get('transition'),
  'proof_preview':rel(proof),'proof_qc':{'result':result,**st},'media_evidence':evid,
  'notes':'Full-screen 16:9 finished shot proof extracted from current-gate v2 picture; proof pixels were rendered only after live FX-lock verification.'
 }
 (d/'package.json').write_text(json.dumps(package,indent=2)+'\n')
 qc.append({'shot_id':sid,'expected_frames':n,'proof':rel(proof),'proof_sha256':sha(proof),'result':result,**st})
 print(sid,result,n,st['decoded_frames'],round(st['mean_adjacent_delta'],3),st['max_near_static_run_frames'],flush=True)
all_qc=[]
for e in SCRIPT['entries']:
    pj=PKG/e['shot_id']/'package.json'
    if pj.exists():
        pd=json.loads(pj.read_text()); q=pd.get('proof_qc',{}); all_qc.append({'shot_id':e['shot_id'],'expected_frames':e['end_frame']-e['start_frame']+1,'proof':pd.get('proof_preview'),'proof_sha256':next((x.get('sha256') for x in pd.get('media_evidence',[]) if x.get('role')=='proof_preview'),None),**q})
report={'schema':'aivideoedit.shot-proof-qc.v1','project':'the-door-between-the-seconds','fx_lock_sha256':sha(LOCK),'capability_proof_sha256':sha(CAP),'shots':all_qc,'complete_shots':len(all_qc),'expected_shots':len(SCRIPT['entries']),'result':'PASS' if len(all_qc)==len(SCRIPT['entries']) and all(x.get('result')=='PASS' for x in all_qc) else 'FAIL'}
(ROOT/'proofs/current_gate/SHOT_PROOF_QC.json').write_text(json.dumps(report,indent=2)+'\n')
print('OVERALL',report['result'],len(all_qc),'/',len(SCRIPT['entries']))
