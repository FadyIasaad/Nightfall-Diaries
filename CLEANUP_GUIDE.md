# CLEANUP: what to remove and what to keep

**Do not bulk-delete your existing repository.** The following are candidates **only if they exist in your actual repository**. Your current GitHub repository may contain files added after this package was prepared. The cleanup recommendations are based on V3 source and the old workflow filenames discussed, not a verified live inventory of your private repository.

## Step A — Disable immediately (before first V4 run)

Under **Actions**, disable every older video/post workflow (if present), especially:

- `.github/workflows/03_drama_cloud_full_online.yml` — the old V3 cloud studio.
- `.github/workflows/03_create_and_upload_now.yml` — old direct-public upload workflow.
- Other older workflows that automatically run `generate_video.py`, publish Shorts/Reels, or schedule queue checks. Search `.github/workflows/` and inspect each one.

**Disable** first, then delete later only after V4 succeeds.

## Step B — Remove old files only after verifying nothing imports them

Possible redundant legacy code files (names differ by old version):

- Old root `generate_video.py`, old video generator modules and old prompt folders, **only if they are unused by any retained workflow**.
- Old `archive_v2/`, README backup copies, `legacy_templates/` / `legacy_tools/` copies already superseded.
- Old local-PC scripts such as Windows Task Scheduler wrappers, `.bat`, `.ps1` for unattended video generation **if you no longer use them**.
- Output test MP4s and unused raw exports in root; keep any approved/licensed art assets.

Our V4 ZIP already **omits** `archive_v2/` and the V3 workflow YAML. When copying over the repo, GitHub **does not remove existing old files automatically**. Delete them manually after the successful V4 preview.

## Never delete

- `seasons/` including scripts, characters, locked voice identities and story bibles.
- `cloud_data/episode_queue.json`, `identity_locks.json`, trend history, and upload receipts. Preserving them prevents losing episodes or duplicate uploads.
- `studio/art.py` — still used by the future-series identity-reference generator.
- `studio/publish.py`, `studio/one_click.py`, `studio/video.py`, `studio/cinematic_art.py`, `studio/audio.py`, `studio/shot_plan.py`.
- `assets/scene_overrides` or `assets/approved_characters` once you've placed licensed assets there.
- GitHub repository secrets or the Facebook/TikTok/YouTube tokens you need to post.
- `04_daily_trend_research.yml` if you want the 7-day trend history to accumulate automatically.

## Keep final workflows

- `.github/workflows/03_one_click_fantasy_video.yml`: **manual video button**.
- `.github/workflows/04_daily_trend_research.yml`: **daily trend research only; doesn't publish**.

Do not delete data just to make the repository look cleaner; old uploading workflows are the main interference risk.
