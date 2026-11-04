#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Do the chips clear what stands around them? Exports the placed 3D models around the four chips with kicad-cli, into a temporary
folder, samples each neighbour's surfaces every 0.02 mm and measures three things. Writes fit-check.json. Needs numpy.

- body gap: from the chip, leads included, to whatever of the neighbour is no higher than the chip. 0 means they touch in the model.
- land gap: from the solder lands to whatever of the neighbour is no higher than the chip plus room for an iron tip.
- overhang: what of a neighbour stands above the chip's plan outline, and how far above the chip's top its lowest point is.

Sizes come from the illustrative models, not from the parts that will be bought. Usage: fit_check.py
"""
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'adapters' / 'ssip5-dual'))
sys.dont_write_bytecode = True
import fit_check as F  # noqa: E402

CHIPS = ('Q112', 'Q121', 'Q122', 'Q126')
SIP = {'Q112': 'Q12', 'Q121': 'Q21', 'Q122': 'Q22', 'Q126': 'Q26'}
TOP = 1.1             # SOT-363 height, mm
BODY = 1.05, 1.0      # half size along the leads, with the leads, and along the pin rows
LAND = 1.6, 0.845     # half size of the land pads
IRON = 0.3            # room above the chip for an iron tip's approach
PITCH = 0.02          # surface sample spacing, mm
REACH = 5.0           # neighbours' triangles further than this in plan are skipped


def triangles(path):
    """{reference: Nx3x3 array of triangles}, in mm: PCB x, PCB y, height above the mainboard surface."""
    b = Path(path).read_bytes()
    size = struct.unpack('<I', b[12:16])[0]
    g = json.loads(b[20:20 + size])
    data = b[20 + size + 8:]

    def values(i, kind, width):
        a = g['accessors'][i]
        v = g['bufferViews'][a['bufferView']]
        return np.frombuffer(data, dtype=kind, count=a['count'] * width, offset=v.get('byteOffset', 0) + a.get('byteOffset', 0))

    def local(n):
        if 'matrix' in n:
            return np.array(n['matrix'], float).reshape(4, 4).T
        m = np.eye(4)
        x, y, z, w = n.get('rotation', [0, 0, 0, 1])
        m[:3, :3] = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)], [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)], [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]) @ np.diag(n.get('scale', [1, 1, 1]))
        m[:3, 3] = n.get('translation', [0, 0, 0])
        return m
    out = {}

    def walk(i, parent, trail):
        n = g['nodes'][i]
        m = parent @ local(n)
        here = trail + [n.get('name', '')]
        if 'mesh' in n:
            for p in g['meshes'][n['mesh']]['primitives']:
                v = values(p['attributes']['POSITION'], '<f4', 3).reshape(-1, 3).astype(float)
                v = (m @ np.c_[v, np.ones(len(v))].T).T[:, :3] * 1e3
                v = np.c_[v[:, 0], v[:, 2], v[:, 1] - F.SURFACE]
                kind = {5121: '<u1', 5123: '<u2', 5125: '<u4'}[g['accessors'][p['indices']]['componentType']]
                t = values(p['indices'], kind, 1).reshape(-1, 3)
                ref = [s for s in here if s][0].split('/')[0]
                out.setdefault(ref, []).append(v[t])
        for c in n.get('children', []):
            walk(c, m, here)
    for r in g['scenes'][g.get('scene', 0)]['nodes']:
        walk(r, np.eye(4), [])
    return {k: np.vstack(v) for k, v in out.items()}


def surface_points(tris, x, y):
    """Points on those triangles that come within REACH of (x, y) in plan, PITCH apart."""
    keep = (tris[:, :, 0].max(1) > x - REACH) & (tris[:, :, 0].min(1) < x + REACH) & (tris[:, :, 1].max(1) > y - REACH) & (tris[:, :, 1].min(1) < y + REACH)
    pts = []
    for a, b, c in tris[keep]:
        n = max(1, int(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / PITCH) + 1)
        n = min(n, 600)
        i, j = np.mgrid[0:n + 1, 0:n + 1]
        ok = i + j <= n
        i, j = i[ok, None] / n, j[ok, None] / n
        pts.append(a + i * (b - a) + j * (c - a))
    return np.vstack(pts) if pts else np.empty((0, 3))


def gap_to_box(p, x, y, half):
    dx = np.maximum(np.abs(p[:, 0] - x) - half[0], 0)
    dy = np.maximum(np.abs(p[:, 1] - y) - half[1], 0)
    return np.hypot(dx, dy)


def main():
    fps = F.footprints()
    near = set(CHIPS)
    for s in CHIPS:
        for r, f in fps.items():
            if f['pads'] and min(math.dist(p, q) for p in fps[s]['pads'] for q in f['pads']) < 10:
                near.add(r)
    with tempfile.TemporaryDirectory() as tmp:
        glb = Path(tmp) / 'near.glb'
        subprocess.run([F.CLI, 'pcb', 'export', 'glb', '--force', '--no-board-body', '--user-origin', '0x0mm', '--component-filter', ','.join(sorted(near)), '-o', str(glb), str(F.PCB)], check=True, capture_output=True)
        models = triangles(glb)
    report = dict(note='Clearance to the placed illustrative models, nominal sizes. Not a physical fit qualification. The SIP pair at each site is left out because the chip replaces it.', chip_mm=dict(top=TOP, body_half=BODY, land_half=LAND), chips={})
    for chip in CHIPS:
        f = fps[chip]
        turned = bool(f['rot'])
        body, land = (BODY[::-1], LAND[::-1]) if turned else (BODY, LAND)
        rows, over = [], []
        for ref, tris in models.items():
            if ref in (chip, SIP[chip]):
                continue
            p = surface_points(tris, f['x'], f['y'])
            p = p[p[:, 2] > 0.05]
            if not len(p):
                continue
            low = p[p[:, 2] <= TOP]
            room = p[p[:, 2] <= TOP + IRON]
            row = dict(ref=ref)
            if len(low):
                row['body_gap_mm'] = round(float(gap_to_box(low, f['x'], f['y'], body).min()), 2)
            if len(room):
                row['land_gap_mm'] = round(float(gap_to_box(room, f['x'], f['y'], land).min()), 2)
            if len(row) > 1:
                rows.append(row)
            above = p[(p[:, 2] > TOP) & (gap_to_box(p, f['x'], f['y'], body) == 0)]
            if len(above):
                depth = np.minimum(body[0] - np.abs(above[:, 0] - f['x']), body[1] - np.abs(above[:, 1] - f['y']))
                over.append(dict(ref=ref, lowest_above_chip_top_mm=round(float(above[:, 2].min()) - TOP, 2), reach_into_outline_mm=round(float(depth.max()), 2)))
        rows.sort(key=lambda r: min(r.get('body_gap_mm', 99), r.get('land_gap_mm', 99)))
        over.sort(key=lambda r: r['lowest_above_chip_top_mm'])
        report['chips'][chip] = dict(at=[f['x'], f['y']], rotation=f['rot'], smallest_body_gap_mm=min(r.get('body_gap_mm', 99) for r in rows), smallest_land_gap_mm=min(r.get('land_gap_mm', 99) for r in rows), nearest=rows[:5], overhanging=over)
        print(chip, 'body', report['chips'][chip]['smallest_body_gap_mm'], 'land', report['chips'][chip]['smallest_land_gap_mm'], 'nearest', rows[:4], 'over', over)
    report['touching_in_the_models'] = sorted(f"{chip}-{r['ref']}" for chip, c in report['chips'].items() for r in c['nearest'] if r.get('body_gap_mm', 99) == 0)
    report['over_a_land'] = sorted(f"{chip}-{r['ref']}" for chip, c in report['chips'].items() for r in c['nearest'] if r.get('land_gap_mm', 99) == 0)
    (HERE / 'fit-check.json').write_text(json.dumps(report, indent=1) + '\n')
    print('touching:', report['touching_in_the_models'], 'over a land:', report['over_a_land'])


if __name__ == '__main__':
    main()
