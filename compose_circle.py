#!/usr/bin/python3

from PIL import Image

ROTATIONS = (1,3,3,5,2,3,6,5,1,6,2,10,2,4,1,4,2,4,1,5,3,3)

mask = Image.open("mask.png")

for i, r in enumerate(ROTATIONS):
  im = Image.open(f"{i+1:02d}.png")
  out = Image.new("RGBA", (720, 720), (0,0,0,0))

  out.paste(im, (10,10), mask=im)
  out.paste(mask, (0,0), mask=mask)

  out = out.rotate(215-r*30, Image.BICUBIC)

  fn = f"w{i+1:02d}.png"
  out.save(fn)
  print(r, fn)
