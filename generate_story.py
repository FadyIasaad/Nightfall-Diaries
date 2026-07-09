import json
import os
import re
import time
from typing import Any, Dict, List

import google.generativeai as genai

from config import (
    CHANNEL_NAME,
    CINEMATIC_VISUAL_STYLE,
    DEFAULT_NARRATOR_STYLE,
    VIDEO_TYPES,
    ENABLE_STORY_CHUNKING,
    STORY_CHUNK_MIN_MINUTES,
    GEMINI_MODEL_FALLBACKS,
    STORY_BACKUP_DIR,
)
from nd_common import (
    append_row,
    find_column,
    find_optional_column,
    get_all_values,
    get_cell,
    get_sheets_client,
    get_worksheet,
    get_logs_worksheet,
    log,
    open_spreadsheet,
    require_env,
    run_with_retry,
    update_cell,
    update_optional,
    utc_now,
)

CONTENT_SHEET_NAME = "Content"
LOGS_SHEET_NAME = "Logs"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

VALID_EMOTIONS = {"dread", "tension", "eerie", "calm", "fear", "relief", "mystery", "anger", "satisfaction"}

HOOK_BEATS = [
    "cold open with one disturbing line, no context yet",
    "fast scene-setting: where, who, what already feels wrong",
    "the detail that confirms something is deeply wrong",
    "the moment it becomes undeniable",
    "the choice or the discovery",
    "final gut-punch line, no comforting resolution",
]

HORROR_BEATS = [
    "cold open with an unanswered, unsettling question",
    "ordinary setting established, something subtly off",
    "a first small wrongness, dismissed as nothing",
    "routine continues but unease quietly grows",
    "a detail noticed that should not exist",
    "an attempt to explain it away rationally",
    "the rational explanation quietly fails",
    "isolation deepens: night, an empty space, no one to call",
    "a sound, motion, or presence is noticed for the first time",
    "checking and finding nothing, which is somehow worse",
    "a memory or piece of backstory hints at why this is happening",
    "the wrongness becomes impossible to dismiss",
    "a false moment of safety",
    "the false safety breaks",
    "direct confrontation or pursuit begins",
    "a choice between fleeing and understanding",
    "a piece of the truth is revealed, raising more questions than it answers",
    "the danger becomes personal and close",
    "a costly decision made under pressure",
    "the full nature of the threat is revealed",
    "a desperate struggle or escape attempt",
    "a moment of near-loss",
    "the cost of surviving: something is taken or permanently changed",
    "a quiet aftermath that does not feel fully resolved",
    "a final unsettling detail, planted for the ending",
    "closing line that lingers, ambiguous rather than comforting",
]

CONFESSION_BEATS = [
    "cold open: the narrator states plainly what was done, no context yet",
    "establish the relationship and how it looked from the outside",
    "the first small sign something was wrong, dismissed at the time",
    "life continues normally despite a quiet, growing doubt",
    "a discovery or confirmation of the betrayal",
    "the narrator's immediate gut-level reaction",
    "the narrator deliberately decides not to react right away",
    "quietly gathering information or proof, unnoticed",
    "a moment of forced public normalcy while privately knowing the truth",
    "a second betrayal or complication is uncovered",
    "the narrator's plan begins to take shape",
    "a test of resolve: almost confronting, holding back",
    "someone else's selfish or oblivious behavior raises the stakes",
    "the narrator prepares the move that will change everything",
    "a moment of real doubt or guilt about what is about to happen",
    "the narrator commits anyway",
    "the confrontation or reveal begins",
    "the other party's reaction: denial, anger, or collapse",
    "consequences ripple outward to everyone else involved",
    "a twist the listener did not see coming",
    "the narrator's own cost for what they did",
    "a quiet moment of clarity, or regret, or both",
    "how things stand now, well after the fact",
    "final line: matter-of-fact, no moral lecture, just the truth",
]


def clean_json_response(text: str) -> str:
    text = (text or "").strip()
    if not text:
        raise ValueError("Gemini returned empty text")
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"Could not find JSON object in Gemini response: {text[:500]}")
    return text[start : end + 1]


def _balance_close(s: str) -> str:
    """Best-effort repair for a truncated JSON string: drop a dangling trailing
    comma, close an unterminated string, and append the closing brackets needed
    to balance any still-open objects/arrays. String contents are respected so
    braces inside text don't confuse the counter."""
    stack = []
    in_str = False
    esc = False
    for ch in s:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            stack.append("}")
        elif ch == "[":
            stack.append("]")
        elif ch in "}]":
            if stack:
                stack.pop()
    t = s.rstrip()
    if in_str:
        t += '"'          # close a string that was cut off mid-value
    t = t.rstrip()
    if t.endswith(","):
        t = t[:-1].rstrip()
    return t + "".join(reversed(stack))


def parse_model_json(raw: str) -> Dict[str, Any]:
    """Parse the model's JSON. With JSON mode the output is normally already
    valid; if a long generation still gets truncated, repair it by balance-closing
    and, if needed, trimming back to the last complete top-level object boundary
    so a partial response degrades gracefully instead of hard-failing the run."""
    cleaned = clean_json_response(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # 1) Try to simply balance-close the whole thing.
    try:
        return json.loads(_balance_close(cleaned))
    except json.JSONDecodeError:
        pass
    # 2) Trim back through each '}' boundary (outside strings) and retry.
    positions, in_str, esc = [], False, False
    for i, ch in enumerate(cleaned):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "}":
            positions.append(i)
    for i in reversed(positions):
        try:
            return json.loads(_balance_close(cleaned[: i + 1]))
        except json.JSONDecodeError:
            continue
    # Nothing parsed — surface a clear, retryable error.
    raise ValueError("Could not parse or repair JSON from model response")


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text or ""))


def clamp_int(value, default, low, high):
    try:
        parsed = int(float(str(value).strip()))
    except Exception:
        parsed = default
    return max(low, min(high, parsed))


def normalize_type(raw: str) -> str:
    value = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "": "horror_story",
        "horror": "horror_story",
        "scary": "horror_story",
        "confession": "confession_story",
        "revenge": "confession_story",
        "betrayal": "confession_story",
        "reddit": "confession_story",
        "shorts": "short",
    }
    value = aliases.get(value, value)
    return value if value in VIDEO_TYPES else "horror_story"


def build_story_context(characters: str, narrator_pov: str, setting: str) -> str:
    cast = (characters or "").strip() or "the people involved in this story"
    pov = (narrator_pov or "").strip() or DEFAULT_NARRATOR_STYLE
    place = (setting or "").strip() or "an ordinary, true-to-life modern setting"
    return f"Cast: {cast}. Setting: {place}. Narrator: {pov}."


def emotional_score(data: Dict[str, Any]) -> int:
    script = " ".join(scene.get("narration_en", "") for scene in data.get("scenes", []))
    lower = script.lower()
    signals = [
        "alone", "afraid", "silence", "quiet", "still", "trembled", "whispered", "heart",
        "shadow", "never", "warm", "cold", "promise", "remembered", "waited", "watched",
        "knew", "lied", "found out", "proof", "truth", "finally", "every night", "again",
    ]
    score = sum(1 for s in signals if s in lower)
    if data.get("emotional_arc"):
        score += 3
    if len(data.get("scenes", [])) >= 20:
        score += 4
    if word_count(script) >= 1500:
        score += 4
    return score


