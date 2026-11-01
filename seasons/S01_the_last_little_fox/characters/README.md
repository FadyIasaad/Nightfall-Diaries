# Character asset lock

Before publishing, generate original character reference sheets, approve front/side/three-quarter PNGs at the paths specified in `character_registry.json`, generate audition WAVs using the assigned Kokoro voice and speed, approve them, and back up these assets outside a temporary GitHub runner. Update `reference_status` and `voice_status` to `APPROVED` **only after files are on disk**. Scenes must reference only stable character IDs. Do not make up missing images or voices.
