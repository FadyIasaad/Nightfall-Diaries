# Nightfall Diaries — Zero-Budget Cloud Studio

**Status (4 November 2026): Engineering foundation / quality proof not passed / public posting disabled.** This repository does **not** yet produce a verified premium animated 3–6-minute episode. No successful public four-platform upload is claimed.

The non-negotiable requirements are recorded in [MASTER_PLAN_CONTRACT.md](MASTER_PLAN_CONTRACT.md). The two original series remain unchanged: **The Last Little Fox (12 episodes)** then **The Boy Who Forgot Tomorrow (10 episodes)**. Never replace the existing YouTube channel, Nightfall Diaries Facebook Page, stores.nightfall Instagram, or the intended TikTok identity.

## One workflow, browser or phone only

Go to **Actions → Nightfall Diaries - One Free Online Workflow → Run workflow**. The action dropdown has:

- **Check setup**: validates all 22 original story files and reports current blockers without any AI-video dependencies, cloud GPU usage, or publishing.
- **Render quality proof**: tries three real-motion shots for a 15–30-second Ember/Moss dialogue-action candidate using a configured, *independently tested* free Hugging Face Gradio Space. This may fail when the provider is unavailable or the voice/motion is too short; it must never fall back to photo zooms.
- **Generate full episode**: requires an actual 400+ word, coherent full screenplay and a 180–360-second playable vertical H.264/AAC MP4. Archived E01 is currently too short, so this action refuses to waste scarce video quota.
- **Generate + Publish**: fully gated. Cannot post while the config and independent quality/platform verification fields are false.
- **Retry missing platforms**: currently fail-closed because the current receipts lack confirmed-public status and source MP4 recovery is not completed. Will not duplicate an upload.
- **Prepare episode**, **Validate stories**, **Check Instagram**: existing safe preparation and diagnostics.

The **10 AM Cairo** schedule is active as a *read-only preflight/standby*. It must not start public posting until a real visual/lip-sync proof and each official platform integration pass verification. A GitHub release, an upload response or a TikTok inbox draft is **not proof of public posting**.

## Current technical restrictions

- GitHub's normal free public Actions runner is CPU-only. There is no proven free GPU service that can deliver film-quality 3–6-minute daily character animation indefinitely. The optional Hugging Face endpoint is not guaranteed.
- Kokoro neural speech is implemented, but differentiated emotions, facial/lip synchronization, soundtrack and full cinematic action are **unproven**.
- Tracked cloud character images exist and are now used per character. These are reference images, **not rigged, professionally animated models**.
- The original E01 script has only brief scene outlines, not 3–6 minutes of dialogue/storyboarding.
- YouTube, Facebook, Instagram and TikTok publishing still need separate official API, visibility and idempotency proofs; no manual upload substitute is permitted.

**Next engineering gates:** expand E01, lock neural voices and acting references, produce a watchable 15–30-second cinematic body-action/lip-sync proof within free resources, render full pilot, then independently verify each publisher. Publishing remains off until the requirements are met.
