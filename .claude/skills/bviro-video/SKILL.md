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
- **Omani identity (Bader, 2026-09-26): Omani only, never Gulf/Saudi.** Men: white collarless dishdasha with the neckline tassel (farrokha), Omani mussar (patterned cashmere turban wound flat, no hanging ends) or embroidered kuma; bisht for formal. The farrokha tassel hangs at the FRONT neckline only — check back views and remove any tassel on the back (cv2.inpaint on the fabric, free). Handshakes are right hand to right hand — check every handshake/eating/giving gesture in generated clips; a mirrored clip (`"flip": true`) only fixes it when BOTH hands are wrong — check the visitor's hand too (thumb side). Safer: generate handshakes from a three-quarter side view with "BOTH men use their RIGHT hands" in the image prompt, then animate (fixed this way 2026-09-27, `w121`). Women: abaya + shayla. Places: Muttrah, Nizwa Fort, Jebel Shams, Muttrah Souq, Sur, Royal Opera House. `soul_2` without soul_id FAILS this (draws shemagh/ghutra even with negatives) — use `gpt_image_2_5` (quality medium, 1k, 0.5 credits) for people B-roll; add "NOT a shemagh, no checked headscarf, no ghutra, no agal". Finished example: `storyboards/oman-vr-promo.json` (57 s, stills only, multiple hooks/open loops, feature cards, end-card contacts).
- NEVER use `Marketing_Avatar` (e3249eb8-…) — it is not Bader; he asked for it to be deleted.
- Only Soul V2 / Soul Cinema accept a soul_id. Retraining: 15–20 unfiltered images, varied angles/expressions/light, several mid-speech frames; real phone video frames work (crop 3:4, keep sharpest via edge variance).
- Voice clone is **blocked on the Starter plan** — use Bader's own recordings (lip-synced with `wan2_7`).

## Workflow (text first, pixels last)
1. **Script + storyboard.** Agree the spoken script (≈2.2 words/sec → 20 s ≈ 40 words) and a shot list with Bader. Bader on camera ≤ 7 s; the rest is B-roll under his voice.
2. **Voice.** Bader records on his phone (m4a). Convert to mp3, then locally (`pip install faster-whisper`; first run downloads the ~1.5 GB medium model, ~1 min per 20 s of audio on CPU):
   `python3 scripts/transcribe.py voice.mp3 script.txt` → `words.json` (pass the script to fix brand spelling)
   `python3 scripts/tighten_vo.py voice.mp3 words.json --tempo 1.05 --talk A:<i>-<j> --talk B:<i>-<j>`
   → `vo.mp3`, `words_final.json`, `talk_A.mp3`… and the exact start time of each talk clip.
   **Voice polish (free, before tightening):** `ffmpeg -i voice.wav -af "highpass=f=75,afftdn=nr=8:nf=-55,equalizer=f=120:t=q:w=1:g=1.5,equalizer=f=280:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.4:g=2.5,highshelf=f=9000:g=2,deesser=i=0.35,acompressor=threshold=-22dB:ratio=3:attack=6:release=90:makeup=3,alimiter=limit=0.95" vo_enh.wav` (clarity, warmth, less mud/sibilance), then run tighten_vo on vo_enh.wav.
   Never speed speech above ~1.1×; shorten the script or accept a longer reel instead.
   **Audio guard (a silent clip once burned 15 credits):** before uploading any audio that drives lip-sync, check `ffmpeg -i x.mp3 -af volumedetect -f null -` (mean must be above −35 dB) and re-transcribe it to confirm the words. When cutting with fades, put `-ss/-t` BEFORE `-i` — with `-ss` after `-i`, `afade=...:st=` uses the original timestamps and silences the whole cut.
