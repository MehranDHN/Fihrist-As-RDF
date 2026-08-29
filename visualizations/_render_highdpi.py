# -*- coding: utf-8 -*-
"""Render the complete Sa'di graph at ~300 dpi.

Graphviz/Cairo cannot emit one bitmap wider than 32767 px. This layout is
39852 pt wide; at 300 dpi that is ~166k px. We therefore:
  1) write overlapping 300 dpi tiles that cover the whole drawing
  2) write one combined PNG at the highest dpi that still fits Cairo
"""

from __future__ import print_function

import subprocess
import sys
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parents[1]
DOT = ROOT / "visualizations" / "cambridge_person_100206721.dot"
OUT_DIR = ROOT / "visualizations"

# From the SVG header: width="39852pt" height="1676pt"
GRAPH_W_PT = 39852.0
GRAPH_H_PT = 1676.25
DPI = 300
# Cairo max dimension ~32767 px. At 300 dpi, max tile width in points:
# 32767 * 72 / 300 = 7864.08
TILE_W_PT = 7800.0
CAIRO_MAX = 32767


def run_dot(args, out):
    cmd = ["dot"] + args + ["-o", str(out), str(DOT)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout or "dot failed\n")
        raise SystemExit(proc.returncode)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return out


def tiles():
    out_files = []
    x = 0.0
    i = 1
    while x < GRAPH_W_PT - 1:
        w = min(TILE_W_PT, GRAPH_W_PT - x)
        # viewport: W,H,Z,X,Y  with X,Y = center of the window in graph points
        cx = x + w / 2.0
        cy = GRAPH_H_PT / 2.0
        viewport = "%f,%f,1,%f,%f" % (w, GRAPH_H_PT, cx, cy)
        dest = OUT_DIR / ("cambridge_person_100206721_300dpi_tile%02d.png" % i)
        print("tile", i, "x0=", int(x), "w=", int(w), "->", dest.name)
        run_dot(["-Tpng", "-Gdpi=%d" % DPI, "-Gviewport=%s" % viewport], dest)
        im = Image.open(dest)
        print("  pixels", im.size, "mode", im.mode)
        out_files.append(dest)
        x += TILE_W_PT
        i += 1
    return out_files


def combined_max_cairo():
    """Single PNG: fill Cairo's 32767 px width, keep aspect. Record real dpi."""
    dest = OUT_DIR / "cambridge_person_100206721_maxres.png"
    # Request 300 dpi; Cairo will scale to 32767 if needed.
    run_dot(["-Tpng", "-Gdpi=300"], dest)
    im = Image.open(dest)
    w, h = im.size
    # Effective dpi along the width relative to 39852 pt (72 pt/inch)
    inches_w = GRAPH_W_PT / 72.0
    eff_dpi = w / inches_w
    print("combined cairo png", dest.name, "pixels", (w, h), "effective_dpi_x", round(eff_dpi, 1))
    # Stamp the true effective dpi into the PNG metadata
    im.save(dest, dpi=(round(eff_dpi, 1), round(eff_dpi, 1)))
    return dest, w, h, eff_dpi


def stitch(tile_paths):
    images = [Image.open(p).convert("RGB") for p in tile_paths]
    total_w = sum(im.size[0] for im in images)
    h = max(im.size[1] for im in images)
    pixels = total_w * h
    print("stitch canvas", total_w, "x", h, "mpix", round(pixels / 1e6, 1))
    dest = OUT_DIR / "cambridge_person_100206721_300dpi.png"
    try:
        canvas = Image.new("RGB", (total_w, h), (255, 255, 255))
        x = 0
        for im in images:
            canvas.paste(im, (x, 0))
            x += im.size[0]
        canvas.save(dest, dpi=(DPI, DPI), optimize=False)
        print("wrote", dest, "size_mb", round(dest.stat().st_size / 1e6, 1))
        return dest
    except MemoryError:
        print("stitch MemoryError — tiles kept, no single 300dpi PNG")
        return None


def main():
    if not DOT.exists():
        sys.stderr.write("missing %s\n" % DOT)
        return 2
    combined_max_cairo()
    tiles_list = tiles()
    stitch(tiles_list)
    return 0


if __name__ == "__main__":
    sys.exit(main())
