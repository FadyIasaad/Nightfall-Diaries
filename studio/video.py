"""Illustrated cinematic fantasy short renderer with per-shot artwork and synced captions."""
import subprocess, json
from pathlib import Path
from .cinematic_art import render_frame

def make_video(series_id,manifest,ep,script,cast,audio_path,durations,workdir,config):
    width=config['video']['width'];height=config['video']['height'];fps=config['video']['fps']
    if (width,height)!=(720,1280):raise ValueError('Cinematic painter expects 720x1280')
    cbyid={c['id']:c for c in cast['characters']}
    scenes=script['scenes']
    shots=script.get('shots') or [
        {'shot_id':f'{i+1:02d}','subtitle':sc['text'],'text':sc['text'],
         'featured_character_id':sc['character_id'],'camera_motion':'slow_push'}
        for i,sc in enumerate(scenes)]
    if len(shots)!=len(durations):raise ValueError('Audio and shot counts disagree')
    slides=[]
    for n,shot in enumerate(shots,1):
        filename=workdir/f'shot_{n:02d}.png'
        render_frame(manifest,ep,shot,n,len(shots),cbyid[shot['featured_character_id']],filename)
        slides.append(filename)
    concat=workdir/'slides.ffconcat'
    items=['ffconcat version 1.0']
    for p,d in zip(slides,durations):
        if "'" in str(p):raise ValueError('Unsupported quote in path')
        items.extend([f"file '{p}'",f'duration {d:.6f}'])
    items.append(f"file '{slides[-1]}'")
    concat.write_text('\n'.join(items)+'\n')
    target=workdir/f'{ep["id"]}.mp4'
    # Input images form time-coded shots; subtle motion is applied to every frame.
    # FPS BEFORE zoompan avoids the classic 25-frames-per-input-picture bug.
    graph=f"[0:v]fps={fps},scale=780:1387,zoompan=z='min(zoom+0.00018,1.075)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s={width}x{height}:fps={fps},format=yuv420p[v]"
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-safe','0','-f','concat','-i',str(concat),'-i',str(audio_path),
         '-filter_complex',graph,'-map','[v]','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','26',
         '-r',str(fps),'-c:a','aac','-b:a','96k','-pix_fmt','yuv420p','-movflags','+faststart','-t',f'{sum(durations):.3f}',str(target)]
    subprocess.run(cmd,check=True,timeout=700)
    res=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-show_entries','stream=codec_type','-of','json',str(target)],check=True,capture_output=True,text=True)
    info=json.loads(res.stdout)
    dur=float(info['format']['duration']);kinds={s['codec_type'] for s in info['streams']}
    if not config['video']['min_seconds']-.6<=dur<=config['video']['max_seconds']+.2:raise ValueError(f'Duration outside range: {dur:.2f}s')
    if not {'audio','video'}<=kinds:raise ValueError('Missing track')
    return target,dur
