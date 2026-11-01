"""Free-tier Hugging Face Gradio image-to-video adapter.

A public Space is not a guaranteed service; this code insists on actual MP4
pixels from the remote model, never a slideshow or fabricated success.
"""
import json
import os
import shutil
from pathlib import Path
from gradio_client import Client, handle_file

class VideoUnavailable(RuntimeError):
    pass

def find_video(value):
    if isinstance(value, str):
        p = Path(value)
        if p.is_file() and p.suffix.lower() in (".mp4", ".mov", ".webm"):
            return p
    if isinstance(value, dict):
        for key in ("video", "path", "name", "value", "data"):
            if key in value:
                p = find_video(value[key])
                if p: return p
    if isinstance(value, (list, tuple)):
        for v in value:
            p = find_video(v)
            if p: return p
    return None

def generate_video(image_file, prompt, destination):
    space = os.getenv("HF_VIDEO_SPACE", "JCisHERE/wan2-2-i2v-v3").strip()
    endpoint = os.getenv("HF_VIDEO_ENDPOINT", "/generate").strip()
    token = os.getenv("HF_TOKEN") or None
    if not image_file or not Path(image_file).is_file():
        raise VideoUnavailable("Missing the approved cinematic start-frame image in studio/assets/ember_approved.jpg.")
    if not space or "/" not in space:
        raise VideoUnavailable("HF_VIDEO_SPACE must be a public Gradio image-to-video Space ID.")
    template = os.getenv("HF_VIDEO_ARGS_JSON", '["$image", "$prompt"]')
    try:
        positional = json.loads(template)
        if not isinstance(positional, list): raise ValueError("not a JSON list")
    except ValueError as exc:
        raise VideoUnavailable("HF_VIDEO_ARGS_JSON must be a JSON list of Gradio endpoint arguments.") from exc
    args = []
    for value in positional:
        if value == "$image":
            args.append(handle_file(str(Path(image_file).resolve())))
        elif value == "$prompt":
            args.append(prompt)
        else:
            args.append(value)
    try:
        client = Client(space, token=token)
        generated = client.predict(*args, api_name=endpoint)
        actual = find_video(generated)
    except Exception as exc:
        raise VideoUnavailable(
            "Free video service unavailable, quota exhausted, or Gradio endpoint arguments changed. "
            f"Check the Space's 'Use via API' docs for {space} endpoint {endpoint}. "
            f"Provider error: {type(exc).__name__}: {str(exc)[:240]}"
        ) from exc
    if actual is None:
        raise VideoUnavailable("The free provider did not return a real video file. Refusing slideshow fallback.")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(actual, destination)
    if destination.stat().st_size < 10000:
        destination.unlink(missing_ok=True)
        raise VideoUnavailable("Returned MP4 too small to be a credible animated scene.")
    return destination
