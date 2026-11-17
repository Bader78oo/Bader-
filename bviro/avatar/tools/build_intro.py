"""Avatar intro reel: re-cut the lip-synced talking shot so it opens on the hook, add captions and brand mark.
Order: hook (misconception) -> who is speaking -> what the account does -> one action.
usage: python3 -I build_intro.py SRC_VIDEO VOICE_MP3 OUT_MP4   (run from anywhere; assets resolve from this file)
"""
import os
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.dirname(os.path.dirname(HERE))  # bviro/
SRC, VO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
OV = os.path.join(os.path.dirname(os.path.abspath(OUT)), "ov")
os.makedirs(OV, exist_ok=True)
W, H = 1080, 1920
PURPLE, TURQ, DARK, WHITE = (127, 2, 254), (0, 205, 200), (43, 1, 87), (255, 255, 255)
CHIP, TCHIP = "chip", "tchip"

# (source start, source end, zoom) in the voice track's own time; cuts sit inside the pauses
SEGS = [(7.62, 15.34, 1.00), (1.20, 7.56, 1.14), (15.38, 23.10, 1.00)]


def new_t(src_t):
    off = 0.0
    for a, b, _ in SEGS:
        if a <= src_t <= b:
            return off + src_t - a
        off += b - a
    raise ValueError(src_t)


def cairo(size, weight=900):
    f = ImageFont.truetype(f"{B}/fonts/Cairo-VF.ttf", size)
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


def caption(name, lines, size=92, cy=1465, lead=1.36):
    font = cairo(size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    step = int(size * lead)
    y0 = cy - step * (len(lines) - 1) / 2
    for i, segs in enumerate(lines):
        draw_line(layer, segs, font, y0 + i * step)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.6))
    sh.paste((20, 0, 45, 255), (0, 10), a)
    Image.alpha_composite(sh, layer).save(f"{OV}/{name}.png")


def handle():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sym = Image.open(f"{B}/logo/bviro_sym_white.png").convert("RGBA")
    sh = 50
    sym = sym.resize((int(sym.size[0] * sh / sym.size[1]), sh), Image.LANCZOS)
    f = ImageFont.truetype(f"{B}/fonts/Tajawal-Bold.ttf", 44)
    txt = "@bviro.1"
    t = d.textlength(txt, font=f)
    pw, ph = int(sym.size[0] + 16 + t + 56), 80
    x, y = (W - pw) // 2, 44
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=(*DARK, 215))
    layer.alpha_composite(sym, (x + 24, y + (ph - sh) // 2))
    d.text((x + 24 + sym.size[0] + 14, y + ph / 2 + 1), txt, font=f, fill=WHITE, anchor="lm")
    layer.save(f"{OV}/handle.png")


# name, lines, source start, source end
CARDS = [
    ("c1", [[("واجد ناس يحسبوا", WHITE)], [("الـVR", WHITE), ("ألعاب أطفال", CHIP)]], 7.62, 10.95),
    ("c2", [[("لا!", TURQ)], [("الـVR", WHITE), ("عالم كبير", TCHIP)]], 11.08, 12.75),
    ("c3", [[("تدريب", WHITE), ("·", TURQ), ("طب", WHITE)], [("طيران", WHITE), ("·", TURQ), ("تعليم", WHITE)]], 12.90, 15.34),
    ("c4", [[("أنا بدر الريسي", WHITE)], [("النسخة الرقمية", CHIP)]], 1.25, 3.80),
    ("c5", [[("بدر الأصلي مشغول", WHITE)], [("وأنا هنا", WHITE), ("أشرح لكم", TCHIP)]], 3.90, 7.56),
    ("c6", [[("نشرح لك الـVR", WHITE)], [("بالعماني", CHIP), ("من الصفر", WHITE)]], 15.40, 18.60),
    ("c7", [[("كيف يشتغل", WHITE)], [("ووين ينفع", WHITE)]], 18.80, 20.45),
    ("c8", [[("عندك سؤال عن الـVR؟", WHITE)], [("أرسله في الخاص", CHIP)]], 20.62, 23.10),
]
for name, lines, _, _ in CARDS:
    caption(name, lines)
handle()

fc, vouts, aouts = [], [], []
for i, (a, b, z) in enumerate(SEGS):
    sw, shh = int(round(W * z / 2) * 2), int(round(H * z / 2) * 2)
    crop = f",crop={W}:{H}:{(sw - W) // 2}:{int((shh - H) * 0.30)}" if z > 1 else ""
    fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS,scale={sw}:{shh}:flags=lanczos{crop},unsharp=5:5:0.6,setsar=1[v{i}]")
    d = b - a
    fc.append(f"[1:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={d - 0.03:.3f}:d=0.03[a{i}]")
    vouts.append(f"[v{i}]")
    aouts.append(f"[a{i}]")
n = len(SEGS)
fc.append(f"{''.join(vouts)}concat=n={n}:v=1:a=0[vc]")
fc.append(f"{''.join(aouts)}concat=n={n}:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11[ao]")
inputs = ["-i", SRC, "-i", VO]
last = "vc"
for k, (name, _, a, b) in enumerate(CARDS):
    inputs += ["-loop", "1", "-i", f"{OV}/{name}.png"]
    t0, t1 = new_t(a), new_t(b)
    fc.append(f"[{last}][{k + 2}:v]overlay=0:0:enable='between(t,{t0:.2f},{t1:.2f})'[o{k}]")
    last = f"o{k}"
inputs += ["-loop", "1", "-i", f"{OV}/handle.png"]
fc.append(f"[{last}][{len(CARDS) + 2}:v]overlay=0:0:enable='gte(t,{new_t(1.25):.2f})'[vo]")
total = sum(b - a for a, b, _ in SEGS)
cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vo]", "-map", "[ao]", "-t", f"{total:.2f}",
       "-r", "24", "-c:v", "libx264", "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
       "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True)
print("ok", OUT, round(total, 2), "s")
for name, _, a, b in CARDS:
    print(name, round(new_t(a), 2), round(new_t(b), 2))
