# AI Drama Universe V3 — Browser-only cloud setup

**No PC running needed after initial browser setup.** Uses GitHub Actions hosted machines. Keep the current repo **private**.

### 1. Merge into your existing repo

- On GitHub, open the original project (for example Nightfall-Diaries). If it has a different name, that is fine.
- Click **Code → Codespaces → Create codespace on main**. Browser terminal opens.
- Upload `AI_Drama_Universe_Cloud_V3_Complete_Project.zip` through the Codespaces Explorer, then inside Codespaces use:

```bash
unzip -o AI_Drama_Universe_Cloud_V3_Complete_Project.zip
cp -a AI_Drama_Universe_Cloud_V3/. ./
```

- Inspect differences with `git status`. **Merge carefully; do not overwrite hand-edited project code or existing secrets.** The new cloud script is independent of previous `generate_video.py`.
- Disable old scheduled workflow files via GitHub Actions or remove their scheduled triggers; leave the new V3 workflow enabled.
- Commit in the Codespaces terminal:

```bash
git add .
git commit -m "Upgrade to cloud-only AI Drama Universe V3"
git push
```

(The ZIP is not stored in the repo; remove it after copying.)

### 2. GitHub Actions settings

- Repository **Settings → Actions → General**: Actions enabled; `GITHUB_TOKEN` has read/write repository access.
- Actions may be delayed and can be disabled by GitHub on long-inactive repos.
- Schedule uses local timezone `Africa/Cairo`, every day at **10:00** with a valid timezone-aware cron.
- A run generates exactly one episode. A failed run can be rerun without skipping the unfinished episode.
- The first run must download Kokoro models and may be resource-heavy. Free GitHub Actions minutes, artifacts and models availability are not unlimited.

### 3. Publish credentials one destination at a time

**YouTube:** Configure OAuth through Google Cloud for the exact existing YouTube account/channel and obtain refresh token legally via consent flow. Add secrets `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`. Add repository variable `YOUTUBE_EXPECTED_CHANNEL_ID`. An OAuth token with only upload-only scope may not be sufficient for channel-ID verification; authorize the required read scope as well. If you cannot get Google Cloud OAuth credentials without a payment method, leave YouTube disconnected: download the MP4 from GitHub Actions and upload manually. No bypass is provided.

**Facebook:** Use an authorized Meta developer app with Page permissions for the existing Page. Add `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN`. The adapter uses Meta Page Reel start/upload/finish with DRAFT. If Meta disallows that Page/app, download the MP4; **no draft is created without permission**.

**TikTok:** Register developer app with approved `video.upload` and creator OAuth. Add `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REFRESH_TOKEN` and a one-time-generated Fernet secret `DRAMA_TOKEN_KEY`. The workflow saves **encrypted** rotating refresh credentials in the private Git repo and sends content to TikTok inbox for creator confirmation. Without TikTok authorization, no inbox upload happens. Direct public posting is intentionally not implemented.

### 4. Preview first and approve your quality

Run **Actions → 03 - AI Drama Cloud Studio V3 → Run workflow**. Download the MP4 under **Artifacts** (retention 7 days). `cloud_data/episode_queue.json` shows progress. Current saved image assets are original **simple cartoons**, not 3D or Pixar-equivalent. The default upload options do not expose videos publicly.

To upgrade a character card to an approved image, upload a PNG within the repository and in a Codespace run:

```bash
python -m studio.approve_art S01_the_last_little_fox s01_ember approved_art/ember.png
```

This writes the image to the permanent character directory and refreshes its locked SHA256. For voice approval, listen to the generated `cloud_audition.wav` and use:

```bash
python -m studio.approve_voice S01_the_last_little_fox s01_ember
```

**Note:** Voice samples only appear after that speaker has appeared in a rendered episode. You do not need to approve them to use private/draft uploads; **public** mode is gated until approval.

### 5. Understand statuses

- `rendered`: MP4 created and checked; not necessarily uploaded.
- `missing_credentials`: Service not connected. You can download the rendered MP4 artifact for manual posting.
- `staged`: Submission accepted by remote API, **not proof of public visibility**.
- `inflight` / `needs_reconcile`: uncertain. Check platform Studio before any manual retry to avoid duplicate posts.
- `pending_series_generation`: No fresh eligible real trend available; next scheduled run will retry safely.

### 6. When first two series end

The engine has **22 saved outlines and 22 prewritten scripts**. After S01 episode 12, start S02 episode 1. After S02 episode 10, rank up to seven days of real observed trends. Choose an eligible concept (not a current celebrity story or a tragedy); generate next season with 10–12 episodes, new character portraits and a new consistent voice allocation; continue daily. If RSS is down or no eligible topic is found, wait for a verified trend rather than make one up.

### 7. What remains external

Access/approvals for GitHub, OAuth for 3 social apps, and a live GitHub Actions run. This package does not contain any owner token, automatically grant developer permissions, or promise $0 unlimited cloud AI generation. **The user's account credentials are never included in this ZIP.**