3. **Retouch the start still (free, local)** when Bader wants it: `scripts/retouch.py in.png out.png --slim 0.07 --skin 0.5 --eyes 0.9` (his preference 2026-09-24: slimmer cheeks, light skin smoothing, no crow's feet; centre of face protected). The video model keeps the start frame's face.
4. **Stills before video.** One `soul_2` still per on-camera angle (~1 credit each). Show Bader, get approval.
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

## Motion without new credits
Stills move for free: `depth` (2.5D parallax) per shot + `transitions` + `grade.grain` (see `references/templates.md`). Spend credits only on 4–6 hero shots as real video — cheapest image-to-video seen: `seedance_2_0_mini` 4 s 480p no audio = 2 credits (720p = 4).

## Editing without new credits
Text, timing, icons, name card, colors, LUT, music: edit the storyboard and re-run `build.py` (`--reuse-overlay` if only shots/audio changed). Only regenerate a clip when the picture itself is wrong — and quote the cost first.

## Token discipline
- Never paste base64, frame dumps or full voice lists into the conversation; use `qa_sheet.jpg` (one small frame per shot) for visual checks.
- Presigned upload URLs are ~2 KB each: request all uploads in one `media_upload` call. With ≥10 files the result is too big for the context and is saved to a tool-results JSON file — that's the cheap path: PUT every file with a short Python loop over that file (`uploads[].upload_url`, `media_id`, `content_type`) without ever printing the URLs.
- Keep this kit in the repo; edit JSON, don't rewrite scripts. Long waits: `jobs_wait` (15 s) rather than chatty polling; schedule a check-in for trainings.
- Ask for cost with `get_cost: true` before any generation and tell Bader the number.

## HyperFrames (motion graphics, Apache-2.0)
Installed by `.claude/hooks/session-start.sh` (CLI + ~20 agent skills in `~/.claude/skills/hyperframes*`). Use it for kinetic
Arabic titles, animated stickers/lower-thirds, stat count-ups and logo stings; render to MP4 (or `--format webm` for a
transparent overlay) and drop the result into a storyboard shot. Starter: `hyperframes/kinetic-title/index.html` (9:16).
Environment rules (learned 2026-09-26):
- `cdn.jsdelivr.net` is blocked: copy `vendor/gsap.min.js` next to index.html and use `<script src="gsap.min.js">`; fonts from `brand/fonts`.
- Rendering uses the preinstalled Playwright headless shell via `HYPERFRAMES_BROWSER_PATH` (set by the hook) — no `browser ensure`.
- Never put `dir="rtl"` on `<html>` (renders a blank video); put `direction: rtl` on text elements. Run `hyperframes lint` before `render`.
- A 3 s 1080×1920 title renders in ~9 s on CPU.

## Replace the background of Bader's real video (free)
1. `ffmpeg -i src.mp4 -vf fps=30 src30.mp4` then `hyperframes remove-background src30.mp4 -o fg.mov --device cpu` (~0.6 s/frame; a plain wall behind him matts cleanly).
2. Background plate: `gpt_image_2_5` medium **2k** 9:16 (1 credit), "empty, eye-level seated view, understated office, soft daylight, no people".
3. `python3 scripts/composite.py fg.mov office.png comp.mp4 --key 1.0` — erodes the matte + decontaminates edges (kills the white-wall halo), colour-matches, light-wraps, soft shadow, lens defocus, slow push.
4. Voice from the phone is quiet: run the voice-polish chain with `acompressor=threshold=-30dB:...:makeup=6,loudnorm=I=-16`; keep the original timing (lip-sync), no tightening.
5. Edit `comp.mp4` like any clip; cut to B-roll mid-sentence so he stays ≤ 7 s on screen. Example: `storyboards/intro-office.json`.

## Hook lab (first 3 seconds)
- Library + checklist: `references/hooks.md` (10 formulas × 5 sectors, opening-shot recipes).
- Score any reel: `python3 scripts/hook_score.py reel.mp4 --sb sb.json` → 0–100 + fixes (motion from frame 1, text ≤ 7 words
  by 0.5 s, sound hit at 0, face in the opening via OpenCV YuNet, a change before 3 s, visual punch). Free, local, our own code.
- Compare openings: `python3 scripts/hook_lab.py sb.json variants.json --secs 4` → `hooklab/<name>/hook.mp4`, `scores.md`,
  `compare.mp4`. Variants: `first_shot` (swap), `open_shots` (two-shot opening), `hook` (text), `sfx_add`.
  Example: `hooklab/oman-promo.variants.json` — face-first opening scored 98 vs 88 for the original (2026-09-28).
- NeuroViral (MIT) could add a second opinion, but running external code needs Bader's permission in this environment.
- Never reuse a shot across two published reels (Bader, 2026-09-28): keep a per-reel shot list and generate fresh stills/clips.
- Check the hook text at full size against faces (the scorer does not know where faces are): move `hook.top` below them.
- After posting, ask Bader for Instagram "3-second views / skip rate" and note which hook formula won in `references/hooks.md`.

## Teasers with real footage + HyperFrames scenes (2026-09-30)
- Bader's phone clips: `ffmpeg -i x.mov -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30"` (rotation is applied automatically); landscape clips → two 9:16 crops (person / screen).
- Photos must fill the 9:16 frame (Bader rejected the blurred-fill look): full-bleed crop on the subject, then `depth` push/pull or `kb` so every photo moves.
- Motion-graphic scenes (partner logos, "coming soon") are HyperFrames renders dropped in as shots: templates `hyperframes/partners-card`, `hyperframes/coming-soon`. Never animate letterSpacing on Arabic (breaks letter joins; lint flags it).
- Partner/government logos: only the files Bader sends, unchanged.
- Uploads now go to `upload.higgsfield.ai` (allowlisted for new sessions from 2026-09-30); if blocked, generate from text instead.
- Generated backgrounds invent English slogans on banners/signage — keep them out of frame (zoom) or cover with the hook text.
- Action hooks: keep a generated fall/drop ≤ 1.5 s — speed-ramp it (`setpts=PTS/2.6`) and cut on the impact.
- Teaser music: `scripts/trailer_music.py out.wav --dur 20 --hit <hook impact> --lift <logos> --build <pre-end> --final <end slam>` (heartbeat/ticks → braam → 130 BPM drive → snare build → slam); mix at about −4 dB under the sfx. Plain `music.py` beds were judged not attention-grabbing.
- Generated voice (no recording): Higgsfield `text2speech_v2` variant `elevenlabs`, preset "Arthur" (`30fc8796-ceb6-4a66-b3a7-4a145ef7f346`) — clear Arabic (Gulf/MSA, not Omani), ≈0.75 credits per 30 s; write numbers as words. `seed_audio` mangles Arabic — don't use. Microsoft's Omani voices (ar-OM-Abdullah/Aysha) need an Azure key + allowlisted host.
- Seedance may return `ip_detected` on some stills (no charge) — use a free `depth` move on the still instead of retrying.
- Lucide icons come from jsdelivr; when it is blocked, copy the SVGs into the work dir's `icons/` (e.g. from the `lucide-static` npm tarball).
- Mix rule (Bader, 2026-10-02): the voice must sit clearly above the music — speech ≈ −18 dBFS RMS, music bed ≈ −24 in intros and ducked ~11 dB under the voice. `trailer_music.py` at −6 dB buried the voice and its dark braam style was rejected; for teasers use `scripts/suspense_music.py` (calm pad/piano/pulse → soft boom at the reveal), or a licensed track Bader sends / Instagram's library.
- Key names in TTS (e.g. «إطلالة عبري»): generate them as a separate fully-vowelled line (`إِطْلَالَةُ عِبْرِي`) and keep music/sfx out from under them (duck −20 dB, no impact/shimmer on the word); check with faster-whisper on the final mix.
- Hook strategy is mandatory on every reel (references/hooks.md): moving first frame, sound at 0.0, ≤7-word promise by 0.3 s, a change before 3 s, an open loop paid off at the end. Always render 3 hook variants as 4-s clips, score them with `hook_score.py`, and send a labelled A/B/C comparison before the full render.
- Run `build.py` for different storyboards in separate folders — it writes fixed temp names (base_t.mp4, ov/, mix.wav) and parallel runs in one folder corrupt each other.
- Precision/countdown look: `hyperframes/precision-hud` (transparent MOV via `hyperframes render --format mov`, overlaid after build.py): corner countdown, crosshair, ±1 mm dimension line, big racing countdown before the reveal. Pro SFX files live in `~/.claude/skills/media-use/audio/assets/sfx/` (impact-bass, whoosh-cinematic, riser…); `scripts/precision_bed.py` mixes VO + suspense bed + clock ticks + those SFX.
- Phone numbers are written without spaces everywhere (captions, end cards): WhatsApp 96946416, Call 77721144.
- Recolour a structure (e.g. booth → Bviro purple, rest grey, neon edge trace, optional light-sweep reveal): `scripts/sam_recolor.py in.mp4 out.mp4 --ss --dur --pts "x,y;..." [--neg ...] [--scan]` — SAM 2 small ONNX on CPU (~1 s/frame), points tracked by optical flow. Works on large, clearly separated surfaces; flickers on busy wide shots (check a preview first).
- Uploads to Higgsfield work again (2026-10-03): `media_upload` + curl PUT (with `If-None-Match: *`) + `media_confirm`; then `seedance_2_0_mini` with role `start_image` for a real-frame drone/crane shot (4 credits). Use only the first ~2 s if it starts inventing signage text.
- Never name a build.py output base.mp4 / mix.wav / seg*.mp4 — those are its temp files.
