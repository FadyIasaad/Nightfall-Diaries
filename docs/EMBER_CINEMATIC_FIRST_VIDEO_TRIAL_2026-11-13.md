# Nightfall Diaries — Ember cinematic reference and first video quality trial

**Date:** 2026-11-13 (Africa/Cairo). **Branch:** `pilot/ember-cinematic-ltx25-20261113`.

This branch prepares ONE controlled quality test using the newly generated Ember
cinematic art instead of the old flat, labeled fox icon. **It does not generate
a complete episode and does not post to YouTube, Facebook, Instagram, or TikTok.**

## Proven failure from previous attempts
- The old original flat PNG was a printed **character card** containing the word Ember.
  Wan2.2 and LTX-2.5 both inherited that 2D style and the title; their prior
  short clips were visually rejected.
- LTX-2.5 official ZeroGPU Space did successfully return a short video on the
  previous PR, with no billed LTX API key, but the source image was unsuitable.
- Kaggle T4 was **not allocated** during the last real Kaggle GPU check;
  starting another Kaggle full-episode job would not be justified by evidence.

## New reference artifact
- New `pilot/assets/ember_cinematic_fullbody_512.webp`, an original
  feature-animation-style image generated in the conversation and derived into
  a compact **512×640** WebP for the video provider's input.
- SHA-256 `c6cfda4f199c13d5fdf6d4e5057026d718787a495aefc29125c06779eb662432`.
- Rich reddish fur and cream chest, one **white-tipped LEFT ear**, turquoise
  scarf carrying **one gold star**, cinematic forest and lighting, no captions.
- The **existing original locked reference stays untouched**; this is a new
  isolated proof source, not a replacement for canon or actor locks.

## Automated first-shot quality gate
- On **the first `opened` event** of this exact pilot PR only,
  with `github.run_attempt == 1`, load the new asset and verify SHA-256,
  22 original story archives, 14-scene E01 screenplay and five locked cast
  profiles. The motion test does not read any YouTube/Meta/TikTok secrets.
- Convert the compact WebP to PNG on the GitHub runner using free ffmpeg.
- Use the **official** `Lightricks/LTX-2.5` Hugging Face ZeroGPU Space,
  `/run`, anonymous `token=None`, diffusion decoder, seed 41,
  576×1024 vertical, **2.0 seconds**. Call the provider **only once** and
  fail closed if the public API schema or free allowance changes.
- The result is archived as a **visually UNAPPROVED** MP4 candidate. Technical
  track inspection is not cinematic proof. An absent quota / failed call
  produces a JSON artifact with the actual error. No retries or paid fallback.
- A GitHub PR `synchronize`, ordinary push, scheduled run or manual rerun
  is **not permitted** to initiate another LTX call.
- No public posting is enabled by this PR or by any green CI result.

## Acceptance checklist before producing full E01
1. Ember maintains the exact same furry CGI identity through motion, including
   one white-tipped left ear, one star, and real quadrupedal locomotion.
2. Scene exhibits believable eye, body and paw acting, physically plausible
   scarf and tail movement, no text/watermarks, no static photo zoom.
3. Video timing and dimensions verified; later release needs true 9:16, 24fps,
   real emotionally expressive Kokoro voice profiles and **actual lip-sync**.
4. The approved E01 is **3–6 minutes**, with continuous 14+ planned scenes and
   original story continuity. Existing `quality_gate.py` currently accepts
   90–180s, and the 279-word screenplay is too short to guarantee a 3–6 min
   film — these remain explicit blockers, not silently changed to fake length.
5. Four existing-platform uploads need authenticated, official API integration
   tests, privacy-mode review, and an approved complete film. Do not rename a
   two-second test as episode one.

## Status
- GitHub pilot source branch: **ready for one free quality trial**.
- First full episode: **not rendered**.
- No paid provider, no account charge, no upload to social media.
