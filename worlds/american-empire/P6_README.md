# P6 — American Empire Geographic Living Earth (technical prototype)

**GitHub branch:** \`world/american-empire\` on \`SouthPaw302/GodRender\`. No changes to \`main\` or the P1–P5 source mechanics.

## What exists

P6 adds **Earth Network** to the browser. This is a genuine georeferenced, zoomable interactive map with Natural Earth public-domain 1:110m land geometry and **12 approximate real city-center positions mentioned in the original P1 written universe**, including Anderson, Bandar Abbas, Tehran, Karachi, Gwadar, Basra, Mombasa, Thessaloniki, Guayaquil, Philadelphia, Washington, and Geneva.

Place-name authority: a literal story reference in the original \`UNIVERSE_BIBLE.md\` or \`CHRONICLE_04_CORRIDOR_TREATIES.md\`. Cartographic coordinates refer to modern real-world approximate city centers, not fictional hospital entrances, borders, municipal referendum boundaries, stations, or precise facilities.

- 16 **illustrative directed model links**. These are NOT claims that routes or shipments existed, still exist, or operate in the original canon. Some original chronicle passages merely describe requests or ideas for corridors.
- Two explicitly **invented and local** indices per node: service reliability and independent capacity (0–100, never measured historic conditions).
- One-year lag causal diffusion along directed connections. An intervention at Bandar Abbas can affect Gwadar in a subsequent year, and potentially further downstream. No instantaneous global animation or scripted 2037 ending.
- Real dependence on the active P5/P3 scenario's **seven-variable model receipts**: year-over-year P3 material reliability and right-of-exit changes drive shared macro effects. Local choices never rewrite the P3 model or P1 timeline.
- Four local hypothetical interventions: service disruption, Stack-linked relief, independent supply, and practical exit rights; each supports 1–3 intensity.
- Inspect city name, documented textual mention, approximate coordinates, outgoing network effects, indexed variables, time travel and zoom. Compare current regional run against the same P5 run without the local interventions.
- Browser-local saving of P6 interventions keyed by P5 run hash. JSON export includes the exact P5 run SHA and geographic source SHA. No Drive write, GitHub mutation, or GodRender worker invocation.

## How the engine works

**One-step deterministic network state for each 2026–2037 year**:
1. Get the exact active \`AE_Live.current().run\`, previously hash-verified against P3 Python.
2. Read each node's previous year's local state and all inbound modeled edges; compute bounded integer equalization \`trunc((source_service - destination_service) * edge_weight / 20)\`. Restrict total incoming contribution to ±8. This is explicitly an invented **diffusion heuristic**; not measured transport, capacity, flow, hospital safety, or an economic estimate.
3. Add year-over-year P3 material reliability macro delta (integer truncation of delta/2) to service, right-of-exit macro delta (integer truncation of delta/3) to independence.
4. Apply same-year local decisions at the selected node, clamp indices to 0–100, keep one-year step spacing; downstream nodes cannot react to that local decision until a later year.
5. Record each place and route's supply proxy in an independent scenario-only 12-year history. No local action touches original source data.

The display's routes are schematic dependency curves connecting actual georeferenced centers, **not** route navigation or proof of territorial/political ownership. The real-world background uses Natural Earth public-domain dataset <https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson>. Its stored file retains geometry and is fully available offline. Coordinate labels are approximate; Bandar Abbas 27.1865, 56.2808 from GeoNames <https://www.geonames.org/141681/bandar-abbas.html> and Anderson 34.5034,-82.6501 from publicly accessible gazetteer references; remaining coordinates are approximate city-center references, **not site surveys**.

## Proof gate

- P1 canon SHA pinning, P2 WorldMatrix, P3 exact Python model, P4 Godot and P5 browser checks still run.
- Reproducible browser build emits \`data/geo.json\`, \`data/land.geojson\`, and local \`regions.js\` / \`earth.js\` into both HTTP and standalone \`file://\` distributions.
- Python tests verify node/edge typing, fictional authority classification, source mentions and new assets.
- Chromium test \`web/tests/p6_earth.mjs\` loads public-domain land shapes, checks 12 selectable locations and 16 edges, triggers a port service interruption at Bandar Abbas in 2030, verifies Gwadar does not change instantly in the same year but responds in 2031, checks geographic export, zoom/undo and active P5 scenario sync.

## Future scope

P6 is a **georeferenced regional causal prototype**, NOT yet a full Earth economic engine, nationally resolved sovereignty model, physics-accurate transport system, or a global population simulator. The original narrative's 2030 Bandar Abbas medical corridor is **canonical**, but its numerical service indices, modeled links, and any new local choices in this prototype are **strictly hypothetical**.

The Drive Second Brain continues to be the existing reusable production library. GodRender native Studio/Godot/ONNX/FX/run infrastructure is available by retrieval and evidence-gated handoff if later creating actual visual assets. Geographic modeling does not itself call tools or create production media; future accepted AE proof/assets belong in Drive AE, and reusable verified techniques should return to the Second Brain.

## Operating

1. Open the existing preview deployment's **Earth Network** tab, or build locally with \`python3 worlds/american-empire/tools/build_web.py --repro\`.
2. Select Bandar Abbas, year 2030, apply **Interrupt port / service access**.
3. Advance to 2031; Gwadar's modeled service index should differ relative to the no-local-event counterfactual.
4. Choose a different P5 scenario under **Simulation Lab** and revisit Earth to see its global indices drive the regional model.
5. Export P6 JSON for reproducibility; the map's local changes are not saved to Google Drive or promoted to canon.
