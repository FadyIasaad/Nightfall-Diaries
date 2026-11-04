# Nightfall Diaries — Zero-Budget Cloud Studio

**Status (4 November 2026): Engineering foundation / quality proof not passed / public posting disabled.** This repository does **not** yet produce a verified premium animated up-to-3-minute episode. No successful public four-platform upload is claimed.

The non-negotiable requirements are recorded in [MASTER_PLAN_CONTRACT.md](MASTER_PLAN_CONTRACT.md). The two original series remain unchanged: **The Last Little Fox (12 episodes)** then **The Boy Who Forgot Tomorrow (10 episodes)**. Never replace the existing YouTube channel, Nightfall Diaries Facebook Page, stores.nightfall Instagram, or the intended TikTok identity.

## One workflow, browser or phone only

Go to **Actions → Nightfall Diaries - One Free Online Workflow → Run workflow**. The action dropdown has:

- **Check setup**: validates all 22 original story files and reports current blockers without any AI-video dependencies, cloud GPU usage, or publishing.
- **Check free motion provider**: read-only probe of the reviewed Wan2.2 public ZeroGPU endpoint; consumes no GPU quota or money.\n- **Render quality proof**: tries three real-motion shots for a 15–30-second Ember/Moss dialogue-action candidate using the public Wan2.2 ZeroGPU candidate (up to 5 seconds each, subject to shared free quotas). The output is only a **motion candidate**: no audio-driven lip-sync has been established. This may fail when the provider is unavailable or the voice/motion is too short; it must never fall back to photo zooms.
- **Audition character voices**: creates one Kokoro WAV per locked Fox-series character and an audition manifest in a cloud artifact. These are listening candidates, not approved emotional acting or lip sync.\n- **Generate full episode**: requires an actual 240+ word, coherent full screenplay and a 90–180-second playable vertical H.264/AAC MP4. A separate, canon-preserving E01 pilot screenplay now contains 14 directed scenes, but the moving-actor GPU/voice quality and total measured runtime still require proof. Other original episodes remain short archives and cannot pass the full-length gate.
- **Generate another episode**: select a specific original episode ID (for example `S01_the_last_little_fox_E02`) to try a second 90–180-second episode on the same day. Free GPU quota may prevent completion that day.\n- **Generate + Publish**: fully gated. Cannot post while the config and independent quality/platform verification fields are false.
- **Retry missing platforms**: currently fail-closed because the current receipts lack confirmed-public status and source MP4 recovery is not completed. Will not duplicate an upload.
- **Prepare episode**, **Validate stories**, **Check Instagram**: existing safe preparation and diagnostics.

The **10 AM Cairo** schedule is active as a *read-only preflight/standby*. It must not start public posting until a real visual/lip-sync proof and each official platform integration pass verification. A GitHub release, an upload response or a TikTok inbox draft is **not proof of public posting**.

## Current technical restrictions

- GitHub's normal free public Actions runner is CPU-only. There is no proven free GPU service that can deliver film-quality up-to-3-minute daily character animation indefinitely. The optional Hugging Face endpoint is not guaranteed.
- An automated one-time proof run can be triggered by a main-branch merge commit containing `[nightfall-first-motion-proof]`. This does not enable social publishing.\n- Kokoro neural speech is implemented, but differentiated emotions, facial/lip synchronization, soundtrack and full cinematic action are **unproven**.
- Tracked cloud character images exist and are now used per character. These are reference images, **not rigged, professionally animated models**.
- The original E01 archive remains four short scenes; a separate compact E01 production screenplay now has directed shots and preserves those lines. The other 21 original episodes still require expansion.
- YouTube, Facebook, Instagram and TikTok publishing still need separate official API, visibility and idempotency proofs; no manual upload substitute is permitted.

**Next engineering gates:** verify the expanded E01 speech timing, lock neural voices and acting references, produce a watchable 15–30-second cinematic body-action/lip-sync proof within free resources, render full pilot, then independently verify each publisher. Publishing remains off until the requirements are met.

## Cast lock and episode length revision

Original character reference images are SHA-256 verified before rendering. The exact Kokoro voice preset, engine, language, and speed for every original character in both series are locked in `studio/voice_profile_locks.json`. Missing or altered visual assets and changed voice profiles cause an immediate error before requesting GPU footage. These checks protect source consistency; no free generative model can guarantee every output frame preserves identity, so actual video appearance and lip synchronization remain separate approval gates. The first two Fox scripts now have concise production drafts targeting **90–180 seconds**, without overwriting the original canon.

## Quota-safe nightly resume (4 November 2026)

Actual run [41907266545](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/41907266545) verified that Wan2.2 ZeroGPU generated **one real 5-second moving clip** for Fox E02; its second request failed with **126 GPU seconds requested, only 90 remaining**. The missing `HF_TOKEN` meant the run was unauthenticated. The first clip was checkpointed to `nightfall-shots-v2-41907266545-1`, and GitHub confirmed the cache saved. A public API readiness check is not proof of a full movie.

The workflow now recognizes the provider's quota-exhaustion error and writes `output/render_status.json` with **PAUSED_FREE_QUOTA**, retry eligibility, and **completed_full_episode: false**. It retains all already-created clips and the pending episode queue in the existing GitHub Actions cache. Cache restore checks SHA-256 and prompt/model/locked cast fingerprints before reuse; a cache miss can cause regeneration.

The same workflow checks for due pending episodes at **10:00 and 23:00 Africa/Cairo**. The 23:00 run is **resume-only** and can never publish. The 10:00 scheduled production remains in safe standby until live quality/publishing gates pass, but may resume a pending *unpublished* render. Provider availability and cache retention are best effort; scheduled triggers may be delayed. Run a manual **Generate another episode** again with `S01_the_last_little_fox_E02` if you want to retry before the next due schedule.

To optionally increase the free Hugging Face allowance without paying or creating multiple accounts, create a free **read** access token on [Hugging Face](https://huggingface.co/settings/tokens) and save it *only* as your repository Actions secret named `HF_TOKEN` (Settings → Secrets and variables → Actions). Do not paste tokens in chats or commit them into source. Authentication increases the provider's free quota relative to anonymous calls but does **not** guarantee daily 90–180-second video production. Each 5-second clip can cost around 126 GPU seconds on this Space; dozens of shots may take many free-quota reset cycles.

Neither cloud checkpoints nor the sample motion clip prove premium character consistency, emotional lip-sync, SFX/captions, or reliable public posting. **Keep NIGHTFALL_LIVE disabled.** A green job that reports PAUSED_FREE_QUOTA is a checkpointed *pause*, not a completed episode.
