# Higgsfield notes (measured on the Starter plan, Sept 2026)

## Costs seen
| Generation | Credits |
|---|---|
| `soul_2` still (2k) | 0.12 (shown as "1" in get_cost; balance confirms 0.12) |
| `kling3_0` std, 5 s, sound off, 9:16 | 6.25 |
| `kling3_0` std, 10 s, sound on | 17.5 |
| `kling3_0` pro | blocked — needs Plus |
| `wan2_7` 720p 5 s with audio reference (preflight) | 7.5 (real 4 s runs cost more — whole edu reel spent ~63 vs ~45 estimated; always preflight) |
| `wan2_7` 1080p 5 s | 12.5 |
| `seedance_2_5` 10 s 1080p / 720p | 120 / 70 |
| `grok_video_v15` 10 s 720p | 45 |
| `minimax_h3` 10 s | 20 |
| Soul training | v1 (5 photos): no charge seen · v2 (20 photos): **25 credits**; ~15–25 min wall time |

Rules: preflight with `get_cost: true`; draft low-res, final hi-res; B-roll `sound: off`; 5 s clips and cut; stills + Ken-Burns in the overlay instead of video where motion isn't essential; reuse the B-roll library across ads.

## Talking-head benchmark (lipsync_score.py, 2026-09-24)
| Clip | corr | lag | face_drift | face_scale_change |
|---|---|---|---|---|
| Bader real phone video (reference) | 0.12–0.25 | ±217 ms | 5.4% | 10–12% |
| v1 Wan 2.7 720p, "slow dolly-in" prompt | 0.19–0.35 | +200–300 ms | 5.8–6.3% | 45–81% |
| **v2 Wan 2.7 1080p, static-camera prompt, natural-speed audio** | 0.19 | **+33 ms** | 5.8% | **11%** |
Winning recipe: v2 still (chest-up, mouth closed, "no text"), audio at natural speed (no atempo), 6 s, 1080p (15 credits),
prompt = precise lip sync + natural blinking + small nods + "static locked-off tripod camera: no zoom, no dolly" + "no exaggerated smile".
corr from mouth-gap vs loudness is noisy even on real footage — compare against the real-video baseline, and always look at a mouth-crop strip.

## Gotchas
- **Concurrency**: Starter caps at 4 concurrent jobs total (images count too) and in practice runs ~2 video jobs at once; extra submits fail with 429 `rate_limit_reached`. Queue them.
- **Preset interception**: `generate_video_batch` may answer "Preset X was recommended" instead of submitting — resubmit with `declined_preset_id`.
- **Aspect**: `soul_2` has no 4:5 (uses 3:4). Kling/Wan take 9:16. A 3:4 start image gets cropped to 9:16 — generate 9:16 stills for video.
- **Voice clone**: `create_voice_from_confirmed_audio` → "Voice limit reached" on Starter even with zero voices.
- **Audio upload**: `media_upload` of `.m4a` returns an `.mp3` slot — convert to mp3 first (ffmpeg).
- **Network (fixed 2026-09-24):** Bader's cloud environment now uses Custom network access with `d8j0ntlcm91z4.cloudfront.net` and `d2ol7oe51mr4n9.cloudfront.net` allowed, so Higgsfield media downloads and local rendering work. `huggingface.co`, `*.huggingface.co`, `*.hf.co` are allowed too, so Whisper transcription runs locally. `cdn.jsdelivr.net` is NOT allowed — icons and the Cairo font are vendored in the kit.
- `sandbox_exec` stdout is truncated around 18 KB, so images can't be pulled through it for review (tried with base64). Visual QA needs the cloudfront allowlist above.
- Sandbox is discarded ~10 s after a call: chain download → build → upload in one command; long work with `background: true`, poll the log.
- `transcribe.py` output needs a glance: Whisper can hallucinate words into the trailing silence (the script drops anything after the last speech, found with silencedetect).

## Open-source upgrades worth adopting (see plan in chat, 2026-09-24)
- HyperFrames (Apache-2.0) — HTML→MP4 with 21 agent skills; natural successor to `overlay.html`.
- WhisperX — sharper word alignment than faster-whisper.
- lutgen-rs / `lut3d` — a Bviro `.cube` LUT for consistent grading (`grade.lut` in the storyboard).
- DeepFilterNet — clean phone recordings before transcription.
- ACE-Step 1.5 (GPU) — real background music (`audio.music` in the storyboard).
- Video2X (GPU) — upscale 720p finals to 1080p instead of paying for 1080p generations.
