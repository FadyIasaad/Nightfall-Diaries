# Nightfall E01 — V4 cinematic art upgrade (17 Nov 2026)

## Implemented
The existing V1/V2/V3 and the earlier V4 clean-shell review remain untouched. This branch adds a separate CPU-only candidate (pilot/e01_v4_cinematic.py) with an isolated checkpoint and workflow.

### Art direction
- **Ember:** original source SHA-locked cutout with white left ear tip, teal scarf and one gold star; no source alteration.
- **Moss:** V3 independently articulated character with subtle contrast/sharpness integration and better duo/solo scale. **It does NOT yet match Ember's reference-illustration detail; true parity needs a properly licensed and rigged premium Moss reference.**
- **Story world:** all 14 original scenes receive multi-scale texture, scene-specific fire/cyan color lighting, atmosphere, smoky haze, geology and foreground branches.
- **Camera:** 14 distinct editorial framings for discovery, peril, rescue and mystery; improved grounded shadows and gaze space.
- **Magic feather:** slim blue feather with fine barbs, environmental glow and natural motion; no large blue sticker.
- **Subtitles:** subtle lower gradient, outlined readable text and small speaker label instead of large game-like card.
- **Motion:** Ember articulated parts + Moss head/feet + drifting embers; no static slideshow substitution.

## Limits
2.5D CPU animation, not generated feature-film 3D, and amplitude-timed mouth movement rather than verified phoneme lip sync. Automated tests cannot certify cinematic-quality art. Source images from external generative tools are only candidates until their bytes, rights and rigs are approved and committed safely.

## Run
- Workflow: .github/workflows/nightfall_e01_v4_cinematic.yml
- PR event: safe 1-scene sample for tests, no upload.
- Manual on main: sample or full.
- Main marker .github/nightfall_e01_v4_cinematic_start.txt: full 180s episode.
- Full artifact nightfall-e01-v4-cinematic-art-unpublished contains H.264/AAC MP4, scene stills, storyboard and QA JSON.
- 14 original scenes and Kokoro WAVs are preserved.
- No public posting or paid AI calls.

## Acceptance gates
1. CI passes with Pillow, OpenCV and NumPy installed in the dedicated art job.
2. Sample shows real articulated body movement, audible original voice and no black gaps.
3. All 14 backgrounds are distinct, feather stays clear of eyes, captions legible.
4. Moss and Ember quality genuinely match after **human** comparison; currently not established.
5. Whole 180-second film passes technical timing and cinematic subjective review.
6. Only later, after verified platform eligibility, consider public posting; no posting in this workflow.
