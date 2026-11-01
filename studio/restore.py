"""Validate preserved original stories directly from tracked repository files."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERIES = (("S01_the_last_little_fox", 12), ("S02_the_boy_who_forgot_tomorrow", 10))

def read_json(path):
    if not path.is_file():
        raise ValueError(f"Missing tracked file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON: {path}: {exc}") from exc

def validate_stories(root=ROOT):
    count = 0
    for series, expected in SERIES:
        season = root / "seasons" / series
        if not (season / "series_bible.md").is_file():
            raise ValueError(f"Missing series bible: {series}")
        registry = read_json(season / "characters" / "character_registry.json")
        tracker = read_json(season / "episodes" / "episodes.json")
        character_ids = [c["id"] for c in registry.get("characters", [])]
        if registry.get("series_id") != series or not character_ids or len(character_ids) != len(set(character_ids)):
            raise ValueError(f"Invalid cast registry: {series}")
        episodes = tracker.get("episodes", [])
        if tracker.get("series_id") != series or tracker.get("episode_count") != expected or len(episodes) != expected:
            raise ValueError(f"Wrong episode count: {series}")
        for n in range(1, expected+1):
            identifier = f"{series}_E{n:02d}"
            episode = episodes[n-1]
            if episode.get("id") != identifier or episode.get("episode") != n:
                raise ValueError(f"Tracker mismatch: {identifier}")
            script = read_json(season / "scripts" / f"E{n:02d}.json")
            scenes = script.get("scenes", [])
            if script.get("episode_id") != identifier or len(scenes) < 3:
                raise ValueError(f"Invalid episode: {identifier}")
            for scene in scenes:
                if (scene.get("character_id") not in character_ids or
                        not isinstance(scene.get("text"), str) or not scene["text"].strip()):
                    raise ValueError(f"Unknown speaker or empty dialogue: {identifier}")
            count += 1
    return count

def main():
    try:
        print(f"STORIES_READY: {validate_stories()} tracked episodes validated without Git history")
    except ValueError as exc:
        raise SystemExit(f"STORIES_INVALID: {exc}") from exc

if __name__ == "__main__":
    main()
