"""Fail-closed, render-free G1 asset and immutable-source readiness check.

This module MUST NOT download models, invoke Blender, render images/videos, call
publishing APIs, or access payment settings. It exists to prevent false success.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from studio.restore import ROOT, validate_stories

ALLOWED_LICENSES={"CC0-1.0","CC-BY-4.0"}
EXPECTED_IDS=("s01_ember","s01_moss")

def git_blob_sha1(raw: bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def _safe_relative(root: Path, raw: str, *, base: str):
    if not isinstance(raw,str) or not raw.startswith(base+"/") or raw.startswith("/"):
        return None
    path=(root/raw).resolve()
    anchor=(root/base).resolve()
    if anchor not in path.parents:
        return None
    return path

def assess(root:Path=ROOT)->dict:
    issues=[]
    result={"schema_version":1, "mode":"g1_proof", "status":"BLOCKED",
            "ready_to_render":False, "rendered_video":False,
            "publicly_published":False, "gpu_used":False,
            "approved_owner_look":False, "checked_assets":[], "issues":issues}
    try:
        manifest=json.loads((root/"docs/g1_protected_git_blobs.json").read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            p=(root/entry["path"]).resolve()
            if root.resolve() not in p.parents or not p.is_file():
                issues.append("Protected file missing/invalid: "+entry["path"])
            elif git_blob_sha1(p.read_bytes())!=entry["git_blob_sha1"]:
                issues.append("Protected file changed: "+entry["path"])
        if len(manifest["files"])<40:
            issues.append("Protected manifest unexpectedly short")
    except (OSError,KeyError,ValueError,TypeError) as exc:
        issues.append("Protected sources not verifiable: "+type(exc).__name__)
    try:
        if validate_stories(root)!=22:
            issues.append("Wrong original series episode count")
        settings=json.loads((root/"studio/production_settings.json").read_text(encoding="utf-8"))
        config=json.loads((root/"config.json").read_text(encoding="utf-8"))
        for key,value in settings.items():
            if key.endswith("_verified") or key in (
                "production_enabled","cinematic_video_approved",
                "publishing_implemented","automatic_new_series"):
                if value is not False:
                    issues.append("Unsafe production gate: "+key)
        if config.get("public_publish_enabled") is not False:
            issues.append("Unsafe public_publish_enabled")
    except (OSError,ValueError,KeyError,TypeError) as exc:
        issues.append("Original stories or safety flags failed: "+type(exc).__name__)
    try:
        contract=json.loads((root/"docs/g1_asset_contract.json").read_text(encoding="utf-8"))
        candidates=contract["candidates"]
        if contract.get("render_is_authorized") is not False:
            issues.append("Premature rendering authorization")
        if len(candidates)!=2 or {c.get("character_id") for c in candidates}!=set(EXPECTED_IDS):
            issues.append("Missing expected Ember/Moss candidates")
        for model in candidates:
            label=str(model.get("character_id","unknown"))
            problems=[]
            for field in ("source_url","author","spdx_license","license_url",
                          "licence_checked_utc","sha256","identity_sheet_file"):
                if not model.get(field):
                    problems.append(field+" missing")
            for field in ("commercial_use_verified","repo_redistribution_allowed",
                          "headless_source_verified","identity_features_reviewed",
                          "face_jaw_rig_reviewed","owner_approved"):
                if model.get(field) is not True:
                    problems.append(field+" unverified")
            if model.get("spdx_license") not in ALLOWED_LICENSES:
                problems.append("commercial redistribution license not approved")
            p=_safe_relative(root,model.get("asset_file"),base="assets")
            if p is None or not p.is_file() or p.suffix.lower() not in {".blend",".glb"}:
                problems.append("locally available rig missing or unsafe path")
            elif model.get("sha256")!=hashlib.sha256(p.read_bytes()).hexdigest():
                problems.append("rig SHA256 mismatch")
            sheet=_safe_relative(root,model.get("identity_sheet_file"),base="assets")
            if sheet is None or not sheet.is_file():
                problems.append("verified identity sheet missing")
            result["checked_assets"].append({"character_id":label,
                                               "asset_ready":not problems,
                                               "blockers":problems})
            if problems:
                issues.append(label+": "+", ".join(problems))
    except (OSError,KeyError,ValueError,TypeError) as exc:
        issues.append("Asset contract not verifiable: "+type(exc).__name__)
    # No rendering implementation or auto-approval exists in this module.
    if not issues:
        result["status"]="ASSETS_RESEARCH_READY_NOT_RENDERED"
        result["ready_to_render"]=False
        result["issues"].append("G1 rendering engine not yet implemented/approved. Separate visual gate required.")
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="output/g1_readiness.json")
    args=parser.parse_args()
    report=assess()
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("G1_"+report["status"]+": no render or publication was performed")
    print("G1_REPORT: "+str(out))
    for item in report["issues"][:8]:
        print("G1_BLOCKER: "+item)
    if report["issues"]:
        raise SystemExit(2)

if __name__=="__main__":
    main()
