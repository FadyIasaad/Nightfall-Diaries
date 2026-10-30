"""Episode selection, fixed cast constraints, and short scene text generation."""
import json, os, re
from pathlib import Path
import requests
from .util import ROOT, read, save

def all_series():
    manifests=[]
    for p in (ROOT/'seasons').glob('*/series_manifest.json'):
        m=json.loads(p.read_text(encoding='utf-8')); manifests.append(m)
    return sorted(manifests,key=lambda x: x['series_order'])

def series_files(manifest):
    folder=ROOT/'seasons'/manifest['series_id']
    return folder, json.loads((folder/'episodes/episodes.json').read_text()), json.loads((folder/'characters/character_registry.json').read_text())

def next_episode(queue):
    """Never jump an unfinished episode or a future series."""
    for manifest in all_series():
        folder, collection, cast = series_files(manifest)
        eps=sorted(collection['episodes'],key=lambda x:x['episode'])
        if len(eps)<10: raise ValueError('Series must have >=10 episodes')
        for ep in eps:
            if ep['id'] not in queue['rendered']:
                return manifest, ep, cast
    return None

def neutral_script(manifest, ep, cast):
    """Deterministic original motion-comic baseline using *real saved* story beats.
    This is a basic fallback, not falsely attributed AI dialogue or full screenplay.
    """
    named=[c for c in cast['characters'] if not c['id'].endswith('narrator')]
    narrator=next(c for c in cast['characters'] if c['id'].endswith('narrator'))
    hero=named[0]
    supporting=named[(ep['episode'] % max(1,len(named)-1))] if len(named)>1 else hero
    beat=ep['main_beat'].rstrip('. ')
    cliff=ep['ending'].rstrip('. ')
    return {'source':'authored_template_from_locked_outline','episode_id':ep['id'],'scenes':[
      {'character_id':narrator['id'],'text':f"Episode {ep['episode']}. {ep['title']}. The story takes another unexpected turn. {beat}."},
      {'character_id':hero['id'],'text':f"There is something I still don't understand. I need to find out what happened before it's too late."},
      {'character_id':supporting['id'],'text':"Look again. The smallest detail might be the one that changes everything. We cannot give up now."},
      {'character_id':narrator['id'],'text':f"But one question remained. {cliff}? The answer comes in the next episode."}
    ]}

def validate_script(script, cast, ep):
    ids={c['id'] for c in cast['characters']}
    if not isinstance(script,dict) or not 3<=len(script.get('scenes',[]))<=7: raise ValueError('script must have 3-7 scenes')
    for scene in script['scenes']:
        if scene.get('character_id') not in ids: raise ValueError('Unregistered speaker')
        if not isinstance(scene.get('text'),str) or len(scene['text'].strip())<8 or len(scene['text'])>600: raise ValueError('Invalid line')
    if script.get('episode_id') != ep['id']: raise ValueError('Wrong episode id')
    return script

def github_chat(system,user,model):
    token=os.environ.get('GH_MODELS_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token: raise RuntimeError('GitHub Models token missing')
    resp=requests.post('https://models.github.ai/inference/chat/completions',headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},json={'model':model,'temperature':0.65,'response_format':{'type':'json_object'},'messages':[{'role':'system','content':system},{'role':'user','content':user}]},timeout=90)
    resp.raise_for_status()
    content=resp.json()['choices'][0]['message']['content']
    result=json.loads(content)
    return result

def create_script(manifest,ep,cast,config):
    path=f"seasons/{manifest['series_id']}/scripts/E{ep['episode']:02d}.json"
    old=read(path)
    if old: return validate_script(old,cast,ep)
    system=('You write original family-friendly dramatic 35-60 second motion-comic scripts. '
            'Return ONLY JSON {"episode_id":"...", "scenes":[{"character_id":"...","text":"..."}]}. '
            'Use 4 scenes, 12-26 spoken words each, natural emotional language, consistent with existing plot, '
            'end on precise cliffhanger. Use ONLY speaker IDs in character registry. No real public figures or copyrighted characters.')
    data={'series':manifest['title'],'series_ending':manifest.get('ending'),'episode':ep,'fixed_cast':[
        {'id':c['id'],'name':c['name'],'personality':c.get('personality'),'voice':c['voice']['voice_id']} for c in cast['characters']]}
    try:
        result=github_chat(system,json.dumps(data,ensure_ascii=False),config['story']['github_model'])
        result=validate_script(result,cast,ep)
        result['source']='github_models'
    except Exception as e:
        if not (config['story']['starter_offline_baseline_fallback'] and manifest['series_order']<=2):
            raise RuntimeError(f'No valid model-written episode: {type(e).__name__}: {e}') from e
        result=neutral_script(manifest,ep,cast)
        validate_script(result,cast,ep)
        print('NOTE: using simple starter baseline, model not available:',str(e)[:120])
    save(path,result)
    return result
