# The American Empire — P1: Original Canon Recovery and Lock

**Development branch:** \`world/american-empire\` in \`SouthPaw302/GodRender\`.

**Current stage:** P1, a locked *written-universe* archive. This is **not** a new film production, a Godot runtime integration, or a simulated world implementation. Do not claim P2/P3 completion from P1 files.

## Start here

1. Read \`CANON_POLICY.md\` and \`CANON_LOCK.json\`.
2. Read the **verbatim** recovered files in \`archive/\` in the lock's \`read_order\`: Universe Bible, Reality Matrix, Chronicles 02, 03, 04. Chronicle Zero is contained within the Bible.
3. Treat the structured Reality Matrix as the initial authority for characters, systems, relationships and 2026–2037 timeline. Do not use a later cinematic script to overwrite it.
4. Run \`python worlds/american-empire/tools/verify_canon.py\` from a GodRender checkout, or \`python tools/verify_canon.py\` from this world folder.
5. New entries belong in a separate proposed-addenda and derived-state layer (future phase), never by editing \`archive/\`. A future canon promotion requires explicit human approval and its own traceable change.

The archived source comes from [the pinned written-canon Git revision](https://github.com/SouthPaw302/AIVideoEdit/tree/d768ee1684ebddd06af249f3a366181c929bc80c/projects/american-empire-canon-archive) and the independently preserved [Drive canon folder](https://drive.google.com/drive/folders/1UYyGfYE4bhd5fqh8QdOQWgqmpTc2TA0z). Source paths, bytes, and Git blob hashes are pinned in \`CANON_LOCK.json\`. \`archive/03_PRODUCTION_LINK/\` is **historical provenance only**.

## P1 scope and boundary

- Included: 9 verbatim archived source/support files; the five-item authoritative reading sequence; hash-pinned lock; source/adaptation separation; deterministic local verifier and tests.
- Not included: Paris images, scores, video masters, archived production runners, a live simulation engine, a Godot scene, or approval of new story additions.
- Separately recovered full Chronicle Five is **not** in the pinned canonical archive; it must not silently enter canon. Chronicle 01 is not a separate recovered source file.
- Sections titled \`Additive canon proposed\` or \`Proposed additive canon\` inside the recovered chronicles are preserved **as proposals**, not automatically promoted historical facts.

**Validation:** The verifier is an audit guard, not GitHub branch protection or proof that any world simulation/production media ran. Native GodRender production boot/guard rules still apply before production processing.

Next milestone **P2:** build a read-only source parser, entity/event/relation schema and provenance-backed query layer from these exact sources, with alternative hypotheses and cinematic adaptation kept explicitly separate.
