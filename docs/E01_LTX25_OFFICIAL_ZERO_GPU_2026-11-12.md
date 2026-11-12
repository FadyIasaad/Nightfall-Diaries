# Alternate video engine evaluation — Official LTX-2.5 ZeroGPU, Ember E01

Date: 2026-11-12. Project: Nightfall Diaries, original E01 of The Last Little Fox.

## Decision: do not repeat the rejected PR #36 renderer

The public Wan2.2 ZeroGPU run #43306872905 generated one moving but **visually rejected** shot:
flat 2D-looking fox, broken letters, weak character identity, no voice/lip-sync, 720×832 at 16 fps.
It was **NOT** a cinematic E01. The Kaggle CUDA test previously reported **no GPU
allocated**, so simply trying Wan on Kaggle again does not solve visual fidelity.

## Better candidate: official Lightricks/LTX-2.5

- Model weights and official demo: https://huggingface.co/Lightricks/LTX-2.5
  and https://huggingface.co/spaces/Lightricks/LTX-2.5
- The **official** ZeroGPU Space is deployed on Hugging Face, supports image-to-video with
  an actual input image, has a two-stage distilled denoiser, a higher-quality diffusion
  decoder, and can output video with audio. We do not claim it matches Flow until tested.
- LTX-2.5 local inference has substantially higher GPU/RAM requirements than Kaggle
  T4×2 alone can confidently satisfy; use the official shared ZeroGPU demo instead.
- Hugging Face ZeroGPU docs: https://huggingface.co/docs/hub/spaces-zerogpu.
  Unauthenticated free quota is limited and can run out; **xlarge uses 2× quota**.
  There is no automatic paid GPU upgrade or credit purchase in this project.
- We deliberately call the Space **without HF_TOKEN** so paid subscription credits
  cannot be consumed by accident. The free anonymous queue may reject the job.
- Open model weights still have an applicable model license; commercial/public
  publication requires a separate license check and character continuity approval.

## Exactly one conservative test (on THIS PR's first 'opened' event)

1. Source: SHA-256 locked original `seasons/S01_the_last_little_fox/characters/s01_ember/cloud_reference.png`.
2. Fixed first E01 action: Ember runs three natural steps in the burning forest, turns
   anxiously toward a falling ember-lit branch; show expressive eyes, fur, scarf motion,
   volumetric light, a real tracking camera; no visible words.
3. Official Gradio Space `Lightricks/LTX-2.5`, endpoint `/run`; inspect public endpoint
   schema and fail closed before inference if the expected API no longer matches.
4. Requested **576×1024**, exact **9:16**, **2.0s**, seed 41, diffusion decoder,
   prompt enhancement off, no random seed, source image-to-video.
5. **At most one request per run**, no programmatic retry; only on initial PR
   `opened` (never from ordinary PR revisions, push, schedule or new episodes).
   A manual GitHub re-run can send another request; avoid re-running without consent.
6. Validate H.264/video properties with free `ffprobe`, archive only as
   `nightfall-ltx25-ember-unapproved-mp4`. If quota, model startup, image
   conditioning or API schema fails, archive the reason instead.
7. Human compare with approved original Ember and the Flow-quality reference:
   realistic fur, left white ear tip, *one* gold star on teal scarf, natural eye and
   body motion, coherent geography, no warped text, no flicker.

## Boundaries

- This is **not** 3–6 minutes, and is NOT an approved voice/lip-sync proof.
- The E01 14-scene expanded screenplay and 22 archived episodes stay untouched.
- All original visual and Kokoro voice SHA/profile locks stay intact.
- `production_enabled=false`, `cinematic_video_approved=false`, social publishing disabled.
- No Twitter/Instagram/TikTok/YouTube uploads, no local PC use, no paid endpoints.
- If free space fails to deliver convincing cinema, do NOT render a full episode using
  the same unproven setup. Do not fabricate a fallback slideshow.

## Review

Check PR CI logs and the `nightfall-ltx25-ember-report` artifact. A green
GitHub Actions check proves code and continuity validation only. Rendering and
visual quality must be judged separately, and full automation cannot be
guaranteed free under the small daily quota.
