"""Studio local reviewed-shot renderer, using exactly the same FXExecutor as CI."""
from __future__ import annotations
import json
import shutil
import sys
import uuid
from pathlib import Path
import server as base
import production_project

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"render"))
from godrender_runtime import manifest_load,render_one,sha256,SCHEMA

def execute(job):
    pid=str(job["project"]);jid=str(job["id"])
    base.update_job(jid,status="running",started_at=base.now(),progress=10,
                    result="Rendering real source through canonical FXExecutor")
    current=production_project.status(pid)
    if not current.get("initialized") or current.get("stage") not in {"SHOT_PACKAGES_BUILT","SHOT_PROOFS_ACCEPTED"}:
        raise RuntimeError("moving shot proof requires locked shot packages")
    mode=str(job.get("mode") or "still_fx")
    aid=str(job.get("asset_id") or "")
    shot_id=str(job.get("shot_id") or "")
    if not shot_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in shot_id):
        raise ValueError("safe shot id required")
    record={"id":shot_id,"seconds":float(job.get("seconds") or 3),
            "mode":mode,"fx_ids":job.get("fx_ids") or []}
    if mode in {"still_fx","video_fx"}:
        with base.LOCK:
            asset=base.find_asset(aid)
            if not asset or asset.get("project")!=pid or asset.get("status")!="ready":
                raise ValueError("source must be a ready, authorized project asset")
            asset=dict(asset)
        path=Path(asset["local_path"]).resolve()
        root=base.ASSET_ROOT.resolve()
        if root not in path.parents:
            raise RuntimeError("source asset escaped approved media root")
        if sha256(path)!=asset.get("sha256"):
            raise RuntimeError("source asset changed after ingestion")
        key="image" if mode=="still_fx" else "video"
        record[key]={"path":path.relative_to(root).as_posix(),"sha256":asset["sha256"]}
        input_root=root
    elif mode=="godot":
        record["scene"]=str(job.get("scene") or "")
        input_root=ROOT
    else:
        raise ValueError("unknown shot renderer")
    doc={"schema":SCHEMA,"width":int(job.get("width") or 640),
         "height":int(job.get("height") or 360),"fps":int(job.get("fps") or 24),
         "shots":[record],"human_visual_approval":False}
    output=base.PROJECT_ROOT/pid/"rendered_shots"/shot_id
    output.mkdir(parents=True,exist_ok=True)
    manifest=output/"source_manifest.json"
    manifest.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
    manifest_load(manifest,input_root)
    receipt=render_one(doc,record,input_root,output)
    movie=output/(shot_id+".mp4")
    asset_id=uuid.uuid4().hex[:12]
    folder=base.ASSET_ROOT/asset_id
    folder.mkdir(parents=True,exist_ok=False)
    dst=folder/(shot_id+".mp4")
    shutil.copyfile(movie,dst)
    metadata,_=base.ffprobe_metadata(dst)
    media={"id":asset_id,"project":pid,"filename":dst.name,
           "content_type":"video/mp4","size_bytes":dst.stat().st_size,
           "status":"ready","created_at":base.now(),"updated_at":base.now(),
           "folder":str(folder),"local_path":str(dst),"metadata":metadata,
           "sha256":sha256(dst),"source_url":f"/media/{asset_id}/{dst.name}",
           "thumbnail_url":None,"proxy_url":None,"review_frames":[],
           "qc":{"status":"unchecked"},"creative_status":"needs_review",
           "render_receipt":str(output/(shot_id+".receipt.json"))}
    with base.LOCK:
        base.STATE["assets"].append(media)
        base.STATE["assets"]=base.STATE["assets"][-base.MAX_ASSETS:]
        base.save_state()
    base.update_job(jid,status="complete",finished_at=base.now(),progress=100,
                    result="Technical video ready; Director approval pending; asset_id="+asset_id,
                    proof_asset_id=asset_id,receipt_sha256=receipt["video_sha256"])
    return {"asset":base.public_asset(media),"receipt":receipt}
