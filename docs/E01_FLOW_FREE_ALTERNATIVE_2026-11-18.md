# Nightfall E01 — $0 Google Flow web alternative (18 November 2026)

## Why this branch exists
The owner's Kaggle account has **only None** in Accelerator. Repeated real Kaggle job #44403130470 was accepted but had no CUDA GPU. Do not request T4 again, claim the account has access, buy credits, or silently replace the rejected E01 film with 2.5D.

## Verified alternative
- Google's official [Flow site](https://labs.google/fx/tools/flow) offers **50 free Flow credits per day** without a Google AI subscription.
- Google's official [credit table](https://support.google.com/flow/answer/16526234) says **Veo 3.1 Lite 720p**, with durations **4, 6 or 8 seconds**, costs **10 Flow credits per generation** for non-Ultra users.
- Google's official [supported-country list](https://support.google.com/flow/answer/16353544) includes **Egypt**.
- Under the most optimistic single-take plan, 15 E01 scenes × (8s + 4s) = 30 generated clips × 10 credits = **300 free credits**, theoretically **at least six daily allowances** (50 credits/day). This is not a delivery date or a guarantee: account eligibility, queue, model result, unexpected multi-output charges, retakes and quality all vary. **Do not enable more than one generated output per request**.
- Because free Flow credits exist inside the Flow website, **there is no confirmed supported free API to call from GitHub Actions** and no legal unattended cloud-only automation proven. Using unapproved private browser endpoints or cookies would be fragile and potentially unsafe. Nothing here claims those credits can be accessed headlessly.

## Production pack added
- Source code: `pilot/e01_free_flow_clip_pack.py`
- Output artifact: `nightfall-e01-google-flow-30shot-promptbook-no-video` containing `e01_30shot_promptbook.md` and `e01_30shot_free_flow_plan.json`.
- All prompts preserve original 15-scene E01 story, Ember's white LEFT ear tip, teal scarf and ONE golden star, Moss no glasses, rich connected forest backgrounds and genuine moving action.
- `Veo 3.1 Lite` can supply genuine video and often native sound, but **it has not been demonstrated to preserve the locked Kokoro voices or synchronize its native animal mouth acting to the downloaded WAV files**. These remain hard review gates.
- The 30 clip (8+4s) budget is **not** the 45 clip (4+4+4s) budget of the current `e01_premium_45shot_assembler.py`; do not pass 30 Flow clips through that 45-clip editor. A separate 30-clip editor must be built only after real Flow clips exist and are approved.
- Final sound master ALREADY exists: `nightfall-E01-180s-complete-original-soundtrack-unpublished`, generated in successful Actions run #44404174792. Full cinematic MP4 is **NOT** yet produced.

## Hard $0 rules
Never submit paid model requests, connect a pay-as-you-go API, purchase credit packs, bypass per-account limits, or submit a request that exceeds the shown free balance. Never automatically post an unapproved video. Daily 10 AM Cairo GitHub QA remains a readiness check only.

## What can happen next
Flow is cloud/browser-based, so no local GPU is necessary. Sign into your normal Google account through official Flow, confirm the free credits appear, and make **one** Frame-to-Video test from the locked cinematic Ember reference with the first 8s prompt. Inspect the result for true moving fur, continuous environment, natural behavior and correct scarf/ear/star. Any full film requires the remaining visually reviewed clips and a verified way to sync the locked voices.

The supplied promptbook is a useful production blueprint but **not** a filmed or scheduled episode.
