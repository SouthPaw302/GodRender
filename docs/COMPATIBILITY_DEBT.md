# GodRender — Native Runtime Migration (2026-10-19)

GodRender is the only active production/processing authority. Native bootstrap, Studio, project state, guard contracts, release checks, Jev, model/ONNX routing and FX execution use GodRender-owned runtime identifiers. The Studio core adapter uses a pinned GodRender local checkout; no historical repository is cloned, executed, or required.

## Removed active legacy interfaces
- Native session and boot data use `.godrender` and `godrender.*` identifiers.
- Environment variables and asset URIs use `GODRENDER_*` and `godrender://`.
- The active OS guard manifest is `general/reusable/GODRENDER_OS_MANIFEST.json`.
- MCP executes from `studio/godrender_mcp.py`, without the retired adapter module.
- CI enforces both `tools/verify_independence.py` (external repo isolation) and `tools/verify_native_identity.py` (active-code identifiers).

## Frozen historical evidence
`upstream/`, `config/brain_source_index.json` and immutable source/FX proofs remain traceable historical inputs. They cannot authorize execution, and their legacy labels are **not** connections to old repositories. The import manifest records retired files and intentional native replacements. Do not rewrite approved media, effect identities, hashes or past receipts to make the archive look newly produced.

Historical local project files are **not silently converted**: any import requires explicit project-by-project conversion with a backup and hash evidence. Unconverted data must fail closed instead of being interpreted as a validated native production.

## Verification boundary
Native bootstrap, CI, import integrity and schema checks establish technical correctness only. They do not establish that a particular song's media was processed, that a full-film proof was reviewed, or that the user approved release.
