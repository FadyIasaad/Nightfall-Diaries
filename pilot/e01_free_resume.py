"""Nightfall E01: resumable one-shot-at-a-time on ONE registered free HF account.

A single manual run may generate at most ONE genuinely fresh LTX motion shot.
No account rotation, no billable inference, no public uploads, no fake loops.
GitHub Actions cache + artifacts keep verified MP4/WAV checkpoints between runs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from pilot import e01_full_run as film
from studio.quality_gate import check_media
from studio.continuity import sha256

ROOT = film.ROOT
OUT = ROOT / "output/e01_resumable"
STATE = OUT / "progress.json"
VERSION = "e01-one-free-account-v1"
MAX_REQUESTS_PER_RUN = 1


def plan_digest(report):
    material = {
        "version": VERSION,
        "provider": film.SPACE, "api": film.API,
        "cinematic_ref": film.SOURCE_SHA,
        "scenes": [
            {
                "no": s["scene_no"], "voice": s["voice_id"],
                "text": s["script_text"], "prompt": s["ai_motion_prompt"],
                "image": s["reference_sha256"],
                "parts": s["subshot_seconds"]
            } for s in report["scenes"]
        ],
    }
    return hashlib.sha256(
        json.dumps(material, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def create_state(report):
    return {
        "schema": VERSION,
        "episode": film.EPISODE,
        "plan_sha256": plan_digest(report),
        "target_seconds": film.TARGET_SECONDS,
        "expected_distinct_shots": sum(len(s["subshot_seconds"]) for s in report["scenes"]),
        "completed": [],
        "voices": [],
        "technical_full_mp4": False,
        "human_cinematic_approved": False,
        "true_lipsync_verified": False,
        "published_anywhere": False,
        "paid_api_calls": False,
        "status": "READY_FOR_FREE_ACCOUNT_CHECK",
    }


def _save(state):
    OUT.mkdir(parents=True, exist_ok=True)
    temp = STATE.with_suffix(".json.tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    temp.replace(STATE)


def _safe_record(record, prefix):
    name = record.get("file")
    return (
        isinstance(name, str) and
        len(name) < 140 and
        Path(name).name == name and
        name.startswith(prefix) and
        (name.endswith(".mp4") or name.endswith(".wav"))
    )


def _verify_cache(state, plan):
    if (state.get("schema") != VERSION or state.get("episode") != film.EPISODE
            or state.get("plan_sha256") != plan_digest(plan)):
        raise RuntimeError("Resumed state does not match approved character/script/model plan")
    seen = set()
    for row in state.get("completed", []):
        no, part = row.get("scene"), row.get("part")
        if not isinstance(no, int) or not 1 <= no <= 14:
            raise RuntimeError("Invalid cached scene")
        spec = plan["scenes"][no - 1]
        if not isinstance(part, int) or not 1 <= part <= len(spec["subshot_seconds"]):
            raise RuntimeError("Invalid cached part")
        key = (no, part)
        if key in seen or not _safe_record(row, f"scene_{no:02d}_part_{part:02d}_"):
            raise RuntimeError("Duplicate or unsafe cached shot")
        seen.add(key)
        p = OUT / row["file"]
        if not p.is_file() or sha256(p) != row.get("sha256"):
            raise RuntimeError("Cached motion missing or SHA-256 mismatch; refusing to restart")
    for row in state.get("voices", []):
        no = row.get("scene")
        if not isinstance(no, int) or not 1 <= no <= 14:
            raise RuntimeError("Invalid cached voice number")
        if not _safe_record(row, f"voice_{no:02d}."):
            raise RuntimeError("Unsafe voice filename")
        f = OUT / row["file"]
        if not f.is_file() or sha256(f) != row.get("sha256"):
            raise RuntimeError("Voice WAV cache missing or SHA-256 mismatch")
    if len(state.get("completed", [])) > 36 or len(state.get("voices", [])) > 14:
        raise RuntimeError("Unexpected checkpoint count")
    return state


def load_state(plan):
    OUT.mkdir(parents=True, exist_ok=True)
    if STATE.exists():
        return _verify_cache(json.loads(STATE.read_text()), plan)
    if any(OUT.glob("scene_*_generated.mp4")):
        raise RuntimeError("Partial motion exists without matching manifest; no destructive restart")
    state = create_state(plan)
    _save(state)
    return state


def next_unfinished(state, plan):
    done = {(row["scene"], row["part"]) for row in state["completed"]}
    for s in plan["scenes"]:
        for part, seconds in enumerate(s["subshot_seconds"], 1):
            if (s["scene_no"], part) not in done:
                return s, part, seconds
    return None


def account_preflight(token, *, hf_api_factory=None, minimum_seconds=220):
    """Only a normal free personal account; reject PRO and unknown billing tiers."""
    if not token:
        raise RuntimeError("HF_TOKEN_MISSING: add a read token for ONE free HF account")
    if hf_api_factory is None:
        from huggingface_hub import HfApi
        hf_api_factory = HfApi
    api = hf_api_factory(token=token)
    who = api.whoami()
    if not isinstance(who, dict) or who.get("isPro") is not False:
        raise RuntimeError("HF_ACCOUNT_NOT_VERIFIED_FREE: decline paid or unknown tier")
    if who.get("type") not in (None, "user"):
        raise RuntimeError("Not an individual free account")
    # Added in huggingface_hub 2.1.0; fail closed if an old library is
    # installed instead of skipping the free quota check or using paid credits.
    get_quota = getattr(api, "get_zero_gpu_quota", None)
    if not callable(get_quota):
        raise RuntimeError(
            "HF_HUB_VERSION_TOO_OLD: huggingface_hub>=2.1.1 is required for "
            "read-only ZeroGPU quota verification"
        )
    try:
        q = get_quota()
    except Exception as exc:
        http_status = getattr(getattr(exc, "response", None), "status_code", None)
        if http_status in (401, 403):
            # Fine-grained HF tokens require Billing -> Read billing usage and
            # payment method status; this permission is READ-ONLY.
            raise RuntimeError(
                "HF_ZERO_GPU_QUOTA_PERMISSION_REQUIRED: create a free-account "
                "token with read-only Billing usage permission; no GPU call made"
            ) from None
        # Never include raw HTTP body, query string or token in Actions logs.
        raise RuntimeError(
            "HF_ZERO_GPU_QUOTA_CHECK_FAILED: " + type(exc).__name__
        ) from None
    base, remaining = float(q.base), float(q.remaining)
    if base <= 0 or base > 300.001:
        raise RuntimeError("ZeroGPU quota does not match a known non-billed free allowance")
    if float(q.overquota_used or 0) > 0:
        raise RuntimeError("Paid overquota detected: refuses to generate")
    return {
        "quota_base_seconds": base,
        "quota_remaining_seconds": remaining,
        "quota_resets_at": str(q.resets_at) if q.resets_at else None,
        "within_observed_budget": remaining >= minimum_seconds,
    }


def status():
    cast, plan = film.scene_plan()
    state = load_state(plan)
    next_part = next_unfinished(state, plan)
    return {
        "episode": film.EPISODE, "state": state["status"],
        "auth": "NOT_SENT_IN_STATUS_MODE",
        "shots_completed": len(state["completed"]),
        "shots_total": 36, "seconds_requested": film.TARGET_SECONDS,
        "real_motion_seconds": round(sum(float(x.get("seconds", 0))
                                          for x in state["completed"]), 2),
        "next": ({"scene": next_part[0]["scene_no"], "part": next_part[1],
                  "seconds": next_part[2]} if next_part else None),
        "automatic_publishing": False, "paid_api_calls": False,
    }


def resume_one_shot(*, client_factory=None, hf_api_factory=None):
    """No more than 1 fresh inference per explicit GitHub workflow execution."""
    event = os.getenv("GITHUB_EVENT_NAME")
    if not (event == "workflow_dispatch" or
            (event == "schedule" and
             os.getenv("NIGHTFALL_FREE_DAILY_ENABLED") == "YES")):
        raise RuntimeError("Not the authorized manual/daily free one-shot operation")
    if (os.getenv("GITHUB_REF") != "refs/heads/main" or
        os.getenv("NIGHTFALL_FREE_RESUME") != "YES" or
        os.getenv("GITHUB_RUN_ATTEMPT") != "1"):
        raise RuntimeError("Not the manually approved main-branch one-shot operation")
    token = os.getenv("HF_TOKEN", "")
    cast, plan = film.scene_plan()
    state = load_state(plan)
    target = next_unfinished(state, plan)
    if target is None:
        # Scheduled runs never spend GPU after the last of 36 genuine clips.
        if not state.get("technical_full_mp4"):
            state["status"] = "ALL_SHOTS_READY_AUTOMATIC_ASSEMBLY_PENDING"
            _save(state)
        return status()
    scene, number, seconds = target
    # Observed 5s xlarge request failed at 194s on unauthenticated tier;
    # conservative budget check errs toward waiting, not paying.
    required = 220 if seconds >= 4 else 140
    try:
        quota = account_preflight(token, hf_api_factory=hf_api_factory,
                                  minimum_seconds=required)
        if not quota["within_observed_budget"]:
            state["status"] = "PAUSED_FREE_QUOTA_INSUFFICIENT"
            state["quota_resets_at"] = quota["quota_resets_at"]
            _save(state)
            return status()
        if client_factory is None:
            from gradio_client import Client
            client_factory = Client
        client = client_factory(film.SPACE, token=token)
        params = (client.view_api(return_format="dict").get("named_endpoints", {})
                  .get(film.API, {}).get("parameters", []))
        if len(params) != 10:
            raise RuntimeError("LTX-2.5 API schema changed: no inference")
        # Continue from the last REAL model-generated frame, not an arbitrary still.
        film.OUT = OUT
        input_image = ROOT / scene["reference_file"]
        if number > 1:
            previous = next((r for r in state["completed"]
                             if r["scene"] == scene["scene_no"] and r["part"] == number - 1), None)
            if previous is None:
                raise RuntimeError("Continuity missing for prior shot")
            input_image = film.last_actual_frame(
                OUT / previous["file"], scene["scene_no"], number - 1)
        dest, actual = film.generate_shot(client, scene, number, seconds, input_image)
        if not dest.is_file():
            raise RuntimeError("No generated video to save")
        state["completed"].append({
            "scene": scene["scene_no"], "part": number,
            "file": dest.name, "sha256": sha256(dest),
            "seconds": round(actual, 3), "requested_seconds": seconds,
        })
        state["status"] = "PARTIAL_REAL_MOTION_UNAPPROVED"
        state["quota_resets_at"] = quota["quota_resets_at"]
        _save(state)
        return status()
    except Exception as exc:
        # Never persist raw exception content: HF exceptions can contain tokens.
        state["status"] = "BLOCKED_FREE_PROVIDER_OR_AUTH"
        state["error_type"] = type(exc).__name__
        _save(state)
        raise


def assemble_unapproved():
    """CPU-only assembly: all 36 verified moving shots required before any output."""
    event = os.getenv("GITHUB_EVENT_NAME")
    if event not in ("workflow_dispatch", "schedule"):
        raise RuntimeError("Assembly is allowed only in manual or scheduled workflow")
    if (os.getenv("GITHUB_REF") != "refs/heads/main"
            or os.getenv("NIGHTFALL_FREE_ASSEMBLE") != "YES"
            or os.getenv("GITHUB_RUN_ATTEMPT") != "1"):
        raise RuntimeError("Assembly requires authorized main-branch first-attempt workflow")
    if event == "schedule" and os.getenv("NIGHTFALL_FREE_DAILY_ENABLED") != "YES":
        raise RuntimeError("Scheduled assembly must be the authorized free daily run")
    cast, plan = film.scene_plan()
    state = load_state(plan)
    if next_unfinished(state, plan) is not None:
        raise RuntimeError("Cannot assemble incomplete E01: all 36 real motion clips required")
    # Idempotent: do not regenerate voices or film on every daily schedule.
    if state.get("technical_full_mp4"):
        existing = OUT / "S01_the_last_little_fox_E01_full_unapproved.mp4"
        if (not existing.is_file()
                or sha256(existing) != state.get("assembled_video_sha256")):
            raise RuntimeError("Previously assembled film SHA-256 missing/mismatch")
        return {
            "status": state["status"],
            "duration_seconds": state.get("full_duration_seconds"),
            "video_file": existing.name,
            "already_assembled": True,
            "public_publishing": False,
            "true_lipsync_verified": False,
        }
    film.OUT = OUT
    records = {(x["scene"], x["part"]): x for x in state["completed"]}
    voiced = []
    voice_records = {x["scene"]: x for x in state["voices"]}
    for spec in plan["scenes"]:
        number = spec["scene_no"]
        parts = [OUT / records[(number, part)]["file"]
                 for part in range(1, len(spec["subshot_seconds"]) + 1)]
        joined, actual = film.combine_unique_subshots(number, parts)
        if number in voice_records:
            wav = OUT / voice_records[number]["file"]
            audio_seconds = film.duration(wav)
        else:
            wav, audio_seconds = film.create_voice(spec, cast)
            voice_records[number] = {"scene": number, "file": wav.name,
                                     "sha256": sha256(wav)}
            state["voices"] = list(voice_records.values())
            _save(state)
        if actual < audio_seconds - 0.05:
            raise RuntimeError("Kokoro dialogue is longer than natural AI motion; no slowdown")
        voiced.append(film.join_scene(joined, wav, number, actual))
    listing = OUT / "e01_real_scenes.txt"
    listing.write_text("".join("file '" + str(x.resolve()) + "'\n" for x in voiced))
    film_path = OUT / "S01_the_last_little_fox_E01_full_unapproved.mp4"
    film.safe_ffmpeg("-f", "concat", "-safe", "0", "-i", listing,
                     "-c", "copy", "-movflags", "+faststart", film_path)
    metrics = check_media(film_path, mode="full")
    state["technical_full_mp4"] = True
    state["assembled_video_sha256"] = sha256(film_path)
    state["full_duration_seconds"] = metrics["duration_seconds"]
    state["status"] = "TECHNICAL_MP4_ONLY_AWAITING_TRUE_LIPSYNC_AND_VISUAL_QA"
    # Critically, audio-on-video does not certify animal mouth/viseme sync.
    state["human_cinematic_approved"] = False
    state["true_lipsync_verified"] = False
    state["published_anywhere"] = False
    _save(state)
    return {
        "status": state["status"],
        "duration_seconds": metrics["duration_seconds"],
        "video_file": film_path.name,
        "all_36_actual_shots_required": True,
        "public_publishing": False,
        "true_lipsync_verified": False,
    }


def assembly_gate():
    """Read-only determination; never turn planned shots into actual media."""
    _, plan = film.scene_plan()
    state = load_state(plan)
    all_shots_present = next_unfinished(state, plan) is None
    ready = all_shots_present and not state.get("technical_full_mp4", False)
    result = {
        "episode": film.EPISODE,
        "all_36_genuine_shots_verified": all_shots_present,
        "ready": ready,
        "already_assembled": bool(state.get("technical_full_mp4")),
        "shots_completed": len(state["completed"]),
        "movie_will_not_be_published": True,
    }
    output = os.getenv("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write("ready=" + ("true" if ready else "false") + "\n")
            handle.write("assembled=" + (
                "true" if state.get("technical_full_mp4") else "false") + "\n")
    return result


def write_job_summary(result, mode):
    """Report only the real E01 operation, never test fixtures or old queues."""
    target = os.getenv("GITHUB_STEP_SUMMARY")
    if not target or mode == "status":
        return
    if mode == "one-shot":
        completed = int(result["shots_completed"])
        total = int(result["shots_total"])
        seconds = float(result["real_motion_seconds"])
        next_part = result["next"]
        lines = [
            "## Nightfall E01 — actual registered-free video progress",
            "",
            "- **Episode:** S01_the_last_little_fox_E01",
            f"- **Generated moving shots:** {completed}/{total}",
            f"- **Real generated motion:** {seconds:.2f}/150 requested seconds",
            f"- **State:** {result['state']}",
            ("- **Next shot:** Scene {scene}, part {part} ({seconds}s)".format(
                **next_part) if next_part else "- **Next shot:** None; all 36 saved"),
            "- **Public upload:** Not attempted",
            "- **Fully approved episode:** No",
            "",
        ]
    elif mode == "assemble":
        lines = [
            "## Nightfall E01 — technical assembly (not release approval)",
            "",
            "- **Episode:** S01_the_last_little_fox_E01",
            f"- **Technical MP4 duration:** {float(result['duration_seconds']):.2f}s",
            "- **Lip sync & cinematic quality approval:** Not verified",
            "- **Public upload:** Not attempted",
            "",
        ]
    else:
        return
    with open(target, "a", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("status", "one-shot", "assemble", "assembly-gate"), required=True)
    args = p.parse_args()
    if args.mode == "status":
        result = status()
    elif args.mode == "assemble":
        result = assemble_unapproved()
    elif args.mode == "assembly-gate":
        result = assembly_gate()
    else:
        result = resume_one_shot()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    write_job_summary(result, args.mode)


if __name__ == "__main__":
    main()
