#!/usr/bin/env python3
"""Score the hook (first 3 s) of a reel — local, free, explainable. Our own heuristic, built on what
short-form research and platform guidance agree on: the first frame must already move, a readable
promise must be on screen within ~0.5 s, sound must hit immediately, a face or a clear subject helps,
and the opening must be visually punchy (contrast / saturation) with at least one change before 3 s.

Usage: python3 hook_score.py video.mp4 [--sb sb.json] [--json out.json]
  --sb   storyboard: lets it read the hook text/time exactly instead of guessing
Prints a 0-100 hook score, the components, and concrete fixes.
"""
import argparse, json, os, subprocess

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("--sb"); ap.add_argument("--json")
ap.add_argument("--window", type=float, default=3.0)
a = ap.parse_args()
WIN = a.window

# ---- frames of the first WIN seconds (analysed at 10 fps, 270 px wide) -------------------------
cap = cv2.VideoCapture(a.video); fps = cap.get(cv2.CAP_PROP_FPS) or 30
step = max(1, round(fps / 10)); frames, i = [], 0
while i < WIN * fps:
    ok, f = cap.read()
    if not ok: break
    if i % step == 0:
        frames.append(cv2.resize(f, (270, int(270 * f.shape[0] / f.shape[1]))))
    i += 1
cap.release()
g = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames]
diffs = np.array([np.mean(np.abs(g[k] - g[k - 1])) for k in range(1, len(g))]) if len(g) > 1 else np.zeros(1)
motion_first = float(diffs[:5].mean()) if len(diffs) else 0.0          # first 0.5 s
motion_all = float(diffs.mean())
cuts = int((diffs > 28).sum())                                            # hard changes (cuts / flashes)

f0 = frames[0]; hsv = cv2.cvtColor(f0, cv2.COLOR_BGR2HSV)
contrast = float(g[0].std()); saturation = float(hsv[..., 1].mean()); brightness = float(hsv[..., 2].mean())

# ---- face in the opening (OpenCV YuNet, good on small faces; ~6 frames at 720 px) ------------
face_area = 0.0
try:
    model = os.path.expanduser("~/.cache/yunet/face_detection_yunet_2023mar.onnx")
    if not os.path.exists(model):  # Apache-2.0 model from the OpenCV zoo, mirrored on Hugging Face
        import shutil
        from huggingface_hub import hf_hub_download
        os.makedirs(os.path.dirname(model), exist_ok=True)
        shutil.copy(hf_hub_download("opencv/face_detection_yunet", "face_detection_yunet_2023mar.onnx"), model)
    cap = cv2.VideoCapture(a.video); det = None
    for t in np.linspace(0, WIN - 0.1, 6):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
        if not ok: continue
        fr = cv2.resize(fr, (720, int(720 * fr.shape[0] / fr.shape[1])))
        if det is None: det = cv2.FaceDetectorYN.create(model, "", (fr.shape[1], fr.shape[0]), 0.7)
        _, faces = det.detect(fr)
        for fc in (faces if faces is not None else []):
            face_area = max(face_area, float(fc[2] * fc[3]) / (fr.shape[0] * fr.shape[1]))
    cap.release()
except Exception as e:
    print("face check skipped:", e); face_area = -1.0

