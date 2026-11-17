# LTX-2.3 zero-budget full-scene proof — quality verdict (2026-11-18)

Run: https://github.com/FadyIasaad/Nightfall-Diaries/actions/runs/44188101006

## Technical result
- Official public Lightricks/LTX-2-3 Space via unauthenticated ZeroGPU
- Generated an actual 4.042-second H.264 video at 512×768, with an audio stream
- The animal and camera demonstrably change across frames; a detailed forest is in-scene, unlike CPU cutouts
- No paid API key, owner token, social upload, or credit card was used

## Visual result: **REJECTED**
Examined 1s, 2s, 3s, 4s frames in the genuine generated MP4:
- Giant black top strip includes a fake social-media/Twitter-like logo and spurious text (e.g., 'Vryriof')
- Giant black bottom strip includes multiple pseudo social/media control icons
- Screen-space artifacts are present for the entire generation, despite the instruction requesting no text/UI
- The fox is newly invented from a prompt, **not** a source-locked Ember; character appearance is inconsistent with approved image
- Audio track exists, but character speech timing, actual dialogue, sound quality and lip-sync are **not** verified

This proof passes the technical MP4 check but **fails the actual quality standard**. Do **not merge this PR as a production renderer**; do not make an episode or public post from this output.

## Changed strategy
A reliable attempt cannot rely on text-to-video alone. Next candidate should start from an approved, coherent full-scene keyframe: locked Ember reference plus a cinematic genuine forest environment rendered *together in one frame*, no preprinted UI or cards. Then run image-to-video with short actions and maintain visual continuity; independently audition a character + locked Kokoro WAV audio-driven speaking clip. Test the exact model service's free access and expenses before an actual call. Reject if either (1) original character drifts, (2) synthetic UI/text appears, (3) character mouth/body do not naturally follow the voice, (4) foreground/background look disconnected, (5) action stutters, repeats or leaves dead time.

The hard requirement remains 100% cloud and zero payment; this free quota is not sufficient to guarantee daily 3–6 minute premium episodes. The old 2.5D renderer must not be an automatic fallback.
