# GodRender

**GodRender is the one active home for our film-production and Godot-rendering work.** New features, fixes, agents, FX integration, runtime tests and release decisions belong in this repository. Earlier productions remain a recoverable creative and technical history—not separate active systems.

## Studio and production system

- **Studio:** browser production workflow, asset preparation, direction, storyboard, shots, FX, assembly and final review.
- **Rendering:** Godot 2D/3D scenes, camera and depth experiments, still-image motion, video/FFmpeg tooling.
- **FX library:** consolidated source, canonical registry and historical recoverable techniques, with provenance and proof gates.
- **Evidence:** per-shot source hashes, moving proofs, technical QC, human Director acceptance and reproducible GitHub Actions.
- **External Brain:** [GodRender production knowledge on Google Drive](https://docs.google.com/spreadsheets/d/1Xi2wSER-vEIjy52FTKA5RvMXNnGrTxoYiEoPhyXw77c/edit). Historical production names and techniques are retained there.

## Run

From a GodRender checkout with Python, Git and FFmpeg:

```bash
python godrender_boot.py
python studio/stack.py
```

Open **http://127.0.0.1:8080**. To use the browser without loading production authority first, start the Studio alone; guarded production operations require a successful bootstrap. For Windows or Termux, use `studio/start_windows.bat` or `studio/start_termux.sh`.

To verify the consolidated sources and the Studio contracts:

```bash
python tools/verify_consolidation.py
PYTHONPATH=studio python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=studio python studio/selftest.py
```

## One repository, preserved productions

- **New work:** commit in `SouthPaw302/GodRender`, on reviewed branches; do not start or update a different active video repo.
- **Historical source:** retained, unchanged under `upstream/`, and tracked by `config/verified_import_manifest.json` and `config/brain_source_index.json`.
- **Recovered production technology:** `upstream/recovered-song-tech/` is a forensic library. Reuse its neutral method only after media authorization, current gates and representative proof.
- **Current production authority:** `AGENTS.md` and the live guarded runtime. Do not promote rejected scenes or infer success from an archived render.

## Important runtime compatibility boundary

The visible product, project direction, agent workspace and change destination are **GodRender**. After PR #6, the checked-in core and Studio bootstrap use **GodRender's own checkout**. Legacy storage paths and schema identifiers remain supported for existing media/projects, but no external historical repository is an active production authority. Do not remove compatibility interfaces without a tested migration. See [compatibility migration status](docs/COMPATIBILITY_DEBT.md).

GodRender's GitHub checks verify the imported source, Studio HTTP and bootstrap. A full Godot → FX → music → final-film Director-accepted render is **not yet proven** by these checks.

[Native guardrails](docs/NATIVE_GUARDRAILS.md) · [GodRender Studio guide](studio/README.md) · [Agent boot contract](AGENTS.md) · [External brain](docs/BRAIN_INTEGRATION.md) · [Import history](docs/VIDEO_CONSOLIDATION.md)
