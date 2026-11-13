# Nightfall Diaries — publish immediately on E01 completion, not at any set time

**Implementation:** `pilot/e01_completion_publish.py` and the `Nightfall - One Click Story` workflow.

## Distinguish rendering quota checks from the publication trigger

The OWNER asked to make the completed episode available on **YouTube, Facebook, Instagram and TikTok immediately when it is finished**, without any chosen publication time. The publisher is therefore an **on-completion step in the SAME GitHub Actions job as the 36-shot film assembler**. It does not read an upload date, queue a publication clock or wait for the next 10 AM trigger after film assembly.

**Rendering itself is not continuously runnable at no cost.** A single registered Free Hugging Face account has a daily GPU budget, and ZeroGPU needs a quota reset before more genuine clips can be generated. Because GitHub Actions runners are finite and cannot wait indefinitely, the existing 10:00/10:17 Africa/Cairo runs are still **only the mechanism for resuming unfinished GPU work**, not a publishing schedule. Removing these checks without adding a permitted persistent free executor would make the 150-second episode stop when the quota runs out. We must not suggest that all 36 shots can be generated in a single free invocation.

## Four full-length original-video delivery routes

All four are prepared as official-API calls but are **not authorized to send anything** until the real completed episode is approved:

- **YouTube:** if an authenticated private E01 review video already exists, request changing the *same video ID* to public (never upload a duplicate). Otherwise, upload the approved finished MP4 with visibility `public`. Verify the exact expected channel and OAuth rights. A previously ambiguous private transfer with no receipt is a hard stop.
- **Facebook Page:** publish the original approximately 150-second MP4 via the official **Page Videos** upload API using the verified expected Page ID. Do **not** send the full episode via the legacy limited-duration `/video_reels` endpoint, and do not truncate it to fit a Reel.
- **Instagram:** publish one Reel using a public HTTPS media URL via Graph `/media` and `/media_publish`, after validating the professional-account identity and access. Hosting the complete approved video as a public GitHub release asset only happens after the film and publication gates all succeed.
- **TikTok:** attempt Direct Post only with the user's valid `video.publish` grant, audited TikTok app, explicitly authorized creator posting, eligible public privacy selection, and duration permitted by the official `creator_info/query` response. The unaudited-app or `video.upload` **Inbox** transfer is *not* considered a public post and is never labelled one. No account policy bypass, borrowed tokens or hidden charges.

A video upload API response may only mean **accepted or processing**. The report tracks `public_confirmed=false` until each platform independently confirms public visibility; mere API acceptance is not proof that a post is publicly available.

## Mandatory media and publication gates

Do NOT attempt public upload unless *all* are independently verified:

1. 36 distinct original generated MP4 sub-shots with matching SHA-256 checkpoints and source prompt/character continuity.
2. All 14 original scenes and 14 Kokoro voice WAVs, one final H.264/AAC portrait 9:16 MP4 lasting **120–180 real seconds**, matching `assembled_video_sha256`.
3. **Actual** cinematic character acting/identity reviewed, and the **real dialogue-to-mouth lip synchronization** verified. Adding an audio track is not lip sync. A green GitHub Actions check does not satisfy this.
4. Production settings `production_enabled`, `renderer_verified`, `cinematic_video_approved`, `voice_lipsync_verified`, `publishing_implemented`, each platform's `*_verified` remain false until genuine evidence exists. `config.json.public_publish_enabled` also must be verified enabled after approval.
5. Each of the four target official accounts, page/channel IDs, tokens/scopes, and TikTok app auditing/creator consent are verified before submitting any media. A 403/400 identity failure is a BLOCKER, not publish success.

The new publisher has **zero uploads** while any gate above is missing. That is the current reality: only **2/36 authentic shots (~10.08 seconds)** were proven on the last connected run. YouTube previously failed OAuth channel read 403, Instagram Graph identity 400, TikTok access token was missing; Facebook identity GET worked but not the publication scope. No full E01, approved mouth sync, four-platform posting or public URLs exist yet.

## Duplicate-safe, immediate per-destination delivery

Immediately after final assembly passes, the same job invokes the completion publisher. The publisher persists a **remote GitHub main-branch `published/<episode>.json` receipt with phase `initiated` BEFORE starting each external upload**, then saves the returned ID/status. This guard survives Actions cache eviction or runner crashes and prevents accidental second public posts after uncertain API responses. It independently tracks YouTube, Facebook, Instagram and TikTok so one failed destination is not falsely reported as published everywhere. Ambiguous transfers require account inspection before any reattempt.

All steps have a read-only progress report in Actions. Neither a fixed time nor a manual video upload is required **for publishing once complete and approved**. The GitHub free quota checks for unfinished rendering are a separate limitation and remain, as described above.

## Official API docs

- https://developers.google.com/youtube/v3/docs/videos/insert
- https://developers.facebook.com/docs/video-api/
- https://developers.facebook.com/docs/instagram-platform/content-publishing/
- https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post
- https://developers.tiktok.com/docs/en/content-sharing-guidelines
