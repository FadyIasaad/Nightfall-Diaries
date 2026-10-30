# FULL UPDATED PROJECT — AI DRAMA UNIVERSE V3

**Date:** 29 October 2026  
**Core objective:** A fully online, $0-budget-target short drama production system whose first two stories run sequentially, followed by original trend-driven seasons of at least ten episodes, using consistent cast visuals and voices. The publishing destination is the same owner's existing YouTube channel, Facebook Page, and TikTok account whenever API permissions permit.

## 1. First two series — permanent story canon

| Order | Series | Episodes | Genre | Stars |
|---|---|---:|---|---|
| 1 | **The Last Little Fox** | 12 | Animal-led adventure | Ember, Moss, Luma, Ash + narrator |
| 2 | **The Boy Who Forgot Tomorrow** | 10 | Mystery/fantasy | Noah, Mira, Dr. Vale, Clockkeeper + narrator |

All 22 story beats, character appearance attributes and narrative endings are contained in `seasons/S01_...` and `seasons/S02_...`. No episode is skipped and each season completes before the next starts. The original 2-series Bibles remain untouched.

## 2. Fixed voices matched to cast

| Character | Voice ID | Role direction |
|---|---|---|
| Ember | `am_puck` | youthful curious brave fox |
| Moss | `bm_george` | measured older mentor |
| Luma | `af_heart` | gentle, perceptive |
| Ash | `am_fenrir` | guarded low voice |
| Fox narrator | `bf_emma` | warm cinematic voice |
| Noah | `am_liam` | worried adventurous child-style delivery, not cloned child |
| Mira | `af_bella` | bright and expressive |
| Dr. Vale | `af_nicole` | calm intelligent |
| Clockkeeper | `am_michael` | mysterious controlled |
| Tomorrow narrator | `bm_fable` | measured suspenseful storyteller |

Kokoro voice presets are **suggestions frozen for continuity**, not tested character impersonations. Visual reference PNGs now exist in the package but are *rudimentary, original 2D placeholders* until a person provides/approves better stylized art. Each character's visual and audio profile is fingerprinted and cannot silently switch midway through the series.

## 3. Complete cloud episode pipeline

```text
GitHub Actions schedule (10:00 Africa/Cairo; optional Run workflow)
  ↓
Collect live Google Trends RSS snapshots and preserve observed dates
  ↓
Read persistent episode queue (only next episode from earliest unfinished series)
  ↓
Read fixed cast + voice registry; verify identity SHA256 locks
  ↓
Read one of 22 prewritten original scripts; for later episodes, use GitHub Models or a labeled original fallback
  ↓
Load original approved/stylized cast reference PNGs (never regenerate if saved)
  ↓
Kokoro CPU TTS: matching cast voice per line + save first audition WAV
  ↓
Pillow frames: scene captions, consistent portrait, episode title
  ↓
FFmpeg H.264/AAC MP4, 9:16, 720x1280, approximately 35–60 seconds
  ↓
FFprobe duration/audio/video validation; store script + receipts
  ↓
YouTube private / Facebook draft / TikTok creator inbox, if authorized
  ↓
Git-tracked immutable queue + video download artifact (7 days)
  ↓
If season ended: trend rank → new original cast, world and 10–12 ep arc
```

The baseline does **not** do face-aware character motion, text-to-3D or video diffusion. Short drama comes from storytelling, dialogue, music-less cinematic framing, and motion-comic camera movement. Your free 3D-look goal would require a separately tested AI image/video provider or a sufficiently powerful cloud GPU that may incur costs.

## 4. Next season: strict automatic behavior

