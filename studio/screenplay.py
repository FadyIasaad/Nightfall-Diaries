"""Choose production-grade expanded scripts without changing the original 22 story archives."""
import json
from .restore import ROOT

def load_screenplay(episode_id, root=ROOT):
    series, number = episode_id.rsplit("_E", 1)
    archive = root / "seasons" / series / "scripts" / ("E" + number + ".json")
    original = json.loads(archive.read_text(encoding="utf-8"))
    if original["episode_id"] != episode_id:
        raise ValueError("Archive episode ID mismatch")
    draft = root / "seasons" / series / "screenplays" / ("E" + number + ".json")
    if not draft.is_file():
        return original
    expanded = json.loads(draft.read_text(encoding="utf-8"))
    if expanded.get("episode_id") != episode_id:
        raise ValueError("Production screenplay ID mismatch")
    if expanded.get("original_script") != archive.relative_to(root).as_posix():
        raise ValueError("Production screenplay must cite preserved original episode")
    scenes = expanded.get("scenes", [])
    if not scenes or any(not isinstance(s.get("text"), str) or not s["text"].strip()
                         for s in scenes):
        raise ValueError("Expanded screenplay has empty scenes")
    positions = []
    for source in original["scenes"]:
        matches = [i for i, scene in enumerate(scenes)
                   if scene.get("character_id") == source["character_id"]
                   and source["text"] in scene["text"]]
        if len(matches) != 1:
            raise ValueError("Each original spoken scene must survive verbatim and exactly once")
        positions.append(matches[0])
    if positions != sorted(positions) or len(set(positions)) != len(positions):
        raise ValueError("Original scenes must retain their chronology")
    registry = json.loads((root / "seasons" / series / "characters/character_registry.json")
                          .read_text(encoding="utf-8"))
    allowed = {c["id"] for c in registry["characters"]}
    for scene in scenes:
        if scene.get("character_id") not in allowed:
            raise ValueError("Expanded scene invented an unapproved speaker")
        if not isinstance(scene.get("direction"), str) or not scene["direction"].strip():
            raise ValueError("Expanded scene missing physical blocking/camera direction")
        if any(c not in allowed for c in scene.get("visible", [])):
            raise ValueError("Expanded scene references unapproved visible character")
    words = sum(len(scene["text"].split()) for scene in scenes)
    if not 240 <= words <= 430:
        raise ValueError(f"Expanded screenplay has {words} words; target 240–430 for no more than three minutes")
    return expanded
