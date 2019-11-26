#!/usr/bin/python3

import argparse
import os
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true")
options = parser.parse_args()

with zipfile.ZipFile("masked_images.zip", mode="w") as z:
  with z.open("puzzle.html", "w") as f_out:
    with open("masked_images.html", "rb") as f_in:

      html = f_in.read()

      if options.debug:
        head = ('<link rel=stylesheet href="/maskdebug/masked_images.css" />'
                '<script src="/closure/goog/base.js"></script>'
                '<script src="/maskdebug/masked_images.js"></script>')
      else:
        head = ('<link rel=stylesheet href="masked_images.css" />'
                '<script src="masked_images-compiled.js"></script>')

      html = html.replace(b"@HEAD@", head.encode("utf-8"))

      f_out.write(html)

  with z.open("solution.html", "w") as f_out:
    with open("solution.html", "rb") as f_in:
      f_out.write(f_in.read())

  with z.open("metadata.yaml", "w") as f_out:
    with open("metadata.yaml", "rb") as f_in:
      f_out.write(f_in.read())

  for i in ("vman.jpg", "vmanmasked.jpg"):
    with z.open("solution/"+i, "w") as f_out:
      with open("solution/"+i, "rb") as f_in:
        f_out.write(f_in.read())

  for i in range(1, 23):
    with z.open(f"{i:02d}.png", "w") as f_out:
      with open(f"w{i:02d}.png", "rb") as f_in:
        f_out.write(f_in.read())

  if not options.debug:
    with z.open("masked_images.css", "w") as f_out:
      with open("masked_images.css", "rb") as f_in:
        f_out.write(f_in.read())

    with z.open("masked_images-compiled.js", "w") as f_out:
      with open("masked_images-compiled.js", "rb") as f_in:
        f_out.write(f_in.read())

