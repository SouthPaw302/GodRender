# Nordic B04 — Director Batch FX Gate Review (RC1)

Date (ET): 2026-10-26
Branch: `song/nordic-remastered`
Runner: https://github.com/SouthPaw302/GodRender/actions/runs/40271950676
Runner artifact: https://github.com/SouthPaw302/GodRender/actions/runs/40271950676/artifacts/12628627303
Durable proof ZIP (includes continuous MP4, silent render, ffprobe and receipt): https://drive.google.com/file/d/15X4VvdvEifBswKsmHKjVApQWSrEOlQIa/view
Decoded continuous picture/audio SHA-256: `863efa114a5d27d58344bcfe3fa081b8f9088d0863705d35267494fc8322afff`

## Director verdict: B04 PASSED — BATCH FX GATE (RC1)

This is the scope-limited **Director working-cut gate**, not final film, master-FX or publication acceptance.

The GitHub runner completed native source checks and boot, verified ZIP/video/still/audio source hashes, compiled the exact canonical FX lock, rendered and muxed a continuous movie, and passed ffprobe frame/duration QC: **326 frames, 1280×720, 24 fps, 13.583333 s, H.264 + AAC stereo**. Both video and audio fully decoded end-to-end in sandbox without error.

Source scene truth: storyboard ZIP `2e2a1d59c4ad76d52ceed915abc3565f7622cff8bf8a5cea1b4a334a90a39564`; original Gemini B `79b7a65bef53cfd35fc9905c9ea4f09ee8a96bcf794e9296596c49d0c5933e68`. Verified from authenticated Drive download in sandbox before runner stage. Original studio audio reused without replacement.

**Creative review scope:** sampled 27 decoded frames across the complete B04 proof (including both sides of joins at 40,58,76,114,131,149,187,205,221,263), with complete adjacent-frame numerical audit of 325 boundaries. No claim is made of uninterrupted normal-speed entire-film playback. Scenes sampled show original Observer/portal boundaries, city topology/transit structure, and emissary poses recognizable; no obvious geometric break in sampled joins. Source-video bridges supply live scene motion; no ten-image flipbook.

## Temporal QC
- Global mean absolute adjacent difference: **1.606** at 256×144; median **0.398**, 95th percentile **4.964**.
- Maximum adjacent difference **13.22** at frame 190, within original Gemini motion bridge, not authored transition.
- Boundary values at 40/58/76/114/131/149/187/205/221/263: **0.438 / 0.321 / 0.252 / 3.299 / 0.283 / 0.262 / 3.412 / 0.398 / 0.323 / 0.022**.
- The transient break begins precisely at B04 frame **263** (film time **90.743333 s**); clean architecture hold through end. No big decorative transition over the break.
- FX actually executed: `FX2-CAMERA-023`, architecture-isolated `FX2-CAMERA-021` and `FX2-SPATIAL-021`, `FX2-LIGHT-002`, `FX2-LIGHT-025`, three `FX2-TRANS-025` internal handoffs. All executed via native registered executor.
- No master inter-batch FX attempted. No source video sped/slowed or looped.

## Production state
B01, B02, B03, **B04** batch FX gates passed (working cuts). Next: B05 batch direction/edit/FX, then B06. Global continuity, master FX rhythm, and final uninterrupted film QC only after all batches are assembled. Preserve original source hashes and leave `main` and prior accepted batches unchanged.
