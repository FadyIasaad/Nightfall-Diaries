# Setup Guide — Nightfall Diaries

This channel needs its **own** Google Sheet, its **own** Gemini API key (or you can reuse one),
and its **own** YouTube OAuth client tied to the Nightfall Diaries channel/Google account. Nothing
here touches any other channel's sheet, repo, or credentials.

## 1. Create the GitHub repo

Create a new (can be public, GitHub Actions is free on public repos) GitHub repository and push
everything in this folder to it.

## 2. Create a new Google Sheet

1. Create a new, blank Google Sheet. Copy its ID from the URL
   (`https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`).
2. Create a Google Cloud service account with the Sheets API and Drive API enabled, download its
   JSON key, and **share the Sheet** with the service account's email address (Editor access).
3. You'll add the Sheet ID and the full JSON key as GitHub Secrets in step 5.

## 3. Get a Gemini API key

Get a key from Google AI Studio. You can reuse an existing key if you already have one from
another project — it's just an API credential, not tied to a specific channel.

## 4. Create a YouTube OAuth client for THIS channel

This is the one step that must be done fresh, on the Google account that owns the Nightfall
Diaries YouTube channel:

1. In Google Cloud Console, create (or reuse) a project, enable the **YouTube Data API v3**.
2. Create OAuth 2.0 credentials of type **Desktop app**. Note the Client ID and Client Secret.
3. On your own machine (not in GitHub Actions), with Python installed, run:
   ```
   pip install google-auth-oauthlib
   YOUTUBE_CLIENT_ID=xxx YOUTUBE_CLIENT_SECRET=yyy python get_youtube_refresh_token.py
   ```
4. Open the printed URL **while logged into the Nightfall Diaries Google/YouTube account**,
   approve access, copy the final redirect URL back into the terminal, and the script prints a
   refresh token. Save it.

## 5. Add GitHub Secrets

In the repo: Settings → Secrets and variables → Actions → New repository secret.

| Secret | Value |
|---|---|
| `GOOGLE_SHEET_ID` | the Sheet ID from step 2 |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | the full service account JSON key, pasted as-is |
| `GEMINI_API_KEY` | the key from step 3 |
| `YOUTUBE_CLIENT_ID` | from step 4 |
| `YOUTUBE_CLIENT_SECRET` | from step 4 |
| `YOUTUBE_REFRESH_TOKEN` | from step 4 |
| `PEXELS_API_KEY` | optional, free key — used as a backup visual source |
| `PIXABAY_API_KEY` | optional, free key — used as a backup visual source |

## 6. Run the workflows, in order

From the repo's **Actions** tab, run these manually (`workflow_dispatch`):

1. **01 - Setup Sheet Schema** — creates the `Content` and `Logs` tabs with the right columns
   and 3 starter rows.
2. **02 - Seed Content Ideas** — loads the 45 starter premises from
   `content_ideas_by_type.csv` into the sheet as `IDEA` rows (15 short, 15 horror, 15 confession).
3. **04 - Generate Story Only** — pick a `video_type`, review the generated script directly in
   the sheet before spending render time on it.
4. **05 - Generate Video Only** — renders the video for a `GENERATED` row. Download it from the
   workflow's run artifacts to preview before uploading anywhere.
5. **03 - Create and Upload Now** — runs the full chain (story → video → upload) end to end and
   uploads the result as a **private** video on the channel.

Run 04 and 05 once each before trusting 03 on autopilot — exactly like you'd want to sanity-check
any new content pipeline before letting it run unattended.

## 7. Add more story ideas later

Add new rows directly to the `Content` sheet (status `IDEA`), or add more rows to
`content_ideas_by_type.csv` and re-run workflow **02**.

## 8. Going on a schedule

Once you're happy with output quality, add a `schedule:` trigger (cron) to
`.github/workflows/03_create_and_upload_now.yml` to run automatically, e.g. daily or a few times
a week.
