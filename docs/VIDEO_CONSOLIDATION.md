# GodRender video systems consolidation — source + runtime boundary

**2026-10-18 transfer from** `SouthPaw302/AIVideoEdit-MainV2-Lab` `900e3e5749ed6fa13ad91524975a9e64661e6649`.
**Original GodRender main** `cdf69c11c121a61a605dec09da4e96cf5418f24d`. No source repos or song branches were mutated.

## Included
- All 233 selected text-based canonical source/config/studio files from Lab main, with Git blob identity check. Relocated source files are under `upstream/mainv2-lab/current-main/`; inactive workflow snapshots under `upstream/mainv2-lab/workflow-snapshots/current-main/`; Studio sources under `studio/`. Three Studio files are patched only in GodRender (core authority, deferred Jev, GUI link).
- Original Godot experiment source remains intact, including 2D/3D renderers, sourced film, procedural film and nonexecuting workflow snapshots.
- 24 archived song-specific render/proof scripts from Pandora, A Thousand Doors, Silver Coin, Leave It by the Door, IronFlame, La Luna. They are **forensic source**, not automatically promoted FX or authorized reusable imagery.
- Branch discovery: 100 commit-pinned heads in `config/brain_source_index.json`; Drive's separate forensic atlas documents parameters and actual pixel-mask application for 100 indexed canonical/branch techniques.
- Source lineage SHA inventory: `config/verified_import_manifest.json` with exact Git SHA for each file and, when known, upstream source path/commit.

## Architecture
`GodRender`: owns Godot scene build, temporal cameras, frame/export mechanics, experimental renderers and the Studio host integration.
`AIVideoEdit-MainV2-Lab`: **single authoritative** production OS and latest approved FX gate, rules, music interpretation, shot auth, release QC and edit decisions. GodRender boots an isolated real AIVideoEdit checkout; snapshots do not grant production rights.
`Drive brain`: searchable retrieval and history, not execution or merge authority.

## Agent startup and GUI
Run `python godrender_boot.py` from a networked GodRender checkout. This clones AIVideoEdit-MainV2-Lab main into `studio/.runtime/core/repo` and runs its original bootstrap, refusing to claim PASS without a real current-main attestation. Offline requires `AIVE_CORE_LOCAL_REPO` pointing to an actual, locally available AIVideoEdit checkout, plus `--offline`.
Then `python studio/stack.py` serves the browser Studio at `http://127.0.0.1:8080` by default. The GUI has a direct FX Brain link. This is an imported Alpha Studio with a fixed boot path; it does not yet expose a proved GodRender 3D job queue or complete one-click full-film editor.

## Operational gates (not implied by copy)
1. `python tools/verify_consolidation.py` must verify all exact content SHA values.
2. GitHub-first OS boot must return literal PASS and valid current-main SHA.
3. Existing Godot demo sources must pass independent dependency/path/3D smoke tests.
4. A versioned film-shot request adapter must send authorized source hashes, scene/camera/fps/duration, art direction, output format; MainV2 must validate resulting output and FX ledgers.
5. Recoverable song technologies require neutralization (remove hard-coded source paths/character geometry), own short moving evidence, canonical gate approval and human visual review before they can be reused as current production FX.
6. The full film, transitions, audio, Director QC and final release still require separate test and approval; prior production technical PASS ≠ creative acceptance.

**DO NOT** call this a complete runnable integration or import rejected media merely because source files are preserved here. The 100-branch Drive inventory is broader than the 24 physically copied script files; branch-by-branch callable FX harvest remains a separate incomplete layer.
