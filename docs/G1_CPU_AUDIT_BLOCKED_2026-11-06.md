# G1 Blender-CPU Proof — Safety and Rig Feasibility Review
**Checked:** November 6, 2026. **Verdict: BLOCKED — NO QUALIFYING EMBER/MOSS RIG HAS BEEN PROVED.**
**Repository:** https://github.com/FadyIasaad/Nightfall-Diaries
**Working branch:** `proof/g1-blender-cpu` only (no main merge). **Verified latest baseline:** `ef613a5ce78b8d54b9f33fba381060249b7593b9`. The uploaded directive's `e7a2448` baseline is outdated.

## Rules preserved
The user selected Option A as a **conditional, no-cost G1 experiment**, not permission to change protected files, use paid services, weaken the cinematic target, or enable posting. The current main-branch one-workflow schedule remains at 10:00/23:00 Cairo (the 23:00 run is a safe resume check). GitHub standard `ubuntu-latest` runners are free for public repositories, while GPU/larger runners cost money. <https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job> and <https://docs.github.com/en/billing/reference/actions-runner-pricing>.

**Important:** The owner has **not** confirmed GitHub billing settings ($0, no payment method). Therefore **NO G1 workflow dispatch, Blender installation, CPU render, new schedule or production setting change was made**. CPU rendering is an engineering *candidate*, not a guarantee of premium quality or sustainable free daily 3-minute output.

Protected source evidence: [`docs/g1_protected_git_blobs.json`](g1_protected_git_blobs.json) records `44` Git blob SHA-1 identifiers for original scripts, character registries/image locks, `cloud_reference.png` assets, Kokoro profiles, episode inventories, the Series #3 proposal, GPU status and publishing settings. [`tests/test_g1_source_integrity.py`](../tests/test_g1_source_integrity.py) recomputes blob identifiers using exact file bytes; any change fails on the proof branch. These are Git blob hashes, not a claim that all image-frame identities have been visually checked.

## Findings
1. **A valid rig licence alone is insufficient.** The actual official Ember design is a *small quadruped russet fox cub* with a white-tipped **left** ear, two amber eyes, ivory tail tip and **teal scarf with one gold star**. Moss is a *large olive elder tortoise* with a spiralled dome shell and small crack at its **front-right** edge. The candidates found below cannot yet be shown to match those details.
2. **No approved facial performance rig.** Body joints and a walk loop do not prove lips/jaw shapes, eye tracking, emotional morphs, blinking or Rhubarb cue mapping. Some models will require substantial new modeling/rigging. No rig was imported, inspected, downloaded or approved in Blender during this step. That is a **hard stop under §4.2/§7**.
3. **License trap:** several professional-looking free models are **CC BY-NC** or impose contradictory "personal use only" statements; these are disallowed for a monetizable project. Treat "free download" and "royalty-free" separately from model source-file redistribution in the public repo.
4. **Budget gate:** the requested owner confirmation of **no payment method / $0 spending limit** is unavailable to this coding agent. Do not run a proof, add a runner, or route assets through a paid endpoint until independently confirmed.
5. **G1/G2 ambiguity:** §4.4 mandates at least a simple working mouth-sync sample as part of the 15–20-second G1 preview; §8 reserves a full emotional voice+lip-sync acceptance for G2. Use the distinction: sample mouth/jaw motion in G1, *separate* owner acceptance of full speech acting in G2.
6. **Compute risk:** `ubuntu-latest` offers standard CPU, not GPU. Need evidence of wall time/render settings for 720×1280 at 24 fps before forecasting 90 or 180 seconds of video. No benchmark measured; extrapolation = **UNVERIFIED**. A complete 3-minute premium short may still be infeasible at $0 even after acquiring rigs.

## Candidate rig outcome (each NOT APPROVED)

| Candidate and provenance | Licence / access | Evidence | Result |
|---|---|---|---|
| [Bake3D Fox](https://bake3d.ai/free-3d-models) | CC BY 4.0, redistributable with credits, no login | 28-joint quadruped rig, one walk clip | **REJECT AS-IS:** no verified face/jaw shape keys, different appearance; not a locked Ember |
| [OpenGameArt Turtle — Heathal](https://opengameart.org/content/turtle-0) | CC0, .blend download, walk cycle | Simple, low-poly character/basic rig | **REJECT AS-IS:** lacks established cinematic textures/expressive mouth; not Moss |
| [Sketchfab GIGI stylized fox](https://sketchfab.com/3d-models/gigi-the-little-female-fox-warrior-animated-db51a4356af94bddba9a39a44f21e56e) | CC BY on listing | Humanoid fox with many animations, fantasy armor | **REJECT AS-IS:** wrong species presentation, outfit/proportions and mouth controls unverified |
| [Sketchfab tortoise by Christian](https://sketchfab.com/3d-models/tortoise-riggedanimated-f911589e275e4c60963d52b31bc0b061) | CC BY-NC derivative | Detailed rig from museum scan | **FORBIDDEN for commercial-use plan** |
| [Sketchfab WildMesh fox demo](https://sketchfab.com/3d-models/fox-realistic-3d-model-demo-free-83b1b144712c43d282d90c2fb15ba450) | CC BY-NC | Full animal animation promotional demo | **FORBIDDEN for commercial-use plan** |
| [Blendkit Cartoon Turtle](https://www.blendkit.com/asset-gallery-detail/8b5e0bab-4716-4f95-a79a-e5964d7e5cea/) | "Royalty free", account/add-on required | Eyes/tongue/rig listed, but source redistribution/headless fetch unclear | **BLOCKED — rights and browser-only cloud access unverified** |
| [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync/blob/master/LICENSE.md) | MIT | Produces mouth cues from audio | **Technically eligible, but useless without suitable shape keys/jaw rig** |

The [candidate licence ledger](licence_ledger.md) records these URLs, researched licence terms, explicitly **null file hashes** (not downloaded), and no usage approvals. The first usable model must be source-authorized for commercial adaptation and either redistributable or fetched noninteractively from a documented permitted URL. It must also have sufficient rig and editable facial shapes for a faithful three-angle identity sheet **before** touching the real rendering workflow.

## GitHub changes and risk
- Working branch created at the **latest** main, not the stale directive baseline.
- Protected source hashes recorded. Only **audit documents + an immutable-baseline test** are committed on this branch.
- **No change** to `.github/workflows/nightfall.yml`, schedule, runner label, original 22 scripts, the stored S01/S02 identities, the 30-episode S03 proposal, or locked neural voices.
- **No GPU or CPU render, no 15-second proof, no identity sheet, no media artifact, no publishing**. Therefore rubric fields = **UNVERIFIED**. This is a stopped G1 *preflight*, not a failed finished film.

## Next legitimate $0 step (owner; maximum 3 decisions)
1. Confirm whether the repository account has a **$0 GitHub Actions spend budget and no payment method** (Settings → Billing and licensing; exact controls depend on account UI). Don't paste billing details.
2. Keep **Option A** only if a commercially reusable and aesthetically adequate Ember+Moss rig pair, including facial controls, can be legally obtained/cloud-rendered. Current evidence does **not** establish one.
3. If no candidate passes, authorize **Option B: investigate another $0 production method** without lowering the character/animation standard, or keep the branch frozen pending a licensed rig pair.

**Verdict: BLOCKED.** No source files or existing workflow changed, no costs incurred by running a render. The audit branch is prepared for safe continuation once both funding guardrails and original-compatible licensed rigs are established.
