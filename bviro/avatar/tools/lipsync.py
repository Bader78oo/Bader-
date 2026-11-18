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
# In running speech the long «aa» uses the half-open shape too: the wide AA shape drops the jaw, and cross-fading a
# dropped jaw with any other shape shows a double chin. AA is kept for a held exclamation or laugh, shown on its own.
VOWELS = {"a": ("A", 1.0), "aa": ("A", 1.7), "i": ("EE", 0.9), "ii": ("EE", 1.6), "u": ("OO", 0.9), "uu": ("OO", 1.6)}
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


def frame_weights(track, n_frames, fps=24, t_offset=0.0, lead=0.04, snap=0.62):
    """Per frame: {shape: weight}; REST fills whatever is not speech. `track` times are in voice-file seconds,
    frame k covers [k/fps, (k+1)/fps) + t_offset on that clock; the mouth leads the sound by `lead` seconds.
    A shape that fills most of a frame is shown alone (crisp); only real transitions are cross-faded."""
    out = []
    for k in range(n_frames):
        a, b = k / fps + t_offset + lead, (k + 1) / fps + t_offset + lead
        w = {}
        for t0, t1, p in track:
            ov = min(b, t1) - max(a, t0)
            if ov > 0:
                v = viseme(p)
                w[v] = w.get(v, 0.0) + ov * fps
        rest = max(0.0, 1.0 - sum(w.values()))
        if rest > 1e-3:
            w["REST"] = rest
        top = sorted(w.items(), key=lambda kv: -kv[1])[:2]  # at most two shapes are mixed in one frame
        if top[0][1] >= snap or len(top) == 1:
            out.append({top[0][0]: 1.0})
        else:
            s = top[0][1] + top[1][1]
            out.append({top[0][0]: top[0][1] / s, top[1][0]: top[1][1] / s})
    # a lip closure must be seen: every M/B gets the frame holding its middle, fully closed, plus the fuller neighbour
    for t0, t1, p in track:
        if viseme(p) != "MBP":
            continue
        mid = ((t0 + t1) / 2 - t_offset - lead) * fps
        k = int(mid)
        if not 0 <= k < n_frames:
            continue
        out[k] = {"MBP": 1.0}
        j = k + 1 if mid - k >= 0.5 else k - 1
        if 0 <= j < n_frames and out[j].get("MBP", 0) < 0.7:
            other = max((s for s in out[j] if s != "MBP"), key=lambda s: out[j][s], default="REST")
            out[j] = {"MBP": 0.7, other: 0.3}
    return out


