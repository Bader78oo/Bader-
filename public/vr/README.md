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

Built from lesson 1's engine (same Salem, cards, snap-turn and voice pipeline) in an Omani family
wildlife park. Seven enclosures surround the child, each with a parent and its young: lion and cub
(الشبل), elephant and calf, she-camel and حوار, goat and جدي, a duck with eight ducklings, a rabbit
with nine young, and an Omani mother with her baby in a cradle.

1. **Welcome** — objectives and vocabulary (صغير، الإنسان، الشبل، طفل).
2. **Mission 1: Meet the young** — touch each young (or its parent / sign) to hear its name, what it
   becomes when it grows up, and how many young are born at a time.
3. **Mission 2: Who is my mother?** — a lost young appears; the child points at its mother or her
   sign. Five rounds, stars for first-try answers, hint after two misses.
4. **Mission 3: The young grow up** — press «كبّره!» to watch a cub become a lion, a حوار become a
   camel, and a baby become a boy and then an adult.
5. **Mission 4: Count the young** — count eight ducklings, nine young rabbits and the mother's one
   baby, then compare.
6. **Mission 5: An enclosure for the kid** — choose food, water and shelter for the جدي; toys and
   sweets are politely refused.
7. **What did I learn?** — summary matching the book's «ماذا تعلمت», replay or free explore.

`?gallery` lines up all of lesson 2's models; `?test` exposes hooks used by the automated flow check.

## Voice

Every spoken line has a key. `content.js` holds the text; `audio/SCRIPT.md` lists all lines for
recording (regenerate with `node scripts/vr-audio-script.mjs lesson-01-local-habitats`). Put each
recording in `audio/<key>.mp3` and add the key to `audio/manifest.json` (a list of keys), or map
keys to hosted audio URLs (`{ "key": "https://…mp3" }`) — lessons 1 and 2 currently use Higgsfield-hosted
ElevenLabs "Benji" recordings this way; anything not recorded is
read by the browser's Arabic speech synthesis (if the device has an Arabic voice) and is always
shown in Salem's speech bubble.
