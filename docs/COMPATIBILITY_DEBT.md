# GodRender — Native Core Cutover

GodRender contains its own checked-in `bootstrap.py`, `general/reusable/` production guards, FX runtime, model registry and `scripts/` utilities. The Studio boot adapter clones **only its own current local GodRender Git checkout** into an isolated attested runtime. No other repository is cloned or treated as an executable authority.

## Versioned compatibility (not active legacy infrastructure)

Old `.aivideoedit` directories, `aivideoedit.*` JSON schemas, `AIVE_*` configuration keys, `aive://` links and the literal bootstrap PASS are kept as wire/storage compatibility formats. Their presence does not mean GodRender depends on a historical repository. Existing projects, receipts, and older production records continue to use those formats.

The 175 original core files were restored from the historical MainV2-Lab main source, including the exact original FX proof MP4 and contact sheet. The Git source history remains provenance only. Native bootstrap `REPOSITORY` and the current-main source manifest now point to `SouthPaw302/GodRender`; all original code/FX files remain traceable to their Git SHA. `upstream/` history is never executed as the primary core.

## Cutover acceptance

The change is not qualified for production until both GitHub Studio integration verification and parallel processing checks pass on the native cutover branch, the real native boot attests its snapshot, the source integrity manifest passes, and an independent production review confirms existing song state is preserved. Approval for releasing a film remains manual.
