"""usage: grid.py OUT.jpg COLS img1 img2 ... -> tile images (resized to the first one's size)"""
import sys
from PIL import Image
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert("RGB") for f in files]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
o = Image.new("RGB", (w * cols, h * rows), "white")
for i, im in enumerate(ims):
    o.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
o.save(out, quality=88)