- Research the latest **seven days of actual observed RSS trend items** from countries `US`, `GB`, `CA`, `AU`, `IN`, starting on launch day; do not claim seven days of history until seven days were collected.
- Record date, geography, link, title, approximate search traffic, observation count. No fabricated traffic.
- Disqualify unsafe, sensational real-person, political, disaster-related, or unadaptable intellectual property topics. Rank remaining *eligible* concepts using a disclosed traffic-frequency-regions score; highest **eligible** idea wins, not necessarily the single worldwide highest search term.
- Convert the trend **theme**, not its exact current people or brands, into an original serialized drama: fresh plot, setting, 3–5 fictional cast members, stable voice IDs and 10–12 complete episodes. No copy of an existing franchise.
- Prefer GitHub Models for better outlines; deterministic, clearly labeled original concept templates keep free workflow operational if model quotas are exhausted. Artistic quality may be limited.
- **Do not generate a false trend** if RSS history is empty or unavailable; retry another day. The old completed series and metadata stay intact.
- New voice presets are chosen to match role (hero/ally/mentor/narrator), prioritizing voices unused in prior seasons. The English voice catalog is finite, so indefinite generation cannot guarantee a brand-new audio timbre each time; new identity and per-season voice lock remain guaranteed.

## 5. Character and audio assets are permanent

- Saved cast identity: `seasons/Sxx_*/characters/character_registry.json`.
- Original voice ID, speaking speed, direction, and audition phrase remain in the cast entry.
- Saved per-character render reference: `characters/[cast-id]/cloud_reference.png` + SHA256 in `cloud_reference_locks.json`.
- Saved audition generated on first spoken episode: `voices/[cast-id]/cloud_audition.wav`.
- Extra SHA256 specs: `cloud_data/identity_locks.json`. Any unexpected change breaks the run until resolved.
- User may intentionally replace reference using `python -m studio.approve_art ...`; do not change appearance in individual episode prompts.
- New seasons produce new unique identities, not re-used story canon, with dedicated character folders.

## 6. Automatic upload targets and limits

| Destination | Default | API status if permission missing | Unattended public upload |
|---|---|---|---|
| YouTube | Existing channel **Private** upload | `missing_credentials` | Possible after channel OAuth, approvals and explicit public opt-in |
| Facebook | Existing Page Reel **DRAFT** | `missing_credentials` | Possible after Meta review/permissions, approvals and opt-in |
| TikTok | Existing account **Inbox editing flow** | `missing_credentials` | **Not supported** in this package; creator confirms in TikTok |

An uploaded YouTube Private video is **not** a native unsaved Studio draft. TikTok inbox uploads are not public TikTok posts. No API permissions are spoofed. Inflight uncertain uploads are not automatically repeated to prevent duplicates.

## 7. Zero-budget limits and fallback behavior

- CPU-only Kokoro plus FFmpeg runs on an ephemeral GitHub-hosted runner, using GitHub Actions free allowance if available. The first model download can be large.
- GitHub Models inference is limited by separate access and rate quotas. The first 22 scripts are individually prewritten and do not require a writing API. New series outlines also have a deterministic original concept-template fallback.
- The rendering quality is **simple illustrated 2D motion comics** (not Pixar-like full 3D). It is not honest to promise free unlimited photo-real character animation in hosted GitHub runners.
- Without OAuth/API approval, the MP4 remains reviewable as a short-lived GitHub Actions artifact; no account receives it.
- Quotas and live API behaviors can change; the first manual test is required. No credentials or uploads are included in the package.

## 8. What was implemented in this version

- Complete source for cloud workflow, script/plot management, RSS trends, new season factory, locked art/voice cache, Kokoro audio, Pillow/FFmpeg video, YouTube, Meta and TikTok API adapters, approval helpers, state journaling, Python unit tests, and setup documentation.
- Preloaded 22 episode outlines AND 22 original ready-to-narrate scripts, permanent cast identities, 10 saved 2D reference PNGs with hashes.
- Offline tests for queue ordering, voice IDs, safe trend selection, and one FFmpeg playable sample passed in the build environment.
- **Still to be validated by you:** actual model inference/CPU Kokoro on GitHub, developer app access, social uploads, title/asset quality. This is implementation-ready source, not a claim of completed live deployment.

## 9. How to start

Read `README.md` then `CLOUD_ONLY_SETUP.md`. Upload the complete ZIP contents into the current private GitHub repository through browser Codespaces, disable previous overlapping workflows, add only the supported account credentials you actually possess, then run `03 - AI Drama Cloud Studio V3` manually once. Inspect the first MP4 and queue receipts before public posting.
