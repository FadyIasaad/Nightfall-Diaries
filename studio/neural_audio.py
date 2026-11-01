"""Offline open-source neural voice generation, not espeak robotic speech."""
from pathlib import Path

def render_kokoro(text, character, output_path):
    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except ImportError as exc:
        raise RuntimeError("Kokoro voice dependencies unavailable; refusing robotic fallback.") from exc
    voice = character.get("voice") or {}
    voice_id = voice.get("voice_id")
    if not voice_id:
        raise ValueError(f"No locked neural voice for {character.get('id')}")
    lang = "b" if voice_id.startswith("b") else "a"
    pipeline = KPipeline(lang_code=lang)
    parts = []
    for _graphemes, _phonemes, audio in pipeline(text, voice=voice_id, speed=float(voice.get("speed", 1))):
        parts.append(np.asarray(audio, dtype=np.float32))
    if not parts:
        raise RuntimeError("Neural TTS returned no audio")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output, np.concatenate(parts), 24000)
    return output
