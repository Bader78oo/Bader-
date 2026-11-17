"""v2 overlays: highlight words sit in a purple chip (better contrast on sky), bigger list caption,
and the brand ending is laid over live footage (purple gradient + logo + tagline + large CTA) instead of a slate."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = "/tmp/claude-0/-home-user-Bader-/871f84b2-2289-5b97-9b32-a74e478b68cd/scratchpad/bviro"
W, H = 1080, 1920
PURPLE, TURQ, DARK, WHITE = (127, 2, 254), (0, 205, 200), (43, 1, 87), (255, 255, 255)
CHIP = "chip"


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
    widths = [tw(d, t, font) + (2 * pad if c == CHIP else 0) for t, c in segs]
    total = sum(widths) + gap * (len(segs) - 1)
    x = W / 2 + total / 2
    for (text, col), w in zip(segs, widths):
        x -= w
        if col == CHIP:
            h = int(font.size * 1.18)
            d.rounded_rectangle([x, cy - h / 2 + 4, x + w, cy + h / 2 + 4], radius=int(h * 0.28), fill=PURPLE)
            d.text((x + pad, cy), text, font=font, fill=WHITE, anchor="lm", direction="rtl", language="ar")
        else:
            d.text((x, cy), text, font=font, fill=col, anchor="lm", direction="rtl", language="ar", stroke_width=stroke, stroke_fill=DARK)
        x -= gap


def caption(name, lines, size=104, cy=430, lead=1.34):
    font = cairo(size)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    step = int(size * lead)
    y0 = cy - step * (len(lines) - 1) / 2
    for i, segs in enumerate(lines):
        draw_line(layer, segs, font, y0 + i * step)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.55))
    sh.paste((20, 0, 45, 255), (0, 10), a)
    Image.alpha_composite(sh, layer).save(f"{S}/ov2/{name}.png")


def logo(name, h):
    im = Image.open(f"{S}/logo/{name}.png").convert("RGBA")
    return im.resize((int(im.size[0] * h / im.size[1]), h), Image.LANCZOS)


def ending():
    # purple gradient: solid at the top, clear over the camel's face, solid again at the bottom
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = g.load()
    for y in range(H):
        if y < 760:
            a = 0.93 * (1 - max(0, (y - 520)) / 240) if y > 520 else 0.93
        elif y > 1100:
            a = min(0.93, 0.93 * (y - 1100) / 220)
        else:
            a = 0
        if a > 0:
            for x in range(W):
                px[x, y] = (*DARK, int(255 * a))
    g.save(f"{S}/ov2/end_grad.png")

    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sym, ar, la = logo("bviro_sym_white", 104), logo("bviro_ara_white", 74), logo("bviro_lat_white", 60)
    gap = 30
    total = la.size[0] + gap + sym.size[0] + gap + ar.size[0]
    x0, y = (W - total) // 2, 250
    top.alpha_composite(la, (x0, y + 24)); top.alpha_composite(sym, (x0 + la.size[0] + gap, y)); top.alpha_composite(ar, (x0 + la.size[0] + gap * 2 + sym.size[0], y + 16))
    d = ImageDraw.Draw(top); f = cairo(88)
    for i, (t, col) in enumerate([("نودّيك أي مكان", WHITE), ("وانت في مكانك", TURQ)]):
        d.text((W / 2, 468 + i * 116), t, font=f, fill=col, anchor="mm", direction="rtl", language="ar")
    top.save(f"{S}/ov2/end_top.png")

    srv = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(srv)
    d.text((W / 2, 1262), "تجارب VR  ·  تصوير 360  ·  شاشات LED", font=tajawal(46, "Bold"), fill=(226, 208, 255), anchor="mm", direction="rtl", language="ar")
    srv.save(f"{S}/ov2/end_srv.png")

    cta = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(cta); fc = cairo(74)
    txt = "أرسل VR بالخاص"; w = tw(d, txt, fc); pw, ph = int(w + 150), 150; x, y = (W - pw) // 2, 1318
    d.rounded_rectangle([x, y, x + pw, y + ph], radius=ph // 2, fill=TURQ)
    d.text((W / 2, y + ph / 2 - 5), txt, font=fc, fill=DARK, anchor="mm", direction="rtl", language="ar")
    cta.save(f"{S}/ov2/end_cta.png")


caption("t1", [[("ليش هالناقة", WHITE)], [("لابسة نظارة", WHITE), ("VR؟", CHIP)]], size=112, cy=430)
caption("t2", [[("حتى راعيها", WHITE)], [("ما فاهم ايش صاير", WHITE)]], size=98, cy=420)
caption("t3a", [[("هي الحين في", WHITE)], [("خريف صلالة", CHIP)]], size=108, cy=420)
caption("t3b", [[("خضرة.. وضباب", WHITE)], [("وشلالات", WHITE)]], size=104, cy=420)
caption("t4", [[("وهي ما تحركت", WHITE)], [("من الرمل", CHIP)]], size=108, cy=430)
caption("t5", [[("والحين دور", WHITE), ("راعيها", CHIP)]], size=104, cy=400)
ending()
print("ok")
