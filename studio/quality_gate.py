"""Technical MP4 acceptance gate; cinematic acting needs separate visual approval."""
import json
import subprocess
from pathlib import Path

def check_media(path, mode="full"):
    if mode not in ("proof", "full"):
        raise ValueError("Unknown rendering mode")
    p = Path(path)
    if not p.is_file() or p.stat().st_size < 10_000:
        raise RuntimeError("Playable output file missing or suspiciously small")
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,codec_name,width,height",
         "-of", "json", str(p)],
        text=True, capture_output=True, check=True
    )
    info = json.loads(result.stdout)
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    seconds = float(info.get("format", {}).get("duration") or 0)
    lower, upper = (15, 30) if mode == "proof" else (90, 180)
    if not lower <= seconds <= upper:
        raise RuntimeError(f"INVALID_DURATION: {seconds:.1f}s; {mode} requires {lower}-{upper}s")
    if not v or v.get("codec_name") != "h264":
        raise RuntimeError("Video track must be H.264")
    if not a or a.get("codec_name") != "aac":
        raise RuntimeError("Audio track must be AAC")
    width, height = int(v.get("width", 0)), int(v.get("height", 0))
    if width < 720 or height < 1280 or abs(width / height - 9 / 16) > 0.015:
        raise RuntimeError(f"Invalid vertical video dimensions {width}x{height}")
    return {"mode": mode, "duration_seconds": round(seconds, 2),
            "width": width, "height": height, "video_codec": "h264",
            "audio_codec": "aac", "technical_check_passed": True,
            "cinematic_and_lipsync_review_passed": False}
