# American Empire — Native production boot handoff

**Do not create, rename or delete a remote GitHub branch.** Keep `world/american-empire` as the source of truth. Protected `main` remains the authoritative OS.

Native branch policy in current main requires `song/<slug>` (prefix), not `*/song` (suffix). The on-branch workflow `.github/workflows/american-empire-native-boot.yml` already proves the correct, nonpersistent production setup.

1. Checkout existing `world/american-empire` with full `origin/main` ancestry.
2. In the disposable CI checkout only, create local `song/american-empire` at *the exact same AE commit SHA*, without pushing any refs.
3. Adjust `projects/american-empire/PROJECT_STATE.json` **only in that disposable checkout** so its branch value matches `song/american-empire`. Never silently commit this translated state to the canonical world branch.
4. Run `python3 bootstrap.py boot --offline --repo-root "$GITHUB_WORKSPACE" --branch song/american-empire --project-dir projects/american-empire`. Run production and workflow guards.
5. Verify bootstrap prints PASS and its main SHA matches the protected main revision. Preserve proof receipts.

**First verified PASS:** https://github.com/SouthPaw302/GodRender/actions/runs/39557339190 on source `eb18a24ea44b5609d6310fb5b0f00d33c4fe1032`.

This is a genuine native song-production boot of the source checkout under an isolated local branch. It is **not** an assertion that `world/american-empire` itself satisfies the main OS production naming contract or that the client browser invokes Godot. Do not claim persistent in-production agent, Godot processing, source ingestion, accepted film shots or automatic Drive sync without additional run-specific proof.

Next: keep using the built-in Studio/GodRender production guards, formally inspect media source hashes and design an auditable world-event-to-Godot scene contract; then run short Godot proofs with the existing cinematic continuity.
