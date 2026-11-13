# Nightfall Diaries — Telegram after every real video segment + truthful platform delivery

Updated 13 November 2026, Africa/Cairo. This is a **continuous GitHub-cloud** production process with one manually selected story title. No PC, manual MP4 upload, approval click per episode or paid notification provider required.

## Telegram notifications

The `Nightfall - One Click Story` workflow now sends, immediately after every genuinely new LTX-2.5 MP4 sub-shot is saved and hash-verified, one Arabic Telegram message:

> 🎞️ تم إنتاج جزء فيديو جديد — Nightfall Diaries
>
> القصة: The Last Little Fox | الحلقة E01
>
> 🎬 المشهد 1 من 14 — الجزء 3
>
> ✅ اللقطات المكتملة: 3 من 36
>
> ⏱️ مدة الحركة المنتجة: 15.12 من أصل 150 ثانية تقريبًا
>
> 🔄 جاري استكمال بقية اللقطات ضمن حصة المحرك المجانية.
>
> 📌 هذه لقطة مكتملة، وليست حلقة منشورة بعد.

The numbers are **examples**, not actual current progress or promised render success. The existing proof was 2/36 shots / 10.08 seconds; the next generated shot will be clip 3 if this saved checkpoint is still authoritative.

Only a **real newly produced** sub-shot triggers progress. Each media state stores the generating `GITHUB_RUN_ID`; the Telegram script will never send a false "new" alert just because the workflow restored the same cached clips during a GPU quota pause or during the 10:17 backup run. The sender uses the official free `https://api.telegram.org/bot<token>/sendMessage` HTTPS API. The message and the clip's SHA digest are recorded in `published/S01_the_last_little_fox_E01.json`, behind a remote `initiated` marker, to prevent repeated Telegram notifications.

The full-film completion message still requires 36 true moving MP4s, 14 Kokoro voice WAVs and a SHA-checked complete MP4. It then lists **every channel** with clearly different labels: ✅ verified public, ⏳ upload accepted/processing, ⚠️ blocked or upload outcome unknown, or ▫️ not attempted. Actual confirmed URLs are included only when present and independently verified. Later, a separate **all four publicly posted** Telegram success message is sent only once the official YouTube, Facebook, Instagram and TikTok APIs have each confirmed live public availability. A TikTok inbox draft or API accepted reply will never be misreported as public.

## Verification of the two secrets added by owner

The two GitHub repository Actions secrets **must** be named:
- `TELEGRAM_BOT_TOKEN`: the actual private HTTP API key provided by BotFather.
- `TELEGRAM_CHAT_ID`: the numeric private chat's `chat.id` discovered after starting the bot.

The numeric chat ID and token **must never be committed or echoed to CI logs**. Both values are resolved only from GitHub Secrets at runtime. The test on this PR's merge is triggered only if the squash commit's subject contains `[telegram-connection-test-20261113]` and sends ONE harmless message to the owner:

> ✅ تم ربط إشعارات Nightfall Diaries على Telegram بنجاح!
>
> 🎞️ هيوصلك إشعار مع كل لقطة فيديو حقيقية جديدة، وتقرير عند اكتمال الحلقة والرفع على المنصات الأربع.
>
> ℹ️ دي رسالة اختبار اتصال فقط؛ الحلقة لسه ما اكتملتش.

This does **not** run an AI video render, leak secrets, post to public channels, or falsely claim film completion. If the test fails, check that the real token/ID were saved and that the owner has started the newly created @NightfallDiariesNotifyBot. GitHub Actions test run may say OK but that only proves delivery to Telegram API, not public social publishing.

A separate manual dispatch exists solely to retest Bot API connectivity if needed. Future regular `push` commits do not automatically send duplicate connection tests.

## Remaining production constraints

- The original E01 script, original cast references, locked Kokoro voices and real SHA-checked cumulative footage are preserved. The free HF account can generate at most one extra shot per Cairo day when quota permits; its 10:00/10:17 GitHub quota checks are **rendering retries, not publication times**.
- The user already preauthorized **automatic posting when a real film is complete**, stored in `pilot/owner_release_intent.json`. This eliminates individual approval clicks but does not override unverified film, lip sync or platform API gates in immutable `studio/production_settings.json`.
- Not all four official platform posting credentials/scopes have been verified. Do not promise public URLs until each account verifies a real post. TikTok and Meta may impose additional app review requirements.
- GitHub scheduled triggers, free GPU quota, and Telegram uptime are external services; automatic progress notifications occur after genuinely successful new clips rather than on a fixed clock.

Reference: <https://core.telegram.org/bots/api#sendmessage>.
