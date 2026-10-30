# AI Drama Universe — Cloud Studio V3 (full updated source)

**Updated:** 29 October 2026 · **Designed for:** GitHub Actions cloud runner · **License for new code:** MIT (see `LICENSE`). This project includes earlier user-authored story plans in `archive_v2/` and `seasons/`.

> **Status:** A complete, installable cloud **motion-comic production prototype**, with live API integrations requiring the owner's account authorization. Unit tests and a short offline FFmpeg render passed; GitHub-hosted Kokoro generation and actual YouTube, Facebook, and TikTok uploads **have not been live-tested**. No channels/accounts are connected, no episodes are posted, and this bundle is not a Pixar-style 3D animation engine.

## The exact creative promise

1. **Starter S01:** *The Last Little Fox* — 12 episodes, permanent cast `Ember`, `Moss`, `Luma`, `Ash`, narrator. An animal-led story.
2. **Starter S02:** *The Boy Who Forgot Tomorrow* — 10 episodes, permanent cast `Noah`, `Mira`, `Dr. Vale`, `Clockkeeper`, narrator.
3. No interleaving seasons. Exactly **one new episode per successful daily run**, normally at **10:00 AM Cairo local time**. Manual `Run workflow` also available.
4. After the final episode, monitor the **last seven days of *observed* Google Trends RSS** data. Select a high-ranked topic suitable for original fiction. Avoid real-person drama, tragedy, politics, and copyrighted franchise content. New story gets a **fresh title, fictional world, cast, character-art asset files, voice profiles, and at least 10 episodes**. An eligible real trend is required; no fabricated trends.
5. Every cast member has a frozen appearance specification and Kokoro voice ID, plus saved **identical visual reference PNG** (simple procedural cartoon). The project blocks unexpected identity edits. Use `approve_art.py` if you later create better rights-cleared reference images.
6. Default uploads go to **the same intended YouTube channel (Private)**, **Facebook Page (DRAFT)**, and **TikTok inbox** *only after their respective API authorization exists*. The TikTok creator must finalize a post. No automatic public posting by default.
7. Fully online execution: GitHub Actions hosted runner; after setup **no PC is required during generation**. Uses FFmpeg, Kokoro TTS, optional GitHub Models, and Python.

**Reality check:** The baseline artwork uses simple 2D cartoon character cards, captions, gentle zoom motion, and multi-character speech. **It is not full-body animated 3D and not comparable in quality to Pixar.** If an available free GPU image/video service becomes reliable, it can be added as an optional adapter later. Do not claim this version supplies it.

## Browser-only repository deployment (Codespaces)

1. Use your **existing GitHub repository** for the original YouTube channel. **Make it Private** first: draft media, encrypted TikTok refresh-token data, scripts, and cast assets belong to you.
2. Open the repository in **GitHub Codespaces** from your browser, or use GitHub's web editor. Upload/extract this ZIP in Codespaces and **copy the package's *contents* to repository root**, not an extra nested project directory. Retain any old secrets/settings and original files.
3. **Disable old scheduled video workflows** (including the old Edge TTS generator) or they may double-post. Keep only the new `.github/workflows/03_drama_cloud_full_online.yml` enabled for generation.
4. In repo **Settings → Actions → General**, enable Actions and permit **Read and write permissions**. The workflow requests `contents: write` to save the queue and `models: read` for GitHub Models when permitted. If branch protection disallows bot commits, use a permitted state branch/store; do not bypass the policy.
5. In **Settings → Secrets and variables → Actions**, add credentials for platforms when available (next section). Before credentials, videos are still rendered to a **downloadable GitHub Actions artifact** and the queue records `missing_credentials`.
6. In **Actions → 03 - AI Drama Cloud Studio V3 → Run workflow**, run manually. After success, open the `drama-cloud-preview-[run]` artifact and review the MP4, and inspect `cloud_data/episode_queue.json` for platform receipts.
7. If the first run fails, check the log, fix the specific dependency/API issue, rerun. A failed render does not advance the queue. There is **no guaranteed runner speed or free quota**.

To test syntax without building an MP4 inside Codespaces (after `pip install -r requirements.txt`):

```bash
python -m unittest discover -s tests -v
python -m studio.main --dry-run
```

Full documentation: `FULL_UPDATED_PROJECT.md` and `CLOUD_ONLY_SETUP.md`.

## Account credentials (never paste tokens into code or chat)

