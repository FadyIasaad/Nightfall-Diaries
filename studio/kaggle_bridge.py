"""Stage & dispatch a private Kaggle free GPU notebook from existing GitHub Actions.

The only cloud commands are Kaggle's documented kernels push/status/output.
No Google Cloud billing, paid endpoint, new socials, or scheduler is involved.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from .restore import ROOT

EMBER_PATH = ROOT / "seasons/S01_the_last_little_fox/characters/s01_ember/cloud_reference.png"
LOCKS_PATH = ROOT / "seasons/S01_the_last_little_fox/characters/cloud_reference_locks.json"
TEMPLATE = ROOT / "kaggle/nightfall_gpu_job.py"
KERNEL_SLUG = "nightfall-t4-ember-safe"
SUPPORTED_MODES = ("gpu_probe", "ember_i2v")
MAX_IMAGE_BYTES = 8_000_000


def safe_owner(owner):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,49}", owner or ""):
        raise ValueError("KAGGLE_USERNAME must be your Kaggle profile slug")
    return owner


def original_ember_bytes():
    expected = json.loads(LOCKS_PATH.read_text(encoding="utf-8"))["s01_ember"]
    raw = EMBER_PATH.read_bytes()
    if len(raw) > MAX_IMAGE_BYTES or raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Original Ember PNG missing or unexpectedly large")
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Ember SHA256 does not match the original immutable lock")
    return raw


def stage(mode, owner, directory):
    """No external calls; embed the original image for an optional proof run."""
    if mode not in SUPPORTED_MODES:
        raise ValueError("Unsupported Kaggle mode")
    owner = safe_owner(owner)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    embedded = base64.b64encode(original_ember_bytes()).decode("ascii") if mode == "ember_i2v" else ""
    source = TEMPLATE.read_text(encoding="utf-8")
    source = source.replace('RUN_MODE = "gpu_probe"  # overwritten by the GitHub staging tool',
                            'RUN_MODE = ' + repr(mode))
    source = source.replace('EMBER_B64 = ""           # ORIGINAL image bytes embedded by GitHub when needed',
                            'EMBER_B64 = ' + repr(embedded))
    if f"RUN_MODE = {mode!r}" not in source or "EMBER_B64 = " not in source:
        raise RuntimeError("Kaggle source template changed unexpectedly")
    (directory / "nightfall_run.py").write_text(source, encoding="utf-8")
    metadata = {
        "id": owner + "/" + KERNEL_SLUG,
        "title": KERNEL_SLUG,
        "code_file": "nightfall_run.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": mode == "ember_i2v",
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
        "model_sources": [],
    }
    (directory / "kernel-metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def runner(args, timeout=120):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=timeout, check=False)
    # No API token is passed on the command line; CLI reads it from environment.
    if p.returncode:
        raise RuntimeError("Kaggle CLI failed: " + (p.stdout or "")[-700:])
    return p.stdout or ""


def dispatch(mode, owner, output_dir, max_wait_seconds=2000, dry_run=False):
    owner = safe_owner(owner)
    if mode not in SUPPORTED_MODES:
        raise ValueError("Unsupported mode")
    output_dir = Path(output_dir)
    staged = output_dir / "kaggle_staged"
    metadata = stage(mode, owner, staged)
    info = {
        "status": "STAGED_NO_CLOUD_RUN" if dry_run else "NOT_STARTED",
        "mode": mode, "kernel_id": metadata["id"],
        "requested_accelerator": "NvidiaTeslaT4",
        "paid_api_calls": False, "publishing": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = output_dir / "kaggle_dispatch.json"
    def save():
        summary.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    save()
    if dry_run:
        return info
    if not os.getenv("KAGGLE_API_TOKEN"):
        info["status"] = "BLOCKED_KAGGLE_API_TOKEN_MISSING"
        save()
        raise RuntimeError("Add the KAGGLE_API_TOKEN GitHub Actions secret first")
    # Single manually dispatched Kaggle job. No retries or automatic re-run.
    try:
        info["status"] = "SUBMITTING"
        save()
        print(runner(["kaggle", "kernels", "push", "-p", str(staged),
                      "--accelerator", "NvidiaTeslaT4",
                      "--timeout", "1800"], timeout=150)[-800:])
        info["status"] = "SUBMITTED"
        save()
        deadline = time.monotonic() + max_wait_seconds
        while time.monotonic() < deadline:
            result = runner(["kaggle", "kernels", "status", metadata["id"]],
                            timeout=60)
            state = result.lower()
            if re.search(r"\b(complete|completed|success|succeeded)\b", state):
                info["status"] = "KAGGLE_RUN_COMPLETED"
                break
            if re.search(r"\b(error|failed|cancelled|canceled)\b", state):
                raise RuntimeError("Kaggle run failed: " + result[-450:])
            time.sleep(25)
        else:
            raise TimeoutError("Kaggle run still pending after poll deadline; check Kaggle sessions")
        outputs = output_dir / "kaggle_results"
        outputs.mkdir(exist_ok=True)
        runner(["kaggle", "kernels", "output", metadata["id"],
                "-p", str(outputs), "-o"], timeout=150)
        report_file = outputs / "nightfall_kaggle_report.json"
        if not report_file.exists():
            raise RuntimeError("Kaggle did not produce the expected GPU report")
        report = json.loads(report_file.read_text(encoding="utf-8"))
        info["gpu_report_result"] = report.get("result")
        info["gpu_devices"] = report.get("gpu_devices", [])
        if mode == "gpu_probe" and report.get("result") != "GPU_TEST_PASSED_NO_VIDEO_GENERATED":
            raise RuntimeError("GPU smoke test did not pass")
        if mode == "ember_i2v":
            video = outputs / "nightfall_ember_candidate.mp4"
            if report.get("result") != "CANDIDATE_CREATED_REQUIRES_OWNER_VISUAL_QA" or not video.exists():
                raise RuntimeError("Video candidate missing/failed; see Kaggle report")
        info["status"] = "PROOF_COMPLETE_NOT_APPROVED"
        return info
    except Exception as exc:
        info["status"] = "BLOCKED"
        info["failure_type"] = type(exc).__name__
        info["reason"] = str(exc)[:600]
        raise
    finally:
        save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=SUPPORTED_MODES, required=True)
    parser.add_argument("--owner", default=os.environ.get("KAGGLE_USERNAME", ""))
    parser.add_argument("--output-dir", default="output/kaggle_dispatch")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    info = dispatch(args.mode, args.owner, args.output_dir, dry_run=args.dry_run)
    print(json.dumps(info, sort_keys=True))


if __name__ == "__main__":
    main()
