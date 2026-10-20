# American Empire — P2 World Matrix and Relationship Engine

**Branch:** \`SouthPaw302/GodRender@world/american-empire\`  
**Phase:** P2 read-only world graph and historical query interface  
**Source authority:** P1 locked original written canon, not the Paris film.

## What was built

- \`engine/world_matrix.py\`: Python standard-library parser/projection from the exact hash-pinned Reality Matrix and source chronicles.
- \`tools/world.py\`: read-only command-line interface with deterministic JSON output.
- \`P2_WORLD_GRAPH.schema.json\`: machine-readable graph/export contract.
- \`tests/test_world_matrix.py\`: regression tests for provenance, identity, chronology, link integrity, proposal isolation, copy isolation, and failure on altered canon.
- \`.github/workflows/american-empire-p2-world.yml\`: branch-scoped verification and reproducible JSON-index artifact.
- \`CANON_LOCK.json\`, \`archive/\` and P1 verifier remain **untouched**.

The graph tracks the original Matrix's 10 actors, six imperial systems, five viewpoint people, 12 year phases, seven collapse steps, seven simulation variables, four historical anchors and Continuity Directorate institution. Relationships use only recorded \`key_relationships\`, named prerequisites and transparently marked direct projections of ordering/affiliation. Negative relationship strengths stay signed. **No new fictional facts are generated.**

Each queryable node/link has exact Matrix JSON Pointer and historical Git blob SHA; archived proposals link to the correct chronicle SHA and heading line. Free text is only literal search, not semantic similarity or a fabricated explanation.

## Commands

From the **GodRender repository root**:

\`\`\`bash
python3 worlds/american-empire/tools/world.py status
python3 worlds/american-empire/tools/world.py list --kind actor
python3 worlds/american-empire/tools/world.py show person:P3
python3 worlds/american-empire/tools/world.py relations system:S1
python3 worlds/american-empire/tools/world.py timeline --year 2030
python3 worlds/american-empire/tools/world.py timeline --year 2030 --through
python3 worlds/american-empire/tools/world.py search "Atlas"
python3 worlds/american-empire/tools/world.py search "Winter Bridge Compact" --layer proposal
python3 worlds/american-empire/tools/world.py proposals
python3 worlds/american-empire/tools/world.py documents
python3 worlds/american-empire/tools/world.py export --output /tmp/american-empire-world-graph.json
\`\`\`

\`export\` constructs a deterministically serialized, provenance-backed graph snapshot. It can be stored externally or reproduced from the immutable, versioned Git sources at any time. Export is forbidden to modify \`archive/\` or \`CANON_LOCK.json\`. CI publishes it as a **derived artifact**, not as canonical source.

## API

\`\`\`python
import sys
sys.path.insert(0, "worlds/american-empire/engine")
from world_matrix import WorldMatrix

world = WorldMatrix()  # verifies P1 lock first; throws on source drift
world.entity("actor:A4")                    # Keepers, with JSON pointer
world.relations("system:S1")                 # Atlas's source-backed links
world.timeline(year=2031, through=True)     # established years, no simulation
world.search("transport")                   # literal canon node matching
world.search("Winter Bridge", layer="proposal")  # candidate only
snapshot = world.export()                   # versioned, deterministic JSON
\`\`\`

All public API results are defensive deep copies. No function writes a canon source or a film asset.

## Authority boundary

**Established:** Universe Bible + Reality Matrix and compatible recovered source chronicle facts. The graph is an index into the Matrix, not an assertion that the entire Bible and chronicle prose has been mechanically formalized.

**Proposals:** \`Additive canon proposed\` sections of Chronicles 02–04 are retained with \`candidate_unapproved\` status and **excluded from the established graph**.

**Adaptation:** Paris Act I remains linked via \`ADAPTATION_LINKS.md\`. No adaptation scene, character, film still or score was imported into the graph.

**Hypotheticals:** No counterfactual interventions or simulations are represented as established facts; P3 must keep scenario state namespaced, reproducible, and separate from the canon index.

**Temporal limits:** The \`timeline\` command returns authored phase events; \`--through\` is a chronology filter, *not* a simulated reconstruction or assertion about what any person knew in a given year. Collapse pressures are sequence-indexed rather than assigned invented exact dates. System prerequisites are documented relationships, **not** an executable dependency schedule.

## Validation and next phase

\`\`\`bash
python3 worlds/american-empire/tools/verify_canon.py
python3 -m unittest discover -s worlds/american-empire/tests -p 'test_*.py' -v
python3 worlds/american-empire/tools/world.py status
\`\`\`

P2 success requires actual GitHub CI passing these steps and a queryable graph export. A green job is technical evidence only; it does not claim Godot execution, world simulation or production acceptance.

**P3** would implement deterministic world-state transitions, scenario branching, typed event effects, reproducible snapshots and canon-safe causal calculations. That functionality is **not** silently included in P2.
