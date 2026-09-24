# مهارات Blender مفتوحة المصدر لتصميم بيئات تعليمية VR في Unity

دليل مرجعي لأدوات ومهارات (Claude Skills و MCP) مفتوحة المصدر تساعد في إنتاج نماذج 3D احترافية
في Blender وتصديرها بشكل جاهز لـ Unity وتطبيقات الواقع الافتراضي.

## 1. الأساس: ربط Claude بـ Blender و Unity (MCP)

| الأداة | الوظيفة | الترخيص |
|---|---|---|
| [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) | يتحكم Claude مباشرة في Blender: إنشاء الكائنات، المواد، فحص المشهد، تنفيذ Python، وجلب أصول من Poly Haven و Sketchfab. أغلب المهارات في الأسفل تعتمد عليه | MIT |
| [CoplayDev/unity-mcp](https://github.com/CoplayDev/unity-mcp) | يتحكم Claude في محرر Unity: المشاهد، الـ GameObjects، السكربتات، الأصول. يدعم Unity 2021.3 حتى 6.x | MIT |
| [IvanMurzak/Unity-MCP](https://github.com/IvanMurzak/Unity-MCP) | بديل لـ Unity MCP يتضمن Skills وأداة CLI | مفتوح المصدر |

## 2. مهارات Claude الخاصة بـ Blender

| المهارة | لماذا تناسب مشروع VR تعليمي |
|---|---|
| [arjun988/blender-skills](https://github.com/arjun988/blender-skills) **(الأنسب)** | 94 مهارة متخصصة تغطي كل خط الإنتاج: النمذجة (بيئات، دعائم، شخصيات)، Retopology، UV، Baking، **LOD** و**Collision proxies**، و**تصدير مخصص لـ Unity**. تعمل عبر BlenderMCP |
| [RobLe3/cc-blender-skill](https://github.com/RobLe3/cc-blender-skill) | 30 مهارة متسلسلة (نمذجة، مواد، إضاءة، كاميرات، إخراج، أنيميشن، تصدير glTF/FBX). مجرّبة على Blender 5.x. لا تتضمن إعدادات خاصة بـ Unity |
| [mhd347/blender-expert-skill](https://github.com/mhd347/blender-expert-skill) | مهارة معرفية (بدون MCP) عن Geometry Nodes، Sculpt، PBR، الإضاءة، و Python في Blender 4.x. تُرفع كملف `.skill` في إعدادات Claude |
| [freshtechbro/claudedesignskills – blender-web-pipeline](https://github.com/freshtechbro/claudedesignskills/blob/main/.claude/skills/blender-web-pipeline/SKILL.md) | تصدير glTF بالدفعات مع تحسين الأداء. مفيدة إذا أردت عرض النماذج على الويب داخل منصة SaaS هذه |
| [OpenAEC-Foundation/Blender-Bonsai-…-Skill-Package](https://github.com/OpenAEC-Foundation/Blender-Bonsai-ifcOpenshell-Sverchok-Claude-Skill-Package) | 73 مهارة لـ Blender مع Bonsai و IFC. مناسبة إذا كانت البيئات التعليمية مباني أو فصولاً واقعية مأخوذة من مخططات معمارية |

## 3. إضافات Blender للتصدير إلى Unity

| الإضافة | الفائدة |
|---|---|
| [EdyJ/blender-to-unity-fbx-exporter](https://github.com/EdyJ/blender-to-unity-fbx-exporter) | تصدير FBX يصحح اتجاه المحاور والمقياس ليتوافق مع Unity (لا دوران ‎-90 ولا مقياس 100) |
| [berkecuhadar/Blender_to_Unity](https://github.com/berkecuhadar/Blender_to_Unity) | إعدادات جاهزة لـ Unity 6 بضغطة واحدة: تثبيت التحويلات (bake transforms)، والعظام المشوِّهة فقط، والأنيميشن |
| [VRse FBX Batch Exporter](https://extensions.blender.org/add-ons/vrsefbxbatchexporter/) | تصدير عدة كائنات دفعة واحدة، مع التحقق من نجاح التصدير |

## 4. طريقة التركيب المقترحة (Claude Code)

```bash
# 1) ثبّت BlenderMCP: فعّل ملف addon.py داخل Blender، ثم أضف الخادم إلى Claude Code
claude mcp add blender uvx blender-mcp

# 2) أضف مهارات Blender إلى مشروع Unity/Blender الخاص بك (وليس إلى هذا المستودع)
git clone https://github.com/arjun988/blender-skills
cp -r blender-skills/.claude/skills/* <مشروعك>/.claude/skills/

# 3) في Unity: Package Manager → Add package from git URL
#    https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#main
```

## 5. قائمة تحقق لأصول VR التعليمية

- **ميزانية المضلعات (Poly budget):** لنظارات Quest المستقلة اجعل المشهد كله في حدود 300k–750k مثلث تقريباً، وأضف LOD للكائنات الكبيرة.
- **المقياس:** 1 وحدة في Blender = 1 متر في Unity. هذا أمر أساسي في VR، لأن أي خطأ في المقياس يلاحظه المستخدم فوراً.
- **المواد:** استخدم PBR من نوع Principled BSDF، ثم اجمع القوام في Atlas وقلّل عدد المواد لتخفيض Draw calls.
- **الإضاءة:** اخبز الإضاءة مسبقاً (Lightmaps) في Unity، وجهّز UV2 غير متداخلة في Blender.
- **التصادم:** صمّم Collision proxies مبسطة للأجسام التي يمسكها المتعلم باستخدام XR Interaction Toolkit.
- **الصيغة:** استخدم FBX للنماذج المتحركة والمربوطة بعظام، و glTF (عبر حزمة `com.unity.cloud.gltfast`) للأصول الثابتة أو التي تُحمَّل أثناء التشغيل.
- **مصادر أصول مجانية:** [Poly Haven](https://polyhaven.com) (CC0)، ومتاحة مباشرة عبر BlenderMCP.
