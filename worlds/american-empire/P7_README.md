# P7 — Living Inhabitants (deterministic agent simulation)

**Source branch:** `SouthPaw302/GodRender@world/american-empire`. P1/P2/P3/P4/P5/P6 and GodRender `main` remain unmodified.

## Scope

The browser's **Living Inhabitants** tab now runs ten modeled actors: five original P1 viewpoint characters (Mara Venn, Caleb Reed, Neda Farzan, Lin Meiyu, Jonah Vale) and five existing political institutions (Keepers, Ascendants, Continental Clearing Union, Plural League, Unbound).

The original Reality Matrix establishes only their names, roles, goals, known facts and sealed unknowns. **Agent locations except explicitly established story settings, starting resources, goals as numbers, trust scores, policy rules, decisions, communications and memories are hypotheses and do not create canon.** The model never automatically reveals the explicit `does_not_know` passages.

## Causal mechanics

- Replays 12 annual steps (2026–2037), reading the *exact active P5 run* and the associated P6 regional model, with no edits to either.
- Each actor observes material services and local independence, weighs five policy preferences (relief, liberty, truth, order, trade), selects an affordable response, spends bounded resources, and gains personal experience.
- Actions influence service/autonomy as a separate **P7 overlay**, plus the participant's modeled standing and social trust. Hypothetical spatial effects propagate via inherited P6 directed edges with a one-year delay.
- Public action summaries reach connected agents on the *next* simulated year only if their modeled trust remains adequate. Private memories and canonically unknown information are **not transmitted**.
- Each actor retains at most 40 timestamped, typed memory records. Memory reflects its local observations, personal decisions and inbound modeled reports—not arbitrary omniscient lore.
- A user can issue a priority directive for one actor from a selected year. The baseline remains available for direct comparisons; earlier annual choices must not change.
- A deterministic source-bound SHA-256 chain records every annual state, with exact replay and export. Browser-local storage records directives keyed to the P5 run and P6 event hash.

## Browser verification

Real Playwright/Chromium tests run both HTTP and file:// builds and check:
- P7 source and locked P1 character knowledge remain byte-consistent;
- 10 distinct actors, 30 modeled directed trust edges, 12 annual snapshots;
- private sealed canon unknowns cannot leak into acquired knowledge;
- 2030-directed policy intervention changes the selected actor's decision and leaves 2029 untouched;
- replay, tamper rejection, full JSON export, local persistence/reload and undo;
- switching P5 worlds rebuilds P7 against the proper shared P6 regional source.

## Limits and production boundaries

This is a **real working but small, deterministic, rule-based social simulation**, not an autonomous LLM society, freeform speech engine, population simulation, self-aware agents, or full geopolitical model. Ten seed actors are illustrative, and modeled local effects are not historical estimates.

The Second Brain on Drive is **GodRender's reusable production library** of workflows/skills/FX/proofs; it is not fictional world memory. Future character portraits, environments, voices, 3D scenes and media processing should retrieve proven methods from that library, run through native GodRender safeguards, save working outputs in Drive AE, and write back only verified reusable improvements. **Opening this browser tab performs no remote processing or Drive writes.**

## Acceptance procedure

Open the preview's **Living Inhabitants** tab, select Neda Farzan, set 2030, choose **Centralized order**, then apply. Observe the behavioral divergence and resulting local/trust effects, advance to 2037 to inspect memory, and verify replay. Export the source-bound receipt. Reload and confirm the local directive persists; undo and return to the baseline.
