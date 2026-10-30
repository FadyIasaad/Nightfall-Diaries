#!/usr/bin/env python3
"""Approve and hash *actual* reference PNGs + audition WAV for one character.
Run only after manually reviewing each image and listening to the audition.
Usage: python tools/lock_character_assets.py S01_the_last_little_fox s01_ember
       python tools/lock_character_assets.py --verify
No placeholder/absent files are ever marked approved. Existing locks cannot silently change.
"""
import hashlib, json, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
LOCK_FILE=P/'data/approved_asset_locks.json'

def digest(file):
    h=hashlib.sha256()
    with file.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def read_locks():
    if not LOCK_FILE.exists(): return {'schema_version':'1.0','locks':{}}
    return json.loads(LOCK_FILE.read_text(encoding='utf-8'))

def verify():
    obj=read_locks(); bad=0
    for sid, cast in obj['locks'].items():
        for cid, paths in cast.items():
            for rel, expected in paths.items():
                p=P/'seasons'/sid/rel
                if not p.is_file() or digest(p)!=expected:
                    print('CHANGED/MISSING:',sid,cid,rel); bad+=1
                else: print('VALID:',sid,cid,rel)
    if bad: sys.exit(1)
    print('Approved asset hashes match. This is a file-integrity check, not a visual/audio quality test.')

def lock(sid,cid):
    f=P/'seasons'/sid/'characters/character_registry.json'
    if not f.is_file(): sys.exit('Unknown series')
    obj=json.loads(f.read_text(encoding='utf-8'))
    cs=[c for c in obj['characters'] if c['id']==cid]
    if len(cs)!=1: sys.exit('Unknown character')
    c=cs[0]; assets=c['assets']
    relpaths=[v for k,v in assets.items() if k in ('front_ref','side_ref','three_quarter_ref','voice_audition') and v]
    collected={}
    for rel in relpaths:
        path=P/'seasons'/sid/rel
        if not path.is_file() or path.stat().st_size==0: sys.exit(f'MISSING required real asset: {path}')
        with path.open('rb') as f: header=f.read(12)
        if path.suffix=='.png' and not header.startswith(b'\x89PNG\r\n\x1a\n'): sys.exit(f'Not a PNG: {path}')
        if path.suffix=='.wav' and not (header[:4]==b'RIFF' and header[8:12]==b'WAVE'):
            sys.exit(f'Not a standard WAV: {path}')
        collected[rel]=digest(path)
    locks=read_locks()
    old=locks['locks'].get(sid,{}).get(cid)
    if old is not None:
        if old != collected: sys.exit('Existing lock differs! Do not replace a published character without an explicit reviewed versioning process.')
        print('Already locked and unchanged:',sid,cid);return
    locks['locks'].setdefault(sid,{})[cid]=collected
    LOCK_FILE.write_text(json.dumps(locks,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('APPROVED AND LOCKED:',sid,cid, 'files:', len(collected))
    print('Remember to preserve files and back them up. Run --verify before every publishing batch.')

if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='--verify': verify()
    elif len(sys.argv)==3: lock(sys.argv[1],sys.argv[2])
    else: sys.exit('Usage: python tools/lock_character_assets.py SERIES_ID CHARACTER_ID | --verify')
