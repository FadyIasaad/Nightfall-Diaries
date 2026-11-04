"""Persistent zero-cost episode queue shared through best-effort Actions cache.

This is a render queue, NOT authorization to publish anything. Cache may be
evicted or not restored; no full reliability guarantee is claimed.
"""
import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .restore import ROOT, SERIES

DEFAULT_PATH = ROOT / "output/checkpoints/episode_queue.json"
STATUS_PATH = ROOT / "output/render_status.json"

def now():
    return datetime.now(timezone.utc)

def valid_episode(episode):
    if not isinstance(episode, str):
        return False
    for series, count in SERIES:
        for num in range(1, count + 1):
            if episode == f"{series}_E{num:02d}":
                return True
    return False

def load(path=DEFAULT_PATH):
    path=Path(path)
    if not path.exists():
        return {"schema_version": 1, "episodes": []}
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("episodes"), list):
        raise ValueError("Render queue schema invalid; refuse guessing about pending uploads")
    for item in data["episodes"]:
        if (not valid_episode(item.get("episode_id"))
                or item.get("mode") not in ("full", "proof")
                or not isinstance(item.get("status"), str)):
            raise ValueError("Invalid queued episode; refuse running a different story")
    return data

def write(data, path=DEFAULT_PATH):
    path=Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp=path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    temp.replace(path)

def enqueue(episode, mode="full", path=DEFAULT_PATH):
    if not valid_episode(episode) or mode not in ("full", "proof"):
        raise ValueError("Only original episodes with explicit mode may be queued")
    data=load(path)
    for item in data["episodes"]:
        if item["episode_id"]==episode and item["mode"]==mode:
            if item["status"] != "RENDERED_NOT_VISUALLY_APPROVED":
                item["status"]="QUEUED"
                item["retry_after_utc"]=None
            write(data,path)
            return item
    item={"episode_id":episode,"mode":mode,"status":"QUEUED","retry_after_utc":None}
    data["episodes"].append(item)
    write(data,path)
    return item

def next_due(path=DEFAULT_PATH, at=None):
    when=at or now()
    for item in load(path)["episodes"]:
        if item["status"] not in ("QUEUED","PAUSED_FREE_QUOTA","PAUSED_PROVIDER"):
            continue
        date=item.get("retry_after_utc")
        if not date or datetime.fromisoformat(date.replace("Z","+00:00")) <= when:
            return item
    return None

def set_status(episode, mode, status, retry_seconds=None, details=None, path=DEFAULT_PATH):
    if status not in ("PAUSED_FREE_QUOTA","PAUSED_PROVIDER","RENDERED_NOT_VISUALLY_APPROVED"):
        raise ValueError("Unsafe status")
    data=load(path)
    match=next((x for x in data["episodes"] if x["episode_id"]==episode and x["mode"]==mode),None)
    if match is None:
        raise ValueError("Episode was never queued")
    match["status"]=status
    match["retry_after_utc"]=((now()+timedelta(seconds=max(0,int(retry_seconds)))).isoformat()
                              if retry_seconds is not None else None)
    match["last_note"]=(details or "")[:300]
    write(data,path)
    return match

def write_report(episode, mode, status, details, retry_after=None, path=STATUS_PATH):
    report={"episode_id":episode, "mode":mode, "status":status,
            "completed_full_episode":status=="RENDERED_NOT_VISUALLY_APPROVED",
            "publicly_published":False, "reason":str(details)[:500],
            "retry_after_utc":retry_after, "generated_at_utc":now().isoformat()}
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    summary=os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as output:
            output.write("## Nightfall render state: "+status+"\n\n")
            output.write("- Episode: "+episode+"\n- **No public upload attempted**\n")
            output.write("- "+str(details)[:300]+"\n")
            if retry_after: output.write("- Next eligible UTC: "+retry_after+"\n")
    return report

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--detect",action="store_true")
    args=parser.parse_args()
    if args.detect:
        item=next_due()
        text="has_pending="+("true" if item else "false")+"\n"
        if item: text+="pending_episode="+item["episode_id"]+"\n"
        if os.getenv("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"],"a",encoding="utf-8") as handle:
                handle.write(text)
        print("PENDING_RENDER_SCAN:",item or "no episode currently eligible")

if __name__=="__main__":
    main()
