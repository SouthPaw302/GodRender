#!/usr/bin/env python3
"""American Empire P2: query the original canon without modifying it."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "engine"))
from world_matrix import CanonIntegrityError, UnknownEntityError, WorldMatrix  # noqa: E402


def _display(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))


def _export(graph: WorldMatrix, path: Path | None):
    payload = json.dumps(graph.export(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path is None:
        print(payload, end="")
        return
    target = path.expanduser().resolve()
    archive = (graph.root / "archive").resolve()
    locked = (graph.root / "CANON_LOCK.json").resolve()
    if target == locked or target == archive or archive in target.parents:
        raise ValueError("Refusing to write into the canonical archive or its lock")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")
    print(f"Wrote derived snapshot: {target}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-root", type=Path, default=HERE,
                        help="World folder containing CANON_LOCK.json and archive/")
    cmd = parser.add_subparsers(dest="command", required=True)

    cmd.add_parser("status", help="Graph counts and semantic fingerprint")

    list_cmd = cmd.add_parser("list", help="Enumerate canon nodes")
    list_cmd.add_argument("--kind", default=None,
                          choices=("institution", "actor", "system", "person", "event",
                                   "variable", "reality_anchor", "document"))

    show = cmd.add_parser("show", help="Inspect an exact entity ID and provenance")
    show.add_argument("id", help="e.g. actor:A1, system:S1, person:P3, event:2030")

    relations = cmd.add_parser("relations", help="Source-backed graph links for an entity")
    relations.add_argument("id")
    relations.add_argument("--direction", default="both",
                           choices=("both", "incoming", "outgoing"))

    timeline = cmd.add_parser("timeline", help="Inspect historical sequence, not sim predictions")
    timeline.add_argument("--year", type=int)
    timeline.add_argument("--through", action="store_true")

    query = cmd.add_parser("search", help="Literal search, with explicit authority layer")
    query.add_argument("text")
    query.add_argument("--layer", default="established",
                       choices=("established", "proposal", "source_narrative", "adaptation", "scenario"))

    cmd.add_parser("proposals", help="View unapproved proposal sections separately")
    cmd.add_parser("documents", help="Show indexed chronicle provenance")
    output = cmd.add_parser("export", help="Deterministically serialize read-only graph JSON")
    output.add_argument("--output", type=Path, default=None,
                        help="Optional derived-file path; archive/ and CANON_LOCK.json are forbidden")

    opts = parser.parse_args(argv)
    try:
        graph = WorldMatrix(root=opts.world_root)
        if opts.command == "status":
            _display({"stage": "P2_QUERY_ONLY", "semantic_sha256": graph.digest,
                      "counts": graph.counts(), "canon_verified": True})
        elif opts.command == "list":
            _display(graph.list_entities(kind=opts.kind))
        elif opts.command == "show":
            _display(graph.entity(opts.id))
        elif opts.command == "relations":
            _display(graph.relations(opts.id, direction=opts.direction))
        elif opts.command == "timeline":
            _display(graph.timeline(year=opts.year, through=opts.through))
        elif opts.command == "search":
            _display(graph.search(opts.text, layer=opts.layer))
        elif opts.command == "proposals":
            _display(graph.proposals())
        elif opts.command == "documents":
            _display(graph.documents())
        elif opts.command == "export":
            _export(graph, opts.output)
        return 0
    except (CanonIntegrityError, UnknownEntityError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"American Empire P2 query rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
