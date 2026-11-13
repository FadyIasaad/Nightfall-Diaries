# Nightfall Diaries — One legitimate free account, persistent E01 150s animation

Status: **experimental, not production approved**, 2026-11-13.

## Why the earlier PR #39 could not produce the episode

- The original 14 scenes total **150 seconds**, split into **36 UNIQUE 2–5 second AI motion sub-shots**.
- The old workflow used anonymous `Lightricks/LTX-2.5`. It stopped before the first shot because ZeroGPU estimated 194 GPU seconds for a single 5s request, exceeding the anonymous **120s daily quota**.
- The merged code did **not** securely resume finished shots between different days; a new job restarted from shot 1. GitHub Actions CI green means tests passed, not a real E01 film.
- No legitimate four-platform uploading was verified. YouTube identity was HTTP 403, Facebook page identity OK but publish permission unverified, Instagram identity HTTP 400, and TikTok access token was absent. The real animal-face lip sync still has not been implemented.

## Safe solution in this PR

1. Use **ONE real personal free Hugging Face account only**. No extra or disposable accounts, sharing/rotating tokens, quota bypass, PRO or billed APIs.
2. A one-time GitHub secret `HF_TOKEN` enables `Client("Lightricks/LTX-2.5", token=...)`, but only after an official read-only `whoami()` confirms `isPro == false`, and `get_zero_gpu_quota()` confirms a free baseline of no more than 300 GPU-seconds, no paid overquota, and enough remaining quota to conservatively reserve one inference. If account tier cannot be safely verified, **STOP**. Free-account billing is not upgraded.
3. Manual Actions dropdown **Resume E01 one free HF shot** may submit **AT MOST ONE genuinely new clip** per job and preserve the exact original image/scene voice/prompt locks.
4. Each clip is real LTX image-to-video motion; subsequent clips start from the **actual last frame** of the preceding clip, no slides, looping, or synthetic length extension.
5. After each success, save MP4 + SHA256 + plan fingerprint to GitHub Actions Cache AND a cumulative Actions Artifact. The next run restores, checks checksum, skips finished clips and moves to the next scene. A cache or artifact mismatch **stops** rather than re-rendering or silently losing progress.
6. Default is manual; automatic 10:00 Africa/Cairo execution may be **opted in later** by setting repository variable `NIGHTFALL_E01_RESUME_ENABLED=true` **after a real free-tier test succeeds**. The variable is NOT set by this PR. The workflow never creates a paid job and has no publishing command in this path.
7. Once 36 real sub-shots have been saved, Actions dropdown **Assemble E01 from 36 real shots (no publish)** merges all 14 scenes, generates locked Kokoro voices, validates a genuine 120–180-second H.264/AAC 9:16 film, and archives it as **unapproved**. This stage consumes **no HF GPU**.
8. Owner/QA must still verify cinematic character continuity, coherent actions, dialogue, music/SFX and **actual mouth-to-voice lip sync** before publishing. Simply adding Kokoro audio is NOT lip sync. All production/publication flags stay false.

## Practical daily limit (not a guaranteed timeline)

Official ZeroGPU docs: https://huggingface.co/docs/hub/spaces-zerogpu

- Anonymous: 120 GPU-s/day. Registered free: 300 GPU-s/day; xlarge uses 2× quota. 24-hour quota reset from first request.
- **194 GPU-s requested** for a prior 5-second xlarge call is an observed figure, not a video-duration allowance. A registered free account might fit one such request per day if its quota is available, but model availability and account per-call restrictions may still reject it. This suggests roughly 36+ days for 36 distinct short clips if no optimization or failures; it cannot promise a daily 150s episode.
- A smaller 2s request can have different estimated GPU reservation; this trial uses conservative 140s minimum for short shots and 220s for 4–5s shots. The actual official scheduler remains authoritative.
- This PR cannot verify the owner's Free plan or remaining quota because the user's `HF_TOKEN` is not accessible to the assistant. Never send or paste the token into chat.

Official quota read-only API: https://huggingface.co/docs/huggingface_hub/guides/manage-spaces

## One-time setup after PR merge

1. Open https://huggingface.co/settings/tokens, create a **READ** token from the single legitimate **Free** personal account. Do not upgrade to PRO or buy credits.
2. In https://github.com/FadyIasaad/Nightfall-Diaries/settings/secrets/actions set **Repository secret** `HF_TOKEN` to that token. Do NOT paste it into a commit or chat.
3. Open **Actions → Nightfall Diaries - One Free Online Workflow → Run workflow**, select **Resume E01 one free HF shot**, episode `S01_the_last_little_fox_E01`.
4. Read the run and download artifact `nightfall-e01-cumulative-real-shots`. If free-account verification/quota or Space generation fails, do not rerun in a loop; inspect the blocker and available reset time.
5. Once at least one genuine moving clip was generated and its reference identity/quality passes review, optionally set Actions Repository Variable `NIGHTFALL_E01_RESUME_ENABLED` = `true` to attempt one free shot on the existing 10 AM Cairo schedule. Disable it if the Space/model is unavailable.
6. After all 36 genuine shots, run **Assemble E01 from 36 real shots (no publish)**. Do not post before real face lip-sync, visual review and official uploader permission tests.

## Limitations and safeguards

- GitHub Actions cache is best effort; the cumulative Actions artifact (30-day retention) is a secondary backup, not permanent media storage. If both copies expire, do not claim any recovered progress.
- The model's current 5s maximum and ZeroGPU reservation are independent of film duration. Splitting solves the **model clip-length limit** and preserves partial work; it **does not multiply free quota or create GPU capacity**.
- Creating a farm of free accounts to evade usage limits is not implemented; it is unreliable and can result in service restrictions.
- Genuine 3D quality, natural acting, multi-character image lock, 150s final mix and approved lip sync are **not yet demonstrated**.
- Existing GitHub social-upload code and publishing flags are unchanged; this PR does not publish to YouTube/Facebook/Instagram/TikTok, nor does it promise a full episode today.


## Fix — 13 Nov 2026: actual HF quota API Python version and permissions

The owner's first authenticated one-shot
[GitHub Actions #43351214405](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/43351214405)
did NOT make a GPU inference. The real runner installed
`huggingface_hub==1.33.0` because the workflow specified
`huggingface_hub>=0.36,<2`. The code then failed with
`AttributeError: 'HfApi' object has no attribute 'get_zero_gpu_quota'`.
This method was added in the official Hugging Face Hub **2.1.0**
release. The fix requires `huggingface_hub>=2.1.1,<3` and tests
the actual method import in a PR-only, no-credential dependency smoke test.
The free quota check is NEVER skipped on older installations.

**Fine-grained token permission:** Hugging Face's quota API requires
`Billing > Read billing usage and payment method status` for
fine-grained tokens (read-only permission). A token without this
permission may return HTTP 401/403; the code stops before any GPU request,
prints `HF_ZERO_GPU_QUOTA_PERMISSION_REQUIRED` and does NOT fall back
to anonymous/paid inference. It does not require permission to make
payments or purchase credits. Do not put your token into GitHub logs,
repo commits or chat.

Once the bug-fix PR is merged, repeat the manual option
`Resume E01 one free HF shot` on branch `main`. If the new failure is
a permissions message, add only the specified Billing **read** permission
to a fine-grained HF token and update the existing `HF_TOKEN` GitHub secret;
then rerun. No new account, PR, GPU paid service, or publishing consent.
No automatic daily inference is enabled by this fix.
