# VR lessons

Interactive WebXR lessons for children, built with [A-Frame](https://aframe.io) (vendored in `lib/`,
so lessons work without a CDN). Each lesson is a single static `index.html`.

| # | Lesson | Subject |
|---|--------|---------|
| 1 | [`lesson-01-local-habitats/`](lesson-01-local-habitats/) — رحلة إلى البيئات المحلية | Science, Grade 1 — local habitats |
| 2 | [`lesson-02-young-animals/`](lesson-02-young-animals/) — صغير الإنسان وصغير الحيوان | Science, Grade 1 — young humans and young animals |

## Running

Files in `public/` are served by Next.js as static assets:

```bash
pnpm dev   # then open http://localhost:3000/vr/
```

Any static server works too, e.g. `python3 -m http.server -d public` → `http://localhost:8000/vr/`.

**On a headset (Meta Quest etc.):** open the lesson URL in the headset browser and press the **VR**
button. WebXR requires HTTPS (or `localhost`), so serve it from a deployed URL rather than a LAN IP.

Controls: drag / touch to look around and tap to select on desktop and phone; in VR, point the
controller laser and pull the trigger.

## Lesson 1 structure

1. **Welcome** — lesson objectives and vocabulary (بيئة، مزرعة، حيوانات أليفة).
2. **Mission 1: Explore** — five habitats around the child (forest, pond, desert, farm, home);
   touching an animal/plant shows where it lives and what the habitat provides. Goal: 12 discoveries.
3. **Mission 2: Sort** — a "lost" animal or plant appears; the child points at the correct habitat
   (its sign, or any creature in it). Stars for first-try answers, hint after two misses.
4. **What did I learn?** — summary matching the lesson's learning outcomes, replay or free explore.

What's in the scene:

- **3D models** — every animal and plant is built in code from simple shapes and merged into one
  mesh per model (one draw call each, light enough for a standalone headset). `?gallery` lines them
  all up for review.
- **Omani identity** — Salem (سالم), a guide in a dishdasha with its tassel and an embroidered
  kumma; the Omani flag; a Nizwa-style fort; Hajar mountains; date palms; a falaj in the farm;
  a traditional house; the Arabian oryx; Jebel Akhdar roses; an eight-point star floor.
- **Cards** — laid out on canvas at high resolution and sized to their content, so text never
  overflows; the habitat signs stand at the back of each habitat, above the animals.
- **Turning** — flick the right (or left) thumbstick to turn 30°; arrow keys on desktop.

## Lesson 2 structure

Set in **Salalah in the khareef**: green Dhofar hills in light mist, coconut palms, banana plants,
frankincense trees, a Darbat-style waterfall and Omani brass lanterns. A sun-dial post (or the
«الوقت» button / `T` key) switches between sunrise, day, sunset and night: sky, light, fog, stars,
moon, glowing lanterns and fireflies all change, and Salem comments on it. Seven enclosures surround
the child, each with a parent and its young: lion and cub (الشبل), elephant and calf, she-camel
(in Omani camel dress) and حوار, Omani goat and جدي, a duck with eight ducklings, a rabbit with nine
young, and an Omani mother with her baby in a cradle.

1. **Arrival** — a start button (plus one that enters VR directly); a welcome banner with the
   lesson's name, fireworks and Salem greeting the class.
2. **Welcome** — objectives and vocabulary (صغير، الإنسان، الشبل، طفل).
3. **Mission 1: Meet the young** — touch each young (or its parent / sign) to hear its name, its
   sound, what it becomes when it grows up, and how many young are born at a time.
4. **Mission 2: Who is my mother?** — a lost young appears with a 40-second timer; the child points
   at its mother or her sign. Stars for first-try answers, hint after two misses; when time runs out
   Salem shows the mother and the young flies home.
5. **Mission 3: The young grow up** — press «كبّره!» to watch a cub become a lion, a حوار become a
   camel, and a baby become a boy and then an adult.
