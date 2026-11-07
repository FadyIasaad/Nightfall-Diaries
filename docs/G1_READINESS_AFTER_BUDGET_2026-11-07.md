# G1 CPU readiness after screenshot of $0 GitHub budgets
**Date:** November 7, 2026. **Phase:** G1 asset preflight; no actual 15–20 second proof. **Status: BLOCKED by unapproved Ember and Moss rigs.**

## Budget evidence
The owner provided a screenshot of their GitHub **Budgets and alerts** page with five budgets, all set to `$0.00 / $0.00 spent` and all marked **Usage blocked**: Actions, Packages, Codespaces, Git LFS and All AI Credit SKUs. This is real evidence that those budget limits are set at $0 at screenshot time. It **does not** prove the account has no saved card or permanently prevent billing for an unrelated service. The repo is public and the **standard** `ubuntu-latest` runner is free, per [GitHub billing documentation](https://docs.github.com/en/actions/concepts/billing-and-usage). Larger runners / GPUs and storage over free included quotas remain prohibited; no such products are used in this work order.

## New implementation (safe, branch only)
- Keep the original **single** `.github/workflows/nightfall.yml` and unchanged 10 AM / 11 PM Cairo schedule. Introduce optional manual `mode=g1_proof` only. No second workflow and no automatic proof launch.
- The manual mode invokes `python -m studio.g1_readiness` on existing free CPU runner, **without running Blender or downloading rigs**. It emits `output/g1_readiness.json` and intentionally **returns blocked** if model identity, commercial license, redistributability, source URL, exact SHA-256 or mouth controls are not established. The Actions run's error status is an **honest blocked preflight**, not an application crash or render result.
- Require a dedicated `docs/g1_asset_contract.json`. Both original cast IDs are hard-coded. Missing assets/approval flags are recorded as blockers. Report lists each one. No content was silently changed or approved.
- Preserve the 44-source-file original baseline and original scripts/tests, with all publishing gates off.
- There is **no Blender render code or complete episode** in this change. Rendering can only be developed later after the separate character asset feasibility gate passes.

## Current character research
1. [Bake3D fox](https://bake3d.ai/free-3d-models) is CC BY 4.0 and comes with a quadruped 28-joint rig, but not confirmed to support a speaking face or Ember's exact asymmetric markings.
2. [OpenGameArt Turtle](https://opengameart.org/content/turtle-0) is CC0 and has a basic animal rig but is **low-poly**, not cinematic Moss.
3. [Mesh2Motion](https://mesh2motion.org/) supplies free CC0 creature rigs/animation (including fox quadrupeds) and even mouth controls in some versions, but it does **not** supply the locked Ember or Moss cinematic model.
4. [Blender Studio character rigs](https://studio.blender.org/characters/) include professional CC BY rigs for *other* characters. They are not direct replacements for Ember or Moss and some require browser login/download.
5. [WildMesh realistic fox](https://sketchfab.com/3d-models/fox-realistic-3d-model-demo-free-83b1b144712c43d282d90c2fb15ba450) is CC BY-NC. **Forbidden** for monetized originals.
6. [Red Fox with Fur and Rig](https://blendswap.com/blend/24920) is CC BY-SA but cloud fetch, mouth controls and owner-quality match are unverified. Not approved.

**Decision:** Do not insert a generic licensed fox/turtle and call it a G1 success. The model design + controls gap is real. Existing low-poly `studio/render_blender.py` stays retired for visual approval.

## Status
- Original 22 story archives: PRESERVED / hash-checked at preflight.
- Original Kokoro voices: PRESERVED / not reconfigured.
- Production/publishing flags: all FALSE.
- Public publishing and S03: NOT STARTED.
- Motion/lip-sync proof: NOT RENDERED.
- Hardware benchmark extrapolation: UNVERIFIED (no legitimate approved actors).
- Cost spent by this source change: no paid service or model requested; GitHub public standard-runner CI applies.
- Next gate: source/build two licensed models that **visually and technically match** Ember and Moss, then produce 3-angle identity sheets and mouth/eye tests; **owner approves visual quality** before integrating actual film mode. A CPU benchmark must then establish whether the free renderer can meet episode demand.

**No cinematic video exists yet. CI passing proves code consistency only.**
