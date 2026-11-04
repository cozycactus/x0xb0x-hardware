#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Where do two boards' Gerbers differ? Exports both with kicad-cli, draws each layer with gerbv at 1000 dpi and locates every
differing pixel. Writes nothing into the project. Needs gerbv, numpy, scipy and Pillow.

Usage: compare_gerbers.py <old board> <new board> [--json out.json]
"""
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
GERBV = os.environ.get('GERBV', '/opt/homebrew/bin/gerbv')
SITES = {'Q112': (85.24, -114.7), 'Q121': (61.6, -121.7), 'Q122': (62.2, -104.9), 'Q126': (156.55, -144.9)}
LAYERS = 'F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts'
DPI, OX, OY, WI, HI, NEAR, POCKET = 1000, -0.05, -0.05, 9.6, 7.5, 14.0, 8.0
MM2 = (25.4 / DPI) ** 2


def board_xy(col, row, shape):
    """Pixel to board mm. gerbv pads the image beyond the window, by half the extra size on each side: 5% of the window in all."""
    pad_x, pad_y = (shape[1] - WI * DPI) / 2, (shape[0] - HI * DPI) / 2
    return ((col - pad_x) / DPI + OX) * 25.4, -(((shape[0] - pad_y - row) / DPI + OY) * 25.4)


def pour_lost(old, new):
    """Copper on the old F.Cu that the new one doesn't have, within POCKET of each chip: mostly the pocket cut into the pour."""
    rows, cols = np.ogrid[:old.shape[0], :old.shape[1]]
    pad_x, pad_y = (old.shape[1] - WI * DPI) / 2, (old.shape[0] - HI * DPI) / 2
    lost = old & ~new
    out = {}
    for name, (x, y) in SITES.items():
        col, row = (x / 25.4 - OX) * DPI + pad_x, old.shape[0] - pad_y - (-y / 25.4 - OY) * DPI
        out[name] = round(float((lost & ((rows - row) ** 2 + (cols - col) ** 2 <= (POCKET / 25.4 * DPI) ** 2)).sum()) * MM2, 2)
    return out


def draw(gerber, png):
    subprocess.run([GERBV, '-x', 'png', f'--dpi={DPI}', f'--window_inch={WI}x{HI}', f'--origin={OX}x{OY}', '-o', str(png), '--foreground=#FFFFFFFF', '--background=#000000', str(gerber)], capture_output=True, check=True)
    return np.array(Image.open(png).convert('L')) > 127


def main():
    old, new = sys.argv[1:3]
    report = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for tag, board in (('old', old), ('new', new)):
            (tmp / tag).mkdir()
            copy = tmp / tag / 'b.kicad_pcb'
            copy.write_bytes(Path(board).read_bytes())
            subprocess.run([CLI, 'pcb', 'export', 'gerbers', '--layers', LAYERS, '-o', f'{tmp / tag}/', str(copy)], capture_output=True, check=True)
        for g in sorted((tmp / 'new').glob('b-*')):
            if g.suffix == '.gbrjob':
                continue
            a, b = draw(tmp / 'old' / g.name, tmp / 'a.png'), draw(g, tmp / 'b.png')
            d = a ^ b
            lab, n = ndimage.label(d, structure=np.ones((3, 3)))
            near = away = 0.0
            biggest_away = 0
            if n:
                sizes = ndimage.sum(d, lab, range(1, n + 1))
                for size, o in zip(sizes, ndimage.find_objects(lab)):
                    x, y = board_xy((o[1].start + o[1].stop) / 2, (o[0].start + o[0].stop) / 2, d.shape)
                    if min(math.dist((x, y), s) for s in SITES.values()) < NEAR:
                        near += size * MM2
                    else:
                        away += size * MM2
                        biggest_away = max(biggest_away, int(size))
            report[g.stem[2:]] = dict(differing_mm2=round(float(d.sum()) * MM2, 3), near_chips_mm2=round(float(near), 3), away_mm2=round(float(away), 4), largest_away_region_pixels=biggest_away, pixel_um=round(25400 / DPI, 1))
            if g.stem[2:] == 'F_Cu':
                report['F_Cu']['pour_lost_within_8mm_of_chip_mm2'] = pour_lost(a, b)
            print(g.stem[2:], report[g.stem[2:]])
    if '--json' in sys.argv:
        Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
