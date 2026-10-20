# American Empire — Browser-First World Explorer

**Source branch:** \`SouthPaw302/GodRender@world/american-empire\`  
**Primary application:** \`web/src/index.html\` built via \`tools/build_web.py\`; the existing P4 Godot desktop scene remains an optional visualization client.

## Architecture

\`\`\`
P1 original written canon (byte-locked, unmodified)
 ├─ P2 World Matrix → actors, Stack systems, relations, people, chronology
 └─ P3 simulation → isolated hypothetical scenario snapshots
           ↓
P4 data bridge → provenance-backed static world JSON
           ↓
GodRender Second Brain on main (already inherited on this branch)
 ├─ config/brain_source_index.json (dated legacy provenance; not live authority)
 ├─ FX v2 registry (91 registered names/gates; not proof of execution)
 ├─ Standard Workflow Registry (approved source recipes; not job results)
 ├─ MODEL_REGISTRY.json (configured model metadata; not inference)
 ├─ MEDIA_CAPABILITY_MATRIX.json (supported source and output classes)
 ├─ docs/BRAIN_INTEGRATION.md (Drive brain authority and evidence rules)
 └─ Google Drive source (linked, authentication retained; never copied to public web)
           ↓
Python tools/build_web.py → static site with source-linked brain index
           ↓
Browser → World Matrix / Chronology / Second Brain / Director Desk
\`\`\`

## Build and view

With Python 3.10+ from GodRender repository root:

\`\`\`bash
python3 worlds/american-empire/tools/build_web.py --repro
python3 -m http.server 8765 --directory worlds/american-empire/web/dist
\`\`\`

Open http://127.0.0.1:8765. On Windows use \`py\` instead of \`python3\` where necessary. **No Godot installation required to use the browser.** No Node dependency for the application. Browser-interaction CI uses pinned Playwright Chromium only for testing.

Vercel-compatible project settings (for the GodRender Git repository branch \`world/american-empire\`): **Framework Other; root repository root; build command** \`python3 worlds/american-empire/tools/build_web.py --repro\`; **output directory** \`worlds/american-empire/web/dist\`. Deploy as a preview first, not by changing GodRender \`main\`. Live URL exists only after a real completed provider deployment.

## First browser capabilities

- Interactive source-provenanced faction/Stack relationship canvas, source inspector and viewpoint characters.
- Canonical written chronology across 2026–2037 (unchanged as users switch scenarios).
- Clearly marked P3 hypothetical numeric gauges, three scenarios, and explicit proxy labels.
- Searchable real Git registry of FX, workflows, models and media classes, with source blob SHA and status; source links open exact GodRender branch paths. Effects requiring proof cannot be selected as approved.
- Authenticated links to Drive Second Brain and contract. No Drive content or credentials are redistributed.
- Director Desk creates \`american-empire.production-brief.v1\` JSON with scenario/canon separation, source pointers, optional approved-registry effect ID and a documented non-execution flag.
- Native GodRender Studio source and local launch documented and linked. Static browser **does not** start Studio workers, FX, ML inference, GitHub Actions production pipelines or Godot.
- CI regenerates from pinned canon, verifies source hash evidence and executes a real Chromium browser smoke test.

## Authority/safety requirements

1. Only the P1 Reality Matrix and Universe Bible are literary authority. Later unapproved chronicle proposals and the Paris film adaptation are not silently merged.
2. P3 numerical projections are experimental global seven-variable deterministic mechanics, not established events or evidence of actual politics.
3. Second Brain is a search/evidence index; a registry gate label or last historical SHA cannot certify an effect for execution. Native guards, current exact code, prior proofs, rights and creative acceptance remain necessary.
4. Web preview is read-only; production briefs are suggestions. The viewer never uses hidden cloud credentials, does not request Drive authentication tokens and does not expose the contents of connected user documents.
5. Drive remains durable original media and provenance; GitHub tracks source code and non-executable indexes; Actions artifacts expire.
6. Any future secure live Studio connection should use a separately audited authenticated server interface and explicit action authorization; **never expose Studio's loopback controls or auth token in this static site**.

**Scope note:** This release integrates *retrieval and handoff* with the inherited GodRender stack and Second Brain. It does not yet create a physical Earth-scale simulation, run agents autonomously, spawn native FX jobs from the web, or embed the Drive database anonymously.
