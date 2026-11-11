# Kaggle Free T4×2 GPU — Nightfall Diaries manual proof path (2026-11-11)

**Status: implemented as a manual, private, single-run experiment. NOT yet proven on the owner's Kaggle account.** There is no guaranteed 30h/week entitlement or proven Flow-grade output.

## Verified services and constraints

- Kaggle's official [GPU guidance](https://www.kaggle.com/docs/efficient-gpu-usage) says the free weekly GPU quota is generally **30 hours or sometimes higher**; it varies with account/demand and may be exhausted. Check your **own Kaggle account's notebook GPU quota**. No automatic quota bypass.
- Official Kaggle [announcement](https://www.kaggle.com/product-announcements/735239): **P100 retired September 15, 2026**. Request **T4×2** using CLI accelerator `NvidiaTeslaT4`, not P100. Each T4 has only 16GB independent VRAM; **2×16GB is not one 32GB GPU**.
- The [Kaggle CLI](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md) supports push/status/output for scripts. It can be used from GitHub without running a laptop.
- The proposed lower-memory [LTX-Video 2B family](https://github.com/Lightricks/LTX-Video) has publicly accessible weights, but **open weights ≠ unrestricted open source**; the [LTX license](https://huggingface.co/Lightricks/LTX-Video) must be reviewed for commercial use. This proof is **not approved for publication**.
- Official [Wan2.2 TI2V-5B](https://github.com/Wan-Video/Wan2.2) documents **24GB on a single GPU**. Do not claim Kaggle T4×2 can run it without a separately proven parallel/quantized path.

## Added implementation

- Existing **single** `.github/workflows/nightfall.yml` gets **Kaggle GPU check** and **Kaggle Ember proof** manual-only choices. Schedule, publish switches and main production paths are untouched.
- `studio/kaggle_bridge.py` verifies the **original Ember PNG SHA-256** before staging and embeds the bytes in a **private** Kaggle script, so no Kaggle Dataset/image re-upload is required. It submits a single Kaggle notebook via CLI, polls status, and retrieves a diagnostic report and optional candidate MP4.
- `kaggle/nightfall_gpu_job.py` executes a real CUDA calculation in the free GPU session and writes `nightfall_kaggle_report.json`. GPU check does **not** download a large video model.
- **Ember proof** (only by separate manual click) downloads original LTX-Video weights via public Hugging Face and tries a **49-frame / ~2-second 320×576 vertical** motion smoke-test, using CPU offload and FP16 on T4. This deliberately **does not meet final 720×1280 or 90–180-second episode specs**, and may fail due to memory, network, model/pipeline mismatches, or your GPU quota. It is only a first feasibility measurement, not a cinematic quality success.
- Nothing uses a billed inference API. The trial uses your **own Kaggle free quota**. There is **no third-party auto-upgrade** logic, zero publishing, and no job retries.
- Successful runs return the JSON report and, for the video trial, MP4 as short-lived **GitHub Actions Artifacts**. The Kaggle notebook itself is private, with no automatic public posting.

## One-time cloud setup (not required every episode)

1. At [Kaggle settings/API](https://www.kaggle.com/settings/api), create a new Kaggle **API token**, and ensure your Kaggle account can use Notebook GPU sessions. Kaggle might require account/phone verification. Inspect the actual weekly quota in Kaggle first.
2. In [Nightfall GitHub Actions secrets](https://github.com/FadyIasaad/Nightfall-Diaries/settings/secrets/actions), add **Repository secret** `KAGGLE_API_TOKEN` with the token **value**; never commit or post it. This is a Kaggle token, **not** the `kaggle.json` file.
3. In GitHub **Settings → Secrets and variables → Actions → Variables**, add `KAGGLE_USERNAME` using the **Kaggle profile slug** (not a display name or GitHub username).
4. Review and merge the PR. In **Actions → Nightfall Diaries - One Free Online Workflow → Run workflow**, choose **Kaggle GPU check**. It requests a private T4 GPU notebook once. It will refuse submission if the token is absent.
5. Open the **nightfall-kaggle-t4-report** artifact. Require `GPU_TEST_PASSED_NO_VIDEO_GENERATED` and inspect GPU name/VRAM.
6. **Only if the GPU check passes**, run **Kaggle Ember proof** and download the **nightfall-kaggle-ember-unapproved-mp4** artifact, if generated. Assess the actual motion, face/scarf/ear identity, fur and lighting before moving to a higher-quality candidate. Neither mode touches social accounts.

## Safeguards and limitations

- **No publication**, no changes to S01/S02 canon, voice locks, or public account credentials. Locked Kokoro voice and lip-sync **are not attempted** by this GPU proof.
- No assumption that T4x2 is available on the owner's Kaggle account. If Kaggle responds GPU unavailable, quota exhausted, account unverified, or notebook times out, the result is **BLOCKED**; do not switch to a paid accelerator.
- Failed/aborted Kaggle notebook might remain visible in Kaggle Sessions; check your sessions to terminate an unexpected lingering run.
- If it fails, the GitHub Action should expose a failure and report; **do not claim completion** because a Kaggle CLI command returned success.
- The first LTX trial produces a deliberately small smoke clip; **it cannot be used as a substitute for the desired Flow-grade animated film**.
- Model downloads require Kaggle Notebook internet. If Kaggle refuses external access, leave it blocked and use a legitimate Kaggle Models or Dataset attachment in a later tested PR instead of bypassing restrictions.
- **Next gates:** test a viable higher-resolution image-to-video renderer, preserve Kokoro WAVs with true animal-face lip-sync, then benchmark the **entire** 90–180 second episode across the real free quota before enabling unattended production.
