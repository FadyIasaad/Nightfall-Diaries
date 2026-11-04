# Nightfall Diaries — Phase 0 Platform Audit Preparation
**Status: prepared, NOT submitted.** No private credential values appear in this document. The owner has not confirmed live policy URLs or any provider app-review submissions.

## 1) GitHub Pages policies
The draft pages are in `docs/`: [privacy](privacy.md), [terms](terms.md), [support](support.md). They are **not externally verified until enabled**. In GitHub, the owner must choose **Settings → Pages → Deploy from a branch → main → /docs → Save**, then open the displayed real URL. GitHub [documents this publishing setup](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site). The owner must configure a **real private contact channel** and approve the legal/operator wording before using these URLs for a platform review.

**Do not guess URL host/path; copy the working link from GitHub Pages after deployment.** Public Issues are only for non-sensitive issues. Never post tokens, sensitive account details or personal information in them.

## 2) YouTube — updated November 2026
**Important correction:** Google's [November 2, 2026 revision](https://developers.google.com/youtube/data/revision_history) removed the former rule forcing uploads from unverified API projects into private status. The current [videos.insert documentation](https://developers.google.com/youtube/data/reference/rest/v3/videos/insert) also lists `status.containsSyntheticMedia` as supported. **The previous mandatory audit-to-be-public assumption is outdated.**

An audit may still be needed when requesting additional quotas or when Google's separate OAuth verification/compliance procedures require it; Google's [quota-and-compliance page](https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits) covers that process. Do **not** submit an unnecessary audit solely on the superseded privacy lock claim.

### Draft use-case statement (owner should verify)
> Nightfall Diaries is an owner-controlled automation producing original, AI-assisted episodic animated fiction. The tool uploads only to the owner's existing authorized YouTube channel, retains a platform video ID and processing/privacy status, discloses synthetic media where required, and does not offer third-party uploads or conceal sponsored content. Publishing is blocked until actual video quality and YouTube account authorization are verified.

Before testing any public YouTube post, check OAuth application credentials, scope, channel ownership, upload quota, AI disclosure field, and actual `videos.list` status/permalink. **Never claim public visibility just because `videos.insert` returned an ID.** Use a private/unlisted test only after owner authorization and quality gates allow it.

## 3) TikTok — platform audit is a real gate
TikTok's [Direct Post guide](https://developers.tiktok.com/docs/en/content-posting-api-get-started) requires an authorized `video.publish` scope. Its [app FAQ](https://developers.tiktok.com/docs/en/getting-started-faq) confirms unaudited clients have private-viewing restrictions, and [Direct Post reference](https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post) requires `creator_info` and appropriate privacy choices.

**Owner action:** use the TikTok for Developers dashboard to register/configure the Content Posting API app, choose Direct Post, provide verified policy URLs and working demo evidence as requested, grant creator OAuth to the intended TikTok account, then submit the app audit through the portal. Do not claim that any audit was actually submitted; this repo currently lacks `TIKTOK_ACCESS_TOKEN`.

### Draft TikTok use-case statement
> Nightfall Diaries produces original short animated fiction for the single owner-authorized TikTok account. The workflow displays the destination account and allowed posting choices, requires owner-approved release gates, uses the official Content Posting API, declares AI-assisted media when applicable, tracks the publishing ID and polls the actual post status. Pending inbox uploads remain drafts, not publicly published posts. Access can be revoked in the user's TikTok account settings.

The app should honor creator-provided visibility and platform review guidelines. The present `studio/crosspost.py` uploader does not implement all required creator_info, chunking, privacy and public-status reconciliation; **no final TikTok review should claim those features are implemented yet**.

## 4) Meta: existing Page + Instagram
Intended Page: **Nightfall Diaries**; Instagram business account: **stores.nightfall**. Logs show masked credentials were supplied, **not** that the Page or IG upload/public-post permissions were demonstrated. Verify business/Page ownership and Meta permissions, then test official supported Page video and Instagram Reels endpoints in later phases. Never repurpose personal Pages or the wrong account. Verify URL and correct Graph API version before any posts.

## 5) Credential checklist (one-time, browser only)
- [ ] Owner configures a working private support contact and approves public privacy/terms.
- [ ] Owner confirms Pages site is live and policy URLs are readable without login.
- [ ] Owner confirms intended YouTube project/channel and whether quota/OAuth review is actually required (do not assume).
- [ ] Owner creates/authorizes TikTok API app and submits audit only once its requested functionality is honestly demonstrated.
- [ ] Owner confirms Meta account ownership and permissions.
- [ ] Owner separately obtains Kaggle account access and credentials; only store tokens in GitHub Actions secrets.
- [ ] Owner does **not** paste tokens, cookie files, OAuth codes, or sensitive identifiers into chats or Markdown.

## Explicit scope
This Phase 0 work **does not** submit audits, connect a new OAuth app, verify account access, activate Pages, issue keys, publish videos, or change any production gate. Those actions require owner authorization and/or functioning platform integrations.
