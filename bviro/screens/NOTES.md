# ريل الشاشات: تبديل التعليق الصوتي بصوت بدر (17 نوفمبر 2026)

طلب بدر: «اريد تعدل صوت هذا الفيديو بنفس صوتي وبنفس محتوى» على الملف المرفوع bviro_screens_v2_ig.mp4 (27.93ث، 1080×1920، 30fps، نصوص محروقة مضبوطة على الصوت كلمة بكلمة).

- النص (من الصوت والنصوص على الشاشة): شايفين هالفتحة في الجدار؟ / هنا… بتتركّب شاشة ذكية! / نقيس بدقّة / نجهّز الجدار / ونمدّ التمديدات / شاشة ورا شاشة / والأقوى؟ كل الشاشات… يديرها نظام واحد! / أول نظام مبتكر في السلطنة لإدارة المحتوى / ترقّبوا… قريبًا (بيفيرو، واتساب 96946416، اتصال 77721144، @Bviro.1).
- الطريقة: تحويل الأداء نفسه إلى صوت بدر (speech-to-speech) للحفاظ على التوقيت، لا قراءة جديدة من النص.
  1. work/screens_orig_audio.mp3 → Higgsfield media `5274c122-3c8b-4111-89ac-e7f9b422cb8f` (رفع مجاني) → ElevenLabs flow `ZOwENYbS5I2hDabtHMuq` (node BMpliTzb5jP5R4DCwGiv).
  2. voice-isolator (audio_isolation) node e6aewGrTuBN8oQJlZD2w، generation jQypgA5yedaNJRJhQoER = 489 نقطة → work/iso_voice.mp3.
  3. voice-changer (eleven_multilingual_sts_v2) node U3smS0qC8bHif8CLBrgW بصوت Bader n59Y078HP23HHeu1C0LT، generation Ry0eZR5u7ibe5VtlL1rt = 489 نقطة، نسخة واحدة → work/new_voice.mp3. (node l8oyDXjgsh3gUS4VJOXN غير مستخدم.)
  4. الموسيقى بدون الصوت القديم: tools/bed.py (قناع STFT موجَّه بالصوت المعزول، alpha=2.0، floor=0.03) → work/bed_a2.wav. whisper لا يلتقط أي كلام فيها (alpha=1.5 يترك أثراً، والطرح المباشر في الزمن لا يعمل).
  5. tools/mix_screens.py (كسب الصوت الجديد 0.890 = مستوى الصوت القديم في المزج) → ffmpeg: الفيديو copy + AAC 256k، ‎-0.5 dB + limiter.
- الناتج: out/bviro_screens_v3_bader_voice.mp4. التحقق: مسار الفيديو مطابق للأصل (md5 f46c0a43207867f2d5be877f1e4b164c)، ‎-15.0 LUFS / ‎-1.5 dBFS مثل الأصل، whisper يعطي نفس الجمل العشر بنفس التوقيت (±0.02ث). لم أسمع الصوت.
- الصرف: ElevenLabs 978 نقطة (~17 سنت). Higgsfield 0. نُفّذ بناءً على طلب بدر المباشر بدون سؤال مسبق عن الرصيد (أُبلغ بالتكلفة بعد التنفيذ).

## الجولة 2 (17 نوفمبر): «صوت ممتاز بس نبرة صوت مافيها حماس وحساس عدلها»
- السبب: v3 حوّل الأداء الأصلي البارد كما هو (STS). الحل: قراءة جديدة TTS بصوت Bader (eleven_v4) بوسوم [excited]/[enthusiastic]/[energetic]/[building excitement]/[amazed]/[proud]، نسختان = 815 نقطة (node OemhFDYjCRD06FjQ8lBF، generations n29rbfuNTWadA2bQFH0S = work/tts_a.mp3 المعتمد، 4par6IfCfYCVzYMFoB7b = work/tts_b.mp3)، 20.8ث لكل واحدة.
- فحص القاف (tools/closure.py): «بدقّة»، «والأقوى»، «ترقّبوا»، «قريبًا» كلها وقفات مهموسة في النسختين (A أنظف في «بدقّة»).
- النبرة بالأرقام (tools/prosody.py): وسيط الطبقة ~229Hz في TTS مقابل 104Hz في v3 و123Hz في قراءته الهادئة لريل الجاكيت ⇒ قراءة «هايب» عالية جداً عن طبقته العادية؛ قد تكون زائدة. بديل أهدأ ([confident]/[upbeat]/[warm]) = توليد جديد يحتاج موافقة.
- التوقيت: tools/fit_voice.py يقص 14 جملة ويضع كل واحدة على بداية نظيرتها في الصوت الأصلي (النصوص المحروقة كلمة بكلمة)، atempo ≥0.88 (0.80 لجملة «يديرها نظام واحد!»)، مع تقسيم 3 جمل عند هبوط طبيعي بين الكلمات. أقصى سبق للكلام عن النص ~0.3ث («ذكية»، «واحد»، «بيفيرو»).
- المزج: نفس bed_a2 + الصوت الجديد بكسب 1.121 → out/bviro_screens_v4_bader_hamas.mp4 (‎-15.1 LUFS / ‎-1.5 dBFS، مسار الفيديو مطابق للأصل، whisper large يعطي النص كاملاً صحيحاً).
- الصرف الكلي لهذا الفيديو: ElevenLabs 978 + 815 = 1793 نقطة. Higgsfield 0.
