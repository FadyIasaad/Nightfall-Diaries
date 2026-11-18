"""Original 180s E01 cloud-only story soundtrack, with real locked neural cast.

Audio is a production component, NOT an animated episode or proof of lip sync.
No paid inference, GPU, new social releases, sample loops, or stretched speech.
Creates exact 15x12s timeline with dynamically generated ORIGINAL ambient Foley.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCREENPLAY = ROOT / "seasons/S01_the_last_little_fox/revised_screenplays/E01_2026-11-18.json"
CAST_FILE = ROOT / "seasons/S01_the_last_little_fox/characters/character_registry.json"
OUT = ROOT / "output/e01_180s_cinematic_soundtrack"
SAMPLE_RATE = 24000
SCENE_SECONDS = 12
EP_SECONDS = 180
PAID_KEYS = ("OPENAI_API_KEY", "ELEVENLABS_API_KEY", "AGNES_API_KEY",
             "RUNWAY_API_KEY", "DASHSCOPE_API_KEY", "EVERYPIXEL_API_KEY")


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(128 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_story():
    script = json.loads(SCREENPLAY.read_text(encoding="utf-8"))
    registry = json.loads(CAST_FILE.read_text(encoding="utf-8"))
    cast = {c["id"]: c for c in registry["characters"]}
    scenes = script["scenes"]
    if (script["episode_id"] != "S01_the_last_little_fox_E01"
        or script["target_duration_seconds"] != EP_SECONDS
        or len(scenes) != 15
        or any(s["scene"] != i + 1 or s["target_seconds"] != SCENE_SECONDS
               or not s.get("text") or s["character_id"] not in cast
               for i, s in enumerate(scenes))):
        raise RuntimeError("ORIGINAL_REVISED_E01_SCRIPT_LOCK_OR_DURATION_INVALID")
    return scenes, cast


def atmosphere(scene_num, n, np):
    """Original deterministic 2-channel fire/wind/ash texture, no licensed samples."""
    rng = np.random.default_rng(51140 + scene_num)
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    # Low-frequency swells of wind over the whole valley.
    low_knots = np.arange(0, n + 4800, 4800)
    mid_knots = np.arange(0, n + 480, 480)
    low = np.interp(np.arange(n), low_knots,
                    rng.normal(0, .8, len(low_knots))).astype(np.float32)
    mid = np.interp(np.arange(n), mid_knots,
                    rng.normal(0, .7, len(mid_knots))).astype(np.float32)
    left = (.016 * low + .009 * mid + .0038 * rng.normal(size=n)).astype(np.float32)
    right = (.014 * low + .010 * np.roll(mid, 35) +
             .0038 * rng.normal(size=n)).astype(np.float32)
    # More fire early; eerie blue-feather/river air in the second half.
    fire = scene_num in (1,2,3,4,5,6,7,8,9,10,11,12)
    if fire:
        for _ in range(50):
            k = int(rng.integers(0, max(1, n - 1600)))
            length = min(int(rng.integers(150, 1500)), n-k)
            decay = np.exp(-np.arange(length, dtype=np.float32) /
                           rng.uniform(70,330)).astype(np.float32)
            crack = (rng.normal(0, 1, length) * decay *
                     rng.uniform(.012,.034)).astype(np.float32)
            left[k:k+length] += crack
            right[k:k+length] += crack * rng.uniform(.6,1.0)
    else:
        tone = np.sin(2 * np.pi * 118 * t) * np.sin(2 * np.pi * .27 * t)
        left += .0035 * tone.astype(np.float32)
        right += .0025 * np.roll(tone.astype(np.float32),120)
    return np.stack((left,right),axis=-1)


def compose():
    if any(os.getenv(name) for name in PAID_KEYS):
        raise RuntimeError("PAID_INFERENCE_SECRET_PRESENT_REFUSE_THIS_JOB")
    import numpy as np
    import soundfile as sf
    from studio.neural_audio import render_kokoro
    OUT.mkdir(parents=True, exist_ok=True)
    scenes, cast = validate_story()
    audio = np.zeros((EP_SECONDS * SAMPLE_RATE, 2), dtype=np.float32)
    cue_records = []
    for i, scene in enumerate(scenes):
        scene_no = scene["scene"]
        speaker = scene["character_id"]
        person = cast[speaker]
        voice = person.get("voice") or {}
        if voice.get("engine") != "kokoro" or not voice.get("voice_id"):
            raise RuntimeError(f"VOICE_ENGINE_NOT_ORIGINAL_KOKORO_SCENE_{scene_no:02d}")
        wav = OUT / f"scene_{scene_no:02d}_{speaker}.wav"
        if not wav.exists():
            render_kokoro(scene["text"], person, wav)
        voice_data, sr = sf.read(wav, dtype="float32", always_2d=False)
        if sr != SAMPLE_RATE:
            raise RuntimeError("ORIGINAL_VOICE_UNEXPECTED_SAMPLE_RATE")
        if voice_data.ndim != 1:
            voice_data = voice_data.mean(axis=-1)
        voice_duration = len(voice_data) / sr
        # No cutting, artificial speed-up, silence filling to fake speech or loops.
        start_offset = 1.0 if speaker != "s01_narrator" else 1.25
        if start_offset + voice_duration > SCENE_SECONDS - .35:
            raise RuntimeError(f"SCENE_{scene_no:02d}_VOICE_EXCEEDS_AUTHENTIC_SCENE_WINDOW_{voice_duration:.2f}")
        scene_start = i * SCENE_SECONDS * SAMPLE_RATE
        n = SCENE_SECONDS * SAMPLE_RATE
        env = atmosphere(scene_no, n, np)
        # Ambient remains below spoken voices, but audible between action beats.
        local = env
        offset_samples = round(start_offset * SAMPLE_RATE)
        voice_end = offset_samples + len(voice_data)
        # Keep the voice center while atmosphere remains spatially wider.
        voice_mono = np.clip(voice_data, -.99, .99) * .66
        envelope = np.ones(len(voice_mono), dtype=np.float32)
        ramp = min(len(envelope)//3, round(.025 * sr))
        if ramp > 0:
            envelope[:ramp] = np.linspace(0,1,ramp,endpoint=False)
            envelope[-ramp:] = np.linspace(1,0,ramp,endpoint=False)
        local[offset_samples:voice_end, 0] += voice_mono * envelope
        local[offset_samples:voice_end, 1] += voice_mono * envelope
        audio[scene_start:scene_start+n,:] = local
        cue_records.append({
            "scene":scene_no,
            "beat":scene["beat"],
            "speaker":speaker,
            "locked_voice_id":voice["voice_id"],
            "spoken_text":scene["text"],
            "scene_start_seconds":i*SCENE_SECONDS,
            "scene_end_seconds":(i+1)*SCENE_SECONDS,
            "voice_start_seconds":round(i*SCENE_SECONDS+start_offset,3),
            "voice_end_seconds":round(i*SCENE_SECONDS+start_offset+voice_duration,3),
            "voice_file":wav.name,
            "voice_sha256":file_sha(wav),
            "voice_duration_seconds":round(voice_duration,3),
            "no_animated_scene_claim":True,
        })
        print(f"E01_ORIGINAL_NEURAL_CUE scene={scene_no:02d} voice={voice['voice_id']} duration={voice_duration:.2f}s",flush=True)
    # Avoid digital clipping but retain each natural speaking interval.
    peak = float(np.max(np.abs(audio)))
    if peak > .92:
        audio *= .92 / peak
    # Natural film open/end fades; not silent gaps between scenes.
    fade = int(.45 * SAMPLE_RATE)
    audio[:fade] *= np.linspace(0,1,fade)[:,None]
    audio[-fade:] *= np.linspace(1,0,fade)[:,None]
    full_wav = OUT/"Nightfall_S01_E01_180s_original_soundtrack_REVIEW.wav"
    sf.write(full_wav, audio, SAMPLE_RATE, subtype="PCM_16")
    # Encode original soundtrack for quick audition and editor ingest.
    mp3 = OUT/"Nightfall_S01_E01_180s_original_soundtrack_REVIEW.mp3"
    subprocess.run([
        "ffmpeg","-hide_banner","-loglevel","error","-y",
        "-i",str(full_wav),"-c:a","libmp3lame","-q:a","3",str(mp3)
    ],check=True,timeout=160)
    from collections import Counter
    # RMS per complete second (except expected head/tail fade); no dead intervals.
    v = audio.reshape(EP_SECONDS,SAMPLE_RATE,2)
    rms = np.sqrt((v**2).mean(axis=(1,2)))
    if min(rms[1:-1]) < 0.002:
        raise RuntimeError("SILENT_ONE_SECOND_GAP_IN_SOUNDTRACK")
    if not mp3.is_file() or mp3.stat().st_size < 100000:
        raise RuntimeError("MP3_MISSING_OR_EMPTY")
    result = {
        "episode":"S01_the_last_little_fox_E01",
        "status":"FULL_180S_AUDIO_TRACK_READY_VISUAL_VIDEO_NOT_PRODUCED",
        "story_source":str(SCREENPLAY.relative_to(ROOT)),
        "story_sha256":file_sha(SCREENPLAY),
        "duration_seconds":EP_SECONDS,
        "scene_count":len(scenes),
        "voice_count":len(cue_records),
        "voice_engine":"original_Kokoro_CPU",
        "cast_voice_ids":dict(Counter(x["locked_voice_id"] for x in cue_records)),
        "min_between_scene_one_second_rms":round(float(min(rms[1:-1])),6),
        "wav_file":full_wav.name, "wav_sha256":file_sha(full_wav),
        "mp3_file":mp3.name,"mp3_sha256":file_sha(mp3),
        "all_45_cinematic_video_shots_rendered":False,
        "accurate_animal_lipsync_verified":False,
        "owner_cinematic_visual_approval":False,
        "paid_service_used":False,"new_public_release":False,
        "cues":cue_records
    }
    (OUT/"soundtrack_manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("E01_180S_SOUNDTRACK_COMPLETE_NOT_MOVIE",file_sha(mp3),flush=True)
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=["render","validate"],default="render")
    args=parser.parse_args()
    if args.mode=="validate":
        scenes,cast=validate_story()
        print("E01_AUDIO_SCRIPT_VALID",len(scenes),EP_SECONDS)
    else:
        compose()
