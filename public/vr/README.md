# VR lessons

Interactive WebXR lessons for children, built with [A-Frame](https://aframe.io) (vendored in `lib/`,
so lessons work without a CDN). Each lesson is a single static `index.html`.

| # | Lesson | Subject |
|---|--------|---------|
| 1 | [`lesson-01-local-habitats/`](lesson-01-local-habitats/) — رحلة إلى البيئات المحلية | Science, Grade 1 — local habitats |
| 2 | [`lesson-02-young-animals/`](lesson-02-young-animals/) — صغير الإنسان وصغير الحيوان | Science, Grade 1 — young humans and young animals |
| 3 | [`lesson-03-sunken-ship/`](lesson-03-sunken-ship/) — سفينة مسقط الغارقة | Science, Grade 1 — a sunken ship as a marine habitat |

Standalone experiences (not tied to a numbered Grade-1 lesson):

| Experience | Theme |
|---|---|
| [`omani-garden/`](omani-garden/) — ازرع واحصد الثمرة | A small Omani nursery: plant and care for 4 crops (tomato, strawberry, Omani lemon, apple) through 6 growth stages, with Salem |

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
  hand's own position directly instead of a ray.

**v10 — from the user's third round of testing, hands now render but couldn't move/select/grab:**
- *Voice still silent after granting the permission*: the mic permission itself now works (the
  v9 fix), but the underlying speech-recognition *service* may simply not be available on the
  Quest browser at all — that's a platform limitation, not something fixable from this page.
  So: timeouts are now much shorter (≈6.5s max instead of 10s), and after any one real failure
  (not a menu-driven cancel) voice is disabled for the rest of the session — the mic button and
  its instructions disappear, the panel goes straight to "الصوت غير متاح، جرّب الأمثلة", so the
  child isn't left repeatedly trying something that plainly won't work on their device. The
  guaranteed-to-work path (tapping a word chip) was always there and remains the default.
- *Hands moved but couldn't turn or reach the menu*: two more real gaps. (1) Turning (snap-turn)
  was thumbstick-only, same problem walking had — a bare hand has no thumbstick, so there was no
  way to turn at all. Added two touchable buttons (↩️/↪️) always on screen. (2) Menus and panels
  are shown ~2–3 m in front of the child — far outside any hand's near-field reach, so v9's
  touch-only interaction could never reach them (this was the "no pointer/cursor to reach the
  choices" the user reported). Added a head-gaze pointer: a small dot fixed at the centre of the
  view (a 3D object riding on the camera — an HTML overlay can't render inside an immersive WebXR
  session) that lights up over anything interactive the child is looking at; a pinch confirms it,
  from any distance.
- *Couldn't grab the young: "my hand goes straight through it"*: correct diagnosis, but the fix
  isn't collision (a bare hand can't be physically stopped by a virtual object without haptic
  gloves — no WebXR app can do that) — it's detection range. Grab range was a small radius from
  one centre point, too tight and too exact for a hand that isn't tracked with pinpoint accuracy.
  Widened it and switched to measuring from the object's full bounding box, not just its centre,
  and the object now glows softly once a hand is close enough to grab it, before the child pinches.

Verified end to end in the automated check: the rotation buttons turn the rig exactly 30°, a
real recognition failure flips voice off for the rest of the session, an empty-air pinch walks
the child, a gaze+pinch on a menu tile ~2.5 m away opens that activity, and a hand placed at the
lost young's position grabs it and carries it along as the hand moves — all pass clean. Still
needs the user's real headset for what none of this can simulate: actual hand tracking.

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

## Lesson 3 — سفينة مسقط الغارقة (the sunken ship)

