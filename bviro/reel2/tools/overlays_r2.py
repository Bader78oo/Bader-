"""Reel 2 («الجو نزل درجتين») caption layers -> reel2/ov/*.png (1080x1920 RGBA).
White Cairo 900 with dark-purple stroke; the key word of each card sits in a brand-purple chip.
usage: python3 -I overlays_r2.py"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = "/tmp/claude-0/-home-user-Bader-/871f84b2-2289-5b97-9b32-a74e478b68cd/scratchpad/bviro"
OUT = f"{S}/reel2/ov"
W, H = 1080, 1920
PURPLE, TURQ, DARK, WHITE = (127, 2, 254), (0, 205, 200), (43, 1, 87), (255, 255, 255)
CHIP, TCHIP = "chip", "tchip"
os.makedirs(OUT, exist_ok=True)


def cairo(size, weight=900):
    f = ImageFont.truetype(f"{S}/fonts/Cairo-VF.ttf", size)
    f.set_variation_by_axes([weight, 0])
    return f


def tajawal(size, w="Bold"):
    return ImageFont.truetype(f"{S}/fonts/Tajawal-{w}.ttf", size)


def tw(d, t, font):
    return d.textlength(t, font=font, direction="rtl", language="ar")


def draw_line(img, segs, font, cy, stroke=10):
    d = ImageDraw.Draw(img)
    gap = int(font.size * 0.26)
    pad = int(font.size * 0.20)
    widths = [tw(d, t, font) + (2 * pad if c in (CHIP, TCHIP) else 0) for t, c in segs]
    total = sum(widths) + gap * (len(segs) - 1)
    assert total < W - 60, (segs, total)
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


def caption(name, lines, size=104, cy=430, lead=1.34):
    font = cairo(size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    step = int(size * lead)
    y0 = cy - step * (len(lines) - 1) / 2
    for i, segs in enumerate(lines):
        if segs:
            draw_line(layer, segs, font, y0 + i * step)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.55))
    sh.paste((20, 0, 45, 255), (0, 10), a)
    Image.alpha_composite(sh, layer).save(f"{OUT}/{name}.png")


def handle():
    """Small own-brand mark for the top of the frame from the reveal on: symbol + @bviro.1 in a dark pill."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sym = Image.open(f"{S}/logo/bviro_sym_white.png").convert("RGBA")
    sh = 58
    sym = sym.resize((int(sym.size[0] * sh / sym.size[1]), sh), Image.LANCZOS)
    f = tajawal(50, "Bold")
    txt = "@bviro.1"
    t = d.textlength(txt, font=f)
    pw, ph = int(sym.size[0] + 18 + t + 64), 92
    x, y = (W - pw) // 2, 228
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=(*DARK, 215))
    layer.alpha_composite(sym, (x + 26, y + (ph - sh) // 2))
    d.text((x + 26 + sym.size[0] + 16, y + ph / 2 + 1), txt, font=f, fill=WHITE, anchor="lm")
    layer.save(f"{OUT}/handle.png")


# main cut (hook A)
caption("c1", [[("الجو نزل", WHITE)], [("درجتين…", CHIP)]], size=124, cy=420)
caption("c2", [[("وربيعنا", WHITE)], [("أعلن الشتا", CHIP)]], size=116, cy=420)
caption("c3", [[("لبس الجاكيت…", WHITE)], [("وشبّ الضو", CHIP)]], size=110, cy=420)
caption("c4a", [[("والمكيّف…", WHITE)], []], size=116, cy=450)
caption("c4x", [[], [("بعده شغّال", CHIP)]], size=116, cy=450)
caption("c5a", [[("نودّيك أي مكان…", WHITE)], []], size=106, cy=450)
caption("c5x", [[], [("وانت في مكانك", TCHIP)]], size=106, cy=450)
caption("c6", [[("إهداء لأول واحد", WHITE)], [("لبس الجاكيت", CHIP)]], size=112, cy=450)
caption("c6send", [[("طرّشه لأول واحد", WHITE)], [("لبس الجاكيت", CHIP)]], size=112, cy=450)
caption("c7", [[("وكلنا نعرفه…", WHITE)], [("كل سنة", CHIP)]], size=112, cy=450)
caption("c3b", [[("وشبّ الضو", CHIP)]], size=124, cy=430)
# alternative hooks
caption("hB", [[("أول واحد", WHITE)], [("لبس الجاكيت", CHIP)]], size=120, cy=420)
caption("hB2", [[("الجو نزل", WHITE)], [("درجتين بس", CHIP)]], size=120, cy=420)
caption("hC", [[("ربيعنا", WHITE)], [("أعلن الشتا", CHIP)]], size=124, cy=420)
caption("cL3a", [[("لبس الجاكيت…", CHIP)]], size=116, cy=420)
# v4: the friend speaks (turquoise speech chips), and the ending names the brand and the service
caption("f1", [[("الحبيب..", TCHIP)]], size=124, cy=430)
caption("f2", [[("تراك في الـVR..", TCHIP)], []], size=112, cy=450)
caption("f3", [[], [("انتبه!", CHIP)]], size=124, cy=450)


def service():
    """small service line for the last shot: what the company actually offers"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = tajawal(50, "ExtraBold")
    txt = "تجارب واقع افتراضي VR"
    t = d.textlength(txt, font=f, direction="rtl", language="ar")
    pw, ph = int(t + 84), 96
    x, y = (W - pw) // 2, 1300
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=(*DARK, 225))
    d.text((W / 2, y + ph / 2 + 2), txt, font=f, fill=WHITE, anchor="mm", direction="rtl", language="ar")
    layer.save(f"{OUT}/service.png")


service()
handle()


def end_layers():
    """last shot: a top pill naming the brand and the service, the brand line under it, the handle low in the frame"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    sym = Image.open(f"{S}/logo/bviro_sym_white.png").convert("RGBA")
    sh = 60; sym = sym.resize((int(sym.size[0] * sh / sym.size[1]), sh), Image.LANCZOS)
    f = tajawal(50, "ExtraBold"); txt = "بيفيرو | تجارب واقع افتراضي VR"
    t = d.textlength(txt, font=f, direction="rtl", language="ar")
    pw, ph = int(sym.size[0] + 22 + t + 72), 100
    x, y = (W - pw) // 2, 224
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=PURPLE)
    d.text((x + 36, y + ph / 2 + 2), txt, font=f, fill=WHITE, anchor="lm", direction="rtl", language="ar")
    layer.alpha_composite(sym, (int(x + 36 + t + 22), y + (ph - sh) // 2))
    layer.save(f"{OUT}/brandpill.png")
    low = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(low)
    f = tajawal(46, "Bold"); txt = "@bviro.1"; t = d.textlength(txt, font=f)
    pw, ph = int(t + 72), 84; x, y = (W - pw) // 2, 1396
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=(*DARK, 220))
    d.text((W / 2, y + ph / 2 + 1), txt, font=f, fill=WHITE, anchor="mm")
    low.save(f"{OUT}/handle_low.png")


end_layers()
caption("e2", [[("نودّيك أي مكان", WHITE)], []], size=104, cy=478)
caption("e3", [[], [("وانت في مكانك", TCHIP)]], size=104, cy=478)
print("ok")
