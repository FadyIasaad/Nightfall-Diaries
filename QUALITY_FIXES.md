# Tiny Brave Tails Quality/Error Fix Update

This update fixes the real failure points without lowering video or sound quality.

## Fixed
- YouTube upload now uses the Web OAuth secrets: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`.
- Upload now refreshes the token before upload.
- Upload now verifies the returned YouTube video ID with `videos.list` before writing `UPLOADED` to the sheet.
- Upload now searches recursively inside `output/`, not only the top output folder.
- Upload now writes `UPLOAD_ERROR` and `error_message` back to the sheet if the upload fails.
- Upload-only workflow no longer uses the wrong `YOUTUBE_TOKEN_JSON` path only.
- All workflows install FFmpeg, espeak fallback, and fonts needed for Arabic/English subtitles.
- Video quality increased: 1080x1920, H.264 high profile, CRF 18, 7.5 Mbps target, faststart.
- Audio is normalized scene-by-scene with FFmpeg loudnorm to reduce sudden jumps and prevent ugly sound imbalance.
- Subtitle box is larger and safer; English/Arabic wrapping supports up to 4 lines to reduce cut-off.
- Pillow/MoviePy compatibility patch added.
- Old `__pycache__`, fake `New.py`, and nested old zip clutter removed.
- Category uploader now supports both old `YOUTUBE_TOKEN_JSON` and the newer Web OAuth secret method.

## Important
The sheet is readable and has the expected columns. Do not manually mix `youtube_video_id` and `video_file_path` in the same cell. The updated script writes them separately when the columns exist.

## Best workflow to use
Use:

`Actions -> Create And Upload Now -> Run workflow`

This is the cleanest path: story -> video -> verify MP4 -> upload -> verify YouTube -> update sheet.
