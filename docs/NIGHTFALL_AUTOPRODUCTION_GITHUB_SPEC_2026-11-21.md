# Nightfall Diaries — Actual GitHub Production Implementation & Status

**Revision:** 2026-11-21  
**Mode:** `AUTO_BEST_WITH_HONEST_QUALITY_GATES`  
**User constraints:** 3–6 minute stories, 22 original episodes (The Last Little Fox ×12; The Boy Who Forgot Tomorrow ×10), high-end stylized cinematic moving characters, strong complete environments, consistent locked characters and voices, meaningful camera/action, correct speaking and lip-sync, fully online, automated daily at 10AM Cairo, Telegram events, **$0** and no approval wait for each shot.

## 1. Delivery truth, not another fake green workflow
The owner explicitly rejected:
- Rendered 2.5D cutout/slideshow Episode 1 V4, even though its MP4 duration was 180s.
- Text-to-video E01-like samples with fake social UI and captions.
- E01 first raw AI shot with poor movement and incorrect green forest (SHA `269dcfac81b2e294b25219e88f6ecc93139e50a74b3e733389d17ee41bb6b1a4`).
- E01 next 4s revision with genuine movement but wrong fire background and fox exiting frame (SHA `78832db77d0a5ff23cdfa715d240e499804db6359c61471226fdf40c5512c71a`).

