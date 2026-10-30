# Nightfall V4.1 — التشغيل والنشر التلقائي أونلاين

## المطلوب من النظام

- **كل يوم 10 صباحًا بتوقيت القاهرة:** GitHub Actions يشغّل حلقة جديدة باستخدام سيرفر GitHub (ليس جهازك).
- يمكنك في أي وقت الضغط يدويًا: **Actions → 03 - Nightfall One Click Auto Upload V4.1 → Run workflow**.
- الوضع الافتراضي `generate_and_upload`، والحلقة `auto`، والمنصات `all`.
- نفس القناة الحالية على YouTube ونفس صفحة Facebook ونفس حساب TikTok **بعد توصيل الصلاحيات**.
- النشر العام على YouTube وFacebook فقط بعد إضافة `DRAMA_ALLOW_UNREVIEWED_PUBLIC=true` إلى Actions Secrets؛ بدونه تذهب الفيديوهات إلى YouTube **Private** وFacebook **Draft** تلقائيًا.
- TikTok يرسل إلى **Inbox** للمراجعة والإكمال، وليس منشورًا عامًا؛ النشر المباشر يتطلب موافقة تطبيق TikTok و `video.publish` وموافقة منشئ المحتوى وفق شروط المنصة.
- لو منصة لا يوجد لها حساب/صلاحية متصلة، لن يصلها الفيديو؛ ستظهر `missing_credentials` وستظل نسخة MP4 في Artifacts (الاحتفاظ 7 أيام).
- لو API أعطى ردًا غير واضح بعد بدء عملية رفع، النظام لا يعيد الرفع تلقائيًا لمنع تكرار الحلقة؛ سترى `needs_reconcile`، ويجب مراجعة الحساب.

## رفع المشروع إلى GitHub

1. انسخ مجلدات **المشروع داخل ZIP** إلى جذر مستودع `Nightfall-Diaries` باستخدام Codespaces (لا ترفع ZIP كمجرد ملف وتظن أنه ثبت).
2. احتفظ بملفات بيانات العمل السابقة `cloud_data/` ولا تستبدل ملفات تقدم الحلقات الحقيقية بملفات البداية الموجودة في ZIP.
3. عطّل الـworkflows القديمة التي تنشر الفيديو، ومنها V3 وV4 القديم إن كان لا يزال مجدولًا.
4. Settings → Actions → General → Workflow permissions → Read and write permissions.
5. أضف كل بيانات دخول API في Settings → Secrets and variables → Actions **من دون مشاركتها في الدردشة**.

## أسرار وبيانات الحسابات

**YouTube:** `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`، وفي Variables: `YOUTUBE_EXPECTED_CHANNEL_ID`.

**Facebook Page:** `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN`، مع صلاحيات Page المسموح بها.

**TikTok Inbox:** `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REFRESH_TOKEN`, `DRAMA_TOKEN_KEY` وتفويض `video.upload`.

**للنشر العام تلقائيًا على YouTube وFacebook:** Secret باسم `DRAMA_ALLOW_UNREVIEWED_PUBLIC` وقيمته `true`. **لا تضفها إلا إذا كنت موافقًا على نشر الحلقات للجمهور دون مراجعة كل فيديو.** غيابها لا يمنع إنشاء الفيديو أو رفعه خاصًا/مسودة.

## تشغيل من زر واحد

1. افتح صفحة Actions → `03 - Nightfall One Click Auto Upload V4.1` → Run workflow.
2. اضبط `mode=generate_and_upload`, `episode=auto`, `destinations=all`، واضغط Run workflow.
3. راجع نتائج `UPLOAD RESULTS` في لوج خطوة التشغيل.
4. الفيديو متاح في Summary → Artifacts → `nightfall-video-...`.

اختيار `preview_only` هو **اختياري** إذا أردت اختبارًا من غير رفع. واختيار `upload_private_drafts` يجبر YouTube/Facebook على الوضع الخاص/المسودة حتى لو كنت مفعّل النشر العام.

## تنبيه عن جودة الرسوم

المولّد الموجود هنا ينشئ رسومات فانتازيا **2D أصلية، ثابتة الشخصيات**، مع تحريك كاميرا وكلام ومؤثرات؛ ليس مولّد مشاهد واقعية ثلاثية الأبعاد. يعتمد على GitHub Actions وسماحيات المنصات وحصص التشغيل المجانية؛ ليس هناك ضمان أن كل تشغيل سينجح أو أن النشر العام سيتاح لكل حساب.
