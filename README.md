# Nightfall Diaries — Cloud Automated Studio Foundation

Original 22 episode scripts and reference assets are preserved. `studio.auto_prepare` prepares the whole cast, voice specifications and shot jobs automatically without asking for each character's approval.

## GitHub Actions controls

- **Daily schedule:** every day at **10:00 AM Africa/Cairo**, with daylight-saving support.
- **`check_setup`:** reports exact missing integration gates.
- **`prepare_auto_episode`:** selects the next unpublished original episode when `episode=auto`, prepares the visual, voice and shot pack and attaches JSON (NOT an MP4).
- **`generate_and_upload` / `generate_only`:** reserved production controls; currently **fail closed with an explanation** because the cinematic rendering/publishing adapters do not exist yet. **Do not confuse button visibility with working video generation.**
- **`validate_stories` / `check_instagram`:** safe verification tools.

The schedule currently **only checks readiness**, and does not create or upload videos. All production switches remain disabled in `studio/production_settings.json`. Full scope and remaining work are in `AUTOMATION_POLICY.md`. No secrets are embedded in repository code.
