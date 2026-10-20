#!/usr/bin/env python3
"""GodRender AE population inference gate: accepts source-bound P7 receipt.

A tiny language model may propose a *priority* only. Nothing in this worker
changes canon, simulated history, or Drive. Every proposal requires a separate
review in Observer and a deterministic replay after acceptance.
"""
import argparse
import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path

PRIORITIES = {"relief", "liberty", "truth", "order", "trade"}
MODEL_ID = "HuggingFaceTB/SmolLM2-135M-Instruct"
SCHEMA = "american-empire.p8-population-proposal.v1"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(obj):
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def assert_run(receipt, actor, year):
    if receipt.get("schema") != "american-empire.p7-run.v1":
        raise ValueError("Not a P7 agent world-state receipt")
    if receipt.get("authority_layer") != "scenario_only":
        raise ValueError("Unexpected source authority")
    snapshots = receipt.get("snapshots")
    if not isinstance(snapshots, list) or len(snapshots) != 12:
        raise ValueError("P7 year count wrong")
    value = receipt.get("run_sha256")
    clean = deepcopy(receipt)
    clean.pop("run_sha256", None)
    if not isinstance(value, str) or value != digest(clean):
        raise ValueError("P7 run digest mismatch")
    for i, snap in enumerate(snapshots):
        s = deepcopy(snap)
        h = s.pop("sha256", None)
        if h != digest(s) or snap.get("year") != 2026 + i:
            raise ValueError("Tampered P7 annual snapshot")
        if i and snap.get("previous_sha256") != snapshots[i - 1]["sha256"]:
            raise ValueError("Broken annual chain")
    if not isinstance(year, int) or year < 2026 or year > 2037:
        raise ValueError("Year outside modeled horizon")
    snap = snapshots[year - 2026]
    if actor not in snap.get("people", {}):
        raise ValueError("Agent does not exist in this run")
    a = snap["people"][actor]
    if not isinstance(a.get("knowledge"), list) or not isinstance(a.get("memory"), list):
        raise ValueError("Missing actor knowledge or memory")
    if len(a["memory"]) > 40:
        raise ValueError("Memory bound exceeded")
    return snap, a


def select_smoke(snapshot, agent):
    # Explicitly non-LLM; only for testing the worker/receipt contract.
    local = snapshot["places"][agent["place"]]
    if local["service"] < 45:
        return "relief", "Deterministic test suggestion for low service"
    if local["independence"] < 50:
        return "liberty", "Deterministic test suggestion for weak independence"
    return "truth", "Deterministic smoke-test choice, NOT neural inference"


def select_smollm(snapshot, agent):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch

    # Keep only the selected actor's known observations; never send omniscient
    # matrix contents or other characters' private thoughts.
    known = [str(x)[:250] for x in agent["knowledge"][-8:]]
    memories = [str(m.get("text", ""))[:250] for m in agent["memory"][-8:]]
    local = snapshot["places"][agent["place"]]
    prompt = (
        "You are advising one fictional character in a strictly hypothetical "
        "alternate-history simulation. Choose exactly one priority token from "
        "relief, liberty, truth, order, trade. Reply ONLY with the token. "
        "Do not invent historical facts or change fixed film dialogue.\n"
        f"Location: {agent['place']}\nYear: {snapshot['year']}\n"
        f"Local model service index: {local['service']}\n"
        f"Local independence index: {local['independence']}\n"
        f"Personal known facts: {json.dumps(known,ensure_ascii=False)}\n"
        f"Own remembered observations: {json.dumps(memories,ensure_ascii=False)}"
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, trust_remote_code=False).eval()
    messages = [
        {"role": "system", "content": "Select one policy priority for the fictional character."},
        {"role": "user", "content": prompt},
    ]
    # Constrained candidate scoring: genuine neural forward passes, but the
    # model cannot generate unconstrained instructions or overwrite canon.
    prefix = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=True, return_tensors="pt"
    )
    scores = {}
    with torch.no_grad():
        for label in sorted(PRIORITIES):
            target = tokenizer.encode(label, add_special_tokens=False)
            if not target:
                raise ValueError("Tokenizer could not encode allowed priority")
            seq = torch.cat([prefix, torch.tensor([target], dtype=prefix.dtype)], dim=1)
            logits = model(seq).logits[0]
            # Candidate token probabilities at each continuation position.
            start = prefix.shape[1] - 1
            logprobs = torch.log_softmax(logits[start:start+len(target)], dim=-1)
            scores[label] = float(sum(logprobs[i,tid].item() for i,tid in enumerate(target))) / len(target)
    candidate = max(scores, key=lambda choice:(scores[choice],choice))
    if candidate not in PRIORITIES:
        raise ValueError("Language model produced no valid constrained priority")
    return candidate, "Constrained neural scoring of approved priorities using a real CPU model"


def propose(receipt, actor, year, mode="smoke"):
    snap, agent = assert_run(receipt, actor, year)
    if mode == "smoke":
        priority, note = select_smoke(snap, agent)
        backend = "deterministic_smoke_no_model"
    elif mode == "smollm2-135m":
        priority, note = select_smollm(snap, agent)
        backend = MODEL_ID
    else:
        raise ValueError("Unknown inference backend")
    if priority not in PRIORITIES:
        raise ValueError("Invalid proposal")
    return {
        "schema": SCHEMA, "authority_layer": "scenario_only_proposal_not_applied",
        "actor": actor, "year": year, "priority": priority,
        "backend": backend, "status": "proposal_only_requires_observer_approval",
        "source_p7_run_sha256": receipt["run_sha256"],
        "source_p7_snapshot_sha256": snap["sha256"],
        "source_manifest_sha256": receipt["manifest_sha256"],
        "known_fact_count": len(agent["knowledge"]),
        "private_memory_count": len(agent["memory"]),
        "reason": note,
        "warnings": ["The 2027 Paris film year is a modeling assumption, not an established date.",
                     "No direct execution, canon promotion, or film-dialogue modification occurred."]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--actor", default="claire")
    parser.add_argument("--year", type=int, default=2027)
    parser.add_argument("--mode", choices=["smoke", "smollm2-135m"], default="smoke")
    args = parser.parse_args()
    record = json.loads(args.receipt.read_text(encoding="utf-8"))
    output = propose(record, args.actor, args.year, args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"],"backend": output["backend"],
                      "actor": output["actor"],"year": output["year"],
                      "priority": output["priority"],"source": output["source_p7_run_sha256"][:12]}))


if __name__ == "__main__":
    main()
