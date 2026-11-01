import argparse,json,subprocess,tempfile,pathlib
from .audio import synthesize
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 a=argparse.ArgumentParser();a.add_argument('--episode',default='S01_the_last_little_fox_E01');args=a.parse_args()
 ep=args.episode
 if '/' in ep or '..' in ep or not(ep.startswith('S01_the_last_little_fox_E') or ep.startswith('S02_the_boy_who_forgot_tomorrow_E')):raise SystemExit('Invalid episode identifier')
 series=ep.rsplit('_E',1)[0];number=ep.rsplit('_E',1)[1]
 p=ROOT/'seasons'/series/'scripts'/f'E{int(number):02d}.json'
 if not p.exists():raise SystemExit(f'Authored episode script missing: {p}')
 script=json.loads(p.read_text())
 if script.get('episode_id')!=ep:raise SystemExit('Episode identity mismatch')
 scenes=script['scenes']
 with tempfile.TemporaryDirectory() as tmp:
  wd=pathlib.Path(tmp);segments=synthesize(scenes,wd)
  # Each narration segment gets its own moving-camera / character animation shot.
  # The 3D animation is rendered by Blender: no static screenshots or zoompan images.
  durations=[max(5.0,s+0.4) for _,s in segments]
  plan={'episode':ep,'scenes':scenes,'durations':durations,'series':series}
  (wd/'plan.json').write_text(json.dumps(plan))
  shotfiles=[]
  for i,(wav,seconds) in enumerate(segments):
   shot=wd/f'shot_{i:02d}.mp4';shotfiles.append(shot)
   subprocess.run(['blender','-b','-t','2','--python',str(ROOT/'studio'/'render_blender.py'),'--',str(wd/'plan.json'),str(i),str(shot)],check=True,timeout=1100)
  concat=wd/'parts.txt';concat.write_text(''.join("file '"+str(p)+"'\n" for p in shotfiles))
  out=ROOT/'output';out.mkdir(exist_ok=True)
  # WAV segments differ from final shot lengths; create an audio timeline in exact order.
  filters=''.join(f'[{i}:a]apad=pad_dur={max(0,d-segments[i][1]):.3f},atrim=duration={d:.3f},asetpts=PTS-STARTPTS[a{i}];' for i,d in enumerate(durations))
  filters+=''.join(f'[a{i}]' for i in range(len(durations)))+f'concat=n={len(durations)}:v=0:a=1[a]'
  audio=wd/'speech.wav'
  cmd=['ffmpeg','-hide_banner','-loglevel','error','-y']
  for wav,_ in segments:cmd.extend(['-i',str(wav)])
  cmd.extend(['-filter_complex',filters,'-map','[a]',str(audio)])
  subprocess.run(cmd,check=True,timeout=120)
  combined=wd/'combined.mp4'
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-i',str(audio),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-shortest',str(combined)],check=True,timeout=300)
  dest=out/f'{ep}.mp4';dest.write_bytes(combined.read_bytes());print('PREVIEW_READY',dest, 'seconds',round(sum(durations),2))
if __name__=='__main__':main()
