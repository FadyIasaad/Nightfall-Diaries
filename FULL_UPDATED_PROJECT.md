# Full update V4.1 — Auto Upload Preference

The prior V4 was preview-only by default. V4.1 makes automatic video creation **and upload** the default for both the manual button and the 10 AM Cairo daily GitHub Actions schedule. Preview remains optional. Public posting on YouTube/Meta is enabled only after the explicit account-owner `DRAMA_ALLOW_UNREVIEWED_PUBLIC=true` secret; otherwise the **same generated video** is submitted as private/draft, if permissions are available.

TikTok supports creator Inbox flow with `video.upload`. Direct Post with public visibility requires separate approval (`video.publish`), audit and creator consent and is not implemented here. There is no promise that any service will accept uploads without authorized accounts. Unknown upload results are held for reconciliation to avoid duplicates. The free 2D cinematic illustration engine, locked voices, cast continuity, starter 22 episodes, trend-driven new seasons, and cloud-only operation remain unchanged.

See `AUTO_PUBLISH_SETUP_AR.md` for setup, `README.md` for behavior, `CLEANUP_GUIDE.md` for cleanup.
