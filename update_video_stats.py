"""
Weekly analytics feedback loop.

1. Pulls public view/like counts for every uploaded video (YouTube Data API
   with a plain API key - the upload OAuth token can't read stats).
2. Writes them into the Content sheet (adds view_count / like_count /
   stats_updated_at columns on first run).
3. Ranks topics by views per video type and asks Gemini for fresh IDEA rows
   "in the same vein" as the winners, so the channel doubles down on what
   actually performs. Skips seeding when plenty of unused ideas remain.

Required env: GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_JSON, GEMINI_API_KEY,
YOUTUBE_API_KEY (create one free at console.cloud.google.com -> APIs &
Services -> Credentials -> Create credentials -> API key, in the same project
where the YouTube Data API is already enabled).
"""
import os
import re

import requests

from generate_story import (
    build_sheet_row,
    clamp_int,
    generate_json_with_models,
    normalize_type,
)
from nd_common import (
    append_row,
    find_column,
    find_optional_column,
    get_all_values,
    get_cell,
    get_logs_worksheet,
    get_sheets_client,
    get_worksheet,
    log,
    open_spreadsheet,
    require_env,
    update_cell,
    utc_now,
)

CONTENT_SHEET_NAME = "Content"
IDEAS_PER_TYPE = 3          # how many new ideas to seed per video type
MIN_UNUSED_IDEAS = 5        # skip seeding a type that still has this many IDEA rows
TOP_N = 4                   # how many top videos per type to show the model


def ensure_column(sheet, headers, name):
    """Return the 1-based column index for `name`, creating the column if missing."""
    if name in headers:
        return headers.index(name) + 1
    headers.append(name)
    update_cell(sheet, 1, len(headers), name)
    print(f"Added missing column: {name}")
    return len(headers)


def fetch_stats(video_ids, api_key):
    """Return {video_id: (views, likes)} for public videos, batched by 50."""
    stats = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "statistics", "id": ",".join(batch), "key": api_key},
            timeout=30,
        )
        r.raise_for_status()
        for item in r.json().get("items", []):
            s = item.get("statistics", {})
            stats[item["id"]] = (int(s.get("viewCount", 0) or 0), int(s.get("likeCount", 0) or 0))
    return stats


