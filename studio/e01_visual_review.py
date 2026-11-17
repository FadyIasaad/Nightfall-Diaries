"""Fail-closed technical visual audit and 14-scene storyboard for the E01 director cut.

This cannot certify cinematic quality or human art approval. It records evidence
for checking every set and the full cast against approved Ember art.
Offline CPU/Pillow only; does not render, upload, or modify source images.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
from studio.e01_v2_art_direction import SETS

W, H = 360, 640
EXPECTED = tuple(range(1, 15))


def audit(folder, output=None):
    folder = Path(folder)
    output = Path(output) if output else folder
    output.mkdir(parents=True, exist_ok=True)
    records = []
    thumbs = []
    signatures = set()
    failures = []
    font = ImageFont.load_default()
    for n in EXPECTED:
        source = folder / f"scene_{n:02d}_still.png"
        if not source.is_file():
            failures.append(f"SCENE_{n:02d}_STILL_MISSING")
            continue
        with Image.open(source) as raw:
            im = raw.convert("RGB")
        if im.size != (W, H):
            failures.append(f"SCENE_{n:02d}_WRONG_DIMENSIONS_{im.size}")
            continue
        stat = ImageStat.Stat(im)
        spread = max(stat.stddev)
        if spread < 20:
            failures.append(f"SCENE_{n:02d}_LOW_CONTRAST")
        # Use a small luminance thumbnail as a heuristic, not an art approval.
        tiny = im.convert("L").resize((24, 42), Image.Resampling.BILINEAR)
        fingerprint = hashlib.sha256(tiny.tobytes()).hexdigest()
        if fingerprint in signatures:
            failures.append(f"SCENE_{n:02d}_DUPLICATE_FRAME")
        signatures.add(fingerprint)
        records.append({"scene": n, "set": SETS[n][0],
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                        "contrast_stddev": round(spread, 2),
                        "technical_checks_passed": spread >= 20})
        card = Image.new("RGB", (260, 510), (19, 24, 34))
        view = im.resize((250, 444), Image.Resampling.LANCZOS)
        card.paste(view, (5, 5))
        d = ImageDraw.Draw(card)
        d.text((9, 454), f"SCENE {n:02d}", font=font, fill=(245, 240, 220))
        d.text((9, 474), SETS[n][0][:36], font=font, fill=(150, 205, 214))
        thumbs.append(card)
    board = Image.new("RGB", (260 * 7, 510 * 2), (12, 17, 27))
    for i, card in enumerate(thumbs):
        board.paste(card, ((i % 7) * 260, (i // 7) * 510))
    boardpath = output / "e01_all_14_scenes_storyboard.jpg"
    board.save(boardpath, quality=90, optimize=True)
    report = {
        "schema": "nightfall-e01-technical-visual-audit-v1",
        "expected_scenes": 14, "found_scenes": len(records),
        "scene_records": records, "failures": failures,
        "storyboard_file": boardpath.name,
        "ember_reference_quality_equivalence_verified": False,
        "moss_reference_quality_equivalence_verified": False,
        "backgrounds_human_approved": False,
        "public_publishing_authorized": False,
        "note": "Automated checks catch missing/blank/repeated frames only. Human side-by-side art review is mandatory; this is not cinematic quality certification."
    }
    (output / "visual_audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if len(records) != 14:
        failures.append("INCOMPLETE_STORYBOARD")
    if failures:
        raise RuntimeError("VISUAL_AUDIT_FAILED: " + ", ".join(failures))
    print("VISUAL_AUDIT_TECHNICAL_PASS_ART_APPROVAL_PENDING", boardpath)
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--folder", default="output/nightfall_e01_director_v3")
    a = p.parse_args()
    audit(a.folder)
