# P10 — Mathematical landscape layer (source-bound technical experiment)

Branch: `SouthPaw302/GodRender@world/american-empire`. This does not overwrite
the existing AE browser simulation, original P9 scene, original film assets, or
P1 canon. It is a second **opt-in** geometry presentation using the exact P9
scenario scene contract. No World Gacha code or media are imported.

## Data chain

1. Existing P9 workflow extracts an actual browser P7 scenario receipt.
2. Existing `export_godot_scene.py` validates that source and produces
   `scene_contract.json` (hash-linked to the annual P7 snapshot).
3. New `build_procedural_geometry.py` validates that scene contract, derives
   independent stage seeds from the source snapshot hash and selected place ID,
   and emits `procedural_geometry.json`, with its own integrity checksum.
4. Godot 4 `procedural_scene.tscn` reuses the verified P9 source loader,
   creates a triangulated terrain surface, sea plane, D8 river fragments,
   slope-aware roads, buildings and optional anonymous actor marker.
5. The new Actions workflow uses P9's real browser, Godot and movie proof
   checks, then verifies the geometry contract again before retaining derived
   technical artifacts. It does not publish canonical video.

## Generator algorithms

Layered value noise + stylized coastal/ridge/valley geography; mass-transfer
thermal/talus relaxation; priority-flood drainage and accumulation; proximity,
slope and separation weighted settlement sites; minimum-spanning-town connection
with A* slope-and-river penalties. 64×64 cells over an **illustrative 2.4 km
region**. Land is **not** real surveyed terrain around the referenced city:
geocoded P6 positions are narrative anchors, not a heightmap source.

Run the actual flow in `.github/workflows/american-empire-procedural-world.yml`.
Synthetic unit checks (no bootstrap, no models, no media):

```sh
python3 -m unittest discover -s worlds/american-empire/tests -p 'test_procedural_geometry.py' -v
```

Given a validated P9 contract:

```sh
python3 worlds/american-empire/tools/build_procedural_geometry.py \
  --contract worlds/american-empire/godot/data/scene_contract.json \
  --output worlds/american-empire/godot/data/procedural_geometry.json
```

Keep geometry outputs derived/ignored. Same snapshot + same place + same
variations yields the same terrain. Independent town or road reroll does not
rewrite the upstream terrain. Source and geometry tampering reject before render.

## Boundaries

- No canonical history, geographic facts, approved film geography, people,
  faces, architecture or source media are derived by this generator.
- Browser simulation numbers and original P9 are unchanged.
- Generated buildings are schematic, not a reconstruction of any city.
- Godot verification requires an **actual CI run**, not only successful tests.
- The original GodRender media processing and final Director acceptance gates
  remain separate. Do not merge to protected `main` without approval.
