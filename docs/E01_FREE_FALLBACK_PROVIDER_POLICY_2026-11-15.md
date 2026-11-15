# Nightfall E01 — second video engine candidate (2026-11-15)

## Candidate: Everypixel Labs LTX 2.3 (Image-to-Video)

Official public evidence as of 2026-11-15:
- https://labs.everypixel.com/video-generate — offers **10 free seconds ONCE** for eligible LTX 2.3 / MiniMax H3 models, no card to sign up. This is a trial only, NOT a recurring 216-second episode budget.
- https://labs.everypixel.com/docs — JSON API POST /v1/video_generate, model `ltx23`, `image_url`, 5-second `duration`, `resolution=720p`, `aspect_ratio=9:16`. Credentials are Client ID and Client Secret over HTTP Basic, if connected in the future. Every accepted queued task can become BILLABLE once the free allowance is depleted. No guaranteed hard-zero-spend API cap was found.
- Official provider docs say trial eligibility and costs are account-specific. **NO Everypixel video requests are authorized now**; new code only prepares a verified original Ember reference + prompt to compare cinematography.

## Production decision and failover rules

- Main Agnes Video 2.5 Flash remains the preferred provider until its output visually passes quality checks.
- Automatic LTX switching is DISABLED: there is no provider-enforced $0 cap and the one-time 10-second offer cannot cover even one original 12-second Agnes shot, let alone all 18 shots.
- `pilot/e01_ltx23_backup_candidate.py` is a safe status/quality experiment planner, not a paid production client.
- Switch eligibility is considered **only** if Agnes explicitly confirms the previous request was NOT accepted (`PAUSED_AGNES_QUEUE_FULL_NOT_ADMITTED`), and only after reviewing unused trial seconds and an enforced $0 spending cap.
- Agnes generic 503/timeout is **ambiguous**: an accepted server task could exist even if the client saw an error. `pending` prevents automatic duplicate motion at another provider.
- No LTX preview goes into E01 final film without a true generated MP4, character-design/cinematic/voice/lipsync review and whole-scene duration reconciliation.
- One-shot quality candidate is 5 seconds, 720p, vertical 9:16; it uses the SHA-locked original Ember image, never a new unapproved reference.
- Existing 14 Kokoro WAV and any Agnes task IDs are preserved in GitHub Actions artifacts. No public YouTube, Facebook, Instagram or TikTok post is enabled.

## Next external owner action (not a request for payment)

To *evaluate* visual quality only, create a free account at https://labs.everypixel.com/video-generate (do NOT add a payment method) and verify the actual LTX 2.3 trial allowance has 5 unused seconds. An API key would eventually require GitHub Secrets `EVERYPIXEL_CLIENT_ID` and `EVERYPIXEL_CLIENT_SECRET` but these are NOT currently needed for this offline plan; do not paste credentials into chat.

Even after signup, do not run the API client on trial credit without independently verifying protection against billing beyond that allowance. The alternate scalable path is an open video model like WanGP/LTX on a genuinely available and allowed free cloud GPU: this was not available on the tested Kaggle or Lightning accounts as of this date.
