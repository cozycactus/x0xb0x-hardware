#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Does the adapter fit at Q12, Q21, Q22 and Q26? Exports the revision's placed 3D models around the four sites with
kicad-cli into a temporary folder (the board is not changed), takes each neighbour's bounding box above the board
surface, and measures the gap to the adapter's boxes. Writes fit-check.json. Needs numpy.

Neighbour boxes are conservative for shape but nominal for size: they come from the illustrative models, not from the
parts that will be bought. A film capacitor of another make can be thicker. Usage: fit_check.py"""
import json
import math
import os
import re
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PCB = HERE.parents[1] / 'mainboard' / 'mainboard.kicad_pcb'
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
SITES = ('Q12', 'Q21', 'Q22', 'Q26')
BOARD_T = 1.6     # adapter thickness
STANDOFF = 2.0    # bottom edge of the adapter above the mainboard surface
HEIGHT = 7.8      # adapter height
WIDTH = 11.4      # adapter length along the pin row
WIRE = 0.6        # wire diameter
CHIP_V = 5.6      # chip centre above the adapter's bottom edge
ROW = 2.286
SURFACE = 1.6     # exported models have y = 0 at the mainboard's bottom face


def blocks(text, head):
    out, i = [], 0
    while (j := text.find('(' + head, i)) >= 0:
        d, k, q = 0, j, False
        while True:
            c = text[k]
            if c == '"' and text[k - 1] != '\\':
                q = not q
            elif not q:
                d += c == '('
                d -= c == ')'
                if d == 0:
                    break
            k += 1
        out.append(text[j:k + 1])
        i = k + 1
    return out


def footprints():
    out = {}
    for f in blocks(PCB.read_text(), 'footprint '):
        ref = re.search(r'\(property "Reference" "([^"]+)"', f)[1]
        at = re.search(r'\n\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', f)
        x, y, r = float(at[1]), float(at[2]), float(at[3] or 0)
        t = math.radians(-r)
        pads = []
        for p in blocks(f, 'pad '):
            a = re.search(r'\(at ([-\d.]+) ([-\d.]+)', p)
            px, py = float(a[1]), float(a[2])
            pads.append((x + px * math.cos(t) - py * math.sin(t), y + px * math.sin(t) + py * math.cos(t)))
        out[ref] = dict(x=x, y=y, rot=r, pads=pads)
    return out


def read_glb(path):
    """{reference: Nx3 array of model vertices}, in mm: PCB x, PCB y, height above the mainboard surface."""
    b = Path(path).read_bytes()
    jl = struct.unpack('<I', b[12:16])[0]
    g = json.loads(b[20:20 + jl])
    data = b[20 + jl + 8:]

    def pos(i):
        a = g['accessors'][i]
        v = g['bufferViews'][a['bufferView']]
        off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
        return np.frombuffer(data, dtype='<f4', count=a['count'] * 3, offset=off).reshape(-1, 3).astype(float)

    def local(n):
        if 'matrix' in n:
            return np.array(n['matrix'], float).reshape(4, 4).T
        m = np.eye(4)
        x, y, z, w = n.get('rotation', [0, 0, 0, 1])
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        m[:3, :3] = R @ np.diag(n.get('scale', [1, 1, 1]))
        m[:3, 3] = n.get('translation', [0, 0, 0])
        return m
    out = {}

    def walk(i, parent, trail):
        n = g['nodes'][i]
        m = parent @ local(n)
        here = trail + [n.get('name', '')]
        if 'mesh' in n:
            for p in g['meshes'][n['mesh']]['primitives']:
                v = pos(p['attributes']['POSITION'])
                v = (m @ np.c_[v, np.ones(len(v))].T).T[:, :3] * 1e3
                ref = [t for t in here if t][0].split('/')[0] if here else ''
                out.setdefault(ref, []).append(np.c_[v[:, 0], v[:, 2], v[:, 1] - SURFACE])
        for c in n.get('children', []):
            walk(c, m, here)
    for r in g['scenes'][g.get('scene', 0)]['nodes']:
        walk(r, np.eye(4), [])
    return {k: np.vstack(v) for k, v in out.items()}


def gap(a, b):
    """Distance between two axis-aligned boxes ((umin, umax), (wmin, wmax), (zmin, zmax)); 0 when they touch or overlap."""
    return math.sqrt(sum(max(0.0, x[0] - y[1], y[0] - x[1]) ** 2 for x, y in zip(a, b)))


def adapter_boxes(d):
    """d = +1 or -1: which way across the pin row the board body sits. The wires stay on the row's centre line, and the
    chip is on the same face as the wires, so it points the other way."""
    w_face = WIRE / 2
    span = lambda lo, hi: (min(d * lo, d * hi), max(d * lo, d * hi))
    boxes = dict(board=((-WIDTH / 2, WIDTH / 2), span(w_face, w_face + BOARD_T), (STANDOFF, STANDOFF + HEIGHT)),
                 chip=((-2.05, 2.05), span(w_face - 1.0, w_face), (STANDOFF + CHIP_V - 1.3, STANDOFF + CHIP_V + 1.3)))
    for i in range(5):
        u = (i - 2) * ROW
        boxes[f'wire{i + 1}'] = ((u - WIRE / 2, u + WIRE / 2), (-WIRE / 2, WIRE / 2), (0.0, STANDOFF + 3.6))
    return boxes


def main():
    fps = footprints()
    near = set(SITES)
    for s in SITES:
        for r, f in fps.items():
            if f['pads'] and min(math.dist(p, q) for p in fps[s]['pads'] for q in f['pads']) < 16:
                near.add(r)
    with tempfile.TemporaryDirectory() as tmp:
        glb = Path(tmp) / 'near.glb'
        subprocess.run([CLI, 'pcb', 'export', 'glb', '--force', '--no-board-body', '--user-origin', '0x0mm', '--component-filter', ','.join(sorted(near)), '-o', str(glb), str(PCB)], check=True, capture_output=True)
        models = read_glb(glb)
    report = dict(assumptions=dict(adapter_mm=[WIDTH, HEIGHT, BOARD_T], standoff_mm=STANDOFF, wire_mm=WIRE, note='Neighbour boxes from the placed illustrative models; sizes are nominal. Not a physical fit qualification.'), sites={})
    for site in SITES:
        row = fps[site]['pads']
        ux, uy = (row[0][0] - row[4][0]) / (4 * ROW), (row[0][1] - row[4][1]) / (4 * ROW)  # unit vector, pin 5 toward pin 1
        cx, cy = fps[site]['x'], fps[site]['y']
        boxes = {}
        for ref, v in models.items():
            if ref == site:
                continue
            v = v[v[:, 2] > 0.05]
            if not len(v):
                continue
            du, dv = v[:, 0] - cx, v[:, 1] - cy
            u = du * ux + dv * uy
            w = -du * uy + dv * ux
            boxes[ref] = ((float(u.min()), float(u.max())), (float(w.min()), float(w.max())), (float(v[:, 2].min()), float(v[:, 2].max())))
        result = dict(row_axis_toward_pin1=[round(ux, 4), round(uy, 4)], options={})
        for d in (1, -1):
            pieces = adapter_boxes(d)
            rows = []
            for ref, box in boxes.items():
                g_, piece = min((gap(p, box), name) for name, p in pieces.items())
                rows.append(dict(ref=ref, gap_mm=round(g_, 2), to=piece, top_mm=round(box[2][1], 2)))
            rows.sort(key=lambda r: r['gap_mm'])
            result['options'][f'{d:+d}'] = dict(smallest_gap_mm=rows[0]['gap_mm'], nearest=rows[:4])
        best = max(result['options'], key=lambda k: result['options'][k]['smallest_gap_mm'])
        toward = result['options'][best]['nearest']
        # Name the part the board body leans toward, so the direction can be read on the mainboard
        d = int(best)
        lean = [r for r, b in boxes.items() if (b[1][0] if d > 0 else -b[1][1]) > 0 and b[0][0] < WIDTH / 2 and b[0][1] > -WIDTH / 2]
        lean.sort(key=lambda r: boxes[r][1][0] if d > 0 else -boxes[r][1][1])
        result.update(best_direction=best, board_body_leans_toward=lean[:2], smallest_gap_mm=result['options'][best]['smallest_gap_mm'], tallest_neighbour_mm=round(max(b[2][1] for r, b in boxes.items() if gap(((-8, 8), (-6, 6), (0, 30)), b) == 0), 2), adapter_top_mm=STANDOFF + HEIGHT)
        report['sites'][site] = result
        print(f"{site}: best {best}, leans toward {lean[:2]}; smallest gap {result['smallest_gap_mm']} mm, to {toward[0]['ref']} ({toward[0]['to']}); other way {result['options'][str('+1' if d < 0 else '-1')]['smallest_gap_mm']} mm; adapter top {STANDOFF + HEIGHT} mm, tallest neighbour {result['tallest_neighbour_mm']} mm")
    report['passed'] = all(s['smallest_gap_mm'] >= 0.3 for s in report['sites'].values())
    (HERE / 'fit-check.json').write_text(json.dumps(report, indent=1) + '\n')
    print('passed (every site has at least 0.3 mm):', report['passed'])


if __name__ == '__main__':
    main()
