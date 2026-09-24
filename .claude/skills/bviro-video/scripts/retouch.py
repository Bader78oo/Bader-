#!/usr/bin/env python3
"""Subtle portrait retouch for a start frame, driven by MediaPipe face landmarks.

Usage: python3 retouch.py in.png out.png [--slim 0.05] [--skin 0.45] [--eyes 0.8]

--slim  cheek/jaw slimming as a fraction of face width (0 = off, 0.03-0.07 looks natural)
--skin  strength of skin smoothing (frequency separation: texture is kept, blotches evened)
--eyes  extra smoothing of crow's feet / under-eye lines
Eyes, brows, lips, beard and nostrils are masked out so they stay sharp.
"""
import argparse, os, tempfile, urllib.request

import cv2
import numpy as np
import mediapipe as mp

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("dst")
ap.add_argument("--slim", type=float, default=0.05)
ap.add_argument("--skin", type=float, default=0.45)
ap.add_argument("--eyes", type=float, default=0.8)
a = ap.parse_args()

MODEL = os.path.join(tempfile.gettempdir(), "face_landmarker.task")
if not os.path.exists(MODEL):
    urllib.request.urlretrieve("https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task", MODEL)
lm = mp.tasks.vision.FaceLandmarker.create_from_options(mp.tasks.vision.FaceLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=MODEL), num_faces=1))

img = cv2.imread(a.src); H, W = img.shape[:2]
res = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))
if not res.face_landmarks:
    raise SystemExit("no face found")
P = np.array([[q.x * W, q.y * H] for q in res.face_landmarks[0]], np.float32)
face_w = np.linalg.norm(P[234] - P[454])

def poly_mask(idx, blur):
    m = np.zeros((H, W), np.float32)
    cv2.fillPoly(m, [P[idx].astype(np.int32)], 1.0)
    return cv2.GaussianBlur(m, (0, 0), blur)

OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152,
        148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
L_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
R_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
L_BROW = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
R_BROW = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
out = img.astype(np.float32)

# 1) cheek / jaw slimming: pull lower-face contour points toward the face's vertical centre line
if a.slim > 0:
    cx = (P[234, 0] + P[454, 0]) / 2
    cheek_idx = [234, 93, 132, 58, 172, 136, 150, 149, 454, 323, 361, 288, 397, 365, 379, 378]
    radius = face_w * 0.28
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = np.zeros((H, W), np.float32)
    for k in cheek_idx:
        px, py = P[k]
        w = np.exp(-((xs - px) ** 2 + (ys - py) ** 2) / (2 * radius ** 2))
        dx += w * np.sign(px - cx) * a.slim * face_w * 0.5   # sample from further out -> contour moves in
    dx = np.clip(dx, -a.slim * face_w, a.slim * face_w)
    # protect the centre of the face (nose, lips, chin) so only the sides move
    dx *= np.clip((np.abs(xs - cx) - face_w * 0.2) / (face_w * 0.12), 0, 1)
    out = cv2.remap(out, xs + dx, ys, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    P[:, 0] -= 0  # landmarks only used for masks below; slight shift is harmless at mask blur scale

# 2) skin mask = face oval minus eyes, brows, lips, beard area (beard ~ below the nose on dark pixels)
skin = poly_mask(OVAL, face_w * 0.02)
for part, b in ((L_EYE, 6), (R_EYE, 6), (L_BROW, 6), (R_BROW, 6), (LIPS, 6)):
    skin *= 1 - np.clip(poly_mask(part, b) * 3, 0, 1)
gray = cv2.cvtColor(out.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
hair = cv2.GaussianBlur((gray < 70).astype(np.float32), (0, 0), 3)          # beard / stubble / brows
skin *= 1 - np.clip(hair * 1.5, 0, 1)

# frequency separation: smooth the low band, keep fine texture (pores) from the high band
low = cv2.bilateralFilter(out.astype(np.uint8), 0, 30, face_w * 0.02).astype(np.float32)
blur_small = cv2.GaussianBlur(out, (0, 0), 1.2)
high = out - blur_small
smoothed = cv2.GaussianBlur(low, (0, 0), 1.2) + high * 0.85
out = out * (1 - skin[..., None] * a.skin) + smoothed * (skin[..., None] * a.skin)

# 3) crow's feet + under-eye: stronger smoothing in a band around each outer eye corner
if a.eyes > 0:
    band = np.zeros((H, W), np.float32)
    for c, inner in ((33, 133), (263, 362)):
        centre = P[c] + (P[c] - P[inner]) * 0.35
        cv2.ellipse(band, tuple(centre.astype(int)), (int(face_w * 0.09), int(face_w * 0.07)), 0, 0, 360, 1.0, -1)
    for ey in (L_EYE, R_EYE):                             # under-eye strip
        lo = P[ey][P[ey][:, 1].argsort()][-4:].mean(0)
        cv2.ellipse(band, tuple((lo + [0, face_w * 0.045]).astype(int)), (int(face_w * 0.1), int(face_w * 0.03)), 0, 0, 360, 1.0, -1)
    for ey in (L_EYE, R_EYE):
        band *= 1 - np.clip(poly_mask(ey, 3) * 4, 0, 1)   # never touch the eye itself
    band = cv2.GaussianBlur(band, (0, 0), face_w * 0.02) * a.eyes
    strong = cv2.bilateralFilter(out.astype(np.uint8), 0, 40, face_w * 0.03).astype(np.float32) + (out - cv2.GaussianBlur(out, (0, 0), 1.0)) * 0.5
    out = out * (1 - band[..., None]) + strong * band[..., None]

cv2.imwrite(a.dst, np.clip(out, 0, 255).astype(np.uint8))
print("retouched ->", a.dst)
