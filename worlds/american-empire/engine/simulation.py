"""American Empire P3 — deterministic, canon-safe counterfactual world simulation.

The engine cannot alter P1/P2 canon. It generates a *scenario* projection from the
original Matrix variables; no computed outcome is an established historical fact.
All mechanics are explicitly declared and versioned in P3_MODEL.json.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from world_matrix import WorldMatrix

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "american-empire.scenario.v1"
RUN_SCHEMA = "american-empire.scenario-run.v1"
YEAR_START, YEAR_END = 2026, 2037
SLUG = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
EVENT_ID = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
MODEL_PATH = "P3_MODEL.json"
VARIABLES = tuple(f"V{x}" for x in range(1, 8))


class ScenarioError(ValueError):
    """Reject invalid or misleading what-if data without mutating any source."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _strict_integer(value: Any, low: int, high: int, label: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ScenarioError(f"{label} must be an integer in [{low}, {high}]")
    return value


def _bounded(value: int) -> int:
    return max(0, min(100, value))


def _exact_fields(item: dict, required: set, optional: set, label: str) -> None:
    if not isinstance(item, dict):
        raise ScenarioError(f"{label} must be an object")
    if set(item) - (required | optional) or required - set(item):
        raise ScenarioError(f"{label} fields invalid; required={sorted(required)}, optional={sorted(optional)}")


