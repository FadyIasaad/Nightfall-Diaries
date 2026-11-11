# NIGHTFALL DIARIES — PHASE 0 REPOSITORY AUDIT & EXECUTION GATE

**Date:** 2026-11-05, Africa/Cairo  
**Authoritative live baseline at audit:** `main` commit `12738ecd80085dbfbe2ed28cd29d81344ffca4b7`  
**Source documents:** `NIGHTFALL_DIARIES_MASTER_EXECUTION_PLAN.md` (2026-11-05) and `NIGHTFALL_DIARIES_COMPLETE_PROJECT_HANDOFF_2026-11-04.md`. The handoff is an historical evidence snapshot; live GitHub code and successful runs take precedence on implementation details.  
**Phase:** 0 ONLY. **No GPU inference, code-engine migration, OAuth, app-review form submission or social upload was attempted.**

## Executive result
The existing repository contains **22 original archived episodes** (12 Fox, 10 Boy), with two short Fox production drafts, SHA-256 locked source reference images, fixed Kokoro voice IDs, a safe manual extra-episode menu, per-clip SHA-verified checkpointing, a quota-paused queue and a 10:00/23:00 Cairo same-workflow retry check. Previous CI passed 52 tests. These **are not proof of a complete cinematic episode**.

The only known real E02 motion sample is about five seconds and does **not** meet the approved cinematic-art benchmark: it resembles a flat orange fox character card with a visible "Ember" label. Actual expressive action, generated-frame identity, audio-driven lipsync, subtitles/music/SFX and fully public four-platform posting are unproven. All production flags and `config.json.public_publish_enabled` are false. **KEEP THEM FALSE.**

This Phase 0 PR adds draft privacy/terms/support pages, platform-audit briefing, model/licence risk table, a complete per-file migration decision, and regression tests that explicitly forbid activating production. It **does not authorize Phase 1**.

## 1. Conflicts / corrections identified before writing code

