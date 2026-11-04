"""Read-only safety check for the known community ZeroGPU image-to-video demo.

This is a *candidate*, not a service guarantee. No inference is done here.
Do not replace it with paid providers or collect billing credentials.
"""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

SPACE_ID = "zerogpu-aoti/wan2-2-fp8da-aoti-faster"
ENDPOINT = "/generate_video"
MODEL_SOURCE = "https://huggingface.co/spaces/" + SPACE_ID
SPACE_HOST = "https://zerogpu-aoti-wan2-2-fp8da-aoti-faster.hf.space"
DEFAULT_NEGATIVE = (
    "still image, static pose, slideshow, photo pan, flicker, duplicate legs, "
    "changing face, distorted anatomy, subtitles, logo, watermark, low quality"
)

def settings(environ=None):
    env = os.environ if environ is None else environ
    space = (env.get("HF_VIDEO_SPACE") or SPACE_ID).strip()
    endpoint = (env.get("HF_VIDEO_ENDPOINT") or ENDPOINT).strip()
    if (space, endpoint) != (SPACE_ID, ENDPOINT):
        raise ValueError("External video provider requires a reviewed zero-cost adapter; do not assume it is free.")
    # Exact nine-input interface from this Space's published app.py:
    # image, prompt, steps, negative prompt, seconds, two scales, seed, randomize
    default = ["$image", "$prompt", 4, DEFAULT_NEGATIVE, 5.0, 1.0, 1.0, 42, False]
    override = (env.get("HF_VIDEO_ARGS_JSON") or "").strip()
    if override:
        try:
            args = json.loads(override)
        except json.JSONDecodeError as exc:
            raise ValueError("HF_VIDEO_ARGS_JSON must be valid JSON") from exc
        if not isinstance(args, list) or len(args) != 9 or args[:2] != ["$image", "$prompt"]:
            raise ValueError("This reviewed ZeroGPU Space requires nine documented input arguments")
        if not 1 <= int(args[2]) <= 8 or not 0.5 <= float(args[4]) <= 5.0:
            raise ValueError("Free probe limited to 1–8 steps and at most five seconds")
        if any(isinstance(value, (dict, list)) for value in args[2:]):
            raise ValueError("Unexpected complex Gradio arguments are not accepted")
        return space, endpoint, args
    return space, endpoint, default

def _read_json(url):
    req = Request(url, headers={"User-Agent":"Nightfall-Diaries-ZeroBudget-Probe/1.0",
                               "Accept":"application/json"})
    with urlopen(req, timeout=25) as response:
        return json.load(response)

def probe():
    space, endpoint, args = settings()
    result = {"space": space, "endpoint": endpoint,
              "candidate_is_zero_gpu": True,
              "inference_attempted": False,
              "public_publishing_attempted": False,
              "state": "BLOCKED", "notes": ""}
    try:
        hub = _read_json("https://huggingface.co/api/spaces/" + space)
        runtime = hub.get("runtime") or {}
        stage = runtime.get("stage")
        if stage and stage.upper() not in ("RUNNING",):
            raise RuntimeError("Space not running: " + str(stage))
        hardware = runtime.get("hardware") or {}
        if isinstance(hardware, dict):
            hardware = hardware.get("current") or hardware.get("requested")
        if hardware and not str(hardware).lower().startswith("zero"):
            raise RuntimeError("Space is not on free ZeroGPU: " + str(hardware))
        api = _read_json(SPACE_HOST + "/gradio_api/info")
        found = api.get("named_endpoints", {}) or {}
        if endpoint not in found:
            raise RuntimeError("Expected Gradio endpoint " + endpoint + " is not exposed; found: " + ", ".join(found)[:120])
        params = found[endpoint].get("parameters", [])
        if len(params) < len(args):
            raise RuntimeError("Gradio endpoint parameter count changed; stop rather than spend free quota")
        result.update({"state":"READY_FOR_ONE_QUOTA_LIMITED_TEST",
                       "parameters":len(params), "runtime_stage":stage,
                       "notes":"Read-only API verified. This is NOT proof of free quota, generated motion or lip sync."})
    except Exception as exc:
        result["notes"] = type(exc).__name__ + ": " + str(exc)[:220]
    return result

def main():
    from .restore import ROOT
    result = probe()
    out = ROOT / "output" / "motion_provider_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("ZERO_BUDGET_PROVIDER_PROBE:", json.dumps(result, sort_keys=True))
    print("READ_ONLY: no GPU generation, no upload, no cost")

if __name__ == "__main__":
    main()
