# Nightfall Diaries — Engine Discovery Scorecard (v2)

**Checked:** 2026-11-07 (Cairo)  
**Verdict: NO-ENGINE — discovery only.** No video engine was proven to meet *all four*: owner-approved Flow-class cinematic quality, sustained $0 with no card, 100% cloud operation, and fully unattended authorized programmatic automation. **Do not enable publishing, begin full production, or create fake automation.**

## 0. Contract and baseline

This is the evidence-only execution of \`NIGHTFALL_AGENT_DIRECTIVE_v2_2026-11-07.md\`, checked against \`NIGHTFALL_DIARIES_FULL_REQUIREMENTS_AND_BLOCKERS_2026-11-07.md\`. No material conflicts identified.

- GitHub main at discovery: \`dddaf8f2f6f8889a84f909154df33ae093642ec1\`.
- All **44 protected Git blob IDs** in \`docs/g1_protected_git_blobs.json\` were compared to the current Git tree: **0 mismatches** (all 22 archived scripts, the original characters/images, voice locks, flags, and S03 draft remain unchanged).
- \`studio/production_settings.json\` production and all publishing-related booleans = **false**; \`config.json.public_publish_enabled=false\`.
- Only the existing \`.github/workflows/nightfall.yml\` orchestrates production. Cairo 10:00 daily plus safe 23:00 retry check remain untouched. Existing **Generate another episode** is not redefined.
- Two open earlier proof PRs, #25 and #26, remain **unmerged**; neither contains an owner-approved production engine.
- No engine API token obtained; no paid calls, trial account signups, web-UI automation, GPU inference, render or posting were attempted.
- Billing screenshot: Actions and other listed GitHub budgets showed $0 and "Usage blocked" when captured; that screenshot does not prove no card is saved or extend free budgets to other providers.
- The Google Flow sample was **8.042 s, 720×480, 24 fps**, not 9:16; owner reported **~25 in-app Flow credits**. This is a *style benchmark*, not accepted Kokoro lip-sync or a GitHub automation API.
- Failed Blender technical diagnostic: **2 seconds, 360×640, 12 fps, 68.44 seconds wall time**, primitive visual quality rejected. Do not repeat this method without approved new character rigs and explicit owner acceptance.

## 1. Hard gates and notation

Evaluate sequentially, stopping at the earliest failed/unverified gate. **P** = verified pass for that narrow gate only; **F** = failed; **U** = unverified, so stop; **—** = not evaluated after the stop.

- **G1**: documented official permitted programmatic API/CLI usable from GitHub, without operating web UI.
- **G2**: documented continuing $0 quota with no card and **no billable fallback**; promotional credits and ordinary pay-as-you-go are not equivalent.
- **G3**: accepts locked reference image and returns true moving MP4 with required vertical format/character control.
- **G4**: actual tested Flow-class identity, acting and cinematic look on both Ember **and** Moss; owner alone approves.
- **G5**: genuine Kokoro voice-ID preservation + matching mouth/facial movement, free and automated.
- **G6**: measured 90–180 s per-episode capacity within free quota and timing, including ×2 retries.
- **G7**: commercial and publishing terms/asset licenses verified per exact component (and no copied reference material).

**Do not read a P under G1 as a recommended engine.** A candidate is selected only if **every** gate passes with evidence.

## 2. Candidate scorecard — stop at first failure

| Candidate | G1 | G2 | G3 | G4 | G5 | G6 | G7 | Earliest stop; evidence (checked 2026-11-07) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Google Flow UI** (Veo/Omni) | **F** | — | — | — | — | — | — | 50 daily UI credits but **no documented no-charge official Flow generation API usable by GitHub**: [Flow credits](https://support.google.com/flow/answer/16526234), [Flow site](https://labs.google/fx/tools/flow) |
| **Google Gemini API: Veo 3.1 / Gemini Omni Flash** | P | **F** | — | — | — | — | — | Official generation API exists, **video output Free Tier not available**: [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| **Runway Developer API** | P | **F** | — | — | — | — | — | Official API; **$10 minimum purchase before first API call**: [setup](https://docs.dev.runwayml.com/guides/setup/), [pricing](https://docs.dev.runwayml.com/guides/pricing/) |
| **fal.ai video API** | P | **F** | — | — | — | — | — | Official API is **prepaid/billed per video**; 5 free Grok clips/24h are **in the logged-in sandbox**, not a free recurring API: [pricing](https://fal.ai/docs/documentation/model-apis/pricing), [free sandbox](https://fal.ai/grok-imagine-free) |
| **Replicate API** | P | **F** | — | — | — | — | — | **Pay as you go**. “Try for Free” models stop after a limited number of runs; not sustainable: [billing](https://replicate.com/docs/topics/billing), [trial](https://replicate.com/collections/try-for-free) |
| **Hugging Face ZeroGPU Gradio Space, existing Wan attempt** | P | P | **U** | — | — | — | — | Free account **5 GPU minutes/day**, previous provider requested **126 GPU seconds for a 5-s clip** and prior result failed owner's look. An actual approved-reference 9:16 test and sustainable throughput are **not demonstrated**: [ZeroGPU docs](https://huggingface.co/docs/hub/spaces-zerogpu), [prior Nightfall evidence](../docs/GPU_ACCESS_BLOCKER_2026-11-06.md) |
| **Lightning AI free Starter GPU credits** | **U** | — | — | — | — | — | — | Cloud/SDK exists, but **unattended stable API control of GPU without account verification is unproved**; only **5 no-card introductory credits**, extra 25 tied to adding card, not sustainable: [pricing](https://support.lightning.ai/pricing/), [billing docs](https://lightning.ai/docs/platform/overview/faq/billing) |
| **Modal Starter GPU** | P | **F** | — | — | — | — | — | Official Functions/Web Functions, **$30 monthly included compute** but *pay-as-you-go* overages, and Starter **environment budgets not included**; no verified hard $0/no-card boundary: [pricing](https://modal.com/pricing) |
| **Cloudflare AI Gateway third-party video** | P | **F** | — | — | — | — | — | Official API; third-party video uses **Unified Billing/prepaid purchased credits**, card required, possible negative balance: [unified billing](https://developers.cloudflare.com/ai-gateway/features/unified-billing/), [video model example](https://developers.cloudflare.com/ai/models/runwayml/aleph-2/) |
| **Cloudflare Workers AI free native allocation** | P | P | **F** | — | — | — | — | **10,000 free neurons/day** available for native models, but verified **native Workers AI catalog does not offer a suitable native text/image-to-video engine**; video entries in broader AI catalog are paid third-party models: [free quota](https://developers.cloudflare.com/workers-ai/platform/pricing/), [native catalog](https://developers.cloudflare.com/workers-ai/models/), [broader catalog](https://developers.cloudflare.com/ai/models/) |
| **Kaggle notebook GPU** | P | **F** | — | — | — | — | — | CLI can submit notebooks, but **owner's Kaggle account has no available T4**; P100 retired. Account-specific availability makes a zero-cost GPU unproven: [Kaggle CLI](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md), [Kaggle update](https://www.kaggle.com/product-announcements/735239) |
| **GitHub Actions standard CPU + existing procedural Blender** | P | P | P | **F** | — | — | — | Real MP4 produced at no runner charge but basic 3D visuals **rejected**; 2 s @ 360×640/12fps, 68.44 s. Rigged, cinematic, expressive animals **not obtained or approved**: [GitHub pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing), [G1 audit](G1_CPU_AUDIT_BLOCKED_2026-11-06.md) |

**No selected provider. No candidate reaches G4–G7 with valid evidence.** Some gate-3 entries are stopped before quality because basic reference consistency or production conditions are unverified.

## 3. Provider findings and implications

### Google Flow (visual benchmark, not an automation endpoint)

The owner showed 1,050 available in-app credits in a prior screenshot, but account eligibility, renewal rate for that amount and their transferability to any API were not proven. [Official Flow documentation](https://support.google.com/flow/answer/16526234) gives non-subscribers **50 daily UI credits** (and may restrict generation during peak times). The uploaded ~8-s clip reportedly used ~25 UI credits. Neither a Flow browser “Agent” nor scripts that automate clicks/cookies are permitted under owner rule I-11.

**Stop G1.** Never substitute paid Gemini API calls for no-charge Flow credits, or silently ask the owner to manually generate/download each shot.

### Google Gemini API — Veo / Omni Flash

Official API supports cinematic image/video generation, but [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing) lists **no free video-generation tier** for Veo or Gemini Omni Flash. Free **text** requests are not free **video** requests.

**Stop G2.** No pay-as-you-go credentials or billing project.

### Runway

Official [API onboarding](https://docs.dev.runwayml.com/guides/setup/) requires **at least $10** of developer credits. The image/video outputs are billed according to [developer rates](https://docs.dev.runwayml.com/guides/pricing/).

**Stop G2.** The existence of a connected Runway app or promotional website trials is not proof of a free API; do not connect or pay.

### fal.ai and the misleading "free video" label

The [model API pricing page](https://fal.ai/docs/documentation/model-apis/pricing) is explicitly prepaid/pay-per-video. The [Grok Imagine Lite sandbox](https://fal.ai/grok-imagine-free) has **five no-charge clips per rolling 24 h inside fal's signed-in web sandbox**, while the same model's **API is priced per second**. Even if free web capacity increased, site UI credits do **not** become an API allowance.

**Stop G2.** Do not automate the browser to harvest sandbox quota.

### Replicate

[Billing](https://replicate.com/docs/topics/billing) is usage-based; [Try for Free](https://replicate.com/collections/try-for-free) explicitly says free runs are finite and billing must be added afterward.

**Stop G2.** A few exploratory shots cannot support original multi-minute daily drama.

### HF ZeroGPU / Wan

[Hugging Face](https://huggingface.co/docs/hub/spaces-zerogpu) says 5 free GPU minutes per day for a normal account; a Space can be accessed programmatically only to the extent its exposed Gradio API and usage policy allow. Nightfall already tested a Wan Space once: the provider requested **126 GPU seconds** for a five-second video when only 90 s quota remained. One clip was saved but was visually rejected, and subsequent generation paused due to quota. This is an *estimated request/quota accounting*, **not a measured average GPU time**.

**Illustrative, non-benchmark math only:** if all 5-s clips really cost 126 GPU seconds, 90s needs 18 clips ≈ 37.8 GPU minutes, **75.6 min at ×2 attempts**, against **5 min/day**; 180s needs 36 clips ≈ 75.6 GPU minutes, **151.2 min at ×2 attempts**. And real character continuity/lipsync may need more compute.

**Stop G3 as unverified for approved locked references/9:16, with prior direct evidence failing G4.** Do not automatically re-run GPU queries or claim guaranteed generation.

### Lightning AI

[Official pricing](https://support.lightning.ai/pricing/) describes one no-card free CPU studio, and **5 introductory Lightning credits at registration**; adding a payment card unlocks another 25. [Billing terms](https://lightning.ai/docs/platform/overview/faq/billing) say free credit eligibility/amounts can change. SDK and unattended GPU execution for the *owner's* specific account, and hard no-billing limits, are untested.

**Stop G1 as unverified (and independently no sustainable no-card GPU pool).** Owner need not create a Lightning account for this report.

### Modal Starter

[Official pricing](https://modal.com/pricing) provides a real programmatic GPU platform with **$30/mo included compute**, but its Starter is **$0 + compute** with pay-as-you-go beyond included usage. Documentation lists environment-level budgets only from Team. The ability to guarantee a strict **no-card / hard $0** compute-only account was not verified. The model/animation throughput under its included credits would still need measurement.

**Stop G2.** Do not start GPU calls or rely on unused free compute as unlimited filming.

### Cloudflare video APIs vs native Workers AI

[Cloudflare AI Gateway](https://developers.cloudflare.com/ai-gateway/features/unified-billing/) requires a **card and prepaid Unified Billing credits** for external video models, and warns of negative credit balances; video offerings in its broader catalog are **third-party**. [Native Workers AI](https://developers.cloudflare.com/workers-ai/platform/pricing/) has a separate **10,000-neuron/day free allowance**, but the [native catalog](https://developers.cloudflare.com/workers-ai/models/) did not establish a qualified native video-generation model. The unified model catalog is not proof that third-party videos share free native neurons.

**Stop external-video G2; native free G3.** Cloudflare remains useful for other free app infrastructure, not for this certified cinematic video engine.

### Kaggle and the existing Blender CPU result

[Kaggle notebook submission via CLI](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md) is possible, but owner **cannot access a T4 accelerator**, and P100 was [retired](https://www.kaggle.com/product-announcements/735239). Owner account availability is decisive here.

GitHub's public standard runners work at $0 for the CPU test and produced a real moving MP4 via Blender/FFmpeg. But the film sample is **primitive, silent, low-resolution, visually wrong**, and had no approved characters or Kokoro sync. See [G1 audit](G1_CPU_AUDIT_BLOCKED_2026-11-06.md). **The old procedural Blender attempt is finished and rejected.** A *new* rigged character and acting workflow would require a documented different method and fresh owner approval.

## 4. Two independent blockers

1. **Video compute and fidelity:** no legal, programmatic, recurring no-card free provider with measured enough capacity and *approved* Flow-class acting for **both** Ember and Moss.
2. **Locked-voice lip synchronization:** a video-generation model's native talking audio is not equivalent to the original fixed **Kokoro \`am_puck\` / \`bm_george\` identities**. To replace audio *and* match mouth/eyes, we need a separate verified rig/viseme or lip-sync/video-to-video animation path, with its own licences, GPU/CPU benchmark and free quota. [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync) can generate mouth cues but does **not** magically animate a diffusion video or supply a 3D facial rig. Character consistency must be proved over clips, not just an image hash.

Even if video generation G1–G4 passed, **the second blocker could independently block the daily pipeline.**

## 5. Required capacity and evaluation protocol

From the owner test: **25 in-app credits / 8.042 s** (observational, not API billing). Required clips under an 8-second assumption: **12** for 90 seconds, **23** for 180 seconds. At 25 credits per attempt, **300 / 575 credits per episode**, respectively. With a conservative **×2 retry allowance**, plan **600 / 1,150 credits per episode**, excluding extras, longer cuts, actors, or separate audio/lipsync. A UI allotment of 50 credits/day does not support that cadence; **do not assume the owner's previously visible 1,050 credits refill at that level**.

Any future actual candidate trial must be *one* authorized 5–8s Ember clip, 9:16, with locked reference material, documented account eligibility, no card/billing and official API access. Required evidence: request model/version, response receipt, seed if supported, GPU seconds or credits consumed, quota remaining, elapsed time, SHA-256 of the returned MP4, ffprobe duration/resolution/audio, inspected frames and owner verdict. Reject once any gate fails, with no quota-burning loops.

**A model name is not a compute provider.** Open weights (Wan, LTX, Hunyuan, CogVideo etc.) solve neither free GPU allocation nor automated rights/quality by themselves.

## 6. Safe work that can proceed without an engine (NOT performed by this discovery PR)

- Preserve original \`S01.../scripts/E01.json\` without editing; write a *separate* storyboard/shot plan once the relevant original scene is selected.
- Run Kokoro locked-voice auditions to WAVs and produce cue metadata; do not substitute synthetic voices.
- Build a **read-only** ffprobe validator for 9:16, 24fps, H.264/AAC, real audio, 90–180s; passing technical fields does not equal owner quality approval.
- Manage shot/status receipts via episode ID and SHA-256, not ambiguous filenames; protect retries from duplicate posts.
- Restore checkpoints from independently hash-verified durable storage, not assumed-permanent GitHub caches.
- Continue reviewing individual audio/model/character licenses and current platform API publishing permissions; public posting remains locked.

**No additional \`workflow_dispatch mode=engine_probe\` is installed at this stage**: no candidate passed enough gates to justify even a bill-safe test, so adding a live button would give a misleading expectation. The directive *permits* this input only after a legitimate test candidate emerges; it does not require an inert control now.

## 7. Decision and owner choices (owner only)

**Current verdict: NO-ENGINE.** Nothing here authorizes the agent to select a visual compromise or billing service.

| Choice | What it means |
|---|---|
| **D1 — Pause** | Keep source, locks and flags unchanged; stop spending trial effort |
| **D2 — Different visual style** | Investigate a CPU-feasible stylized approach **only with a new owner-approved look proof**, never silently replace Flow-quality CGI |
| **D3 — Lower frequency / duration** | Explicitly change the goal after measured feasible throughput; no change without owner's choice |
| **D4 — Limited free-credit batch** | A few finite trials; **not** automatic daily production |
| **D5 — Search later** | Monitor newly launched providers and genuine recurring free API video tiers; keep all rules unchanged meanwhile |

**Owner action now:** choose whether to keep the present standards and revisit providers (D5), to pause (D1), or explicitly authorize a *named* different experiment. No card, token, personal PC or daily clip handling is requested. **None is preselected.**

## 8. Research source index (all accessed/verified 2026-11-07)

1. Flow UI/credits: https://support.google.com/flow/answer/16526234
2. Gemini Video API pricing incl. Veo/Omni: https://ai.google.dev/gemini-api/docs/pricing
3. Runway developer setup + pricing: https://docs.dev.runwayml.com/guides/setup/ ; https://docs.dev.runwayml.com/guides/pricing/
4. fal video usage & free website sandbox: https://fal.ai/docs/documentation/model-apis/pricing ; https://fal.ai/grok-imagine-free
5. Replicate billing and limited free trials: https://replicate.com/docs/topics/billing ; https://replicate.com/collections/try-for-free
6. Hugging Face ZeroGPU: https://huggingface.co/docs/hub/spaces-zerogpu
7. Lightning AI Pricing / Billing: https://support.lightning.ai/pricing/ ; https://lightning.ai/docs/platform/overview/faq/billing
8. Modal pricing: https://modal.com/pricing
9. Cloudflare native free allocation / unified third-party bills: https://developers.cloudflare.com/workers-ai/platform/pricing/ ; https://developers.cloudflare.com/ai-gateway/features/unified-billing/ ; https://developers.cloudflare.com/workers-ai/models/
10. Kaggle CLI/retirement: https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md ; https://www.kaggle.com/product-announcements/735239
11. Free standard GitHub runner policies: https://docs.github.com/en/billing/reference/actions-runner-pricing
12. Rhubarb mouth cues (not full character lip sync): https://github.com/DanielSWolf/rhubarb-lip-sync

**Discovery delivered — no external accounts connected, no rendering, no publishing, no production file edited, no model declared approved.**