| Platform | GitHub Action secrets / variables | Default effect |
|---|---|---|
| YouTube **same channel** | Secrets `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`; Actions **variable** `YOUTUBE_EXPECTED_CHANNEL_ID` | Verifies channel ID before a **Private** video upload; OAuth must include access suitable to read the channel and upload |
| Facebook **same Page** | Secrets `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN`; optional var `FB_GRAPH_API_VERSION` | Creates a Reel with `video_state=DRAFT` if permissions allow |
| TikTok | Secrets `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REFRESH_TOKEN`, `DRAMA_TOKEN_KEY` | Uploads video to **inbox editing flow**, not direct public post; approved `video.upload` scope required |
| Public opt-in | `DRAMA_ALLOW_UNREVIEWED_PUBLIC=true` **AND** `cloud_config.json` public/PUBLISHED, plus manually approved art and voice statuses | Only YouTube/Facebook. TikTok direct publishing is **not supported** by this bundle. |

**TikTok encryption key** (run in a browser-based Codespace terminal after `pip install cryptography`):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Save the printed key as a secret and back it up securely. Only the **encrypted** rotated token is stored in the PRIVATE repo at `cloud_data/tiktok_token.enc`. Losing the key or removing the ciphertext requires TikTok reauthorization. An API approval is not guaranteed.

### About FREE

No paid video API is required by default. But GitHub Actions and GitHub Models have limited free quotas; GitHub-hosted CPU Kokoro may be slow or may run out of resources. Scheduled jobs can be delayed. Platform developer authorization can be cumbersome and depends on account eligibility. A zero-dollar budget is a **target, not an uptime/capacity guarantee**.

## File map

```text
.github/workflows/03_drama_cloud_full_online.yml   daily Cairo-time cloud job
cloud_config.json                                   duration, safety, posting and trend settings
studio/main.py                                      queue + render + upload orchestration
studio/story.py                                     scripts, optional GitHub Models + starter fallback
studio/season_factory.py                            newly trending topic -> new 10-12 ep season
studio/trends.py                                    7-day Google Trends evidence/history/score
studio/identity.py                                  immutable voice/cast fingerprints
studio/art.py                                       persisted stylized 2D character references
studio/audio.py                                     Kokoro character voices (WAV auditions)
studio/video.py                                     FFmpeg 9:16 video + captioned cards
studio/publish.py                                   permission-gated YouTube / FB / TikTok adapters
studio/approve_art.py                               controlled visual-reference replacement
studio/approve_voice.py                             mark audition approved after listening
seasons/S01_*/                                     12 ep outlines, story bible, voice/cast refs
seasons/S02_*/                                     10 ep outlines, story bible, voice/cast refs
cloud_data/episode_queue.json                       per-episode renders, stage receipts
cloud_data/trend_history.json                       observed timestamps, sources, countries
cloud_data/identity_locks.json                      frozen characters across episodes
cloud_data/series_decisions.json                    reasons and evidence for new seasons
tests/test_core.py                                  functional validation tests
archive_v2/                                         prior design notes and legacy scripts
```

## Privacy, duplicate prevention, and future growth

Uploads are **fail-closed**. Before remote API interaction the script persists an `inflight` intent to the private Git repository; uncertain uploads become `needs_reconcile` and are never blindly retried. A `staged` receipt means only that the service accepted the request, **not** that a TikTok post was published or the Reel finished processing. YouTube expected-channel checking prevents unintended uploads to a different channel.

The two starter series now include **22 individually prewritten original scripts**, one per episode: no text-generation quota is required for those 22 videos. If a starter script is deleted, the engine can regenerate it with GitHub Models or transparently fall back to a simple outline-based script. For future seasons, if model inference is not available, the project generates an original **template-driven** 10-episode arc inspired by a verified eligible trend category. This fallback is functional but its creative quality may be limited. New casts are completely new identities; English Kokoro voice presets are **finite**, so they can eventually be reused in later unrelated seasons (never recast within one).

No music or copyrighted movie clips are taken from the internet. No scraping of actual people's private stories. For best visual quality, manually replace original 2D placeholder cards with your own approved images while retaining each character's identity.

## Official references

- [GitHub Actions scheduled workflow timezone](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule)
- [GitHub Models overview](https://docs.github.com/en/github-models)
- [Google Trends 7-day export/RSS](https://support.google.com/trends/answer/3076011?hl=en)
- [Kokoro official voice list](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
- [YouTube videos.insert API](https://developers.google.com/youtube/v3/docs/videos/insert)
- [Meta's Facebook Reels Postman collection](https://www.postman.com/meta/facebook/documentation/r56bjfd/facebook-api)
- [TikTok Inbox video upload](https://developers.tiktok.com/docs/en/content-posting-api-reference-upload-video)
