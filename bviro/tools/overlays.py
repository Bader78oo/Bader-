"""Render the Reel's text overlays and the brand outro layers as 1080x1920 RGBA PNGs (real fonts, RTL shaping)."""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = "/tmp/claude-0/-home-user-Bader-/871f84b2-2289-5b97-9b32-a74e478b68cd/scratchpad/bviro"
W, H = 1080, 1920
PURPLE, TURQ, DARK, WHITE = (127, 2, 254), (0, 205, 200), (43, 1, 87), (255, 255, 255)


def cairo(size, weight=900):
    f = ImageFont.truetype(f"{S}/fonts/Cairo-VF.ttf", size)
    f.set_variation_by_axes([weight, 0])
    return f


def tajawal(size, w="Bold"):
    return ImageFont.truetype(f"{S}/fonts/Tajawal-{w}.ttf", size)


def seg_width(d, segs, font, gap):
    return sum(d.textlength(t, font=font, direction="rtl", language="ar") for t, _ in segs) + gap * (len(segs) - 1)


def draw_line(img, segs, font, cy, stroke=10, gap=None, cx=W // 2):
    """segs: [(text, colour)] in reading order (right to left)."""
    d = ImageDraw.Draw(img)
    gap = gap if gap is not None else int(font.size * 0.26)
    total = seg_width(d, segs, font, gap)
    x = cx + total / 2
    for text, col in segs:
        w = d.textlength(text, font=font, direction="rtl", language="ar")
        x -= w
        d.text((x, cy), text, font=font, fill=col, anchor="lm", direction="rtl", language="ar",
               stroke_width=stroke, stroke_fill=DARK)
        x -= gap
    return total


def caption(name, lines, size=104, cy=470, lead=1.28):
    """lines: list of segment lists. Soft shadow + dark-purple stroke, centred block at cy."""
    font = cairo(size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    step = int(size * lead)
    y0 = cy - step * (len(lines) - 1) / 2
    for i, segs in enumerate(lines):
        draw_line(layer, segs, font, y0 + i * step)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.55))
    sh.paste((20, 0, 45, 255), (0, 10), a)
    out = Image.alpha_composite(sh, layer)
    out.save(f"{S}/ov/{name}.png")
    return out


def logo(name, h):
    im = Image.open(f"{S}/logo/{name}.png").convert("RGBA")
    return im.resize((int(im.size[0] * h / im.size[1]), h), Image.LANCZOS)


def outro():
    # background
    bg = Image.new("RGB", (W, H), DARK)
    glow = Image.new("L", (W, H), 0)
    g = ImageDraw.Draw(glow)
    for r in range(900, 0, -20):
        g.ellipse([W / 2 - r, 640 - r, W / 2 + r, 640 + r], fill=int(120 * (1 - r / 900) ** 1.6))
    bg = Image.composite(Image.new("RGB", (W, H), PURPLE), bg, glow.filter(ImageFilter.GaussianBlur(40)))
    arcs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = ImageDraw.Draw(arcs)
    for k, r in enumerate(range(260, 1500, 62)):
        a.ellipse([W / 2 - r, H + 120 - r, W / 2 + r, H + 120 + r], outline=(177, 99, 255, max(8, 46 - k * 2)), width=3)
    bg = Image.alpha_composite(bg.convert("RGBA"), arcs)
    bg.convert("RGB").save(f"{S}/ov/outro_bg.png")

    def layer():
        return Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # symbol
    l1 = layer(); s = logo("bviro_sym_white", 250); l1.alpha_composite(s, ((W - s.size[0]) // 2, 310)); l1.save(f"{S}/ov/outro_sym.png")
    # wordmarks: Arabic right, Latin left, thin divider
    l2 = layer(); ar = logo("bviro_ara_white", 92); la = logo("bviro_lat_white", 76)
    gap = 44; total = ar.size[0] + la.size[0] + gap * 2 + 3; x0 = (W - total) // 2; y = 630
    l2.alpha_composite(la, (x0, y + 10)); ImageDraw.Draw(l2).rectangle([x0 + la.size[0] + gap, y + 4, x0 + la.size[0] + gap + 3, y + 92], fill=(255, 255, 255, 110))
    l2.alpha_composite(ar, (x0 + la.size[0] + gap * 2 + 3, y)); l2.save(f"{S}/ov/outro_word.png")
    # tagline
    l3 = layer(); f = cairo(82)
    for i, segs in enumerate([[("نودّيك أي مكان", WHITE)], [("وانت في مكانك", TURQ)]]):
        d = ImageDraw.Draw(l3); cx = W // 2
        gapw = int(f.size * 0.26); tot = seg_width(d, segs, f, gapw); x = cx + tot / 2
        for t, col in segs:
            w = d.textlength(t, font=f, direction="rtl", language="ar"); x -= w
            d.text((x, 870 + i * 118), t, font=f, fill=col, anchor="lm", direction="rtl", language="ar"); x -= gapw
    l3.save(f"{S}/ov/outro_tag.png")
    # services
    l4 = layer(); d = ImageDraw.Draw(l4); fs = tajawal(46, "Bold")
    d.text((W // 2, 1125), "تجارب VR  ·  تصوير 360  ·  شاشات LED", font=fs, fill=(214, 190, 255), anchor="mm", direction="rtl", language="ar")
    l4.save(f"{S}/ov/outro_srv.png")
    # CTA pill + handle
    l5 = layer(); d = ImageDraw.Draw(l5); fc = cairo(64)
    txt = "أرسل VR بالخاص"; tw = d.textlength(txt, font=fc, direction="rtl", language="ar")
    pw, ph = int(tw + 130), 132; px, py = (W - pw) // 2, 1228
    d.rounded_rectangle([px, py, px + pw, py + ph], radius=ph // 2, fill=TURQ)
    d.text((W // 2, py + ph // 2 - 4), txt, font=fc, fill=DARK, anchor="mm", direction="rtl", language="ar")
    d.text((W // 2, 1410), "@bviro.1", font=tajawal(44, "Medium"), fill=(214, 190, 255), anchor="mm")
    l5.save(f"{S}/ov/outro_cta.png")


caption("t1", [[("ليش هالناقة", WHITE)], [("لابسة نظارة", WHITE), ("VR؟", TURQ)]], size=112, cy=430)
caption("t2", [[("حتى راعيها", WHITE)], [("ما فاهم ايش صاير", WHITE)]], size=96, cy=430)
caption("t3a", [[("هي الحين في", WHITE)], [("خريف صلالة", TURQ)]], size=108, cy=420)
caption("t3b", [[("خضرة.. وضباب.. وشلالات", WHITE)]], size=84, cy=420)
caption("t4", [[("وهي ما تحركت", WHITE)], [("من الرمل", TURQ)]], size=108, cy=430)
caption("t5", [[("والحين دور", WHITE), ("راعيها", TURQ)]], size=104, cy=400)
outro()
# previews
prev = Image.open(f"{S}/ov/outro_bg.png").convert("RGBA")
for n in ("outro_sym", "outro_word", "outro_tag", "outro_srv", "outro_cta"):
    prev = Image.alpha_composite(prev, Image.open(f"{S}/ov/{n}.png"))
prev.convert("RGB").resize((540, 960)).save(f"{S}/an/outro_prev.jpg", quality=90)
print("ok")