| Plan assertion or default | Live / newly verified fact | Decision |
|---|---|---|
| §12 says GitHub cron is UTC-only and must be doubled for Cairo DST | Current [GitHub Actions syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) **allows `timezone: Africa/Cairo`**; the repo already uses it | **Keep the working timezone syntax.** Do not add duplicate UTC triggers. GitHub schedule may still be delayed. |
| §§3/13 say an unaudited YouTube API project is **forced private** | [Google's November 2, 2026 update](https://developers.google.com/youtube/data/revision_history) **removed that restriction**; current [videos.insert](https://developers.google.com/youtube/data/reference/rest/v3/videos/insert) confirms | Revise review priority: verify existing OAuth/account and public status first; audit only when actually needed for quota/compliance/OAuth rules. |
| File header says GitHub README is an old "V5 lean rebuild" and should be ignored | Live README at this commit was updated through PR #20 and explicitly documents newer quota-pause logic | Treat **README as a maintained source**, cross-check it against code. The header's warning is stale. `config.json` *does* contain legacy `v5.0-safe-rebuild` fields. |
| Architecture presumes **Kaggle GPU notebooks will run headlessly and suffice for a multi-minute animated episode** | The [official Kaggle CLI](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md) supports push/status/output and Kaggle docs mention a fluctuating weekly free GPU limit. **Owner account access, T4 availability, licence eligibility, LoRA training and video throughput were NOT measured** | Treat Kaggle as a **Phase 1 hypothesis**, not a proven engine. Accept actual no-cost benchmarks before adopting it. |
| §5 says a private Kaggle Dataset is "durable" production storage | No live Kaggle account/dataset or recovery test is connected; data/quota and access rules are unverified | Label as **proposed checkpoint storage**. Do not delete GitHub caches until replacement has been tested. |
| §8 expects many 2.5D still-based shots although owner previously rejected still + voice slideshows | Hybrid parallax creates camera motion, but **doesn't guarantee acting**. The uploaded plan describes cinematic reference editing and permits 2.5D support shots | Allow 2.5D only for environmental/inserts; **G1 requires visibly animated character acting** for story beats. A short great-looking still montage alone is not acceptance. |
| §10 suggests reaction-shot editing rather than lipsync for the Fox series | User previously requested moving talking characters with good lip-sync. No successful lip-sync proof exists | **Not resolved by a text plan.** Produce real audio/acting test in Phase 2; owner approves look, method, and mouth-sync compromises explicitly. |
| §11 proposes OCR, embeddings and aesthetics as production gates | Current `studio/quality_gate.py` checks only playable H.264/AAC, size and duration | **Planned**, not implemented. No automatic approval until independently calibrated. |
| §13 assumes a fully operational cross-platform uploader | `studio/crosspost.py` is experimental; Facebook endpoint, TikTok permissions and public-state receipts still need verification | Never enable `Generate + Publish` yet. TikTok unaudited private restrictions **still apply** per [official docs](https://developers.tiktok.com/docs/en/content-posting-api-get-started). |
| §7 assumes hash-locked PNG = character consistency | SHA-256 verifies **source bytes only**; the real E02 test demonstrates unwanted text and flat output | Actual **output-frame identity/visual-audit** is a separate mandatory gate. |
| Master plan requests public privacy URLs/app audits in Phase 0 | No real support contact, verified Pages site, owner OAuth approvals or app audit credentials were supplied | Draft compliant pages/templates **only**. Owner has to finalize contact and enable/verify Pages; audits **not submitted**. |

## 2. Complete `studio/` file decisions (nothing deleted in Phase 0)

Legend: **KEEP** = preserve as source of truth; **EXTEND** = retain and strengthen later; **REPLACE LATER** = phase-gated migration, do not delete until successor works; **RETIRE LATER** = demonstrably obsolete, explicitly exclude from production.

| File | Disposition | Why / next action |
|---|---|---|
| `studio/__init__.py` | KEEP | Python package marker. |
| `studio/audio.py` | **RETIRE LATER** | Robotic `espeak-ng` voice engine violates locked Kokoro-only production. Referenced by the old `preview.py`; do not reinstate as a fallback. |
| `studio/auto_prepare.py` | EXTEND | Story/cast prep metadata, no actual rendered video; add true shot planner/series DNA later. |
| `studio/check.py` | KEEP/EXTEND | Read-only Instagram identity verification; add ownership/permission checks in publishing phase. |
| `studio/checkpoints.py` | KEEP/EXTEND | Clip SHA-256 and deterministic fingerprints; later test versioned Kaggle storage/backups and recovery. |
| `studio/continuity.py` | **KEEP LOCKED** | Reference PNG hashes and exact Kokoro preset/speed/language; never bypass source identity. |
| `studio/crosspost.py` | **REPLACE LATER** | Experimental publisher: Facebook endpoint, TikTok creator_info, authorization, public-status polling, true idempotency unverified. No public use. |
| `studio/episode_length_policy.json` | KEEP | Enforces ≤180 s user decision; maintain same ceiling in final QA. |
| `studio/free_video.py` | REPLACE LATER / optional bonus | Quota-limited HF ZeroGPU video client (first real E02 sample failed quality); keep as non-primary test fallback after G1. |
| `studio/motion_provider.py` | KEEP for diagnostics | Read-only model endpoint probe; not a video-quality guarantee. |
| `studio/neural_audio.py` | **KEEP LOCKED** | Kokoro TTS engine and cached model pipeline; improve emotional delivery without switching voices. |
| `studio/pending.py` | KEEP/EXTEND | Retry queue and `PAUSED_FREE_QUOTA` state; cache is evictable; future durable backend needs proof. |
| `studio/preview.py` | **RETIRE LATER** | Legacy preview calls robotic eSpeak and primitive Blender actors, not owner-approved look. |
| `studio/production.py` | KEEP safety only | Historical production readiness/report; confirm one source of truth for current routing. |
| `studio/production_settings.json` | **KEEP LOCKED** | All production, API, visual and lipsync flags are false; owner gate before any change. |
| `studio/proofs/EMBER_SH01_REAL_MOTION_PROMPT.md` | KEEP as reference | First motion prompt history; not proof of cinematic quality. |
| `studio/proofs/ember_E01_proof_plan.json` | EXTEND after G1 | Three-shot E01 experiment; update to hero/2.5D Look Proof only after the new engine is validated. |
| `studio/quality_gate.py` | **EXTEND** | Technical H.264/AAC 9:16 90–180s checks only; add motion/identity/no-text/audio/content validation. |
| `studio/real_film.py` | **REPLACE LATER** | Current 5-second video clip stitching; inefficient for free quota, generated quality inadequate. Keep until new approach passes G1/G2. |
| `studio/render_blender.py` | **RETIRE LATER** | Procedural low-poly/primitive animal shapes; explicitly rejected as visual target. |
| `studio/restore.py` | **KEEP LOCKED** | Validates all 22 original archives. |
| `studio/run_free.py` | EXTEND | Current one-button safe entry point, manual extra episodes, pending status; maintain fail-closed publishing. |
| `studio/screenplay.py` | KEEP/EXTEND | Short production drafts without overwriting original E01–E22 archives; expand future scripts carefully. |
| `studio/voice_audition.py` | **KEEP** | Existing Kokoro audition feature, generated 5 Fox voices successfully. |
| `studio/voice_profile_locks.json` | **KEEP LOCKED** | Exact voice identities for both casts. |
 
**Deletion policy:** No deletions in Phase 0. A separate migration PR may delete `audio.py`, `preview.py`, `render_blender.py` only after searching for imports, proving the replacement and preserving relevant historic tests.

## 3. Validated repo inventory and observed evidence

- **Series/canon:** `S01_the_last_little_fox` has 12 planned archives; `S02_the_boy_who_forgot_tomorrow` has 10. The 22 original scripts must remain unchanged. Fox E01/E02 have separate compact production drafts.
- **Locked Fox voices:** Ember `am_puck`, Moss `bm_george`, Luma `af_heart`, Ash `am_fenrir`, narrator `bf_emma`. The human series also has five separate locked voices, stored in `studio/voice_profile_locks.json`.
- **Real previous run:** E02 clip 1 ran ~5.083 seconds; next ZeroGPU request needed 126s GPU with 90s remaining. Audio sample and clip were checkpointed. No complete film exists.
- **Previous engineering test:** 52 tests passed in GitHub Actions run `41918782507`. Those tests do not prove GPU access or acting quality.
- **Current publication state:** `studio/production_settings.json` approval booleans false; `config.json.public_publish_enabled` false; TikTok access token missing in latest supplied job logs; masked YouTube/Meta secrets are not verified publish permissions.

## 4. Phase 0 deliverables

| Artifact | Purpose | Ready now? |
|---|---|---|
| [Privacy Policy](privacy.md) | Data handling and provider disclosure | **DRAFT:** real owner support contact/review required. |
| [Terms of Use](terms.md) | Original fiction, IP, safe use and third-party services | **DRAFT:** verify operator details and approval. |
| [Support](support.md) | Safe path for questions/deletion inquiries | **INCOMPLETE:** private support channel pending. |
| [Platform Audits](PLATFORM_AUDITS.md) | YouTube 2026 correction, TikTok review and Meta checklist | **PREPARED**; not submitted. |
| [Model/Asset Licences](MODEL_LICENSE_AUDIT.md) | Monetization / model terms / image provenance | **REVIEWED**; exact weights and source image rights still pending. |
| [Policy hub](index.md) | GitHub Pages-ready `/docs` source folder | **NOT LIVE until Pages settings and URLs are verified.** |
| [Safety tests](../tests/test_phase0_docs.py) | Existence, the exact disabled flags and unchanged original series | **CI must pass before Phase 0 delivery**. |

## 5. Owner-only browser checklist (required before public app reviews)
- [ ] Supply a **working confidential support contact**, approve the operator name and jurisdiction on privacy/terms. Do not post secrets in a public GitHub issue.
- [ ] Open repository Settings → Pages, choose **Deploy from a branch → main → /docs** and Save; test policy URLs in an incognito browser. GitHub Pages setup must be owner verified.
- [ ] Check whether the existing YouTube OAuth app needs **quota** or **OAuth** compliance approval in current policy; do not assume the obsolete private-lock rule.
- [ ] For TikTok, create/authorize the actual Content Posting API app and request the scope/app review with a working demo; submission remains an owner action.
- [ ] Ensure the **same** Page, IG business account, YouTube channel, TikTok identity are selected; permissions not yet verified for public publishing.
- [ ] Verify a legitimate Kaggle account is GPU-eligible and check its displayed free quota. Store `KAGGLE_USERNAME` and `KAGGLE_KEY` as GitHub Actions secrets **only when Phase 1 is approved**. No account creation or token required for Phase 0.
- [ ] Identify source/licence history for existing character reference PNGs and any future music/SFX/fonts.
- [ ] Confirm the hybrid plan will not replace character action with image-panning: approve the owner-visible **G1 look proof** before any further phase.

## 6. Formal Phase 0 acceptance gate — **PENDING OWNER APPROVAL**

Engineering documents and read-only validation can pass without owner credentials. **Full Phase 0 is NOT accepted until the owner has reviewed the corrected plan, approved the draft policy/operator details, enabled and verified GitHub Pages if desired for audits, and acknowledged outstanding licensing/provenance work.**

No promise of one public 3-minute episode daily, extra same-day completed episode, perfect lip sync, guaranteed Kaggle GPU or multi-platform posting is made. Do not start Phase 1 automatically.

## Sources (live official pages checked in Phase 0)
- GitHub schedule timezone: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- YouTube Nov 2 policy reversal: https://developers.google.com/youtube/data/revision_history
- YouTube upload fields: https://developers.google.com/youtube/data/reference/rest/v3/videos/insert
- YouTube quota/compliance audits: https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits
- TikTok audit: https://developers.tiktok.com/docs/en/content-posting-api-get-started
- Kaggle CLI notebook jobs: https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md
- Kaggle GPU quotas: https://www.kaggle.com/docs/efficient-gpu-usage
- Model source evidence: [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M), [Wan2.2](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B), [SDXL](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0), [FLUX-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell), [FLUX-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev), [LTX-2.3](https://huggingface.co/Lightricks/LTX-2.3).

**Status: PHASE 0 DOCUMENTS READY; GATE G0 PENDING. NOTHING PUBLISHED.**

## Contact addendum — November 5, 2026

The owner provided two email addresses for public Nightfall Diaries support and data requests: **fadyasaad.kaz@gmail.com** and **fadyasaad13@gmail.com**. They are now listed in `docs/support.md`, `docs/privacy.md`, `docs/terms.md`, and `docs/index.md`. Actual mailbox deliverability has not been tested; the operator/jurisdiction details and final owner approval are still outstanding. GitHub Pages has not been enabled or verified in this change, and no app-review form or public video publishing has been submitted or activated. **Gate G0 remains pending.**

## November 9, 2026 inventory extension

| File | Disposition | Explanation |
|---|---|---|
| `studio/agnes_probe.py` | **KEEP / READ-ONLY** | Only manual GitHub GET-models connection check; never bill, generate media, or publish; price and quota must be verified separately. |


## 2026-11-11: Agnes pricing-only diagnostic extension

| File | Disposition | Explanation |
|---|---|---|
| `studio/agnes_cost_gate.py` | **KEEP / READ-ONLY** | Exact public Flash promotional pricing and LTX-2.5 metadata via allowlisted GET requests. Prepares Ember shot instructions only. Does not authorize video inference, payment, account changes, or publishing. Account hard zero-spend gate remains unverified. |

See `docs/AGNES_FLASH_ZERO_COST_GATE_2026-11-11.md`. No original story, cast voice lock, character image or production switch was changed.


## 2026-11-11: Kaggle manual free T4 GPU bridge (proposed experiment, not production approval)

| Studio file | Disposition | Rationale |
|---|---|---|
| `studio/kaggle_bridge.py` | **KEEP — experimental, manual-only** | Stages SHA-locked original Ember image into a private Kaggle notebook, submits a single GPU check or low-res image-to-video candidate using the official Kaggle CLI, polls and downloads results; no paid API/publishing/schedule. |

See `docs/KAGGLE_T4_EMBER_PROOF_2026-11-11.md` and `kaggle/nightfall_gpu_job.py`.
Kaggle GPU access, quota, quality, and 2B LTX runtime are unverified on the owner's account.
