# نقل المشروع إلى Claude على سطح المكتب (ويندوز) وربطه بـ Blender وUnity

الهدف: تشغيل Claude Code على كمبيوترك (كرت RTX 5080)، فيفتح المشروع من جهازك ويتحكم في
Blender وUnity مباشرة، ويصوّر الجولات بكرت الشاشة بدل السيرفر السحابي.

> الفرق المهم: الجلسة السحابية (التي بنينا فيها المشروع) تعمل على سيرفر بعيد ولا ترى جهازك.
> الجلسة على سطح المكتب تعمل **على جهازك نفسه**، فترى ملفاتك وتتصل ببرامجك.

---

## الخطوة 1: تثبيت البرامج الأساسية (مرة واحدة)

افتح **PowerShell** (من قائمة ابدأ اكتب PowerShell) وشغّل الأوامر واحدًا واحدًا:

```powershell
# Git: لتنزيل المشروع من GitHub
winget install --id Git.Git -e

# Node.js 22: لتشغيل الموقع
winget install --id OpenJS.NodeJS.LTS -e

# uv: يشغّل خوادم MCP (الجسر بين Claude وBlender/Unity)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

بعدها **أغلق PowerShell وافتحه من جديد** حتى تُعرف الأوامر الجديدة، ثم:

```powershell
# pnpm: مدير الحزم الذي يستخدمه المشروع
corepack enable
```

تأكد أن كل شيء مثبت:

```powershell
git --version
node --version
uvx --version
```

**Blender:** يجب أن يكون الإصدار 4.2 أو أحدث (جربنا على 5.2). من [blender.org](https://www.blender.org/download/).

---

## الخطوة 2: تنزيل المشروع على جهازك

```powershell
cd $HOME\Documents
git clone https://github.com/Bader78oo/Bader-.git
cd Bader-
git checkout claude/claude-md-docs-l47tk2
pnpm install
```

الآن المشروع موجود في `Documents\Bader-`.

> الفرع `claude/claude-md-docs-l47tk2` فيه كل الشغل (المعالجة، صفحة العرض، المجمع التجريبي).
> لاحقًا ندمجه في الفرع الرئيسي `main`.

---

## الخطوة 3: تثبيت Claude على سطح المكتب

1. نزّل تطبيق Claude من [claude.ai/download](https://claude.ai/download) وسجّل دخولك بنفس حسابك.
2. داخل التطبيق افتح تبويب **Code** (Claude Code).
3. اختر **فتح مجلد / Open folder** واختر `Documents\Bader-`.

Claude سيقرأ ملف `CLAUDE.md` تلقائيًا ويفهم المشروع.

---

## الخطوة 4: ربط Blender

نستخدم إضافة **Blender MCP** (مفتوحة المصدر: [github.com/ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp)).

**داخل Blender:**
1. نزّل الملف `addon.py` من صفحة المشروع في GitHub.
2. في Blender: **Edit ← Preferences ← Add-ons**، ثم من السهم في الأعلى **Install from Disk** واختر `addon.py`.
3. فعّل الإضافة **Interface: Blender MCP**.
4. في نافذة العرض الثلاثي اضغط **N** لتظهر القائمة الجانبية، افتح تبويب **BlenderMCP**،
   واضغط **Connect to Claude** (أو Start Server).

**في Claude:** المشروع فيه ملف `.mcp.json` يعرّف خادم Blender. أول مرة تفتح المشروع، Claude
سيسألك هل توافق على تشغيله، **وافق**.

للتأكد: اكتب في Claude الأمر `/mcp` ويجب أن ترى `blender` متصلًا.

> إذا كان Blender مربوطًا عندك من قبل في تطبيق Claude العادي (المحادثة)، فهذا إعداد منفصل.
> Claude Code يحتاج الربط من ملف `.mcp.json` الموجود في المشروع، أو بالأمر:
> `claude mcp add blender -- uvx blender-mcp`

**تنبيه:** Blender MCP يسمح لـ Claude بتشغيل أوامر داخل Blender. احفظ عملك قبل أن تطلب منه
تعديلات كبيرة. ويتصل عميل واحد فقط في نفس الوقت، فأغلق أي جلسة Claude أخرى متصلة بـ Blender.

---

## الخطوة 5: ربط Unity

نستخدم **MCP for Unity** ([github.com/CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp)).

1. افتح مشروعك في Unity.
2. **Window ← Package Manager**، ثم زر **+** ← **Add package from git URL**، والصق الرابط
   الموجود في صفحة المشروع على GitHub (قسم Installation).
3. بعد التثبيت تظهر نافذة **MCP for Unity** في قائمة Window. افتحها واختر إعداد
   **Claude Code**، وهي تضيف الإعداد تلقائيًا.
4. في Claude اكتب `/mcp` وتأكد أن `unity` ظاهر ومتصل.

> أسماء القوائم قد تختلف قليلًا حسب إصدار الإضافة. المرجع الدقيق هو ملف README في صفحتها.
> إذا كان Unity مربوطًا عندك من قبل، فقط تأكد أنه ظاهر في `/mcp` داخل Claude Code.

ملاحظة: Unity ليس ضروريًا للمرحلة الحالية. المعالجة كلها في Blender، وصفحة العرض تعمل في
المتصفح. Unity نحتاجه لاحقًا لنسخة صالة العرض الفاخرة (شاشة كبيرة في مكتب المبيعات).

---

## الخطوة 6: تجربة المعالجة على كرت الـ 5080

في PowerShell داخل مجلد المشروع (عدّل مسار Blender حسب الإصدار عندك):

```powershell
$blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"

