"""Measure how close the faces in the film's stills are to the locked character portraits (CHARACTERS.md).

A face becomes 128 numbers (dlib's face recognition model); two pictures of one person normally sit under 0.6 apart,
and under 0.5 is a strong match. The grandfather's headset shots cannot be measured: his eyes are covered.

usage:
    PYTHONPATH=<dir with dlib> python3 check_identity.py MODELS_DIR LOCKS.json SHOT[=character] ...

MODELS_DIR holds dlib_face_recognition_resnet_model_v1.dat, shape_predictor_5_face_landmarks.dat and
mmod_human_face_detector.dat (they come inside the `face_recognition_models` source archive on PyPI;
dlib itself is `pip install dlib-bin`).
LOCKS.json maps a character to a portrait and, optionally, a crop of it: {"young": {"image": "sheet.png",
"box": [0.61, 0.0, 1.0, 1.0]}} (box as fractions: left, top, right, bottom).
SHOT=character names who should be in the picture; without it the shot is compared with every lock.
A face under 80 px wide is too small to judge, and a wide shot may show no measurable face at all: both are
reported as such, not as failures (the model was built for faces of 150 px), so a close-up is what proves a
character. Exit status 1 only when a measured face of a named shot is 0.6 or further from its lock.
"""
import json
import os
import sys

import dlib
import numpy as np
from PIL import Image

SAME, STRONG, MIN_FACE = 0.60, 0.50, 80
models, locks_path, shots = sys.argv[1], sys.argv[2], sys.argv[3:]
hog = dlib.get_frontal_face_detector()
cnn = dlib.cnn_face_detection_model_v1(os.path.join(models, "mmod_human_face_detector.dat"))
shape = dlib.shape_predictor(os.path.join(models, "shape_predictor_5_face_landmarks.dat"))
encoder = dlib.face_recognition_model_v1(os.path.join(models, "dlib_face_recognition_resnet_model_v1.dat"))


def load(path, box=None, long_side=1600):
    im = Image.open(path).convert("RGB")
    if box:
        w, h = im.size
        im = im.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)))
    k = long_side / max(im.size)
    if k < 1:
        im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    return np.asarray(im)


def faces(img):
    """[(descriptor, face width in px)] for every face found, largest first.

    The quick detector first; when it finds nothing, the slower neural one on a picture shrunk to 800 px (on a
    processor it needs about a second per megapixel, so it never sees the full-size still)."""
    rects = list(hog(img, 1))
    if not rects:
        k = 800 / max(img.shape[:2])
        small = np.asarray(Image.fromarray(img).resize((int(img.shape[1] * k), int(img.shape[0] * k)), Image.LANCZOS)) if k < 1 else img
        k = min(k, 1)
        rects = [dlib.rectangle(int(d.rect.left() / k), int(d.rect.top() / k), int(d.rect.right() / k), int(d.rect.bottom() / k))
                 for d in cnn(small, 0)]
    out = []
    for r in sorted(rects, key=lambda r: -r.width()):
        d = np.array(encoder.compute_face_descriptor(img, shape(img, r), 1))
        out.append((d, r.width()))
    return out


locks = {}
for name, spec in json.load(open(locks_path, encoding="utf-8")).items():
    base = os.path.dirname(os.path.abspath(locks_path))
    found = faces(load(os.path.join(base, spec["image"]), spec.get("box")))
    assert found, f"no face found in the lock portrait of {name}"
    locks[name] = found[0][0]

names = list(locks)
print("locks against each other (different people should be 0.6 or more apart):")
for i, a in enumerate(names):
    for b in names[i + 1:]:
        print(f"  {a} / {b}: {np.linalg.norm(locks[a] - locks[b]):.2f}")

bad = 0
print("shots:")
for item in shots:
    path, _, who = item.partition("=")
    found = faces(load(path))
    label = os.path.basename(path)
    if not found:
        print(f"  {label}: no measurable face" + (f" (expected {who})" if who else ""))
        continue
    for d, width in found[:2]:
        dist = {n: float(np.linalg.norm(d - locks[n])) for n in names}
        nearest = min(dist, key=dist.get)
        row = "  ".join(f"{n} {v:.2f}" for n, v in dist.items())
        if width < MIN_FACE:
            print(f"  {label} (face {width}px" + (f", expected {who}" if who else "") + f"): {row}  ->  too small to judge")
        elif who:
            v = dist[who]
            verdict = "strong match" if v < STRONG else "match" if v < SAME else "TOO FAR"
            bad += v >= SAME
            print(f"  {label} (face {width}px, expected {who}): {row}  ->  {verdict}")
        else:
            print(f"  {label} (face {width}px): {row}  ->  nearest {nearest}")
sys.exit(1 if bad else 0)
