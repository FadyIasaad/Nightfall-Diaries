# AI DRAMA UNIVERSE — 100% CLOUD OPERATIONS (NO PC RUNNER)

**Release:** 29 October 2026. **Status:** Deployable GitHub Actions source and offline-tested renderer/adapter logic, **not yet connected to any account** and **not verified by a live GitHub-hosted render**.

This replaces the Windows Task Scheduler and desktop Ollama system with a GitHub Actions scheduled service. **No desktop computer needs to stay on.** Initial setup can be done in a browser with GitHub's website and optional Codespaces.

## What happens each day

1. GitHub Actions wakes at about **10:00 AM Africa/Cairo**, and can also be run manually from the Actions tab (GitHub may delay scheduled runs).
2. It selects the **next unprocessed episode**: The Last Little Fox E01–E12, then The Boy Who Forgot Tomorrow E01–E10. It will not skip the season order. It maintains a Git-tracked `cloud_data/episode_queue.json` journal.
3. It reuses any saved episode script, or writes a new one using **GitHub Models** and the free-tier allowance. Model-rate errors stop that day's run; they do not generate fake dialogue. The frozen character registry and 10 locked Kokoro voice profiles prevent unintended recasting.
4. It builds original, consistent **illustrated 2D character cards** in a reproducible way, then downloads/runs Kokoro for audio on the temporary runner. This is a GPU-free motion-comic baseline with pans/zooms, captions and voices. **It is NOT full AI-generated 3D character video and does NOT match Pixar-quality animation.** Free hosted GPU video rendering is not supplied.
5. It renders a 9:16 **720×1280 MP4** (CPU-friendly), tests 35–60s duration and an audio/video track, then uploads according to `cloud_config.json`.
6. It saves original character cards, voice samples, scripts and upload receipts in the **same PRIVATE GitHub repository**. The MP4 is downloadable via a GitHub Actions **artifact (7-day retention)**. This avoids depending on temporary runner storage for cast and episode state.
7. After the original 22 episodes, it stops and marks the season queue complete; **automatic safe trend research and brand-new series production are not implemented**. No trends are invented. The supplied trend tool can help prepare the next approved season.

## Default: upload without public posting

| Platform | Default | What this really means | Needs prior authorization |
| --- | --- | --- | --- |
| Existing YouTube channel | `private` | Uploaded video exists in YouTube Studio as **Private** (not a native unsaved Studio Draft) | YouTube OAuth refresh token, API project |
| Existing Facebook Page | `DRAFT` | Creates an **unpublished Page Reel draft** via Meta Graph API | Page ID, Page Access Token, approved Page permissions |
| TikTok | `inbox` | Uploads video to TikTok's **inbox editing flow**; the creator opens the notification and finishes publishing | TikTok developer app, approved `video.upload` scope and user OAuth |

**YouTube and Facebook can also directly publish** after you deliberately set `cloud_config.json` to `public` / `PUBLISHED` and store secret `DRAMA_ALLOW_UNREVIEWED_PUBLIC=true` to explicitly opt in to unattended public AI uploads. The default remains private/draft until you do so. TikTok Direct Post requires eligible/audited app, approved `video.publish` scope, and the separate creator privacy/consent flow; the default inbox path is more realistic. **If permission is missing on any platform, nothing is magically uploaded as a draft there**; instead the run records `missing_credentials` and leaves a downloadable MP4 artifact in GitHub.

## 1. Upload this update to your same GitHub project (browser only)

* **Best option:** Use **GitHub Codespaces** (browser VS Code; not your PC) or the GitHub web editor for copying files into your existing repository. Extract the supplied full-project ZIP inside a Codespace, then commit the *contents of `Nightfall-Diaries-main/`*, not the ZIP itself or its outer folder. Preserve existing GitHub secrets and channel credentials. If you use GitHub's Upload files UI, upload the extracted folder contents under the correct relative paths.
* Make the repository **Private** before using this cloud mode; synthetic art, voice samples, video drafts and state are stored there.
* In repository **Settings → Actions → General**, enable Actions and allow **Read and write permissions** for `GITHUB_TOKEN` (unless explicitly forbidden by your organization). The new workflow requests `contents: write` and `models: read`. Any branch protection blocking automated commits needs an approved alternative state store; do not bypass policy.
* Only `.github/workflows/03_drama_cloud_full_online.yml` generates and uploads. The older scheduled queue-check workflow is archived in this package.

## 2. Configure repository secrets (Settings → Secrets and variables → Actions)

You may add platform credentials gradually. The file is still rendered even with no platform credentials, for review in GitHub Actions.

**YouTube — SAME existing channel:** `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`. Copy the existing, valid credentials from the old project's Actions secrets where possible. In Actions **Variables**, set `YOUTUBE_EXPECTED_CHANNEL_ID` to your own channel ID for safety. `YOUTUBE_REFRESH_TOKEN` must be valid for the intended YouTube account/channel.

