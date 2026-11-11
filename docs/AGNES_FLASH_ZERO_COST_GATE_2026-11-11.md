# Agnes Video 2.5 Flash — zero-charge feasibility gate (2026-11-11)

**State: BLOCKED before video generation.** This is a safe diagnostic and
an Ember quality-proof specification, **not** an approved render engine.
No episode has been created or published by this change.

## Verified public facts

- Official Agnes [pricing](https://wiki.agnes-ai.com/en/docs/pricing.md)
  currently lists `agnes-video-2.5-flash` at a **temporary $0/second**
  trial price for **720P** (base price **$0.025/second**).
- Official [subscription notes](https://wiki.agnes-ai.com/en/docs/tokenplan.md)
  say **Agent Plan** requests use list-price/Credit billing, **not**
  trial-price offers. Do **not** infer the active key type from a successful
  `GET /v1/models` request.
- The provider's account bill is authoritative. Public documentation does
  not establish an auditable, enforceable **hard zero-spend cutoff** for
  this account or certify that no card/paid key/automatic billing can apply.
- Official [Flash API documentation](https://wiki.agnes-ai.com/en/docs/agnes-video-25-flash)
  supports `reference` with image URLs, 9:16, 720P and 4–12 second clips.
  It does **not** establish the quality of the rendered Ember character.
- Official [Hugging Face ZeroGPU](https://huggingface.co/docs/hub/spaces-zerogpu)
  has a free allowance (normally 5 GPU minutes/day on a free account).
  [LTX-2.5](https://huggingface.co/spaces/Lightricks/LTX-2.5) is the
  next **candidate**, not an approved free cinematic full-episode engine.

## What was added

- `studio/agnes_cost_gate.py`: only unauthenticated **GET** calls to the
  fixed Agnes pricing document and Hugging Face LTX-2.5 Space metadata.
  Parses the **exact** Flash video pricing row, records the current public
  offer, prepares the 5-second Ember reference-shot specification, and
  always keeps `generation_authorized=false`.
- `tests/test_agnes_cost_gate.py`: offline tests for exact-price matching,
  unexpected URL rejection, **GET only** and no video approval.
- Two read-only steps in the **existing** `.github/workflows/nightfall.yml`,
  only for the manual `Check setup` + `engine_probe` action. No new
  workflow, scheduler, provider secret, or public publishing switch.
- The previous read-only `studio/agnes_probe.py` remains unchanged. It
  checks the key's ability to read `GET /v1/models` only.

## How to run the safe diagnostic (after merging this reviewed PR)

1. Open repository **Actions** → **Nightfall Diaries - One Free Online Workflow**.
2. Select **Run workflow**, `action=Check setup`, `mode=engine_probe`.
3. Read the `nightfall-agnes-read-only-engine-probe` report and
   `nightfall-agnes-free-trial-cost-gate` artifact.
4. Expected decision: `BLOCKED_ACCOUNT_BILLING_UNVERIFIED`, **even if**
   the exact model and public $0 promo are both confirmed.
5. Never paste `AGNES_API_KEY` into logs, issues, screenshots or chat.

## Prepared Ember test — no generation submitted

- Use the **original** file
  `seasons/S01_the_last_little_fox/characters/s01_ember/cloud_reference.png`.
  Do not replace or edit canon source, approved stills, voice locks, or stories.
- Candidate request *when safe billing is verified independently*:
  `model=agnes-video-2.5-flash`, `mode=reference`,
  `seconds="5"`, `size="720P"`, `aspect_ratio="9:16"`,
  **one** source image. Do not assume a local file path is an image URL.
  The provider requires a publicly accessible URL valid throughout the task.
- The exact **English motion prompt** is stored in
  `studio/agnes_cost_gate.py` and the report under
  `prepared_not_submitted_proof`. It depicts Ember walking, noticing
  firelight, reacting with body/eye/ear acting and camera dolly-in;
  **no dialog yet**. Later Kokoro synchronization is a separate quality gate.
- Compare the result with the owner's Flow Ember reference for 9:16 output,
  body physics, fur, forest light, left white-tipped ear, one star on the
  teal scarf, stable facial identity, and camera action. Human approval
  is required. An MP4 or successful task status alone is **not** approval.

## Required checks BEFORE any `POST /v1/videos`

All must be backed by current, account-specific evidence and clearly
verified before adding/using **any** generation path:

1. Confirm this API key uses Agnes **default-user promotional** access, not
   Agent Plan or any paid/credit-consuming pathway.
2. Verify the account cannot incur charges: no paid billing fallback,
   auto top-ups off, and an enforceable **hard $0 spend stop** or another
   provider-documented guarantee that paid generation is impossible.
   **If no such guarantee is available, do not submit a generation task.**
3. Recheck exact Flash model and same-day official price immediately before
   generation; fail closed if unavailable or changed.
4. Confirm image-reference licensing, storage, and commercial use.
5. Limit any approved proof to **one** 5-second 720P 9:16 reference clip;
   no retries or automatic scheduling until measured and approved.

## Fallback

If Agnes fails any zero-billing or quality gate, next inspect the official
`Lightricks/LTX-2.5` Gradio Space interface using **GET only**. Its
metadata alone cannot prove availability, quota, video fidelity or lip-sync.
Do not call LTX inference, add paid GPU, or activate publication by default.

The main production flags and all 22 original story files remain untouched.
