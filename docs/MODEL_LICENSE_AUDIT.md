# Nightfall Diaries — Phase 0 Model / Media License Review
**Checked:** November 5, 2026. **Scope:** model/library selection for a potential monetized YouTube/Facebook/Instagram/TikTok project, not approval of model performance or Kaggle hardware.

This is a provenance and eligibility screen, **not legal advice**. Model cards and service terms can change; pin exact model weights/revisions and recheck when Phase 1 begins. All GPU services and third-party sites may impose separate usage restrictions.

| Component or candidate | Licence / source | Phase 0 disposition | Critical caveat |
|---|---|---|---|
| Existing **Kokoro-82M** neural TTS | Apache-2.0 — [official weights](https://huggingface.co/hexgrad/Kokoro-82M) | KEEP, candidate commercially usable | Keep all existing voice IDs, speed/language locks; verify each supplemental audio asset's provenance. |
| **Whisper large-v3** transcription | Apache-2.0 — [official model](https://huggingface.co/openai/whisper-large-v3) | ELIGIBLE CANDIDATE | GPU/CPU performance, languages, and actual transcript alignment not benchmarked. |
| **WhisperX** alignment code | BSD-2-Clause — [upstream](https://github.com/m-bain/whisperX) | ELIGIBLE CODE CANDIDATE | Bundled dependencies and acoustic/alignment models require separate licensing checks. |
| **Stable Diffusion XL base 1.0** | CreativeML Open RAIL++-M — [official card](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) | CONDITIONAL candidate | Respect use-based restrictions and include required downstream license terms; **not** a simple Apache licence. Check any LoRA training/reference data rights. |
| **FLUX.1-schnell** | Apache-2.0 — [official card](https://huggingface.co/black-forest-labs/FLUX.1-schnell) | ELIGIBLE LICENSE, HARDWARE UNPROVEN | 12B-class model may be too heavy for practical T4/P100 inference in the desired budget. |
| **FLUX.1-dev** | FLUX.1-dev **Non-Commercial** Licence — [official card](https://huggingface.co/black-forest-labs/FLUX.1-dev) | **DO NOT ADOPT** for monetized production under the free NC licence | A separately granted commercial licence would be contrary to the strict $0 assumption unless expressly free and authorized. |
| **Wan2.2-TI2V-5B** | Apache-2.0 — [official model](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B) | ELIGIBLE LICENSE, **NOT FIT-VERIFIED** | Weights/models total tens of GB; T4 has limited VRAM, so quantization/offload and actual speed must be tested before promising any episode throughput. |
| **LTX-2.3** | **LTX-2 Community License**, not Apache for weights — [official model](https://huggingface.co/Lightricks/LTX-2.3), [actual terms](https://huggingface.co/Lightricks/LTX-2.3/blob/main/LICENSE) | **LEGAL/RESOURCE REVIEW REQUIRED** | Custom restrictions; large commercial entities may require separate paid licence; model weights distinct from Apache-licensed code. Do not install by name without reading exact terms. |
| **Depth Anything V2 Small** | Apache-2.0 — [official weights](https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf) | ELIGIBLE CANDIDATE | Depth only; parallax alone does not establish genuine character acting. Validate artifacts and quality. |
| **FFmpeg / libx264 / fonts** | Varies by build/components; [FFmpeg legal](https://ffmpeg.org/legal.html) | EXISTING TOOLCHAIN; REVIEW FINAL BINARY/ENCODER | Check shipping/distribution implications, build options, font licences and patent obligations; public MP4 is not a redistribution of every binary. |
| **Blender** (legacy) | GPL code; [official licence](https://www.blender.org/about/license/) | LEGACY, NOT QUALITY-APPROVED | GPL alone does not license character assets; old procedural spherical figures fail the owner's visual standard. |
| **Music, SFX, title art, fonts, LoRA datasets** | Per-asset provenance, e.g. CC0 / properly attributed commercial-use license | **BLOCKED UNTIL SOURCED AND LOGGED** | No blanket permission from a "free" website or model. Maintain an asset-by-asset `audio_licenses.json`/manifest with URL, author, licence and attribution obligations. |
| **Original character reference PNGs** | Source/provenance presently not documented in the repo | **PROVENANCE AUDIT REQUIRED** | Existing SHA-256 locks show unmodified bytes, **not ownership or commercial reuse rights**. Get and preserve a provenance record before training LoRAs or commercial release. |

## Provider/compute terms and engineering reality

- **Kaggle:** its [own documentation](https://www.kaggle.com/docs/efficient-gpu-usage) states a free weekly GPU limit (30h, sometimes more), not a contractual entitlement. The [official Kaggle CLI](https://github.com/Kaggle/kaggle-cli/blob/main/docs/kernels.md) supports `kernels push`, `status` and `output`, including an accelerator flag. These establish **API capabilities**, not access to this owner's account, available quota, eligibility for commercial production, or sufficient video quality.
- **Hugging Face:** anonymous 126-GPU-second-per-5-second request exhausted its allowance in the observed E02 run. Keep that engine as a bonus experiment, not the primary continuous-film generator. No alternate-account quota evasion.
- **AI-generated content and monetization:** review each destination's latest synthetic-media disclosure and originality policies before enabling production. Keep traceable licences and original story/character evidence.
- **No real weights, fine-tuning data, or Kaggle GPU have been fetched, trained, or benchmarked in this Phase 0 review.**

## Acceptance
Phase 0 can document license status, but **cannot approve** a model for commercial delivery until (a) exact revision/terms are pinned, (b) character-image provenance is established, (c) audio/assets are logged, (d) hardware benchmark and owner-quality review pass. **All public publishing flags stay false.**
