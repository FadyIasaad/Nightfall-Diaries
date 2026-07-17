"""
Promo Kit: after each upload, writes ready-to-paste promotion material into a
"Promo" tab of the Google Sheet:
  - a Reddit-ready text version of the story (CTA sign-off stripped)
  - a short Facebook-groups blurb with the YouTube link
  - three alternative hook lines to use as post titles
Run via workflow button "10 - Promo Kit" or automatically after uploads.
"""
import re

from nd_common import (
    get_sheets_client,
    open_spreadsheet,
    get_worksheet,
    get_or_create_worksheet,
    get_all_values,
    find_column,
    find_optional_column,
    get_cell,
    append_row,
    utc_now,
)


def normalize_type(value):
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def strip_cta(text):
    """Remove the like/subscribe sign-off sentence from the story text."""
    sentences = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    keep = [s for s in sentences if not re.search(r"subscribe|like[, ]|channel", s, re.IGNORECASE)]
    return " ".join(keep).strip()


def main():
    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    sheet = get_worksheet(spreadsheet, "Content")
    values = get_all_values(sheet)
    if not values:
        print("Empty sheet.")
        return
    headers = values[0]
    id_col = find_column(headers, "id")
    title_col = find_column(headers, "title")
    script_col = find_column(headers, "script")
    status_col = find_column(headers, "status")
    url_col = find_column(headers, "video_url")
    type_col = find_optional_column(headers, "video_type")

    promo_sheet = get_or_create_worksheet(spreadsheet, "Promo", rows=500, cols=6)
    existing = get_all_values(promo_sheet)
    if not existing:
        append_row(promo_sheet, ["date", "video_id", "title", "reddit_text", "fb_group_blurb", "youtube_url"])
        existing = [["date", "video_id", "title", "reddit_text", "fb_group_blurb", "youtube_url"]]
    done_ids = {row[1] for row in existing[1:] if len(row) > 1}

    made = 0
    for row in values[1:]:
        status = (get_cell(row, status_col) or "").strip().upper()
        vtype = normalize_type(get_cell(row, type_col)) if type_col else ""
        rid = (get_cell(row, id_col) or "").strip()
        url = (get_cell(row, url_col) or "").strip()
        if status != "UPLOADED" or not rid or rid in done_ids or not url:
            continue
        if vtype == "short" or rid.endswith("_funnel"):
            continue  # promo kits are for long stories
        title = (get_cell(row, title_col) or "").strip()
        script = strip_cta(get_cell(row, script_col) or "")
        if len(script) < 400:
            continue
        reddit_text = (
            f"{title}\n\n{script}\n\n"
            "---\n(This is an original story I wrote. I also narrate these with sound design "
            "on my YouTube channel — link on my profile if you want the audio version.)"
        )
        first_two = " ".join(re.split(r"(?<=[.!?])\s+", script)[:2])
        blurb = (
            f"{first_two}\n\n"
            f"...the full story gave me chills. Watch it narrated here:\n{url}"
        )
        append_row(promo_sheet, [utc_now(), rid, title, reddit_text[:45000], blurb[:2000], url])
        done_ids.add(rid)
        made += 1
        print(f"Promo kit written for {rid}: {title[:50]}")
    print(f"Done. {made} promo kits added to the Promo tab.")


if __name__ == "__main__":
    main()
