# Templates, storyboard fields, and prompt library

## Pick a template (`storyboards/templates/`)
| Template | Length | Bader on screen | Voice | Typical credits |
|---|---|---|---|---|
| `talking-head.json` | 15–20 s | ~70% (one Wan clip + punch-ins) | his recording, whole | ≈35–40 |
| `broll-explainer.json` | 20 s | ≤7 s (two Wan clips) | his recording, tightened | ≈45–65 |
| `event-promo.json` | 15 s | stills only (optional) | none — pad/music | ≈3–16 |
Each template has a `_guide` block (ignored by the scripts): use, recipe, estimate, rules.
Copy to `storyboards/<slug>.json`, fill the `<...>` placeholders, then follow SKILL.md.

## Storyboard fields
- `shots[]`: sequential. `src` (mp4 or png/jpg), `in` (video start), `dur`, optional `url` (auto-download),
  `zoom` (1.2–1.35 = punch-in "second camera"), stills: `kb` = in | out | left | right | up, `kb_zoom` (0.12).
  Talking-head clips share one audio timeline → their `in` equals the shot's start time in the reel.
- `hook` {s,e,text,sub}: big title top — use in the first 2–3 s of every reel.
- `captions[]` {s,e,from,to,icon} word-synced from `words` · or {s,e,text,icon} fixed line.
- `checklist` {s,e,items[{t,text,icon}], style:"info"?} — benefits (✓) or event facts (date/place/time).
- `name_card` {s,e,name,role} · `stickers[]` {s,e,text} · `cta` {s,e,text,icon} · `end_card` {s,tag,sub}.
- `grade` {contrast,saturation,brightness,vignette,lut} — `lut: "brand/bviro_look.cube"` = Bviro look
  (regenerate/tune with `scripts/make_lut.py brand/bviro_look.cube --mix 0.6`).
- `audio` {pad,pad_gain,whoosh_on_cuts,impact_at_end,music,music_gain_db}; `voiceover`/`words` may be null.
- `layout` tops in px (720×1280): keep text between y≈220 and y≈1080 (Instagram UI covers the edges).
Icons: any Lucide name (lucide.dev/icons), e.g. glasses, graduation-cap, heart-pulse, brain, users,
trending-up, calendar, map-pin, clock, ticket, bell, rocket, sparkles, school, stethoscope, plane, box.

## B-roll prompt library (kling3_0 std, 5 s, sound off, 9:16)
Pattern: `<shot size + angle>, <subject + action>, <setting>, <lighting>, <camera move>, cinematic realistic, no text.`
Always add Omani context (dishdasha + kuma/massar for men, school headscarf/abaya for women) and
Bviro accents: "subtle violet (#7F00FF) and turquoise (#01CEC9) accent light".
- Education: students putting on VR headsets in a bright Omani classroom; POV inside a 3D human heart; POV on the Moon with Earth rising; hand touching a floating solar-system hologram.
- Medical: medical students around a holographic 3D anatomy model in a modern Omani training lab; surgeon trainee in VR performing a simulated procedure.
- Conferences/exhibitions: wide shot of a busy exhibition booth with large LED screens showing 3D content; visitors trying VR headsets at a branded booth.
- Aviation / training simulation: trainee pilot in a VR cockpit simulation, instrument lights, slow orbit.
- 3D design / AR: designer rotating a glowing 3D model with hand gestures; phone showing an AR model placed on a desk.
Camera vocabulary that reads well: slow dolly-in, crane down, orbit, low-angle push-in, rack focus, handheld subtle.
Lighting vocabulary: soft window key, violet side light, turquoise rim/back light, volumetric haze, practical LED glow.

## Soul stills (soul_2, ~1 credit, 9:16)
Medium shot for talking (hands visible, VR lab behind, violet side light) · close 3/4 portrait (turquoise rim, dark holographic bokeh) ·
for stills-only reels: Bader presenting at a podium/exhibition booth, Bader with students wearing headsets.


## Added 2026-09-26
- `hook` may be a list: `[{s,e,text,sub,top,style}]`; `style: "loop"` = teal open-loop panel.
- `end_card.contacts`: `[{icon,text}]` pills under the tagline (e.g. camera `@Bviro.1`, message-circle WhatsApp, phone).
- `scripts/music.py out.wav --dur D --sections 0,a,b,...` builds a section-aware music bed; set `audio.music` + `music_gain_db` (-15 under voice) and `pad: false`.
