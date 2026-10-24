# American Empire sandbox agent — local operation, no Vercel

Run directly from a checked-out **SouthPaw302/GodRender** on
`world/american-empire` (the original main OS and accepted sources are protected).

## Agent commands

All paths below are relative to GodRender's repository root.

```bash
# Python 3.10+, no external hosting service
python3 worlds/american-empire/tools/sandbox_agent.py check

# Starts the complete local World Explorer at http://127.0.0.1:8765
python3 worlds/american-empire/tools/sandbox_agent.py serve

# Optional: source-verifiable browser -> P7 snapshot -> P9 contract ->
# deterministic P10 terrain/towns/roads (requires Node and Playwright in
# worlds/american-empire/web/tests/node_modules)
python3 worlds/american-empire/tools/sandbox_agent.py scene

# Or use a real previously exported P7 receipt without Playwright:
python3 worlds/american-empire/tools/sandbox_agent.py scene \
  --receipt /path/to/ae-p7-receipt.json --actor claire --year 2027 --place paris

# With Godot 4, FFmpeg (and Xvfb on Linux without a desktop), add:
python3 worlds/american-empire/tools/sandbox_agent.py scene --render
```

The existing site offers World Matrix, simulation, Earth Network, inhabitants,
Second Brain and World Scene Forge. It is assembled from the same source
bundles as the prior GitHub Actions proof; not a mock frontend.

The agent's `scene` command boots an ephemeral **loopback-only** HTTP server,
lets existing `replay_scene_request.mjs` run the actual P3/P6/P7 browser
engines, checks the full replay against signed stage and yearly snapshot
hashes, and passes the P7 receipt into the existing canonical
`export_godot_scene.py` and P10 `build_procedural_geometry.py`.
`--request` accepts the exact World Scene Forge exported request JSON.
`--render` uses an isolated copy of the native Godot project plus FFmpeg
and the pre-existing independent P9 scene-proof validator.

If only Python is installed, `check` and `serve` still work; `scene`
may run from an existing receipt. The browser stays local to the sandbox:
a remote user's browser cannot automatically visit that loopback address,
and a sandbox instance is not a permanent server. No remote execution,
Studio Tool API, Vercel, API credentials, or Drive media are exposed.

Derived outputs appear in `worlds/american-empire/sandbox-output/`
(by default, ignored by Git). The existing Godot project, accepted
media, main, and locked fiction are unchanged. Technical checks do not
confer film or canon approval.

For **protected GodRender production** (not a noncanonical technical proof),
use the repo's mandatory native boot and production guard. The existing P9
GitHub Actions workflow uses an ephemeral local `song/american-empire`
checkout for that gate; this launcher is not a substitute for boot authority.

CI: `.github/workflows/american-empire-sandbox-agent.yml`.
