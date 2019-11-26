#!/usr/bin/python3

import sys

from PIL import Image

argv = sys.argv

im = Image.open(sys.argv[1])
im = im.convert("RGBA")

cx = im.size[0] / 2
cy = im.size[1] / 2
r = min(cx, cy)

if len(argv) > 3:
  r += int(argv[3])
if len(argv) > 4:
  cx += int(argv[4])
if len(argv) > 5:
  cy += int(argv[5])

for j in range(im.size[1]):
  for i in range(im.size[0]):
    if (i-cx)*(i-cx) + (j-cy)*(j-cy) > r*r:
      im.putpixel((i,j),(0,0,0,0))

out = im.crop((int(cx-r), int(cy-r), int(cx+r), int(cy+r)))
out = out.resize((700,700), Image.BICUBIC)


out.save(sys.argv[2])
