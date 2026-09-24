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

**Salem's Hub (v7)** — shared across every lesson via `lib/hub.js` and `localStorage`:
- *A growing companion*: a little falcon that hatches from an egg and grows through 4 stages as
  the child discovers more (and returns on new days). Perched near the entrance in both lessons;
  tap it to see its progress. Growing across lessons, not just within one, is the point — the
  same companion is on its perch in lesson 1 too.
- *A field journal* («دفتري 📖» from the summary panel): every animal and magic word discovered,
  as a grid of icons.
- *A portal* between lesson 1 and lesson 2 — a shimmering doorway near the fort in each lesson
  that walks the child straight into the other one, so the two feel like one connected world.
- *Sound made visible*: every 3D animal call sends out a soft golden ripple from its source.
- *Teach-back* («علّم صغيري 🎓» from the summary panel): a student puppet arrives, and the child
  teaches it by picking the right mother for 3 young — reinforcing the lesson by explaining it.
- *Hand tracking* (Quest only, untestable outside real hardware): pinch the lost young directly
  with your fingers in `lesson-02` — no controller needed — via A-Frame's `hand-tracking-controls`.

**v8 — fixes from real-headset testing:**
- *Voice reliability*: speech recognition (magic words, talk to Salem) now explicitly requests
  microphone permission before starting, and gives up with a clear spoken reason (denied /
  timed out / unsupported) instead of silently sitting "listening" forever — this was the
  reported cause of voice input doing nothing on the Quest browser.
- *Hand tracking, fixed properly*: pinching now drives the exact same click/grab pipeline as the
  controller trigger (via A-Frame's `cursor` component remapped to `pinchstarted`/`pinchended`),
  so it works on every button and panel, not just the one grabbable object it could reach before.
  Hands only render instead of the controller model once the headset stops seeing the physical
  controllers (put them down) — that switch is the Quest OS's, not this page's.
- *Games menu* («🎮 القائمة», always on screen, also offered on the welcome screen): jump straight
  into any activity — explore, who's my mother, grow up, count, the enclosure, magic words,
  teach-back, talk to Salem, the journal, the companion, the summary, or back to the start —
  without playing through everything in order.

**v9 — real fixes, not guesses, from the user's second round of headset testing:**
- *Voice still did nothing*: found the actual cause — a browser cannot show a microphone
  permission prompt while already inside an immersive VR session, so asking for it there (as
  v8 still did, the first time a mic feature was opened) just hung forever with no prompt and
  no error. Now the microphone is requested once, explicitly, at the "ابدأ الرحلة" tap — while
  still flat, before entering VR — so the OS prompt can actually appear; and the request itself
  now has a hard 5-second timeout so a prompt that genuinely can't appear (e.g. a mic feature
  opened without ever having primed it) fails fast with a spoken reason instead of hanging.
  Verified with a mocked `getUserMedia`/`SpeechRecognition` end to end (mic tap → recognized
  word → it appears) and with a `getUserMedia` promise that never resolves (times out in ~5s
  with the friendly `micDenied` line, instead of hanging).
- *Hands appeared but couldn't move or grab*: two real bugs. (1) Walking was built entirely
  around a controller's thumbstick, which a bare hand doesn't have — there was no way to move
  at all with hand tracking. (2) Grabbing was wired through the same long-range pointing ray a
  controller uses, but a bare hand doesn't aim as precisely as a controller is shaped to, so the
  ray rarely landed on anything — and carrying an object entirely depended on that ray, so even
  a successful grab couldn't be moved. Replaced with near-field touch: pinch near an object to
  grab or press it (works for every button and panel, not just one hardcoded object); pinch in
  empty air to walk to wherever you're looking; while carrying something, it now follows the
  hand's own position directly instead of a ray. Cannot be verified beyond this without real
  hand-tracking hardware — needs the user's next real test.

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
