#!/usr/bin/env python3
"""Objective lip-sync + identity-stability check for a talking-head clip.

Usage: python3 lipsync_score.py clip.mp4 [reference_audio.mp3]

- Tracks mouth opening (inner-lip gap / face height) per frame with MediaPipe FaceLandmarker.
- Compares it with the speech loudness envelope (clip audio, or the reference voice file):
  corr = Pearson correlation at best lag (higher = mouth follows speech; real footage ~0.5-0.7),
  lag_ms = best offset (positive = mouth late).
- face_drift = spread of face proportions over the clip (lower = steadier identity), and
  face_scale_change = how much the face grows/shrinks (camera push-ins show up here).
Needs: pip install mediapipe opencv-python-headless numpy; ffmpeg on PATH.
"""
import os, subprocess, sys, tempfile, urllib.request

import cv2
import numpy as np
import mediapipe as mp

clip = sys.argv[1]
ref_audio = sys.argv[2] if len(sys.argv) > 2 else clip

MODEL = os.path.join(tempfile.gettempdir(), "face_landmarker.task")
if not os.path.exists(MODEL):
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task", MODEL)

opts = mp.tasks.vision.FaceLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=MODEL), running_mode=mp.tasks.vision.RunningMode.VIDEO, num_faces=1)
lm = mp.tasks.vision.FaceLandmarker.create_from_options(opts)

cap = cv2.VideoCapture(clip); fps = cap.get(cv2.CAP_PROP_FPS) or 24
mouth, props, scale, i = [], [], [], 0
while True:
    ok, frame = cap.read()
    if not ok: break
    res = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), int(i * 1000 / fps))
    i += 1
    if not res.face_landmarks:
        mouth.append(np.nan); continue
    p = np.array([[q.x, q.y] for q in res.face_landmarks[0]])
    face_h = np.linalg.norm(p[10] - p[152])                      # forehead -> chin
    mouth.append(np.linalg.norm(p[13] - p[14]) / face_h)          # inner lips gap
    eye_w, nose_chin = np.linalg.norm(p[33] - p[263]), np.linalg.norm(p[1] - p[152])
    props.append([eye_w / face_h, nose_chin / face_h, np.linalg.norm(p[61] - p[291]) / face_h])
    scale.append(face_h)
mouth = np.array(mouth); n = len(mouth)

# speech envelope sampled at the video frame rate
wav = subprocess.run(["ffmpeg", "-v", "error", "-i", ref_audio, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True).stdout
a = np.frombuffer(wav, np.int16).astype(float)
hop = 16000 / fps
env = np.array([np.sqrt(np.mean(a[int(k * hop):int((k + 1) * hop)] ** 2) + 1e-9) for k in range(int(len(a) / hop))])
m = min(n, len(env)); mo, en = mouth[:m], env[:m]
ok = ~np.isnan(mo)
def corr_at(lag):
    x, y = (mo[lag:], en[:m - lag]) if lag >= 0 else (mo[:m + lag], en[-lag:])
    k = ~np.isnan(x)
    return np.corrcoef(x[k], y[k])[0, 1] if k.sum() > 10 else -1
lags = range(-int(fps * 0.3), int(fps * 0.3) + 1)
best = max(lags, key=corr_at)
props = np.array(props)
print(f"frames {n} @ {fps:.0f}fps, face found {ok.mean() * 100:.0f}%")
print(f"lipsync corr {corr_at(best):.2f} at lag {best * 1000 / fps:+.0f} ms (corr at 0 ms: {corr_at(0):.2f})")
print(f"mouth open range {np.nanmin(mo):.3f}-{np.nanmax(mo):.3f}")
print(f"face_drift {np.mean(np.std(props, 0) / np.mean(props, 0)) * 100:.1f}%  face_scale_change {(max(scale) / min(scale) - 1) * 100:.0f}%")
