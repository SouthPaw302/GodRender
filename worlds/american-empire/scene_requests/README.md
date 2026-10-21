# American Empire scene-request queue

This directory is a **source-bound request inbox**, not a film-media directory.

GitHub's `workflow_dispatch` manual UI only works when a workflow exists on the default branch; the American Empire renderer is intentionally isolated on `world/american-empire`, so we use a safe **push-triggered request** instead.

In the Observer, open **World Scene Forge**, select the actor/year/observer location and prepare the request. Download its JSON file. In GitHub, navigate to this folder on `world/american-empire`, choose **Add file → Upload files**, select exactly ONE `request-*.json` file, and commit directly to the same `world/american-empire` branch. The existing AE workflow will validate all P3/P6/P7 hashes and render it with protected-main GodRender guards. Rejects malformed, source-mismatched, tampered or unauthorized states. No GitHub token is ever exposed to the browser.

Each new request must have a unique filename matching `request-[a-z0-9-]+.json`, and contain only the compact `american-empire.scene-request.v1` document. It must not include any Drive media or raw character data. If you prefer, copy the JSON into ChatGPT, and an authorized connected GitHub tool can commit that specific file to this branch.

After the job is verified, only derived technical Godot output is added to `web/proofs`. Vercel needs to build the latest AE commit to display it. The original media, accepted movie and canonical history remain unchanged.
