# Nightfall E01 — Daily cinematic-only production checkpoint

**Date checked: 18 Nov 2026. Status: NOT PRODUCING A FINISHED EPISODE.**

## Recent GitHub evidence
- Run [44353303816](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/44353303816): scheduled 10 AM Cairo speaking **preflight succeeded**, no generated speaking clip.
- Run [44356160663](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/44356160663): superseded illustrated CPU cutout renderer still ran on an independent schedule. Previously rejected by owner, so daily trigger was removed in this change; kept manual-only for archival diagnostics.
- Run [44355402499](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/44355402499): previous Agnes workflow scheduled repeatedly and failed; its schedule was removed. No paid inference or social posting authorized by this change.
- Archived HF one-click workflow scheduled two skipped runs per day; those redundant schedules were removed. Its existing job remains disabled.
- E01 real speaking test [44195870986](https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/44195870986) generated a 1.85-second Kokoro WAV but hit exhausted **anonymous free ZeroGPU quota**. No spoken animal video was produced.

## Realistic free model candidates (public runtime metadata only)
- [JoyVASA](https://github.com/jdh-algo/JoyVASA) explicitly supports **audio-driven animal face animation**, including LivePortrait animal checkpoints. A community [ZeroGPU Space](https://huggingface.co/spaces/Ammunity/joyvasa-avatar) existed but was **PAUSED when checked**. Do not claim it available just because the model is open source.
- [LongCat-Video-Avatar 1.5](https://huggingface.co/spaces/victor/LongCat-Video-Avatar-1.5) uses an image + speech + cinematic prompt and may generalize to stylized animals. Its public ZeroGPU demo declares a **300-second GPU reservation**. Anonymous free allowance is ~**120 GPU seconds/day** and cannot safely accommodate that reservation. A free registered account has a larger allowance but NO token or paid upgrade is authorized. Not a viable anonymous scheduled fallback.
- [Hugging Face ZeroGPU limits](https://huggingface.co/docs/hub/spaces-zerogpu) apply across public Spaces and can change. Public provider status alone is not quota proof.

The daily workflow now runs `pilot/e01_animal_provider_preflight.py` using **anonymous GET-only public Space metadata**. It reports `PAUSED_OR_UNAVAILABLE`, `FREE_ANONYMOUS_QUOTA_TOO_SMALL`, or `CANDIDATE_ONLY_MODEL_AND_QUALITY_UNVERIFIED`. It never calls a generator or consumes GPU quota.

## Exact owner production requirements
The first original fox episode must have 3–6 minutes of **genuine** scene motion, consistent character identity and detail, natural audio-driven speaking, fully integrated rich backgrounds, meaningful camera direction, and no static loops, black gaps, visible UI stickers or subtitles card.

- Original Ember reference, script and character/voice locks unchanged.
- `seasons/S01_the_last_little_fox/revised_screenplays/E01_2026-11-18.json`: 15 cinematic scene outlines, 45 distinct shots **planned, not generated**.
- Original short Kokoro audio verified, animal lip-sync remains **unproved**.
- No GPU hosting/paid service/token or credit card is used. No automatic social upload.
- The only scheduled E01 workflow is `.github/workflows/nightfall_e01_daily_real_speaking.yml`, **10:00 AM Africa/Cairo** and read-only status. GitHub scheduled invocation is best effort.

## Next gate
Identify an actually running **animal-capable** image+audio video demo with a job reservation that fits anonymous ZeroGPU quota and an official API schema. Produce **one** short source-locked Ember + original Kokoro speech clip, then visually inspect muzzle movement, ear/scarf/star identity and environment integration. If poor or unavailable, stop and report, do not substitute a cutout, motion blur, still slides or video without legitimate acting. Until this passes, the finished E01 and daily publishing stay BLOCKED.
