"""Agnes Flash price and LTX fallback discovery -- read only, fail closed.

No generation, billing mutations, subscription changes, or publishing requests.
Public promotional pricing cannot prove account-specific zero-charge eligibility.
"""
import argparse
import html
import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

PRICING_URL = "https://wiki.agnes-ai.com/en/docs/pricing.md"
LTX_METADATA_URL = "https://huggingface.co/api/spaces/Lightricks/LTX-2.5"
MODEL = "agnes-video-2.5-flash"
EMBER_REFERENCE = (
    "seasons/S01_the_last_little_fox/characters/"
    "s01_ember/cloud_reference.png"
)
MAX_BYTES = 300_000

EMBER_PROMPT = (
    "Use the character and rendering style in <Picture 1> as the exact visual "
    "reference. Ember is a small russet-orange fox cub with large amber eyes, "
    "cream chest, white tip on LEFT ear only, and a teal scarf embroidered "
    "with exactly ONE gold star. In a richly textured magical forest at dusk, "
    "Ember takes three grounded steps forward, stops, turns his head toward "
    "a distant burst of orange firelight, and reacts with visible fear in "
    "his eyes and ears. His legs, fluffy tail, scarf and expression move "
    "naturally. Slow cinematic dolly-in, believable depth, soft volumetric "
    "moonlight, detailed groomed fur. No dialogue, no lip movement, no "
    "character morphing, no extra stars, no clothing changes, no slideshows."
)


def fetch_public_get(url, opener=urlopen):
    """Only the two fixed public URLs are allowed, and no credentials are sent."""
    if url not in (PRICING_URL, LTX_METADATA_URL):
        raise ValueError("Non-allowlisted public URL")
    request = Request(url, headers={"Accept": "text/plain, application/json"},
                      method="GET")
    with opener(request, timeout=20) as response:
        if getattr(response, "status", 200) != 200:
            raise ValueError("Public source did not return HTTP 200")
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Public source too large")
    return raw.decode("utf-8")


def flash_public_trial_is_zero(document):
    """Accept only the exact model's price row in Agnes's official video table."""
    video_section = document.split("## Video models", 1)
    if len(video_section) != 2:
        return False
    video_section = video_section[1].split("## Billing notes", 1)[0]
    for row in re.findall(r"<tr\b[^>]*>.*?</tr>", video_section, re.I | re.S):
        fields = re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.I | re.S)
        fields = [
            " ".join(html.unescape(re.sub(r"<[^>]*>", "", f))
                     .replace("`", "").replace("*", "").split())
            for f in fields
        ]
        if len(fields) == 4 and fields[0] == MODEL:
            return (
                fields[1] == "720P video duration"
                and fields[2] == "$0.025 / second"
                and fields[3] == "$0 / second"
            )
    return False


def inspect(opener=urlopen):
    result = {
        "version": 1,
        "status": "BLOCKED_ACCOUNT_BILLING_UNVERIFIED",
        "provider": "Agnes AI",
        "exact_model": MODEL,
        "documentation": PRICING_URL,
        "public_promotional_zero_price_confirmed": False,
        "offer_is_permanent": False,
        "account_default_key_type_verified": False,
        "no_card_and_no_auto_billing_verified": False,
        "enforced_hard_zero_spend_cap_verified": False,
        "quota_for_complete_episode_verified": False,
        "generation_authorized": False,
        "generation_request_sent": False,
        "publish_request_sent": False,
        "fallback": {
            "name": "LTX-2.5 official Hugging Face ZeroGPU Space",
            "space": "Lightricks/LTX-2.5",
            "metadata_available": False,
            "gpu_generation_attempted": False,
            "quality_verified": False,
        },
        "prepared_not_submitted_proof": {
            "original_reference_in_repo": EMBER_REFERENCE,
            "mode": "reference",
            "model": MODEL,
            "duration_seconds": "5",
            "resolution": "720P",
            "aspect_ratio": "9:16",
            "voice": "none; later Kokoro lip-sync test required",
            "prompt": EMBER_PROMPT,
        },
    }
    try:
        doc = fetch_public_get(PRICING_URL, opener=opener)
        result["public_promotional_zero_price_confirmed"] = (
            flash_public_trial_is_zero(doc)
        )
        result["pricing_note"] = (
            "Official published Flash trial price is $0/second, but temporary. "
            "Agent Plan uses list price, and an account-specific hard $0 billing "
            "cutoff has NOT been verified."
            if result["public_promotional_zero_price_confirmed"]
            else "Exact $0 Flash promotional row unavailable or changed."
        )
    except (ValueError, UnicodeError, OSError, TimeoutError) as exc:
        result["pricing_note"] = "Public GET unavailable: " + type(exc).__name__
    try:
        data = json.loads(fetch_public_get(LTX_METADATA_URL, opener=opener))
        if isinstance(data, dict) and data.get("id") == "Lightricks/LTX-2.5":
            result["fallback"]["metadata_available"] = True
            result["fallback"]["space_stage"] = (
                (data.get("runtime") or {}).get("stage") or "unknown"
            )
    except (ValueError, UnicodeError, OSError, TimeoutError) as exc:
        result["fallback"]["metadata_error"] = type(exc).__name__

    # This is deliberate: public price and model metadata NEVER authorize POST.
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output/agnes_cost_gate.json")
    args = parser.parse_args()
    report = inspect()
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print("AGNES_ZERO_COST_GATE:", report["status"])
    print("PUBLIC_PROMO_ZERO_PRICE:",
          report["public_promotional_zero_price_confirmed"])
    print("LTX_FALLBACK_METADATA:",
          report["fallback"]["metadata_available"])
    print("VIDEO_GENERATION_AND_PUBLISHING: BLOCKED; no POST requests sent")
    print("REPORT:", target)


if __name__ == "__main__":
    main()
