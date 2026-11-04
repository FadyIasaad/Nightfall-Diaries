"""Enforce the original character reference bytes and neural voice settings.

Locked inputs reduce drift but cannot certify every generated video frame.
"""
import hashlib
import json
from .restore import ROOT, SERIES

def sha256(path):
    digest=hashlib.sha256()
    with open(path,"rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()

def locked_cast(series,root=ROOT):
    if series not in dict(SERIES):
        raise ValueError("Unapproved series")
    folder=root/"seasons"/series/"characters"
    registry=json.loads((folder/"character_registry.json").read_text(encoding="utf-8"))
    image_locks=json.loads((folder/"cloud_reference_locks.json").read_text(encoding="utf-8"))
    all_voices=json.loads((root/"studio"/"voice_profile_locks.json").read_text(encoding="utf-8"))
    voice_locks=all_voices.get(series)
    if not isinstance(voice_locks,dict):
        raise ValueError("Missing locked voice manifest")
    cast={}
    for actor in registry["characters"]:
        identity=actor["id"]
        if identity in cast:
            raise ValueError("Duplicate cast identity")
        image=folder/identity/"cloud_reference.png"
        if not image.is_file() or sha256(image)!=image_locks.get(identity):
            raise ValueError("CHARACTER_REFERENCE_DRIFT: "+identity)
        voice=actor.get("voice") or {}
        profile={key:voice.get(key) for key in ("engine","voice_id","lang","speed")}
        if not profile["voice_id"] or profile!=voice_locks.get(identity):
            raise ValueError("VOICE_PROFILE_DRIFT: "+identity)
        if profile["engine"]!="kokoro":
            raise ValueError("Unapproved TTS engine")
        cast[identity]=actor
    if set(cast)!=set(image_locks) or set(cast)!=set(voice_locks):
        raise ValueError("Incomplete cast lock manifests")
    return cast
