# Nightfall One Click Story — verified continuation and daily fallback (13 Nov 2026)

## What was actually proven, not merely unit-tested

The owner's manual [One Click Story GitHub Actions run #43359829081](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/43359829081) used the **ONE registered free HF account**, restored the earlier original E01 5.04-second clip, generated another **distinct** AI motion sub-shot, and uploaded the cumulative original MP4/checkpoint artifact:
- Before: 1 of 36 clips, 5.04 real motion seconds.
- After: **2 of 36 clips, 10.08 real motion seconds.**
- Next clip: original scene 1, part 3. No old shot was generated again.
- 14 scripted scenes total 36 separately generated 2–5-second shots, targeting 150 seconds overall; 14 distinct Kokoro WAVs and FFmpeg assembly follow **only after all clips exist**.
- The full E01 film has **not** been rendered or published. Accurate lip sync, cinematic acting and destination access remain separately unverified.

## What the automatic workflow can legitimately guarantee

The default-branch workflow has a primary **10:00 Cairo** schedule. This PR adds a **10:17 Cairo** recovery schedule, because GitHub documents that scheduled triggers can be delayed or occasionally dropped. A persistent `last_scheduled_attempt_day` marker on the same SHA-checked MP4 progress manifest prevents the backup run from requesting a second free AI shot if the first schedule already attempted one that day.

On each eligible scheduled run:
1. Restore the cumulative original motion clips and signed-by-hash progress manifest from Actions cache or the latest cumulative artifact. **Never** start on some other episode or series silently. Do not replace images, scripts, characters or voice locks.
2. If fewer than 36 authentic AI shots are saved, check official HF Free account quota and attempt **at most one new clip per Cairo day**. If the daily quota is too small, save `PAUSED_FREE_QUOTA_INSUFFICIENT`; the workflow's next scheduled run will check again. Never use PRO, charged credits or multiple accounts.
3. At **36/36 genuinely rendered MP4s**, stop requesting GPU completely. Pass them to original 14-scene/14-Kokoro-voice CPU assembly with 120–180s MP4 technical validation. A failed assembly can be attempted on a future scheduled job without spending more GPU; media hash mismatches still block rather than replacing lost footage.
4. If the film passes technical checks and OAuth identifies one authorized YouTube channel, attempt a **PRIVATE** review copy only, with duplicate-attempt guard. This does **not** prove real lip sync or authorize public posting to YouTube, Facebook, Instagram or TikTok.
5. Report the exact saved clips, generated seconds, last completed motion time and pending shot. If the provider or token is really broken, the post-backup health step reports a **red failure**, rather than a misleading green CI; future daily schedules remain enabled.

## Remaining platform limitations, not falsely claimed away

- The current official YouTube identity check previously returned 403, Instagram 400, and TikTok token was absent. Facebook Page identity alone is not a video publishing permission.
- There is no verified public 4-platform release, no verified 120–180s E01, and no tested facial viseme/lip sync across the cast.
- GitHub scheduled jobs are **best effort**, not a continuously running service. GitHub officially warns of delayed/dropped schedules and public-repository 60-day inactivity auto-disable. The second daily schedule reduces missed slots, but cannot guarantee a job will always execute. A permanently invalid free provider token or unavailable ZeroGPU cannot be fixed by automatic retries.
- GitHub Actions artifacts are retained 30 days and caches can be evicted. Regular daily jobs refresh them. If all backups disappear, re-rendering cannot be pretended as seamless progress.
- The user is not asked for an episode ID or to click Run each day. The selected story is taken from the saved `studio/active_story.json`. **Only The Last Little Fox E01 has a working original cinematic-reference renderer right now.** The second original series and E02+ remain blocked until genuinely prepared.

Official GitHub scheduling docs:
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
