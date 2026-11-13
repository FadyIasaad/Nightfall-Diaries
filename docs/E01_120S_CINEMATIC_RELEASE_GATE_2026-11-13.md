# Nightfall Diaries — First episode cinematic proof and 120-second release floor
Date: 2026-11-13 | Episode: S01_the_last_little_fox_E01

## Unambiguous owner requirement

The user explicitly requires **the first episode to be at least 2 minutes**.
Target **150 seconds (2:30)**, acceptable final window **120–180 seconds**.
The 14-scene original expanded E01 screenplay already targets 150 seconds.
Neither 2-second LTX trials nor 3-second sprite/GIF previews are full episodes.
Never lengthen a still image, loop a tiny test, or call technical interpolation
a finished 120-second original animated film.

## Implemented in this branch

- Save the new cinematic 3D Ember candidate at
  `assets/cinematic_refs/ember_approved_candidate_2026-11-13.webp`.
  Keep the original 22 scripts and all existing locked character sources untouched.
- Test ONE authentic LTX-2.5 image-to-video clip from the new source in a PR-only
  experiment. Tokenless public ZeroGPU only, never any paid endpoints.
  Output is always an **UNAPPROVED CANDIDATE**, not a first episode.
- Update `studio/quality_gate.py` so any full MP4 shorter than **120 seconds**
  fails validation. Upper ceiling remains 180 seconds. H.264, AAC and 9:16
  video-track checks remain mandatory.
- Add offline tests proving 119.99s cannot pass and 120/150/180s can
  technically pass (visual quality, motion and lip-sync still separately
  require real review).
- Readiness report now explicitly states min 120s and 150s E01 target.
- Keep `production_enabled`, `cinematic_video_approved`,
  `voice_lipsync_verified`, all platform flags and
  `publishing_implemented` **FALSE**.

## Evidence versus what is NOT ready

**Known:** the first E01 has 14 scripted scenes and 279 spoken words. The
old flat Ember references caused rejected cinematic results. A new cinematic
reference has been prepared and awaits actual I2V visual QA. The old owner's
Kaggle GPU notebook check did NOT allocate CUDA; the official LTX-2.5
ZeroGPU Space generated just one short sample on the old reference.
The current Runway connected free workspace exposes no video generation
models. Thus no demonstrated **free** runtime exists today to produce
14 coherent cinematic multi-character scenes totaling 150 seconds with
Kokoro voices and accurate viseme/lip synchronization, suitable for
release across YouTube/FB/Instagram/TikTok.

**Not done:** no 150s edited film, no locked voice performance and lip-sync
of all 14 scenes, no music/SFX final mix, no human quality approval,
no official platform upload validation, **no public upload**.
A PR green check does NOT change those facts.

## Release stop conditions — all must pass

1. Generate unique credible 3D cinematic motion matching the new approved
   Ember appearance across all 14 distinct scenes; no still/slideshow
   substitution or duplicate loops.
2. Sync dialogue to each visible character (Kokoro voice locks), SFX,
   captions, soundtrack and 9:16 correct.
3. Technical `ffprobe` confirms complete MP4 duration **120–180s**,
   H.264 720x1280+ 9:16, AAC; scene order and original story verified.
4. Human review verifies narrative integrity, natural acting, no morphing,
   no garbled on-screen text, and true mouth-to-voice sync.
5. Destination account official API + publication authorization validated
   before attempting to post; no assumption that a secret is sufficient.
6. Provider must have a verified zero-billing guarantee and enough remaining
   legitimate GPU quota. No paid API, auto-upgrade or bypass of free quotas.

The PR is an isolated investigation, not a release approval. Keep main
and its existing schedules unchanged until the above has real evidence.


## Actual 150-second generation and official account identity verification attempt

This one-time owner-requested experiment is activated **only** when this PR's
last Git commit subject matches `[nightfall-E01-150s-run-once]`. The
GitHub Actions job runs on a PR `synchronize` event, `run_attempt=1`.
Regular pushes, scheduled runs, reruns and later PR edits are disallowed.
No paid account key is passed to Hugging Face; this is an anonymous ZeroGPU
queue user limited by shared daily GPU quota.

### Actual film proof implementation

`pilot/e01_full_run.py` requests **14 DISTINCT LTX-2.5
image-to-video generations** from all 14 original E01 screenplay directions
with budgets `[13,11,11,12,10,10,10,11,11,8,10,12,10,11]` seconds —
total **150 seconds**. All 14 requests are unique. Clips must be real
model-generated motion: no loops, duplicate stills, stop-frame padding,
synthetic slowdown or other fake length extensions.

The same code requests the locked Kokoro voice for each speaker and merges
it with that scene's real generated motion. It refuses to stretch motion
to audio or upload output when media is missing. Partial WAV and MP4
progress is archived if the free provider returns quota or runtime errors.
It produces a complete unapproved MP4 only if all scenes are present and
`studio.quality_gate.check_media(..., mode="full")` verifies H.264,
AAC, 9:16 720×1280+ and **120–180s** duration.

