# American Empire — P3 Simulation Engine

**Phase:** P3: deterministic, counterfactual world-state engine, **not** canonical-history authoring  
**Branch:** \`SouthPaw302/GodRender@world/american-empire\`  
**World source:** immutable, byte-verified P1 original canon; read-only P2 Matrix query graph.

## Scope delivered

- \`engine/simulation.py\`: 2026–2037 deterministic scenario engine; strict typed actions, bounded integer seven-variable state, simultaneous annual feedback, scenario receipts, hash-chained snapshots, exact deterministic replay, compare/fork.
- \`P3_MODEL.json\`: openly declared illustrative mechanics, coefficients and limitations. These are **model assumptions**, not revelations about the fictional historical timeline or scientific calibration.
- \`P3_SCENARIO.schema.json\`: well-defined input scenario format with strict action enum.
- \`tools/simulate.py\`: no-network CLI for scenario status, execution, fork, comparison and replay.
- \`scenarios/examples/\`: three original/noncanonical examples and standalone fork actions.
- \`tests/test_simulation.py\`: temporal, causality, replay, anti-tamper, comparison, fork and source-immutability tests.
- \`.github/workflows/american-empire-p3-simulation.yml\`: tests P1, P2 and P3 on a GitHub runner, retains scenario outputs as ephemeral evidence.

**P1 canon files and P2 graph implementation remain untouched.** The simulation never writes back to either. Derived decisions are always marked \`scenario_only\`.

## Mechanics: a working prototype, not predicted reality

Initial values of V1–V7 are read *verbatim* from the Matrix \`simulation_variables[].initial\`. The Matrix does not date every value as a 2026 observation: P3 treats them as **2026 experimental seeds** solely for comparability. Annual updates advance by bounded, simultaneous feedback over last year's state and the current year's explicit scenario actions.

| Variable | Matrix meaning |
|---|---|
| V1 | Material reliability |
| V2 | Public consent |
| V3 | Elite defection |
| V4 | Rival interoperability |
| V5 | Military futility |
| V6 | Right of exit |
| V7 | Directorate cohesion |

All are integers clamped to [0, 100]. Explicit actions have named types (e.g. \`stack_relief\`, \`independent_alternative\`, \`civic_oversight\`, \`exit_guarantee\`, \`sentinel_demonstration\`) and a bounded intensity of 1–3. The named \`subject\` must resolve to a real P2 entity, but **does not imply regional simulation**; P3 currently applies global indices only.

P3 exposes two **illustrative proxy calculations**:

- \`accession_pressure_raw = (100 - V1) + V3 + V5 - (100 - V2) - V4\` — a proxy expression loosely mapped to the original text's accession-pressure concepts; **not** an original documented numerical formula or measured political probability.
- \`dependency_gap = V1 - V6\` — a heuristic trade-off between material reliability and usable exit. It is not a welfare measure.

Each snapshot includes the year's **unchanged canon title as a reference anchor** plus distinct, hypothetical numeric state. The order of interventions within the same year is deterministic (sorted event ID). Numerical changes are recorded by typed action, declared amount and actual amount after clamping.

## Try it

From repository root:

\`\`\`bash
python3 worlds/american-empire/tools/simulate.py status
python3 worlds/american-empire/tools/simulate.py run --scenario worlds/american-empire/scenarios/examples/baseline.json --output /tmp/ae-baseline.json
python3 worlds/american-empire/tools/simulate.py run --scenario worlds/american-empire/scenarios/examples/independent-corridor.json --output /tmp/ae-independent.json
python3 worlds/american-empire/tools/simulate.py compare --left worlds/american-empire/scenarios/examples/baseline.json --right worlds/american-empire/scenarios/examples/independent-corridor.json
python3 worlds/american-empire/tools/simulate.py replay --receipt /tmp/ae-independent.json
python3 worlds/american-empire/tools/simulate.py fork --parent worlds/american-empire/scenarios/examples/independent-corridor.json --year 2030 --name second-path --events worlds/american-empire/scenarios/examples/fork-events.json --output /tmp/ae-second-path.json
\`\`\`

The \`baseline\` scenario has no explicit interventions and **is not canon**. The independent-corridor and high-integration scenarios are deliberate counterfactuals and should never be treated as new chapters or events.

## Truth and reproducibility

- P1 local integrity verification runs before P2, and P2 construction precedes P3. Source drift blocks all simulation.
- Inputs undergo strict field/type checks: no unknown action, invented subject, date outside the 2026–2037 spine, negative intensity or unapproved arbitrary variable mutation.
- Each run records the P2 semantic graph digest, P3 model digest, input scenario, yearly state, per-action receipts, previous snapshot digest and final run SHA-256.
- \`replay\` regenerates the **entire** result and requires exact equality. It does not simply trust the original \`run_sha256\`.
- \`fork\` references a parent run hash; it drops later parent actions and verifies unchanged pre-fork numeric states. It is an **offline, independently checkable** branch artifact, not a durable mutable database. A supplied child branch reference must be interpreted as lineage metadata and validated against its parent independently if that guarantee is needed for external third-party inputs.
- User-selected output files are permitted outside this world's source tree or beneath \`scenarios/generated/\`. No overwrite of existing files, no writes in P1 archive.
- CI-created JSON run files are temporary artifacts subject to GitHub retention; the engine and input spec in Git are the long-term source of reproducibility.

## Explicit non-goals

P3 is a **prototype deterministic world-state calculation**, not a global-resolution civilization simulator, geopolitical forecasting engine, AI decision-agent society, Godot environment, or live historical feed. No geographic supply graph or per-character behavior is simulated yet. Parameters are not calibrated to external data. New scenario choices are **not** changes to the canonical 2026–2037 event spine.

Next phase (P4) could feed hypothetical, versioned snapshots to a Godot viewport while keeping every visualization marked as either canon scene reference or counterfactual state.

## Validation

\`\`\`bash
python3 worlds/american-empire/tools/verify_canon.py
python3 -m unittest discover -s worlds/american-empire/tests -p 'test_*.py' -v
python3 worlds/american-empire/tools/simulate.py status
\`\`\`

Check the **GitHub Actions conclusion and artifact** before calling the version verified. Boot and production acceptance remain governed by GodRender's native guards; a P3 PASS is an isolated technical check, not a media-production run.
