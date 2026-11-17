"""usage: frames.py VIDEO OUT.jpg X0 Y0 X1 Y1 H t1 t2 ... -> row of crops (fractions) at given times, each H px tall"""
import subprocess, sys, tempfile, os
from PIL import Image
v, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = (float(a) for a in sys.argv[3:7]); H = int(sys.argv[7]); ts = sys.argv[8:]
tiles = []
tmp = tempfile.mkdtemp()
for t in ts:
    p = os.path.join(tmp, "f.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", v, "-frames:v", "1", p], check=True)
    im = Image.open(p).convert("RGB"); w, h = im.size
    c = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    tiles.append(c.resize((int(c.size[0] * H / c.size[1]), H), Image.LANCZOS))
o = Image.new("RGB", (sum(t.size[0] for t in tiles), H)); x = 0
for t in tiles: o.paste(t, (x, 0)); x += t.size[0]
o.save(out, quality=88)
