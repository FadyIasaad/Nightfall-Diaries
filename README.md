# Nightfall Diaries V4.1 — One-Click + Scheduled Auto Upload

**Default behavior:** generate a short cinematic 2D fantasy episode in the cloud and attempt automatic uploads to all connected destinations.

**Manual:** GitHub → Actions → **03 - Nightfall One Click Auto Upload V4.1** → Run workflow → `generate_and_upload` / `auto` / `all`.

**Scheduled:** daily at 10 AM `Africa/Cairo` through GitHub Actions (delays possible).

**Visibility:** YouTube `public`, Facebook `PUBLISHED` **only when** Actions secret `DRAMA_ALLOW_UNREVIEWED_PUBLIC=true` and platform permissions allow it; otherwise they go `private`/`DRAFT`. TikTok is **Inbox upload** requiring creator to publish, not public Direct Post. These are *submission attempts*, not proof public processing finished.

**Missing permissions:** records `missing_credentials`, does not fabricate a draft. **Ambiguous failures:** records `needs_reconcile` without a blind retry. MP4 is available in Actions artifacts for 7 days. A successful upload on *at least one platform* advances the episode queue; failed platforms can be reattempted by explicitly selecting the episode after fixing permissions. This is not an automatic backfill queue.

**First series:** The Last Little Fox (12 episodes) → The Boy Who Forgot Tomorrow (10 episodes) → fresh series chosen from collected trends (10–12 episodes, where available). Locked character graphics and voice IDs. Free illustrated (not photorealistic) visuals.

Read [AUTO_PUBLISH_SETUP_AR.md](AUTO_PUBLISH_SETUP_AR.md) for step-by-step Arabic setup. See [CLEANUP_GUIDE.md](CLEANUP_GUIDE.md) for legacy cleanup after verifying the new workflow.
