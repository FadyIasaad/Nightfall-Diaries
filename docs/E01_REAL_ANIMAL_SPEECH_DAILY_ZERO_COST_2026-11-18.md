# First episode reboot: REAL speaking Ember and daily 10 AM Cairo checks

**Date:** 18 Nov 2026. This is a first-episode *technical quality gate*, not a completed episode and not a publishing activation.

## What the actual code does

- Tests E01 (*The Night the Forest Burned*) from the original screenplay with **the unchanged SHA-locked Ember reference**.
- Renders the original in-script line "Moss? Can anyone hear me?" in the original `am_puck` Kokoro voice using free GitHub CPU.
- Tries one **image+audio-driven** talking clip via `henrybit/SadTalker-Demo` official public ZeroGPU runtime, only after checking it is still running ZeroGPU and no billable API credentials exist.
- **Caveat:** SadTalker was made for human faces; the source is a fox, so it can fail on face detection or move the muzzle unnaturally. Even a valid MP4 is **NOT** evidence of a good animal talking animation.
- Tests generated MP4, audio stream, duration, and rejects black gaps / full freezes. Actual original Ember identity, acting, lip-sync accuracy, consistent backgrounds and cinematic quality need human review.
- No old 2.5D, talking card, cutout, zoom, image slideshow, fabricated dialogue, paid inference or social publishing fallback.

## Daily schedule and test controls

Workflow: `.github/workflows/nightfall_e01_daily_real_speaking.yml`

- Daily at **10:00 Africa/Cairo**, runs a readiness/identity check on public GitHub CPU, **without spending ZeroGPU quota**. GitHub scheduled triggers are best-effort and may run later than the nominal time.
- Both PR checks and daily schedules run **preflight only**; they never consume free GPU quota. To try a single free 2–5 second talking scene, manually dispatch the workflow with `mode=generate`. There are no automatic GPU retries.
- After merge, a manual GitHub Actions dispatch with `mode=generate` permits one anonymous public ZeroGPU call if the provider is still free; **no paid key is passed**.
- `report.json`, original Kokoro WAV and actual generated sample (if any) are archived as a review artifact; failures are real blockers rather than fake output.
- The daily run does NOT automatically publish or generate an entire episode until voice/mouth/visual proof and capacity are independently verified.

## Why the 180-second episode is not yet achievable as a guaranteed $0 daily film

Hugging Face publishes a small free ZeroGPU GPU-minute allowance. SadTalker's public model itself uses short GPU reservations and is human-face-centric. The earlier LTX test preserved Ember only imperfectly. Producing dozens of 4–6 second coherent full-scene videos plus animal dialogue, quality reshoots and final audio consistently is **not demonstrated** within the available daily free allowance.

No recurring billing, purchase, account upgrade, personal PC, privately hosted GPU, old slideshow renderer or low-quality fake episode is authorized. Existing E01 V4 social posts are unchanged. New E01 review is distinct, unpublished, and all global quality/public-release flags remain false.

## Next milestone after this technical test

If this fox-speaking sample genuinely looks natural and preserves Ember's ear/scarf/star, try a **single combined forest + character + dialogue** shot with authentic motion and zero synthetic UI. If it fails, investigate a genuine animal-capable audio-driven model with verified free entitlement before attempting further episode production. Do not choose a paid DashScope-backed model or pretend a human talking face is good fox acting.

## 18 Nov 2026 failed test: actual verified cause

GitHub run `44195870986`, job `134437039229` reached the speaking inference step after successfully generating Ember's 1.85-second Kokoro WAV. The official public ZeroGPU endpoint returned **`AppError: You have exceeded your ZeroGPU runs limit`**. No video was generated; no animal lip-sync proof exists. The saved artifact contains the report and WAV, not an MP4.

**Fix:** Quota refusal is now classified as `BLOCKED_FREE_ZEROGPU_QUOTA`, with a GitHub warning and explicit absence-of-video report rather than misleading code failure. Unrelated provider errors still fail the job. Only an explicit manual dispatch may attempt one GPU call; scheduled 10 AM Cairo and PR runs use fast, GPU-free preflight. Do not add a HF token or paid service automatically. A green readiness run does **not** mean a video was generated, and no public uploads are enabled.
