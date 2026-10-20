#!/usr/bin/env python3
"""Build a deployable, static browser explorer from verified GodRender canon and Brain.

The Drive external Brain stays an authenticated external source; this exports only
Git-tracked, provenance-marked capability metadata and links. No secrets, media,
unreviewed Drive sheets, speculative provenance or dynamic remote code are included.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

WORLD = Path(__file__).resolve().parents[1]
REPO = WORLD.parents[1]
SITE = WORLD / "web"
SOURCE = SITE / "src"
DEFAULT_DEST = SITE / "dist"
sys.path.insert(0, str(WORLD / "tools"))
from build_explorer_bundle import build_bundle

FX_REGISTRY = "general/reusable/fx_v2/registry.json"
WORKFLOWS = "general/reusable/STANDARD_WORKFLOW_REGISTRY.json"
MODELS = "general/reusable/intelligence/MODEL_REGISTRY.json"
MEDIA = "general/reusable/MEDIA_CAPABILITY_MATRIX.json"
SOURCES = "config/brain_source_index.json"
BRAIN = "docs/BRAIN_INTEGRATION.md"
DRIVE_BRAIN = "https://docs.google.com/spreadsheets/d/1Xi2wSER-vEIjy52FTKA5RvMXNnGrTxoYiEoPhyXw77c/edit"
DRIVE_CONTRACT = "https://docs.google.com/document/d/1HKMEg_VuOKjqTDexrDXPioZFD4GxRW_tenYXbi5RjA8/edit"
CANON_DRIVE = "https://drive.google.com/drive/folders/1UYyGfYE4bhd5fqh8QdOQWgqmpTc2TA0z"
MEDIA_DRIVE = "https://drive.google.com/drive/folders/1hnRyqWuHGxBdRI5zeegNs2wDZ5N8SHTz"
GIT_BASE = "https://github.com/SouthPaw302/GodRender/blob/world/american-empire/"

def _git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def _load(path: str):
    return json.loads((REPO / path).read_text(encoding="utf-8"))

def brain_index() -> dict:
    fx = _load(FX_REGISTRY)
    flows = _load(WORKFLOWS)
    models = _load(MODELS)
    media = _load(MEDIA)
    source = _load(SOURCES)
    assert len(fx["effects"]) >= 90
    assert source["drive_spreadsheet_url"] == DRIVE_BRAIN
    assert "External Production Brain" in (REPO / BRAIN).read_text(encoding="utf-8")
    def provenance(path):
        return {"repo": "SouthPaw302/GodRender", "branch": "world/american-empire",
                "path": path, "git_blob_sha1": _git_blob(REPO / path), "url": GIT_BASE + path}
    effects = []
    for eid, e in sorted(fx["effects"].items()):
        effects.append({"id": eid, "name": e.get("name", eid), "family": e.get("family", ""),
                        "gate_status": e.get("gate_status", "unverified"),
                        "implementation_kind": (e.get("implementation") or {}).get("kind"),
                        "proof_ids": e.get("proofs", []),
                        "source": provenance(FX_REGISTRY),
                        "authority": "registry_metadata_only_not_execution"})
    workflows = []
    for f in flows["workflows"]:
        workflows.append({"id": f.get("id", ""), "name": f.get("name", ""),
                          "category": f.get("category", ""), "status": f.get("status", "unknown"),
                          "verification": (f.get("verification") or {}).get("status", "not_reported"),
                          "steps": (f.get("implementation") or {}).get("steps", [])[:6],
                          "source": provenance(WORKFLOWS),
                          "authority": "registry_only"})
    model_list = []
    for m in models["models"]:
        model_list.append({"id": m["id"], "capability": m.get("capability", ""),
                           "runtime": m.get("runtime", ""), "purpose": m.get("purpose", ""),
                           "enabled": bool(m.get("enabled", False)), "authority": "configured_not_executed",
                           "source": provenance(MODELS)})
    capabilities = [{"id": c["id"], "kind": c.get("kind", ""),
                     "requires": c.get("requires", ""), "source": provenance(MEDIA)}
                    for c in media["capabilities"]]
    # Dated source heads indicate historical provenance, NOT current canonical effect approval.
    historical = [v for v in source.get("branch_heads", []) if "american-empire" in v.get("branch", "").lower()]
    return {
      "schema": "american-empire.browser-brain.v1",
      "status": "git_registry_index_with_drive_references",
      "authority_policy": "Drive Brain is an evidence index, not executable runtime authority. Source presence != technical pass != visual acceptance.",
      "source_snapshot_date": source["snapshot_date"],
      "drive_links": [
        {"name":"GodRender Second Brain — Production Brain & FX Registry","url":DRIVE_BRAIN,"type":"external_authenticated_source"},
        {"name":"External Brain — Retrieval & Evidence Contract","url":DRIVE_CONTRACT,"type":"external_authenticated_source"},
        {"name":"Original American Empire Canon","url":CANON_DRIVE,"type":"canon_archive"},
        {"name":"American Empire Act I Media (adaptation)","url":MEDIA_DRIVE,"type":"noncanonical_adaptation_archive"}
      ],
      "native_studio":{"name":"GodRender Studio","readme_url":GIT_BASE+"studio/README.md",
         "launch":"python godrender_boot.py && python studio/stack.py",
         "local_url":"http://127.0.0.1:8080",
         "browser_automation":"not_connected_to_this_static_explorer",
         "note":"Registry selection and brief export do not invoke Studio, GPU, FFmpeg, ONNX, FX gates, or models."},
      "repository_sources":[provenance(p) for p in (FX_REGISTRY, WORKFLOWS, MODELS, MEDIA, SOURCES, BRAIN)],
      "fx":effects, "workflows":workflows, "models":model_list, "media_capabilities":capabilities,
      "historical_am_sources":historical,
      "counts":{"fx":len(effects),"workflows":len(workflows),"models":len(model_list),
                "media_capabilities":len(capabilities),"historical_am_sources":len(historical)},
      "links":{"branch":"https://github.com/SouthPaw302/GodRender/tree/world/american-empire",
               "studio":GIT_BASE+"studio/README.md",
               "godot":GIT_BASE+"worlds/american-empire/godot/project.godot"}
    }

def _write(path: Path, object: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(object, sort_keys=True, ensure_ascii=False, separators=(",",":"))+"\n",
                    encoding="utf-8")

def build(out: Path = DEFAULT_DEST) -> dict:
    out = out.resolve()
    archive = (WORLD / "archive").resolve()
    if (out == archive or archive in out.parents or out == WORLD or out == REPO
        or out == SOURCE or SOURCE in out.parents
        or out == (WORLD / "tools").resolve()
        or out == (WORLD / "engine").resolve()):
        raise ValueError("Cannot export into canon, source code, or a protected directory")
    if not SOURCE.is_dir():
        raise ValueError("Missing browser application source")
    bundle = build_bundle()
    brain = brain_index()
    geo = _load("worlds/american-empire/P6_GEOGRAPHY.json")
    land = _load("worlds/american-empire/geo/natural_earth_110m_land.geojson")
    if geo.get("schema") != "american-empire.geography.v1" or len(geo["nodes"]) != 12 or len(geo["routes"]) != 16:
        raise ValueError("P6 graph input has drifted")
    if land.get("type") != "FeatureCollection" or len(land["features"]) < 100:
        raise ValueError("Natural Earth coastline source is invalid")
    geo["source_geo_sha256"] = hashlib.sha256(json.dumps(geo,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()
    inhabitants = _load("worlds/american-empire/P7_INHABITANTS.json")
    p1matrix = _load("worlds/american-empire/archive/01_CANON_SOURCE/REALITY_MATRIX.json")
    if inhabitants.get("schema") != "american-empire.p7-inhabitants.v1" or len(inhabitants["protagonists"]) != 5 or len(inhabitants["organizations"]) != 5:
        raise ValueError("P7 actor manifest schema or roster drift")
    for actor in inhabitants["protagonists"]:
        found = next((p for p in p1matrix["point_of_view_characters"] if p["id"] == actor["source_id"]), None)
        if found is None or found["knows"] != actor["canon_knows"] or found["does_not_know"] != actor["canon_unknown_sealed"]:
            raise ValueError("P7 character knowledge diverged from immutable P1 source")
    original_orgs = {a["id"]:a for a in p1matrix["actors"]}
    if any(a["source_id"] not in original_orgs for a in inhabitants["organizations"]):
        raise ValueError("P7 institutional agent not in P1 source")
    inhabitants["source_manifest_sha256"] = hashlib.sha256(json.dumps(inhabitants,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()
    people_source = {"point_of_view_characters":p1matrix["point_of_view_characters"],"actors":p1matrix["actors"],
                     "authority":"locked_original_p1_quoted_reference_only"}
    model = _load("worlds/american-empire/P3_MODEL.json")
    references = [_load("worlds/american-empire/scenarios/examples/"+name+".json")
                  for name in ("baseline","independent-corridor","high-integration")]
    canonical_model = json.dumps(model,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
    if hashlib.sha256(canonical_model).hexdigest() != bundle["source"]["simulation_model_sha256"]:
        raise ValueError("P3 model has drifted from verified world bundle")
    # Explicit binding between the visual browser and P4/P3/P2/P1 evidence.
    brain["world_source"] = bundle["source"]
    brain["world_bundle_sha256"] = bundle["bundle_sha256"]
    if out.exists():
        for file in out.rglob("*"):
            if file.is_file() and file.name not in {"index.html", "app.js", "styles.css", "simulator.js", "live.js", "regions.js", "earth.js", "inhabitants.js", "people.js", "inhabitants.json", "people_source.json", "geo.json", "land.geojson", "world.json", "brain.json", "model.json", "reference_scenarios.json", "standalone.html", "explorer-preview.png"}:
                raise ValueError("Unexpected existing dist content: "+str(file))
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    for name in ("index.html","app.js","styles.css","simulator.js","live.js","regions.js","earth.js","inhabitants.js","people.js"):
        shutil.copy2(SOURCE / name, out / name)
    _write(out / "data" / "world.json",bundle)
    _write(out / "data" / "brain.json",brain)
    _write(out / "data" / "model.json",model)
    _write(out / "data" / "reference_scenarios.json",references)
    _write(out / "data" / "geo.json",geo)
    _write(out / "data" / "land.geojson",land)
    _write(out / "data" / "inhabitants.json",inhabitants)
    _write(out / "data" / "people_source.json",people_source)
    # One-file offline artifact: embed signed/source-pinned P3 rules and inputs.
    # Less-than escaping prevents an embedded JSON value from closing its script.
    html = (SOURCE / "index.html").read_text(encoding="utf-8")
    css = (SOURCE / "styles.css").read_text(encoding="utf-8")
    script_map = (
        ("simulator.js", (SOURCE / "simulator.js").read_text(encoding="utf-8")),
        ("app.js", (SOURCE / "app.js").read_text(encoding="utf-8")),
        ("live.js", (SOURCE / "live.js").read_text(encoding="utf-8")),
        ("regions.js", (SOURCE / "regions.js").read_text(encoding="utf-8")),
        ("earth.js", (SOURCE / "earth.js").read_text(encoding="utf-8")),
        ("inhabitants.js", (SOURCE / "inhabitants.js").read_text(encoding="utf-8")),
        ("people.js", (SOURCE / "people.js").read_text(encoding="utf-8")),
    )
    html = html.replace('<link rel="stylesheet" href="./styles.css">', '<style>'+css+'</style>')
    inline_data = (("embeddedWorld",bundle),("embeddedBrain",brain),
                   ("embeddedModel",model),("embeddedReference",references),
                   ("embeddedGeo",geo),("embeddedLand",land),
                   ("embeddedInhabitants",inhabitants),("embeddedPeopleSource",people_source))
    payload = "".join('<script type="application/json" id="'+label+'">'
                      +json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).replace("<","\\u003c")
                      +"</script>\n" for label,data in inline_data)
    for filename,js in script_map:
        html = html.replace('<script src="./'+filename+'" defer></script>',
                            '<script>'+js+'</script>')
    # Parsed before app startup in file:// mode (no fetch fallback permitted).
    html = html.replace('<script>',payload+'<script>',1)
    (out / "standalone.html").write_text(html,encoding="utf-8")
    return {"schema":"american-empire.web-build.v1","world_bundle_sha256":bundle["bundle_sha256"],
            "brain_fx":brain["counts"]["fx"],"brain_workflows":brain["counts"]["workflows"],
            "brain_models":brain["counts"]["models"],"source_hashes":{x["path"]:x["git_blob_sha1"]
            for x in brain["repository_sources"]},"output":str(out)}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=DEFAULT_DEST)
    parser.add_argument("--repro",action="store_true")
    args=parser.parse_args()
    info=build(args.output)
    if args.repro:
        files = {p.relative_to(args.output):hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in args.output.rglob("*") if p.is_file()}
        build(args.output)
        now = {p.relative_to(args.output):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in args.output.rglob("*") if p.is_file()}
        if files != now:
            raise ValueError("Non-reproducible browser build")
    print(json.dumps(info,indent=2,sort_keys=True))
if __name__=="__main__":
    main()
