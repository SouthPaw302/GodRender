# Nordic (Remastered) — Director FX Plan v1

Date: 2026-10-24  
Branch: `song/nordic-remastered`  
Scope: Drive Brain + current GodRender reusable FX + verified Nordic source/storyboard assets.

## Authority and operating rule

This plan uses the Drive Brain as the knowledge/lineage layer and the current GodRender branch registry as the execution authority. Brain entries that still point at legacy AIVideoEdit paths are not sufficient by themselves; an effect enters the production lane only when the matching FX ID is currently present and `approved` in GodRender's canonical registry.

The six Nordic storyboard batches are source-derived candidates, not independent generated shots and not accepted final canon. The two original Gemini videos stay at natural speed when used as source clips. Do not loop or stretch those clips to claim song coverage.

Production law remains: **internal scene motion first; camera motion last**. Observer identity, beard, costume, hands, cliff geometry, horizon, portal boundary, city topology, emissary identities and interface geometry are protected.

## Visual strategy

The film should not use one repeated FX stack. Each story movement gets a distinct visual grammar:

1. **Witness / ancient sky** — restrained living atmosphere and subtle memory behavior.
2. **Sky remembers / portal ignition** — constellations behave like memory; light condenses into a threshold.
3. **Threshold** — the portal becomes a lens and transfers visual dominance to the future world.
4. **Revelation / city** — spatial depth, transit motion and architectural scale become the dominant movement.
5. **Emissaries / future consciousness** — motion becomes precise and localized around interfaces and light, while faces remain almost untouched.
6. **Return / myth completion** — future imagery becomes a memory inside the ancient sky, then motion collapses back toward stillness.

## Current production-approved FX palette

These IDs are currently `approved` on GodRender and are eligible for this plan after normal precompile locking:

- `FX2-MOTION-002` — localized_living_flow
- `FX2-LIGHT-001` — practical_light_breath
- `FX2-LIGHT-002` — moving_light_field
- `FX2-ATM-021` — atmospheric_fog
- `FX2-COMP-021` — disocclusion_alpha_feather
- `FX2-SPATIAL-021` — pseudo_depth_field
- `FX2-CAMERA-021` — corridor_push_focus_definition
- `FX2-CAMERA-023` — narrative_camera_travel
- `FX2-CAMERA-024` — rack_focus_heat_pulse
- `FX2-LIGHT-024` — radial_light_shafts
- `FX2-LIGHT-025` — temporal_grade_shift
- `FX2-LIGHT-027` — volumetric_light_shafts
- `FX2-LIGHT-028` — warm_halation_bloom
- `FX2-TRANS-021` — chroma_pigment_transport
- `FX2-TRANS-024` — fog_pigment_travel
- `FX2-TRANS-025` — ghosted_memory_transition
- `FX2-TRANS-026` — glint_to_orb
- `FX2-TRANS-027` — object_portal

Brain recipes used as planning language:

- `RCP-LONG-HOLD`
- `RCP-GHOSTED-OBJECT`
- `RCP-TRANSPARENT-HANDOFF`
- `RCP-MULTIPLANE`
- `RCP-TEMPORAL-PAINTING`
- `RCP-PIGMENT-TRAVEL`
- `RCP-PROTECTED-ENVIRONMENT`

Recipe descriptors guide composition; they do not themselves prove execution.

---

## Batch 01 — The Witness
**Film range:** 0.000–20.000  
**Music:** near-silent lead-in into low establishment.  
**Source:** ancient Observer, cliff and celestial mythology.

### Creative goal
Make the world feel alive before the camera begins moving. The Observer should feel almost carved into the shot while the sky, distant atmosphere and light subtly evolve around him.

### Primary treatment
- `FX2-MOTION-002 localized_living_flow` only in sky/horizon/environment ROIs; never across face, beard or hands.
- `FX2-ATM-021 atmospheric_fog` at very low strength and only when it reads as distant atmosphere rather than literal smoke.
- `FX2-LIGHT-002 moving_light_field` to make existing constellations and celestial light breathe.
- `FX2-LIGHT-025 temporal_grade_shift` extremely restrained, used to evolve night tone rather than recolor the scene.
- `FX2-TRANS-025 ghosted_memory_transition` on selected handoffs between adjacent source extractions so the constellations feel remembered rather than dissolved.
- `FX2-CAMERA-023 narrative_camera_travel` only on selected anchor shots, not every still.

### What changes from Proof 01 / 02
The current proofs largely repeat motion + light + camera. The next B01 treatment must add **atmospheric depth and memory handoffs**, and remove constant camera travel. Several holds should have a locked or nearly locked camera.

