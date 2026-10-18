# GodRender — video-system consolidation with pinned MainV2 sources

**Status: INTEGRATION CANDIDATE.** GodRender now includes provenance-preserving video-system sources and a Studio boot adapter. Runtime/film acceptance remains gated by live GitHub Actions and full render testing.

Source: `SouthPaw302/AIVideoEdit-MainV2-Lab`, branch `test/godot-render`, commit `289ef9ec997ddc426aba43bf66dcd401ee5c3648`.

This branch preserves source code, Godot scenes, project files, source locks, technical reviews, and four inactive CI workflow snapshots. The import intentionally does **not** rewrite upstream implementations to claim portability or turn historical technical PASS records into artistic approval.

## Imported families

- `upstream/mainv2-lab/lab/godot/` — 2D/3D Godot renderer smoke
- `upstream/mainv2-lab/lab/godot-source/` — authorized source-video atmosphere compositing
- `upstream/mainv2-lab/lab/godot-film/` — still + WAV to film with optional MainV2 FX
- `upstream/mainv2-lab/lab/godot-procedural/` — procedural true 3D scene + WAV + FX
- `upstream/mainv2-lab/lab/reviews/` — historical technical review records
- `upstream/mainv2-lab/workflow-snapshots/` — nonexecuting source workflow YAML copies

The four workflows are not active under `.github/workflows/`. No assets, reference binaries, or trained models were fabricated or silently replaced.

## Architectural authority

GodRender owns native Godot scene generation, cameras, simulation, frames and signed evidence. AIVideoEdit-MainV2-Lab owns lyric/music direction, canonical FX IDs, effect gates, shot/asset authorization, film assembly and release QC. GodRender must **not** copy MainV2's canonical FX runtime as a second independent authority; use a versioned, explicitly approved adapter.

Google Drive external brain (index, not execution authority):
- https://drive.google.com/drive/folders/17ZK0fSakXcDSGGj7EeVtF3IriMoAf1HY
- https://docs.google.com/spreadsheets/d/1Xi2wSER-vEIjy52FTKA5RvMXNnGrTxoYiEoPhyXw77c/edit
- https://docs.google.com/document/d/1HKMEg_VuOKjqTDexrDXPioZFD4GxRW_tenYXbi5RjA8/edit

Read `docs/STAGED_TRANSFER_CONTRACT.md` and `docs/SOURCE_PROVENANCE.md` before touching imported files.


## Video consolidation (October 18, 2026)

- Canonical MainV2 source snapshot: `upstream/mainv2-lab/current-main/` (pinned `900e3e5749ed6fa13ad91524975a9e64661e6649`).
- Godot's existing scene implementations remain under `upstream/mainv2-lab/lab/`.
- Browser workstation Studio port: `studio/` with `python studio/stack.py` (host with Python/Git/FFmpeg).
- Source-only recoverable song techniques: `upstream/recovered-song-tech/`; **not approved to auto-run or reuse historical footage**.
- Source provenance/hashes: `config/verified_import_manifest.json`; machine check `python tools/verify_consolidation.py`.
- 100-branch discovery manifest: `config/brain_source_index.json` with exact Git SHAs.
- [External production brain](https://docs.google.com/spreadsheets/d/1Xi2wSER-vEIjy52FTKA5RvMXNnGrTxoYiEoPhyXw77c/edit): FX Pixel Application Atlas, Callable Capabilities, FX Recipes, Recoverable Render Lineage and Agent Boot Handshake.
- Start by running `python godrender_boot.py`. Only a literal `AIVideoEdit OS BOOTSTRAP: PASS` and attested session permits subsequent production work.

Details, status limits and next validation gates: [Video integration](docs/VIDEO_CONSOLIDATION.md) · [GitHub ↔ Drive brain](docs/BRAIN_INTEGRATION.md). Archived YAML is nonexecuting; CI in `.github/workflows/` is GodRender-specific.
