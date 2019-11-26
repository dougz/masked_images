#!/usr/bin/python3

import math
from PIL import Image

SIZE = (1440, 1440)

mask = Image.new("RGBA", SIZE, (0,0,0,0))

MIN_THETA = -140 * math.pi / 180.0
MAX_THETA = -110 * math.pi / 180.0

for j in range(SIZE[1]):
  for i in range(SIZE[0]):
    if (i-720)*(i-720) + (j-720)*(j-720) < 720*720:
      theta = math.atan2(720-j, i-720)
      if not (MIN_THETA <= theta <= MAX_THETA):
        mask.putpixel((i,j),(0,0,0,255))

mask = mask.resize((720,720), Image.BICUBIC)

mask.save("mask.png")
