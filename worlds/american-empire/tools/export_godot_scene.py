#!/usr/bin/env python3
"""Convert one VERIFIED browser P7 snapshot into a Godot 4 read-only scene contract.

The source is a real browser-exported deterministic simulation receipt.
Not a film/character reconstruction: all generated geometry is a schematic 3D
proof, and all action/metric data remains scenario_only. No Drive media used.
"""
from __future__ import annotations
import argparse
import json
import hashlib
from pathlib import Path

from population_model import assert_run, canonical, digest

REPO = Path(__file__).resolve().parents[3]
WORLD = REPO / "worlds" / "american-empire"
SCHEMA = "american-empire.godot-scene-contract.v1"


def build(receipt: dict, actor: str = "claire", year: int = 2027) -> dict:
    frame, person = assert_run(receipt, actor, year)
    p6 = json.loads((WORLD / "P6_GEOGRAPHY.json").read_text(encoding="utf-8"))
    p8 = json.loads((WORLD / "P8_FILM_BRIDGE.json").read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in p6["nodes"]}
    nodes[p8["location"]["id"]] = p8["location"]
    place_id = person["place"]
    if place_id not in nodes or place_id not in frame["places"]:
        raise ValueError("Actor location not present in approved local source")
    site = nodes[place_id]
    for axis, bound in (("lat", 90), ("lon", 180)):
        if not isinstance(site[axis], (int, float)) or abs(site[axis]) > bound:
            raise ValueError("Malformed geographic reference")
    local = frame["places"][place_id]
    service, autonomy = local["service"], local["independence"]
    if not all(type(v) is int and 0 <= v <= 100 for v in (service, autonomy)):
        raise ValueError("Invalid local indices")
    decision = next((x for x in frame["decisions"] if x["id"] == actor), None)
    if not decision or decision["place"] != place_id:
        raise ValueError("No coherent actor decision for source year")
    if not all(type(person[k]) is int and 0 <= person[k] <= 100 for k in ("budget", "standing")):
        raise ValueError("Actor resources outside bound")
    if year < int(next((a["known_from_year"] for a in p8["agents"] if a["id"] == actor), 2026)):
        raise ValueError("Film actor requested before provisional simulation anchor")
    if receipt["p3_run_sha256"] == "" or receipt["manifest_sha256"] == "":
        raise ValueError("Model provenance unavailable")
    contract = {
        "schema": SCHEMA, "authority_layer": "scenario_only",
        "render_classification": "technical_geometry_proof_not_approved_film",
        "source": {
            "p7_run_sha256": receipt["run_sha256"],
            "p7_snapshot_sha256": frame["sha256"],
            "p3_run_sha256": receipt["p3_run_sha256"],
            "p7_manifest_sha256": receipt["manifest_sha256"],
            "location_source": site["source"]["path"],
            "location_authority": site["numeric_authority"],
        },
        "world": {
            "year": year, "place_id": place_id, "display_name": site["name"],
            "latitude": site["lat"], "longitude": site["lon"],
            "service": service, "independence": autonomy,
        },
        "actor": {
            "id": actor, "simulation_kind": "modeled_character_marker_not_face_or_costume",
            "place": place_id, "budget": person["budget"],
            "standing": person["standing"],
            "last_action": decision["action"],
            "memory_count": len(person["memory"]),
            "knowledge_count": len(person["knowledge"]),
        },
        "production": {
            "branch_source": "world/american-empire",
            "native_boot_checkout": "local_song_alias_only",
            "engine": "Godot 4 3D",
            "media_refs_embedded": False,
            "reuses_canon_assets": False,
            "no_unapproved_source_media": True,
            "scene_seed": int(frame["sha256"][:8], 16),
        },
        "limitations": [
            "Schematic 3D city block; not a reconstruction of the Paris film set.",
            "No Drive/source media imported or displayed.",
            "Region/actor values and 2027 Paris placement are scenario-only.",
            "Godot reads this contract, not P7 character memory or other private source facts.",
        ],
    }
    contract["contract_sha256"] = digest(contract)
    return contract


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--actor", default="claire")
    parser.add_argument("--year", type=int, default=2027)
    args = parser.parse_args()
    world = json.loads(args.receipt.read_text(encoding="utf-8"))
    contract = build(world, args.actor, args.year)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(contract, sort_keys=True, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("AE_SCENE_CONTRACT_PASS "+json.dumps({
        "actor": contract["actor"]["id"], "place": contract["world"]["place_id"],
        "year": contract["world"]["year"], "sha256": contract["contract_sha256"],
        "p7_snapshot_sha256": contract["source"]["p7_snapshot_sha256"],
        "media_refs_embedded": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
