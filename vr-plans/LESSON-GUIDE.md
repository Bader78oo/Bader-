# VR lesson guide (from the version 3 feedback)

Every new lesson follows these rules on top of the lesson 1/2 engine (Salem, cards, snap-turn, voice
pipeline). They come from the user's version-3 review of lesson 2.

## 1. Models
- Childlike but detailed: big eyes with iris, pupil, two catch-lights and eyelids; noses, mouths,
  ears with inner colour; paws with toes or split hooves; tails with tufts; soft belly-to-back colour
  gradients (`Kit.add(geo, [bottom, top], …)`); `eyes2`, `limb`, `paw`, `hoof` helpers in lesson 2.
- Check every model up close with `?gallery` before shipping.

## 2. Salem
- Salem is shared. Change him in one lesson, then copy `kummaTexture`/`dishdashaTexture`/`buildSalem`
  into every lesson so he looks the same everywhere.
- Kumma: embroidered side band (medallions, borders, perforations) and a stitched crown rosette.
  Dishdasha: stitched neckline, front placket, farrakha tassel, cuffs, na'al sandals.

## 3. Arrival
- A start button (it unlocks audio, and there's a second button to enter VR directly). Then a festive
  welcome: a banner with the lesson's name, fireworks, and Salem greeting the class and naming the
  lesson (`intro` line). Only then the objectives, then exploring.

## 4. A new place every lesson (never the same setting twice)
| Lesson | Setting | Time / weather idea |
|---|---|---|
| 1 | Nizwa fort, Hajar mountains, desert and farm | midday |
| 2 | Salalah in the khareef: green hills, coconut palms, frankincense, Darbat-style waterfall, mist | sunrise / day / sunset / night button |
| next | Seeb beach (بحر السيب): waves, fishing boats, shells, crabs | sunrise, tide going out |
| | Nizwa souq (سوق نزوى): stalls, pottery, dates, goat market on Friday | morning bustle |
| | Rustaq fort (قلعة الرستاق) and its falaj | late afternoon |
| | Wahiba sands: dunes, Bedouin tent, camels | starry night |
| | Jebel Akhdar: terraces, roses, pomegranates | cool morning, clouds below |
| | Musandam fjords: dhow ride, dolphins | bright noon |
| | Sur: dhow-building yard, Ras al Jinz turtles | night with a torch |

Use what the lesson is about to pick the place (sea creatures → Seeb beach, plants → Jebel Akhdar …).

## 5. A new way to play every lesson
Each lesson keeps "explore + cards + summary" and adds at least one mechanic that earlier lessons
didn't use. Done so far: sorting into places (L1), a 40-second timer per round, growing up with a
button, counting onto a numbered row, choosing what an animal needs (L2). Ideas for next lessons:
- treasure hunt with a map and footprints to follow
- a camera: photograph the right things, then see the album
- a boat or cart ride between stations
- sound matching: hear a sound, find who made it
- building/assembling (a nest, a plant from seed to fruit)
- feeding with the controller (throw or place food)
- sorting on a moving belt (souq stall)
- day/night observation (who comes out at night?)

## 6. Counting and any arithmetic
- Objects to count stand well apart (≥ 0.6 m), never overlapping, and each counted one moves to a
  numbered spot so the row itself shows the total.
- Numbers come from `content.js` only; assert them in code against the book and against the
  recorded lines (see `console.assert` in lesson 2's counting).

## 7. Sounds
- Animals make their sounds when touched, when they're found, and when they grow up (synthesised
  with WebAudio in lesson 2 — no files to host). Add ambience: birds by day, crickets at night,
  waves at the beach, market chatter in the souq.
