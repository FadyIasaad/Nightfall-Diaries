# Tiny Brave Tails - Stability Fix Notes

This package is a full stability update, not a blind patch.

## Main fixes
1. Kept the character-based dramatic voice system.
2. Kept the full pipeline: IDEA -> GENERATED -> VIDEO_CREATED -> UPLOADED.
3. Fixed Gemini malformed/truncated JSON failures by:
   - Requesting strict JSON output when supported.
   - Increasing output capacity.
   - Reducing randomness.
   - Retrying the whole Gemini generation + parse + validation step.
   - Falling back to another Gemini model if a model repeatedly returns bad JSON.
4. Added JSON parsing errors to retryable transient errors in `tbt_common.py`.
5. Added `GEMINI_MODEL: gemini-1.5-flash` explicitly to story workflows.

## Correct run order
1. Generate First Story
2. Generate Video
3. Upload YouTube

Or run the full workflow only after GitHub Secrets are correct.
