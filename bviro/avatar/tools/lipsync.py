"""Drawn lip movement for the Bader avatar (see ../CHARACTER.md, section 8).

The mouth shapes are edits of the approved pose image in which only the mouth changes. This module
  1. cuts each shape down to a soft-edged mouth/chin patch          (build_library)
  2. times the phonemes of a line against the voice recording       (align)
  3. gives, for every video frame, the blend of shapes to show      (frame_weights)
  4. paints those patches onto the untouched pose image             (Mouth.render)
Nothing outside the mouth/chin patch (and the eyelid patch for a blink) is ever modified.

Phoneme codes, one word per group:  a aa i ii u uu  +  consonants in Latin (b m f l n t d s z sh j k q r x gh h H 3 ' w y th dh)
  doubled consonants are written twice.  Example:  "is s i r | h i n aa"  for «السر هنا».
"""
import json
import os
import subprocess

import numpy as np
from PIL import Image, ImageFilter

SHAPES = ["MBP", "A", "AA", "EE", "OO", "FV", "L", "C"]
VOWELS = {"a": ("A", 1.0), "aa": ("AA", 1.7), "i": ("EE", 0.9), "ii": ("EE", 1.6), "u": ("OO", 0.9), "uu": ("OO", 1.6)}
CONS = {**{c: "MBP" for c in ("m", "b", "p")}, **{c: "FV" for c in ("f", "v")}, "w": "OO", "y": "EE",
        **{c: "L" for c in ("l", "n", "t", "d", "th", "dh", "T", "D")}}
SR, HOP = 16000, 80  # envelope: 5 ms hop


def viseme(ph):
    return VOWELS[ph][0] if ph in VOWELS else CONS.get(ph, "C")


