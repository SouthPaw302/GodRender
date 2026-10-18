#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, shutil, json, hashlib
from pathlib import Path

TIMELINE = [
    ("cold",0,6.0),
    ("main",34,4),("main",16,4),
    ("main",6,6),("main",16,6),("main",30,6),("main",34,6),("main",50,6),("main",71,6),
    ("main",94,3.25),("main",52,3.25),("main",109,3.25),("main",80,3.25),("main",117,3.25),("main",100,3.25),("main",122,3.25),("main",127,3.25),
    ("main",77,5),("repass",20,5),("main",83,5),("main",86,5),("main",94,5),("main",102,5),("main",132,5),("main",135,5.02),
    ("main",109,3.5),("main",52,3.5),("repass",70,3.5),("main",120,3.5),("main",57,3.5),("main",117,3.5),("main",71,3.5),("main",153,3.5),
    ("main",153,5),("main",145,5),("main",160,5),("main",137,5),("main",163,5.1),
]

def run(cmd):
    subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def sha256(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--cold',type=Path,required=True)
    ap.add_argument('--main-source',type=Path,required=True)
    ap.add_argument('--repass',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--crf',default='20')
    args=ap.parse_args()
    src={'cold':args.cold,'main':args.main_source,'repass':args.repass}
    for p in src.values():
        if not p.is_file(): raise SystemExit(f'missing source: {p}')
    outdir=args.output.parent
    work=outdir/'segments'
    if work.exists(): shutil.rmtree(work)
    work.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for i,(kind,start,dur) in enumerate(TIMELINE):
        p=work/f'{i:03d}.mp4'
        cmd=['ffmpeg','-y','-hide_banner','-loglevel','error','-ss',str(start),'-t',str(dur),'-i',str(src[kind]),'-an',
             '-vf','scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,fps=30,setsar=1',
             '-c:v','libx264','-preset','ultrafast','-crf',str(args.crf),'-pix_fmt','yuv420p','-threads','2','-g','60','-keyint_min','60','-sc_threshold','0',str(p)]
        run(cmd)
        manifest.append({'index':i,'source':kind,'source_start':start,'duration':dur,'file':p.name})
        print(f'{i+1}/{len(TIMELINE)} {kind} {start}+{dur}',flush=True)
    concat=work/'concat.txt'
    concat.write_text(''.join(f"file '{(work/f'{i:03d}.mp4').as_posix()}'\n" for i in range(len(TIMELINE))))
    picture=outdir/'fresh_picture_v1.mp4'
    run(['ffmpeg','-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(picture)])
    run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(picture),'-i',str(args.main_source),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','320k','-shortest','-movflags','+faststart',str(args.output)])
    meta={'schema':'door-seconds.fresh-cut.v1','title':'The Door Between the Seconds','lead_character':'Pandora','timeline_seconds':sum(d for _,_,d in TIMELINE),'segments':manifest,'output':args.output.name,'sha256':sha256(args.output)}
    (outdir/'FRESH_CUT_v1.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('DONE',args.output,meta['sha256'],flush=True)
if __name__=='__main__': main()
