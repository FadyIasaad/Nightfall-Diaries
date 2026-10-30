"""One daily run: collect trends, render one episode, stage to allowed platforms.
Run: python -m studio.main [--dry-run] [--plan-only] [--backfill]
"""
import argparse, json, os, tempfile
from pathlib import Path
from .util import read, save, sha, utcnow, checkpoint, ROOT
from .story import next_episode, create_script, all_series
from .trends import collect, rank
from .season_factory import generate_new_series
from .identity import verify_locked_cast, approved_for_public
from .audio import make_audio
from .video import make_video
from .publish import upload_all

def run(args):
    config=read('cloud_config.json')
    if not config:raise RuntimeError('Config missing')
    if args.dry_run:
        queue=read('cloud_data/episode_queue.json');n=next_episode(queue)
        print(json.dumps({'planned': n[1]['id'] if n else 'generate new season','already_rendered':len(queue.get('rendered',{})),
                          'series_count':len(all_series()),'trending_topics':len(rank(read('cloud_data/trend_history.json',{})))},indent=2))
        return
    history=collect(config)
    print('TREND RSS:',len(history['entries']),'observations;',len(history['errors']),'country errors')
    checkpoint('cloud: seven-day trend observations')
    queue=read('cloud_data/episode_queue.json')
    if args.plan_only:
        print(json.dumps({'next':next_episode(queue)[1]['id'] if next_episode(queue) else None,'trend_rank':rank(history)[:3]},indent=2));return
    if args.backfill:
        # Intentionally explicit: backfill MP4s must be regenerated from saved scripts.
        candidates=[(id,pl) for id,platforms in queue['uploads'].items() for pl,rec in platforms.items() if rec.get('status')=='missing_credentials']
        print('Use artifacts for manual backfill; unattended duplicate-retry is disabled:',len(candidates));return
    planned=next_episode(queue)
    if not planned:
        if not config['series']['auto_new_after_starters']:print('All series completed. Auto-new disabled.');return
        try:
            new_manifest=generate_new_series(config)
        except RuntimeError as e:
            queue['pending_series_generation']=True;save('cloud_data/episode_queue.json',queue)
            checkpoint('cloud: future season awaiting verified trends')
            print('WAITING FOR REAL TREND:',e);return
        checkpoint('cloud: new trend-driven series generated')
        queue['pending_series_generation']=False;save('cloud_data/episode_queue.json',queue)
        planned=next_episode(queue)
    manifest,ep,cast=planned
    verify_locked_cast(manifest['series_id'],cast)
    checkpoint('cloud: immutable cast voice and visual IDs')
    print('CREATING:',ep['id'])
    if args.plan_only:return
    script=create_script(manifest,ep,cast,config)
    with tempfile.TemporaryDirectory(prefix='drama_cloud_') as name:
        workdir=Path(name)
        audio,durations=make_audio(manifest['series_id'],script,cast,workdir,config['video']['min_seconds'],config['video']['max_seconds'])
        mp4,duration=make_video(manifest['series_id'],manifest,ep,script,cast,audio,durations,workdir,config)
        # COPY mp4 for Actions artifact; never commit high-size video to git.
        target=ROOT/'output'/mp4.name;target.parent.mkdir(exist_ok=True)
        import shutil;shutil.copy2(mp4,target)
        queue=read('cloud_data/episode_queue.json')
        queue['rendered'][ep['id']]={'utc':utcnow(),'sha256':sha(target),'duration':round(duration,2),'script_source':script.get('source')}
        save('cloud_data/episode_queue.json',queue)
        checkpoint(f'cloud: produced {ep["id"]} and locked cast assets')
        desc=f"{manifest['title']} | Episode {ep['episode']}/{manifest['episode_count']}: {ep['title']}\n{manifest['logline']}\n#ShortDrama #AnimatedStory #AIDrama"
        title=f"{manifest['title']} | Ep {ep['episode']} — {ep['title']}"
        wants_public = config['platform_modes']['youtube']=='public' or config['platform_modes']['facebook']=='PUBLISHED'
        if wants_public and not approved_for_public(manifest['series_id'],cast):
            print('PUBLIC UPLOAD GATE: cast visual references and voice auditions not all user-approved; recording review needed.')
            upload_config={**config,'publish_unreviewed':False}
        else:
            upload_config=config
        print('UPLOAD RESULTS:',json.dumps(upload_all(ep['id'],target,title,desc,upload_config),indent=2))
        # Try to create NEXT story bible after the final starter/future episode; no posting before its turn.
        # New series may also be created on next scheduled run if trend data is unavailable today.
        try:
            if next_episode(read('cloud_data/episode_queue.json')) is None and config['series']['auto_new_after_starters']:
                nxt=generate_new_series(config);checkpoint('cloud: next trend-driven story bible')
                print('NEXT SEASON READY:',nxt['title'])
        except Exception as e:print('Next season not created yet:',type(e).__name__,str(e)[:200])
        print('ARTIFACT:',target)

def main():
    p=argparse.ArgumentParser();p.add_argument('--dry-run',action='store_true');p.add_argument('--plan-only',action='store_true');p.add_argument('--backfill',action='store_true')
    run(p.parse_args())
if __name__=='__main__':main()
