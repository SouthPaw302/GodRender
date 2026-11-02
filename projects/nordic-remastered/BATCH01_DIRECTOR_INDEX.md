# Nordic — Batch 01 Source Storyboard (2026-10-22)

Production branch: `song/nordic-remastered`.

## Actual evidence
- Native GodRender boot: PASS, [workflow 39725935406](https://github.com/SouthPaw302/GodRender/actions/runs/39725935406).
- Original first video, 10.005 s 1280x720 24fps: [Drive](https://drive.google.com/file/d/1PyHI7F7In-uZxYhZfHKJK17Ah_8LCWaB/view).
- Original portal video, 10.005 s 1280x720 24fps: [Drive](https://drive.google.com/file/d/1wpHGl6NgP9XMPbEtasYrqt8sEbQaXFJ8/view).
- Original master audio, 137.952 s: [Drive](https://drive.google.com/file/d/1DxnCzKJK-bJkCgQsyEbXypCvbdJ25Vvr/view).
- Batch 01 ZIP (ten individually hashed source keyframes, storyboard image, manifest, shot plan): [Drive](https://drive.google.com/file/d/1ILpXLRpxg-1_VFD3zoNqlH4r3cskIGPK/view).
- Parent: [GodRender / Nordic](https://drive.google.com/drive/folders/1TUZg5lJ0eIsNDOokp0mmBI_pxe0izdq7).

## Director guidance
The first ten storyboard frames are exact extracts at 0.50, 1.45, 2.40, 3.35, 4.30, 5.25, 6.20, 7.15, 8.10 and 9.05 seconds of the first user-supplied film. These are source-derived keyframes, **not** model-generated variants, FX proofs, or accepted final shots. The Observer (face, beard, costume), cliff and night geography are protected starting anchors, pending review and promotion to user-accepted canon. Emissary Pair design comes from the second video. Story thesis: 'Humans became conscious of their own existence and began creating mythologies. The observer began rendering reality.'

Planned six batches of ten, advanced only after reviewing source stills and FX moving proofs per GodRender `AGENTS.md`, `PRIME_DIRECTIVE.md` and Zero Drift. Batch 01 is the Witness; the portal and futuristic Emissaries become primary in later batches. Do not invent an image generation or FX execution receipt.

Next: use source media by the exact Drive file IDs above, ingest with current GodRender-supported runner route, verify local hashes against uploaded bytes, inspect storyboarding, then create representative genuine moving FX proof and perform actual sandbox viewing / repo receipt QC.


## Moving FX proof 01 — rendered, awaiting Director acceptance

- Timing authority: `analysis/ONNX_SCAN_RECEIPT.json` + `analysis/EDIT_RETIMING_PLAN.json`.
- Proof edit: `B01_01 0.000–6.580` → `B01_05 6.580–12.140` → `B01_09 12.140–20.000`.
- Master audio remains byte-locked at SHA-256 `d5dc263e6edc7a248503acc1f8ecc5cc2ab91727905ef8ddac3d63a6a1644c2f`.
- Native Main FX identities used: `FX2-MOTION-002 localized_living_flow`, `FX2-LIGHT-002 moving_light_field`, `FX2-CAMERA-023 narrative_camera_travel`; all are `approved` in Main at `03e4d790a2cfb14b4e9848ee5f5f948f9498a4eb`.
- Rendered proof: 20.000 s, H.264/AAC, 640×360, 24 fps, 480 expected decoded frames, zero black frames.
- Proof SHA-256: `f7a612fb1495acf8438f25d0afdeefae16e764898a4a9fc7c206b0511c8efcd1`.
- Receipt: `proofs/B01_MOVING_FX_PROOF01_RECEIPT.json`.
- Storage status: current conversation proof only; **not promoted to Drive, canon, or release**.
- QC status: mechanical decode/pixel-motion checks pass; artistic acceptance remains Director/user review.
