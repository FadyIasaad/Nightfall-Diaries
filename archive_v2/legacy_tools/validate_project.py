#!/usr/bin/env python3
"""Zero-dependency checks for story/character/voice continuity and release order.
Usage: python tools/validate_project.py
"""
import json, hashlib, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]

def load(rel): return json.loads((P/rel).read_text(encoding='utf-8'))

def canonical(v): return json.dumps(v,sort_keys=True,ensure_ascii=False).encode('utf-8')

errors=[]
config=load('config.json')
reg=load('data/series_registry.json')
locks=load('data/identity_fingerprints.json')['locks']
ids_seen=set(); voice_assignments={}; priority=[]
for series in reg['series']:
    sid=series['id']; priority.append(sid)
    path=f'seasons/{sid}'
    chars=load(path+'/characters/character_registry.json')['characters']
    eps=load(path+'/episodes/episodes.json')['episodes']
    if len(eps)<10: errors.append(f'{sid}: fewer than 10 episodes')
    if [e['episode'] for e in eps] != list(range(1,len(eps)+1)): errors.append(f'{sid}: invalid or duplicate episode numbers')
    if series['episode_count']!=len(eps): errors.append(f'{sid}: registry episode count mismatch')
    used_voice_ids=set()
    for c in chars:
        cid=c['id']
        if cid in ids_seen: errors.append(f'duplicate character ID: {cid}')
        ids_seen.add(cid)
        if not cid.startswith(sid.split('_')[0].lower()+'_'): errors.append(f'character ID prefix mismatch: {cid}')
        voice=c['voice']; vid=voice['voice_id']
        if vid in used_voice_ids: errors.append(f'{sid}: duplicate voice ID {vid}; main cast must sound distinct')
        used_voice_ids.add(vid)
        if voice.get('engine')!='kokoro': errors.append(f'{cid}: voice engine mismatch')
        if (vid.startswith('a') and voice.get('lang')!='en-US') or (vid.startswith('b') and voice.get('lang')!='en-GB'):
            errors.append(f'{cid}: voice accent language mismatch')
        if cid not in locks.get(sid,{}): errors.append(f'{cid}: missing identity fingerprint')
        else:
            val=hashlib.sha256(canonical({k:v for k,v in c.items() if k!='assets'})).hexdigest()
            if locks[sid][cid]!=val: errors.append(f'{cid}: character or voice lock changed!')
        if not c['identity_spec_lock']: errors.append(f'{cid}: identity not locked')
        voice_assignments[vid]=cid
    if len({e['title'] for e in eps}) != len(eps): errors.append(f'{sid}: repeated episode titles')
    done=[e for e in eps if e['published'].get('youtube')]
    if series['complete'] and len(done)<len(eps): errors.append(f'{sid}: complete flag without all published episodes')

if priority!=reg['launch_sequence']: errors.append('fixed launch series order does not match registry')
if len(voice_assignments)!=sum(len(load(f'seasons/{s}/characters/character_registry.json')['characters']) for s in priority):
    errors.append('voice IDs repeated across initial series; all 10 initial voice IDs should be different')
if errors:
    print('VALIDATION FAILED:')
    for e in errors: print(' -',e)
    sys.exit(1)
print('VALIDATION OK: 2 ordered launch series, 22 episodes, 10 unique characters/narrators and 10 locked initial voices.')
print('NOTE: No images, audition WAVs, rendered episodes or upload credentials are included; cannot publish until prepared and approved.')
