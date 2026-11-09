"""No-charge read-only Agnes API connection check for Nightfall Diaries.

Strictly NO POST, NO video jobs, NO credit/usage invocation, NO publishing,
NO payment API. The presence of a model is NOT evidence of $0 billing.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_MODELS_URL = "https://apihub.agnes-ai.com/v1/models"
ONLY_CANDIDATE = "agnes-video-2.5-flash"
MAX_RESPONSE_BYTES = 250_000


def probe(token, opener=urlopen):
    result = {
        "schema_version": 1,
        "provider": "Agnes AI",
        "endpoint": "/v1/models",
        "http_method": "GET",
        "model": ONLY_CANDIDATE,
        "status": "BLOCKED",
        "secret_configured": bool(token),
        "model_list_accessible": False,
        "target_model_listed": False,
        "current_zero_price_verified": False,
        "zero_card_auto_billing_disabled_verified": False,
        "free_recurrent_quota_verified": False,
        "image_reference_supported_verified": False,
        "rendered_video": False,
        "submitted_generation_task": False,
        "uploaded_to_any_platform": False,
        "video_generation_authorized": False,
        "next_gate": "Verify account-specific $0 eligibility and sustainable quota outside this probe",
    }
    if not token:
        result["reason"] = "AGNES_API_KEY repository secret missing or unavailable to this workflow"
        return result

    # This probe may query only the fixed official metadata endpoint, via GET.
    request = Request(
        API_MODELS_URL,
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        method="GET",
    )
    try:
        with opener(request, timeout=15) as response:
            code = getattr(response, "status", 200)
            if code != 200:
                result["reason"] = "Model listing HTTP " + str(code)
                return result
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                result["reason"] = "Model response exceeds safe size"
                return result
        data = json.loads(raw)
        entries = data.get("data", []) if isinstance(data, dict) else []
        if not isinstance(entries, list):
            result["reason"] = "Unrecognized model listing structure"
            return result
        ids = {
            entry.get("id") for entry in entries
            if isinstance(entry, dict) and isinstance(entry.get("id"), str)
        }
        result["model_list_accessible"] = True
        result["target_model_listed"] = ONLY_CANDIDATE in ids
        result["status"] = "CONNECTED_PRICING_UNVERIFIED" if result["target_model_listed"] else "BLOCKED"
        result["reason"] = (
            "Free trial model visible; current price and account quota NOT certified; no generation attempted"
            if result["target_model_listed"] else
            "Model listing accessible but target Flash model not listed; no generation attempted"
        )
    except HTTPError as exc:
        result["reason"] = "Model listing HTTP " + str(exc.code)
    except (URLError, TimeoutError):
        result["reason"] = "Model listing network error; no generation attempted"
    except (ValueError, TypeError, OSError):
        result["reason"] = "Model listing invalid or unreadable; no generation attempted"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output/agnes_engine_probe.json")
    args = parser.parse_args()
    report = probe(os.environ.get("AGNES_API_KEY", ""))
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("AGNES_ENGINE_PROBE:", report["status"])
    print("REPORT:", path)
    print("VIDEO_GENERATION_BLOCKED: No API generation requests were sent.")
    # Absence, forbidden credentials, or a missing model fail closed.
    if report["status"] == "BLOCKED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
