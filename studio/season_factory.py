"""Create ORIGINAL next seasons from verified weekly-trend observations.
Prefer GitHub Models, but have explicitly labelled creative fallback concept arcs.
"""
import json, re, hashlib
from .util import read, save, utcnow, ROOT
from .story import github_chat, all_series
from .trends import pick_unseen

FIRST=['Iris','Kairo','Nova','Lyra','Tavi','Sora','Rin','Echo','Orin','Nia','Lio','Zuri']
VOICES=['af_aoede','am_eric','bf_isabella','bm_daniel','af_kore','am_echo','af_sky','bm_lewis','af_sarah','am_onyx','af_nova','am_adam','af_alloy','am_santa','bf_alice','bf_lily','af_jessica','af_river']
VOICE_ROLES={'hero':['af_nova','am_eric','af_aoede','am_echo','af_sky'],
             'ally':['af_sky','af_aoede','am_echo','af_sarah','af_kore'],
             'mentor':['bm_daniel','bm_lewis','af_kore','af_sarah','am_onyx'],
             'villain':['am_onyx','bm_daniel','am_adam','af_kore'],
             'narrator':['bf_isabella','bm_lewis','bf_alice','bf_lily']}

def _new_voices(cast,prior_used):
    assigned=[]
    for c in cast:
        role=c['role'].casefold()
        key=next((k for k in VOICE_ROLES if k in role),'ally')
        choices=VOICE_ROLES[key]+VOICES
        option=next((v for v in choices if v not in prior_used and v not in assigned),None)
        if option is None:
            # Finite English TTS pool: later seasons may reuse a preset, never swap mid-season.
            option=next(v for v in choices if v not in assigned)
        assigned.append(option)
    return assigned
BACKGROUND={
  'space':('The Moonlight Signal','moonlit science-fantasy','a young stargazer finds a message inside a fallen star','silver observatory','star maps'),
  'robotics':('The Robot Who Kept a Secret','robot-led sci-fi drama','a repair robot discovers that the city is powered by stolen memories','glowing factory','memory chips'),
  'ocean':('Whispers Under the Tide','undersea adventure','a young ocean guardian finds a staircase hidden beneath the waves','underwater lighthouse','pearl compass'),
  'animals':('The Hidden Animal Kingdom','animal adventure','a curious young animal discovers an invisible valley where lost creatures gather','enchanted valley','golden footprint'),
  'storms':('The Girl Who Caught Lightning','fantasy adventure','a weather apprentice receives a storm in a glass bottle','rain-covered town','glass lightning'),
  'science':('The Museum of Impossible Things','science fantasy','a museum apprentice finds a fossil that tells stories from the future','ancient museum','shifting fossil'),
  'sports':('One More Race','inspiring youth drama','a young athlete saves a forgotten community race','old stadium','silver whistle'),
  'music':('The Last Note','musical mystery drama','a student hears a melody that can unlock doors nobody remembers','empty theater','silver tuning fork'),
  'gaming':('The Door Beyond Level One','game-world fantasy','a game designer discovers an unfinished level that changes each night','pixel village','crystal controller'),
  'nature':('The Secret Inside the Seed','nature fantasy','a tiny explorer discovers a seed growing toward the stars','hidden greenhouse','blue seed')
}
STEPS=[
 ('The First Signal','The hero finds a strange clue and senses an impossible threat','A quiet voice calls from somewhere hidden'),
 ('Nobody Believes','Friends dismiss the warning, but the clue leads to a locked path','The lock opens without a key'),
 ('The New Friend','A wary companion appears and offers a dangerous bargain','The companion knows the hero’s secret'),
 ('The Map of Lies','The pair find a map that contradicts the town’s oldest story','A missing symbol begins to glow'),
 ('The Betrayal','Someone trusted hides important evidence from the team','The traitor leaves a message'),
 ('Beyond the Gate','The team enters the forbidden place and sees why it was abandoned','A hidden watcher steps from the shadows'),
 ('The Hardest Truth','A mentor reveals what happened and why it was hidden','The clue points back to the hero'),
 ('The Choice','The hero sacrifices safety to protect a stranger','The only path home disappears'),
 ('The Final Hour','Friends reunite to stop the disaster before dawn','The final signal fails'),
 ('A New Dawn','The mystery is resolved with courage and compassion; peace returns','One tiny new clue hints at the next adventure')
]

