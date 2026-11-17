"""Explicit one-time public release of V4 E01 REMASTER to verified Meta accounts.

Uses the previously tested, receipt-locked E01 uploader with distinct pinned
media SHA, receipt namespace, and remaster title. Never claims 3D CGI or
phoneme-accurate lipsync; never silently overwrites the older E01 posts.
YouTube and TikTok remain blocked without verified credentials and scopes.
"""
import os
import hashlib
import shutil
from pathlib import Path

from pilot import e01_painterly_upload_once as uploader

SOURCE_SHA256 = "8aa394e7c3a30b819b2f03721ca08d6ed3327a0ef84bd8fa237e3a9b8a6b21a5"
RECEIPT = "published/S01_the_last_little_fox_E01_V4_remastered.json"
TAG = "nightfall-e01-v4-painterly-remaster-20261117"
REPO = "FadyIasaad/Nightfall-Diaries"
FILM = Path("output/v4_remaster_release/Nightfall_S01_E01_V4_Remastered_180s_PUBLIC.mp4")
SOURCE = Path("output/v4_remaster_release/original_original_approved_E01.mp4")


def configure():
    # These are the only changes to the legacy uploader: unique exact source
    # media and idempotency receipt, not different credentials or endpoints.
    uploader.SRC_SHA = SOURCE_SHA256
    uploader.RECEIPT_PATH = RECEIPT
    uploader.FILM = FILM
    uploader.TAG = TAG
    uploader.RELEASE_URL = (
        "https://github.com/" + REPO + "/releases/download/" + TAG + "/" + FILM.name
    )
    uploader.GH_API = (
        "https://api.github.com/repos/" + REPO + "/contents/" + RECEIPT
    )
    uploader.TITLE = "The Last Little Fox | Episode 01 — V4 Remastered"
    uploader.DESCRIPTION = (
        "The Last Little Fox Episode 1 — V4 Remastered. "
        "A revised 180-second illustrated 2.5D Nightfall Diaries drama, "
        "with original Ember and Moss, story-matched backgrounds and Kokoro voices. "
        "This is a NEW REMASTERED EDIT of Episode 1, not Episode 2; "
        "it uses articulated 2.5D cutouts, not full 3D animation or perfect lip-sync. "
        "#NightfallDiaries #TheLastLittleFox #AnimatedStory"
    )


def execute():
    if os.environ.get("OWNER_AUTHORIZED_E01_V4_REMASTER_PUBLIC") != "YES":
        raise RuntimeError("OWNER_REMASTER_RELEASE_AUTHORIZATION_MISSING")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("NOT_MAIN_BRANCH_REFUSE_PUBLIC_RELEASE")
    if os.environ.get("GITHUB_RUN_ATTEMPT", "1") != "1":
        raise RuntimeError("PUBLIC_POST_NO_RETRY_AFTER_AMBIGUOUS_OUTCOME")
    configure()
    if not SOURCE.is_file():
        raise RuntimeError("HASHED_ORIGINAL_V4_NOT_PRESENT")
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise RuntimeError("HASHED_ORIGINAL_V4_MISMATCH_NO_UPLOAD")
    # Legacy uploader's immutable-source verifier reads this isolated
    # compatibility path. Copy only after the V4 source hash passes.
    legacy_source = Path("output/painterly_release/original_original_approved_E01.mp4")
    legacy_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, legacy_source)
    return uploader.execute()


if __name__ == "__main__":
    execute()