### Avoid
- No synthetic star-field generation.
- No cloud-drift unless separately proven.
- No full-frame parallax over the Observer.
- No repeated zoom-in on every shot.

---

## Batch 02 — The Sky Remembers
**Film range:** 20.000–40.960  
**Music:** building into full groove.  
**Source:** Observer beneath luminous mythic constellations; final two anchors introduce the portal and future-city glimpse.

### Creative goal
The constellations should stop feeling like decoration and begin behaving like remembered structure. Light should gather into a threshold.

### Constellation phase
Use the Brain's `RCP-GHOSTED-OBJECT` and `RCP-TRANSPARENT-HANDOFF` logic:

- `FX2-TRANS-025 ghosted_memory_transition`
- `FX2-COMP-021 disocclusion_alpha_feather`
- `FX2-ATM-021 atmospheric_fog`
- `FX2-LIGHT-002 moving_light_field`

Use adjacent source extractions as the secondary image source; do not invent new celestial geometry.

### Ignition phase
B02_07 → B02_08 → B02_09 → B02_10 should become the first major FX event:

- `FX2-TRANS-026 glint_to_orb` for the bright stellar flare becoming a concentrated portal cue.
- `FX2-LIGHT-024 radial_light_shafts` or `FX2-LIGHT-027 volumetric_light_shafts` only where the existing bright source motivates them.
- `FX2-TRANS-027 object_portal` for the actual threshold handoff between the portal-circle state and the first future-city view.
- Camera remains secondary to the light/portal evolution.

The portal should feel like **meaning condensing out of the sky**, not a generic wipe.

---

## Source Video A
**Film range:** 40.960–50.965  
Play `gemini_generated_video_4b4db55f.mp4` at natural speed.

### Treatment
Prefer the source motion itself. Do not add decorative motion just because FX are available. Only continuity grading/light balancing may be considered if the cut into/out of the clip requires it.

---

## Batch 03 — The Threshold
**Film range:** 50.965–69.780  
**Music:** sustained drive.  
**Source:** portal grows into a lens; future city and emissaries become increasingly dominant.

### Creative goal
Move from looking **at** the future to looking **through** the threshold.

### Primary treatment
- `FX2-TRANS-027 object_portal` as the structural transition language.
- `FX2-TRANS-025 ghosted_memory_transition` and `FX2-COMP-021 disocclusion_alpha_feather` for transparent overlap between ancient and future layers.
- `FX2-ATM-021 atmospheric_fog` only around threshold edges / depth boundaries.
- `FX2-LIGHT-025 temporal_grade_shift` to migrate from ancient night into the brighter future palette.
- `FX2-CAMERA-021 corridor_push_focus_definition` for selected shots where a forward move into the city is narratively justified.
- `FX2-LIGHT-002 moving_light_field` to unify the portal edge and city illumination.

### Spatial rule
`FX2-SPATIAL-021 pseudo_depth_field` is approved, but its current implementation is broad. Use it only on environment-dominant/cropped frames where face and identity risk is low. Do not apply it blindly to Observer/emissary close-ups.

---

## Source Video B
**Film range:** 69.780–79.785  
Play `gemini_generated_video_e4937f10.mp4` at natural speed.

### Treatment
Let the actual source motion carry the sequence. No looping, no speed stretching. FX are optional continuity treatment only.

---

## Batch 04 — The Revelation / The City
**Film range:** 79.785–93.360  
**Music:** high drive into a transient break.  
**Source:** city-wide compositions, transit channels, towers, portal rim, emissaries at frame edge.

### Creative goal
The city itself becomes the moving subject. Architecture remains stable while depth, transit flow and light create scale.

### Primary treatment
Use `RCP-MULTIPLANE` logic selectively:

- `FX2-CAMERA-021 corridor_push_focus_definition` for deep-city pushes along real transit/architecture axes.
- `FX2-LIGHT-025 temporal_grade_shift` for gradual city illumination evolution.
- `FX2-LIGHT-002 moving_light_field` for transit/interface light response.
- `FX2-LIGHT-027 volumetric_light_shafts` only from existing portal/horizon/highlight sources.
- `FX2-SPATIAL-021 pseudo_depth_field` only on architecture-dominant wides such as B04_07–B04_09, where protected faces are absent or negligible.
- `FX2-COMP-021 disocclusion_alpha_feather` only when a real foreground/midground layer is deliberately separated.

### 90.740–93.360 break
Strip most FX away. No big transition and no decorative light burst over the transient. Hold architecture or emissary geometry clean and let the musical pivot register.

---

## Batch 05 — The Emissaries / Future Consciousness
**Film range:** 93.360–114.320  
**Music:** high return, then second breath.  
**Source:** close emissary pair, luminous orb/interface motifs, city background.

