#!/usr/bin/env python3
"""American Empire P3 scenario runner: run, branch, compare and replay."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from simulation import ScenarioError, Simulation  # noqa: E402
from world_matrix import CanonIntegrityError  # noqa: E402


def _json_file(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _emit(data, output: Path | None, root: Path):
    rendered = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output is None:
        print(rendered, end="")
        return
    target = output.expanduser().resolve()
    allowed_generated = (root / "scenarios" / "generated").resolve()
    within_world = target == root or root in target.parents
    generated = target != allowed_generated and allowed_generated in target.parents
    if within_world and not generated:
        raise ScenarioError(
            "Refusing to write into the world source tree; only scenarios/generated/ is writable"
        )
    if target.suffix.lower() != ".json":
        raise ScenarioError("P3 output must use .json")
    if target.exists() or target.is_symlink():
        raise ScenarioError("Refusing to overwrite existing output; use another name")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    print(f"Counterfactual P3 JSON saved: {target}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-root", type=Path, default=ROOT)
    cmd = parser.add_subparsers(dest="command", required=True)
    cmd.add_parser("status")
    run = cmd.add_parser("run", help="Execute 2026–2037 counterfactual")
    run.add_argument("--scenario", type=Path, required=True)
    run.add_argument("--output", type=Path)
    fork = cmd.add_parser("fork", help="Fork a scenario after a selected historical simulation year")
    fork.add_argument("--parent", type=Path, required=True)
    fork.add_argument("--year", type=int, required=True)
    fork.add_argument("--name", required=True)
    fork.add_argument("--events", type=Path, required=True, help="JSON array of future event definitions")
    fork.add_argument("--output", type=Path)
    compare = cmd.add_parser("compare", help="Compare two deterministic what-if simulations")
    compare.add_argument("--left", type=Path, required=True)
    compare.add_argument("--right", type=Path, required=True)
    compare.add_argument("--output", type=Path)
    replay = cmd.add_parser("replay", help="Verify every field of a previous run receipt")
    replay.add_argument("--receipt", type=Path, required=True)
    opts = parser.parse_args(argv)
    try:
        world = Simulation(root=opts.world_root)
        if opts.command == "status":
            output = {
                "phase": "P3", "authority_layer": "scenario_only",
                "source_world_sha256": world.graph_digest,
                "model_sha256": world.model_digest,
                "model_id": world.model["id"],
                "years": [2026, 2037],
                "variables": world.initial,
                "action_types": sorted(world.model["actions"]),
                "source_canon_integrity": "verified",
            }
            _emit(output, None, world.root)
        elif opts.command == "run":
            _emit(world.run(_json_file(opts.scenario)), opts.output, world.root)
        elif opts.command == "fork":
            events = _json_file(opts.events)
            _emit(world.fork(_json_file(opts.parent), name=opts.name,
                             fork_year=opts.year, additional_events=events),
                  opts.output, world.root)
        elif opts.command == "compare":
            _emit(world.compare(_json_file(opts.left), _json_file(opts.right)),
                  opts.output, world.root)
        elif opts.command == "replay":
            _emit(world.replay(_json_file(opts.receipt)), None, world.root)
        return 0
    except (ScenarioError, CanonIntegrityError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"AMERICAN EMPIRE P3 REJECTED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
