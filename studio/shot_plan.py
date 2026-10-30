"""Persisted shot plans; 8 carefully art-directed shots for E01, stable derived shots otherwise."""
import re
from .util import read, save

MOODS=('mystery','magic','fire','mystery','magic','mystery','cliffhanger','magic')

def _split(text):
    # Keep each spoken phrase expressive without splitting arbitrary words.
    sentences=[s.strip() for s in re.split(r'(?<=[.!?])\s+',text.strip()) if s.strip()]
    result=[]
    for sentence in sentences:
        if len(sentence.split())>16:
            parts=re.split(r',\s+|;\s+|\s+(?=but\b|and\b|because\b)',sentence,flags=re.I)
            result.extend([p.strip() for p in parts if p.strip()])
        else:result.append(sentence)
    return result

def _fallback(manifest,ep,script,cast):
    hero=next(c for c in cast['characters'] if c.get('type')!='narrator')
    shots=[]
    for scene in script['scenes']:
        featured=scene['character_id'] if 'narrator' not in scene['character_id'] else hero['id']
        for part in _split(scene['text']):
            shots.append({'shot_id':f'{len(shots)+1:02d}', 'character_id':scene['character_id'],
                          'featured_character_id':featured,'text':part,'subtitle':part,
                          'mood':MOODS[len(shots)%len(MOODS)],'camera_motion':'slow_push',
                          'image_prompt':f'Original illustrated dark fantasy storybook scene; {manifest.get("world","magical world")}; {part}; cinematic vertical composition, expressive character; no text.'})
    if len(shots)<6:
        # Split longer lines at natural middle spaces to create at least six panels.
        i=0
        while len(shots)<6 and i<len(shots):
            tokens=shots[i]['text'].split()
            if len(tokens)>=10:
                j=len(tokens)//2
                a=dict(shots[i]);b=dict(shots[i]);a['text']=' '.join(tokens[:j]);b['text']=' '.join(tokens[j:]);a['subtitle']=a['text'];b['subtitle']=b['text']
                shots[i:i+1]=[a,b]
            i+=1
    for i,shot in enumerate(shots):shot['shot_id']=f'{i+1:02d}'
    return {'episode_id':ep['id'],'visual_style':'stylized illustrated cinematic fantasy, character-locked, not photorealistic','shots':shots}

def get_shot_plan(manifest,ep,script,cast):
    path=f'episode_shots/{manifest["series_id"]}/E{ep["episode"]:02d}.json'
    plan=read(path)
    if plan is None:
        plan=_fallback(manifest,ep,script,cast)
        save(path,plan)
    verify(plan,ep,cast)
    return plan

def verify(plan,ep,cast):
    characters={c['id'] for c in cast['characters']}
    if plan.get('episode_id')!=ep['id']:raise ValueError('Shot plan and episode do not match')
    shots=plan.get('shots',[])
    if not 6<=len(shots)<=14:raise ValueError('Shot plans must have 6-14 shots')
    ids=[s['shot_id'] for s in shots]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate shot IDs')
    for s in shots:
        if s['character_id'] not in characters or s['featured_character_id'] not in characters:raise ValueError('Invalid character in shot plan')
        if not s.get('text') or len(s['text'])>360:raise ValueError('Shot narration invalid')
        if not s.get('subtitle'):raise ValueError('Subtitle missing')
    return True

def speech_from_plan(plan):
    return {'episode_id':plan['episode_id'],'source':'saved_shot_plan',
            'scenes':[{'character_id':s['character_id'],'text':s['text']} for s in plan['shots']],
            'shots':plan['shots']}
