# Agnes safe read-only API probe — November 9, 2026

**Status:** Connection evidence requested; zero-cost generation NOT approved. **Only one workflow. No billing or video calls.**

The owner reports creating `AGNES_API_KEY` as a GitHub Actions repository secret. The GitHub connector cannot read or list repository Secrets and cannot inspect the value. This report does not claim that the secret was independently verified.

## Why the next operation is metadata-only

- The earlier Agnes account screenshot showed **effective balance $0.000000** and voucher balance $0. This does *not* guarantee free API video eligibility or prohibit paid charges if account settings change.
- Research found `agnes-video-2.5-flash` (720P) as a **limited-time** promotional free model in Agnes docs; **the live price/eligibility of this exact key remains unverified**.
- The **different** model `agnes-video-2.5` is listed as paid. The probe must not fall back to it.
- `GET https://apihub.agnes-ai.com/v1/models` is documented as a model listing API. Merely seeing a model there does **not** prove its current price or quota.
- No ability to bypass quota via rotating accounts/tokens and no unofficial browser automation are allowed by the user's binding v2 directive.

## Exact implementation

- Add **optional** manual `workflow_dispatch.mode=engine_probe` to the **existing** `.github/workflows/nightfall.yml`. Keep `action=Check setup` and `episode=auto`.
- The step runs only for an explicitly selected **manual** dispatch (never schedule, push, PR, or production).
- `studio/agnes_probe.py` reads `AGNES_API_KEY` in memory, invokes only a single authorized **GET /v1/models**, and writes a **redacted JSON report**. It never logs the token, model catalog raw response, or account information.
- No media jobs, video requests, images, GPU, payments, charge estimates, data uploads, or social publishing.
- **Fail closed:** absent key, API/auth failure, or absent target model ⇒ `BLOCKED`. If the candidate appears, status `CONNECTED_PRICING_UNVERIFIED`. This is **not** `ENGINE-FOUND`.
- User can download `nightfall-agnes-read-only-engine-probe` artifact after the manual action. Existing source integrity tests must pass.

## Binding limits / what must happen before even one 5–8-second test

1. Verify on Agnes' official current account-specific pricing/usage screen that **exactly** `agnes-video-2.5-flash` costs **$0 per generated second**, with no extra image/reference fee and no card/autorecharge, and that no other billable fallback can occur. Record screenshot/date.
2. Confirm the free API key has video Flash access and independent sustainable allowance. A temporary promotional offer is insufficient for the **daily $0** goal.
3. Separately authorize **one** 5–8-second vertical Ember test using the locked repository reference, and record its actual spent balance, MP4 hash, frame QA, elapsed generation time and returned rights. No retries until the result is reviewed.

## Preserved gates

- 22 protected original scripts and character source images unchanged; 44 protected blob IDs unchanged.
- Kokoro voice identity locks unchanged.
- All `studio/production_settings.json` gates remain false; `config.json.public_publish_enabled=false`.
- No episodes, fake generated videos or public posts.

**No model can be called production-ready until the full 7-gate v2 scorecard passes, including locked voice lip-sync and capacity.**
