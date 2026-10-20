#!/usr/bin/env python3
"""P4 bridge: build a read-only Godot world explorer bundle from verified P1/P2/P3.

Never fabricates canonical geopolitical data or touches the original archive.
The only simulated values are clearly tagged P3 counterfactual scenario output.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORLD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORLD / "engine"))
from simulation import Simulation, ScenarioError, canonical_bytes, digest  # noqa: E402

SCHEMA = "american-empire.godot-explorer-bundle.v1"
CASES = (
    ("baseline.json", "No intervention"),
    ("independent-corridor.json", "Independent corridor"),
    ("high-integration.json", "High integration"),
)
KINDS = {"actor", "system"}
EDGES = {"source_relationship", "prerequisite"}
YEAR_RANGE = range(2026, 2038)


def build_bundle(world: Path = WORLD) -> dict:
    sim = Simulation(root=world.resolve())  # includes P1 hash gate and P2 graph creation
    graph = sim.world
    exported = graph.export()
    nodes = [n for n in exported["nodes"] if n["kind"] in KINDS]
    shown = {n["id"] for n in nodes}
    edges = [
        e for e in exported["edges"]
        if e["kind"] in EDGES and e["from"] in shown and e["to"] in shown
    ]
    people = graph.list_entities(kind="person")
    variables = graph.list_entities(kind="variable")
    years = [
        {"year": int(n["attributes"]["year"]), "title": n["name"],
         "summary": n["attributes"]["turn"], "source": n["source"]}
        for n in graph.timeline()
    ]
    scenarios = []
    for filename, name in CASES:
        path = world / "scenarios" / "examples" / filename
        spec = json.loads(path.read_text(encoding="utf-8"))
        run = sim.run(spec)
        if not sim.replay(run)["verified"]:
            raise ScenarioError(f"Scenario receipt cannot replay: {filename}")
        scenarios.append({
            "id": spec["id"], "name": name,
            "authority_layer": "scenario_only",
            "run_sha256": run["run_sha256"],
            "source_world_sha256": run["source_world_sha256"],
            "model_sha256": run["model_sha256"],
            "snapshots": [
                {"year": snap["year"], "state": snap["state"],
                 "indicators": snap["indicators"],
                 "scenario_event_ids": snap["scenario_event_ids"],
                 "snapshot_sha256": snap["sha256"]}
                for snap in run["snapshots"]
            ],
        })
    payload = {
        "schema": SCHEMA,
        "classification": "interactive schematic, not a geographic map",
        "authority_policy": {
            "entities": "original Reality Matrix graph (established)",
            "historical_anchors": "original 2026–2037 authored chronology",
            "numeric_variables": "hypothetical P3 scenario_only",
            "paris_adaptation": "not imported; noncanonical until separately approved",
            "fictional": True,
        },
        "source": {
            "world_graph_sha256": graph.digest,
            "matrix_blob_sha1": exported["source"]["matrix_git_blob_sha1"],
            "canon_commit": exported["source"]["commit"],
            "simulation_model_sha256": sim.model_digest,
        },
        "year_min": 2026, "year_max": 2037,
        "years": years,
        "nodes": nodes, "edges": edges,
        "people": people, "variables": variables,
        "scenarios": scenarios,
        "sources_read_only": True,
    }
    validate_bundle(payload)
    payload["bundle_sha256"] = digest(payload)
    return payload


def validate_bundle(payload: dict) -> None:
    if payload.get("schema") != SCHEMA:
        raise ValueError("Explorer schema mismatch")
    if payload.get("sources_read_only") is not True:
        raise ValueError("Bundle must never mutate original canon")
    if payload.get("year_min") != 2026 or payload.get("year_max") != 2037:
        raise ValueError("Unexpected explorer chronology bounds")
    if [int(y["year"]) for y in payload["years"]] != list(YEAR_RANGE):
        raise ValueError("Timeline spine mismatch")
    nodes = {n["id"] for n in payload["nodes"]}
    if len(nodes) != 16 or len(payload["nodes"]) != 16:
        raise ValueError("Expected exactly ten actors and six systems")
    if not all(e["from"] in nodes and e["to"] in nodes for e in payload["edges"]):
        raise ValueError("Unresolved graph edge")
    if any(e["kind"] not in EDGES for e in payload["edges"]):
        raise ValueError("Unexpected graph edge class")
    if len(payload["people"]) != 5 or len(payload["variables"]) != 7:
        raise ValueError("P2 person or variable index mismatch")
    if [s["id"] for s in payload["scenarios"]] != [
        "baseline", "independent-corridor", "high-integration"
    ]:
        raise ValueError("Nonapproved scenario source")
    for scenario in payload["scenarios"]:
        if scenario["authority_layer"] != "scenario_only":
            raise ValueError("Simulation numeric history promoted to canon")
        if len(scenario["snapshots"]) != 12:
            raise ValueError("Incomplete annual P3 history")
        if scenario["source_world_sha256"] != payload["source"]["world_graph_sha256"]:
            raise ValueError("Cross-world scenario loaded")
        if scenario["model_sha256"] != payload["source"]["simulation_model_sha256"]:
            raise ValueError("Cross-model scenario loaded")
        for y, snapshot in zip(YEAR_RANGE, scenario["snapshots"]):
            if snapshot["year"] != y:
                raise ValueError("Inconsistent scenario timestamp")
            if sorted(snapshot["state"]) != [f"V{x}" for x in range(1, 8)]:
                raise ValueError("Lost P3 global state")
            if any(type(x) is not int or not 0 <= x <= 100 for x in snapshot["state"].values()):
                raise ValueError("Scenario variables invalid")
    if payload["authority_policy"].get("paris_adaptation") != (
        "not imported; noncanonical until separately approved"
    ):
        raise ValueError("Adaptation authority was modified")


def write_bundle(out: Path, root: Path = WORLD) -> dict:
    bundle = build_bundle(root)
    out = out.expanduser().resolve()
    canon_dir = (root / "archive").resolve()
    forbidden = ((root / "CANON_LOCK.json").resolve(),)
    if out in forbidden or out == canon_dir or canon_dir in out.parents:
        raise ValueError("Cannot place viewer bundle inside P1 canonical archive")
    if out.suffix != ".json":
        raise ValueError("Output must be .json")
    out.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    out.write_text(content, encoding="utf-8")
    return {
        "bundle_sha256": bundle["bundle_sha256"], "file": str(out),
        "bytes": len(content.encode("utf-8")), "nodes": len(bundle["nodes"]),
        "edges": len(bundle["edges"]), "years": len(bundle["years"]),
        "scenarios": [x["id"] for x in bundle["scenarios"]],
        "source_world_sha256": bundle["source"]["world_graph_sha256"],
        "source_model_sha256": bundle["source"]["simulation_model_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-root", type=Path, default=WORLD)
    parser.add_argument("--output", type=Path, default=WORLD / "godot" / "data" / "world_bundle.json")
    parser.add_argument("--check-reproducible", action="store_true")
    args = parser.parse_args()
    try:
        info = write_bundle(args.output, args.world_root)
        if args.check_reproducible:
            original = args.output.read_bytes()
            info_second = write_bundle(args.output, args.world_root)
            if args.output.read_bytes() != original or info_second["bundle_sha256"] != info["bundle_sha256"]:
                raise ValueError("Nonreproducible P4 export")
        print(json.dumps(info, indent=2, sort_keys=True))
        return 0
    except (ScenarioError, OSError, ValueError, KeyError, TypeError) as e:
        print(f"AMERICAN EMPIRE P4 EXPORT FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