def _unique_title(base,order):
    existing={s['title'].lower() for s in all_series()}
    return base if base.lower() not in existing else f'{base}: Chapter {order}'

def _invent(topic,order):
    base,genre,logline,world,item=BACKGROUND[topic['theme']]
    name=_unique_title(base,order)
    hero=FIRST[(order*3)%len(FIRST)]
    partner=FIRST[(order*3+1)%len(FIRST)]
    mentor=FIRST[(order*3+2)%len(FIRST)]
    return {'title':name,'genre':genre,'logline':logline,'world':world,'theme':'Truth, friendship and bravery','ending':f'{hero} and {partner} use the {item} to save their community and restore hope.',
        'characters':[{'name':hero,'role':'hero','visual':f'young adventurous character with copper hair, sapphire cloak and a single silver pin; setting {world}','personality':'curious, brave, quick-witted'},
                      {'name':partner,'role':'ally','visual':f'kind cautious companion with dark curls, emerald vest and a single crescent brooch; setting {world}','personality':'loyal, clever, warm'},
                      {'name':mentor,'role':'mentor','visual':f'older mysterious mentor with silver hair, plum robe, and small round spectacles; setting {world}','personality':'measured, protective, patient'}],
        'episodes':[{'title':x[0],'main_beat':f'{hero} and {partner}: {x[1]}. Their search involves {item} in the {world}.','ending':x[2]} for x in STEPS]}

def _valid_model(raw):
    if not isinstance(raw,dict): return False
    if len(raw.get('episodes',[]))<10 or len(raw.get('episodes',[]))>12:return False
    if len(raw.get('characters',[]))<3 or len(raw['characters'])>6:return False
    for c in raw['characters']:
        if not all(isinstance(c.get(x),str) and len(c[x])>=3 for x in ('name','role','visual','personality')):return False
    for ep in raw['episodes']:
        if not all(isinstance(ep.get(x),str) and len(ep[x])>=8 for x in ('title','main_beat','ending')):return False
    for x in ('title','genre','logline','ending'):
        if not isinstance(raw.get(x),str) or len(raw[x])<7:return False
    return True

