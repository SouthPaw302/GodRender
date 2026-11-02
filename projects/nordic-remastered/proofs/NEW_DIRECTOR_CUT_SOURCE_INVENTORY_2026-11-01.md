# Nordic Remastered — New Director Cut Original Asset Inventory (2026-11-01)
Repository: SouthPaw302/GodRender
Branch: `song/nordic-remastered`
Reference: `production/NEW_DIRECTOR_CUT_V1_MANIFEST.json`

## Actual source-locked film inventory

| Batch | Source storyboard ZIP SHA256 | Individual stills | Narrative |
|---|---|---:|---|
| B01 | 3afe2ca261582e04459ade185bfd18ccc1983b29fcd0a977538c8a9babfb2ecd | 10 | Observer witness / cliff / celestial patterns |
| B02 | 0de98a96c73ebd644d19c49eab1091804f26302e5229a2f32b03f568b585f309 | 10 | Sky memory / glint / portal |
| B03 | 156dd5916efc46b148f92a6bbc07ce91271bbff4412b0f4ea4ef22ea37f8c618 | 10 | Portal threshold / world reveal |
| B04 | 2e2a1d59c4ad76d52ceed915abc3565f7622cff8bf8a5cea1b4a334a90a39564 | 10 | City / architecture / scale |
| B05 | e3609729dd069c5f3ef970a27ef9e26d7b0206a07772cd742921030b5b148abe | 10 | Emissary pair / orb / future awareness |
| B06 | ca31e1bef59dd2332e193596a5840c241d22888c6e7242c4c0704f69bccd80b4 | 10 | Future memory / celestial return / Observer |

All **60/60** PNG inputs were decoded and independently checked against SHA-256 fields inside their respective ZIP manifests in sandbox; source-canon, not generated images. Still selection order and individual frame assignments in `NEW_DIRECTOR_CUT_V1_MANIFEST.json`. Their source shapes are 1280×720 or source-optical-crop variants consistently upscaled to 1280×720 before FX.

Original moving footage (**24fps / 240 frames each**), each used once at original speed:
- `gemini_generated_video_4b4db55f.mp4`, SHA256 `d68af243b94e77f0a7311f99daa6f5b5b4dd9fdfa7a90d3b4b9c002020be6e70`.
- `gemini_generated_video_e4937f10.mp4`, SHA256 `79b7a65bef53cfd35fc9905c9ea4f09ee8a96bcf794e9296596c49d0c5933e68`.
Original complete soundtrack:
- `Nordic  (Remastered).mp3`, SHA256 `d5dc263e6edc7a248503acc1f8ecc5cc2ab91727905ef8ddac3d63a6a1644c2f`.

## Other media found; intentionally inventoried but not promoted into source canon

- Generated B05 stills, **2 ZIP packages**, Drive folder `1uRFte0Fi_PAQyePvQgsjfcZA4uSH30VI`: **QC_PENDING**.
- Generated B06 stills, **2 ZIP packages**, Drive folder `1YGlbhNAL2vyAjgg9y4Iukc2AFjjZBYK9`: **QC_PENDING**.
- Recovered assorted/unclassified images, **5 ZIP packages**, Drive folder `1lCGlaZKqCMezjitjCsGmgVhT8dL7L_ho`: **UNCLASSIFIED_REVIEW_ONLY**.
- Previous rendered FX batches B01–B06: preserved as accepted editorial proofs, **NOT** source footage for this new cut.
- Prior rough cut, FX workprint and archived loose renders: not treated as original media.

No new images were generated. The existing 60 source-derived storyboards and two 240-frame original videos define the source-authorized film.

## Native workflow route

Repository staged all six storyboards and both Gemini videos using current `runner_sources` paths. Missing B02 storyboard and Gemini A source were additionally staged as Git base64 text blobs in `runner_sources/directors-cut-02`, with SHA locks; B01/03/04/05/06 and original Gemini B/audio already reside in existing runner sources. **GitHub Actions must never download source media directly from Drive.**

Native GodRender boot + `FXExecutor` + canonical V2 precompile are mandatory. Existing ONNX result, `analysis/ONNX_SCAN_RECEIPT.json`, is PASS: 90.91 BPM, 210 beats, 58 downbeats; reused, not rescanned.

New edit duration: **3311 frames / 137.958333 s** at 1280×720 24fps, 60 still-derived animated shots and both full original moving clips. 61 registered FX approved, 28 proof-required, 1 conditional and 1 unavailable; only compositionally suitable production-approved entries may be executed. Protect faces, emissaries, observer cliff, portal and structural identity.

**Status:** Inventory SOURCE_VERIFIED; new full-film native Director render and artistic acceptance are separate gates.
