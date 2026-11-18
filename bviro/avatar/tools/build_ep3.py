"""«صورة لكل عين» (الـVR من الصفر، حلقة 3) — avatar reel builder.
Shots: A headset on, reaching (hook) -> B shows the lenses, speaking -> match-zoom into the lenses ->
the virtual world plays inside both lenses (one image per eye) -> the two images merge and fill the screen ->
full-screen virtual world -> E closing line + «احفظه».

usage: python3 -I build_ep3.py WORKDIR STEP
  STEP = base  : write lipsync base video + audio (B then E) into WORKDIR/sync_base.mp4, sync_audio.mp3
  STEP = final : build WORKDIR/out/bviro_vr_ep3.mp4 (needs WORKDIR/sync_out.mp4 from the lipsync job)
WORKDIR holds: cA.mp4 cB2.mp4 cD.mp4 cE.mp4 k2c_closeup.png vo_b.mp3
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BV = os.path.dirname(os.path.dirname(HERE))  # bviro/
WD, STEP = sys.argv[1], sys.argv[2]
W, H, FPS = 1080, 1920, 24
PURPLE, TURQ, DARK, WHITE = (127, 2, 254), (0, 205, 200), (43, 1, 87), (255, 255, 255)
CHIP, TCHIP = "chip", "tchip"

# ---- timeline (seconds on the final video; the voice track runs from 0 unchanged) ----
VO_LEN = 16.88
T_A = (0.00, 2.25)      # cA local A_IN..
A_IN = 0.30
T_B = (2.25, 6.40)      # lens shot, lipsynced
T_ZOOM = (6.40, 7.10)   # match-zoom from B's last frame into the close-up
T_LENS = (7.10, 9.55)   # close-up, world inside both lenses
T_MERGE = (9.55, 10.45)
T_WORLD = (10.45, 14.75)
T_E = (14.75, 18.90)    # closing, lipsynced
D_OFF = 6.30            # world clip time = video time - D_OFF
E_IN, E_OUT = 3.00, 4.95  # stable part of cE, played forward then backward
TOTAL = T_E[1]

# close-up keyframe geometry at 1080x1920
LENS_L, LENS_R, LENS_R0 = (298.0, 955.0), (783.0, 955.0), 186.0
MID = (540.5, 955.0)
# lens centres in B's last frame (1080x1920), measured by lens_probe() below
B_LENS = None


def run(cmd):
    subprocess.run(cmd, check=True)


def n_frames(t0, t1):
    return int(round((t1 - t0) * FPS))


def read_frames(path, t0, n, vf=""):
    """n frames from path starting at t0 as uint8 array (n, H, W, 3)."""
    f = f"fps={FPS},scale={W}:{H}:flags=lanczos" + (("," + vf) if vf else "")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.4f}", "-i", path, "-frames:v", str(n), "-vf", f,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
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


def zoomed(img, s, src_c, dst_c):
    """Scale PIL img by s so that source point src_c lands on dst_c; output W x H."""
    a = 1.0 / s
    return img.transform((W, H), Image.AFFINE, (a, 0, src_c[0] - dst_c[0] * a, 0, a, src_c[1] - dst_c[1] * a), resample=Image.BICUBIC)


def disc(c, r, feather=2.0):
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.hypot(xx - c[0], yy - c[1])
    return np.clip((r - d) / feather + 0.5, 0, 1).astype(np.float32)


# ---------------- steps ----------------
def e_frames():
    n = n_frames(*T_E)
    fwd = read_frames(f"{WD}/cE.mp4", E_IN, n_frames(E_IN, E_OUT))
    seq = list(fwd) + list(fwd[-2:0:-1])
    return np.stack([seq[i % len(seq)] for i in range(n)])


def step_base():
    nb = n_frames(*T_B)
    b = read_frames(f"{WD}/cB2.mp4", 0.0, nb)
    write_video(list(b) + list(e_frames()), f"{WD}/sync_base.mp4")
    db, de = T_B[1] - T_B[0], T_E[1] - T_E[0]
    run(["ffmpeg", "-v", "error", "-y", "-i", f"{WD}/vo_b.mp3", "-filter_complex",
         f"[0:a]atrim={T_B[0]}:{T_B[1]},asetpts=PTS-STARTPTS,apad=whole_dur={db}[a0];"
         f"[0:a]atrim={T_E[0]}:{VO_LEN},asetpts=PTS-STARTPTS,apad=whole_dur={de}[a1];[a0][a1]concat=n=2:v=0:a=1[a]",
         "-map", "[a]", "-ar", "44100", "-ac", "1", "-b:a", "192k", f"{WD}/sync_audio.mp3"])
    print("base ok", nb + n_frames(*T_E), "frames")


def cairo(size, weight=900):
    f = ImageFont.truetype(f"{BV}/fonts/Cairo-VF.ttf", size)
    f.set_variation_by_axes([weight, 0])
    return f


def tw(d, t, font):
    return d.textlength(t, font=font, direction="rtl", language="ar")


def draw_line(img, segs, font, cy, stroke=10):
    d = ImageDraw.Draw(img)
    gap, pad = int(font.size * 0.26), int(font.size * 0.20)
    widths = [tw(d, t, font) + (2 * pad if c in (CHIP, TCHIP) else 0) for t, c in segs]
    total = sum(widths) + gap * (len(segs) - 1)
    assert total < W - 80, (segs, total)
    x = W / 2 + total / 2
    for (text, col), w in zip(segs, widths):
        x -= w
        if col in (CHIP, TCHIP):
            h = int(font.size * 1.18)
            d.rounded_rectangle([x, cy - h / 2 + 4, x + w, cy + h / 2 + 4], radius=int(h * 0.28), fill=PURPLE if col == CHIP else TURQ)
            d.text((x + pad, cy), text, font=font, fill=WHITE if col == CHIP else DARK, anchor="lm", direction="rtl", language="ar")
        else:
            d.text((x, cy), text, font=font, fill=col, anchor="lm", direction="rtl", language="ar", stroke_width=stroke, stroke_fill=DARK)
        x -= gap


def caption(lines, size=92, cy=1465, lead=1.36):
    font = cairo(size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    step = int(size * lead)
    y0 = cy - step * (len(lines) - 1) / 2
    for i, segs in enumerate(lines):
        draw_line(layer, segs, font, y0 + i * step)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.6))
    sh.paste((20, 0, 45, 255), (0, 10), a)
    return Image.alpha_composite(sh, layer)


def handle():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sym = Image.open(f"{BV}/logo/bviro_sym_white.png").convert("RGBA")
    sh = 50
    sym = sym.resize((int(sym.size[0] * sh / sym.size[1]), sh), Image.LANCZOS)
    f = ImageFont.truetype(f"{BV}/fonts/Tajawal-Bold.ttf", 44)
    txt = "@bviro.1"
    t = d.textlength(txt, font=f)
    pw, ph = int(sym.size[0] + 16 + t + 56), 80
    x, y = (W - pw) // 2, 44
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=(*DARK, 215))
    layer.alpha_composite(sym, (x + 24, y + (ph - sh) // 2))
    d.text((x + 24 + sym.size[0] + 14, y + ph / 2 + 1), txt, font=f, fill=WHITE, anchor="lm")
    return layer


# captions: (start, end, lines) on the final timeline; words follow the voice take (vo_b)
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


def lens_block(world):
    """Frames for T_ZOOM + T_LENS + T_MERGE (returns list of uint8 arrays)."""
    k2c = Image.open(f"{WD}/k2c_closeup.png").convert("RGB").resize((W, H), Image.LANCZOS)
    k2c_np = np.asarray(k2c).astype(np.float32)
    b_last = Image.fromarray(read_frames(f"{WD}/sync_out.mp4", (T_B[1] - T_B[0]) - 1.0 / FPS, 1)[0])
    (blx, bly), (brx, bry) = B_LENS
    b_mid = ((blx + brx) / 2, (bly + bry) / 2)
    s_end = (LENS_R[0] - LENS_L[0]) / (brx - blx)
    out = []
    # 1) match-zoom: B's last frame grows until its lenses sit exactly on the close-up's lenses, then cross-fades
    nz = n_frames(*T_ZOOM)
    for i in range(nz):
        acc = np.zeros((H, W, 3), np.float32)
        for sub in range(4):  # motion blur
            p = ease((i + sub / 4) / nz) ** 1.6
            s = 1.0 * (s_end ** p)
            dst = (b_mid[0] + (MID[0] - b_mid[0]) * p, b_mid[1] + (MID[1] - b_mid[1]) * p)
            acc += np.asarray(zoomed(b_last, s, b_mid, dst), np.float32)
        fr = acc / 4
        a = ease((i / nz - 0.55) / 0.45)
        out.append((fr * (1 - a) + k2c_np * a).astype(np.uint8))
    # 2) + 3) close-up with the world inside both lenses, then merge to full screen
    nl, nm = n_frames(*T_LENS), n_frames(*T_MERGE)
    for j in range(nl + nm):
        t = T_LENS[0] + j / FPS
        pm = ease((t - T_MERGE[0]) / (T_MERGE[1] - T_MERGE[0])) if t >= T_MERGE[0] else 0.0
        k = 1.0 + 0.06 * (t - T_LENS[0]) / (T_LENS[1] - T_LENS[0]) if pm == 0 else 1.06 + 0.5 * pm
        bg = np.asarray(zoomed(k2c, k, MID, MID), np.float32)
        wf = Image.fromarray(world[n_frames(T_ZOOM[1], T_LENS[0]) + j])
        fade = ease((t - T_LENS[0]) / 0.30)
        fr = bg.copy()
        r = LENS_R0 * k * (1 - pm) + 1180.0 * pm
        s_lens = 2 * LENS_R0 * k * 1.30 / W
        s_c = s_lens * (1 - pm) + 1.0 * pm
        for sign, c0 in ((+1, LENS_L), (-1, LENS_R)):
            cx = MID[0] + (c0[0] - MID[0]) * k
            cy = MID[1] + (c0[1] - MID[1]) * k
            c = (cx + (W / 2 - cx) * pm, cy + (H / 2 - cy) * pm)
            par = sign * 9.0 * (1 - pm)  # each eye gets a slightly shifted picture
            content = np.asarray(zoomed(wf, s_c, (W / 2 + par / s_c, H / 2), c), np.float32)
            m = disc(c, r)[..., None] * fade
            glass = np.clip(bg, 0, 255) * (1 - pm) * 0.9  # keep the lens highlight over the picture (screen blend)
            lit = 255 - (255 - content) * (255 - glass) / 255
            fr = fr * (1 - m) + lit * m
        out.append(np.clip(fr, 0, 255).astype(np.uint8))
    return out


def step_final():
    os.makedirs(f"{WD}/out", exist_ok=True)
    os.makedirs(f"{WD}/ov", exist_ok=True)
    frames = []
    frames += list(read_frames(f"{WD}/cA.mp4", A_IN, n_frames(*T_A)))
    nb, ne = n_frames(*T_B), n_frames(*T_E)
    frames += list(read_frames(f"{WD}/sync_out.mp4", 0.0, nb))
    world = read_frames(f"{WD}/cD.mp4", T_ZOOM[1] - D_OFF, n_frames(T_ZOOM[1], T_WORLD[1]))
    frames += lens_block(world)
    frames += list(world[n_frames(T_ZOOM[1], T_WORLD[0]):])
    frames += list(read_frames(f"{WD}/sync_out.mp4", nb / FPS, ne))
    assert len(frames) == n_frames(0, TOTAL), (len(frames), n_frames(0, TOTAL))
    write_video(frames, f"{WD}/out/_silent.mp4")
    # overlays
    inputs, fc, last = ["-i", f"{WD}/out/_silent.mp4", "-i", f"{WD}/vo_b.mp3"], [], "0:v"
    layers = [(a, b, caption(lines)) for a, b, lines in CARDS]
    end = caption([[("احفظه", CHIP)]], size=150, cy=1440)
    layers.append((END_CARD[0], END_CARD[1], end))
    layers.append((T_A[1], TOTAL, handle()))
    for k, (a, b, layer) in enumerate(layers):
        p = f"{WD}/ov/l{k}.png"
        layer.save(p)
        inputs += ["-loop", "1", "-i", p]
        fc.append(f"[{last}][{k + 2}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[o{k}]")
        last = f"o{k}"
    fc.append(f"[1:a]apad=whole_dur={TOTAL},loudnorm=I=-14:TP=-1.5:LRA=11[ao]")
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", f"[{last}]", "-map", "[ao]", "-t", f"{TOTAL:.2f}",
         "-r", str(FPS), "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-movflags", "+faststart", f"{WD}/out/bviro_vr_ep3.mp4"])
    print("final ok", TOTAL)


if __name__ == "__main__":
    if os.path.exists(f"{WD}/b_lens.txt"):
        v = [float(x) for x in open(f"{WD}/b_lens.txt").read().split()]
        B_LENS = ((v[0], v[1]), (v[2], v[3]))
    {"base": step_base, "final": step_final}[STEP]()
