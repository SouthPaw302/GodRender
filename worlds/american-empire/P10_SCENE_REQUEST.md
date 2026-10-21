# P10 — Select a world state, render it, return verified Godot output to Observer

This is a **manual-authorized batch renderer**, not a continuous cloud GPU or live Godot server.

## Web observer
- Open **World Scene Forge** (also linked from the Start Here page).
- Choose a modeled actor, simulation year and observer city.
- **Prepare verified world state** uses the currently selected P5 timeline, P6 local events and P7 directives. It prints a compact `american-empire.scene-request.v1` request containing source digests and source model specifications, *not film media*.
- Copy the JSON and open GitHub Actions **AE Browser to Godot Native 3D Proof**; choose `world/american-empire`, click **Run workflow**, paste into `scene_request`. Nothing runs by clicking the browser buttons alone; GitHub credentials are never sent to the client.

## Native GodRender pipeline
1. CI fetches the existing AE source branch and creates an isolated **local** `song/american-empire` checkout at the identical source SHA. The protected `main` OS bootstrap, production guards and source-canon tests must pass.
2. The runner starts Chromium; `web/tests/replay_scene_request.mjs` validates the requested actor, year, observer region, regional events and P7 directives; replays the P3, P6 and P7 engines and compares **every asserted source SHA-256**.
3. The Python validator `tools/export_godot_scene.py` validates the entire P7 12-year snapshot/hash chain, links the city to the approved hypothetical geodata, then generates a Godot contract. If the requested viewpoint is not where the modeled actor lives, the marker is hidden, **not teleported**.
4. Godot 4 generates an abstract streets/blocks/lighting/camera 3D proof. FFmpeg encodes it. Independent `tools/verify_scene_proof.py` checks the original source hashes, film-safety boundary, multiple distinct frames, and encoded movie integrity. A deliberately tampered receipt MUST be rejected.
5. Only after all proof gates PASS does `tools/publish_scene_proof.py` copy the **derived Godot result only**, with SHA verification, into `web/proofs` on the existing AE branch. GitHub Actions does **not** force-push and does **not** update `main`; an unexpected concurrent branch change fails closed.
6. The web build verifies each stored video SHA, then includes the derived video + registry in the deployable application. Vercel may need a new branch-preview deployment after a runner result; it is not a persistent server or automatic authenticated job queue.
7. **World Scene Forge** shows and plays only the published Godot technical proofs. They are never labeled as approved movie footage. Drive IDs, source clips, storyboards, character references and FX source assets are never exposed by the scene-proof registry.

## Current supported limits
- The selected **P5 scenario** must replay deterministically using the already-shipped P3 engine; this includes source-backed original examples and browser forks.
- P6 regional events (up to 40) and P7 directives (up to 20) are included when chosen in the Observer.
- A scene request is bounded to 21,000 characters; GitHub workflow input accepts the compact JSON, not a full private character-history dump.
- Actor and observer place must exist in the built, source-verified 12-agent / 13-location manifest.
- Only short schematic Godot proof output is generated. No automated cinematic recreation of Paris, no accepted film identity reconstruction, no real-world urban geometry claim, no source-media uploads.
- No UI-to-GitHub credential bridge exists; **human action in GitHub Actions is required**. The public Vercel UI should never contain GitHub tokens.

Relevant workflow: `.github/workflows/american-empire-world-godot.yml`.
