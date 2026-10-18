# Archived transfer contract (provenance, not a current project boundary)

This was the initial cross-repository consolidation plan. **GodRender is now the only active project**. Older names and links below are historical evidence. For current operations use [AGENTS.md](../AGENTS.md) and [compatibility status](COMPATIBILITY_DEBT.md).

## Scope

This is an **auditable cross-repository transfer stage**, not a merge of Git histories and not a release. Original code and historic run evidence are preserved under `upstream/mainv2-lab/`. MainV2-Lab `main`, all song branches, and all original Drive media remain untouched.

## Required gates before operational promotion

1. **Content lineage:** compare each imported file against the pinned upstream commit by Git blob/normalized byte hash; record any deliberate rewrite as an adapter delta.
2. **Dependency isolation:** inspect and remove hard-coded assumptions that scripts execute from the MainV2-Lab root. Do not import privileged MainV2 code into GodRender.
3. **Media authority:** retain original source locks as historical reference; a new run must declare authorized media, SHA-256, usage rights, exact WAV offset, and replacement prohibition.
4. **Godot runtime:** pin Godot version, headless renderer, Xvfb/Mesa/ffmpeg/Python environment and deterministic seeds. Pass the source 2D/3D smoke tests first.
5. **Standalone CLI/manifest:** implement **only after review** a versioned shot request contract (target fps/duration/dimensions, camera, scene, input hashes, output artifact names and seed). Nothing is callable from MainV2 just because source was copied here.
6. **FX integration:** MainV2 chooses and gates canonical FX IDs. GodRender exports RGB/alpha/depth/normal/metadata as appropriate; approved MainV2 FX remains a downstream pass or versioned adapter. No silent FX promotion.
7. **Technical QC:** verify exact frame count/timestamp continuity, audio alignment, no black/frozen frames, source fidelity, true-3D claims, deterministic repeat hashes and constrained motion.
8. **Visual QC:** require manual approval of representative proofs. GitHub Actions green status is not cinematic acceptance.
9. **Integration:** run MainV2-Lab against a pinned GodRender build and verify accepted shot manifest, provenance, hashes and returned assets before any production use.
10. **Promotion:** activate new GodRender CI only after dependencies are reworked, smoke tests pass, and this PR is reviewed. Do not auto-merge, publish, or modify Lab `main`.

## Known blockers

- Original source fixtures/media and approved song-specific imagery are not stored in this import.
- Imported `apply_fx.py` utilities may expect the MainV2-Lab FX runtime and repo layout. They have not been ported.
- Existing YAML sources are archival examples, **not runnable workflows for this repo**.
- Source-lock records document earlier runs, not authorization of new media.
- Historical Godot tests were technical successes, with artistic acceptance unverified.

## Historical technical evidence

- Original-image film: https://github.com/SouthPaw302/AIVideoEdit-MainV2-Lab/actions/runs/38694900035
- Procedural 3D film: https://github.com/SouthPaw302/AIVideoEdit-MainV2-Lab/actions/runs/38698906992
- Real-source overlay: https://github.com/SouthPaw302/AIVideoEdit-MainV2-Lab/actions/runs/38692112937

The source branch's code is a **snapshot**, while the Drive external brain is a **lookup and evidence catalog**. Neither grants permission to bypass MainV2 production rules.
