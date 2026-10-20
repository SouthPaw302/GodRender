# P8 Population Intelligence — GodRender bounded runner

This is a real model-runner boundary, not a claim that the browser has a perpetual AI population.

## Operator procedure
1. Open GitHub Actions on GodRender and choose **American Empire Population Intelligence Pilot** on branch world/american-empire.
2. Choose **smoke** (deterministic, no AI inference) or **smollm2-135m** (downloads and executes the public Apache-2.0 HuggingFaceTB/SmolLM2-135M-Instruct model on a temporary GitHub-hosted CPU runner).
3. Select a character ID (e.g. claire, daniel, neda), and a fictional year 2026–2037.
4. The runner builds the exact AE world from Git SHA, opens the local browser, exports a P7 run receipt, verifies every snapshot and the P7 SHA-256 chain, and passes only the selected character's limited knowledge, memory and local state to the chosen model.
5. The model must return exactly ONE validated priority from relief / liberty / truth / order / trade. Unsupported or malformed output fails the job; it is **never** silently replaced with a rule-based action.
6. Download **ae-population-model-proposal.json** from the GitHub Actions artifact; in Observer → Living Inhabitants, choose **Load AI runner proposal (JSON)**.
7. Browser checks run/source/annual snapshot digests, model backend, actor and year. The user must still press **Create alternative choice** to create a scenario-only divergence, and may export the resulting P7 run receipt.

## Canon boundary
The model does not control history, public broadcasts, accepted film dialogue, or any canonical fact. It can propose only an actor's policy PRIORITY, never unbounded free-form actions. Its context never includes other actors' private memories or the sealed unknowable canon passages.

All P8 Paris dates are provisional simulations, not confirmed film chronology. Source movie assets remain in private Google Drive AE.

## Implementation / status
- Python candidate validator / optional CPU model runner: worlds/american-empire/tools/population_model.py
- Browser seed export: worlds/american-empire/web/tests/export_population_seed.mjs
- GitHub workflow: .github/workflows/american-empire-population.yml
- Browser importer: worlds/american-empire/web/src/people.js
- This is a **batch proof with manual review**. It is NOT a 24/7 hosted model service, websocket stream, whole-country population or a Godot full-film render.
- The default push CI mode is deterministic smoke and cannot be advertised as actual model inference. The real public 135M model runs ONLY after explicit workflow_dispatch selection of smollm2-135m; an actual successful Actions log and model-labeled proposal artifact are required before claiming it works.
- HF reference: https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct, Apache 2.0.

Further choices (larger models, ONNX acceleration, Vercel AI Gateway, persistent servers, scaling population) require measured capacity/cost and a tested provider path, not imagination or automatic deployment.