# مثال على المجمع التجريبي بجودة كاملة
& $blender -b -P pipeline\blender\make_test_complex.py -- --output test_complex.glb
& $blender -b -P pipeline\blender\process_model.py -- --input test_complex.glb --output public\tours\compound-hq --device gpu
```

`--device gpu` يجبره على كرت الشاشة. يجب أن ترى في السطور: `rendering on OPTIX: NVIDIA GeForce RTX 5080`.

لعرض النتيجة:

```powershell
pnpm dev
```

ثم افتح في المتصفح: `http://localhost:3000/tour/compound-hq`

> صفحة `/tour` لا تحتاج قاعدة بيانات، لكن الموقع يتطلب ملف `.env`. أسهل طريقة: انسخ
> `.env.example` إلى `.env`. أو اطلب من Claude: "جهّز ملف .env للتجربة المحلية".

---

## الخطوة 7: الفلة التي نزّلتها من CGTrader

1. فك ضغط `Maps.rar` (الخامات) في مجلد، مثلًا `Downloads\villa\Maps`.
2. افتح `villa fbx.fbx` في Blender (**File ← Import ← FBX**).
3. **File ← External Data ← Find Missing Files** واختر مجلد `Maps`، لتظهر الخامات.
4. **File ← External Data ← Pack Resources**، لدمج الخامات داخل الملف.
5. **File ← Save As** ← `Documents\Bader-\models\villa.blend`.

ثم اطلب من Claude في الجلسة الجديدة معالجتها (انظر الرسالة الجاهزة بالأسفل).

---

## الرسالة الأولى للجلسة الجديدة (انسخها والصقها)

```
اقرأ CLAUDE.md و pipeline/README.md لتفهم المشروع.
هذا المشروع بنيناه في جلسة سحابية، والآن نعمل على جهازي (ويندوز، RTX 5080).

1. تأكد أن Blender متصل عبر MCP (/mcp)، وأن Unity متصل إن وجد.
2. افتح الملف models/villa.blend في Blender وأعطني وصفًا للفلة: الغرف، الطوابق، المسبح،
   هل الخامات ظاهرة، وأسماء العناصر الرئيسية.
3. شغّل pipeline/blender/process_model.py عليها بكرت الشاشة (--device gpu) وأخرجها إلى
   public/tours/villa، ثم شغّل الموقع وأرني النتيجة على /tour/villa.
4. إذا لم تُكتشف الغرف أو المرافق بشكل صحيح، عدّل الكود في pipeline/blender حتى يعمل مع
   هذا النوع من الملفات، واشرح لي ما غيّرته.
```

---

## مشاكل شائعة

| المشكلة | الحل |
|---|---|
| `uvx` غير معروف | أغلق PowerShell وافتحه من جديد بعد تثبيت uv |
| `/mcp` لا يظهر blender | تأكد أن الإضافة مفعّلة في Blender وأنك ضغطت Connect، ثم أعد تشغيل Claude |
| المعالجة تقول `rendering on CPU` | حدّث تعريف NVIDIA، وتأكد من Blender → Preferences → System → OptiX |
| الفلة رمادية/وردية في الصور | الخامات مفقودة: كرر الخطوة 7 (Find Missing Files + Pack Resources) |
| لا توجد صور 360 داخلية | الفلة قد تكون بلا سقف أو الغرف مفتوحة؛ اطلب من Claude فحص النموذج |
