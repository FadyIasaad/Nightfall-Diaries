"""Kaggle free T4 GPU test; optional Ember image-to-video candidate.

Only runs when a human chooses the Kaggle action. Never publishes anywhere.
The Kaggle notebook executes in the user's own free quota, without paid APIs.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

RUN_MODE = "gpu_probe"  # overwritten by the GitHub staging tool
EMBER_B64 = ""           # ORIGINAL image bytes embedded by GitHub when needed
REFERENCE_SHA256 = "5a6653ed683ef86c2947b671a73f7b6d5353cb9d5c87a35b74daf4a8a3109503"
MODEL = "Lightricks/LTX-Video"
OUT_DIR = Path("/kaggle/working")
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT = OUT_DIR / "nightfall_kaggle_report.json"
MP4 = OUT_DIR / "nightfall_ember_candidate.mp4"
PROMPT = (
    "Premium stylized 3D animation. Ember, a small four-legged russet fox cub with "
    "a cream muzzle and chest, large amber eyes, LEFT ear with white tip only, "
    "fluffy ivory-tail-tip, teal neck scarf embroidered with exactly ONE gold star. "
    "Rich magical forest at blue dusk, volumetric moonlight and distant orange firelight. "
    "Ember steps forward, senses the flame, slows and looks up in genuine fear. "
    "Grounded full-body acting, expressive eyes and ears, detailed soft fur and "
    "a slow cinematic dolly-in. No changes to the identity or scarf."
)
NEGATIVE = (
    "still portrait, photo zoom, no body movement, morphing, low poly, cheap cartoon, "
    "wrong ear tip, extra stars, deformed legs, duplicate tails, flicker, text, watermark"
)


def write_report(report):
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    report = {
        "purpose": RUN_MODE,
        "provider": "Kaggle free notebook (T4x2 requested; actual device recorded)",
        "model_candidate": MODEL if RUN_MODE == "ember_i2v" else None,
        "free_gpu_confirmed": False,
        "gpu_devices": [],
        "inference_attempted": False,
        "quality_approved": False,
        "publication_attempted": False,
        "paid_api_calls": False,
        "output_mp4": None,
        "result": "BLOCKED",
    }
    try:
        if RUN_MODE not in ("gpu_probe", "ember_i2v"):
            raise ValueError("Unsupported job mode")
        import torch
        count = torch.cuda.device_count()
        if not torch.cuda.is_available() or not count:
            raise RuntimeError("No Kaggle GPU allocated; verify account GPU access/quota")
        for i in range(count):
            props = torch.cuda.get_device_properties(i)
            torch.cuda.set_device(i)
            # Real CUDA computation: cuda.is_available alone is insufficient.
            result = (torch.tensor([1.0, 2.0], device="cuda") * 3).sum().item()
            if abs(result - 9.0) > 0.01:
                raise RuntimeError("GPU calculation failed")
            report["gpu_devices"].append({
                "name": props.name, "vram_gib": round(props.total_memory / (1024 ** 3), 2)
            })
        report["free_gpu_confirmed"] = True
        if RUN_MODE == "gpu_probe":
            report["result"] = "GPU_TEST_PASSED_NO_VIDEO_GENERATED"
            return
        # T4 does not provide the 24GB on ONE device required by Wan2.2-5B.
        # Test a much smaller original LTX-Video open-weights image-to-video model.
        if not all("T4" in x["name"].upper() for x in report["gpu_devices"]):
            raise RuntimeError("Not the approved T4 test environment")
        if max(x["vram_gib"] for x in report["gpu_devices"]) < 14:
            raise RuntimeError("Less than 14GiB VRAM on a single GPU")
        if not EMBER_B64:
            raise RuntimeError("Original Ember reference was not embedded; stop")
        png = base64.b64decode(EMBER_B64, validate=True)
        if hashlib.sha256(png).hexdigest() != REFERENCE_SHA256:
            raise RuntimeError("Original Ember reference SHA256 mismatch")
        # No subscriptions, API calls to paid providers, or third-party upload.
        # Model download from its public Hugging Face repository only.
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q",
             "diffusers>=0.35,<0.39", "transformers>=4.45,<5",
             "accelerate>=1,<2", "safetensors", "sentencepiece",
             "protobuf", "imageio", "imageio-ffmpeg", "pillow"],
            check=True, timeout=540,
        )
        from PIL import Image
        from diffusers import LTXImageToVideoPipeline
        from diffusers.utils import export_to_video

        image = Image.open(io.BytesIO(png)).convert("RGB").resize((320, 576))
        # Explicit float16 for T4 (bf16 is not a native T4 compute format).
        pipe = LTXImageToVideoPipeline.from_pretrained(
            MODEL, torch_dtype=torch.float16
        )
        pipe.enable_model_cpu_offload()
        pipe.vae.enable_tiling()
        report["inference_attempted"] = True
        # First smoke clip: 49 frames at 24fps (~2s), NOT a final 720p quality gate.
        frames = pipe(
            image=image, prompt=PROMPT, negative_prompt=NEGATIVE,
            width=320, height=576, num_frames=49, frame_rate=24,
            num_inference_steps=18, guidance_scale=3.5,
            decode_timestep=0.05, decode_noise_scale=0.025,
            generator=torch.Generator(device="cpu").manual_seed(41),
        ).frames[0]
        export_to_video(frames, str(MP4), fps=24)
        if not MP4.exists() or MP4.stat().st_size < 10_000:
            raise RuntimeError("No valid nonempty video candidate produced")
        report["result"] = "CANDIDATE_CREATED_REQUIRES_OWNER_VISUAL_QA"
        report["output_mp4"] = MP4.name
        report["note"] = (
            "Low-resolution 2-second smoke clip only. Not Flow-grade approval. "
            "No speech, Kokoro lip-sync, final episode, or publishing."
        )
    except Exception as exc:
        report["result"] = "BLOCKED"
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)[:350]
        traceback.print_exc()
        raise
    finally:
        write_report(report)
        print("NIGHTFALL_KAGGLE_RESULT", report["result"])
        print("NIGHTFALL_NO_PUBLISHING", True)


if __name__ == "__main__":
    main()
