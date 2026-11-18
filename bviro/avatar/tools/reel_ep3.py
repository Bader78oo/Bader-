"""«صورة لكل عين» (الـVR من الصفر، الحلقة 3) — built from scratch on ../CHARACTER.md.

  1 hook    he wears the headset and reaches for a glowing object, speaking the question to the viewer
  2 lenses  he shows the two lenses and explains, speaking
  3 zoom    the camera goes into the lenses; the virtual world plays inside both, one picture per eye
  4 merge   the two pictures slide together, fuse and open to full screen
  5 world   first-person view inside the virtual world (voice over)
  6 close   he holds the headset, says the last line, «احفظه»

Every shot of the character is an approved pose image, untouched, under a slow camera move. He speaks with his own
drawn mouth shapes (lipsync.py), one crisp shape per frame, timed to the voice; a drawn blink in the pauses.
No tool that redraws the face is used. The voice in the output is the original recording.

usage: python3 -I reel_ep3.py WORKDIR     -> WORKDIR/out/bviro_vr_ep3.mp4
WORKDIR holds vo.mp3 (the voice) and world.mp4 (the first-person virtual-world clip).
Run one build at a time: two builds writing the same WORKDIR corrupt the file.
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lipsync  # noqa: E402

AV = os.path.dirname(HERE)   # bviro/avatar
BV = os.path.dirname(AV)     # bviro
WD = sys.argv[1]
W, H, FPS = 1080, 1920, 24
PURPLE, TURQ, DARK, WHITE = (127, 2, 254), (0, 205, 200), (43, 1, 87), (255, 255, 255)
CHIP, TCHIP = "chip", "tchip"

# ---------------- timeline: seconds on the video; the voice runs from 0 unchanged ----------------
T_HOOK = (0.00, 2.25)
T_LENSES = (2.25, 6.40)
T_ZOOM = (6.40, 7.10)
T_INSIDE = (7.10, 9.55)
T_MERGE = (9.55, 10.45)
T_WORLD = (10.45, 14.75)
T_CLOSE = (14.75, 18.90)
TOTAL = T_CLOSE[1]
WORLD_OFFSET = 6.30  # world clip time = video time - WORLD_OFFSET

# camera on each character shot: scale from -> to about a fixed point (1080x1920 coordinates)
CAM_HOOK = ((1.12, 1.00), (540.0, 600.0))    # pulls back from his face to reveal the reaching hand
CAM_LENSES = ((1.00, 1.12), (540.0, 1000.0))  # moves in toward the lenses
CAM_CLOSE = ((1.00, 1.07), (540.0, 760.0))

# what he says on camera: runs of (word start, word end, phonemes) in voice seconds; a new run after each pause
SAY_HOOK = [[(0.03, 0.30, "l ii sh"), (0.30, 0.40, "f i"), (0.40, 0.68, "i l f ii"), (0.68, 0.82, "aa r"),
             (0.82, 1.18, "t H i s s"), (1.18, 1.44, "i sh sh a y"), (1.44, 2.02, "q i d d aa m a k")]]
SAY_LENSES = [[(2.40, 2.74, "i s s i r"), (2.74, 3.03, "h i n aa")],
              [(3.28, 3.78, "d aa x i l"), (3.78, 4.38, "i n n a dh dh aa r a"), (4.38, 5.01, "3 a d a s t ii n")],
              [(5.26, 5.68, "w a H d a"), (5.68, 6.00, "l i k u l l"), (6.00, 6.23, "3 ii n")]]
SAY_CLOSE = [[(14.94, 15.12, "b a s"), (15.12, 15.45, "h i n aa")],
             [(15.67, 16.10, "i l 3 aa l a m"), (16.10, 16.63, "m a r s uu m")]]
BLINK_LENSES, BLINK_CLOSE = (0.86, 2.86), (2.40, 3.65)  # seconds into the shot, in the pauses

# the glowing object he reaches for in the hook (1080x1920 coordinates of the pose) and when he touches it
ORB_C, ORB_R, ORB_TOUCH = (122.0, 1000.0), 60.0, 1.50

# lens geometry: centres and radius in the close-up prop, and centres in pose_lenses (all at 1080x1920)
LENS_L, LENS_R, LENS_RAD = (298.0, 955.0), (783.0, 955.0), 186.0
MID = (540.5, 955.0)
POSE_LENS = ((462.5, 1197.5), (625.0, 1197.5))

# captions: (start, end, lines); the words follow the voice
CARDS = [
    (0.00, 2.15, [[("ليش في الـVR", WHITE)], [("تحس الشي", WHITE), ("قدامك؟", CHIP)]]),
    (2.38, 3.15, [[("السر", WHITE), ("هنا", TCHIP)]]),
    (3.26, 6.30, [[("داخل النظارة", WHITE), ("عدستين", CHIP)], [("وحدة لكل عين", WHITE)]]),
    (6.56, 9.42, [[("كل عين تشوف صورة", WHITE)], [("تختلف شوي", TCHIP), ("عن الثانية", WHITE)]]),
    (9.60, 10.72, [[("ومخك", WHITE), ("يدمجهن", CHIP)]]),
    (10.95, 12.82, [[("فتحس إنك واقف", WHITE)], [("داخل المكان", TCHIP)]]),
    (13.02, 14.70, [[("نفس اللي تسويه", WHITE)], [("عيونك كل يوم", WHITE)]]),
    (14.92, 16.78, [[("بس هنا", WHITE)], [("العالم", WHITE), ("مرسوم", CHIP)]]),
]
END_CARD = (17.05, TOTAL)


# ---------------- small tools ----------------
def frames_between(t0, t1):
    """Frames between two timeline points, counted on the frame grid so the shots always add up."""
    return int(round(t1 * FPS)) - int(round(t0 * FPS))


def read_frames(path, t0, n):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.4f}", "-i", path, "-frames:v", str(n), "-vf",
                          f"fps={FPS},scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    assert len(a) == n, (path, t0, n, len(a))
    return a


def write_video(frames, out):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(np.ascontiguousarray(fr).tobytes())
    p.stdin.close()
    assert p.wait() == 0


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def zoom(img, s, src_c, dst_c=None):
    """Scale an image by s so that point src_c lands on dst_c (default: stays put). Points are in 1080x1920
    coordinates whatever the image size, so a 2K pose is sampled directly at full quality."""
    dst_c = dst_c or src_c
    r = img.size[0] / W
    a = r / s
    return img.transform((W, H), Image.AFFINE, (a, 0, src_c[0] * r - dst_c[0] * a, 0, a, src_c[1] * r - dst_c[1] * a), resample=Image.BICUBIC)


def disc(c, r, feather=2.0):
    yy, xx = np.mgrid[0:H, 0:W]
    return np.clip((r - np.hypot(xx - c[0], yy - c[1])) / feather + 0.5, 0, 1).astype(np.float32)


# ---------------- the character speaking ----------------
def talking_shot(pose_file, span, say, cam, mouth, env, blinks=(), fx=None):
    """An approved pose under a slow camera move; mouth shapes follow the voice; optional drawn blink and effect."""
    pose = Image.open(f"{AV}/poses/{pose_file}").convert("RGB")
    n = frames_between(*span)
    track = [seg for run in say for seg in lipsync.align(run, env)]
    shapes = lipsync.frame_shapes(track, n, fps=FPS, t_offset=span[0])
    (s0, s1), centre = cam
    out = []
    for i in range(n):
        t = i / FPS
        blink = 1.0 if any(0 <= t - b < 3 / FPS - 1e-6 for b in blinks) else 0.0  # closed for three frames
        img = mouth.render(pose, {shapes[i]: 1.0}, blink=blink)
        if fx:
            img = fx(img, t)
        out.append(np.asarray(zoom(img, s0 + (s1 - s0) * ease(i / (n - 1)), centre)))
    return out, shapes


def orb_fx(img, t):
    """A small glowing glass sphere floating at his fingertips: it appears, bobs, and ripples when he touches it."""
    k = img.size[0] / W
    grow = ease(t / 0.30)
    if grow <= 0:
        return img
    cx, cy = ORB_C[0] * k, (ORB_C[1] + 7 * np.sin(2 * np.pi * 0.9 * t)) * k
    r = ORB_R * k * grow * (1 + 0.04 * np.sin(2 * np.pi * 1.6 * t))
    pad = int(r * 3.4)
    x0, y0 = int(cx) - pad, int(cy) - pad
    yy, xx = np.mgrid[0:2 * pad, 0:2 * pad].astype(np.float32)
    d = np.hypot(xx - (cx - x0), yy - (cy - y0)) / r
    glow = np.exp(-(d / 1.25) ** 2) * 0.55                           # soft halo
    body = np.clip((1.0 - d) / 0.06, 0, 1)                           # the sphere itself
    shade = np.clip(1.0 - d, 0, 1)
    rim = np.exp(-((d - 0.94) / 0.05) ** 2) * 0.9
    hx, hy = (xx - (cx - x0 - 0.36 * r)) / (0.30 * r), (yy - (cy - y0 - 0.40 * r)) / (0.18 * r)
    spec = np.exp(-(hx ** 2 + hy ** 2)) * 0.95
    ripple = 0.0
    if t >= ORB_TOUCH:
        q = (t - ORB_TOUCH) / 0.55
        ripple = np.exp(-((d - (1.0 + 1.7 * q)) / 0.07) ** 2) * max(0.0, 1 - q) * 0.9
    turq, purp, white = np.array(TURQ, np.float32), np.array(PURPLE, np.float32), np.array(WHITE, np.float32)
    colour = purp * (1 - shade[..., None] ** 0.6) + turq * shade[..., None] ** 0.6
    colour = colour * (1 - 0.55 * shade[..., None] ** 3) + white * 0.55 * shade[..., None] ** 3
    arr = np.asarray(img, np.float32).copy()
    ys, xs = slice(max(0, y0), min(arr.shape[0], y0 + 2 * pad)), slice(max(0, x0), min(arr.shape[1], x0 + 2 * pad))
    sy, sx = slice(ys.start - y0, ys.stop - y0), slice(xs.start - x0, xs.stop - x0)
    reg = arr[ys, xs]
    a = (body * 0.62)[sy, sx, None]
    reg = reg * (1 - a) + colour[sy, sx] * a                                       # glass: the fingers show through
    add = (glow[sy, sx, None] * turq + rim[sy, sx, None] * turq * 0.8 + spec[sy, sx, None] * white
           + (ripple[sy, sx, None] * turq if t >= ORB_TOUCH else 0.0))
    arr[ys, xs] = 255 - (255 - reg) * (255 - np.clip(add, 0, 255)) / 255           # light adds on top (screen)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ---------------- into the lenses ----------------
def lens_sequence(world, last_frame, lens_now):
    """T_ZOOM + T_INSIDE + T_MERGE. `last_frame` is the last frame of the lenses shot and `lens_now` the two lens
    centres in it; `world` holds the world-clip frames from T_ZOOM[1] on."""
    closeup = Image.open(f"{AV}/poses/prop_lenses_closeup.png").convert("RGB").resize((W, H), Image.LANCZOS)
    closeup_np = np.asarray(closeup, np.float32)
    last = Image.fromarray(last_frame)
    (ax, ay), (bx, by) = lens_now
    mid_now = ((ax + bx) / 2, (ay + by) / 2)
    s_end = (LENS_R[0] - LENS_L[0]) / (bx - ax)
    out = []
    # match-zoom: the shot grows until its lenses sit exactly on the close-up's lenses, then cross-fades to it
    nz, subs = frames_between(*T_ZOOM), 14
    for i in range(nz):
        acc = np.zeros((H, W, 3), np.float32)
        for sub in range(subs):  # many small steps: a smooth push, not a double image
            p = ease((i + sub / subs) / nz) ** 1.6
            dst = (mid_now[0] + (MID[0] - mid_now[0]) * p, mid_now[1] + (MID[1] - mid_now[1]) * p)
            acc += np.asarray(zoom(last, s_end ** p, mid_now, dst), np.float32)
        a = ease((i / nz - 0.55) / 0.45)
        out.append((acc / subs * (1 - a) + closeup_np * a).astype(np.uint8))
    # inside: the world in both lenses (each eye a slightly shifted picture); merge: they slide together, fuse, open up
    centre, backdrop = (W / 2, H / 2), np.array(DARK, np.float32) * 0.55
    for j in range(frames_between(*T_INSIDE) + frames_between(*T_MERGE)):
        t = T_INSIDE[0] + j / FPS
        pm = (t - T_MERGE[0]) / (T_MERGE[1] - T_MERGE[0]) if t >= T_MERGE[0] else 0.0
        slide, expand = ease(pm / 0.45), ease((pm - 0.45) / 0.55)
        k = 1.0 + 0.06 * min(1.0, (t - T_INSIDE[0]) / (T_INSIDE[1] - T_INSIDE[0]))
        bg = np.asarray(zoom(closeup, k, MID), np.float32)
        wf = Image.fromarray(world[j])
        r0 = LENS_RAD * k * (1 + 0.15 * slide)
        r = r0 + (1180.0 - r0) * expand
        s_c = min(1.0, 2 * r * 1.30 / W)
        acc, wsum, cover = np.zeros((H, W, 3), np.float32), np.zeros((H, W, 1), np.float32), np.zeros((H, W, 1), np.float32)
        for sign, c0 in ((+1, LENS_L), (-1, LENS_R)):
            cx, cy = MID[0] + (c0[0] - MID[0]) * k, MID[1] + (c0[1] - MID[1]) * k
            c = (cx + (centre[0] - cx) * slide, cy + (centre[1] - cy) * slide)
            shift = sign * 9.0 * (1 - slide)
            content = np.asarray(zoom(wf, s_c, (W / 2 + shift / s_c, H / 2), c), np.float32)
            m = disc(c, r)[..., None]
            acc += content * m
            wsum += m
            cover = np.maximum(cover, m)
        picture = acc / np.maximum(wsum, 1e-6)
        picture = 255 - (255 - picture) * (255 - bg * (1 - slide) * 0.9) / 255   # the lens highlight stays over the picture
        base = bg * (1 - 0.85 * slide) + backdrop * (0.85 * slide)                # the headset dims as the pictures leave it
        m = cover * ease((t - T_INSIDE[0]) / 0.30)
        out.append(np.clip(base * (1 - m) + picture * m, 0, 255).astype(np.uint8))
    return out


# ---------------- captions and brand mark ----------------
def cairo(size, weight=900):
    f = ImageFont.truetype(f"{BV}/fonts/Cairo-VF.ttf", size)
    f.set_variation_by_axes([weight, 0])
    return f


def line_width(segs, font):
    d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    gap, pad = int(font.size * 0.26), int(font.size * 0.20)
    return sum(d.textlength(t, font=font, direction="rtl", language="ar") + (2 * pad if c in (CHIP, TCHIP) else 0) for t, c in segs) + gap * (len(segs) - 1)


def draw_line(img, segs, font, cy, stroke=10):
    d = ImageDraw.Draw(img)
    gap, pad = int(font.size * 0.26), int(font.size * 0.20)
    x = W / 2 + line_width(segs, font) / 2
    for text, col in segs:
        w = d.textlength(text, font=font, direction="rtl", language="ar") + (2 * pad if col in (CHIP, TCHIP) else 0)
        x -= w
        if col in (CHIP, TCHIP):
            h = int(font.size * 1.18)
            d.rounded_rectangle([x, cy - h / 2 + 4, x + w, cy + h / 2 + 4], radius=int(h * 0.28), fill=PURPLE if col == CHIP else TURQ)
            d.text((x + pad, cy), text, font=font, fill=WHITE if col == CHIP else DARK, anchor="lm", direction="rtl", language="ar")
        else:
            d.text((x, cy), text, font=font, fill=col, anchor="lm", direction="rtl", language="ar", stroke_width=stroke, stroke_fill=DARK)
        x -= gap


def caption(lines, size=92, cy=1465, lead=1.36):
    while max(line_width(segs, cairo(size)) for segs in lines) > W - 130:  # never touch the edges
        size -= 4
    font, step = cairo(size), int(size * lead)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i, segs in enumerate(lines):
        draw_line(layer, segs, font, cy - step * (len(lines) - 1) / 2 + i * step)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((20, 0, 45, 255), (0, 10), layer.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.6)))
    return Image.alpha_composite(shadow, layer)


def handle():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sym = Image.open(f"{BV}/logo/bviro_sym_white.png").convert("RGBA")
    sym = sym.resize((int(sym.size[0] * 50 / sym.size[1]), 50), Image.LANCZOS)
    f = ImageFont.truetype(f"{BV}/fonts/Tajawal-Bold.ttf", 44)
    pw, ph = int(sym.size[0] + 16 + d.textlength("@bviro.1", font=f) + 56), 80
    x, y = (W - pw) // 2, 44
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=(*DARK, 215))
    layer.alpha_composite(sym, (x + 24, y + (ph - 50) // 2))
    d.text((x + 24 + sym.size[0] + 14, y + ph / 2 + 1), "@bviro.1", font=f, fill=WHITE, anchor="lm")
    return layer


# ---------------- build ----------------
def main():
    os.makedirs(f"{WD}/out", exist_ok=True)
    os.makedirs(f"{WD}/ov", exist_ok=True)
    env = lipsync.envelope(f"{WD}/vo.mp3")
    mouth = lipsync.Mouth(f"{AV}/mouth")
    hook, sh_hook = talking_shot("pose_wearing_talk.png", T_HOOK, SAY_HOOK, CAM_HOOK, mouth, env, fx=orb_fx)
    lenses, sh_lenses = talking_shot("pose_lenses.png", T_LENSES, SAY_LENSES, CAM_LENSES, mouth, env, blinks=BLINK_LENSES)
    close, sh_close = talking_shot("pose_holding.png", T_CLOSE, SAY_CLOSE, CAM_CLOSE, mouth, env, blinks=BLINK_CLOSE)
    world = read_frames(f"{WD}/world.mp4", T_ZOOM[1] - WORLD_OFFSET, frames_between(T_ZOOM[1], T_WORLD[1]))
    (s0, s1), c = CAM_LENSES
    lens_now = tuple((c[0] + (x - c[0]) * s1, c[1] + (y - c[1]) * s1) for x, y in POSE_LENS)
    frames = hook + lenses + lens_sequence(world, lenses[-1], lens_now) + list(world[frames_between(T_ZOOM[1], T_WORLD[0]):]) + close
    assert len(frames) == frames_between(0, TOTAL), (len(frames), frames_between(0, TOTAL))
    write_video(frames, f"{WD}/out/_silent.mp4")
    layers = [(a, b, caption(lines)) for a, b, lines in CARDS]
    layers.append((END_CARD[0], END_CARD[1], caption([[("احفظه", CHIP)]], size=150, cy=1440)))
    layers.append((T_HOOK[1], TOTAL, handle()))
    inputs, fc, last = ["-i", f"{WD}/out/_silent.mp4", "-i", f"{WD}/vo.mp3"], [], "0:v"
    for k, (a, b, layer) in enumerate(layers):
        layer.save(f"{WD}/ov/l{k}.png")
        inputs += ["-loop", "1", "-i", f"{WD}/ov/l{k}.png"]
        fc.append(f"[{last}][{k + 2}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[o{k}]")
        last = f"o{k}"
    fc.append(f"[1:a]apad=whole_dur={TOTAL},loudnorm=I=-14:TP=-1.5:LRA=11[ao]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", f"[{last}]", "-map", "[ao]",
                    "-t", f"{TOTAL:.2f}", "-r", str(FPS), "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", f"{WD}/out/bviro_vr_ep3.mp4"], check=True)
    for name, sh in (("hook", sh_hook), ("lenses", sh_lenses), ("close", sh_close)):
        print(name, " ".join(sh))
    print("ok", TOTAL)


if __name__ == "__main__":
    main()
