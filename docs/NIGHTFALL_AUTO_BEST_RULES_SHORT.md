# Nightfall Diaries — AUTO-BEST Production Rules (Short)

**Date:** 2026-11-21  
**Budget:** **$0**, no card or paid fallback  
**Execution:** GitHub Actions/cloud only; no owner's PC  
**Approval:** automatically rank and choose best technically viable candidates; do not ask the owner to approve each shot  
**Public release:** **fail closed** until the WHOLE film actually passes real visual, identity, natural speaking/lip-sync and platform checks.

## Every episode
1. Keep canonical stories and locked voice/character identifiers; rewrite for stronger hooks without losing original endings.
2. Prepare physically coherent full-scene keyframes. Characters must share the same foreground/background depth, consistent lighting and meaningful action.
3. Generate **genuine moving footage** from a legitimate $0 source. Never fake film by panning still pictures or reusing rejected 2.5D puppets.
4. Keep each actual candidate, hash, prompt, audio cue and quality evidence in a **private/draft** persistent store.
5. Score frames for basic motion, sharpness, black gaps and crop proxies; auto-rank highest from the **candidates actually produced**. Technical scores **cannot** guarantee correct character, forest/fire context, captions or speaking; those require additional semantic/lip-sync verification.
6. Automatically reject obvious defects. Retry on the **next legitimate free quota period**, never bypass limits or secretly switch to paid models. With scarce free quota, 3 visual/4 speaking candidates are **targets**, not a guaranteed number per day.
7. Use locked Kokoro voices; **do not invent** natural speaking/lip-sync success. Do not publish speaking scenes without actual validated sync.
8. Assemble 3–6min complete animated film **only** from unique moving shots and a verified complete soundtrack. No missing shots, repeated clips, dead gaps or text/UI artifacts.
9. Upload publicly **only** after the finished video genuinely passes all quality gates and official platform authorization checks. Otherwise keep as private draft and continue according to verified free capacity.
10. Send Telegram status for attempted runs, generated/rejected shots, blockers, assembly and confirmed publication **only when those events occur**. Do not send fake-success messages.

## Current implementation in repo
- **E01:** `pilot/e01_free_ai_studio.py`, `pilot/e01_auto_quality.py`, `pilot/e01_studio_telegram.py`.
- Daily best-effort 10 AM **Africa/Cairo** workflow: `.github/workflows/nightfall_e01_free_ai_studio.yml`.
- Genuine original **180s Kokoro audio master** already archived; 45 unique approved cinematic clips and lip-sync **not produced**.
- Auto-quality = **technical ranking only**, not a claim of cinematic semantic accuracy.
- Telegram uses existing repository secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`; a missing secret must be reported honestly.
- This branch fixes the **three daily failures on Nov 19–21** caused by outdated rejection hashes.

**Never call a green Actions job a finished film.** The saved MP4, SHA, quality metrics and genuine platform confirmation are the evidence.
