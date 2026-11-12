# Nightfall E01 — cloud integration audit and one-shot free video attempt (12 Nov 2026)

**Episode:** `S01_the_last_little_fox_E01` — *The Night the Forest Burned*.

## Baseline evidence before this PR
- GitHub main Actions run #43304870139: completed successfully (tests and continuity), **no rendering**.
- 22 archived episodes exist; the expanded E01 draft has 14 scenes / 279 spoken words, with source archive preserved.
- Kaggle's last actual GPU check #43102587747 ended `KernelWorkerStatus.ERROR`. The returned report explicitly says `free_gpu_confirmed=false`, `gpu_devices=[]`, `inference_attempted=false`, and `No Kaggle GPU allocated`. PR #35 corrected read-only diagnostics, not GPU eligibility.
- Existing public Hugging Face Wan2.2 ZeroGPU `/generate_video` API returned a **read-only ready** response in prior run; GPU allocation, remaining free allowance, quality and continued access are **not proven**.
- Current final `real_film.generate` can compose motion clips with Kokoro speech, but it does not actually bind visemes/lip movements to the locked voice. **No claim of real lip-sync or Flow-grade character acting** is allowed.
- `studio/production_settings.json` has all production/quality/upload gates set to `false`.

## What this one-off PR actually does
1. `pilot/e01_pilot.py --mode audit`: verifies all 22 source episodes, E01 archive/expanded screenplay, 14 scene visual leads, SHA-256 of original on-screen character images, and exact locked Kokoro presets. Generates machine-readable reports with **no network inference or payment**.
2. For **this exact PR branch only, on the initial `opened` action**, attempts at most **one 5-second moving shot** of E01 via the existing explicitly allowed **public ZeroGPU** space; no HF paid endpoints, no retry, all social publishing credentials suppressed. If a free GPU is unavailable or quota fails, records `BLOCKED` instead of substituting still photos.
3. Downloads any successfully generated first-shot candidate into a **separate unapproved GitHub Artifact**, technical ffprobe validation only. Successful output is **not** an approved episode; no voice, lip-sync, 9:16 full-quality gate, or narrative review is claimed.
4. Builds report artifact `nightfall-e01-first-episode-integration` even when free video is blocked. It contains the 14 scene/voice/reference plan and explicit blocker status.
5. Does not modify the 22 scripts, character portraits, voice locks, automatic series policy, daily scheduling, public social credentials or production/publishing approval flags.

## Interpret the results
- `E01_SCRIPT_AND_LOCKS_VALID_MOTION_UNPROVEN`: full episode's **inputs** validated, **not** actual generated film.
- `VIDEO_CANDIDATE_UNAPPROVED`: ONE 5s motion clip was generated and passed a minimal video-track/duration check; a person still needs to compare it against the known Flow reference and inspect Ember’s left white-tipped ear, one gold scarf star, acting, light, and realistic movement.
- `BLOCKED_BY_FREE_PROVIDER_OR_QUOTA` or `BLOCKED_PUBLIC_FREE_PROVIDER`: no usable motion clip. Do not call this an episode.
- `E01_FULL_EPISODE_MP4_GENERATED` is **never** true in this experimental PR. The actual requested full 90–180s/3–6min animated episode still needs a proven free render engine, shots with character acting, locked Kokoro speech with *real* lip-sync, editing/sound, and QA.

## Key safety rule
One trial only; not retriggered on PR updates, push, schedule or other branches. Do not run a paid GPU or Agnes production request and do not enable social publishing as a workaround. Avoid confusing GitHub CI **success** with successful film creation; read the report and artifacts.


## Actual first-run result and visual QA (12 Nov 2026)

**GitHub run:** [#43306872905](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/43306872905) — CI and first-episode integration passed **91 tests**, and the first-shot test produced a real video file:
[unapproved first-shot artifact](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/43306872905/artifacts/13985075076).

**Independent MP4 inspection:** 1,188,064 bytes; **5.0625 seconds**, **H.264**, **720×832**, **16 fps**, 81 frames, **video only / no audio**. The target for a finished episode is true 9:16 at >=720×1280, target 24fps with AAC audio; this artifact does NOT pass that gate.

**Visual inspection of extracted frames at 0.25s, 1.75s, 3.15s, 4.8s:**
- Character appears as **flat, simple 2D orange cartoon**, not refined cinematic stylized CGI with fur.
- Dark forest/fire effects and some pose/scene movement exist, but acting, facial detail and continuity are poor.
- **Unwanted garbled text/title overlays** appear on the frames.
- Ear/scarf detailing is unreliable across shots; one gold scarf star is not a dependable continuity result.
- No Kokoro voices, synchronized mouth movement, sound effects, subtitles, or full 14-scene episode.
- **Decision: reject this model output as a Flow-quality proof. Do not upload or use in a finished episode.**

**Important report correction:** The automated one-shot report labeled the outcome `BLOCKED_BY_FREE_PROVIDER_OR_QUOTA` with `FileNotFoundError: 'ffprobe'`. This diagnosis was incomplete: the provider **actually returned an MP4** and it was uploaded as a GitHub Artifact, but the GitHub runner lacked the external `ffprobe` binary. The independent review above successfully probed the output. The CI job now installs free `ffmpeg` tools when needed before the next expressly authorized test. **This correction is code-only on PR update; it does NOT retrigger any additional GPU trial.**

**Final status of E01:**
- Source screenplay, 14 scenes, 5 locked cast members: validated.
- One real 5-second moving scene: generated, **visually rejected**.
- Full first episode: **NOT RENDERED**.
- Premium cinematic motion and true emotional lip-sync: **NOT PROVEN**.
- Production/public publishing: **DISABLED**.
- Kaggle GPU: still not allocated in the owner's previous actual check; no Kaggle GPU was used in this trial.

Next engine selection must pass one **visually impressive, identity-locked moving test** before scaling to 14 scenes, neural lip-sync and a complete episode. Do not relabel this 5-second demo as a full episode.
