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
import tempfile
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




def _redact_diagnostic(value):
    """Store bounded diagnostics without accidentally disclosing an API token."""
    value = str(value)
    for key in ("KAGGLE_API_TOKEN", "KAGGLE_KEY"):
        secret = os.getenv(key)
        if secret:
            value = value.replace(secret, "[REDACTED]")
    return value[-60000:]


def diagnose_last(owner, output_dir):
    """Read only: inspect an existing Kaggle kernel; NEVER push or allocate GPU."""
    owner = safe_owner(owner)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    kernel_id = owner + "/" + KERNEL_SLUG
    info = {
        "mode": "diagnose",
        "kernel_id": kernel_id,
        "status": "DIAGNOSTIC_INCOMPLETE",
        "paid_api_calls": False,
        "gpu_submission_attempted": False,
        "publishing": False,
        "kaggle_status": "",
        "logs_downloaded": False,
        "output_downloaded": False,
    }
    report_path = output_dir / "kaggle_diagnostic.json"
    try:
        if not os.getenv("KAGGLE_API_TOKEN"):
            info["status"] = "BLOCKED_KAGGLE_API_TOKEN_MISSING"
            return info
        # kaggle-cli 1.8.4 has NO 'kernels logs' command. The real
        # worker .log is delivered by 'kernels output', even for ERROR runs.
        try:
            info["kaggle_status"] = _redact_diagnostic(runner(
                ["kaggle", "kernels", "status", kernel_id], timeout=75
            ))[-1500:]
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            info["kaggle_status_error"] = _redact_diagnostic(str(exc))[-500:]

        # Check the ACCELERATOR actually recorded on Kaggle, independently
        # of the local request. This only downloads metadata/code into a
        # short-lived folder: it does NOT launch a new GPU session.
        try:
            with tempfile.TemporaryDirectory() as temp:
                runner(["kaggle", "kernels", "pull", kernel_id,
                        "-p", temp, "-m"], timeout=90)
                meta_path = Path(temp) / "kernel-metadata.json"
                if not meta_path.is_file():
                    raise RuntimeError("Kaggle metadata file unavailable")
                remote = json.loads(meta_path.read_text(encoding="utf-8"))
                info["remote_gpu_enabled"] = remote.get("enable_gpu")
                info["remote_machine_shape"] = remote.get("machine_shape")
                info["remote_metadata_checked"] = True
        except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
            info["remote_metadata_error"] = _redact_diagnostic(str(exc))[-500:]

        results = output_dir / "kaggle_results"
        results.mkdir(exist_ok=True)
        try:
            runner(
                ["kaggle", "kernels", "output", kernel_id,
                 "-p", str(results), "-o"],
                timeout=120
            )
            info["output_downloaded"] = True
            info["output_files"] = sorted(
                p.name for p in results.iterdir() if p.is_file()
            )[:30]

            # Kaggle writes e.g. 'nightfall-t4-ember-safe.log' to output.
            # Sanitize and limit its size before publishing the CI artifact.
            worker_logs = sorted(
                p for p in results.glob("*.log") if p.is_file()
            )
            if worker_logs:
                with worker_logs[0].open(
                    "r", encoding="utf-8", errors="replace"
                ) as handle:
                    # Avoid embedding full scripts, images, or huge raw logs
                    # in Actions artifacts; only last 60k chars of early text.
                    raw = handle.read(100_000)
                lines = raw.splitlines()
                bounded = "\n".join(line[:1200] for line in lines)
                log_text = _redact_diagnostic(bounded)
                (output_dir / "kaggle_worker_logs.txt").write_text(
                    log_text + "\n", encoding="utf-8"
                )
                info["logs_downloaded"] = True
                info["log_source"] = worker_logs[0].name

            gpu_report = results / "nightfall_kaggle_report.json"
            if gpu_report.is_file():
                data = json.loads(gpu_report.read_text(encoding="utf-8"))
                info["gpu_report_result"] = data.get("result")
                info["cuda_devices"] = data.get("gpu_devices", [])
                info["cuda_reported_available"] = bool(
                    data.get("free_gpu_confirmed", False)
                )
                if (
                    data.get("error_type") == "RuntimeError"
                    and "No Kaggle GPU allocated" in data.get("error", "")
                ):
                    info["root_cause"] = "KAGGLE_CUDA_NOT_ALLOCATED"
        except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
            info["output_error"] = _redact_diagnostic(str(exc))[-500:]
        status_text = info.get("kaggle_status", "").upper()
        if "KERNELWORKERSTATUS.ERROR" in status_text:
            info["status"] = "KAGGLE_WORKER_ERROR_DIAGNOSTIC_COLLECTED"
        elif info["logs_downloaded"] or info["output_downloaded"]:
            info["status"] = "DIAGNOSTIC_COLLECTED_REVIEW_ARTIFACTS"
        else:
            info["status"] = "DIAGNOSTIC_UNAVAILABLE_CHECK_KAGGLE_WEB_UI"
        return info
    finally:
        report_path.write_text(
            json.dumps(info, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        print("KAGGLE_READ_ONLY_DIAGNOSTIC:", info["status"])
        print("KAGGLE_GPU_SUBMISSION: NEVER")


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
        prior_status = info["status"]
        info["status"] = "BLOCKED"
        info["failure_type"] = type(exc).__name__
        info["reason"] = _redact_diagnostic(str(exc))[:600]
        # An errored Kaggle worker can expose its real traceback only in
        # Kaggle logs; fetch it once, without triggering another GPU run.
        if prior_status == "SUBMITTED":
            try:
                diagnostic = diagnose_last(owner, output_dir)
                info["diagnostic_status"] = diagnostic["status"]
                info["diagnostic_log_saved"] = diagnostic["logs_downloaded"]
            except Exception as diagnostic_exc:
                info["diagnostic_error"] = type(diagnostic_exc).__name__
        raise
    finally:
        save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=SUPPORTED_MODES + ("diagnose",), required=True)
    parser.add_argument("--owner", default=os.environ.get("KAGGLE_USERNAME", ""))
    parser.add_argument("--output-dir", default="output/kaggle_dispatch")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.mode == "diagnose":
        if args.dry_run:
            parser.error("diagnose does not support --dry-run")
        info = diagnose_last(args.owner, args.output_dir)
    else:
        info = dispatch(args.mode, args.owner, args.output_dir, dry_run=args.dry_run)
    print(json.dumps(info, sort_keys=True))


if __name__ == "__main__":
    main()
