# Nordic B02 — native FX technical proof, 2026-10-25

Status: TECHNICAL RENDER PASS; DIRECTOR REVIEW REQUIRED. B01 remains protected.

**Video:** https://drive.google.com/file/d/1kHJ_jjs03KBK1JibAWC_nyCMhSe9lMWf/view

**Provenance**
- Branch: `song/nordic-remastered` at `028b4954162f7ebad2dc7422fb847db34ce7deb4`; native Main `03e4d790a2cfb14b4e9848ee5f5f948f9498a4eb`
- GodRender native BOOT PASS, consolidation 296 files PASS, canonical FX precompile PASS
- Original B02 ZIP, original Gemini A and full master MP3 matched their manifest SHA-256; six selected stills individually matched
- Result: 1280×720, H.264/AAC, 503 frames, 24 fps, 20.958333 seconds, 5,541,132 bytes
- Result SHA-256: `33ce1385fa0e8ba10fc16a4c702a64b4abf76455e2c8f118b7eceaec71d4b9f6`
- Executed native FX: FX2-CAMERA-023, FX2-LIGHT-002, FX2-ATM-021, FX2-LIGHT-025, FX2-LIGHT-024, FX2-TRANS-026, FX2-TRANS-027.

**Execution detail:** The unmodified B02 script was attempted but its repeated MP4 source seeks exceeded the sandbox execution window. A local-only memory/seek optimization imported the repository's exact renderer functions and canonical FXExecutor, preserved approved manifest timestamps and all FX, decoded original source video sequentially and encoded the 11 segments individually for final H.264 concatenation. Original renderer and Main remain unchanged. No assertion of byte-for-byte equivalence to the unmodified encoding path.

**Next:** Director reviews B02 scene motion, handoffs, portal ignition and music sync. Do not promote it to accepted or begin B03 without Director acceptance.
