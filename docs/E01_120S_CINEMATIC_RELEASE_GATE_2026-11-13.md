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
