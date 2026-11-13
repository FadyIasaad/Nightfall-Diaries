"""Safely resolve the owner's Nightfall Diaries Facebook Page access token.

The stored FB_PAGE_ACCESS_TOKEN may actually be a *user* access token.
Resolve the specific Page using the official read-only /me/accounts endpoint.
Never log/persist raw tokens, choose an arbitrary first Page, or silently post
to another Page. This module performs NO uploads or changes to Facebook.
"""
import os

GRAPH = "https://graph.facebook.com/"
PAGE_NAME = "Nightfall Diaries"


class PageAuthError(RuntimeError):
    pass


def _get(session, url, token, fields, extra=None):
    params = {"fields": fields}
    if extra:
        params.update(extra)
    response = session.get(
        url, headers={"Authorization": "Bearer " + token},
        params=params, timeout=25)
    if not response.ok:
        # A Graph error response may contain sensitive details; never echo it.
        raise PageAuthError("Facebook read-only page query failed (HTTP " +
                            str(response.status_code) + ")")
    return response.json()


def resolve_nightfall_page(*, session=None, token=None, expected_id=None):
    """Return in-memory {id, access_token, source}; caller must never print it."""
    if session is None:
        import requests
        session = requests
    source_token = token or os.getenv("FB_PAGE_ACCESS_TOKEN", "")
    wanted_id = expected_id if expected_id is not None else os.getenv("FB_EXPECTED_PAGE_ID", "")
    if not source_token:
        raise PageAuthError("Missing Facebook authorization token")
    base = GRAPH + os.getenv("META_API_VERSION", "v25.0")
    profile = _get(session, base + "/me", source_token, "id,name")
    matches_name = str(profile.get("name") or "").strip().casefold() == PAGE_NAME.casefold()
    matches_id = bool(profile.get("id")) and (
        not wanted_id or str(profile["id"]) == str(wanted_id))
    if matches_name and matches_id:
        # Distinguish a Page token from a user named after the Page.
        category, is_page = None, False
        try:
            category = _get(session, base + "/me", source_token, "id,category")
            is_page = bool(category.get("category"))
        except PageAuthError:
            pass
        if is_page:
            return {"id": str(profile["id"]), "access_token": source_token,
                    "source": "verified_page_token"}
    listed = _get(
        session, base + "/me/accounts", source_token, "id,name,access_token",
        {"limit": 100})
    matches = [
        page for page in (listed.get("data") or [])
        if str(page.get("name") or "").strip().casefold() == PAGE_NAME.casefold()
        and (not wanted_id or str(page.get("id")) == str(wanted_id))
        and page.get("id") and page.get("access_token")
    ]
    # Never auto-select a Page if the name is ambiguous or if pagination
    # indicates we did not inspect all returned Pages.
    if listed.get("paging", {}).get("next"):
        raise PageAuthError("Page listing is paginated; cannot safely auto-select")
    if len(matches) != 1:
        raise PageAuthError("Expected Nightfall Diaries Page not uniquely authorized")
    chosen = matches[0]
    verified = _get(session, base + "/" + str(chosen["id"]),
                    chosen["access_token"], "id,name")
    if (str(verified.get("id")) != str(chosen["id"]) or
            str(verified.get("name") or "").strip().casefold() !=
            PAGE_NAME.casefold()):
        raise PageAuthError("Page token did not verify against Nightfall Diaries")
    return {"id": str(chosen["id"]), "access_token": chosen["access_token"],
            "source": "user_token_resolved_to_page_token"}
