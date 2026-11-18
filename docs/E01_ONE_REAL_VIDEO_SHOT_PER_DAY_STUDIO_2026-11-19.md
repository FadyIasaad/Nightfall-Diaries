# Nightfall — first working daily real-AI video studio

**November 19, 2026. This implements a real daily production QUEUE, not a completed film.**

## What is different from 2.5D and failed plans

The code `pilot/e01_free_ai_studio.py` actually calls the official free/public Lightricks LTX-2.3 ZeroGPU Gradio endpoint, which **already produced a genuine 4.042-second animated video for Nightfall E02**. It is not an FFmpeg still-pan, procedural cutout, or fake moving puppet.

The new GitHub workflow:
`.github/workflows/nightfall_e01_free_ai_studio.yml`

- **Daily 10:00 AM Africa/Cairo**: ONE real 4-second shot generation attempt on a public ZeroGPU Space without any paid token or API key. The provider may queue, exhaust its free quota, go offline or change its API; then this run safely reports blocked and attempts no alternative.
- **NOW button:** GitHub Actions → this workflow → `Run workflow` → `generate` (or owner-approved marker push). Only first successful event per Cairo calendar day can spend one anonymous free GPU request.
- **Durable multi-day storage:** the video, 4-frame visual review contact sheet, SHA-256 metadata and cumulative `studio_state.json` are uploaded to an **unpublished draft GitHub Release** `nightfall-s01-e01-real-ai-draft-2026`. No publicly visible release, no social posts and no account-based video API charges.
- **Identity protection:** the approved Ember image hash is checked before requesting video. Scenes featuring only Moss are NOT generated from the Ember image. They are deliberately left pending until a visually acceptable original Moss source exists.
- **No duplicate/trial-loop:** exactly one attempt per Cairo date recorded BEFORE the public model is called. No automatic retries or alternate accounts if ZeroGPU refuses quota.
- **QA:** ffprobe checks actual H.264 video dimensions, 4-second duration and nonzero file. FFmpeg rejects black/frozen intervals; each shot is uniquely named and source-hashed. **This DOES NOT prove a beautiful motion clip, correct character features, or accurate lipsync.** Those require visual/acting review, so the private clip's human approval flag stays false.

## True film status
- 15 scenes × (3 shots × 4 seconds) = 180 seconds target.
- Current certified reviewed complete clips at kickoff: **ZERO**, new queued clips will be counted by the draft release state.
- Existing **180-second Kokoro original soundtrack** is complete and preserved: GitHub run [44404174792](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/44404174792). The original character-specific voice is NOT automatically spoken by LTX. The Studio currently asks LTX for motion only. Therefore natural character speech/phoneme lip sync is **still a blocking quality gate**.
- Existing strict final-film compositor: `pilot/e01_premium_45shot_assembler.py` (PR #79). It requires 45 genuine clip files with separate owner-reviewed SHA sidecars; this queue alone does not activate publication.
- Previous V4 full 2.5D episode and poor-quality Moss shall **never** be reused as fallback. All old social posts are unchanged; don't repeat them.

## The hard $0 feasibility statement
GitHub standard-hosted runners for a PUBLIC repository have no billable Actions minutes. The Hugging Face public ZeroGPU service is freely accessible, but its GPU allowance is rate-limited; a 45-shot project **cannot** be promised complete in a given number of days, let alone generated daily as a new episode. This queue is a best-effort proof of legitimate automated progress at zero provider cost. A new visible episode remains **blocked** until all clips and actual facial acting meet the owner's quality bar.

Reference official docs:
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job
- https://huggingface.co/docs/hub/spaces-zerogpu
- https://huggingface.co/docs/hub/spaces-api-endpoints
- https://cli.github.com/manual/gh_release_create

**Never purchase, upgrade, impersonate a free account, bypass quota, use stolen tokens or run a pay-as-you-go provider.**