class Simulation:
    """Exact integer model over P2's verified Matrix initial values."""

    def __init__(self, *, root: Path | None = None):
        self.root = (root or ROOT).resolve()
        self.world = WorldMatrix(root=self.root)  # P1 integrity guard runs first
        try:
            self.model = json.loads((self.root / MODEL_PATH).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ScenarioError(f"Cannot read P3 model: {exc}") from exc
        self._validate_model()
        self.model_digest = digest(self.model)
        self.graph_digest = self.world.digest
        self.initial = {
            node["attributes"]["id"]: _strict_integer(node["attributes"]["initial"], 0, 100, "canonical seed")
            for node in self.world.list_entities(kind="variable")
        }
        if set(self.initial) != set(VARIABLES):
            raise ScenarioError("P2 source variable keys are not V1..V7")

    def _validate_model(self):
        m = self.model
        _exact_fields(
            m,
            {"schema", "id", "phase", "source_authority", "classification", "seeded_from",
             "initial_year", "last_year", "deterministic_policy", "variable_ids",
             "annual_feedback_algorithm", "actions", "annual_feedback_notes",
             "proxy_mapping", "limitations"}, set(), "model"
        )
        if m["schema"] != "american-empire.simulation-model.v1":
            raise ScenarioError("Model schema must be v1")
        if m["classification"] != "illustrative_mechanics_not_established_history":
            raise ScenarioError("Model cannot impersonate established canon")
        if m["initial_year"] != YEAR_START or m["last_year"] != YEAR_END:
            raise ScenarioError("Model timeline may not silently diverge from canon")
        if m["variable_ids"] != list(VARIABLES):
            raise ScenarioError("Model variables must match the source Matrix")
        if m["annual_feedback_algorithm"] != "simultaneous_p3_feedback_v1":
            raise ScenarioError("Unrecognized annual feedback algorithm")
        if not isinstance(m["actions"], dict) or not m["actions"]:
            raise ScenarioError("Model actions cannot be empty")
        for key, action in m["actions"].items():
            if not SLUG.fullmatch(key.replace("_", "-")):
                raise ScenarioError(f"Invalid action name: {key}")
            _exact_fields(action, {"label", "deltas"}, set(), f"action {key}")
            if not isinstance(action["label"], str) or not action["label"].strip():
                raise ScenarioError(f"Action label missing: {key}")
            if not isinstance(action["deltas"], dict) or not action["deltas"]:
                raise ScenarioError(f"Action effects missing: {key}")
            if not set(action["deltas"]) <= set(VARIABLES):
                raise ScenarioError(f"Action affects nonexistent variables: {key}")
            for variable, amount in action["deltas"].items():
                _strict_integer(amount, -25, 25, f"{key}/{variable}")

    def validate_scenario(self, scenario: dict) -> dict:
        _exact_fields(scenario, {"schema", "id", "events"}, {"description", "source_world_sha256", "branch"}, "scenario")
        if scenario["schema"] != SCHEMA:
            raise ScenarioError(f"Scenario schema must be {SCHEMA}")
        if not isinstance(scenario["id"], str) or not SLUG.fullmatch(scenario["id"]):
            raise ScenarioError("Scenario ID must be a lowercase slug, max 64 characters")
        if "description" in scenario and (
            not isinstance(scenario["description"], str) or len(scenario["description"]) > 500
        ):
            raise ScenarioError("Description must be short text")
        if "source_world_sha256" in scenario and scenario["source_world_sha256"] != self.graph_digest:
            raise ScenarioError("Scenario pinned to a different world graph")
        if "branch" in scenario:
            branch = scenario["branch"]
            _exact_fields(branch, {"parent_scenario_id", "parent_run_sha256", "fork_year"},
                          set(), "branch")
            if (not isinstance(branch["parent_scenario_id"], str) or
                    not SLUG.fullmatch(branch["parent_scenario_id"])):
                raise ScenarioError("Invalid parent scenario ID")
            if (not isinstance(branch["parent_run_sha256"], str) or
                    not re.fullmatch(r"[0-9a-f]{64}", branch["parent_run_sha256"])):
                raise ScenarioError("Invalid parent run digest")
            _strict_integer(branch["fork_year"], YEAR_START, YEAR_END - 1, "fork_year")
        if not isinstance(scenario["events"], list) or len(scenario["events"]) > 100:
            raise ScenarioError("Events must be a list of up to 100 actions")
        seen = set()
        events = []
        for event in scenario["events"]:
            _exact_fields(event, {"id", "year", "type", "intensity"}, {"subject", "note"}, "event")
            if not isinstance(event["id"], str) or not EVENT_ID.fullmatch(event["id"]):
                raise ScenarioError("Event ID must be a lowercase stable identifier")
            if event["id"] in seen:
                raise ScenarioError(f"Duplicate event ID: {event['id']}")
            seen.add(event["id"])
            _strict_integer(event["year"], YEAR_START, YEAR_END, "event year")
            _strict_integer(event["intensity"], 1, 3, "event intensity")
            if not isinstance(event["type"], str) or event["type"] not in self.model["actions"]:
                raise ScenarioError(f"Unknown event type: {event['type']!r}")
            if "subject" in event:
                subject = event["subject"]
                if not isinstance(subject, str):
                    raise ScenarioError("Subject must reference an existing P2 entity")
                try:
                    self.world.entity(subject)
                except KeyError as exc:
                    raise ScenarioError(f"Unknown scenario subject: {subject}") from exc
            if "note" in event and (not isinstance(event["note"], str) or len(event["note"]) > 300):
                raise ScenarioError("Event note must be short text")
            events.append(copy.deepcopy(event))
        # Sorting makes replay independent of JSON input ordering and preserves
        # a deterministic order for non-commutative clamping.
        normalized = {k: copy.deepcopy(v) for k, v in scenario.items() if k != "events"}
        normalized["events"] = sorted(events, key=lambda e: (e["year"], e["id"]))
        return normalized

    @staticmethod
    def _feedback(state: dict) -> dict:
        """Simultaneous year-on-year feedback, viewed from one prior snapshot."""
        v = state
        delta = dict.fromkeys(VARIABLES, 0)
        if v["V7"] >= 65:
            delta["V1"] += 1
        elif v["V7"] < 35:
            delta["V1"] -= 1
        if v["V1"] >= 60:
            delta["V2"] += 2
        elif v["V1"] < 40:
            delta["V2"] -= 2
        if v["V6"] < 30:
            delta["V2"] -= 1
        if v["V1"] >= 65:
            delta["V3"] += 1
        if v["V4"] > 60:
            delta["V3"] -= 1
        if v["V3"] > 65:
            delta["V4"] -= 2
        if v["V5"] > 60:
            delta["V5"] += 1
        if v["V3"] > 60:
            delta["V6"] -= 1
        if v["V2"] < 30:
            delta["V7"] -= 1
        if v["V6"] < 20:
            delta["V7"] -= 1
        return {key: n for key, n in delta.items() if n}

    @staticmethod
    def _apply(state: dict, deltas: dict) -> tuple[dict, dict]:
        updated = {key: _bounded(value + deltas.get(key, 0)) for key, value in state.items()}
        realized = {key: updated[key] - state[key] for key in VARIABLES if updated[key] != state[key]}
        return updated, realized

    @staticmethod
    def _indicators(v: dict) -> dict:
        service_gap = 100 - v["V1"]
        local_trust_proxy = 100 - v["V2"]
        return {
            "service_gap_proxy": service_gap,
            "elite_defection_proxy": v["V3"],
            "security_futility_proxy": v["V5"],
            "local_trust_proxy": local_trust_proxy,
            "viable_alternatives_proxy": v["V4"],
            "accession_pressure_raw": service_gap + v["V3"] + v["V5"] - local_trust_proxy - v["V4"],
            "dependency_gap": v["V1"] - v["V6"],
        }

    def run(self, scenario: dict) -> dict:
        spec = self.validate_scenario(scenario)
        current = dict(self.initial)
        events = spec["events"]
        history = []
        receipts = []
        model = self.model
        previous_digest = digest({
            "genesis": "american-empire.p3.v1",
            "source": self.graph_digest,
            "model": self.model_digest,
            "scenario_id": spec["id"]
        })
        for year in range(YEAR_START, YEAR_END + 1):
            feedback = self._feedback(current) if year > YEAR_START else {}
            current, realized_feedback = self._apply(current, feedback)
            year_events = [e for e in events if e["year"] == year]
            for event in year_events:
                declared = {
                    k: value * event["intensity"]
                    for k, value in model["actions"][event["type"]]["deltas"].items()
                }
                before = dict(current)
                current, applied = self._apply(current, declared)
                receipts.append({
                    "event_id": event["id"], "year": year,
                    "type": event["type"], "intensity": event["intensity"],
                    "subject": event.get("subject"),
                    "declared_delta": declared, "applied_delta": applied,
                    "before": before, "after": dict(current),
                    "authority_layer": "scenario_only",
                })
            anchor = self.world.timeline(year=year)[0]
            snap = {
                "year": year,
                "canon_anchor": {
                    "event_id": anchor["id"], "title": anchor["name"],
                    "source": anchor["source"],
                    "is_historical_reference_only": True
                },
                "state": dict(current),
                "indicators": self._indicators(current),
                "feedback_applied": realized_feedback,
                "scenario_event_ids": [e["id"] for e in year_events],
                "previous_sha256": previous_digest,
                "authority_layer": "scenario_only",
            }
            snap["sha256"] = digest(snap)
            previous_digest = snap["sha256"]
            history.append(snap)
        output = {
            "schema": RUN_SCHEMA,
            "authority_layer": "scenario_only",
            "source_world_sha256": self.graph_digest,
            "model_sha256": self.model_digest,
            "model_id": model["id"],
            "scenario": spec,
            "initial_seed": dict(self.initial),
            "snapshots": history,
            "event_receipts": receipts,
            "final_state": dict(current),
            "final_indicators": self._indicators(current),
            "final_snapshot_sha256": previous_digest,
            "limitations": [
                "Not established history: variables seeded from original Reality Matrix but evolved only under illustrative P3 rules",
                "Historical titles are fixed reference anchors; model outcomes are fictional counterfactual projections",
                "Subject tags do not currently produce geographic or individual effects",
                "No P1 or P2 canon source was changed",
            ],
        }
        output["run_sha256"] = digest(output)
        return output

    def replay(self, record: dict) -> dict:
        """Validate an exported receipt byte-semantically by deterministic replay."""
        if not isinstance(record, dict) or record.get("schema") != RUN_SCHEMA:
            raise ScenarioError("Invalid scenario-run receipt")
        if record.get("source_world_sha256") != self.graph_digest or record.get("model_sha256") != self.model_digest:
            raise ScenarioError("Source graph/model differs from receipt")
        regenerated = self.run(record.get("scenario"))
        if regenerated != record:
            raise ScenarioError("Run receipt does not match exact deterministic replay")
        return {"verified": True, "run_sha256": record["run_sha256"],
                "final_snapshot_sha256": record["final_snapshot_sha256"],
                "snapshots": len(record["snapshots"]), "events": len(record["event_receipts"])}

    def fork(self, parent: dict, *, name: str, fork_year: int, additional_events: list[dict]) -> dict:
        """Branch after a preserved historical *simulation state*, not alternate canon."""
        original = self.validate_scenario(parent)
        _strict_integer(fork_year, YEAR_START, YEAR_END - 1, "fork_year")
        if not isinstance(name, str) or not SLUG.fullmatch(name) or name == original["id"]:
            raise ScenarioError("Fork requires a distinct lowercase scenario ID")
        if not isinstance(additional_events, list) or not additional_events:
            raise ScenarioError("Fork must include at least one new future event")
        for event in additional_events:
            if not isinstance(event, dict) or type(event.get("year")) is not int or event["year"] <= fork_year:
                raise ScenarioError("Fork additions must occur after the fork year")
        parent_run = self.run(original)
        result = {
            "schema": SCHEMA, "id": name,
            "description": f"Counterfactual branch of {original['id']} after {fork_year}; no canon promotion",
            "source_world_sha256": self.graph_digest,
            "branch": {
                "parent_scenario_id": original["id"],
                "parent_run_sha256": parent_run["run_sha256"],
                "fork_year": fork_year,
            },
            "events": [copy.deepcopy(e) for e in original["events"] if e["year"] <= fork_year]
                      + copy.deepcopy(additional_events),
        }
        child = self.validate_scenario(result)
        # A fork never mutates earlier state: confirm with real replay.
        result_run = self.run(child)
        for a, b in zip(parent_run["snapshots"], result_run["snapshots"]):
            if a["year"] <= fork_year and a["state"] != b["state"]:
                raise ScenarioError(f"Fork changed pre-fork state in {a['year']}")
        return child

    def compare(self, left: dict, right: dict) -> dict:
        first, second = self.run(left), self.run(right)
        divergence = next((a["year"] for a, b in zip(first["snapshots"], second["snapshots"])
                           if a["state"] != b["state"]), None)
        return {
            "schema": "american-empire.scenario-comparison.v1",
            "authority_layer": "scenario_only",
            "source_world_sha256": self.graph_digest,
            "model_sha256": self.model_digest,
            "left": {"id": first["scenario"]["id"], "run_sha256": first["run_sha256"]},
            "right": {"id": second["scenario"]["id"], "run_sha256": second["run_sha256"]},
            "first_divergent_year": divergence,
            "final_variable_deltas_right_minus_left": {
                k: second["final_state"][k] - first["final_state"][k] for k in VARIABLES
            },
            "final_indicator_deltas_right_minus_left": {
                k: second["final_indicators"][k] - first["final_indicators"][k]
                for k in first["final_indicators"]
            },
            "not_a_canon_revision": True,
        }
