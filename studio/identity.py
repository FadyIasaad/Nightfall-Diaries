"""Freeze cast appearance and voice presets between runs; explicit approvals required to recast."""
import json, hashlib
from pathlib import Path
from .util import read, save, ROOT

def identity_hash(c):
    keys=['id','name','type','species','visual','palette','never_change','voice']
    payload={key:c.get(key) for key in keys}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def verify_locked_cast(series_id,cast):
    file='cloud_data/identity_locks.json'
    recorded=read(file,{})
    signatures={c['id']:identity_hash(c) for c in cast['characters']}
    if series_id in recorded and recorded[series_id]!=signatures:
        raise RuntimeError('Character/voice identity changed mid-series. Restore it, or consciously approve new cast lock via controlled edit.')
    if series_id not in recorded:
        recorded[series_id]=signatures
        save(file,recorded)
    return True

def approved_for_public(series_id,cast):
    for c in cast['characters']:
        assets=c.get('assets',{})
        if not c['id'].endswith('narrator') and assets.get('reference_status')!='USER_APPROVED':return False
        if assets.get('voice_status')!='USER_APPROVED':return False
    return True