### Official publisher verification implementation

`pilot/official_platform_preflight.py` checks configured credentials
on official APIs with read-only identity calls:

- YouTube: OAuth refresh (token POST) and `channels.list(mine=true)` GET.
- Facebook: Page-token `/me?fields=id,name` GET.
- Instagram: account-id and account-type Graph GET.
- TikTok: `/v2/user/info/?fields=open_id,display_name` GET.

Results distinguish absent credentials, revoked token, account mismatch,
HTTP 403/scope rejection and successful account-identity lookup; all IDs
are redacted. No video upload session is initialized. In particular,
**identity success is NOT proof of video publishing permission**.
True private/draft upload is blocked unless a complete approved 120–180s
cinematic E01 exists. No public videos, drafts, or reels are uploaded
by this PR, because facial lip-sync and owner visual QA are still missing.

### Expected capability limits

Official Hugging Face ZeroGPU documentation currently gives anonymous
access around 2 GPU minutes daily, with the xlarge shared GPU charging
2× quota. Even though LTX-2.5 can make short shots, this has **not**
been shown to sustain 14 distinct 8–13-second shots for E01 at no cost.
If it stops early, the result must explicitly report how many scenes and
seconds were truly produced and whether any Kokoro WAV was completed.

**No credit usage, paid API, public uploads, or false episode-completion
claims are permitted.** Keep this as a draft PR until actual output,
Kokoro dialogue performance and character-mouth lip sync pass review.

Official references:
- https://huggingface.co/docs/hub/spaces-zerogpu
- https://huggingface.co/spaces/Lightricks/LTX-2.5
- https://developers.google.com/youtube/v3/docs/channels/list
- https://developers.tiktok.com/docs/en/tiktok-api-v2-get-user-info


## 2026-11-13: Single authorized full production and account-auth attempt

All **101 offline tests** and the account-check safety tests passed in [CI #43336896632](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/43336896632). This commit is a **one-time authorized full-length generation attempt** using the real head SHA (not GitHub's synthetic PR merge commit), followed by read-only official platform-account checks. A green workflow is never proof of film completion: read the exported evidence JSON. Never repeat inference on a rerun or activate public uploads.


## Actual official I2V limit and first full-run evidence

[GitHub Actions #43337014270](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/43337014270)
ran the real E01 generation path (not merely offline tests). It generated
the **original Kokoro narrator's first WAV**, 11.7 seconds, but the official
LTX-2.5 Space rejected the first 13-second scene request before generating
any motion: `Value 13.0 is greater than maximum value 5.0.`
That proves the deployed public Space enforces **5 seconds per inference**.
The workflow's green conclusion reflected `continue-on-error`, NOT
successful episode rendering. The evidence JSON correctly reported
`BLOCKED_BEFORE_FULL_EPISODE_COMPLETION`, 0 rendered scenes, 0 real video
seconds, 1 Kokoro WAV and no posts. Do not mistake successful GitHub
execution for a completed film.

The actual official read-only identity tests in the same run returned:
- YouTube: `HTTP 403` on channel `mine=true` identity query. OAuth secrets
  were present; the read scope/account cannot be declared verified.
- Facebook: page-token identity GET succeeded (publish scope still unknown).
- Instagram: `HTTP 400` on account identity GET; not verified.
- TikTok: `TIKTOK_ACCESS_TOKEN` absent from Actions Secrets.
- None were sent media. No media-upload API response is available yet.

**Revised technical strategy for next single authorized run:** split the
original 14 scene times into **36 unique sub-shots of 2–5 seconds**, with
a separate public-LTX inference for EACH sub-shot, and each subsequent
part conditioned on the true last video frame from its immediately preceding
part. Audio is synthesized once per original scene using its locked Kokoro
voice, and mixed only against that scene's real generated footage. No
clip looping, slideshow or artificial length extension. Target total
is still **150 seconds**, but no claim that the current anonymous ZeroGPU
quota can support 36 GPU requests. Abort at first genuine provider failure,
report actual generated seconds and keep all partial media in artifacts.
This is a capability test, **not** a production/publication authorization.


## Second authorized real 150-second attempt: 36 unique sub-shots

Commit subject `[nightfall-E01-150s-run-once]` authorizes the redesigned
single PR synchronization run, only once (`GITHUB_RUN_ATTEMPT=1`).
[CI #43337707780](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/43337707780)
passed all offline tests. This is a genuine attempt at creating **36 different
2–5-second motion clips** (aggregating to 150 seconds across the original
14 different scripted scenes), with locked Kokoro speech and sequential
last-frame reference continuity. Shared provider quota may still block
the run before the full film; the JSON and media artifacts will record
exactly how many seconds actually emerged. No paid API or public post.
