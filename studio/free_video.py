"""Free public ZeroGPU Wan2.2 image-to-video client; no fallback to static pictures.

Input schema confirmed from the public Space app source. Availability, quota,
quality and character continuity are NOT guaranteed.
"""
import json
import os
import re
import shutil
from pathlib import Path
from .motion_provider import settings

class VideoUnavailable(RuntimeError):
    pass

class QuotaExhausted(VideoUnavailable):
    """Expected free-tier cap: keep checkpoints, retry after quota reset."""
    def __init__(self, reason, retry_seconds=86400):
        super().__init__(reason)
        self.retry_seconds=retry_seconds

def quota_retry_seconds(message):
    """Read provider HH:MM:SS. Add two-minute grace, default to 24h."""
    match=re.search(r"Try again in (\d+):(\d{2}):(\d{2})", message)
    if not match:
        return 86400
    hours, minutes, seconds=(int(x) for x in match.groups())
    return min(max(300,hours*3600+minutes*60+seconds+120),172800)


def find_video(value):
    if isinstance(value, str):
        p = Path(value)
        if p.is_file() and p.suffix.lower() in (".mp4",".mov",".webm"):
            return p
    if isinstance(value, dict):
        for key in ("video","path","name","value","data"):
            if key in value:
                p = find_video(value[key])
                if p: return p
    if isinstance(value, (list, tuple)):
        for v in value:
            p = find_video(v)
            if p: return p
    return None

def generate_video(image_file, prompt, destination, seconds=5.0):
    image_file = Path(image_file)
    if not image_file.is_file():
        raise VideoUnavailable("Locked character reference missing; no image substitution permitted.")
    try:
        space, endpoint, args = settings()
    except ValueError as exc:
        raise VideoUnavailable(str(exc)) from exc
    seconds = float(seconds)
    if not 4.9 <= seconds <= 5.0:
        raise VideoUnavailable("The first motion proof only supports documented ~5s ZeroGPU clips")
    args[4] = seconds
    try:
        from gradio_client import Client, handle_file
    except ImportError as exc:
        raise VideoUnavailable("Missing free Gradio client. Install requirements.txt only in the actual render job.") from exc
    safe_args = []
    for item in args:
        if item == "$image":
            safe_args.append(handle_file(str(image_file.resolve())))
        elif item == "$prompt":
            safe_args.append(prompt)
        else:
            safe_args.append(item)
    try:
        client = Client(space, token=(os.getenv("HF_TOKEN") or None))
        generated = client.predict(*safe_args, api_name=endpoint)
        result = find_video(generated)
    except Exception as exc:
        reason=str(exc)
        if "exceeded your ZeroGPU quota" in reason:
            raise QuotaExhausted(
                "ZeroGPU free allowance exhausted; saved clips are retained for a later cloud retry. "
                + reason[:310], retry_seconds=quota_retry_seconds(reason)
            ) from exc
        raise VideoUnavailable(
            "ZeroGPU provider unavailable; no payment or static-image fallback attempted. "
            f"Provider said: {type(exc).__name__}: {reason[:230]}"
        ) from exc
    if result is None:
        raise VideoUnavailable("ZeroGPU did not return an actual local video file.")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(result, destination)
    if destination.stat().st_size < 10_000:
        destination.unlink(missing_ok=True)
        raise VideoUnavailable("Tiny/corrupt motion clip; refusing to treat it as video")
    return destination
