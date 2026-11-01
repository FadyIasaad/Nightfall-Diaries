# Nightfall Diaries — Lean Cloud Rebuild

**Safety-first replacement pack** for the existing `FadyIasaad/Nightfall-Diaries` repository. One GitHub Actions workflow; no PC needed to run; preview and read-only account checks only by default.

## What this version really does
- Uses the repository's **original E01–E12 and E01–E10 authored scripts** from its preserved Git history (commit `02f426cb9af1276d78465ff1ec1dbf190153f160`). It DOES NOT rewrite your original scripts. This requires retaining the same GitHub repository/history. Use `git fetch` and `git show` to restore the exact files into each runner. If you create a completely new repo, the restore step will fail.
- Renders **actual moving 3D meshes** using Blender (character locomotion, turns, facial mouth animation); basic stylized procedural artwork, **not Pixar-level character animation** and not the licensed KAI model. No claim of cinematic-grade output.
- Narration uses the open-source system `espeak-ng` voice for a zero-cost fallback. It is robotic, unlike the original Kokoro voices; high-quality TTS is still future work.
- A single manual workflow offers `preview`, `check_instagram`, and `review_publish_config` (configuration audit only). It **does not upload** videos because there is no production-safe proven end-to-end authorization for all four channels yet. No accidental posting.
- Existing platform secrets stay in repository settings (deleting repo files does not normally delete Actions secrets). No secrets shipped.
- No new series is automatically started. The next-series selection requires your approval.

## Important upload instructions
1. **Before deleting anything**, download a backup of the existing repository at GitHub > Code > Download ZIP. Do not delete the repository or its history.
2. Keep the **same repository**. Delete only repository files (not the repository itself); upload the contents of this ZIP into its root, preserving `.github/workflows` and folders. GitHub web uploader may hide dot folders or reject large folder uploads; GitHub Desktop, web editor or GitHub's Add file > Upload files can be used carefully.
3. Navigate to Actions > `Nightfall Cloud V5 - Safe Studio` > Run workflow, select `check_instagram`. Check its logs. Never post a token in an issue or chat.
4. Next choose `preview` and episode `S01_the_last_little_fox_E01`; a rendered MP4 is available under the run's **Artifacts**.
5. `review_publish_config` checks only for secret presence without exposing values or making posting calls.

## Limitations / not ready yet
The code in this pack does **not** auto-publish to YouTube/Facebook/Instagram/TikTok, and its visuals are procedural rather than a finished studio-quality animated cast. This is a safe tested starting point and cannot honestly be called finished production-ready V5.

**Existing Instagram token:** Unified Login SUAT, expected `graph.facebook.com`. The read-only check tries the supplied Instagram Account ID against Graph v25.0; Meta may still deny access. A debugger showing `Valid: True` does NOT prove the token grants account-level access. Do not regenerate credentials blindly.