### Creative goal
This section should feel more intelligent and precise than the city section. The FX should appear to belong to the interfaces, not to the camera.

### Primary treatment
- `FX2-MOTION-002 localized_living_flow` only inside interface/screen/light ROIs.
- `FX2-LIGHT-002 moving_light_field` tied to existing holographic and orb light.
- `FX2-LIGHT-025 temporal_grade_shift` at very low amplitude to keep future-light evolution alive without changing skin/metal identity.
- `FX2-CAMERA-023 narrative_camera_travel` only for tiny reframes or slow push/pull where faces remain geometrically stable.
- `FX2-TRANS-025 ghosted_memory_transition` only for a small number of communication/memory handoffs; avoid visible double-faces.

### Explicitly avoid
The approved visualizer effects `radial_frequency_ring` and `runic_oscilloscope` are not default choices here because their current pixel implementation is centered/full-frame and does not naturally align with the actual orb/interface positions in the B05 crops. Approval in the registry does not make an effect compositionally correct.

### 109.080–114.320 breath
Reduce to almost static emissary light. Prepare the myth-return rather than continuing escalation.

---

## Batch 06 — Return / Myth Completion
**Film range:** 114.320–137.952  
**Music:** late climax then outro decay.  
**Source:** future-city memory, portal, constellations, final solitary Observer.

### Creative goal
The future should stop reading as a destination and start reading as a memory or mythology inside the Observer's sky.

### 114.320–130.020 — motif convergence
- `FX2-TRANS-025 ghosted_memory_transition` to layer future imagery into ancient-sky imagery.
- `FX2-TRANS-024 fog_pigment_travel` for selected city→sky handoffs where a softer non-geometric transition is needed.
- `FX2-TRANS-027 object_portal` for the actual portal-boundary states.
- `FX2-LIGHT-025 temporal_grade_shift` to move future brightness back toward deep-night color.
- `FX2-LIGHT-002 moving_light_field` to connect portal and constellation light.
- `FX2-ATM-021 atmospheric_fog` only as a depth glue layer, not literal smoke.

### 130.020–137.952 — resolution
De-escalate aggressively.

- Remove portal/transition FX after the final handoff.
- Reduce moving light to a minimum.
- No camera motion for the final hold unless a proof demonstrates it is clearly better.
- End on Observer + sky with the feeling that the universe is still present but the active “rendering” has stopped.

The final image should feel calmer than the opening, not larger.

---

## FX deliberately excluded from the current production plan

The Brain remembers these technologies, but they remain outside the immediate compile lane:

- `FX2-ATM-005 cloud_drift` — proof_required
- `FX2-ATM-006 star_field` — proof_required
- `FX2-MOTION-001 depth_parallax` — proof_required
- `FX2-SPATIAL-001 hybrid_25d` — proof_required
- `FX2-SPATIAL-004 streaming_living_parallax` — proof_required
- Historical continuous soft-depth 2.5D / Irish Eyes-Pandora lineage — historically useful, but not currently promoted as a production-callable GodRender effect
- Silver Coin V8 project-local FX algorithms — valuable lineage/reference, but branch-local source inspection is not equivalent to current production registration

These can become separate isolated proof projects later. They are **not blockers** for the Nordic film because the current approved stack already covers portal, memory, atmosphere, light, camera and pseudo-depth language.

---

## Representative proof order before full-film treatment

Do not jump straight from this plan to a 137.952-second compile. Produce six short representative proof packages and review them in story order:

1. **B01 — Breathing Sky**
   - Prove atmosphere + memory handoff + reduced camera usage.
   - Must look materially different from B01 Proof 01/02.

2. **B02 — Portal Ignition**
   - Use constellation-memory handoff → glint/orb → object portal.
   - This is the first proof that should clearly show the new Brain-derived language.

3. **B03 — Threshold Transfer**
   - Prove ancient/future overlap and a controlled push into city space.

4. **B04 — Living City**
   - Prove architecture-dominant pseudo-depth/camera/light on wide frames without topology drift.

5. **B05 — Emissary Interface**
   - Prove that the interfaces can move/light-react while faces remain stable.

6. **B06 — Return to Myth**
   - Prove city-memory → portal → ancient sky → final stillness.

Each proof must keep:
- exact source hashes
- exact FX IDs and params
- ONNX timing range used
- source/target still identities
- current registry gate result
- decoded-frame QC
- human Director acceptance separate from technical PASS

## Director acceptance rule

A technically valid runner result is not enough. Promote a treatment only when the motion reads as **story**, not merely as visible FX.

The intended progression is:

**stillness → remembered sky → threshold → world depth → intelligent light → memory → stillness.**
