# Nightfall Diaries — free-GPU speed diagnosis and compatible migration (2026-11-13)

> **Evidence hierarchy:** actual `main` code, SHA-verified MP4/manifest and GitHub Actions job logs take precedence over older guides; then the owner's creative requirements; then external model documentation. This proposal makes **no engine change, no paid call and no public post**.
>
> **Status:** Performance measurement implemented in this PR. A faster engine is **not** proven or enabled. Do not equate a green CI check with completed film or a 3–6-minute cinematic episode.

## A. What is actually running

- Core workflow: `.github/workflows/nightfall_story_one_click.yml`.
- Current active GPU provider: `Lightricks/LTX-2.5` ZeroGPU via `pilot/e01_free_resume.py`; one authenticated free Hugging Face account.
- Current real checkpoint: **3/36** shots after [Run #43439850156](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/43439850156); its job log reports `PAUSED_FREE_QUOTA_INSUFFICIENT`, one new shot, and one successful Telegram notification. Check the next run before treating 3/36 as today's latest.
- The 14-scene, 36-shot plan in `pilot/e01_full_run.py` targets **150 seconds**, below the owner's hard **180–360 seconds**. Existing `progress.json` checkpoint and model/source/plan hashes must not be rewritten without a complete, reversible migration.
- **Correct image orientation:** `client.predict(..., 1024, 576, ...)` passes **height then width**, so output is portrait 576×1024, not landscape. Keep 9:16 and validate output with ffprobe.
- The current quota preflight reserves a **conservative minimum** of 220 reported GPU seconds for a 4–5s shot, 140 for shorter parts. This is a safety threshold, not proof of actual GPU seconds consumed.
- Hugging Face states that normal Free ZeroGPU accounts receive **5 minutes/day** with a reset 24 hours after first use: https://huggingface.co/docs/hub/spaces-zerogpu .
- The real bottleneck is free GPU allocation, not the number of GitHub CPU runners or insufficient cron triggers.

## B. Direct evaluation of the suggested engines

| Option | Evidence | Action |
|---|---|---|
| FLUX.2 klein 4B | Official Apache-2.0 multi-reference image/editing model, approximate 13GB VRAM. https://huggingface.co/black-forest-labs/FLUX.2-klein-4B | Candidate for **reference still generation only**; test Ember's left white ear tip and the single gold star. A still is not animation. Load/unload separately from the video model on 16GB GPU. |
| Wan2.2 TI2V-5B stock | Official implementation requires about 24GB single-GPU VRAM. https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B | **Not directly T4-ready**; T4×2 is not a combined 32GB memory pool. |
| FastWan / optimized WanGP 480p | Third-party optimized runners exist; model compatibility and speed depend on exact checkpoint, VRAM, precision and runtime. https://github.com/deepbeepmeep/Wan2GP | **First conditional GPU benchmark candidate**, not a verified automated film engine. Test actual 5s image-to-video with the real locked reference and a headless CLI; no Gradio public tunnel or manual UI. |
| Kaggle free GPU | The repository already contains `studio/kaggle_bridge.py` and `kaggle/nightfall_gpu_job.py`. The project's real earlier Kaggle probe reported `gpu_devices: []`, `free_gpu_confirmed: false`. Kaggle CLI supports GPU kernel push and status, but account eligibility is not guaranteed. https://www.kaggle.com/docs/efficient-gpu-usage | **Blocked until a read-only diagnosis and successful no-cost CUDA probe show actual GPU availability in the owner's account.** Don't submit a batch or install a large video model before that. |
| Modal | Starter includes $30 of monthly compute, **can charge for overage**; included credits are not zero-bill protection. https://modal.com/pricing | **Disabled** while no hard verified $0 charge boundary exists. No payment method, auto-top-up or pay-as-you-go fallback. |
| LTX-2.x / 14B/4-step LoRA | Quality/throughput may improve with a proven compatible distilled checkpoint on sufficient GPU; not established on this owner's eligible free hardware. | Only benchmark after verifying licensing, memory, headless execution, free compute, and output quality. |
| CogVideoX-Flash | Exact model ID/terms/API and sustainable no-cost capacity not validated. | **No automatic fallback**. |

## C. What this PR actually changes

1. Add per-shot **model inference wall-clock time** to newly completed checkpoint rows.
2. Optionally read ZeroGPU remaining quota *after* a real successful shot. Compare with preflight quota to record an **observed delta**, never guaranteed or reserved cost. It can include other account usage.
3. The existing `pilot/e01_capacity_audit.py` new CPU-only step reads those records and reports median timing and observed quota delta. Older cached shots remain valid (their telemetry fields are optional).
4. Preserve the old `VERSION`, `plan_digest`, `completed` identifiers, SHA-256 validation, real MP4 files, Telegram receipts, calendar jobs and publishing gates.
5. New tests ensure the audit cannot approve a film, select a provider, or enable paid usage.

The audit **does not** accelerate LTX on its own. The purpose is to select an alternate engine from measured evidence and avoid wasting more free GPU credits on blind attempts.

## D. Safe migration path once free GPU exists

1. **Kaggle eligibility diagnostic (no new GPU run):** inspect previous kernel metadata, actual worker logs, accelerator entitlement and account quota. Past status: no GPU allocated. If still blocked, stop here.
2. **Single native-portrait speed/quality trial:** headless FastWan/WanGP on the *original* immutable Ember input, generate one genuine 3–5s 9:16 clip at 480p. Capture seconds, peak VRAM, model checkpoint SHA, worker status, job elapsed time and render frames. Never publish.
3. **Continuity trial:** second clip from the first clip's last real frame, plus a different character (Moss). Inspect Ember's white **left** ear-tip, teal scarf, **one** golden star, acting, movement and cinematic fidelity. Reject still zooms, loops, identity shifts and elementary low-poly renders.
4. **Separate provider manifests:** don't change `e01-one-free-account-v1` plan digest or mark old LTX clips as Wan clips. New jobs store `engine_id`, `model_sha256`, `reference_sha256`, `shot_id`, `duration`, `frame geometry`, `file SHA-256`, `provider_cost_class`, plus a source-aware continuity plan. Reuse authentic existing LTX MP4s only if visual/technical compatibility is verified, and never regenerate or overwrite them silently.
5. **Scale using measured throughput:** reserve the verified free GPU quota, generate multiple real shot MP4s per authorized batch, checkpoint and Telegram per shot, resume on the next legitimate session. Keep a concurrency guard to avoid two writers to the same manifest. Use long-lived model/dataset caches only when supported by Kaggle's policies, without putting large weight files into the Git tree.
6. **Correct episode length and acting:** 24×5s is only 120s; 32×5s is only 160s. The owner's required **180–360s** will need an actual revised screenplay and shot allocation (not freeze frames or fake stretching). Existing 36-shot plan is 150s. Test emotion-appropriate locked Kokoro speech, actual timed lip-sync, sound effects, subtitles and cinematic quality before accepting any episode. Upscaling 480p to 720p improves output dimensions, **not native detail**.
7. **Automatic episodes only after proof:** port shot planning, render/checkpoints, voice timing, quality gate, and Telegram to E02–E12 and then S02 E01–E10. Do not use publication success as the story-completion criterion. S03 still needs owner choice.
8. **Publishing:** remains out of scope for this speed experiment. Existing cross-post logic must pass real cinematic/lip-sync and official platform permission gates. Never turn those gates on as part of a model benchmark.

## E. Acceptance test before calling the speed issue resolved

- A usable **real** free GPU is shown in the actual owner's account, with billing unable to exceed $0.
- A fresh genuine portrait Ember MP4 at acceptable cinematic fidelity, plus one sequential continuation and a second-character proof.
- Measured end-to-end GPU minutes per **approved** shot (not merely model diffusion time) and achieved production capacity per eligible free session; no invented "20× speedup" promise.
- No loss of 3 existing verified shots, hashes, voice locks or story canon.
- Quality gate distinguishes technical MP4 from approved character acting and **real** lip-sync.
- Real 180–360s episode is both watchable and properly checked; Telegram confirms each verified shot and unapproved/publishing status truthfully.
- No unexpected use of billing, manual PC, manual uploads, alternate free accounts to evade quotas, or public uploads during testing.

**Next actual blocker:** Kaggle account GPU allocation, not adding a second GitHub schedule. Until a real free GPU is confirmed, performance optimization remains an evidence-based preparation rather than a finished throughput fix.
