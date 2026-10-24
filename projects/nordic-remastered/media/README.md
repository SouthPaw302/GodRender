# Nordic (Remastered) — Media storage and production registry

**Branch:** `song/nordic-remastered` — staged here only; no `main` changes and no Vercel deployment.

**Definitive machine-readable hashes:** [MEDIA_ASSET_MANIFEST_2026-10-23.json](./MEDIA_ASSET_MANIFEST_2026-10-23.json) (SHA-256 for 54 individually indexed assets, including 20 chat-generated Batch 05/06 stills and nine new recovery ZIP archives).

## Canonical Drive hierarchy

| Folder | Drive | What belongs here |
|---|---|---|
| 01 Source Media | [Open](https://drive.google.com/drive/folders/1rnLZQSepdEiYhd0Uld-Fi0YKzaNa5dDC) | Song MP3 and both original Gemini MP4s, unchanged |
| 02 Director & Storyboard | [Open](https://drive.google.com/drive/folders/19dvRrCvwV90bl9_RfLYbrCMGiK-1NM85) | B01–B06 extracted-frame packages and their internal manifests |
| 03 Shots & FX Proofs | [Open](https://drive.google.com/drive/folders/17ovXoXQ0do1ElC-VMAggMS9Qkt3mxmHk) | Generated still candidates, source-faithful optical B05 frames, asset registry, recovered unclassified images |
| 04 Review Renders | [Open](https://drive.google.com/drive/folders/1rTfflq8yNB7JzuiMje5upJ9zYVIxUdax) | Current Nordic editorial rough-cut MP4, QC still and receipt |
| 05 Masters & Delivery | [Open](https://drive.google.com/drive/folders/1uP79DaLiVE19bbKM_YX7EeWClJ3GGefN) | Reserved; no approved master |
| 06 Previous Backups & Assorted Archives | [Open](https://drive.google.com/drive/folders/1qDCFGT--rlCWX9OsQ3VA1BhsimluzD5G) | Original eight-part assorted image backup and earlier loose renders backup, moved unchanged |

### Exact recovered stills from conversation

- [B05 AI renders](https://drive.google.com/drive/folders/1uRFte0Fi_PAQyePvQgsjfcZA4uSH30VI) — 10 full-frame individual images `B05_01.png` to `B05_10.png`, in two ZIP packages.
- [B06 AI renders](https://drive.google.com/drive/folders/1YGlbhNAL2vyAjgg9y4Iukc2AFjjZBYK9) — 10 full-frame individual images `B06_01.png` to `B06_10.png`, in two ZIP packages.
- [Recovered unclassified loose images](https://drive.google.com/drive/folders/1lCGlaZKqCMezjitjCsGmgVhT8dL7L_ho) — 22 previously unbacked loose image files, stored in five separate packages, marked **review only**. Some are concept/drift artifacts; none is silently promoted to a song shot.
- [Manifest copy on Drive](https://drive.google.com/file/d/1kk31f1TVsY2rdvuRtFyBx5PiNlah7XMN/view).

The B05 **optical** frames predate the B05 generated renders, remain distinct, and are still in `03 Shots & FX Proofs`. Distinguish `SOURCE_FAITHFUL_OPTICAL` from `chat_generated_individual_image`.

### Batch acceptance / editorial contract

- B05 and B06 **rendered** does not mean director-QC **accepted**, motion-processed, or assembled into a film.
- The numbered B05 and B06 files are the real images generated in the current ChatGPT session and recovered as exact original byte snapshots. No storyboard or source extract is substituted as a generated image.
- B01–B04 earlier art is preserved in previous assorted archives, but its exact numbered-image-to-archive mapping is **not yet reconciled and is not falsely asserted here**.
- Originals are preserved, older miscellaneous material is quarantined for review, no drifted snow-cloak replacements are approved, and no final release occurs without user approval.

### Provenance

This index references Drive files and the accompanying SHA-256 JSON registry; it does not claim GitHub runners executed these images or that GodRender FX has processed them. Future moving-shot proofs should use native repository workflows and publish their own runner logs/artifact SHA-256 after visual inspection.
