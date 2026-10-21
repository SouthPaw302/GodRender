#!/usr/bin/env python3
"""Publish only verified, derived Godot world-proof videos to AE Observer source.

Never copy Drive or accepted film footage. Limit artifact size and registry.
Requires successful independent verifier before invocation in CI.
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
PROOFS=REPO/"worlds/american-empire/web/proofs"
CLASS="technical_geometry_proof_not_approved_film"

def publish(root:Path, run_id:str)->dict:
    report=json.loads((root/"verification.json").read_text(encoding="utf-8"))
    contract=json.loads((root/"scene_contract.json").read_text(encoding="utf-8"))
    if report.get("status")!="PASS" or report.get("render_classification")!=CLASS:
        raise ValueError("No independent verified render receipt")
    if report["contract_sha256"]!=contract["contract_sha256"] or report["p7_snapshot_sha256"]!=contract["source"]["p7_snapshot_sha256"]:
        raise ValueError("World scene contract/source mismatch")
    if report.get("media_refs_embedded") is not False or contract["production"]["media_refs_embedded"] is not False:
        raise ValueError("Archival media cannot be published")
    if not re.fullmatch(r"\d{9,18}",run_id):
        raise ValueError("Invalid workflow-run proof id")
    actor,year,place=contract["actor"]["id"],contract["world"]["year"],contract["world"]["place_id"]
    if not re.fullmatch(r"[a-z0-9-]{1,50}",actor) or not re.fullmatch(r"[a-z0-9-]{1,50}",place):
        raise ValueError("Unexpected source labels")
    filename=f"godot-{year}-{actor}-{contract['contract_sha256'][:12]}"
    video=root/"godot-proof.mp4"
    if not video.is_file() or not 10000 < video.stat().st_size <= 5_000_000:
        raise ValueError("Generated proof exceeded safe size bounds")
    digest=hashlib.sha256(video.read_bytes()).hexdigest()
    PROOFS.mkdir(parents=True,exist_ok=True)
    registry_path=PROOFS/"registry.json"
    registry=json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry,list) or len(registry)>12:raise ValueError("Registry source invalid")
    item={
      "id":filename,"classification":CLASS,"verified":True,
      "video":f"proofs/{filename}.mp4","video_sha256":digest,
      "actor":actor,"year":year,"place":place,"frames":report["frames"],
      "contract_sha256":report["contract_sha256"],
      "p7_snapshot_sha256":report["p7_snapshot_sha256"],
      "p7_run_sha256":report["p7_run_sha256"],
      "source_workflow_url":f"https://github.com/SouthPaw302/GodRender/actions/runs/{run_id}",
      "scope":"scenario_only_procedural_godot_technical_proof_not_original_media",
    }
    destination=PROOFS/(filename+".mp4")
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest()!=digest:
        raise ValueError("Existing proof ID has different bytes; no overwrite")
    shutil.copy2(video,destination)
    registry=[item]+[e for e in registry if e.get("id")!=filename]
    if len(registry)>8:
        stale=registry[8:]
        registry=registry[:8]
        for e in stale:
            name=e.get("id","")
            if re.fullmatch(r"godot-[a-z0-9-]+",name):
                old=PROOFS/(name+".mp4")
                if old.is_file():old.unlink()
    registry_path.write_text(json.dumps(registry,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("AE_VERIFIED_GODOT_PUBLISHED "+json.dumps(item,sort_keys=True))
    return item

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    publish(args.root,args.run_id)
