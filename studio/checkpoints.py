"""Safe reusable video-shot checkpoints for interruptible cloud rendering.

Files are restored via GitHub Actions cache. Their fingerprints prevent reuse
when the reference image, voice, prompt or provider settings have changed.
The cache is best effort and is not a permanent archive.
"""
import hashlib
import json
import re
import shutil
from pathlib import Path
from .restore import ROOT

CACHE_ROOT=ROOT/"output"/"checkpoints"

def fingerprint(parts):
    content=json.dumps(parts,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def paths(episode,mode,shot,part,root=CACHE_ROOT):
    if not re.fullmatch(r"S0[12]_[a-z_]+_E\d{2}",episode) or mode not in ("proof","full"):
        raise ValueError("Unsafe checkpoint identity")
    folder=Path(root)/episode/mode
    basename=f"shot_{shot:03d}_clip_{part:03d}"
    return folder/(basename+".mp4"),folder/(basename+".json")

def restore_clip(episode,mode,shot,part,expected,destination,root=CACHE_ROOT):
    video,record=paths(episode,mode,shot,part,root)
    if not (video.is_file() and record.is_file()):
        return False
    try:
        meta=json.loads(record.read_text(encoding="utf-8"))
        if meta.get("fingerprint")!=expected or video.stat().st_size<10000:
            return False
        if meta.get("sha256")!=hashlib.sha256(video.read_bytes()).hexdigest():
            return False
        dest=Path(destination);dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(video,dest)
        return True
    except (OSError,ValueError,TypeError):
        return False

def save_clip(episode,mode,shot,part,expected,source,root=CACHE_ROOT):
    video,record=paths(episode,mode,shot,part,root)
    source=Path(source)
    if source.stat().st_size<10000:
        raise ValueError("Cannot checkpoint tiny/corrupt moving clip")
    video.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,video)
    meta={"fingerprint":expected,
          "sha256":hashlib.sha256(video.read_bytes()).hexdigest(),
          "episode":episode,"mode":mode,"shot":shot,"part":part,
          "status":"TECHNICAL_MOTION_ONLY_NOT_VISUALLY_APPROVED"}
    tmp=record.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    tmp.replace(record)
    return record
