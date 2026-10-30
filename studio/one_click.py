"""Online one-click runner: create and upload, public if explicitly enabled, otherwise private/draft."""
import argparse
import json
import shutil
import tempfile
from pathlib import Path
from .util import read,save,sha,utcnow,checkpoint,ROOT
from .story import next_episode,all_series,series_files,create_script
from .shot_plan import get_shot_plan,speech_from_plan
from .identity import verify_locked_cast
from .audio import make_audio
from .soundscape import add_soundscape
from .video import make_video
from .publish import upload_all

MODES=('generate_and_upload','preview_only','upload_private_drafts')
DESTINATIONS=('all','youtube','facebook','tiktok')

def choose(queue,episode):
    if episode=='auto':return next_episode(queue)
    for m in all_series():
        _,eps,cast=series_files(m)
        for ep in eps['episodes']:
            if ep['id']==episode:return m,ep,cast
    raise ValueError(f'Unknown episode: {episode}. Example S01_the_last_little_fox_E01')

def do_one(mode='generate_and_upload',episode='auto',destinations='all'):
    if mode not in MODES:raise ValueError('Invalid mode')
    if destinations not in DESTINATIONS:raise ValueError('Invalid destination')
    config=read('cloud_config.json')
    q=read('cloud_data/episode_queue.json')
    planned=choose(q,episode)
    if planned is None:
        from .trends import collect
        from .season_factory import generate_new_series
        collect(config)
        checkpoint('v4: observe verified trend for future series')
        new=generate_new_series(config)
        checkpoint('v4: create new original series from observed topic')
        print('NEW SERIES CREATED:',new['title'])
        planned=choose(read('cloud_data/episode_queue.json'),episode)
        if planned is None:raise RuntimeError('No episode after generation')
    manifest,ep,cast=planned
    verify_locked_cast(manifest['series_id'],cast)
    checkpoint('v4: preserve cast and voice identities')
    base=create_script(manifest,ep,cast,config)
    plan=get_shot_plan(manifest,ep,base,cast)
    script=speech_from_plan(plan)
    checkpoint('v4: save shot plan')
    with tempfile.TemporaryDirectory(prefix='nightfall_v4_') as tmp:
        wd=Path(tmp)
        wav,durations=make_audio(manifest['series_id'],script,cast,wd,config['video']['min_seconds'],config['video']['max_seconds'])
        add_soundscape(wav,manifest['series_id'])
        clip,duration=make_video(manifest['series_id'],manifest,ep,script,cast,wav,durations,wd,config)
        out=ROOT/'output';out.mkdir(exist_ok=True)
        target=out/clip.name;shutil.copy2(clip,target)
        poster=wd/'shot_01.png'
        if poster.exists():shutil.copy2(poster,out/f'{ep["id"]}_poster.png')
    q=read('cloud_data/episode_queue.json')
    q['last_preview']={'episode_id':ep['id'],'time_utc':utcnow(),'duration_sec':round(duration,2),'sha256':sha(target),'mode':mode}
    # Crucial: PREVIEW is NOT marked complete, pressing the button again keeps E01.
    save('cloud_data/episode_queue.json',q)
    checkpoint(f'v4: preview {ep["id"]} prepared')
    print('VIDEO PREVIEW:',str(target),'duration:',round(duration,2),'seconds')
    if mode=='preview_only':
        print('SAFE PREVIEW ONLY: no upload APIs called. Choose upload_private_drafts to upload.');return
    if mode=='upload_private_drafts':
        allowed={'youtube':'private','facebook':'DRAFT','tiktok':'inbox'}
        effective_config={**config,'platform_modes':allowed,'publish_unreviewed':False}
    else:
        effective_config=config

    title=f'{manifest["title"]} | Episode {ep["episode"]}/{manifest["episode_count"]} — {ep["title"]}'
    desc=f'{manifest["title"]} • Episode {ep["episode"]}/{manifest["episode_count"]}\n{manifest["logline"]}\n#FantasyDrama #AIDrama #Shorts'
    requested=None if destinations=='all' else [destinations]
    results=upload_all(ep['id'],target,title,desc,effective_config,platforms=requested,allow_safe_fallback=True)
    print('UPLOAD RESULTS:',json.dumps(results,indent=2))
    # Advance only if at least one platform actually staged an upload.
    updated=read('cloud_data/episode_queue.json')
    if any(r.get('status')=='staged' for r in updated.get('uploads',{}).get(ep['id'],{}).values()):
        updated.setdefault('rendered',{})[ep['id']]={'utc':utcnow(),'duration':round(duration,2),'source':'v4.1_cloud_upload_'+mode}
        save('cloud_data/episode_queue.json',updated)
        checkpoint(f'v4: at least one platform accepted {ep["id"]}')
    else:
        print('No upload accepted: episode stays next in queue. Check missing credentials or reconciliation status.')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=MODES,default='generate_and_upload')
    p.add_argument('--episode',default='auto')
    p.add_argument('--destinations',choices=DESTINATIONS,default='all')
    args=p.parse_args();do_one(args.mode,args.episode,args.destinations)
if __name__=='__main__':main()