Built on the same engine as lessons 1–2 (Kit models, Salem, showPanel, hub.js, snap-turn, near-field
+ gaze hand tracking), following [`vr-plans/LESSON-GUIDE.md`](../../vr-plans/LESSON-GUIDE.md): a new
place (underwater, off Muscat's coast — sand, rocks, coral clusters, swaying kelp, light shafts from
above, rising bubble particles, `THREE.FogExp2` for underwater depth) and new mechanics not used
before: walking into an enclosed interior space (the wreck's hull), a multi-select "who lives here?"
habitat activity, and grabbing a prop (the captain's bottle) and carrying it to Salem to unlock a
bonus line, reusing the existing `grabbable`/`carryStep` system with a single grab target instead of
lesson 2's per-round one.

Flow: festive arrival (bubbles instead of confetti) → descend to the seabed → the ship emerges from
the fog → free exploration of six glowing hotspots on and around the hull (each with a Fusha fact
line) → enter the ship (dimmer interior, a moray eel and an octopus to find, the grabbable bottle) →
the habitat activity (pick the five sea creatures that live in/around the ship from a set that also
includes land-animal distractors) → a 3-question quiz (reusing the `makeStage`/`stageCard` stage
engine, not lesson 2's teach-back pupil) → "what did I learn?" summary. Salem wears a simple diving
mask + snorkel (added as an extra `Kit` shape on his existing head, so `buildSalem` itself didn't
need to change) instead of redesigning the character. The falcon companion and field journal
(`hub.js`) carry over from lessons 1–2 unchanged, since they're meant to be the same growing
companion across the whole site; magic-words voice-summon and the "ask Salem" AI chat panel were
left out of this lesson — the user's real-Quest testing on lesson 2 found speech recognition
unreliable on that browser, and this lesson's spec didn't call for them. A portal was added in both
directions: lesson 2 now also links to lesson 3 (`buildPortal` there was given an `angle` parameter
so a second doorway could be placed without overlapping the existing lesson-1 one), and lesson 3
links back to lesson 2.

Verified end to end with the `?test` hooks and a Playwright run: intro → welcome → descend → all six
hotspots discovered → auto-enter the ship → both interior creatures found → bottle grabbed and
carried to Salem → exit → all five habitat creatures picked correctly → all three quiz questions
answered → summary, then the level menu and the portal to lesson 2 — zero console/page errors across
the full run. One real bug caught this way: the habitat activity's panel entity was left assigned to
the shared `panel` variable after being torn down, so opening the next panel (the quiz intro) called
`.remove()` on an already-detached element and crashed — fixed by clearing `panel` when the habitat
activity closes.

## ازرع واحصد الثمرة (OmaniGarden) — a standalone experience

Not a numbered Grade-1 lesson: a self-contained nursery experience, requested as a web-VR
reimplementation of a Unity/Blender prototype spec (`vr-plans/omani-garden-brief.md` has the full
translation table and the corrections made after reviewing the user's reference video/photos).
Built on the same engine as the lessons (Kit models, Salem, canvas UI, hub.js, voice pipeline), but
reusing **lesson 1's exploration mechanic** rather than lesson 2/3's walking: the child never moves
at all, only turns in place (`snap-turn` / on-screen ↩️/↪️ buttons) and reaches every pot with a
long-range raycaster, exactly like lesson 1's habitat zones.

Setting: a walled Omani courtyard nursery — mud-brick crenellated walls with an arched gate, date
palms, a stone-bordered falaj channel, a tools table with four colour-coded seed bowls, a trowel and
a rake, and an arc of four large terracotta pots, each starting at a different growth stage (matching
the reference video, which showed pots already at mixed stages rather than all starting from seed).

Flow: welcome → **Mission 1: explore** (touch each pot to hear what it is and see its current stage;
goal: discover all 4) → **Mission 2: care** (6 rounds; for each round's pot, pick the correct one of
water 💧 / sun ☀️ / soil 🌱 — right answers advance that pot's growth stage) → any pot that reaches
stage 6 ("ثمار ناضجة") becomes harvestable — touching it moves its fruit into the wicker basket → "what
did I learn?" summary, which calls out that trees (lemon, apple) take longer to fruit than vegetables
(tomato, strawberry) — by design the 6 care rounds are weighted so only the two vegetables actually
reach harvest, the two trees only advance partway, making that point visible rather than just stated.

Two new model builders were added for this lesson's own content: `bushPlant()` (soil + stem + leaves,
gaining flowers at stage 5 and fruit at stage 6) and `potTree()` (trunk + sampled canopy leaves, same
flower/fruit gating) — both driven purely by a stage number, so growing a plant is just rebuilding its
model at a new stage rather than animating anything. `buildSalem`/`kummaTexture`/`dishdashaTexture`,
the canvas-card UI, the voice pipeline and `hub.js` (companion + journal) are all copied verbatim from
the lessons, unchanged, so Salem and the companion stay the same character across the whole site; a
one-way portal links back to lesson 1.

One real bug caught during testing: the ground was initially built from a low-subdivision
`CircleGeometry` (16 radial segments, no ring subdivisions), which — like the same mistake lesson 1's
own code had already been fixed for — produces a few huge wedge triangles from the centre to the
edge that pass under the camera and z-fight badly on some GPUs; the whole scene except Salem appeared
to vanish behind a corrupted tan horizon. Fixed by switching to a finely tessellated `PlaneGeometry`,
matching lesson 1's existing fix. Verified end to end with the `?test` hooks and Playwright
screenshots: all 4 pots discovered, all 6 care rounds answered correctly in sequence advancing the
right pots' stages, both ripe pots harvested into the basket, summary panel reached — zero console
errors in the final run.

**Opened up into a real farm, from the user's "the farm feels incomplete" feedback:** the courtyard's
full enclosing wall (which made the whole experience read as a small walled yard) is now a single
standalone archway; two loose rings of palms, a scatter of orchard trees, a hazy ring of hills on the
horizon and scene fog surround the child instead, so they stand in the middle of a farm among palms
and trees rather than inside a box. The falaj gained a second branch and a small footbridge. Pots now
have a real painted-clay texture; plant leaves are built from thin flat blades (the same technique the
palm fronds already used) instead of round blobs, and the potted trees have a banded bark trunk and a
canopy of leaf-blade clusters scattered over a sphere for a fuller, leafier silhouette instead of a
spiky starburst. Render cost checked against lesson 1 (≈207k triangles / 64 draw calls here vs. ≈102k /
78 there) — comfortably within a standalone headset's budget.

A full Playwright run of the care mission caught two real bugs this pass missed before: the care
round's answer chips are shuffled on screen each round, but the `?test` hook assumed a fixed
water/sun/soil order, so it silently answered the wrong chip after the first round — fixed by tagging
each chip with its need id. That fix then exposed a second, real content bug underneath it: strawberry
started too early (stage 2) for its two care rounds to ever reach stage 6, so it could never actually be
harvested — contradicting the lesson's own closing line that both vegetables ripen. Fixed by starting
it one stage further along.

**Replaced the abstract water/sun/soil quiz with the child actually planting, from the user's
"I want the child to be the one who plants" feedback:** every pot now starts completely empty — no
pre-grown stage. The child goes to the tools table, equips a tool by clicking it (trowel, a seed from
one of the four bowls, or the new orange watering can — a small on-screen label shows what's in hand),
then clicks a pot to use that tool there, in order: dig, plant, water. Watering starts real-time growth:
each pot now advances through the 6 named stages on its own, once every 6 seconds for the vegetables
and every 9 for the trees (so "trees take longer" is something the child watches happen, not just a
line they're told), with a small floating label over each pot naming its current stage. A ripe pot
(stage 6) is harvested the same way as before — touch it to move its fruit into the basket. The four
pots can be planted in any order and grow in the background while the child keeps exploring — nothing
blocks on a single pot. The old discover-by-touch mission is gone; each plant's fact line is now said
the moment its seed goes in, and the two-mission "explore then quiz" structure collapses into one
plant-then-watch flow, matching the user's explicit interaction-style choice: point-and-click
equip-then-use rather than full pick-up-and-carry grab physics.

Three lines whose text changed for the new mechanic (`m1`, `half`, `m1done`) were re-recorded through
the same Higgsfield pipeline, same Benji voice, as every other lesson; the rest of the voice lines
carried over unchanged since their wording still fits. Verified end to end: dig→plant→water all 4 pots
in any order, growth advances on its own over real time, harvesting all 4 once ripe, zero console
errors, and render cost actually dropped slightly (pots start empty) to ≈151k triangles / 59 draw
calls.

**Follow-up fixes from the user's first hands-on test:** the tools table moved from an awkward
behind-left position to directly in front of the child, just closer than the pot ring, so every tool
is reachable without turning. Each seed bowl now shows a little scatter of seed shapes (round reds for
tomato, pale pips for strawberry, yellow pips for lemon, brown pips for apple) instead of a plain disc.
Every pot now shows real dark soil inset just under its rim (previously the inside just looked like
more clay), and the whole pot is raised slightly off the ground so it reads as sitting on the sand
rather than sinking into it. The falaj dropped its diagonal side-branch, which crossed the main channel
at an untidy angle — it's a single straight channel with one footbridge now. Added a live growth
countdown: the moment a pot is watered, a floating label above it starts counting down the seconds left
until harvest (6s/stage for vegetables, 9s/stage for trees, so the "trees take longer" point is a number
the child can watch tick down, not just a label). Caught one more real bug while wiring the countdown up:
the on-screen "what to do next" hint was read before the just-used tool was cleared from the child's
hand, so right after watering a pot it would still say "touch the pot to water it" instead of the
correct "pick up a tool" — fixed by clearing the held tool before refreshing the hint, not after.

**Two more real-headset-video bugs, fixed the same way (watch → diagnose → fix → re-verify):** the
tools table's rotation had been tuned for its old behind-left position and was never re-derived when
it moved to straight-ahead, so on the real headset it ran away from the child lengthwise instead of
sitting broadside — fixed with rotation 0. Separately, the pot's clay body was a *closed* cylinder, so
its solid top cap sat right over the soil disc and still hid it — fixed by making the body open-ended
(with a small interior floor so it doesn't look hollow from a low angle). A third video then showed the
welcome/mission panels (which always open ~2.2m in front of wherever the child is facing) clipping
straight through the table, which had been moved to only 2.1m away — fixed by moving the table to 3.8m,
past the pot ring and safely past every panel's render distance.

**More interactive growth, a tool-use guide, no falcon, and a basket beside the child** — from the
user's next round of feedback (two more real-device videos):

- Every pot now pauses once, partway through growing (at stage 3), and needs a second watering to
  keep going — so the growing period itself is something the child does, not just something they
  wait out. A floating label switches to "needs watering to continue" and the watering can glows
  again until they water it.
- A soft glowing marker now hovers over whichever tool is actually needed — the trowel while any pot
  still needs digging, the seed bowls once it's dug, the watering can once it's seeded (and again if
  a pot pauses mid-growth) — so the child has a visual guide to follow instead of relying only on the
  HUD text.
- Removed the growing falcon companion from this experience entirely (per the user's explicit "احذف
  الصقر") — it was a cross-lesson feature inherited from `hub.js` that didn't fit a standalone
  planting experience. The field journal (discovery tracking) stays; only the bird and its perch are
  gone.
- Added a harvest basket right beside where the child stands (not out at the pots or the tools
  table), and harvesting now animates a small colored dot flying from the pot into the basket instead
  of just popping an info card — "collect the fruit" reads as an actual action. Because the basket
  sits at ground level close to the child while the default view looks straight ahead at eye height,
  it's naturally just below the resting view (the same way a real basket by your feet would be) — the
  welcome panel's text was given a one-line nudge ("look down a bit, it's beside you") rather than
  moving the basket somewhere that reads as less "beside" the child.

Verified end to end via Playwright: tool glows appear/disappear exactly when expected, the stage-3
re-water pause triggers and clears correctly, harvest's fly-to-basket animation runs, the falcon's
removal leaves no dead code path, zero console errors.

**More detail and real tool-use animations**, from the next round of feedback (a close-up photo and a
video of the still fairly plain basket/pot/tool interactions):

- The basket got a proper woven texture (reusing the clay-texture technique) instead of flat vertex
  colors, plus a rim band and smoother geometry (16→28 radial segments). Harvested fruit no longer
  disappears after the fly-in animation — each one settles into a visible spot inside the basket and
  stays there, so the pile grows with every harvest.
- Every empty pot now shows a dashed circular "plant here" marker with a crosshair on the soil,
  visible only until it's dug — a direct visual answer to "where do I plant."
- Using the trowel now spawns a real trowel model that dips down and scoops at the pot instead of
  just a sound and a particle puff. Using the watering can (both the first time and for the mid-growth
  re-water) spawns the can tipped over the pot with real blue water drops falling and fading into the
  soil.
- The trowel was factored out of the tools table into its own reusable `trowelModel()` (the watering
  can already was one) so both animations could spawn independent copies at the pot without disturbing
  the one sitting on the table.

**Official branding, seed labels, a farm identity for the welcome, and a Salem/table collision
fix** — a further round of polish requested with the ministry's own logo lockup (government of
Oman emblem + the ministry name, alongside a project logo):

- Added that logo (extracted from the supplied PDF, trimmed, background made transparent) as a
  camera-fixed overlay in the upper right, visible both on screen and inside the headset, never
  blocking the main view.
- Salem now has a proper title ("الْمُرْشِدُ الزِّرَاعِيُّ") and the welcome screen names the farm by
  name — "مزرعة عبري" in محافظة الظاهرة — supervised by the Ministry of Agricultural Wealth,
  Fisheries and Water Resources. Salem's own `hello` line was reworded (and re-recorded) to
  introduce himself with that same context instead of the generic "Omani nursery" framing.
- Each seed bowl now has a small name card hovering over it (icon + crop name), so the child isn't
  guessing which bowl is which before picking one up.
- Fixed a real placement bug: `salemBeside()` only ever positioned Salem relative to whichever
  panel was open, with no awareness of the tools table's own location — depending on the panel's
  width and the child's facing direction, Salem could end up standing on top of or inside the
  table. Fixed by tracking the table's world position and repelling Salem's target spot away from
  it whenever it would land too close.

Verified via Playwright by tracking the scene graph's child count through each action (mesh added
mid-animation, cleaned back up afterward — not pixel-diffing screenshots, since getting the headless
camera angle to exactly frame a specific pot had been unreliable in earlier rounds): dig, water and
harvest all add and correctly clean up their temporary meshes, the harvested fruit persists as
expected, zero console errors throughout.

Verified this pass with screenshots: the logo renders cleanly with no white box, the welcome panel
and Salem's spoken line both carry the new farm/ministry framing, every bowl shows its crop name, and
Salem stands clearly beside the table rather than inside it. Full regression suite still clean.
