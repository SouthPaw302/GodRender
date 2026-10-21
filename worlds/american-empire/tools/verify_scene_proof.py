#!/usr/bin/env python3
"""Verify AE GodRender world->Godot technical proof and source receipts."""
from __future__ import annotations
import argparse, json, hashlib, subprocess
from pathlib import Path
from export_godot_scene import SCHEMA, digest
from population_model import assert_run

def verify(root: Path) -> dict:
    source=json.loads((root/"ae-p7-receipt.json").read_text(encoding="utf-8"))
    contract=json.loads((root/"scene_contract.json").read_text(encoding="utf-8"))
    if contract.get("schema") != SCHEMA or contract.get("authority_layer") != "scenario_only":
        raise ValueError("Contract authority invalid")
    clean=dict(contract)
    expected=clean.pop("contract_sha256", None)
    if digest(clean)!=expected: raise ValueError("Scene contract tampered")
    frame,person=assert_run(source, contract["actor"]["id"], contract["world"]["year"])
    if frame["sha256"] != contract["source"]["p7_snapshot_sha256"] or source["run_sha256"] != contract["source"]["p7_run_sha256"]:
        raise ValueError("World source hash mismatch")
    place=person["place"]
    if place!=contract["world"]["place_id"] or frame["places"][place]["service"]!=contract["world"]["service"]:
        raise ValueError("Rendered place or service disconnected from source")
    if frame["places"][place]["independence"]!=contract["world"]["independence"]:
        raise ValueError("Rendered independence disconnected from source")
    if contract["production"].get("media_refs_embedded") is not False or contract["production"].get("no_unapproved_source_media") is not True:
        raise ValueError("Source-media safety gate failed")
    log=(root/"godot.log").read_text(encoding="utf-8")
    if "AE_GODOT_SCENE_READY contract="+expected not in log: raise ValueError("Godot did not instantiate verified contract")
    for n in (2,24,44):
        if f"AE_SCENE_CAMERA_PROOF frame={n} " not in log: raise ValueError(f"Godot did not advance camera to frame {n}")
    images=[root/f"frame{n:08d}.png" for n in (2,24,44)]
    for p in images:
        if not p.is_file() or p.stat().st_size<2000 or p.read_bytes()[:8]!=b"\x89PNG\r\n\x1a\n":
            raise ValueError("Missing/invalid screenshot "+p.name)
    h=[hashlib.sha256(p.read_bytes()).hexdigest() for p in images]
    if len(set(h))<3:raise ValueError("Camera images did not change")
    video=root/"godot-proof.mp4"
    if not video.is_file() or video.stat().st_size<10000: raise ValueError("No encoded Godot movie proof")
    output=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=nb_frames,width,height","-of","json",str(video)],text=True)
    track=json.loads(output)["streams"][0]
    if int(track.get("width",0))<800 or int(track.get("height",0))<500:
        raise ValueError("Wrong viewport dimensions")
    if int(track.get("nb_frames",0))<44:raise ValueError("Fewer than 44 rendered frames")
    return {"schema":"american-empire.godot-scene-proof.v1","status":"PASS",
      "authority_layer":"scenario_only","render_classification":"technical_geometry_proof_not_approved_film",
      "p7_run_sha256":source["run_sha256"],"p7_snapshot_sha256":frame["sha256"],
      "contract_sha256":expected,"year":frame["year"],"actor":contract["actor"]["id"],
      "place":place,"frames":int(track["nb_frames"]),"image_sha256":h,
      "media_refs_embedded":False,"canon_mutations":0,"source":"browser_p7_run_via_python_validator"}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.root)
    (args.root/"verification.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("AE_WORLD_TO_GODOT_PASS "+json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
