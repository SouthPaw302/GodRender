# Historical Source Provenance

This document preserves original Git SHA and source URLs for reproducibility; it does **not** identify another active project. All new work is in **GodRender**. See [compatibility migration status](COMPATIBILITY_DEBT.md).

Source repository: `SouthPaw302/AIVideoEdit-MainV2-Lab`
Source branch: `test/godot-render`
Pinned commit: `289ef9ec997ddc426aba43bf66dcd401ee5c3648`
Import date: 2026-10-17
Target: `SouthPaw302/GodRender`, branch `stage/mainv2-godot-hybrid-import-20261017`

The `upstream/mainv2-lab/lab/` directory mirrors source `.lab/` with the single path relocation. `workflow-snapshots/` mirrors source `.github/workflows/godot-*.yml` without activating any workflows. Historical proofs retain their original status and SHA claims; output binaries were not copied.

Provenance anchors:
- `.lab/godot/` — original 2D/3D smoke suite
- `.lab/godot-source/` — source media overlay experiment
- `.lab/godot-film/` — still + WAV film
- `.lab/godot-procedural/` — procedural 3D film
- `.lab/reviews/godot-*.json` — experiment reviews

Source Git tree URLs:
- https://github.com/SouthPaw302/AIVideoEdit-MainV2-Lab/tree/289ef9ec997ddc426aba43bf66dcd401ee5c3648/.lab
- https://github.com/SouthPaw302/AIVideoEdit-MainV2-Lab/tree/289ef9ec997ddc426aba43bf66dcd401ee5c3648/.github/workflows

A separate implementation and runtime smoke verification is required; this PR stages provenance-preserving imports only.