6. **Mission 4: Count the young** — the young play on the grass, well apart; each one touched hops
   onto the next numbered spot on a bench, so the row shows the count (8 ducklings, 9 young rabbits,
   the mother's one baby). The numbers come from `content.js` and are checked in code.
7. **Mission 5: An enclosure for the kid** — choose food, water and shelter for the جدي; toys and
   sweets are politely refused.
8. **What did I learn?** — summary matching the book's «ماذا تعلمت», replay or free explore.

**Immersion (v4)** — the child moves and uses their hands instead of only pointing:
- *Walk*: push the thumbstick forward to aim an arc of golden beads with a footprint marker, let go
  to jump there (a short fade to black keeps it comfortable); arrow keys / W-S on screen.
- *Grab and carry*: in «من أمي؟» the lost young sits on the grass; hold the trigger (or mouse button)
  on it, carry it across the park and let go inside its mother's enclosure. The wrong mother shakes
  her head and the young runs back. Touching the mother or her sign still works as a fallback.
- *Feel and hear*: controller haptics on grab, success and petting; hearts when an animal is touched;
  animal voices come from where the animal is (HRTF panning), and the lost young and its mother call
  to each other so the child can follow the sound.
- *A living park*: parents turn to watch a child who comes close, young wander and come over, the
  duck swims round the pond with her ducklings in a line, Salem walks along with the child.
- *Become small*: from the summary, the world grows three times around the child, who stands among
  the ducklings under a giant mother duck.

The full vision for the project (a hub of lesson worlds, story quests, next settings) is in
[`vr-plans/VISION.md`](../../vr-plans/VISION.md).

Animal voices (roar, trumpet, bleat, quack, peep …), birdsong by day and crickets at night are
synthesised with WebAudio, so there are no sound files to host.

**Magic words (v5)** — «الكلمات السحرية 🪄» from the summary panel: the child says an Arabic word
out loud (browser speech recognition, `ar-SA`) or taps a word chip, and it appears in front of them
with a sparkle and Salem's voice — animals (lion, elephant, camel + حوار, goat + جدي, duck, rabbit,
baby), objects (a palm tree, a hut), and nature words (water, sun, moon, star) via emoji billboards
for the abstract ones. Chips work with no mic and no speech recognition support (Quest's browser
support for it is inconsistent), so the feature is always usable.

**Talk to Salem (v6, pending a live backend)** — «تكلم مع سالم 🎙️» from the summary panel: the
child asks Salem any question by voice; it's sent to a small backend (holds the AI API key,
never exposed client-side) which returns a short in-character Arabic reply, spoken live via the
browser's TTS (an AI reply can't be pre-recorded — it's different every time). Falls back to a
warm recorded line if the backend is unreachable, so the feature never breaks the lesson. The
backend (`vr-plans/salem-backend/`, built on Replit) is not live yet — publishing is blocked by
a Replit account/billing restriction; `SALEM_BRAIN_URL` in `index.html` is a placeholder until
then.

`?gallery` lines up all of lesson 2's models; `?test` exposes hooks used by the automated flow check
(`&rt=8` shortens the timer). Guidance for future lessons (new place and new mechanic each time):
[`vr-plans/LESSON-GUIDE.md`](../../vr-plans/LESSON-GUIDE.md).

## Voice

Every spoken line has a key. `content.js` holds the text; `audio/SCRIPT.md` lists all lines for
recording (regenerate with `node scripts/vr-audio-script.mjs lesson-01-local-habitats`). Put each
recording in `audio/<key>.mp3` and add the key to `audio/manifest.json` (a list of keys), or map
keys to hosted audio URLs (`{ "key": "https://…mp3" }`) — lessons 1 and 2 currently use Higgsfield-hosted
ElevenLabs "Benji" recordings this way; anything not recorded is
read by the browser's Arabic speech synthesis (if the device has an Arabic voice) and is always
shown in Salem's speech bubble.
