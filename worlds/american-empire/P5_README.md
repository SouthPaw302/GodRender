# The American Empire — P5 Living Simulation (Browser)

## Delivery and authority

P5 extends the verified browser-first World Explorer from \`SouthPaw302/GodRender@world/american-empire\`. It does **not** create a new server or duplicate GodRender's production toolchain. The simulation runs locally in Opera/Chrome/Firefox using a browser port of the verified P3 Python rules. The original P1 archive, P2 source graph, P3 model, Godot project, Drive Second Brain and native Studio are untouched.

The **Simulation Lab** now offers:

- Source-backed validation of all ten P3 action types, subjects, intensities and allowed years
- User decisions that create isolated, SHA-referenced counterfactual branches at a selected year (2027–2037), retaining all prior parent years
- Advance/rewind to any year, display seven modeled world variables plus accession and dependency *proxies*
- Deterministic replay and hash-chained yearly snapshots, explicit per-action realized deltas, export of full P3-compatible receipts
- Comparison between any two available branches, including first divergent year and signed 2037 state deltas
- Browser-local scenario save/load and JSON import with fail-closed provenance, source/model compatibility, lineage verification and exact full run replay for receipts
- A direct cross-link into the existing World Matrix so custom branch values can be viewed alongside canonical entity relationships and the original timeline

### Golden parity contract

The client **does not trust a rewritten explanation of the rules**. \`build_web.py\` exports the exact P3_MODEL.json and source scenario specifications from Git. On startup, the browser constructs the P3 rules and checks its model SHA-256 against the Python-generated bundle's model hash. It then recalculates baseline, independent-corridor and high-integration scenarios entirely in JavaScript and verifies their run hashes **and all 12 annual snapshot SHA-256 values** against the P3 Python outputs. A parity mismatch halts the explorer. Python P1/P2/P3/P4 regression suites still gate the build.

The browser's \`simulator.js\` uses strict typed inputs, sorted event IDs, bounded integer 0–100 variables, simultaneous feedback, source-anchored event names, SHA-256 snapshot chaining, receipt replay and explicit \`scenario_only\` authority. P3 Python is the source-of-truth reference implementation, not a remote runtime dependency.

### Persistence boundary

Saved scenarios use browser \`localStorage\` and are **not cloud-synced**. Losing local storage loses any unexported work; use the JSON export for durable backup. Imported data must match the exact P2/P3 source and parent lineage. Neither simulation decisions nor archived file uploads can promote new canon. The P5 site makes no writes to Google Drive or GitHub and never invokes model workers, FX processing, GitHub runners or Godot behind the scenes.

This phase is a **live, responsive deterministic seven-variable prototype**. It is not yet a geographic, multi-agent, multiplayer or continuously running server-backed world.

## Run and verify

\`\`\`bash
python3 worlds/american-empire/tools/build_web.py --repro
python3 -m http.server 8765 --directory worlds/american-empire/web/dist
\`\`\`

Visit \`http://127.0.0.1:8765\` and select **Simulation Lab**. For an offline copy, open the newly generated \`web/dist/standalone.html\` directly in a supported browser. Cryptographic replay requires browser WebCrypto SHA-256 support in a secure context, supported by mainstream HTTPS or file:// browser implementations but may vary with privacy policies.

GitHub Actions \`American Empire Web + Second Brain\` tests the HTTP page and offline HTML in Chromium. Besides the inherited browser tests, P5 tests exercise Python hash parity, a 2029 Atlas fork, comparison, advancing to 2037, SHA replay, full receipt export, local save/reload and rejection of a modified imported receipt.

The Drive Second Brain remains a *production capability library* (FX, recipes, models, proofs), **not** the simulation database. For real media work, retrieve relevant entries and their evidence, execute through GodRender's native gates, and save accepted outputs in Drive AE; this Simulation Lab currently creates scenario metadata only.

## Suggested manual acceptance check

In **Simulation Lab** choose baseline, set 2029, select Atlas integration with intensity 2 and source \`system:S1\`, name the fork \`atlas-alternative\`, and press **Branch & apply decision**. Compare it against baseline, advance to 2037, verify replay, save locally, export JSON and reload the browser. The canonical 2029 title stays unchanged; only modeled scenario numbers diverge.
