# Nightfall Diaries — Safe Story Validation & Cinematic Proof Planning

The original **22 episode scripts**, two series bibles, episode trackers, character registries and legacy reference images are now versioned in `seasons/`.

## Safe manual actions
- `validate_stories`: read-only validation of 22 scripts, character IDs and episode order without relying on old Git commits.
- `prepare_ember_proof`: validates stories, then exports a **13.5-second shot plan JSON — NOT a video**.
- `check_instagram`: read-only credential/access check.
- `review_publish_config`: verifies secret presence, never logs secret values.

Quality standard: original emotional storytelling with real character acting, coherent motion, consistent identity, cinematic camera, natural voices, lip-sync and sound. We **do not know yet** which cloud video provider will satisfy that standard within the budget. Archived low-resolution PNGs are not approved final references. The earlier primitive Blender and eSpeak modules remain as historical code only; they are not available as GitHub Actions rendering modes.

**There is no approved or generated cinematic MP4 yet. No automated posting is implemented. Public publishing and automatic new series are disabled.**

## Automatic production preparation

Select `prepare_auto_episode` to create a single downloadable pack for all character sheets, voice profiles and cinematic shots of the selected episode. No per-character approval is requested. The full intent and remaining cloud generation blockers are in `AUTOMATION_POLICY.md`. This is preproduction JSON, **not an animated MP4**.
