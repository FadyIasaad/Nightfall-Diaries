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


## 2026-11-11 consolidation: serialized Kaggle production, independent PR checks

Previously all GitHub events shared one `concurrency.group` with `cancel-in-progress: false`, so a queued PR validation run could occupy the same group as a manual Kaggle test. The current PR separates:
- PR verification by PR number (new revisions cancel superseded PR checks).
- Normal push validation in its own `push-check` lane.
- Scheduled/manual/Kaggle operations in one serialized `production` lane.

Before any private Kaggle kernel is submitted, the manual workflow now checks the `KAGGLE_API_TOKEN` secret and `KAGGLE_USERNAME` variable, then performs `kaggle kernels list --mine --page-size 1` (read only, no GPU). The Kaggle CLI `six` import and `kernels push --help` preflight introduced in merged PR #31 are retained. The Kaggle actual GPU quota **cannot** be checked by this read-only list and remains to be proven by a manual GPU test.

**Not solved by code:** a GitHub Actions run reporting `Queued` with **zero jobs**, or dynamic Pages `startup_failure`, can be due to GitHub service scheduling or account-level restrictions. No code-only PR can guarantee it will start a hosted runner. Existing queued runs may need cancellation from **Actions** UI; merged PRs cannot be canceled or retroactively undone. Pages deployments are managed independently by GitHub Pages settings and not by this Nightfall workflow.

To clear old queued runs manually, visit their individual Actions run pages, use **Cancel workflow** on stuck runs (if offered), and use **Run workflow → Kaggle GPU check** only once after the PR is merged. Never activate automatic generation/public publishing to test runner scheduling.


## 2026-11-11: Debugging the first actual Kaggle worker error (run #43102587747)

The first authenticated GitHub Kaggle run **did reach Kaggle**:
- `kaggle kernels list --mine` authentication passed using the stored secret.
- `kaggle kernels push` created **version 1** of the private notebook at
  `https://www.kaggle.com/code/fadyasaadnightfall/nightfall-t4-ember-safe`.
- The remote status was `KernelWorkerStatus.ERROR`, **not** a Kaggle CLI
  import failure. GitHub previously stopped without downloading the worker
  logs, so this alone does **not** establish missing quota or GPU availability.
- No visual clip or validated CUDA report was returned.

The existing single GitHub Actions workflow now offers **Kaggle diagnose last run**:
1. Run this action after merging this PR, not `Kaggle GPU check`; it does
   **not** push a new kernel version or consume another GPU session.
2. It authenticates to Kaggle using the existing `KAGGLE_API_TOKEN` secret,
   reads `kaggle kernels status`, `kaggle kernels logs`, and tries downloading
   any existing kernel output files with `kaggle kernels output`.
3. Get the GitHub Actions `nightfall-kaggle-t4-report` artifact, and inspect
   `kaggle_diagnostic.json` plus `kaggle_worker_logs.txt` (when available).
4. If the logs report no GPU, account restriction, worker startup failure,
   Python import error, or other root cause, fix **that exact failure** before
   running another GPU test. No automatic retry, paid fallback or publication.

When an ordinary Kaggle GPU check or Ember proof fails **after submission**,
the bridge also attempts the same read-only log capture automatically. If Kaggle
does not return logs, the status remains blocked and the Kaggle Notebook UI
is the next source of evidence. **GitHub success does not imply GPU success.**


## 2026-11-11: Findings from the owner's uploaded Kaggle diagnostic ZIP

The **actual** `nightfall_kaggle_report.json` from the owner's GPU check says:

```json
{
  "result": "BLOCKED",
  "error": "No Kaggle GPU allocated; verify account GPU access/quota",
  "free_gpu_confirmed": false,
  "gpu_devices": [],
  "inference_attempted": false
}
```

The existing `kernel-metadata.json` requests `enable_gpu: true` and
`machine_shape: "NvidiaTeslaT4"`, which is the **official T4×2** identifier:
[Kaggle kernel metadata reference](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels_metadata.md).
**Do not switch to P100 or assume two T4s combine into 32GB on one device.**

The uploaded diagnostic showed `kaggle kernels output` returned both
`nightfall_kaggle_report.json` and `nightfall-t4-ember-safe.log`; however
the original script attempted `kaggle kernels logs` (unsupported in the
installed **1.8.4** CLI), and the GitHub artifact ignored the downloaded
`.log`. This PR fixes diagnosis to **read the actual worker log from
`kernels output`**, sanitize it, and save a bounded
`kaggle_worker_logs.txt` file.

A second **read-only** check calls `kaggle kernels pull -m` to inspect
Kaggle's committed `enable_gpu` and `machine_shape` for the existing
notebook. It downloads code into a temporary directory and **does not push
or run** the kernel. Future GPU probes also record `nvidia-smi -L`,
`torch.version.cuda`, `torch.cuda.is_available()` and device count before
failing, to distinguish worker allocation from a Python CUDA mismatch.

**Next step, without using another GPU session:** After CI and merging,
run `Kaggle diagnose last run` once and read the updated artifact.
If remote metadata has `enable_gpu=false`, this is a configuration
mismatch. If it says T4 is enabled but no GPU was visible to the worker,
check the owner's Kaggle Notebook **Settings → Accelerator** and GPU quota/
account eligibility, or Kaggle-side availability; the GitHub workflow
cannot grant GPUs. Do not attempt the Ember film until a separate real
CUDA probe has passed.