def build_prompt(topic: str, characters: str, theme: str, video_type: str, target_minutes: int, scene_count: int, story_context: str, audience: str, forced_title: str = "", chapters: int = 1, split_parts: int = 1) -> str:
    if video_type == "short":
        beats = HOOK_BEATS
        target_words = "110 to 170"
        instruction = (
            "Create a sharp, unsettling YouTube Short hook story of about 50-70 SECONDS. It must work as a "
            "single complete moment, not a trailer for a longer story: a fast, real-feeling account with an "
            "immediate hook and a final line that lands hard. CRITICAL LENGTH RULE: the ENTIRE narration, "
            "across every scene and every shot combined, must total only 110-160 English words. Each shot's "
            "narration_en is exactly ONE short spoken sentence of about 6-12 words. Never write paragraphs "
            "in a short. Each scene's narration_en must contain exactly 4 short sentences "
            "(one per shot), so the whole short has 12 spoken sentences total."
        )
    elif video_type == "confession_story":
        beats = CONFESSION_BEATS
        min_words = max(1800, target_minutes * 115)
        max_words = max(2400, target_minutes * 160)
        target_words = f"{min_words} to {max_words}"
        instruction = (
            "Create a long-form, real-feeling first-person confession story about betrayal, deception, "
            "or quiet revenge, in the voice of someone telling you exactly what happened. Calm, exact, "
            "and emotionally controlled, not melodramatic. No moral lecture at the end."
        )
    else:
        beats = HORROR_BEATS
        min_words = max(1800, target_minutes * 115)
        max_words = max(2400, target_minutes * 160)
        target_words = f"{min_words} to {max_words}"
        instruction = (
            "Create a long-form, slow-burn psychological horror story for a general adult audience. "
            "It should feel like a calm, real-feeling late-night account, not a jump-scare video and "
            "not an over-explained plot. Dread builds through small details, not gore — but it must "
            "genuinely frighten: the threat gets closer and more personal in every act, and the ending "
            "reveals something that quietly recontextualizes the whole story."
        )

    if video_type == "short":
        depth_rules = ""
    else:
        depth_rules = """
- LENGTH IS MANDATORY: every scene's narration_en must be 80-130 words (5-8 full spoken sentences).
  Never write a scene with only one or two sentences. If a scene feels thin, slow down and add
  sensory detail, interior thought, and small physical actions instead of skipping ahead.
- ESCALATION: the tension must be stronger in every act. By the midpoint the threat is undeniable;
  by the final quarter it is personal and unavoidable. Include at least three distinct, memorable
  set-piece moments the listener could retell afterwards.
- COMPLETENESS: the story must finish its arc. The central question raised in the opening scenes is
  answered (even darkly), the confrontation actually happens on-page, and consequences land. Never
  end on an unexplained shrug or an arbitrary cutoff.
- MEANING: the story is ABOUT something — guilt, grief, denial, trust, obsession, the cost of
  silence. Weave that theme through the narrator's choices and let the final line land on it, so a
  listener could say in one sentence what the story meant."""

    beat_text = "\n".join(f"{i+1}. {beat}" for i, beat in enumerate(beats[:scene_count])) if video_type != "short" else "\n".join(f"{i+1}. {beat}" for i, beat in enumerate(beats))
    title_rule = (
        "a punchy, curiosity-driven title under 70 characters that makes someone need to click it; no ALL CAPS, no clickbait spam"
        if video_type == "short"
        else "a curiosity-driven title under 95 characters that opens a question in the viewer's mind; intriguing but not clickbait-spam"
    )
    if forced_title:
        title_rule = f'that is EXACTLY this text, character for character, unchanged: "{forced_title}"'

    # Multi-part / chapter rules (both default to 1 = a normal single video).
    extra_rules = ""
    if chapters > 1:
        extra_rules += (
            f"\n- PARTS: structure the story into exactly {chapters} clearly labeled parts inside this ONE video. "
            f"Split the {scene_count} scenes as evenly as possible across the parts. The FIRST scene of each part "
            f"must begin its narration_en with 'Part N.' (e.g. 'Part 2.'). Every part except the last must end on "
            f"a strong mini-cliffhanger; the last part resolves the story."
        )
    if split_parts > 1:
        block = max(1, scene_count // split_parts)
        extra_rules += (
            f"\n- SPLIT RELEASE: this single continuous story will be published as {split_parts} separate videos, "
            f"in order. Make the act boundaries fall cleanly every {block} scenes: each block of {block} scenes "
            f"must end on a strong cliffhanger (except the final block, which resolves the story), and the first "
            f"scene of each block must re-hook a brand-new viewer in its opening line without a long recap."
        )
        if video_type == "short":
            extra_rules += (
                f"\n- LENGTH OVERRIDE FOR SPLIT SHORTS: total narration across ALL scenes is "
                f"{110 * split_parts}-{160 * split_parts} words, and each block of 3 scenes must total only "
                f"110-160 words so each published short stays 50-70 seconds."
            )

    return f"""
You are the showrunner, novelist, and voice director for the YouTube channel Nightfall Diaries.
Positioning: real-feeling late-night stories for adults — confessions, betrayal/revenge accounts, and
quiet psychological horror — narrated slowly over dark visuals, meant to watch, unwind, or fall asleep to.

Task: {instruction}
Topic / premise: {topic}
Characters involved: {characters}
Core theme / throughline: {theme}
Audience: {audience or 'general adult audience'}
{story_context}
Target duration: about {target_minutes} minutes
Target narration length: {target_words} English words
Exact scene count: {scene_count}

Hard quality rules:
- This must read as a real, plausible first-person or close-third account, not a fairy tale and not a fable.
- No real named public figures, no real identifiable private individuals, no real specific addresses or businesses.
- Restrained, not graphic: build dread or tension through detail, pacing, and implication. No gore, no explicit
  violence, no sexual content, no step-by-step instructions for harming anyone or anything. This must stay
  comfortably general-audience and monetization-safe.
- No moral lecture at the end. Let the story land on its own.
- The story must have ONE clear throughline from hook to payoff: a single situation that escalates and then
  resolves with a final line that recontextualizes what came before. It must actually tell a complete story,
  never a set of disconnected, repetitive vignettes.
- CONTINUITY IS MANDATORY: in scene 1, establish the narrator's first name, the names of the other
  characters, and ONE specific setting. Reuse exactly those names and that setting in every later scene.
  Each scene must continue directly from where the previous scene ended — one continuous chain of events in
  chronological order. Never restart the story, never jump to an unrelated event or new characters, and
  never contradict an earlier detail. Repeat the names often enough that the listener never loses track.
- Every image_prompt must mention the same setting and time of day established in scene 1, so every visual
  clearly belongs to the same story.
- English narration only.
- Every scene needs a distinct location/action/emotional beat so the video never repeats the same visual.
  The first scene must hook within 2 seconds.
- Use cinematic sensory detail: rain on glass, a porch light, a hallway, a phone screen glow, footsteps, silence.
- Every scene must include exactly 4 visually different shots. Each shot needs its own narration_en and image_prompt.
- Visual identity: dark cinematic stills, moody lighting, restrained and suggestive rather than graphic, faces
  obscured or not shown, atmosphere and objects carry the story rather than detailed recurring character portraits.
- Every image_prompt must describe camera framing, lighting, location, and the exact action/emotion of that shot.
  Generic prompts are forbidden.
- Narration must sound like a real person speaking slowly and carefully, not an essay. Short sentences. Real pauses.
- Each scene's "emotion" must be exactly one of: dread, tension, eerie, calm, fear, relief, mystery, anger, satisfaction.

{depth_rules}
{extra_rules}

Scene beats:
{beat_text}

Return valid JSON only, exactly in this shape:
{{
  "title": "YouTube title {title_rule}",
  "thumbnail_text": "a 2-5 word ALL-CAPS emotional hook for the thumbnail, punchier than the title, e.g. SHE KNEW ALL ALONG",
  "description": "A 2-3 sentence YouTube description that hooks the viewer and teases the premise without spoiling the ending, for a general adult audience. End it with a final line of 4-6 relevant lowercase hashtags, e.g. #nightfalldiaries #scarystories #truestory #horror #creepy",
  "audience": "general audience",
  "video_type": "{video_type}",
  "target_minutes": {target_minutes},
  "emotional_arc": "one sentence describing the feeling journey",
  "theme": "one sentence: the deeper idea this story is about (guilt, grief, trust, obsession, ...)",
  "scenes": [
    {{
      "scene_number": 1,
      "beat": "narrative purpose of this scene",
      "emotion": "one of: dread, tension, eerie, calm, fear, relief, mystery, anger, satisfaction",
      "voice_style": "specific direction for narrator performance",
      "pause_after": 0.45,
      "camera_motion": "one of: slow_zoom_in, slow_zoom_out, gentle_pan_left, gentle_pan_right, tiny_handheld, still_soft",
      "narration_en": "full spoken English narration for the scene",
      "subtitle_en": "short English subtitle only",
      "image_prompt": "main scene visual prompt",
      "shots": [
        {{
          "shot_number": 1,
          "emotion": "one of: dread, tension, eerie, calm, fear, relief, mystery, anger, satisfaction",
          "narration_en": "one short sentence for this exact moment",
          "subtitle_en": "short English subtitle only",
          "image_prompt": "vertical 9:16 dark cinematic still for this exact moment, no text",
          "camera_motion": "slow_zoom_in"
        }},
        {{
          "shot_number": 2,
          "emotion": "one of: dread, tension, eerie, calm, fear, relief, mystery, anger, satisfaction",
          "narration_en": "next short sentence for a new visual moment",
          "subtitle_en": "short English subtitle only",
          "image_prompt": "different visual composition for this moment, no text",
          "camera_motion": "gentle_pan_left"
        }},
        {{
          "shot_number": 3,
          "emotion": "one of: dread, tension, eerie, calm, fear, relief, mystery, anger, satisfaction",
          "narration_en": "third short sentence for a close, intimate moment",
          "subtitle_en": "short English subtitle only",
          "image_prompt": "different close, intimate framing for this moment, no text",
          "camera_motion": "tiny_handheld"
        }},
        {{
          "shot_number": 4,
          "emotion": "one of: dread, tension, eerie, calm, fear, relief, mystery, anger, satisfaction",
          "narration_en": "final short sentence for this scene's consequence",
          "subtitle_en": "short English subtitle only",
          "image_prompt": "final consequence frame with cinematic lighting, no text",
          "camera_motion": "slow_zoom_out"
        }}
      ]
    }}
  ]
}}
"""


def split_into_shots(narration: str, image_prompt: str, emotion: str, story_context: str, scene_index: int) -> List[Dict[str, Any]]:
    parts = [x.strip() for x in re.split(r"(?<=[.!?])\s+", narration or "") if x.strip()]
    if len(parts) < 3:
        parts = [
            narration.strip() or "The room was quiet in a way that felt deliberate.",
            "For a moment, the silence felt heavier than it should have.",
            "Somewhere close, something shifted that should not have moved.",
            "Whatever it was, it was not finished yet.",
        ]
    parts = parts[:4]
    shot_styles = [
        "wide establishing shot showing the full location and atmosphere",
        "medium shot showing the exact action or choice in this moment",
        "close, intimate framing showing tension without showing a face",
        "final consequence shot showing what changed and why it matters",
    ]
    motions = ["slow_zoom_in", "gentle_pan_left", "tiny_handheld", "slow_zoom_out"]
    shots = []
    for n, sentence in enumerate(parts, start=1):
        shots.append({
            "shot_number": n,
            "emotion": emotion,
            "narration_en": sentence,
            "subtitle_en": sentence,
            "camera_motion": motions[(n - 1) % len(motions)],
            "image_prompt": (
                f"{story_context} {shot_styles[n-1]}. {image_prompt}. "
                f"Action based on this exact narration: {sentence}. "
                f"{CINEMATIC_VISUAL_STYLE}. No text, no watermark."
            ),
        })
    return shots


def normalize_shot(shot: Dict[str, Any], n: int, scene_narration: str, scene_prompt: str, emotion: str, story_context: str) -> Dict[str, Any]:
    shot_emotion = str(shot.get("emotion", emotion)).strip().lower()
    if shot_emotion not in VALID_EMOTIONS:
        shot_emotion = emotion if emotion in VALID_EMOTIONS else "calm"
    narration = str(shot.get("narration_en", "")).strip() or scene_narration
    subtitle = str(shot.get("subtitle_en", "")).strip() or narration
    prompt = str(shot.get("image_prompt", "")).strip() or scene_prompt
    if story_context and story_context[:30].lower() not in prompt.lower():
        prompt = f"{story_context} {prompt}"
    return {
        "shot_number": n,
        "emotion": shot_emotion,
        "narration_en": narration,
        "subtitle_en": subtitle,
        "image_prompt": prompt,
        "camera_motion": str(shot.get("camera_motion", ["slow_zoom_in", "gentle_pan_left", "slow_zoom_out", "gentle_pan_right", "tiny_handheld"][n % 5])).strip(),
        "pause_after": float(shot.get("pause_after", 0.28) or 0.28),
    }


def distribute_narration(narration: str, max_shots: int = 4):
    """Split a scene's narration into at most max_shots contiguous, non-overlapping
    chunks so the full narration is spoken exactly ONCE across the shots. Using the
    model's per-shot narration directly made the voice repeat and loop lines; this
    guarantees the audio matches the script with no repeats."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", (narration or "").strip()) if s.strip()]
    if not sentences:
        text = (narration or "").strip()
        return [text] if text else [""]
    n = max(1, min(max_shots, len(sentences)))
    base, extra = divmod(len(sentences), n)
    chunks, idx = [], 0
    for g in range(n):
        take = base + (1 if g < extra else 0)
        chunks.append(" ".join(sentences[idx:idx + take]))
        idx += take
    return chunks


def normalize_scene(scene: Dict[str, Any], i: int, story_context: str, video_type: str) -> Dict[str, Any]:
    narration = str(scene.get("narration_en", "")).strip()
    subtitle_en = str(scene.get("subtitle_en", "")).strip() or narration
    image_prompt = str(scene.get("image_prompt") or scene.get("visual_prompt") or scene.get("prompt") or "").strip()
    beats = HOOK_BEATS if video_type == "short" else (CONFESSION_BEATS if video_type == "confession_story" else HORROR_BEATS)
    beat_default = beats[min(i - 1, len(beats) - 1)]
    emotion = str(scene.get("emotion", "calm")).strip().lower()
    if emotion not in VALID_EMOTIONS:
        emotion = "calm"
    if not narration:
        narration = "Something about the room was wrong before anyone could say exactly what."
    if not subtitle_en:
        subtitle_en = narration
    if not image_prompt:
        image_prompt = (
            f"vertical 9:16 dark cinematic still, distinct scene {i}, emotion: {emotion}, "
            f"beat: {scene.get('beat', beat_default)}, action based on: {narration[:280]}, "
            "moody practical lighting, restrained composition, no text, no watermark"
        )
    if story_context and story_context[:30].lower() not in image_prompt.lower():
        image_prompt = f"{story_context} {image_prompt}"

    raw_shots = scene.get("shots") if isinstance(scene.get("shots"), list) else []
    if not raw_shots:
        raw_shots = split_into_shots(narration, image_prompt, emotion, story_context, i)
    # Speak the scene narration exactly once, split across the shots with no overlap
    # (fixes the voice repeating / looping lines).
    narration_chunks = distribute_narration(narration, 4)
    shots = []
    for n in range(1, len(narration_chunks) + 1):
        raw_shot = raw_shots[n - 1] if n - 1 < len(raw_shots) else {}
        ns = normalize_shot(raw_shot, n, narration, image_prompt, emotion, story_context)
        ns["narration_en"] = narration_chunks[n - 1]
        ns["subtitle_en"] = narration_chunks[n - 1]
        shots.append(ns)

    return {
        "scene_number": i,
        "beat": str(scene.get("beat", beat_default)).strip(),
        "emotion": emotion,
        "voice_style": str(scene.get("voice_style", "calm, controlled, late-night narrator, speaking slowly")).strip(),
        "pause_after": float(scene.get("pause_after", 0.45) or 0.45),
        "camera_motion": str(scene.get("camera_motion", ["slow_zoom_in", "gentle_pan_left", "slow_zoom_out", "gentle_pan_right", "still_soft"][i % 5])).strip(),
        "narration_en": narration,
        "subtitle_en": subtitle_en,
        "image_prompt": image_prompt,
        "shots": shots,
    }


def fallback_expand_scenes(data: Dict[str, Any], scene_count: int, story_context: str, video_type: str) -> Dict[str, Any]:
    scenes = data.get("scenes", []) if isinstance(data.get("scenes"), list) else []
    if not scenes:
        scenes = []
    beats = HOOK_BEATS if video_type == "short" else (CONFESSION_BEATS if video_type == "confession_story" else HORROR_BEATS)
    while len(scenes) < scene_count:
        i = len(scenes) + 1
        beat = beats[min(i - 1, len(beats) - 1)]
        scenes.append({
            "scene_number": i,
            "beat": beat,
            "emotion": ["tension", "eerie", "calm", "dread", "mystery"][i % 5],
            "voice_style": "slow, intimate, controlled, with small real pauses",
            "pause_after": 0.5,
            "camera_motion": ["slow_zoom_in", "gentle_pan_left", "slow_zoom_out", "gentle_pan_right", "still_soft"][i % 5],
            "narration_en": (
                "Nothing about it made sense yet, but something had already changed. "
                "The quiet stretched a little too long to be nothing. "
                "Whatever came next, there was no taking back what had already been noticed."
            ),
            "subtitle_en": "Something had already changed, and the quiet stretched too long to be nothing.",
            "image_prompt": f"vertical 9:16 dark cinematic still, {beat}, moody practical lighting, no text",
        })
    data["scenes"] = scenes[:scene_count]
    return data


def clamp_cell(text: str, max_chars: int = 49000) -> str:
    """
    Google Sheets rejects any single cell longer than 50,000 characters with a
    400 error. Long-form narration (an 18-minute horror story) can exceed that,
    so any plain-text field written to a cell is clamped to a safe length. The
    full narration is rebuilt per-shot from scene_prompts at video time anyway,
    so the script cell is only a human-readable reference.
    """
    s = str(text or "")
    if len(s) <= max_chars:
        return s
    return s[:max_chars - 20].rstrip() + " […truncated]"


def trim_payload_for_cell(payload: Dict[str, Any], max_chars: int = 49000) -> str:
    """
    Serialize scene_payload and shrink it until it fits Google Sheets' 50k
    char-per-cell limit. Escalates through progressively more aggressive steps,
    and ends with a guaranteed hard cap so it can NEVER return something bigger
    than the limit, no matter how large the story is.
    """
    import copy
    payload = copy.deepcopy(payload)

    def size(p):
        return len(json.dumps(p, ensure_ascii=False))

    if size(payload) <= max_chars:
        return json.dumps(payload, ensure_ascii=False)

    # Step 1: strip redundant scene-level fields already present in shots
    for scene in payload.get("scenes", []):
        scene.pop("image_prompt", None)
        scene.pop("narration_en", None)
        scene.pop("subtitle_en", None)
    if size(payload) <= max_chars:
        return json.dumps(payload, ensure_ascii=False)

    # Step 2: truncate shot image_prompts
    for scene in payload.get("scenes", []):
        for shot in scene.get("shots", []):
            if len(shot.get("image_prompt", "")) > 280:
                shot["image_prompt"] = shot["image_prompt"][:280]
    if size(payload) <= max_chars:
        return json.dumps(payload, ensure_ascii=False)

    # Step 3: truncate shot narration and drop subtitle duplicates
    for scene in payload.get("scenes", []):
        for shot in scene.get("shots", []):
            if len(shot.get("narration_en", "")) > 200:
                shot["narration_en"] = shot["narration_en"][:200]
            shot.pop("subtitle_en", None)
    if size(payload) <= max_chars:
        return json.dumps(payload, ensure_ascii=False)

    # Step 4: progressively tighten narration further until it fits (long
    # stories with many scenes can still be over the limit after step 3).
    for limit in (150, 120, 100, 80, 60):
        for scene in payload.get("scenes", []):
            for shot in scene.get("shots", []):
                n = shot.get("narration_en", "")
                if len(n) > limit:
                    shot["narration_en"] = n[:limit]
                # At the tightest levels, also drop per-shot image prompts; the
                # renderer falls back to scene/generic visuals, which is far
                # better than failing to save the story at all.
                if limit <= 100:
                    shot.pop("image_prompt", None)
        if size(payload) <= max_chars:
            return json.dumps(payload, ensure_ascii=False)

    # Step 5 (guaranteed): hard-cap the serialized JSON. We keep as many whole
    # scenes as fit, so the video still renders from valid JSON rather than a
    # broken truncated string.
    scenes = payload.get("scenes", [])
    lo, hi = 1, len(scenes)
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        trial = dict(payload)
        trial["scenes"] = scenes[:mid]
        if size(trial) <= max_chars:
            best = json.dumps(trial, ensure_ascii=False)
            lo = mid + 1
        else:
            hi = mid - 1
    if best is not None:
        return best

    # Absolute last resort: a minimal valid payload (should never be reached).
    minimal = {
        "video_type": payload.get("video_type", "horror_story"),
        "target_minutes": payload.get("target_minutes", ""),
        "scenes": scenes[:1] if scenes else [],
    }
    out = json.dumps(minimal, ensure_ascii=False)
    return out[:max_chars]


def _precall_pacing_delay():
    """
    Free-tier Gemini allows only 5 requests/minute. Pace before each model call
    so back-to-back runs don't immediately trip the per-minute quota. Set
    GEMINI_PRECALL_DELAY=0 once billing is enabled.
    """
    try:
        delay = float(os.getenv("GEMINI_PRECALL_DELAY", "13"))
    except ValueError:
        delay = 13.0
    if delay > 0:
        print(f"Pacing for free-tier quota: waiting {delay:.0f}s before the model call...")
        time.sleep(delay)


def generate_json_with_models(prompt: str, max_output_tokens: int = 32768, label: str = "model call") -> Dict[str, Any]:
    """
    Runs a single prompt against the configured model, falling back through
    GEMINI_MODEL_FALLBACKS if one model is quota-blocked or errors. Each model
    attempt still gets the full retry/backoff treatment from run_with_retry, so
    a transient 429 on the primary is waited out before we ever fall back.
    Returns parsed JSON.
    """
    genai.configure(api_key=require_env("GEMINI_API_KEY"))
    # De-duplicate while preserving order.
    seen = set()
    models = []
    for name in GEMINI_MODEL_FALLBACKS:
        if name and name not in seen:
            seen.add(name)
            models.append(name)

    last_error = None
    for model_name in models:
        model = genai.GenerativeModel(model_name)

        def call_model():
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.8,
                    "top_p": 0.93,
                    "max_output_tokens": max_output_tokens,
                    # JSON mode (structured output): constrain the model to emit
                    # syntactically valid JSON, eliminating the free-form
                    # "Expecting ',' delimiter" parse failures on long stories.
                    "response_mime_type": "application/json",
                },
            )
            return parse_model_json(response.text)

        try:
            _precall_pacing_delay()
            print(f"{label}: using model {model_name}")
            return run_with_retry(f"{label} ({model_name})", call_model, max_attempts=6)
        except Exception as exc:
            last_error = exc
            print(f"Model {model_name} failed after retries: {exc}")
            print("Falling back to the next model if one is available...")
            continue

    raise RuntimeError(f"All models failed for {label}. Last error: {last_error}")


def generate_story_package(topic: str, characters: str, theme: str, video_type="horror_story", target_minutes=18, narrator_pov="", setting="", audience="general audience", forced_title="", chapters=1, split_parts=1) -> Dict[str, Any]:
    video_type = normalize_type(video_type)
    settings = VIDEO_TYPES[video_type]
    target_minutes = clamp_int(target_minutes, int(settings.get("duration_minutes", 18)), 1, 60)
    if video_type == "short":
        scene_count = 3 * max(1, split_parts)
    else:
        # Scale scene count with duration and keep it modest: fewer, richer scenes
        # produce smaller, valid JSON (the model was emitting broken JSON at ~24
        # scenes) and less bloated videos.
        scene_count = clamp_int(round(target_minutes * 1.2), 12, 8, 24)
    story_context = build_story_context(characters, narrator_pov, setting)

    prompt = build_prompt(topic, characters, theme, video_type, target_minutes, scene_count, story_context, audience, forced_title=forced_title, chapters=chapters, split_parts=split_parts)
    # Long-form stories need generous output headroom so the JSON isn't truncated
    # mid-generation (a source of malformed JSON). Shorts are tiny.
    max_tokens = (16384 * max(1, split_parts)) if video_type == "short" else 65536
    data = generate_json_with_models(prompt, max_output_tokens=max_tokens, label="Generating story package")

    # Optional chunked deepening for long-form, off by default (free-tier safe).
    # When enabled (billing on), we ask the model to expand the middle of the
    # story in a second pass for richer, longer narration. Single model call
    # otherwise. Shorts are never chunked.
    if (
        ENABLE_STORY_CHUNKING
        and video_type != "short"
        and target_minutes >= STORY_CHUNK_MIN_MINUTES
        and isinstance(data.get("scenes"), list)
        and len(data["scenes"]) >= 4
    ):
        try:
            data = _expand_story_middle(data, topic, characters, theme, video_type, target_minutes, scene_count, story_context, audience)
        except Exception as exc:
            # Non-fatal: keep the perfectly good single-call story if expansion fails.
            print(f"Chunked expansion skipped (non-fatal): {exc}")

    if forced_title:
        data["title"] = forced_title
    if "title" not in data or not data["title"]:
        data["title"] = "A Story From Nightfall Diaries"
    if "description" not in data or not data["description"]:
        data["description"] = "A late-night story for a general adult audience. #nightfalldiaries #truestory #scarystories"
    data["audience"] = "general audience"
    data["video_type"] = video_type
    data["target_minutes"] = target_minutes
    data = fallback_expand_scenes(data, scene_count, story_context, video_type)
    data["scenes"] = [normalize_scene(scene, i, story_context, video_type) for i, scene in enumerate(data["scenes"], start=1)]
    data["script"] = " ".join(scene["narration_en"] for scene in data["scenes"])
    data["emotional_score"] = emotional_score(data)
    return data


def _expand_story_middle(data, topic, characters, theme, video_type, target_minutes, scene_count, story_context, audience):
    """
    Second-pass deepening for long-form stories (only when chunking is enabled).
    Asks the model to lengthen and enrich the existing middle scenes without
    changing the plot, then merges the richer narration back in. Uses one extra
    model call (hence free-tier-gated upstream).
    """
    existing = data.get("scenes", [])
    middle = existing[1:-1] if len(existing) >= 3 else existing
    middle_json = json.dumps({"scenes": middle}, ensure_ascii=False)
    expand_prompt = (
        f"You are deepening the MIDDLE of an existing {video_type.replace('_',' ')} for {CHANNEL_NAME}.\n"
        f"Theme: {theme}\nStory context: {story_context}\n\n"
        "Here are the current middle scenes as JSON. Rewrite ONLY their narration to be richer, "
        "slower, and more sensory, keeping the exact same events, order, and number of scenes. "
        "Do not add or remove scenes. Do not change image_prompt. Keep each scene's emotion field. "
        "Return ONLY valid JSON of the form {\"scenes\": [...]} with the same length and keys.\n\n"
        f"{middle_json}"
    )
    expanded = generate_json_with_models(expand_prompt, max_output_tokens=65536, label="Deepening story middle")
    new_middle = expanded.get("scenes", [])
    if isinstance(new_middle, list) and len(new_middle) == len(middle):
        data["scenes"] = [existing[0]] + new_middle + [existing[-1]] if len(existing) >= 3 else new_middle
        print(f"Chunked expansion merged {len(new_middle)} middle scenes.")
    else:
        print("Chunked expansion returned mismatched scenes; keeping original.")
    return data


def package_from_user_story(story_text: str, forced_title: str, video_type: str, target_minutes, chapters: int = 1, split_parts: int = 1) -> Dict[str, Any]:
    """
    The channel owner wrote the story themselves (TBT_CUSTOM_STORY). Instead of
    inventing a story, ask the model only to SEGMENT the given text into the
    standard scene/shot JSON (keeping the narration verbatim) and to add the
    production metadata: title, description, emotions, and image prompts.
    """
    video_type = normalize_type(video_type)
    wc = word_count(story_text)
    if video_type == "short":
        scene_count = 3 * max(1, split_parts)
    else:
        scene_count = clamp_int(round(wc / 110.0), 12, 3, 24)
    est_minutes = clamp_int(round(wc / 130.0), clamp_int(target_minutes, 18, 1, 60), 1, 60)
    story_context = build_story_context("", "", "")

    title_rule = (
        f'EXACTLY this text, character for character, unchanged: "{forced_title}"'
        if forced_title
        else "a curiosity-driven YouTube title under 95 characters based on the story; no ALL CAPS, no clickbait spam"
    )
    parts_rule = ""
    if chapters > 1:
        parts_rule = (
            f"\n- Split the scenes as evenly as possible into {chapters} labeled parts: the first scene of each "
            f"part must begin its narration_en with 'Part N.' (add only that label, change nothing else)."
        )
    if split_parts > 1:
        block = max(1, scene_count // split_parts)
        parts_rule += (
            f"\n- The scenes will later be published as {split_parts} separate videos, split every {block} scenes "
            f"in order. Choose scene boundaries so each block of {block} scenes ends at a natural break in the text."
        )

    prompt = f"""
You are the production editor for the YouTube channel Nightfall Diaries. The channel owner has written
this story themselves. Your job is ONLY to prepare it for production. Do NOT rewrite, improve, shorten,
extend, or censor the story: the narration must be the owner's text, split in original order.

THE OWNER'S STORY:
\"\"\"{story_text}\"\"\"

Rules:
- Split the story text into exactly {scene_count} scenes IN ORDER. Together, the scenes' narration_en must
  contain the entire story text, once, with nothing added and nothing left out (you may only fix obvious
  typos and normalize whitespace).
- Every scene needs exactly 4 shots. Distribute that scene's narration across its shots in order.
- Each scene's "emotion" must be exactly one of: dread, tension, eerie, calm, fear, relief, mystery, anger, satisfaction.
- Every image_prompt: a vertical 9:16 dark cinematic still matching that exact moment; describe camera framing,
  lighting, location, and action; faces obscured or not shown; no text, no watermark. Keep every prompt in the
  same setting the story establishes so all visuals belong to one story.{parts_rule}

Return valid JSON only, exactly in this shape:
{{
  "title": "{title_rule}",
  "thumbnail_text": "a 2-5 word ALL-CAPS emotional hook for the thumbnail, punchier than the title, e.g. SHE KNEW ALL ALONG",
  "description": "A 2-3 sentence YouTube description that hooks the viewer without spoiling the ending. End with a final line of 4-6 relevant lowercase hashtags, e.g. #nightfalldiaries #scarystories #truestory #horror #creepy",
  "audience": "general audience",
  "video_type": "{video_type}",
  "target_minutes": {est_minutes},
  "emotional_arc": "one sentence describing the feeling journey",
  "scenes": [
    {{
      "scene_number": 1,
      "beat": "narrative purpose of this scene",
      "emotion": "one of the allowed emotions",
      "voice_style": "specific direction for narrator performance",
      "pause_after": 0.45,
      "camera_motion": "one of: slow_zoom_in, slow_zoom_out, gentle_pan_left, gentle_pan_right, tiny_handheld, still_soft",
      "narration_en": "this scene's portion of the owner's story text, verbatim",
      "subtitle_en": "short English subtitle only",
      "image_prompt": "main scene visual prompt",
      "shots": [
        {{"shot_number": 1, "emotion": "...", "narration_en": "...", "subtitle_en": "...", "image_prompt": "...", "camera_motion": "slow_zoom_in"}},
        {{"shot_number": 2, "emotion": "...", "narration_en": "...", "subtitle_en": "...", "image_prompt": "...", "camera_motion": "gentle_pan_left"}},
        {{"shot_number": 3, "emotion": "...", "narration_en": "...", "subtitle_en": "...", "image_prompt": "...", "camera_motion": "tiny_handheld"}},
        {{"shot_number": 4, "emotion": "...", "narration_en": "...", "subtitle_en": "...", "image_prompt": "...", "camera_motion": "slow_zoom_out"}}
      ]
    }}
  ]
}}
"""
    data = generate_json_with_models(prompt, max_output_tokens=65536, label="Segmenting owner-written story")
    if forced_title:
        data["title"] = forced_title
    if not data.get("title"):
        data["title"] = "A Story From Nightfall Diaries"
    if not data.get("description"):
        data["description"] = "A late-night story for a general adult audience. #nightfalldiaries #truestory #scarystories"
    data["audience"] = "general audience"
    data["video_type"] = video_type
    scenes = data.get("scenes") if isinstance(data.get("scenes"), list) else []
    if not scenes:
        raise ValueError("Story segmentation returned no scenes.")
    # NOTE: no fallback_expand_scenes here on purpose — padding with generic
    # filler scenes would inject narration the owner never wrote.
    data["scenes"] = [normalize_scene(scene, i, story_context, video_type) for i, scene in enumerate(scenes, start=1)]
    data["script"] = " ".join(scene["narration_en"] for scene in data["scenes"])
    data["emotional_score"] = emotional_score(data)
    return data


def split_package_into_parts(package: Dict[str, Any], n: int) -> List[Dict[str, Any]]:
    """Split one finished story package into n sequential per-video packages
    ("Part 1/n", "Part 2/n", ...) by dividing its scenes evenly, in order."""
    scenes = package.get("scenes", [])
    n = max(1, min(int(n), len(scenes) or 1))
    if n == 1:
        return [package]
    base, extra = divmod(len(scenes), n)
    total_minutes = clamp_int(package.get("target_minutes", 18), 18, 1, 60)
    per_part_minutes = max(1, round(total_minutes / n))
    base_title = str(package.get("title", "")).strip() or "A Story From Nightfall Diaries"
    # Keep room for the " — Part N/N" suffix inside YouTube's 100-char limit.
    if len(base_title) > 84:
        base_title = base_title[:84].rstrip()
    parts, idx = [], 0
    for p in range(1, n + 1):
        take = base + (1 if p <= extra else 0)
        chunk = scenes[idx: idx + take]
        idx += take
        part = dict(package)
        part["scenes"] = [dict(scene, scene_number=j) for j, scene in enumerate(chunk, start=1)]
        part["title"] = f"{base_title} — Part {p}/{n}"
        hook = str(package.get("thumbnail_text", "") or "").strip()
        part["thumbnail_text"] = f"{hook} — PART {p}" if hook else f"PART {p} OF {n}"
        part["description"] = f"Part {p} of {n}. " + str(package.get("description", ""))
        part["script"] = " ".join(scene.get("narration_en", "") for scene in part["scenes"])
        part["target_minutes"] = per_part_minutes
        parts.append(part)
    return parts


def pick_idea_from_csv(video_type: str, existing_topics) -> Dict[str, str]:
    """
    AUTO-REFILL: when the sheet has no IDEA row left for the requested type,
    pull a fresh idea from content_ideas_by_type.csv (committed in the repo)
    so a run NEVER ends silently with nothing produced. Prefers ideas whose
    topic isn't already in the sheet; if all are used, reuses a random one
    (generation temperature makes the resulting story different anyway).
    """
    import csv
    import random
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content_ideas_by_type.csv")
    if not os.path.exists(path):
        return None
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = [r for r in csv.DictReader(fh) if (r.get("topic") or "").strip()]
    if not rows:
        return None
    matching = [r for r in rows if normalize_type(r.get("video_type", "")) == video_type] or rows
    unused = [r for r in matching if (r.get("topic") or "").strip() not in existing_topics]
    return random.choice(unused or matching)


def build_sheet_row(headers: List[str], assignments) -> List[str]:
    """Build a full sheet row (list of strings) from (column_index, value) pairs
    produced by find_column / find_optional_column (1-based, None = missing)."""
    row = [""] * len(headers)
    for col, value in assignments:
        if col:
            row[col - 1] = str(value)
    return row


def main():
    client = get_sheets_client()
    spreadsheet = open_spreadsheet(client)
    content_sheet = get_worksheet(spreadsheet, CONTENT_SHEET_NAME)
    logs_sheet = get_logs_worksheet(spreadsheet)
    values = get_all_values(content_sheet)
    if not values:
        raise ValueError("Content sheet is empty.")
    headers = values[0]
    id_col = find_column(headers, "id")
    topic_col = find_column(headers, "topic")
    characters_col = find_column(headers, "characters")
    theme_col = find_column(headers, "theme")
    script_col = find_column(headers, "script")
    title_col = find_column(headers, "title")
    description_col = find_column(headers, "description")
    status_col = find_column(headers, "status")
    created_at_col = find_column(headers, "created_at")
    scene_prompts_col = find_column(headers, "scene_prompts")
    image_status_col = find_column(headers, "image_status")
    audio_status_col = find_column(headers, "audio_status")
    youtube_status_col = find_column(headers, "youtube_status")
    youtube_video_id_col = find_column(headers, "youtube_video_id")
    video_type_col = find_optional_column(headers, "video_type")
    target_minutes_col = find_optional_column(headers, "target_minutes")
    narrator_pov_col = find_optional_column(headers, "narrator_pov")
    setting_col = find_optional_column(headers, "setting")
    audience_col = find_optional_column(headers, "audience")
    made_for_kids_col = find_optional_column(headers, "made_for_kids")
    error_message_col = find_optional_column(headers, "error_message")

    requested_video_type = normalize_type(os.getenv("TBT_VIDEO_TYPE", "") or os.getenv("VIDEO_TYPE", "")) if (os.getenv("TBT_VIDEO_TYPE") or os.getenv("VIDEO_TYPE")) else ""

    # Manual-run extras (all optional, set by the workflow's Run-workflow inputs):
    #   TBT_CUSTOM_TITLE - use exactly this title; AI writes the story from it
    #   TBT_CUSTOM_STORY - the owner wrote the story; use it as the narration
    #   TBT_PARTS / TBT_PARTS_MODE - split into N separate videos, or N labeled
    #                                chapters inside one video
    custom_title = os.getenv("TBT_CUSTOM_TITLE", "").strip()
    custom_story = os.getenv("TBT_CUSTOM_STORY", "").strip()
    parts = clamp_int(os.getenv("TBT_PARTS", "1") or "1", 1, 1, 10)
    parts_mode = (os.getenv("TBT_PARTS_MODE", "") or "separate_videos").strip().lower()
    chapters = parts if (parts > 1 and parts_mode == "chapters") else 1
    split_parts = parts if (parts > 1 and parts_mode != "chapters") else 1
    custom_mode = bool(custom_title or custom_story)

    if custom_mode:
        # The run brings its own title and/or story, so no sheet IDEA row is
        # consumed; new row(s) are appended to the sheet instead.
        target_row_number = None
        target_row = None
        video_id = "CUSTOM-" + re.sub(r"\D", "", utc_now())
        video_type = requested_video_type or "horror_story"
        topic = custom_title or "a story written by the channel owner"
        characters = ""
        theme = ""
        narrator_pov = ""
        setting_value = ""
        audience = "general audience"
        target_minutes = os.getenv("TBT_TARGET_MINUTES", "").strip() or VIDEO_TYPES[video_type].get("duration_minutes", 18)
        print(f"Custom mode: title={'yes' if custom_title else 'no'} story={'yes' if custom_story else 'no'} parts={parts} mode={parts_mode}")
    else:
        target_row_number = None
        target_row = None
        for index, row in enumerate(values[1:], start=2):
            row_status = get_cell(row, status_col).upper()
            row_type = normalize_type(get_cell(row, video_type_col))
            if row_status == "IDEA" and (not requested_video_type or row_type == requested_video_type):
                target_row_number = index
                target_row = row
                break
        if target_row_number is None:
            # AUTO-REFILL: the sheet ran out of IDEA rows for this type. This used
            # to print "No IDEA row found" and exit 0, which made the workflow
            # look green while uploading NOTHING. Now a fresh idea is pulled from
            # content_ideas_by_type.csv and the run continues; results are
            # appended to the sheet as a new row.
            video_type = requested_video_type or "horror_story"
            existing_topics = {get_cell(row, topic_col) for row in values[1:]}
            idea = pick_idea_from_csv(video_type, existing_topics)
            if idea is None:
                msg = f"No IDEA row for video_type={video_type} and content_ideas_by_type.csv is missing/empty - nothing to produce."
                log(logs_sheet, "", "GENERATE_STORY_ERROR", msg)
                raise RuntimeError(msg)  # fail RED so the run is never silently empty
            video_id = "AUTO-" + re.sub(r"\D", "", utc_now())
            topic = (idea.get("topic") or "").strip()
            characters = (idea.get("characters") or "").strip()
            theme = (idea.get("theme") or "").strip()
            narrator_pov = (idea.get("narrator_pov") or "").strip()
            setting_value = (idea.get("setting") or "").strip()
            audience = (idea.get("audience") or "").strip() or "general audience"
            target_minutes = os.getenv("TBT_TARGET_MINUTES", "").strip() or (idea.get("target_minutes") or "").strip() or VIDEO_TYPES[video_type].get("duration_minutes", 18)
            log(logs_sheet, video_id, "GENERATE_STORY", f"No IDEA row for {video_type}; auto-seeded from CSV: {topic[:120]}")
            print(f"No IDEA row for {video_type}; auto-seeded idea from CSV: {topic[:120]}")
        else:
            video_id = get_cell(target_row, id_col)
            video_type = requested_video_type or normalize_type(get_cell(target_row, video_type_col))
            target_minutes = os.getenv("TBT_TARGET_MINUTES", "").strip() or get_cell(target_row, target_minutes_col) or VIDEO_TYPES[video_type].get("duration_minutes", 18)
            topic = get_cell(target_row, topic_col)
            characters = get_cell(target_row, characters_col)
            theme = get_cell(target_row, theme_col)
            narrator_pov = get_cell(target_row, narrator_pov_col)
            setting_value = get_cell(target_row, setting_col)
            audience = get_cell(target_row, audience_col) or "general audience"
    try:
        # For separate part videos, generate ONE continuous story long enough
        # for all parts, then split it. target_minutes means minutes PER video.
        gen_minutes = clamp_int(target_minutes, 18, 1, 60)
        if split_parts > 1 and video_type != "short":
            gen_minutes = min(60, gen_minutes * split_parts)

        if custom_story:
            package = package_from_user_story(
                custom_story, custom_title, video_type, gen_minutes,
                chapters=chapters, split_parts=split_parts,
            )
        else:
            package = generate_story_package(
                topic,
                characters,
                theme,
                video_type=video_type,
                target_minutes=gen_minutes,
                narrator_pov=narrator_pov,
                setting=setting_value,
                audience=audience,
                forced_title=custom_title,
                chapters=chapters,
                split_parts=split_parts,
            )

        packages = split_package_into_parts(package, split_parts)

        for part_number, pkg in enumerate(packages, start=1):
            pkg_id = video_id if len(packages) == 1 or (part_number == 1 and target_row_number is not None) else f"{video_id}-p{part_number}"
            scene_payload = {
                "emotional_arc": pkg.get("emotional_arc", ""),
                "emotional_score": pkg.get("emotional_score", ""),
                "audience": pkg.get("audience", "general audience"),
                "video_type": pkg.get("video_type", video_type),
                "target_minutes": pkg.get("target_minutes", target_minutes),
                "thumbnail_text": str(pkg.get("thumbnail_text", "") or "").strip(),
                "scenes": pkg["scenes"],
            }

            # Save a local backup of the story BEFORE touching the sheet, so the
            # generated work is never lost even if a sheet write fails. Picked up
            # by the workflow's upload-artifact step. Non-fatal if it can't be written.
            try:
                STORY_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                safe_id = re.sub(r"[^A-Za-z0-9_-]", "_", str(pkg_id).strip() or "story")
                backup_path = STORY_BACKUP_DIR / f"story_{safe_id}.json"
                with open(backup_path, "w", encoding="utf-8") as fh:
                    json.dump(
                        {
                            "id": pkg_id,
                            "title": pkg.get("title", ""),
                            "description": pkg.get("description", ""),
                            "script": pkg.get("script", ""),
                            "video_type": video_type,
                            "target_minutes": pkg.get("target_minutes", target_minutes),
                            "scene_payload": scene_payload,
                        },
                        fh,
                        ensure_ascii=False,
                        indent=2,
                    )
                print(f"Story backup saved: {backup_path}")
            except Exception as backup_exc:
                print(f"Story backup skipped (non-fatal): {backup_exc}")

            if part_number == 1 and target_row_number is not None:
                # Normal path: fill in the sheet's IDEA row.
                update_cell(content_sheet, target_row_number, title_col, pkg["title"])
                update_cell(content_sheet, target_row_number, script_col, clamp_cell(pkg["script"]))
                update_cell(content_sheet, target_row_number, description_col, clamp_cell(pkg["description"]))
                update_cell(content_sheet, target_row_number, scene_prompts_col, trim_payload_for_cell(scene_payload))
                update_cell(content_sheet, target_row_number, status_col, "GENERATED")
                update_cell(content_sheet, target_row_number, created_at_col, utc_now())
                update_cell(content_sheet, target_row_number, image_status_col, "PENDING")
                update_cell(content_sheet, target_row_number, audio_status_col, "PENDING")
                update_cell(content_sheet, target_row_number, youtube_status_col, "")
                update_cell(content_sheet, target_row_number, youtube_video_id_col, "")
                update_optional(content_sheet, target_row_number, video_type_col, video_type)
                update_optional(content_sheet, target_row_number, target_minutes_col, str(pkg.get("target_minutes", target_minutes)))
                update_optional(content_sheet, target_row_number, audience_col, "general audience")
                update_optional(content_sheet, target_row_number, made_for_kids_col, "FALSE")
                update_optional(content_sheet, target_row_number, error_message_col, "")
            else:
                # Custom-mode row, or extra part rows: append a ready GENERATED row.
                new_row = build_sheet_row(headers, [
                    (id_col, pkg_id),
                    (topic_col, topic),
                    (characters_col, characters),
                    (theme_col, theme),
                    (title_col, pkg["title"]),
                    (script_col, clamp_cell(pkg["script"])),
                    (description_col, clamp_cell(pkg["description"])),
                    (scene_prompts_col, trim_payload_for_cell(scene_payload)),
                    (status_col, "GENERATED"),
                    (created_at_col, utc_now()),
                    (image_status_col, "PENDING"),
                    (audio_status_col, "PENDING"),
                    (youtube_status_col, ""),
                    (youtube_video_id_col, ""),
                    (video_type_col, video_type),
                    (target_minutes_col, str(pkg.get("target_minutes", target_minutes))),
                    (audience_col, "general audience"),
                    (made_for_kids_col, "FALSE"),
                    (error_message_col, ""),
                ])
                append_row(content_sheet, new_row)

            log(logs_sheet, pkg_id, "GENERATE_STORY", f"Generated {video_type} story: {pkg['title']} | part={part_number}/{len(packages)} | scenes={len(pkg['scenes'])} | words={word_count(pkg['script'])} | score={pkg['emotional_score']}")
            print(f"Generated story: {pkg['title']} (part {part_number}/{len(packages)})")
            print(f"Scenes: {len(pkg['scenes'])} | Words: {word_count(pkg['script'])} | Type: {video_type}")
    except Exception as exc:
        if target_row_number is not None:
            update_optional(content_sheet, target_row_number, error_message_col, str(exc)[:1500])
        log(logs_sheet, video_id, "GENERATE_STORY_ERROR", str(exc))
        raise


if __name__ == "__main__":
    main()
# EOF
