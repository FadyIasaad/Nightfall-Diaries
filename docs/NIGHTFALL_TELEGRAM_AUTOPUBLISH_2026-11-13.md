# Nightfall Diaries — Automatic publishing without approval clicks + Telegram alerts

**Owner instruction (13 Nov 2026):** do not ask for a manual approval each time an episode is ready. Publish the complete original episode immediately to YouTube, Facebook Page, Instagram and TikTok, and send a Telegram message only describing what has actually finished or been made public. Telegram is the chosen free alternative to WhatsApp Business Cloud API.

## Implementation in the ONE-click GitHub workflow

After 36/36 unique *real* motion shots and 14 Kokoro spoken WAVs have been assembled into the original 120–180-second portrait H.264/AAC MP4:
1. The **same Actions run** calls the existing event-driven four-platform publisher. There is **no publishing timetable and no extra approval button**. The owner has pre-authorized automatic posting using `owner_auto_public_release_authorized=true` and `owner_approval_per_episode_required=false` in `studio/production_settings.json`.
2. If a platform's credentials or identity verification are missing, the script can still try **other eligible platforms**. It cannot claim all four are public until all four independently confirm. It keeps per-platform remote GitHub receipts to avoid duplicate videos after uncertain uploads.
3. After submitting to eligible platforms, `pilot/e01_verify_platforms.py` uses official public status APIs in the SAME run: YouTube `videos.list(status,snippet)`, Facebook Graph video `published`+Page owner+permalink, Instagram Graph media Reel `permalink`+owner, and TikTok `status/fetch` with `PUBLISH_COMPLETE` and a real `publicaly_available_post_id`. It writes each verified `confirmed_public` receipt remotely and NEVER marks upload acceptance or processing as public.
4. `pilot/e01_telegram_notify.py` sends an **Arabic film-completion notification** with per-platform status as soon as a real MP4 is complete and the platform checks have run. It sends a **separate all-four-platform success notification** only after EVERY platform has a verified public receipt. Telegram messages are idempotent using remote initiated/sent markers; no duplicates after network uncertainty.
5. If Facebook, Instagram, YouTube or TikTok has a processing delay, later scheduled GPU-check runs (which request no GPU once all 36 clips are complete) can recheck status and issue the final Telegram success alert, but **the publishing itself was already attempted immediately on completion**.

## One-time Telegram setup (NO CHAT TOKEN IN CONVERSATION)

- Start Telegram and open the official <https://t.me/BotFather> bot. Send `/newbot`, choose a bot name/username and copy its token. No paid bot service is necessary.
- Open your newly created bot chat and send **/start** so the bot is authorized to message you.
- To identify your chat ID, use the official Bot API's `getUpdates` request **privately in your browser or terminal**, replacing `YOUR_PRIVATE_TOKEN` with the token:
  `https://api.telegram.org/botYOUR_PRIVATE_TOKEN/getUpdates`
  Find `result[].message.chat.id` for the chat you just opened. This is a numeric ID. Do NOT paste this URL, token, or response into a GitHub issue, public repository, screenshot, or chat.
- In <https://github.com/FadyIasaad/Nightfall-Diaries/settings/secrets/actions>, add **two repository secrets**:
  - `TELEGRAM_BOT_TOKEN` = official Telegram bot token
  - `TELEGRAM_CHAT_ID` = your private chat's numerical ID
- The ONE-click story workflow will automatically pick up the two secrets after the PR is merged. No new bot messages are sent while the episode is incomplete. No extra approval, computer or manual file upload is needed for notifications.

If the bot uses a webhook, `getUpdates` may not work; check BotFather/webhook configuration rather than exposing the token.

## Important production and platform blockers (not falsely bypassed)

The last real E01 proof was **2 of 36 genuine LTX moving shots, 10.08 seconds**. There is **no finished cinematic episode yet**. The project has not independently verified genuine character-mouth lip sync or finished cinematic acting; actual production/publication verification flags remain false, even though the owner has now granted **standing authorization** for automatic publication. Never set quality flags to true just because approval clicks were waived. The producer must supply proof of accurate character lip sync and real output quality; these are technical blockers, **not a request for manual owner approval**.

The previous official account preflight gave YouTube 403, Instagram 400, no TikTok access token, and Facebook Page identity verified (not its actual video-publishing permission). We cannot promise all four URLs without fixing OAuth, app audits and approved scopes. In particular, a TikTok Inbox upload is NOT public posting; it requires legitimate direct-post permission and creator consent. Meta Graph Page Videos is used for a 150-second full episode instead of the limited shorter Reel API. When an API response only says `accepted` or `processing`, Telegram will explicitly tell you publishing is **not yet confirmed**.

The existing daily 10:00/10:17 Cairo ZeroGPU quota rechecks are used ONLY to resume unfinished generation within the legitimate Free account allowance. They are NOT scheduled times for public posting. A video completion triggers the delivery path at once.

## Safe testing

All PR tests use fake Chat IDs, fake tokens, fake API replies and mocked GitHub receipts: no Telegram messages or real social publishing during CI. They check that incomplete films cannot trigger alerts, partial acceptance is not falsely reported as published, all four official public confirmations are needed, bot notices are sent at most once, and a missing TikTok token never blocks other eligible platforms.

Official documentation:
- Telegram Bot API: https://core.telegram.org/bots/api#sendmessage
- TikTok public post status: https://developers.tiktok.com/docs/en/content-posting-api-reference-get-video-status
- YouTube videos.list: https://developers.google.com/youtube/v3/docs/videos/list
- Meta Graph API overview: https://developers.facebook.com/docs/graph-api/overview/
