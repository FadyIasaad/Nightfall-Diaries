import subprocess, math, json
from pathlib import Path
from .art import build_slide

def make_video(series_id,manifest,ep,script,cast,audio_path,durations,workdir,config):
    width=config['video']['width'];height=config['video']['height'];fps=config['video']['fps']
    if (width,height)!=(720,1280):raise ValueError('Image painter currently supports 720x1280')
    cbyid={c['id']:c for c in cast['characters']}
    slides=[]
    for n,scene in enumerate(script['scenes'],1):
        filename=workdir/f'scene_{n:02d}.png'
        build_slide(series_id,manifest,ep,cbyid[scene['character_id']],scene['text'],filename,n,len(script['scenes']))
        slides.append(filename)
    frames_file=workdir/'slides.ffconcat'
    # Concat demuxer uses last frame repeated as recommended, exact per-scene durations.
    items=['ffconcat version 1.0']
    for p,d in zip(slides,durations):
        if "'" in str(p):raise ValueError('Unsupported single quote in work directory')
        items.extend([f"file '{p}'",f'duration {d:.6f}'])
    items.append(f"file '{slides[-1]}'")
    frames_file.write_text('\n'.join(items)+'\n')
    output=workdir/f"{ep['id']}.mp4"
    # Subtle zoompan creates moving still-image animation, not rigged 3D.
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-safe','0','-f','concat','-i',str(frames_file),'-i',str(audio_path),
         '-filter_complex',f"[0:v]fps={fps},scale={width}:{height},zoompan=z='min(zoom+0.00035,1.08)':d=1:s={width}x{height}:fps={fps},format=yuv420p[v]",
         '-map','[v]','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','25','-r',str(fps),'-c:a','aac','-b:a','96k','-pix_fmt','yuv420p','-movflags','+faststart','-t',f'{sum(durations):.3f}',str(output)]
    subprocess.run(cmd,check=True,timeout=500)
    # Verify actual playable tracks and duration, before uploader sees file.
    res=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-show_entries','stream=codec_type','-of','json',str(output)],check=True,capture_output=True,text=True)
    details=json.loads(res.stdout)
    duration=float(details['format']['duration']);types={s['codec_type'] for s in details['streams']}
    if not config['video']['min_seconds']-.6<=duration<=config['video']['max_seconds']+.2:raise ValueError(f'Invalid duration {duration:.3f}s')
    if not {'video','audio'}<=types:raise ValueError('Missing video/audio track')
    return output,duration
