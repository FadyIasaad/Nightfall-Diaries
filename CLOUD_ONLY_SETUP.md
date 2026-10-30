# V4.1 Cloud-Only Setup

See `AUTO_PUBLISH_SETUP_AR.md` for full Arabic step-by-step instructions.

Manual button: `03 - Nightfall One Click Auto Upload V4.1`, mode `generate_and_upload` (default), episode `auto`, destinations `all`.

Scheduled cloud operation: 10:00 Africa/Cairo daily (`timezone` on `on.schedule`). Disable older video-generating workflows to prevent duplicate posts. GitHub may delay a scheduled job and free quotas may stop it.

Auto visibility: YouTube public and Facebook PUBLISHED only with `DRAMA_ALLOW_UNREVIEWED_PUBLIC=true` Action secret plus actual API approval. If that secret is absent, automatic preventive fallback to YouTube private and Facebook DRAFT. TikTok inbox only. OAuth credentials are still required for all platforms. Missing credentials means **no remote upload**, not a draft.

Never commit plain API credentials. Keep existing `cloud_data/` queue and token vault. Read receipt status before retrying (`needs_reconcile` might have reached the platform).