# ---------------- mouth library ----------------
def _shift(base, img, box):
    """Whole-pixel offset of img against base, measured on a region that must not have changed."""
    a = np.asarray(base.crop(box).convert("L"), np.float32)
    b = np.asarray(img.crop(box).convert("L"), np.float32)
    r = np.fft.ifft2(np.fft.fft2(a - a.mean()) * np.conj(np.fft.fft2(b - b.mean()))).real
    dy, dx = np.unravel_index(r.argmax(), r.shape)
    return (dy - r.shape[0] if dy > r.shape[0] // 2 else dy), (dx - r.shape[1] if dx > r.shape[1] // 2 else dx)


def _mask(d, thr, grow, feather):
    m = Image.fromarray((d > thr).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(feather))
    return np.clip(np.asarray(m, np.float32) / 255 * 1.5, 0, 1)


def build_library(base_path, shape_paths, out_dir, mouth_box, eye_box, anchor_box, blur=7):
    """shape_paths: {"MBP": path, ..., "BLINK": path}. Writes <shape>.png (RGB + halo mask), <shape>_core.png and
    geometry.json. Every shape image is a re-render, so hair strands differ everywhere at pixel level. So:
      core  - where the mouth (or eyelid) really changed shape: these pixels are taken from the shape image;
      halo  - a wider soft ring around it: only the smooth shading change is added there, and the hair strands
              of the approved pose stay, so the beard does not shimmer when the shapes alternate.
    Outside the halo the approved pose is untouched."""
    os.makedirs(out_dir, exist_ok=True)
    base = Image.open(base_path).convert("RGB")
    report = {}
    for name, path in shape_paths.items():
        img = Image.open(path).convert("RGB").resize(base.size, Image.LANCZOS)
        dy, dx = _shift(base, img, anchor_box)
        img = Image.fromarray(np.roll(np.roll(np.asarray(img), dy, 0), dx, 1))
        box = eye_box if name == "BLINK" else mouth_box
        a_img, b_img = base.crop(box), img.crop(box)
        g = ImageFilter.GaussianBlur(blur)
        d = np.abs(np.asarray(a_img.filter(g), np.float32) - np.asarray(b_img.filter(g), np.float32)).mean(2)
        yy, xx = np.mgrid[0:d.shape[0], 0:d.shape[1]]
        edge = np.clip(np.minimum.reduce([xx, yy, d.shape[1] - 1 - xx, d.shape[0] - 1 - yy]) / 30.0, 0, 1)  # fade before the box border
        core = _mask(d, 24.0, 17, 7) * edge
        halo = np.maximum(_mask(d, 9.0, 41, 14) * edge, core)
        Image.fromarray(np.dstack([np.asarray(b_img, np.float32), halo * 255]).astype(np.uint8), "RGBA").save(f"{out_dir}/{name}.png")
        Image.fromarray((core * 255).astype(np.uint8), "L").save(f"{out_dir}/{name}_core.png")
        report[name] = {"shift": [int(dy), int(dx)], "core": round(float(core.mean()), 3), "halo": round(float(halo.mean()), 3)}
    json.dump({"base": os.path.relpath(base_path, out_dir), "base_size": base.size, "mouth_box": mouth_box, "eye_box": eye_box, "shapes": report},
              open(f"{out_dir}/geometry.json", "w"), indent=1)
    return report


class Mouth:
    def __init__(self, lib_dir, smooth=6):
        g = json.load(open(f"{lib_dir}/geometry.json"))
        self.size, self.mouth_box, self.eye_box = tuple(g["base_size"]), tuple(g["mouth_box"]), tuple(g["eye_box"])
        lib_base = Image.open(os.path.join(lib_dir, g["base"])).convert("RGB")
        self.shape = {}
        for n in g["shapes"]:
            rgba = np.asarray(Image.open(f"{lib_dir}/{n}.png").convert("RGBA"), np.float32)
            core = np.asarray(Image.open(f"{lib_dir}/{n}_core.png").convert("L"), np.float32)[..., None] / 255
            box = self.eye_box if n == "BLINK" else self.mouth_box
            delta = rgba[..., :3] - np.asarray(lib_base.crop(box), np.float32)
            # smooth part of the change (PIL blurs 8-bit only: halve the signed difference around 128, blur, undo)
            packed = Image.fromarray(np.clip(delta / 2 + 128, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(smooth))
            low = (np.asarray(packed, np.float32) - 128) * 2
            self.shape[n] = (rgba[..., :3], core, np.clip(rgba[..., 3:4] / 255 - core, 0, 1), low)

    def _apply(self, region, name, amount=1.0):
        rgb, core, halo, low = self.shape[name]
        return region + amount * (core * (rgb - region) + halo * low)

    def render(self, pose, weights, blink=0.0):
        """pose: PIL image of an approved pose at the library's size. Returns the pose with the blended mouth."""
        assert pose.size == self.size, (pose.size, self.size)
        out = np.asarray(pose.convert("RGB"), np.float32).copy()
        x0, y0, x1, y1 = self.mouth_box
        base = out[y0:y1, x0:x1].copy()
        total = sum(weights.values())
        acc = np.zeros_like(base)
        for name, w in weights.items():
            acc += (base if name == "REST" else self._apply(base, name)) * (w / total)
        out[y0:y1, x0:x1] = acc
        if blink > 0:
            x0, y0, x1, y1 = self.eye_box
            out[y0:y1, x0:x1] = self._apply(out[y0:y1, x0:x1].copy(), "BLINK", blink)
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
