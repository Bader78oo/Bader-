---
name: bviro-video
description: Produce Bviro (بيفيرو) Instagram reels/ads with Bader's digital twin on Higgsfield — storyboard, voice-over tightening, word-synced Arabic captions, icons, name card, checklist, logo end card, grading and sound — at the lowest Higgsfield-credit and token cost. Use for any Bviro video, reel, ad or social clip.
---

# Bviro video pipeline

Everything below was proven on the "VR in Omani education" reel (`storyboards/edu-vr-oman.json`).
Reply to Bader in Gulf Arabic. Brand data: `brand/brand.json` (colors, tagline, values, founder card).

## Fixed IDs
- Soul v1 "بدر الريسي": `soul_id 50e0dfad-e7d5-4904-8d3d-46277ee3e7a7` — 5 filtered car selfies; faces drift, skin looks plastic.
- Soul v2 "بدر الريسي v2": `soul_id c8d2cf32-535a-49ac-8681-455a1392aee8` — v1 photos + 15 frames from real talking videos (kuma cap, gestures, open mouth, head tilts, 4 face close-ups). DEFAULT since 2026-09-24: adaptation test showed real skin texture and much closer likeness than v1 (close-up, 3/4, talking, outdoor 8–9/10; stage 7; full-body 5 — face too small, outfit invented).
- Soul prompt rules (v2): write the headwear exactly — "small round white embroidered Omani kuma cap (not a turban)" or "traditional embroidered Omani massar turban"; v2 mixes the two otherwise. Prefer close/medium shots; for full body say "ankle-length white dishdasha, sandals". Add "no text, no signage" — backgrounds invent gibberish lettering; put real text in the overlay.
- NEVER use `Marketing_Avatar` (e3249eb8-…) — it is not Bader; he asked for it to be deleted.
- Only Soul V2 / Soul Cinema accept a soul_id. Retraining: 15–20 unfiltered images, varied angles/expressions/light, several mid-speech frames; real phone video frames work (crop 3:4, keep sharpest via edge variance).
- Voice clone is **blocked on the Starter plan** — use Bader's own recordings (lip-synced with `wan2_7`).

## Workflow (text first, pixels last)
1. **Script + storyboard.** Agree the spoken script (≈2.2 words/sec → 20 s ≈ 40 words) and a shot list with Bader. Bader on camera ≤ 7 s; the rest is B-roll under his voice.
2. **Voice.** Bader records on his phone (m4a). Convert to mp3, then locally (`pip install faster-whisper`; first run downloads the ~1.5 GB medium model, ~1 min per 20 s of audio on CPU):
   `python3 scripts/transcribe.py voice.mp3 script.txt` → `words.json` (pass the script to fix brand spelling)
   `python3 scripts/tighten_vo.py voice.mp3 words.json --tempo 1.05 --talk A:<i>-<j> --talk B:<i>-<j>`
   → `vo.mp3`, `words_final.json`, `talk_A.mp3`… and the exact start time of each talk clip.
   Never speed speech above ~1.1×; shorten the script or accept a longer reel instead.
   **Audio guard (a silent clip once burned 15 credits):** before uploading any audio that drives lip-sync, check `ffmpeg -i x.mp3 -af volumedetect -f null -` (mean must be above −35 dB) and re-transcribe it to confirm the words. When cutting with fades, put `-ss/-t` BEFORE `-i` — with `-ss` after `-i`, `afade=...:st=` uses the original timestamps and silences the whole cut.
3. **Stills before video.** One `soul_2` still per on-camera angle (~1 credit each). Show Bader, get approval.
4. **Clips — only approved shots** (see `references/higgsfield.md` for models, costs, gotchas):
   - B-roll: `kling3_0`, `mode: std`, `sound: off`, `duration: 5`, `aspect_ratio: 9:16`, text-to-video.
   - Talking: `wan2_7`, start_image = approved still, `audio_references` = `talk_X.mp3`, `duration: 4`, 720p.
     Clip audio starts at t=0 of the talk mp3 → place the shot at the printed start time.
   - Submit with `generate_video_batch`, max **2 concurrent** jobs on Starter (else 429).
5. **Storyboard JSON.** Start from a template in `storyboards/templates/` (talking-head, broll-explainer, event-promo — see `references/templates.md` for fields and the B-roll prompt library); `storyboards/edu-vr-oman.json` is a finished example. Shot durations must sum to `duration`. Use `grade.lut: "brand/bviro_look.cube"` for the house look, `zoom` for free punch-in angles, and still images with `kb` (Ken Burns) instead of paid video where motion isn't essential.
6. **Render locally when possible** (fastest, no upload tokens): needs `ffmpeg` (`apt-get install -y ffmpeg`), node + playwright (preinstalled in Claude Code cloud), and the environment's network allowlist to include `d8j0ntlcm91z4.cloudfront.net` + `d2ol7oe51mr4n9.cloudfront.net` (Higgsfield media). Put clip URLs in the storyboard (`shots[].url`, `assets`) and run
   `python3 .claude/skills/bviro-video/scripts/build.py sb.json --qa` from a scratch dir (~1 min for 15–20 s). Hand the MP4 to Bader with SendUserFile.
   **Fallback — Higgsfield sandbox** (has ffmpeg, node+playwright, faster-whisper):
   `bash scripts/pack.sh storyboards/<name>.json /tmp/kit.tgz` → `media_upload` (file) → local `curl PUT` → `media_confirm`.
   In ONE `sandbox_exec` (background:true): `curl <kit url> | tar xz && cd kit && python3 scripts/build.py sb.json --qa && curl -X PUT --upload-file final.mp4 '<video upload_url>'`.
   Call `media_upload` for the output **before** starting the command. Then `media_confirm`.
7. **QA before delivery.** Run `scripts/lipsync_score.py clip.mp4 voice.mp3` on every talking clip (mouth-vs-voice correlation, lag, face drift, camera push-in). Look at frames yourself (contact sheet of 5–9 frames at 240 px, then full-res crops of any caption that looks off — downscaled Arabic can look garbled when it isn't). Check: text never covers the face (keep overlays in y≈700–1030 under a face), no two overlay blocks at once, lip-sync offset 0 ms (cross-correlate clip audio vs talk mp3), loudness ≈ −14 LUFS with voice (≈ −18 pad-only). Deliver via SendUserFile, or the `d2ol7oe51mr4n9.cloudfront.net/...` link with phone download steps.

## Editing without new credits
Text, timing, icons, name card, colors, LUT, music: edit the storyboard and re-run `build.py` (`--reuse-overlay` if only shots/audio changed). Only regenerate a clip when the picture itself is wrong — and quote the cost first.

## Token discipline
- Never paste base64, frame dumps or full voice lists into the conversation; use `qa_sheet.jpg` (one small frame per shot) for visual checks.
- Presigned upload URLs are ~2 KB each: request all uploads in one `media_upload` call. With ≥10 files the result is too big for the context and is saved to a tool-results JSON file — that's the cheap path: PUT every file with a short Python loop over that file (`uploads[].upload_url`, `media_id`, `content_type`) without ever printing the URLs.
- Keep this kit in the repo; edit JSON, don't rewrite scripts. Long waits: `jobs_wait` (15 s) rather than chatty polling; schedule a check-in for trainings.
- Ask for cost with `get_cost: true` before any generation and tell Bader the number.