def parse_age_days(created_at):
    """Days since the row was created (min 1) so old videos don't win by age."""
    try:
        from datetime import datetime, timezone
        dt = datetime.strptime(str(created_at).strip(), "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
        return max(1.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
    except Exception:
        return 30.0  # unknown age: assume a month so it doesn't dominate


def title_traits(title):
    """Simple title-formula features to learn which packaging style wins."""
    t = (title or "").strip()
    traits = []
    if re.search(r"\b(I|My|Me|We|Our)\b", t):
        traits.append("first-person")
    if re.search(r"\d", t):
        traits.append("contains-number")
    if "?" in t:
        traits.append("question")
    if "'" in t or '"' in t:
        traits.append("quoted-detail")
    if 0 < len(t) <= 55:
        traits.append("short-title")
    return traits


def main():
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "YOUTUBE_API_KEY secret is missing. Create a free API key at "
            "console.cloud.google.com (APIs & Services -> Credentials -> Create "
            "credentials -> API key) in the project where the YouTube Data API is "
            "enabled, then add it as a GitHub Actions secret named YOUTUBE_API_KEY."
        )

    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    sheet = get_worksheet(spreadsheet, CONTENT_SHEET_NAME)
    logs_sheet = get_logs_worksheet(spreadsheet)
    values = get_all_values(sheet)
    if not values:
        raise ValueError("Content sheet is empty.")
    headers = list(values[0])

    id_col = find_column(headers, "id")
    topic_col = find_column(headers, "topic")
    characters_col = find_column(headers, "characters")
    theme_col = find_column(headers, "theme")
    status_col = find_column(headers, "status")
    title_col = find_column(headers, "title")
    youtube_video_id_col = find_column(headers, "youtube_video_id")
    video_type_col = find_optional_column(headers, "video_type")
    target_minutes_col = find_optional_column(headers, "target_minutes")
    narrator_pov_col = find_optional_column(headers, "narrator_pov")
    setting_col = find_optional_column(headers, "setting")
    audience_col = find_optional_column(headers, "audience")
    made_for_kids_col = find_optional_column(headers, "made_for_kids")
    created_at_col = find_optional_column(headers, "created_at")

    view_col = ensure_column(sheet, headers, "view_count")
    like_col = ensure_column(sheet, headers, "like_count")
    stats_at_col = ensure_column(sheet, headers, "stats_updated_at")

    # ── 1) Update stats ────────────────────────────────────────────────
    uploaded = []  # (row_number, yt_id, topic, theme, title, video_type)
    for index, row in enumerate(values[1:], start=2):
        yt_id = get_cell(row, youtube_video_id_col)
        if yt_id:
            uploaded.append((index, yt_id, get_cell(row, topic_col), get_cell(row, theme_col),
                             get_cell(row, title_col), normalize_type(get_cell(row, video_type_col))))
    if not uploaded:
        print("No uploaded videos with youtube_video_id yet; nothing to rank.")
        return

    stats = fetch_stats([u[1] for u in uploaded], api_key)
    now = utc_now()
    ranked = []  # dicts: vpd, views, likes, engagement, topic, theme, title, vtype
    for row_number, yt_id, topic, theme, title, vtype in uploaded:
        views, likes = stats.get(yt_id, (0, 0))
        update_cell(sheet, row_number, view_col, str(views))
        update_cell(sheet, row_number, like_col, str(likes))
        update_cell(sheet, row_number, stats_at_col, now)
        age = parse_age_days(get_cell(values[row_number - 1], created_at_col) if created_at_col else "")
        ranked.append({
            "vpd": views / age,
            "views": views,
            "likes": likes,
            "engagement": (likes / views) if views else 0.0,
            "topic": topic, "theme": theme, "title": title, "vtype": vtype,
        })
    print(f"Updated stats for {len(ranked)} videos.")
    log(logs_sheet, "", "UPDATE_STATS", f"Updated view/like counts for {len(ranked)} videos.")

    # ── Title-formula analysis: which packaging traits earn the most views/day ──
    trait_scores = {}
    for r in ranked:
        for trait in title_traits(r["title"]):
            trait_scores.setdefault(trait, []).append(r["vpd"])
    trait_summary = sorted(
        ((sum(v) / len(v), trait, len(v)) for trait, v in trait_scores.items() if len(v) >= 2),
        reverse=True,
    )
    traits_text = "\n".join(f"- {trait}: avg {avg:.1f} views/day across {n} videos" for avg, trait, n in trait_summary[:5]) or "- not enough data yet"

    # ── Weekly report (written to a Reports tab so it's easy to read) ──
    from nd_common import get_or_create_worksheet
    top_overall = sorted(ranked, key=lambda r: r["vpd"], reverse=True)[:5]
    report_lines = [f"Videos tracked: {len(ranked)}"]
    report_lines.append("TOP 5 BY VIEWS/DAY:")
    for r in top_overall:
        report_lines.append(f"  {r['vpd']:.1f} vpd | {r['views']} views | {r['engagement']*100:.1f}% likes | [{r['vtype']}] {r['title'][:70]}")
    report_lines.append("WINNING TITLE TRAITS:")
    report_lines.append(traits_text.replace("\n", " ; "))
    report_text = "\n".join(report_lines)
    try:
        reports_sheet = get_or_create_worksheet(spreadsheet, "Reports", rows=500, cols=2)
        append_row(reports_sheet, [now, report_text])
    except Exception as exc:
        print(f"Reports tab write skipped: {exc}")
    print(report_text)
    log(logs_sheet, "", "WEEKLY_REPORT", report_text[:1500])

    # ── 2) Seed new ideas from the winners ─────────────────────────────
    existing_topics = {get_cell(row, topic_col).strip().lower() for row in values[1:]}
    unused_by_type = {}
    for row in values[1:]:
        if get_cell(row, status_col).upper() == "IDEA":
            t = normalize_type(get_cell(row, video_type_col))
            unused_by_type[t] = unused_by_type.get(t, 0) + 1

    for vtype in ("short", "horror_story", "confession_story"):
        if unused_by_type.get(vtype, 0) >= MIN_UNUSED_IDEAS:
            print(f"{vtype}: {unused_by_type[vtype]} unused ideas remain; skipping seeding.")
            continue
        winners = sorted([r for r in ranked if r["vtype"] == vtype], key=lambda r: r["vpd"], reverse=True)[:TOP_N]
        if not winners:
            print(f"{vtype}: no uploaded videos yet; skipping.")
            continue
        winners_text = "\n".join(
            f"- {r['vpd']:.1f} views/day ({r['views']} total, {r['engagement']*100:.1f}% like rate) | topic: {r['topic']} | theme: {r['theme']} | title: {r['title']}"
            for r in winners
        )
        prompt = f"""
You plan content for the YouTube channel Nightfall Diaries (real-feeling late-night stories for adults:
quiet psychological horror, confession/betrayal stories, and unsettling shorts).

These are the channel's BEST performing {vtype.replace('_', ' ')} videos so far (ranked by views per day,
so age doesn't distort the picture):
{winners_text}

Title packaging traits that currently earn the most views/day on this channel:
{traits_text}

Create {IDEAS_PER_TYPE} NEW story ideas in the same vein as these winners: same kind of premise energy,
same emotional territory, but each a clearly different story. Never reuse or lightly reword an existing
topic. Keep every idea general-audience and monetization-safe (no gore, no real people).

Return valid JSON only, exactly in this shape:
{{
  "ideas": [
    {{
      "topic": "one-sentence premise, concrete and specific",
      "characters": "who is involved, comma separated",
      "theme": "the deeper throughline in one short phrase",
      "narrator_pov": "an anonymous adult narrator, calm and a little tired, telling it after the fact",
      "setting": "one specific everyday setting"
    }}
  ]
}}
"""
        data = generate_json_with_models(prompt, max_output_tokens=8192, label=f"Seeding {vtype} ideas")
        ideas = data.get("ideas") if isinstance(data.get("ideas"), list) else []
        added = 0
        stamp = re.sub(r"\D", "", utc_now())
        for n, idea in enumerate(ideas[:IDEAS_PER_TYPE], start=1):
            topic = str(idea.get("topic", "") or "").strip()
            if not topic or topic.lower() in existing_topics:
                continue
            existing_topics.add(topic.lower())
            minutes = "1" if vtype == "short" else "18"
            new_row = build_sheet_row(headers, [
                (id_col, f"SEED-{stamp}-{vtype[:4].upper()}{n}"),
                (topic_col, topic),
                (characters_col, str(idea.get("characters", "") or "").strip()),
                (theme_col, str(idea.get("theme", "") or "").strip()),
                (status_col, "IDEA"),
                (video_type_col, vtype),
                (target_minutes_col, minutes),
                (narrator_pov_col, str(idea.get("narrator_pov", "") or "").strip()),
                (setting_col, str(idea.get("setting", "") or "").strip()),
                (audience_col, "general audience"),
                (made_for_kids_col, "FALSE"),
                (created_at_col, utc_now()),
            ])
            append_row(sheet, new_row)
            added += 1
        print(f"{vtype}: seeded {added} new ideas from top performers.")
        log(logs_sheet, "", "SEED_IDEAS", f"Seeded {added} {vtype} ideas from top performers.")


if __name__ == "__main__":
    main()
