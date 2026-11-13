# One-click Nightfall story name — no episode ID

## How to run (one button, one story field)

Open [Nightfall GitHub Actions](https://github.com/FadyIasaad/Nightfall-Diaries/actions) and select **Nightfall - One Click Story**.

Click **Run workflow**, choose `main`, and type the story title in the ONLY input `story`. It defaults to **The Last Little Fox**, so the user can run it without typing an episode ID or changing other options. Click **Run workflow**.

Accepted story titles (including selected Arabic aliases):
- **The Last Little Fox** (الثعلب الصغير الأخير) — the validated resume path for E01, original `S01_the_last_little_fox_E01`
- **The Boy Who Forgot Tomorrow** (الولد الذي نسي الغد) — recognized and saved, but not eligible for cinematic inference yet, because no approved motion engine/reference/expanded production screenplay exists for this story. It will report **BLOCKED_UNPREPARED_EPISODE_NO_GPU_NO_UPLOAD**, without spending Free GPU minutes or fabricating a film

The selected story ID/title is saved to `studio/active_story.json` on `main` (not a secret). Subsequent daily 10:00 **Africa/Cairo** GitHub runs automatically read that selection. No need to enter `S01_the_last_little_fox_E01` or other episode IDs; the router checks each series' immutable `episodes/episodes.json` and selects the first episode **not fully publicly delivered**. A YouTube PRIVATE review copy is **NOT** a published episode and does not automatically advance to a new episode.

## Resume behavior (currently tested only for The Last Little Fox E01)

The workflow restores the existing SHA-locked `nightfall-e01-cumulative-real-shots` cache/artifact and picks the **next genuinely unfinished part**. The actual authenticated run #43353270078 produced **scene 1 / part 1, 5.04 real seconds (1/36)**. The next eligible shot is **scene 1 / part 2 (5 seconds)**. It must not re-render part 1 or reset the original story.

Each scheduled run sends at most **ONE LTX-2.5 call** using the same personal registered Free Hugging Face account, only after free-tier/quota checks. If quota is insufficient, it preserves all clips and tries again next Cairo day. No extra accounts, paid services or hidden usage.

After 36 distinct AI shots totaling approximately 150 seconds exist, the separate CPU-only step assembles all 14 original scenes with 14 locked Kokoro WAVs and checks 120–180s, H.264, AAC and 9:16. A technically complete video is archived as **UNAPPROVED** until actual character acting and accurate lip-sync receive review.

If official YouTube OAuth identity works and the entire technical video exists, the existing pipeline attempts **ONE PRIVATE review copy** only, with duplicate guard. It cannot promise publication to YouTube, Facebook, Instagram or TikTok: YouTube previously returned 403, Instagram 400, TikTok token was missing, and true character lip-sync has not been proved. Publishing to the public stays OFF.

## Why a separate, simpler workflow?

The original `Nightfall Diaries - One Free Online Workflow` still has many technical/diagnostic options and an episode field. These remain for advanced manual debugging only. **Nightfall - One Click Story** is the main user interface with exactly one story-title input. The older workflow's scheduled E01 GPU steps are disabled to prevent duplicate daily requests and quota use. Other quality/publication safeguards are unchanged.

The workflow's source code/tests and the actual 150-second film are different claims: passing offline tests does not mean an episode has rendered. The current E01 completion date depends on legitimate free ZeroGPU availability and is not guaranteed.

## Security and longevity

- Only two immutable story manifest titles and explicit aliases are accepted; unknown names abort safely.
- The current chosen series is persisted to `main` using GitHub's token with `contents: write`; it is not guessed from a prior chat. Schedule reads this same persisted selection.
- MP4 clips remain in cumulative Actions cache and 30-day refreshed artifacts; if both are evicted, no fabricated completion is allowed. All historical SHA-256 checks remain enforced.
- The one-click workflow and regular scheduled workflow share the exact same concurrency group `nightfall-production`, preventing concurrent GPU races.
- No user PC, manual video upload, free-account rotation, new story canon rewriting, or changes to the real public publishing gate.
