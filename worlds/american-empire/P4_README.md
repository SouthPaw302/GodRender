# American Empire — P4 Godot World Explorer

**Status:** technical interactive explorer; not a film production, web deployment, or geographic planetary simulation.

P4 is the first real Godot view of the locked **Quiet Accession** world. The project is wholly inside `worlds/american-empire/` on `world/american-empire`; the main GodRender runtime, original P1 text, P2 graph and P3 model remain unchanged.

## What is on screen

- A 2026–2037 interactive year slider and next/previous year buttons.
- Canonical timeline title and authored phase description, sourced directly from the locked P1/P2 Matrix.
- Scenario selector: baseline, independent corridor, high integration — *all P3 modeling hypotheses, never historical facts*.
- A schematic **16-node relationship canvas** for the canonical ten actors and six imperial Stack systems, using only P2 recorded relationships and prerequisites.
- Clickable graph nodes and a five-character viewpoint selector. Inspect goals, roles, fears, benefits, relationships, source JSON Pointers and original Git blob hashes.
- Seven live numeric indicators with bars for P3 simulation variables and two explicitly labeled *proxy* indicators, changing as year and scenario change.
- The Paris Act I adaptation remains linked separately in `ADAPTATION_LINKS.md`. Nothing is imported into the canon.

This is **not a map**. The actor/system ring positions are visual layout, not cities or geocoordinates. P3 does not simulate local infrastructure or citizens yet.

## Open locally

Requires Python 3.10+ and the **Godot 4** desktop executable. From GodRender repository root:

```bash
python3 worlds/american-empire/tools/launch_explorer.py --godot-bin /path/to/Godot_4.x
```

Or manually:

```bash
python3 worlds/american-empire/tools/build_explorer_bundle.py --check-reproducible
godot --path worlds/american-empire/godot --rendering-method gl_compatibility
```

The launcher refuses to open a viewer with unverified canon. It generates a temporary ignored `godot/data/world_bundle.json` from exact P1/P2/P3 data before launching. No network, third-party inference, paid model, database or data reconstruction required.

Godot source is at `godot/project.godot`, with `scenes/world_explorer.tscn`, `scripts/explorer.gd`, and `scripts/relationship_graph.gd`.

## Source-to-screen architecture

```text
P1 archive (hash-verified immutable text)
    -> P2 WorldMatrix() (source JSON Pointers + relationship graph)
    -> P3 Simulation() (separate hypothetical annual state & replay receipts)
    -> tools/build_explorer_bundle.py (deterministic read-only JSON bridge)
    -> godot/data/world_bundle.json (generated, ignored)
    -> Godot 4 World Explorer (interactive desktop viewport)
```

The bridge verifies the original source and replays all bundled scenarios. Bundle includes `bundle_sha256`, P2 graph digest, P3 model digest, canonical matrix blob SHA, authenticated source pointers, and simulation-run SHA-256 per scenario. Original archive source files are never replaced or modified.

The viewer checks bundle schema, authority mode, years, entity counts, scenario layer, P2 source hash and cross-model references. Full SHA and scenario replay verification is performed in **Python before Godot starts**; Godot should not be treated as independent cryptographic validator of the JSON.

## CI proof

The branch-only workflow `.github/workflows/american-empire-p4-godot.yml`:

1. Verifies the P1–P4 Python regression suites and exports the deterministic bundle.
2. Downloads official Godot 4.7.2-stable Linux executable with the existing research-pinned SHA-256, runs through actual Xvfb/Mesa OpenGL compatibility renderer (not the headless dummy canvas).
3. Opens the actual P4 scene, cycles the year and scenario UI with a deterministic **testing-only** flag, captures 48 real UI frames and 2-second MP4.
4. Checks nonblank 1440 × 900 image geometry, multiple visibly changing frames, actual Godot state-change logs, and encoded movie characteristics.
5. Saves screenshots, proof movie, viewer bundle and a technical verification report as expiring **GitHub Actions artifacts**.

CLI-only engine tests cannot prove user-interface interaction. The recorded smoke exercises programmatic UI selection and visible redraw; **manual mouse and keyboard usability, visual legibility and production/artistic approval still require human review**.

No GitHub production action, Vercel URL, Google Drive media archive or approved master is generated. This is a standalone technical Godot viewer on the world-development branch.

## P4 completion boundary

P4 success means verifiable interactive desktop Godot exploration of **original source graph** plus **explicit what-if numeric evolution** with source traceability. P4 does **not** indicate validated 3D landscapes, actual global political borders, real-world geopolitics or an operational web app.

The next meaningful expansion would be a location-indexed world with provenance-backed places, infrastructure corridors, physical regional models, characters and optional cinematic scenes. Those must remain additions to or adaptations of canon, not silent edits to recovered text.
