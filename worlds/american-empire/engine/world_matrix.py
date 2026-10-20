"""Read-only, provenance-backed world graph for the locked American Empire canon.

P2 is a query/index layer, NOT an evolving simulation. Its only factual data
comes from the hash-pinned source Matrix. Inferences, proposals and adaptations
are isolated and clearly classified.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

WORLD_ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = "01_CANON_SOURCE/REALITY_MATRIX.json"
CHRONICLES = (
    "02_CHRONICLES/CHRONICLE_02_THE_FIRST_WINTER.md",
    "02_CHRONICLES/CHRONICLE_03_THE_MEASURE.md",
    "02_CHRONICLES/CHRONICLE_04_CORRIDOR_TREATIES.md",
)
EXPECTED_TIMELINE = list(range(2026, 2038))
KINDS = ("institution", "actor", "system", "person", "event", "variable", "reality_anchor", "document")


class CanonIntegrityError(RuntimeError):
    """Locked sources, references or structural invariants are invalid."""


class UnknownEntityError(KeyError):
    """Entity is not in this canon graph."""


def _load_guard(root: Path):
    spec = importlib.util.spec_from_file_location("ae_p1_guard", root / "tools" / "verify_canon.py")
    if spec is None or spec.loader is None:
        raise CanonIntegrityError("P1 guard is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unique(items: list[dict], field: str, label: str) -> None:
    values = [str(item[field]) for item in items]
    if len(values) != len(set(values)):
        raise CanonIntegrityError(f"Duplicate {label} {field}")


def _source(path: str, pointer: str, lock: dict, *, layer: str = "established") -> dict:
    names = {record["path"]: record["git_blob_sha1"] for record in lock["files"]}
    if path not in names:
        raise CanonIntegrityError(f"Unpinned source: {path}")
    return {
        "path": f"archive/{path}",
        "json_pointer": pointer if pointer.startswith("/") else "",
        "git_blob_sha1": names[path],
        "authority_layer": layer,
        "source_commit": lock["source"]["commit"],
    }


def _proposal_sections(content: str, path: str, lock: dict) -> list[dict]:
    """Extract proposal sections without interpreting candidate facts as canon."""
    lines = content.splitlines()
    output = []
    in_proposal = False
    active: list[str] = []
    title = ""
    anchor_line = 0

    def flush():
        if not active:
            return
        body = "\n".join(active).strip()
        if body:
            output.append({
                "id": f"proposal:chronicle-{CHRONICLES.index(path) + 2:02d}",
                "label": title,
                "text": body,
                "status": "candidate_unapproved",
                "source": _source(path, "", lock, layer="proposal"),
                "source_heading_line": anchor_line,
            })

    for number, line in enumerate(lines, 1):
        m = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if m:
            if in_proposal:
                flush()
                in_proposal = False
                active = []
            heading = m.group(1).strip()
            if heading.casefold() in ("additive canon proposed", "proposed additive canon"):
                in_proposal = True
                anchor_line = number
                title = heading
        elif in_proposal:
            active.append(line)
    if in_proposal:
        flush()
    return output


class WorldMatrix:
    """Immutable-by-interface, deterministic graph projected from P1 canonical sources.

    Every public result is a fresh deep copy. No method mutates archive bytes.
    No network or AI generation is used. An optional scenario is simply tagged,
    never merged into this graph.
    """

    def __init__(self, *, root: Path | None = None):
        self.root = (root or WORLD_ROOT).resolve()
        guard = _load_guard(self.root)
        errors = guard.verify(self.root)
        if errors:
            raise CanonIntegrityError("P1 canon verification failed: " + "; ".join(errors))
        self._lock = json.loads((self.root / "CANON_LOCK.json").read_text(encoding="utf-8"))
        self._matrix = json.loads((self.root / "archive" / MATRIX_PATH).read_text(encoding="utf-8"))
        self._validate()
        self._nodes: dict[str, dict] = {}
        self._edges: dict[str, dict] = {}
        self._proposals: list[dict] = []
        self._documents: list[dict] = []
        self._build()
        self._digest = hashlib.sha256(
            json.dumps(self._payload(include_digest=False), ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _validate(self):
        m = self._matrix
        expected = ("actors", "imperial_stack", "point_of_view_characters", "ten_year_phases",
                    "collapse_chain", "simulation_variables", "reality_anchors", "key_relationships")
        for key in expected:
            if not isinstance(m.get(key), list):
                raise CanonIntegrityError(f"Missing list: {key}")
        for key in expected[:-1]:
            _unique(m[key], "id" if key not in ("ten_year_phases", "collapse_chain") else
                    ("year" if key == "ten_year_phases" else "order"), key)
        years = [int(entry["year"]) for entry in m["ten_year_phases"]]
        if years != EXPECTED_TIMELINE:
            raise CanonIntegrityError(f"Unexpected canonical chronology: {years}")
        if m.get("reality_cutoff") != "2026-08-31":
            raise CanonIntegrityError("Reality cutoff changed")
        actors = {a["id"] for a in m["actors"]}
        systems = {a["id"] for a in m["imperial_stack"]}
        for link in m["key_relationships"]:
            if link.get("from") not in actors | systems or link.get("to") not in actors | systems:
                raise CanonIntegrityError(f"Unknown relationship endpoint: {link}")
            if not -5 <= link.get("strength", -999) <= 5:
                raise CanonIntegrityError("Out-of-range relationship strength")
        for item in m["imperial_stack"]:
            for dependency in item.get("prerequisites", []):
                if dependency not in systems:
                    raise CanonIntegrityError(f"Unresolved prerequisite {dependency}")
        if [int(x["order"]) for x in m["collapse_chain"]] != list(range(1, len(m["collapse_chain"]) + 1)):
            raise CanonIntegrityError("Collapse-chain sequence is not contiguous")

    def _node(self, ident: str, label: str, kind: str, attributes: dict, pointer: str):
        if ident in self._nodes or kind not in KINDS:
            raise CanonIntegrityError(f"Duplicate/unknown node: {ident} ({kind})")
        self._nodes[ident] = {
            "id": ident, "name": label, "kind": kind,
            "layer": "established", "attributes": copy.deepcopy(attributes),
            "source": _source(MATRIX_PATH, pointer, self._lock),
        }

    def _edge(self, ident: str, start: str, end: str, kind: str, label: str,
              pointer: str, *, strength: int | None = None, derived: bool = False):
        if ident in self._edges or start not in self._nodes or end not in self._nodes:
            raise CanonIntegrityError(f"Invalid graph edge: {ident}: {start} -> {end}")
        self._edges[ident] = {
            "id": ident, "from": start, "to": end, "kind": kind, "label": label,
            "strength": strength, "derived": derived,
            "layer": "established",
            "source": _source(MATRIX_PATH, pointer, self._lock),
        }

    def _build(self):
        m = self._matrix
        self._node("institution:continuity", m["hidden_history"]["organization"], "institution",
                   m["hidden_history"], "/hidden_history")
        for kind, key, prefix in (
            ("actor", "actors", "actor"),
            ("system", "imperial_stack", "system"),
            ("person", "point_of_view_characters", "person"),
            ("variable", "simulation_variables", "variable"),
            ("reality_anchor", "reality_anchors", "anchor"),
        ):
            for index, obj in enumerate(m[key]):
                self._node(f"{prefix}:{obj['id']}", obj["name"] if "name" in obj else obj["fact"],
                           kind, obj, f"/{key}/{index}")
        for index, obj in enumerate(m["ten_year_phases"]):
            self._node(f"event:{obj['year']}", obj["name"], "event", obj,
                       f"/ten_year_phases/{index}")
        for index, obj in enumerate(m["collapse_chain"]):
            self._node(f"event:collapse-{obj['order']}", f"Collapse pressure {obj['order']}",
                       "event", obj, f"/collapse_chain/{index}")

        # Recorded relationships, including signed strengths. Never infer edges
        # from the prose of a chronicle or an adaptation.
        for i, obj in enumerate(m["key_relationships"]):
            self._edge(f"relation:{i+1:02d}", self._canonical_id(obj["from"]),
                       self._canonical_id(obj["to"]), "source_relationship",
                       obj["relation"], f"/key_relationships/{i}", strength=obj["strength"])
        for i, obj in enumerate(m["imperial_stack"]):
            for j, dependency in enumerate(obj.get("prerequisites", [])):
                self._edge(f"prerequisite:{obj['id']}:{dependency}",
                           f"system:{obj['id']}", f"system:{dependency}", "prerequisite",
                           "requires", f"/imperial_stack/{i}/prerequisites/{j}")
        for i in range(len(m["ten_year_phases"]) - 1):
            older = m["ten_year_phases"][i]["year"]
            newer = m["ten_year_phases"][i+1]["year"]
            self._edge(f"chronology:{older}:{newer}", f"event:{older}", f"event:{newer}",
                       "chronological_successor", "precedes",
                       f"/ten_year_phases/{i+1}/year", derived=True)
        for i in range(len(m["collapse_chain"]) - 1):
            self._edge(f"collapse_sequence:{i+1}:{i+2}", f"event:collapse-{i+1}",
                       f"event:collapse-{i+2}", "causal_sequence", "next recorded pressure",
                       f"/collapse_chain/{i+1}/order", derived=True)
        for i, actor in enumerate(m["actors"]):
            if actor["type"] == "Continuity faction":
                self._edge(f"member:{actor['id']}", f"actor:{actor['id']}",
                           "institution:continuity", "affiliation", "Continuity faction",
                           f"/actors/{i}/type", derived=True)

        # Readable source documents are indexed by identity and source hash only.
        # Proposed addenda remain in a separate unapproved, queryable layer.
        for path in CHRONICLES:
            text = (self.root / "archive" / path).read_text(encoding="utf-8")
            self._documents.append({
                "id": f"chronicle:{CHRONICLES.index(path)+2:02d}",
                "name": Path(path).stem,
                "layer": "source_narrative",
                "source": _source(path, "", self._lock, layer="source_narrative"),
            })
            self._proposals.extend(_proposal_sections(text, path, self._lock))

    @staticmethod
    def _canonical_id(raw: str) -> str:
        return f"{'actor' if raw.startswith('A') else 'system'}:{raw}"

    @property
    def digest(self) -> str:
        """Deterministic semantic graph digest (distinct from Git's blob SHA-1)."""
        return self._digest

    def counts(self) -> dict:
        return {
            "nodes": len(self._nodes), "edges": len(self._edges),
            "proposed_sections": len(self._proposals),
            "source_chronicles": len(self._documents),
            "kinds": {kind: sum(n["kind"] == kind for n in self._nodes.values()) for kind in KINDS},
        }

    def list_entities(self, *, kind: str | None = None) -> list[dict]:
        if kind and kind not in KINDS:
            raise ValueError(f"Unknown kind: {kind}")
        return copy.deepcopy([n for n in self._nodes.values()
                              if kind is None or n["kind"] == kind])

    def entity(self, ident: str) -> dict:
        if ident not in self._nodes:
            raise UnknownEntityError(ident)
        return copy.deepcopy(self._nodes[ident])

    def relations(self, ident: str, *, direction: str = "both") -> list[dict]:
        if ident not in self._nodes:
            raise UnknownEntityError(ident)
        if direction not in ("incoming", "outgoing", "both"):
            raise ValueError("direction must be incoming, outgoing, or both")
        edges = []
        for edge in self._edges.values():
            if (direction in ("outgoing", "both") and edge["from"] == ident or
                    direction in ("incoming", "both") and edge["to"] == ident):
                linked = edge["to"] if edge["from"] == ident else edge["from"]
                relation = copy.deepcopy(edge)
                relation["neighbor"] = {"id": linked, "name": self._nodes[linked]["name"]}
                edges.append(relation)
        return edges

    def timeline(self, *, year: int | None = None, through: bool = False) -> list[dict]:
        if year is not None and year not in EXPECTED_TIMELINE:
            raise ValueError("Year must be within the canonical 2026–2037 spine")
        entries = [self._nodes[f"event:{y}"] for y in EXPECTED_TIMELINE
                   if year is None or (y <= year if through else y == year)]
        return copy.deepcopy(entries)

    def documents(self) -> list[dict]:
        return copy.deepcopy(self._documents)

    def proposals(self) -> list[dict]:
        return copy.deepcopy(self._proposals)

    def search(self, query: str, *, layer: str = "established") -> list[dict]:
        """Basic case-insensitive literal search; no embeddings or invented answers."""
        term = query.strip().casefold()
        if not term:
            raise ValueError("Search query must not be empty")
        if layer == "established":
            entries = self._nodes.values()
            return copy.deepcopy([entry for entry in entries
                                  if term in json.dumps({"name": entry["name"],
                                        "attributes": entry["attributes"]}, ensure_ascii=False).casefold()])
        if layer == "proposal":
            return copy.deepcopy([entry for entry in self._proposals
                                  if term in (entry["label"] + "\n" + entry["text"]).casefold()])
        if layer == "source_narrative":
            return copy.deepcopy([entry for entry in self._documents
                                  if term in entry["name"].casefold()])
        if layer == "adaptation":
            return []  # No adaptation content imported in P2; use ADAPTATION_LINKS.md.
        if layer == "scenario":
            return []  # Hypotheticals belong to P3, not this baseline.
        raise ValueError("Layer must be established, proposal, source_narrative, adaptation or scenario")

    def _payload(self, *, include_digest: bool) -> dict:
        doc = {
            "schema": "american-empire.world-graph.v1",
            "stage": "P2_QUERY_ONLY",
            "fictional_reality_cutoff": "2026-08-31",
            "timeline_range": [2026, 2037],
            "source": {
                "repo": self._lock["source"]["repository"],
                "commit": self._lock["source"]["commit"],
                "matrix_git_blob_sha1": next(x["git_blob_sha1"] for x in self._lock["files"]
                                             if x["path"] == MATRIX_PATH),
            },
            "counts": self.counts(),
            "nodes": list(self._nodes.values()),
            "edges": list(self._edges.values()),
            "documents": self._documents,
            "proposal_sections": self._proposals,
            "excluded_layers": ["adaptation", "scenario"],
        }
        if include_digest:
            doc["semantic_sha256"] = self._digest
        return doc

    def export(self) -> dict:
        """JSON-serializable versioned snapshot. Does not modify canonical sources."""
        return copy.deepcopy(self._payload(include_digest=True))
