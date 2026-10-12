"""
Prepare the profile picture (a flat illustration) for clean ASCII conversion:
  1. remove the background (rembg) so the subject is isolated
  2. bilateral-smooth away texture (otherwise skin turns to noise and the
     eyes drown in it) while keeping the drawn lines sharp
  3. stretch tones so skin lands near white and hair/lines stay dark
  4. darken the line work (difference-of-gaussians ridges) -- eyelids, pupils
     and smile are thin dark strokes that plain luminance averaging washes
     out at ascii resolution
  5. composite onto white and crop square around the subject

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.
Only needs to run locally, once, when the photo changes.

    python scripts/prep_photo.py [input.png] [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

LINE_WEIGHT = float(os.environ.get("LINE_WEIGHT", 0.6))   # how hard drawn lines are pushed toward black
# BG=white -> background becomes white (blanked by WHITE_FLOOR in make_ascii_svg.py, "negative" look:
#             dark hair prints dense/bright). BG=black -> background becomes black, for INVERT=1 in
#             make_ascii_svg.py ("positive" look: bright skin prints dense/bright, dark areas stay sparse).
BG_VALUE = 255.0 if os.environ.get("BG", "black").lower() == "white" else 0.0

# 1. cut out the subject
cut = remove(Image.open(INP).convert("RGBA"))
rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])                 # 0 = background
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# 2. smooth texture, keep edges
smooth = gray
for _ in range(3):
    smooth = cv2.bilateralFilter(smooth, 9, 40, 9)

# 3. tone stretch over the subject only
lo, hi = np.percentile(smooth[alpha > 128], [2, 92])
tone = np.clip((smooth.astype(np.float32) - lo) / (hi - lo), 0, 1)

# 4. dark-on-light ridges -> darken
fine = cv2.GaussianBlur(smooth, (0, 0), 1.5).astype(np.float32)
coarse = cv2.GaussianBlur(smooth, (0, 0), 6).astype(np.float32)
lines = np.clip((coarse - fine) / 40.0, 0, 1)
out = np.clip(tone - LINE_WEIGHT * lines, 0, 1) * 255

# 5. paste onto the background colour (feathered a hair to avoid a halo), square crop
mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
out = out * mask + BG_VALUE * (1.0 - mask)

ys, xs = np.where(alpha > 20)
side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 60
cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
canvas = np.full((side, side), int(BG_VALUE), np.uint8)
x0, y0 = cx - side // 2, cy - side // 2
sx0, sy0 = max(x0, 0), max(y0, 0)
sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)

Image.fromarray(canvas, mode="L").save(OUT)
print("wrote", OUT, canvas.shape)
