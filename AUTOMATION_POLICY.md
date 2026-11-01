# Nightfall Diaries — Automation and Quality Policy

## Automatic target

At 10:00 AM **Africa/Cairo** every day, a GitHub Actions schedule should select the next verified-unpublished episode, generate cinematic character acting, character-specific neural voices, natural lip-sync, audio and captions, and publish to the existing YouTube, Facebook, Instagram and TikTok destinations (draft/inbox where direct publishing is unavailable). The GitHub Actions manual action `generate_and_upload` will provide a one-click button for the same pipeline once verified.

No routine character or episode approvals. The owner approves the creative/quality standard (Ember image approved in chat), and selects a new original series when each approved production cycle finishes. Never choose a new series without owner approval.

## Implementation status — important

- Script restoration, validation, cast and voice *job planning*, next-episode selection, schedule configuration and manual controls are present.
- Cloud image-to-video provider is **NOT connected**. Actual video, neural speech, lip-sync and four-platform publishers are **NOT implemented**.
- Schedule runs as a readiness/standby check, **not a content generator**, until the actual renderer and upload adapters have passed real tests.
- Manual `generate_and_upload` and `generate_only` fail with a clear message rather than inventing completed movies or uploads.
- Flags in `studio/production_settings.json` remain `false`; do not flip them without live verification. The user approved a **still visual reference**, not a proven moving-video result.
- Public publishing is disabled. No posting attempts, episode advancement, content fabrication or duplicate uploads.

## Integration milestones still required

1. Configure/test a cloud renderer with an actual MP4 and stable locked characters. Verify its free quota and API access; do not substitute primitive Blender or moving pictures.
2. Integrate consistent expressive voices, lip-sync and natural effects, and verify cinema-quality output.
3. Test all existing platform accounts individually and ensure durable per-platform receipts for retries/idempotency, before calling an episode PUBLISHED.
4. Enable production gates and schedule publishing only after all tests pass. TikTok direct public posting depends on API review; inbox/draft fallback may require owner action in the app.

References: GitHub Actions now supports `timezone: Africa/Cairo` in scheduled workflows; no hard-coded UTC offset is used.
