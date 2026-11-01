"""Zero-budget offline fallback voice. Not comparable to studio quality."""
import subprocess,wave,pathlib,struct

def synthesize(scenes,directory):
 directory=pathlib.Path(directory);directory.mkdir(parents=True,exist_ok=True)
 segments=[]
 for i,scene in enumerate(scenes):
  dest=directory/f'voice_{i:02d}.wav'
  text=scene['text'][:650]
  subprocess.run(['espeak-ng','-v','en-us','-s','150','-w',str(dest),text],check=True,stdout=subprocess.DEVNULL)
  with wave.open(str(dest),'rb') as w: seconds=w.getnframes()/w.getframerate()
  segments.append((dest,seconds))
 return segments
