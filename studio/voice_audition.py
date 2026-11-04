"""Zero-cost cloud voice auditions for all locked characters; no publishing or false approval."""
import argparse
import json
import wave
from pathlib import Path
from .restore import ROOT, validate_stories
from .production import SERIES

def voice_definitions(series_id):
    allowed = {s for s, _ in SERIES}
    if series_id not in allowed:
        raise ValueError("Only original series can be auditioned")
    data = json.loads((ROOT / "seasons" / series_id /
                       "characters/character_registry.json").read_text(encoding="utf-8"))
    entries = []
    for actor in data["characters"]:
        v = actor.get("voice", {})
        if not v.get("voice_id") or not v.get("audition"):
            raise ValueError(f"Missing voice preset/audition phrase for {actor['id']}")
        entries.append({"id": actor["id"], "name": actor["name"],
                        "voice_id": v["voice_id"], "line": v["audition"],
                        "direction": v.get("voice_direction", ""),
                        "character": actor})
    if len({x["voice_id"] for x in entries}) != len(entries):
        raise ValueError("Voice IDs must be distinct within a series")
    return entries

def audition(series_id, out_dir=ROOT / "output" / "voice_auditions"):
    validate_stories()
    entries = voice_definitions(series_id)
    from .neural_audio import render_kokoro  # expensive import only for real job
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {"series_id": series_id, "status": "UNREVIEWED_VOICE_AUDITIONS",
              "sample_rate_hz": 24000, "samples": []}
    for item in entries:
        output = out_dir / (item["id"] + ".wav")
        render_kokoro(item["line"], item["character"], output)
        with wave.open(str(output), "rb") as wav:
            frames, rate, channels = wav.getnframes(), wav.getframerate(), wav.getnchannels()
            seconds = frames / rate
        if not 0.7 <= seconds <= 30 or rate != 24000 or channels != 1:
            raise RuntimeError(f"Bad neural voice sample: {item['id']}")
        report["samples"].append({
            "id": item["id"], "voice_id": item["voice_id"],
            "file": output.name, "seconds": round(seconds, 2),
            "direction": item["direction"], "line": item["line"],
            "status": "RECORDED_NOT_EMOTION_OR_IDENTITY_APPROVED"
        })
    dest = out_dir / "voice_audition_report.json"
    dest.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return dest

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--series", default="S01_the_last_little_fox",
                   choices=[s for s, _ in SERIES])
    a = p.parse_args()
    result = audition(a.series)
    print("VOICE_AUDITIONS_RENDERED:", result)
    print("VOICE_QA_PENDING: samples are not proof of human-like emotional acting or lip sync.")

if __name__ == "__main__":
    main()
