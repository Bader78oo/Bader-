# VR lessons

Interactive WebXR lessons for children, built with [A-Frame](https://aframe.io) (vendored in `lib/`,
so lessons work without a CDN). Each lesson is a single static `index.html`.

| # | Lesson | Subject |
|---|--------|---------|
| 1 | [`lesson-01-local-habitats/`](lesson-01-local-habitats/) — رحلة إلى البيئات المحلية | Science, Grade 1 — local habitats |

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
   sign. Stars for first-try answers, hint after two misses.
4. **What did I learn?** — summary matching the lesson's learning outcomes, replay or free explore.

Arabic text is drawn to canvas textures (A-Frame's built-in text can't shape Arabic); animals and
plants are emoji sprites. Arabic speech uses the browser's speech synthesis when an Arabic voice exists.
