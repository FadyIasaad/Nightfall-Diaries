# E01 continuous zero-budget production: automatic until complete (13 Nov 2026)

## What the owner explicitly authorized

Produce original **The Last Little Fox — E01**, with **14 distinct story scenes** and target **150 seconds** (absolute final technical gate **120–180 seconds**), from the original cinematic Ember reference and locked Kokoro voices. Continue automatically from saved genuine AI clips, use **ONE registered Hugging Face Free account**, no paid services, no user's computer and no repeated manual clicking. After a complete film exists, automatically stage a private YouTube copy for review, and never misrepresent a partial episode as published.

## Existing actual evidence

- Manual authenticated run [#43353270078](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/43353270078) generated an actual 5.04-second E01 sub-shot and saved a real cumulative asset + hashed progress manifest. Current verified position: **1/36 genuine shots, next scene 1 / part 2 (5s)**.
- The old `PAUSED_FREE_QUOTA E02` GitHub summary was a unit-test fixture, not real E02 production; fixed in merged PR #42.
- The 36 sub-shots total 150 seconds. Each is a **unique actual LTX-2.5 inference**, no still slideshow, repeats, frame-holds or video speed stretching.
- Per the official ZeroGPU documentation, registered **Free** users have **5 GPU minutes/day**, with **xlarge charging 2×** against daily quota. Each real run must confirm `whoami.isPro == false`, zero paid overquota, and sufficient remaining Free quota before inference. If insufficient, pause until the next scheduled run. **Do not create alternate accounts, buy credits or automatically upgrade.**

## New automatic behavior (no owner setting needed after merge)

At **10:00 every day, Africa/Cairo**, the existing GitHub Actions workflow:

1. Restores the **latest cumulative** MP4 and SHA-256 progress manifest from the Actions cache (with a 30-day rolling artifact as backup). A wrong checksum, missing media, changed original story/image, or missing predecessor blocks rendering instead of restarting silently.
2. Attempts **no more than ONE unique new shot** from the same registered **Free** HF token and the actual previous shot's last frame. When quota is insufficient, it preserves progress and retries at the next Cairo schedule. This continues without manual GitHub clicks while 36 shots are incomplete.
3. Once all **36 real clips** exist, immediately stops all future GPU requests and automatically passes the 14 original scenes to the **CPU-only** assembly stage using Kokoro WAVs (14 lines), FFmpeg, 24fps 9:16 H.264/AAC and the mandatory **120–180 second** technical gate. Assembly is idempotent, so subsequent runs never re-render complete scenes.
4. Archives a genuinely complete but **unapproved** MP4 in the `nightfall-e01-full-real-film-awaiting-lipsync-review` Actions artifact, plus all original hashed sub-shots, voice files, progress and receipt in the cumulative artifact. Any failure stays identified; **green CI or scene progress does NOT mean a finished film**.
5. If full MP4 technical gates pass and official YouTube OAuth read-only account identity preflight identifies **exactly one channel**, attempts **once** to upload the video with `privacyStatus=private` as an **unapproved review copy**. If token scopes/accounts are wrong, the status records the blocker and retries the read-only preflight on later daily runs. If an actual upload request might have succeeded but its receipt is missing, it **never automatically retries**, preventing duplicate videos.
6. Does **not** publicly publish to YouTube, Facebook, Instagram, or TikTok, and never marks real animal-mouth **lip sync** or owner cinematic approval true on the basis of technical duration alone. Public posting remains blocked by separate quality gates plus verified platform credentials and correct destination. The old YouTube `channels.list` check gave 403, Instagram gave 400 and TikTok token was missing; these are unresolved.

## Durable safeguards

- Avoid indefinite computer/manual file uploads: everything is GitHub-hosted and triggered by its existing Cairo schedule.
- Preserve a single growing SHA-256 manifest; re-download the last cumulative ZIP when cache expires. Rolling new artifacts each daily run refresh retention.
- Exactly one model call per successful daily scheduled run, and no calls if all shots are complete.
- Failed free-provider requests do not trigger rapid paid retry loops; they resume only with next daily free-quota check.
- YouTube stage is PRIVATE, never public, has a one-attempt duplicate guard and requires a technically complete 120–180s MP4 **and all 14 real Kokoro voices**. Private upload is *not* a finished approved public episode.
- Do not expose HF/YouTube credentials in logs or reports. Fine-grained token may require **Billing → Read billing usage and payment method status** for read-only ZeroGPU quota checks, never payment permission.

## How to inspect

- [Nightfall GitHub Actions](https://github.com/FadyIasaad/Nightfall-Diaries/actions) — daily `studio` run.
- `nightfall-e01-cumulative-real-shots` — genuine incremental MP4s and manifest.
- `nightfall-e01-full-real-film-awaiting-lipsync-review` — appears **only when a complete 120–180s technical MP4 is actually available**.
- Final private YouTube URL, if accepted, appears in the GitHub Job Summary and receipt. A failed YouTube identity check leaves video only in GitHub artifacts until scopes are fixed.

**Not yet proven:** enough free GPU quota and model visual continuity to finish 35 additional unique sub-shots, quality of multi-character acting, correct mouth-to-voice lip-sync, valid YouTube channel OAuth, or any public upload to Facebook/Instagram/TikTok. Scheduled completion is not a time guarantee.

References:
- https://huggingface.co/docs/hub/spaces-zerogpu
- https://developers.google.com/youtube/data/reference/rest/v3/videos/insert
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
