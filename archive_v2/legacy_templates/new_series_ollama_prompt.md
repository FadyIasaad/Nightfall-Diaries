# Automated NEW-SERIES writer prompt (for local model)

This prompt is used ONLY AFTER S01 + S02 have BOTH completed, and after every later season finale. Input must be fresh, timestamped, verified past-seven-day trend candidates and their editorial scores.

Create a NEW, copyright-safe and original animated short-drama series from the highest-scoring eligible TREND_TOPIC. Do not recount actual news as invented fact, reuse private people, or exploit trauma. Do not copy famous characters or stories. Make it an original fictional universe.

REQUIRED OUTPUT:
- 1 unique new title, genre, universe setting and complete 10–12 episode story arc.
- At least 10 individually distinct episodes: title, hook, 3–6 scene outline, twist, end hook, connection to next episode, finale resolution.
- NEW characters with IDs unique across all prior seasons and completely new visual designs and reference prompts; protagonist and main cast unique to this season.
- Distinct new voice *profiles* and audition lines for each character. Prefer unused Kokoro IDs and maintain one voice per character for the whole series. Never change an approved voice mid-season. If unique suitable voices cannot be obtained, require production review rather than pretending uniqueness.
- A locked series bible, identity and voice registries, script templates, reference sheet checklist, first-three-episodes production buffer, editorial/safety/quality gates.
- Core plot must resolve in finale. Output a valid season manifest and episode registry only after validation.

TREND_TOPIC: {{verified_topic}}
TREND_SOURCE_AND_DATE: {{source_and_timestamp}}
REASON_AND_SCORE: {{score_and_selection_reason}}
EXISTING_REGISTRY: {{all_prior_series_names_characters_and_voice_ids}}

Do not invent trend stats, pretend voice WAVs or reference PNGs exist, or publish anything during writing.
