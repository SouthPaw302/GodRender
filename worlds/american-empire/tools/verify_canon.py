#!/usr/bin/env python3
"""P1 guard: verify an exact, byte-preserved American Empire written-canon mirror.

Uses Git blob SHA-1 as historical source identity (not a new security signature).
The independent pinned constants prevent silent lock-file-only revision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SOURCE_COMMIT = "d768ee1684ebddd06af249f3a366181c929bc80c"
SOURCE_REPOSITORY = "SouthPaw302/AIVideoEdit"
MIRROR_REPOSITORY = "SouthPaw302/GodRender"
MIRROR_BRANCH = "world/american-empire"
PINNED = {
    "00_READ_FIRST/README.md": "840942fad12d7f8bc7b28d0d086456fe75d2bb56",
    "01_CANON_SOURCE/UNIVERSE_BIBLE.md": "7dd9055467315f51a1af434ea9c4d3023055b45c",
    "01_CANON_SOURCE/REALITY_MATRIX.json": "575e8c1b20bc6e9bf5c61ac32e32536256abcab0",
    "02_CHRONICLES/CHRONICLE_02_THE_FIRST_WINTER.md": "2e0479e29062f6ff85ce3fb128c1044a0f4595d3",
    "02_CHRONICLES/CHRONICLE_03_THE_MEASURE.md": "02514a52931cfeaf48876799ee49abfb000a2e06",
    "02_CHRONICLES/CHRONICLE_04_CORRIDOR_TREATIES.md": "873f316e6042b08b46e114180d1ef72fe3ed2d90",
    "03_PRODUCTION_LINK/PRODUCTION_MAP.md": "5f9e9ab74732981c9a9795a7424d2efcd3123129",
    "04_RECOVERY/FUTURE_AGENT_HANDOFF.md": "0684954d95016f21448dda82fa72bc5430e59a09",
    "04_RECOVERY/RECOVERY_MANIFEST.json": "325a369531c63ea01f2bd8a82ea9884e23c35d70",
}
READ_ORDER = [
    "01_CANON_SOURCE/UNIVERSE_BIBLE.md",
    "01_CANON_SOURCE/REALITY_MATRIX.json",
    "02_CHRONICLES/CHRONICLE_02_THE_FIRST_WINTER.md",
    "02_CHRONICLES/CHRONICLE_03_THE_MEASURE.md",
    "02_CHRONICLES/CHRONICLE_04_CORRIDOR_TREATIES.md",
]


def git_blob_sha1(content: bytes) -> str:
    header = b"blob " + str(len(content)).encode("ascii") + b"\0"
    return hashlib.sha1(header + content).hexdigest()


def verify(world_root: Path) -> list[str]:
    """Return errors without changing or fetching any files."""
    errors = []
    archive = world_root / "archive"
    lock_path = world_root / "CANON_LOCK.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"Cannot read canon lock: {exc}"]

    expected = list(PINNED)
    if lock.get("schema") != "american-empire.canon-lock.v1":
        errors.append("Unexpected canon lock schema")
    if lock.get("status") != "P1_SOURCE_LOCKED":
        errors.append("Canon lock status changed")
    source = lock.get("source", {})
    mirror = lock.get("mirror", {})
    policy = lock.get("policy", {})
    if source.get("repository") != SOURCE_REPOSITORY or source.get("commit") != SOURCE_COMMIT:
        errors.append("Source repository or pinned commit changed")
    if source.get("root") != "projects/american-empire-canon-archive/":
        errors.append("Source archive root changed")
    if mirror.get("repository") != MIRROR_REPOSITORY or mirror.get("branch") != MIRROR_BRANCH:
        errors.append("Mirror repository or branch changed")
    if mirror.get("root") != "worlds/american-empire/archive/":
        errors.append("Mirror archive root changed")
    if lock.get("read_order") != READ_ORDER:
        errors.append("Authoritative reading order changed")
    if lock.get("historical_spine") != {
        "first_year": 2026,
        "last_year": 2037,
        "authority": "recovered source reality matrix",
    }:
        errors.append("Fictional timeline spine changed")
    if policy.get("original_bytes") != "preserve_verbatim":
        errors.append("Original byte preservation policy changed")
    if policy.get("proposals_auto_promoted") is not False:
        errors.append("Proposal promotion policy changed")
    if policy.get("adaptation_authority") != "non_canon":
        errors.append("Adaptation boundary changed")
    if policy.get("simulations_modify_originals") is not False:
        errors.append("Simulation isolation policy changed")

    records = lock.get("files", [])
    if not isinstance(records, list) or [x.get("path") for x in records if isinstance(x, dict)] != expected:
        errors.append("Locked file list/order differs from source")
    else:
        for record in records:
            if record.get("git_blob_sha1") != PINNED[record["path"]]:
                errors.append(f"Lock hash changed: {record['path']}")
        for record in records:
            path = record["path"]
            classification = record.get("classification")
            if path.startswith("01_CANON_SOURCE/") and classification != "source_canon":
                errors.append(f"Misclassified core canon: {path}")
            if path.startswith("02_CHRONICLES/") and classification != "source_chronicle_with_proposed_additions":
                errors.append(f"Misclassified chronicle/proposals: {path}")
            if path.startswith("03_PRODUCTION_LINK/") and classification != "historical_adaptation_reference_only":
                errors.append(f"Misclassified film provenance: {path}")

    if not archive.is_dir():
        return errors + ["Archive directory is missing"]

    encountered = set()
    for path in archive.rglob("*"):
        relative = path.relative_to(archive).as_posix()
        if path.is_symlink():
            errors.append(f"Symlink is forbidden: {relative}")
        elif path.is_file():
            encountered.add(relative)
    missing = sorted(set(PINNED) - encountered)
    extras = sorted(encountered - set(PINNED))
    if missing:
        errors.append("Missing archived files: " + ", ".join(missing))
    if extras:
        errors.append("Unpinned archived files: " + ", ".join(extras))

    for relative, expected_sha in PINNED.items():
        candidate = archive / relative
        if not candidate.is_file() or candidate.is_symlink():
            continue
        actual = git_blob_sha1(candidate.read_bytes())
        if actual != expected_sha:
            errors.append(f"BYTES DIFFER: {relative} expected {expected_sha}, found {actual}")

    if (archive / "01_CANON_SOURCE/REALITY_MATRIX.json").is_file():
        try:
            data = json.loads((archive / "01_CANON_SOURCE/REALITY_MATRIX.json").read_bytes())
            years = [int(p["year"]) for p in data["ten_year_phases"]]
            if years != list(range(2026, 2038)):
                errors.append(f"Matrix historical years differ: {years}")
            if data.get("reality_cutoff") != "2026-08-31":
                errors.append("Matrix reality cutoff changed")
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(f"Matrix parse/validation failed: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = verify(args.world_root.resolve())
    if errors:
        print("AMERICAN EMPIRE P1 CANON FAIL")
        for error in errors:
            print(" -", error)
        return 1
    print(f"AMERICAN EMPIRE P1 CANON PASS: {len(PINNED)} byte-identical archived files")
    print(f"Source: {SOURCE_REPOSITORY}@{SOURCE_COMMIT}")
    print("No adaptation or proposed chronicle addition promoted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