**Current real deliverables:** the exact original **180s neural voice+atmospheric soundtrack** from successful [GitHub run #44404174792](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/44404174792), 15-scene canonical film outline, two unapproved ~4s AI sample MP4s held in GitHub's owner-only DRAFT release, and a final cut editor that refuses missing shots. **There is not a new accepted complete visual episode, not a verified animal-lip-sync result, and no authorized new public post.**

## 2. The real workflow

| Actual component | File | Current truth |
|---|---|---|
| Real free video shot queue | `pilot/e01_free_ai_studio.py` | Calls public anonymous Lightricks LTX-2.3 ZeroGPU, one genuine 4-second image-to-video generation attempt per Cairo day (unless user explicitly authorized a single-use exception) |
| Daily cloud workflow | `.github/workflows/nightfall_e01_free_ai_studio.yml` | GitHub Actions schedule 10AM Africa/Cairo, may execute late; no PC |
| Canonical screenplay | `seasons/S01_the_last_little_fox/revised_screenplays/E01_2026-11-18.json` | 15 scenes × 3 shots × 4s = 180s *planned* |
| Locked Ember source | `assets/cinematic_refs/ember_approved_candidate_2026-11-13.webp` | SHA-verified reference, although green forest reference is unsuitable for the fire opening |
| Free Kokoro soundtrack | `pilot/e01_cinematic_soundtrack.py` | Completed full 180s mix and SHA manifest, GitHub Actions artifact saved |
| Automatic measurable QA | `pilot/e01_auto_quality.py` | Ranks *actual MP4s* by motion, detail, black-screen and clipping proxies; does not claim lip-sync or semantic correctness |
| Telegram progress | `pilot/e01_studio_telegram.py` | Sends stage-start and honest result messages via Bot API, provided existing GitHub secrets work |
| Film compositor | `pilot/e01_premium_45shot_assembler.py` | Strictly requires all 45 actual unique approved moving clips, no frozen/black gaps and original 180s soundtrack; does NOT fake missing clips |
| Permanent auto-best policy | `docs/NIGHTFALL_AUTO_BEST_RULES_SHORT.md` | No manual approvals per candidate; fail safe on missing objective/semantic validation |

## 3. Actual errors fixed on 2026-11-21
GitHub scheduled real-studio runs [Nov 19 #44571294365](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/44571294365), [Nov 20 #44773773395](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/44773773395), [Nov 21 #44920740036](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/44920740036) all failed **BEFORE VIDEO GENERATION**, because the SHA-locked rejection for original clip `scene_01_shot_01` was compared to a newer revision's SHA, then incorrectly raised `UNMATCHED_VIDEO_REJECTION_HASH`. The fix matches **both clip ID and exact media SHA**, skips irrelevant older-version rejections, and never silently loses the underlying draft video. Existing v2 was separately rejected for wrong background/framing and recorded by its true SHA. Regression tests cover mixed-version review records and duplicate handling.

## 4. Auto-best candidate selection — what is and isn't proved
The CPU `e01_auto_quality.py` derives four real frames per MP4 with FFmpeg and calculates:
- Changed-pixel temporal motion proxy;
- Detail/sharpness proxy;
- Near-black frame fraction;
- Warm/orange subject proximity to frame edge (very rough framing proxy);
- Weighted score from 0 to 100 and machine failure flags.

It can reject frozen/very weak/black/overcropped shots and keep the **highest-scoring candidate actually generated** for a shot. It does NOT reliably check that the forest is burning, Ember's **left** ear tip/scarf's **one** gold star remain perfect, there is no synthetic text, or speech matches phonemes. **A technical score, even 100, must never become `public_approved=true` by itself.** That would merely automate the previous poor-quality mistakes. The candidate model is quota-limited, so the desired 3 visual and 4 speaking generations may require many days or may not be possible. No quota bypass or paid upgrade.

### Why no fixed production deadline
- Genuine cloud video generators require compute; GitHub standard public runners supply CPU, not a guaranteed free GPU.
- Kaggle owner account's Accelerator dropdown showed **None**; repeated kernel allocated 0 CUDA devices.
- Anonymous Hugging Face ZeroGPU is **shared and limited**. Even one short candidate may be rejected on quota/provider changes.
- Google Flow's free web credits have no established supported, unattended free GitHub API. Do not claim automatic website generation from GitHub.
- Correct animal audio-driven facial animation has **not** been technically demonstrated on this repo's free backend.

## 5. Operational state, durability and idempotence
A *draft, unpublished* GitHub release `nightfall-s01-e01-real-ai-draft-2026` contains each real rendered video as `scene_XX_shot_YY_revision_N.mp4`, four-frame review contact sheet, SHA evidence and cumulative `studio_state.json`. On every job:
1. Restore state and verify episode/canon/0 paid requests/draft-only conditions.
2. Reconcile previous rejections by media SHA **without failing for a different revision**.
3. Select next incomplete, supported character shot (Moss-only scenes cannot reuse Ember image).
4. Check date lock and one free attempt; save attempt marker **before** requesting AI video.
5. Try one legitimate public anonymous GPU request, never retry on quota failure in same job.
6. Validate actual MP4 and auto-score measured motion/texture.
7. Retain real candidate with hash and auto-best rank, or reject and enqueue a later retry.
8. Store actual outcome, never turn green CI/test into a completed episode.
9. Send Telegram start and actual final status, never claim publication.

Audio is already assembled, but animation lip-sync, 45 approved shots and final public platforms are **blocked**. The next production run must prove at least one proper forest/fire shot and then a natural speaking shot before any public upload.

## 6. Telegram notifications — honest events
Secrets in GitHub Actions: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
Use the official free `sendMessage` Bot API with no billing and no pasted keys.

- At **start**: named series, E01, production check started, link to real GitHub run.
- At **end**: explicit one of `AUTO_SHORTLISTED_TECHNICAL_MOTION_NOT_SEMANTICALLY_APPROVED`, `AUTO_REJECTED_WEAK_MOTION_OR_FRAMING`, `BLOCKED_FREE_ZEROGPU_QUOTA_NEXT_DAY`, `PROVIDER_OR_MEDIA_FAILURE_NO_FALLBACK`, or missing reference/credentials.
- Include current raw candidate count, selected technical candidates and limited score, if available.
- At real future milestones: scene fully verified, actual 180s MP4 completion, platform-specific confirmed public publication. Never invent/send these before events happen.
- If secrets missing or Telegram cannot deliver, log `TELEGRAM_SECRETS_NOT_CONFIGURED` or a redacted send failure. **A green GitHub workflow is not a Telegram delivery receipt.**

## 7. Release gates and autonomy
The owner authorized choosing the best **without manual shot-by-shot approval**. Therefore routine technical selection and further free-eligible shots should proceed without interrupting them. However, public release remains **disabled until objective evidence verifies all necessary qualities**:
- All 45 unique clips with consistent character and environmental continuity;
- Correct full 180-second video and soundtrack without black/frozen gaps;
- Validated original Kokoro speech timing and natural animal mouth movements;
- Real visual/semantic evidence that the scenery matches the story and no fake captions/UI;
- Official platform identity/permissions/destination-specific visibility, and idempotent upload receipts.
When automated tools cannot verify any gate, do not claim it passed; retain the film in an unpublished draft. A user instruction to auto-select does **not** establish that broken animation should be publicly uploaded.

## 8. Instructions to the next execution agent / contributor
- Do not propose a new "blueprint" as if it is finished production.
- Read `studio_state.json` in the private draft and the last real GitHub Actions run; do not infer progress from green jobs.
- Fix real errors, run offline tests, commit to a branch, merge only tested changes, and trigger one legitimate free inference when daily quota policy permits.
- Do not modify locked original stories or the voice/character registry merely to make tests pass.
- Never produce 180 seconds by repeating a four-second clip, stretching images, primitive mouth-flap sprites or cutout puppets.
- Do not activate public YouTube/Facebook/Instagram/TikTok posting from mock approval or incomplete render.
- Keep the production queue persistent at 10 AM Cairo and notify on Telegram only with verifiable status.
- If the free provider is unavailable, report it precisely; do not charge money, invent video or promise a completion time.
- Keep this document updated with exact run IDs, produced clip SHA and explicit remaining blockers.

## 9. Release checklist
- [x] Original E01 revised 15-scene screenplay
- [x] Original three-minute Kokoro soundtrack
- [x] A source-locked real 4-second video model request has worked previously
- [x] Rejected raw clips preserved for evidence
- [x] Multi-version SHA collision bug fixed in this branch
- [x] Automated **technical** candidate ranking implemented
- [x] Telegram start/result integration written
- [ ] Confirm connected Telegram secrets and successful real notification
- [ ] Obtain consistent rich fire-environment keyframe for E01 from the approved visual design
- [ ] Generate enough *approved* real moving clips (not achieved)
- [ ] Demonstrate actual natural fox-mouth lip-sync (not achieved)
- [ ] Assemble the full approved 180-second cinematic MP4 (not achieved)
- [ ] Independently verify official social publishing on requested destinations (not achieved)

**Truthful stage:** `PARTIAL_E01_PRODUCTION_AUDIO_DONE_VIDEO_MISSING`. The GitHub queue can attempt free genuine clips but is not a promise of a finished daily premium movie.