def generate_new_series(config):
    prior=read('cloud_data/series_decisions.json',{'selected':[]})
    chosen=pick_unseen(read('cloud_data/trend_history.json',{}),prior)
    if not chosen:raise RuntimeError('No verified, eligible, fresh 7-day topic found. No invented trends; retry tomorrow.')
    order=max(m['series_order'] for m in all_series())+1
    selected_source={'topic':chosen['topic'],'theme':chosen['theme'],'traffic':chosen['traffic'],'score':chosen['score'],'observations':chosen['observations'],'regions':chosen['regions'],'sources':chosen['sources'][:8]}
    system='Create an ORIGINAL cinematic, family friendly, independent 10-to-12-episode short drama. JSON only. Do NOT feature real individuals, current news facts, branded IP, copyrighted properties, or an existing franchise. Transform the given trending topic into an original fantasy motif. Return keys title,genre,logline,world,theme,ending,characters (3-5 with name,role,visual,personality), episodes (10-12 with title, main_beat, ending). Each episode has one meaningful progression; final episode resolves the entire plot. No plagiarized titles.'
    try:
        content=github_chat(system,json.dumps({'verified_trending_topic':selected_source,'previous_titles':[s['title'] for s in all_series()]},ensure_ascii=False),config['story']['github_model'])
        if not _valid_model(content):raise ValueError('Invalid generated schema')
        source='github_models'
    except Exception as e:
        # Explicitly original, deterministic fallback using the verified trend category.
        content=_invent(chosen,order)
        source='original_template_fallback'
        print('NEW SERIES MODEL FALLBACK:',type(e).__name__,str(e)[:120])
    # Names and identity of NEW season cannot accidentally inherit prior casts.
    sid=f'S{order:02d}_'+re.sub(r'[^a-z0-9]+','_',content['title'].lower()).strip('_')[:50]
    if (ROOT/'seasons'/sid).exists():raise RuntimeError('Season already exists')
    cast=[]
    used={c['voice']['voice_id'] for s in all_series() for c in json.loads((ROOT/'seasons'/s['series_id']/ 'characters/character_registry.json').read_text())['characters']}
    voices=_new_voices(content['characters']+[{'name':'Narrator','role':'narrator'}],used)
    # Reject duplicate character names and cast reused from starters.
    prior_names={c['name'].casefold() for s in all_series() for c in json.loads((ROOT/'seasons'/s['series_id']/ 'characters/character_registry.json').read_text())['characters']}
    if len(set(c['name'].casefold() for c in content['characters']))!=len(content['characters']):raise ValueError('Duplicate character names')
    if any(c['name'].casefold() in prior_names for c in content['characters']):
        for i,c in enumerate(content['characters']):c['name']=f"{c['name']} of {content.get('world','the new world')} {order}"
    for i,c in enumerate(content['characters']+[{'name':'Narrator','role':'narrator','visual':'no on-screen body','personality':'dramatic storyteller'}]):
        cid=f's{order:02d}_'+('narrator' if i==len(content['characters']) else f'cast{i+1}')
        cast.append({'id':cid,'name':c['name'],'role':c['role'],'type':'human' if i<len(content['characters']) else 'narrator','visual':c['visual'],'personality':c['personality'],
                     'palette':['midnight blue','amber','violet'],'never_change':[c['visual']],
                     'voice':{'engine':'kokoro','voice_id':voices[i],'lang':'en-GB' if voices[i].startswith(('bf','bm')) else 'en-US','speed':1.0,'voice_direction':c['personality'],'audition':f'My name is {c["name"]}. The story has only begun.'},
                     'assets':{'reference_status':'AUTO_STYLIZED_PLACEHOLDER_NOT_APPROVED','voice_status':'PRESET_NOT_AUDITIONED'},'identity_spec_lock':True})
    manifest={'series_id':sid,'title':content['title'],'series_order':order,'genre':content['genre'],'logline':content['logline'],'theme':content.get('theme','adventure'),'ending':content['ending'],'world':content.get('world','fictional'),
              'episode_count':len(content['episodes']),'source_trend':selected_source,'generation_source':source,
              'characters_file':'characters/character_registry.json','episodes_file':'episodes/episodes.json',
              'visual_reference_assets':'AUTO_STYLIZED_PLACEHOLDER','voice_sample_assets':'GENERATED_WHEN_RENDERED'}
    episodes={'series_id':sid,'episode_count':len(content['episodes']),'episodes':[
        {'episode':i,'id':f'{sid}_E{i:02d}',**ep,'status':'PLANNED','published':{}} for i,ep in enumerate(content['episodes'],1)]}
    folder=f'seasons/{sid}'
    save(folder+'/series_manifest.json',manifest)
    save(folder+'/characters/character_registry.json',{'series_id':sid,'schema_version':'3.0','render_policy':'Use persistent per-season identities and locked voice assignments','characters':cast})
    save(folder+'/episodes/episodes.json',episodes)
    # Immediately preserve every new character's reproducible visual reference.
    from .art import ensure_portrait
    for person in cast:ensure_portrait(sid,person)
    prior['selected'].append({'season':sid,'chosen_utc':utcnow(),'topic':chosen['topic'],'trend_evidence':selected_source,'generation_source':source})
    save('cloud_data/series_decisions.json',prior)
    return manifest
