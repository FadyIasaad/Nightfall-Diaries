"""One-click story selection with automatic episode lookup and saved progress.

Never infer a different story from a partial name. Currently only the locked
Fox E01 has the approved-candidate real-motion/resumable pipeline. Other
episodes/stories are reported as BLOCKED, never faked or publicly posted.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

from studio.restore import ROOT, validate_stories

CONFIG_PATH = ROOT / "studio/active_story.json"
REPO = "FadyIasaad/Nightfall-Diaries"
ELIGIBLE_EPISODE = "S01_the_last_little_fox_E01"
CATALOG = (
    ("S01_the_last_little_fox", "The Last Little Fox",
     ("the last little fox", "last little fox", "الثعلب الصغير الأخير", "الثعلب الاخير", "s01_the_last_little_fox")),
    ("S02_the_boy_who_forgot_tomorrow", "The Boy Who Forgot Tomorrow",
     ("the boy who forgot tomorrow", "boy who forgot tomorrow", "الولد الذي نسي الغد", "الفتى الذي نسي الغد", "s02_the_boy_who_forgot_tomorrow")),
)


def normalize(text):
    if not isinstance(text, str):
        return ""
    return " ".join(text.strip().casefold().replace("_", " ").replace("-", " ").split())


def resolve_title(title):
    needle = normalize(title)
    for key, display, aliases in CATALOG:
        if needle in {normalize(display), *(normalize(x) for x in aliases)}:
            return key, display
    raise ValueError(
        "Unknown Nightfall story. Choose exactly 'The Last Little Fox' "
        "or 'The Boy Who Forgot Tomorrow'. No paid/generated alternative."
    )


def default():
    return {"schema_version": 1, "series_id": CATALOG[0][0], "title": CATALOG[0][1]}


def read_selection():
    if not CONFIG_PATH.is_file():
        return default()
    value = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise ValueError("Unknown story selection schema")
    sid, display = resolve_title(value.get("series_id"))
    if value.get("title") != display or sid != value.get("series_id"):
        raise ValueError("Selected story metadata has drifted")
    return value


def select_story(text):
    sid, title = resolve_title(text)
    # Original source manifests are immutable; check against their authoritative title.
    manifest = json.loads((ROOT / "seasons" / sid / "series_manifest.json")
                          .read_text(encoding="utf-8"))
    if manifest.get("series_id") != sid or manifest.get("title") != title:
        raise RuntimeError("Story title does not match immutable series manifest")
    validate_stories()
    return {"schema_version": 1, "series_id": sid, "title": title}


def choose_episode(selection):
    sid = selection["series_id"]
    episodes = json.loads((ROOT / "seasons" / sid / "episodes/episodes.json")
                          .read_text(encoding="utf-8"))
    if episodes.get("series_id") != sid:
        raise ValueError("Original episode index is inconsistent")
    for item in episodes["episodes"]:
        # Do not equate a generated preview or YouTube private copy with a
        # fully approved/publicly distributed episode.
        archived = ROOT / "published" / (item["id"] + ".json")
        if archived.is_file():
            receipt = json.loads(archived.read_text(encoding="utf-8"))
            ok = receipt.get("all_destinations_public") is True
        else:
            ok = False
        if not ok:
            return item["id"]
    return None


def current_state(selection):
    episode = choose_episode(selection)
    ready = episode == ELIGIBLE_EPISODE
    return {
        "series_id": selection["series_id"],
        "story_title": selection["title"],
        "episode_id": episode,
        "e01_free_motion_supported": ready,
        "status": (
            "RESUME_FROM_LAST_SHA_VERIFIED_E01_SHOT" if ready else
            "SEASON_COMPLETED" if episode is None else
            "BLOCKED_UNPREPARED_EPISODE_NO_GPU_NO_UPLOAD"
        ),
        "publishing_is_public": False,
        "may_charge_paid_gpu": False,
    }


def persist_selection(selection, *, token):
    """Only manual owner flow updates the one small non-secret config file."""
    if not token:
        raise RuntimeError("Missing authorized GitHub workflow token; selection not saved")
    path = "studio/active_story.json"
    url = "https://api.github.com/repos/" + REPO + "/contents/" + path
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "nightfall-story-one-click",
    }
    sha = None
    try:
        request = urllib.request.Request(url + "?ref=main", headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            obj = json.load(response)
        sha = obj["sha"]
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise RuntimeError("Story save lookup failed with HTTP " + str(exc.code)) from None
    data = {
        "message": "Set active Nightfall story: " + selection["title"] + " [story-selection-only]",
        "branch": "main",
        "content": base64.b64encode(
            (json.dumps(selection, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        ).decode("ascii"),
    }
    if sha:
        data["sha"] = sha
    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            if response.status not in (200, 201):
                raise RuntimeError("Story selection not saved")
    except urllib.error.HTTPError as exc:
        raise RuntimeError("Story save failed with HTTP " + str(exc.code)) from None
    # Synchronize in this checkout, too, so the same manually started run
    # uses the freshly chosen story rather than the previous daily selection.
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(selection, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")


def write_output(result):
    path = os.getenv("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        for field, value in (
            ("eligible", str(result["e01_free_motion_supported"]).lower()),
            ("series", result["series_id"]),
            ("episode", result["episode_id"] or ""),
            ("status", result["status"]),
        ):
            f.write(field + "=" + value + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("select", "current"), required=True)
    p.add_argument("--story", default="")
    opts = p.parse_args()
    if opts.mode == "select":
        # The GH Actions dispatcher has write access; scheduled runs don't.
        if os.getenv("GITHUB_EVENT_NAME") != "workflow_dispatch":
            raise RuntimeError("Only manual one-click action may change active story")
        selection = select_story(opts.story)
        persist_selection(selection, token=os.getenv("GH_TOKEN", ""))
    else:
        selection = read_selection()
    result = current_state(selection)
    write_output(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