**Facebook Page — NOT personal profile:** `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN`. The token and app must have suitable Page access and approved permissions (such as `pages_manage_posts`, `pages_show_list`, `pages_read_engagement`). Business App Review may be needed, depending on whether you manage the app/Page and your setup. Facebook Reel drafts depend on Graph API access to `/PAGE_ID/video_reels`.

**TikTok inbox:** `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REFRESH_TOKEN`, `DRAMA_TOKEN_KEY`. TikTok user authorization for `video.upload` is required. A static access token expires; the code refreshes via the official OAuth endpoint and encrypts any rotated refresh token in `cloud_data/tiktok_token.enc`. Never commit a plaintext token. `DRAMA_TOKEN_KEY` must be a Fernet key that you generate once. One browser-only way is to run this **inside a new GitHub Codespace terminal**, after `pip install cryptography`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy that output into the GitHub Action secret `DRAMA_TOKEN_KEY` and keep a secure backup. **If you lose or replace this key, the encrypted TikTok token vault cannot be recovered without re-authorizing TikTok.**

**Default skip logic:** Missing YouTube/Facebook/TikTok permissions are recorded separately; one platform cannot quietly impersonate another and an interrupted in-flight upload is blocked for manual reconciliation rather than blindly reposted. If accounts are later connected, the scheduled job can backfill previously staged episodes.

## 3. Test online

1. In GitHub, open **Actions → 03 - AI Drama Cloud Studio → Run workflow**.
2. The run first installs CPU Kokoro and FFmpeg. The first model download may be significant; GitHub caches Hugging Face model weights for future runs.
3. The workflow creates **only one episode per run**. After it completes, open **Artifacts → drama-cloud-preview-[run]** to inspect the MP4.
4. Open `cloud_data/episode_queue.json` in the repository for a status per platform. `staged` means an upload was submitted/accepted by the API, **not proof the video was made publicly visible or that TikTok editing was completed**.
5. After the test, the next runs are automatically scheduled for Cairo local time, including local clock changes.

## 4. Turn on direct public uploads (optional)

Once you have reviewed the quality and understand it is *automated production, not manually approved animation*:

* Change `cloud_config.json`: `platform_modes.youtube` = `public` and `platform_modes.facebook` = `PUBLISHED`.
* Add GitHub Actions secret `DRAMA_ALLOW_UNREVIEWED_PUBLIC` with value `true`.
* TikTok Direct Post is a separate advanced API setup; do **not** enable it just because the `video.upload` permission works. The developer app must have `video.publish` approval and eligible public visibility. The system will not bypass this using third-party tricks.

**Important:** Changing a mode later does not automatically turn previously uploaded private/draft items public. Existing uploaded items need to be published through their platform interface or the appropriate separate API workflow.

## 5. Practical cost/quality limits

* GitHub Free includes **2,000 Actions minutes/month and 500 MB artifact storage** for private repositories at the time this guide was prepared; other plans may differ. You must stay within available free allowance; if exceeded without billing, jobs may stop until the allowance resets. GitHub Models has a separate limited free tier with rate limits. Actual daily render time cannot be guaranteed.
* CPU animation is **2D motion-comic** with stable cast designs, not full talking/acting animation, and may look very simple until higher-quality approved character references are substituted. It does **not** call Pollinations or Edge TTS, avoiding their old HTTP 400/402/403 dependencies.
* No live OAuth connection, real TikTok developer audit, Meta app review, or GitHub Actions cloud run has been performed as part of this packaged update. All three platform upload adapters were checked only by mocked tests. Use the first manual cloud run to expose any live integration issues.
* TikTok inbox uploads are **not public TikTok posts** until the user follows the notification and confirms posting in TikTok.
* Real YouTube and Meta uploads have quotas and app requirements, and scheduled jobs can start late.
* The original 10+ episode rule and exact two-starter order are unchanged. A separate future step is needed to safely automate new weekly-trend seasons with fresh cast and voice profiles.

## Useful official reference pages

* GitHub scheduled workflow timezone: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onschedule
* GitHub Actions billing and free allowance: https://docs.github.com/en/billing/concepts/product-billing/github-actions
* GitHub Models: https://github.blog/ai-and-ml/llms/solving-the-inference-problem-for-open-source-ai-projects-with-github-models/
* YouTube uploads: https://developers.google.com/youtube/data/reference/rest/v3/videos/insert
* Meta Page Reels publishing official collection: https://www.postman.com/meta/facebook/documentation/r56bjfd/facebook-api
* TikTok Inbox Upload API: https://developers.tiktok.com/docs/en/content-posting-api-reference-upload-video
* TikTok Direct Post (different permission): https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post
