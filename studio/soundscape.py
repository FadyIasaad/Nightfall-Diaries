"""Original generated cinematic underscore (no copyrighted music or API)."""
import numpy as np
import soundfile as sf

def add_soundscape(wav_path,series_id,volume=.095):
    signal,sr=sf.read(str(wav_path),dtype='float32')
    if signal.ndim>1: signal=signal.mean(axis=1)
    n=len(signal);t=np.arange(n,dtype=np.float32)/sr
    # An original quiet ambient chord, softened with slow tremolo and fade.
    root=57.0 if series_id.startswith('S01') else 65.4
    wave=sum(np.sin(2*np.pi*(root*x)*t+phase)*amp for x,phase,amp in ((1,0,0.35),(1.5,.7,.1),(2,.3,.15),(3,.9,.08)))
    pulse=(.70+.3*np.sin(t*2*np.pi*.13))
    attack=np.minimum(1,t/2);release=np.minimum(1,(t[-1]-t)/1.5)
    bed=wave*pulse*attack*release*volume
    result=np.clip(signal+bed,-1,1)
    sf.write(str(wav_path),result,sr,subtype='PCM_16')
    return wav_path
