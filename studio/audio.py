"""Kokoro per-character voice pipeline. No Edge TTS or paid API.
We keep the Kokoro voice ID from the locked series registry for every line.
"""
import wave, json, shutil
from pathlib import Path
import numpy as np
import soundfile as sf
from .util import ROOT

def _speak(kpipeline,text,c):
    """Return mono PCM at 24kHz."""
    segments=[]
    for _graphemes,_phonemes,chunk in kpipeline(text,voice=c['voice']['voice_id'],speed=c['voice'].get('speed',1.0),split_pattern=r'\n+'):
        a=np.asarray(chunk,dtype='float32').reshape(-1)
        if len(a):segments.append(a)
    if not segments:raise RuntimeError('Kokoro returned no audio')
    return np.concatenate(segments)

def make_audio(series_id,script,cast,workdir,min_seconds=35,max_seconds=60):
    from kokoro import KPipeline
    characters={c['id']:c for c in cast['characters']}
    engines={}
    samples=[];durations=[];sr=24000
    for i,scene in enumerate(script['scenes']):
        c=characters[scene['character_id']]
        lang='b' if c['voice']['voice_id'].startswith(('bf','bm')) else 'a'
        if lang not in engines:engines[lang]=KPipeline(lang_code=lang)
        audio=_speak(engines[lang],scene['text'],c)
        # 600ms breath between lines; saved as part of scene audio.
        audio=np.concatenate([audio,np.zeros(int(sr*.60),dtype='float32')])
        samples.append(audio);durations.append(len(audio)/sr)
        # First audition is the very same stable voice ID; preserve it with the cast.
        audition=ROOT/'seasons'/series_id/'voices'/c['id']/'cloud_audition.wav'
        if not audition.exists():
            audition.parent.mkdir(parents=True,exist_ok=True)
            sample=_speak(engines[lang],c['voice'].get('audition',f'My name is {c["name"]}.'),c)
            sf.write(audition,sample,sr,subtype='PCM_16')
    total=sum(durations)
    if total<min_seconds:
        extra=min_seconds-total+0.6
        samples[-1]=np.concatenate([samples[-1],np.zeros(round(extra*sr),dtype='float32')]);durations[-1]+=extra;total+=extra
    if total>max_seconds:
        raise ValueError(f'Audio too long ({total:.1f}s): shorten script; do not publish over {max_seconds}s')
    audio_path=workdir/'narration.wav'
    sf.write(audio_path,np.concatenate(samples),sr,subtype='PCM_16')
    return audio_path,durations