# ---- audio: how fast the first sound / hit arrives -------------------------------------------
raw = subprocess.run(["ffmpeg", "-v", "error", "-t", str(WIN), "-i", a.video, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True).stdout
au = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
win = 160  # 10 ms
rms = np.array([np.sqrt(np.mean(au[k:k + win] ** 2) + 1e-12) for k in range(0, max(len(au) - win, 1), win)])
db = 20 * np.log10(rms + 1e-9)
loud = np.where(db > -35)[0]
t_sound = float(loud[0] * 0.01) if len(loud) else WIN
hit = float(db[:30].max()) if len(db) else -90                           # peak in first 0.3 s

# ---- hook text (from the storyboard when given) ----------------------------------------------
t_text, n_words, hook_text = None, None, ""
if a.sb:
    sb = json.load(open(a.sb, encoding="utf-8"))
    hooks = sb["hook"] if isinstance(sb.get("hook"), list) else ([sb["hook"]] if sb.get("hook") else [])
    first = min(hooks, key=lambda h: h["s"]) if hooks else None
    if first and first["s"] < WIN:
        t_text = first["s"]; hook_text = (first["text"] + " " + first.get("sub", "")).strip()
        n_words = len(hook_text.split())
    caps = [c for c in sb.get("captions", []) if c["s"] < WIN]
    if t_text is None and caps:
        t_text = caps[0]["s"]

# ---- scoring (each part 0..1, weighted) -------------------------------------------------------
clip = lambda x: float(np.clip(x, 0, 1))
parts = {
    "motion_from_frame_1": (clip(motion_first / 6), 20),     # something visibly moving in the first 0.5 s
    "pace_changes": (clip(cuts / 2) * 0.6 + clip(motion_all / 8) * 0.4, 10),
    "text_on_screen_fast": ((1.0 if t_text is not None and t_text <= 0.5 else 0.6 if t_text is not None and t_text <= 1.2 else 0.0) if a.sb else 0.5, 20),
    "text_short": ((1.0 if n_words and n_words <= 7 else 0.6 if n_words and n_words <= 10 else 0.2) if n_words else 0.5, 10),
    "sound_hits_immediately": (clip(1 - t_sound / 0.6) * 0.6 + clip((hit + 30) / 20) * 0.4, 15),
    "face_or_subject": ((clip(face_area / 0.02) if face_area >= 0 else 0.5), 10),
    "visual_punch": (clip(contrast / 60) * 0.5 + clip(saturation / 110) * 0.3 + clip(brightness / 140) * 0.2, 15),
}
score = round(sum(v * w for v, w in parts.values()) / sum(w for _, w in parts.values()) * 100)

fixes = []
if parts["motion_from_frame_1"][0] < 0.5: fixes.append("Open on motion: start the clip mid-action (use 'in' later in the shot) or a punch-in/whip — no still first frame.")
if parts["text_on_screen_fast"][0] < 1 and a.sb: fixes.append("Put the hook text on screen by 0.3–0.5 s (hook.s).")
if parts["text_short"][0] < 1 and n_words: fixes.append(f"Hook text has {n_words} words — cut to ≤ 7; move the rest to 'sub'.")
if parts["sound_hits_immediately"][0] < 0.6: fixes.append("Sound must land at 0.0 s: add an impact/whoosh at t=0 and start the voice ≤ 0.3 s.")
if 0 <= face_area < 0.005: fixes.append("No clear face in the opening: faces stop the scroll — open on a person (eyes to camera) or a very clear subject.")
if parts["visual_punch"][0] < 0.55: fixes.append("Opening frame looks flat/dark: brighter, higher-contrast first shot (or grade it up).")
if parts["pace_changes"][0] < 0.4: fixes.append("Add a change before 3 s (cut, zoom punch or flash) — a single static shot loses viewers.")

out = {"hook_score": score, "hook_text": hook_text,
       "components": {k: round(v * 100) for k, (v, _) in parts.items()},
       "measures": {"motion_first_0.5s": round(motion_first, 2), "cuts_in_3s": cuts, "first_sound_s": round(t_sound, 2),
                    "peak_db_first_0.3s": round(hit, 1), "text_at_s": t_text, "hook_words": n_words,
                    "face_area_frac": round(face_area, 4), "contrast": round(contrast, 1), "saturation": round(saturation, 1)},
       "fixes": fixes}
print(f"HOOK SCORE {score}/100  {os.path.basename(a.video)}  «{hook_text}»")
for k, v in out["components"].items(): print(f"  {k:24s} {v:3d}")
for f in fixes: print("  fix:", f)
if a.json: json.dump(out, open(a.json, "w"), ensure_ascii=False, indent=1)