def envelope(path):
    """Speech-band energy envelope of an audio file, one value every 5 ms."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    win = 400
    n = 1 + (len(x) - win) // HOP
    idx = np.arange(win)[None, :] + HOP * np.arange(n)[:, None]
    spec = np.abs(np.fft.rfft(x[idx] * np.hanning(win), axis=1)) ** 2
    f = np.fft.rfftfreq(win, 1 / SR)
    e = spec[:, (f >= 300) & (f <= 3400)].sum(1)
    k = np.hanning(7)
    return np.convolve(np.sqrt(e), k / k.sum(), mode="same")


def align(words, env):
    """words: [(start, end, "ph ph ph"), ...] with times from the voice file (word start/end, clipped to speech).
    Returns [(t0, t1, phoneme)] for the whole line: phonemes are first spread inside each word by typical
    length, then every vowel is pulled onto the nearest energy peak and the boundaries are re-cut between them."""
    centres, phs = [], []
    for w0, w1, text in words:
        seq = text.split()
        wts = [VOWELS[p][1] if p in VOWELS else 0.75 for p in seq]
        edges = w0 + np.concatenate([[0], np.cumsum(wts)]) / sum(wts) * (w1 - w0)
        for p, a, b in zip(seq, edges[:-1], edges[1:]):
            phs.append(p)
            centres.append((a + b) / 2)
    centres = np.array(centres)
    t_env = np.arange(len(env)) * HOP / SR
    for i, p in enumerate(phs):
        if p not in VOWELS:
            continue
        lo = max(centres[i] - 0.07, centres[i - 1] + 0.02 if i else 0)
        hi = min(centres[i] + 0.07, centres[i + 1] - 0.02 if i + 1 < len(phs) else 1e9)
        m = (t_env >= lo) & (t_env <= hi)
        if m.any():
            centres[i] = t_env[m][np.argmax(env[m])]
    cuts = [words[0][0]] + [float((centres[i] + centres[i + 1]) / 2) for i in range(len(phs) - 1)] + [words[-1][1]]
    # keep word-internal silences out of it: the first and last phoneme of the line touch the speech edges
    return [(cuts[i], cuts[i + 1], phs[i]) for i in range(len(phs))]


def frame_weights(track, n_frames, fps=24, t_offset=0.0, lead=0.04, min_closure=2):
    """Per frame: {shape: weight}; REST fills whatever is not speech. `track` times are in voice-file seconds,
    frame k covers [k/fps, (k+1)/fps) + t_offset on that clock; the mouth leads the sound by `lead` seconds."""
    out = []
    for k in range(n_frames):
        a, b = k / fps + t_offset + lead, (k + 1) / fps + t_offset + lead
        w = {}
        for t0, t1, p in track:
            ov = min(b, t1) - max(a, t0)
            if ov > 0:
                v = viseme(p)
                w[v] = w.get(v, 0.0) + ov * fps
        top = dict(sorted(w.items(), key=lambda kv: -kv[1])[:2])  # at most two shapes are mixed in one frame
        rest = max(0.0, 1.0 - sum(top.values()))
        out.append({**top, **({"REST": rest} if rest > 1e-3 else {})})
    # a lip closure must be seen: stretch any M/B shorter than min_closure frames
    for k, w in enumerate(out):
        if w.get("MBP", 0) >= 0.5 and not any(out[j].get("MBP", 0) >= 0.5 for j in (k - 1, k + 1) if 0 <= j < n_frames) and min_closure > 1:
            j = k + 1 if k + 1 < n_frames else k - 1
            out[j] = {"MBP": 0.7, **{s: v * 0.3 for s, v in out[j].items() if s != "MBP"}}
    return out


# ---------------- mouth library ----------------
def _shift(base, img, box):
    """Whole-pixel offset of img against base, measured on a region that must not have changed."""
    a = np.asarray(base.crop(box).convert("L"), np.float32)
    b = np.asarray(img.crop(box).convert("L"), np.float32)
    r = np.fft.ifft2(np.fft.fft2(a - a.mean()) * np.conj(np.fft.fft2(b - b.mean()))).real
    dy, dx = np.unravel_index(r.argmax(), r.shape)
    return (dy - r.shape[0] if dy > r.shape[0] // 2 else dy), (dx - r.shape[1] if dx > r.shape[1] // 2 else dx)


def build_library(base_path, shape_paths, out_dir, mouth_box, eye_box, anchor_box, thr=14.0):
    """shape_paths: {"MBP": path, ..., "BLINK": path}. Writes one RGBA patch per shape plus geometry.json.
    A patch keeps only the pixels that really differ from the base inside its box, with a feathered edge."""
    os.makedirs(out_dir, exist_ok=True)
    base = Image.open(base_path).convert("RGB")
    report = {}
    for name, path in shape_paths.items():
        img = Image.open(path).convert("RGB").resize(base.size, Image.LANCZOS)
        dy, dx = _shift(base, img, anchor_box)
        img = Image.fromarray(np.roll(np.roll(np.asarray(img), dy, 0), dx, 1))
        box = eye_box if name == "BLINK" else mouth_box
        a = np.asarray(base.crop(box), np.float32)
        b = np.asarray(img.crop(box), np.float32)
        diff = Image.fromarray((np.abs(a - b).mean(2) > thr).astype(np.uint8) * 255)
        m = diff.filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(10))
        m = np.asarray(m, np.float32) / 255
        yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
        edge = np.minimum.reduce([xx, yy, m.shape[1] - 1 - xx, m.shape[0] - 1 - yy]) / 24.0  # never reach the box border
        m = np.clip(m * 1.6, 0, 1) * np.clip(edge, 0, 1)
        Image.fromarray(np.dstack([b, m * 255]).astype(np.uint8), "RGBA").save(f"{out_dir}/{name}.png")
        report[name] = {"shift": [int(dy), int(dx)], "coverage": round(float(m.mean()), 3)}
    json.dump({"base_size": base.size, "mouth_box": mouth_box, "eye_box": eye_box, "shapes": report}, open(f"{out_dir}/geometry.json", "w"), indent=1)
    return report


class Mouth:
    def __init__(self, lib_dir):
        g = json.load(open(f"{lib_dir}/geometry.json"))
        self.size, self.mouth_box, self.eye_box = tuple(g["base_size"]), tuple(g["mouth_box"]), tuple(g["eye_box"])
        self.patch = {n: np.asarray(Image.open(f"{lib_dir}/{n}.png").convert("RGBA"), np.float32) for n in g["shapes"]}

    def render(self, pose, weights, blink=0.0):
        """pose: PIL image of an approved pose at the library's size. Returns the pose with the blended mouth."""
        assert pose.size == self.size, (pose.size, self.size)
        out = np.asarray(pose.convert("RGB"), np.float32).copy()
        x0, y0, x1, y1 = self.mouth_box
        base = out[y0:y1, x0:x1].copy()
        acc = base * weights.get("REST", 0.0)
        for name, w in weights.items():
            if name == "REST":
                continue
            p = self.patch[name]
            a = p[..., 3:4] / 255
            acc += (base * (1 - a) + p[..., :3] * a) * w
        out[y0:y1, x0:x1] = acc / max(1e-6, sum(weights.values()))
        if blink > 0:
            x0, y0, x1, y1 = self.eye_box
            p = self.patch["BLINK"]
            a = p[..., 3:4] / 255 * blink
            out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - a) + p[..., :3] * a
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
