# GodRender — Legacy Runtime Compatibility

**This is a technical migration record, not a second product or a second active video repository.** GodRender is the sole active development and film project.

## What was renamed in the GodRender name pass

- Browser title/header, Studio HTTP service identity, startup scripts, application errors, agent instructions, MCP handshake name and GodRender-created production workspace labels.
- Agent documentation and README now direct every new change and handoff to GodRender.
- Prior-production names, source Git URLs, SHA hashes and render histories are preserved because they are evidence.

## What is intentionally still compatible

- `studio/core_adapter.py` currently installs/boots an **external legacy production OS checkout** and checks its literal `AIVideoEdit OS BOOTSTRAP: PASS`. Its remote points to the older implementation; changing the display name does not change this fact.
- `.aivideoedit` directories, `aivideoedit.*` serialized schemas, `aive://asset` URIs and `AIVE_*` environment keys are versioned compatibility interfaces. Renaming them without migrating readers, writers, guards and existing project manifests can damage old projects.
- `upstream/`, legacy branch indexes, technical proof reports and pinned import manifests are historical source evidence; do not rename paths or modify byte hashes to hide provenance.
- The legacy MCP Python module filename is retained for existing harness clients, while `studio/godrender_mcp.py` is the preferred new entrypoint.

## Separate future cutover gate

To remove the last external checkout dependency, **first** implement and independently prove a GodRender-native versioned bootstrap, checked-in runtime snapshot, schema migration/read-compat, guards and per-song workspace initialization. Then test both existing productions and a fresh authorized song in GitHub Actions and with human visual QC. Until that passes, do **not** silently point the legacy bootstrap at GodRender or fabricate a successful session.

The name pass changes identity; it **does not claim** this core boot migration is complete.
