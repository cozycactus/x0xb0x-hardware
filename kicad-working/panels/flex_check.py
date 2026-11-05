#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Estimate how far the main panel and the mainboard bend when a button, a knob or the panel itself is pressed.

Both are thin plates (Kirchhoff), meshed with 1 mm rectangular ACM elements. The panel has its holes and cuts
from the exported Gerber and drill files; the mainboard is a plain plate, which makes it a little too stiff.
The original assembly page puts the short standoffs in the four corners, through the case flanges, so the
corners are held. The three other standoffs tie board and panel together. The board hangs on these seven only.

Two ways the case can hold the panel, because the drawing doesn't settle it:
  corners: only the four corner screws hold the panel.
  ledge:   the panel edge also rests on the case ledge; it can't move into the case there but can lift.

Needs numpy and scipy (the ../../../x0xb0x-si-emc venv has them). Writes flex-check.json.
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

HERE = Path(__file__).resolve().parent
ORIGIN = (20.0, 190.0)
H = 1.0  # element size, mm

FR4 = dict(E=20000.0, nu=0.15)  # MPa; FR-4 laminates are about 18-24 GPa in bending
ALU = dict(E=69000.0, nu=0.33)
PANELS = {'FR-4 1.6 mm': (FR4, 1.6), 'FR-4 1.44 mm (thinnest)': (FR4, 1.44), 'FR-4 2.0 mm': (FR4, 2.0), 'aluminium 1.575 mm': (ALU, 1.575)}
BOARD = (FR4, 1.6)
BOARD_BOX = (-2.54, -12.7, 234.95, 167.64)  # mainboard outline in the panel frame, from mainboard.kicad_pcb
CORNERS = [(6.9088, 8.5852), (225.5012, 8.5852), (6.9088, 154.686), (225.5012, 154.686)]
MIDDLE = [(116.205, 8.5852), (70.485, 154.931), (161.925, 154.931)]
SWITCH_FORCE = 1.57  # N, TL1100F160Q: 160 gf
FIRM = 10.0  # N, a firm press, assumed


def acm(a, b, E, nu, t):
    """Stiffness of a rectangular ACM plate element a x b; dofs per node: w, dw/dx, dw/dy; nodes counter-clockwise."""
    D = E * t ** 3 / (12 * (1 - nu ** 2)) * np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])
    nodes = [(0, 0), (a, 0), (a, b), (0, b)]

    def P(x, y):
        return np.array([1, x, y, x * x, x * y, y * y, x ** 3, x * x * y, x * y * y, y ** 3, x ** 3 * y, x * y ** 3])

    def Px(x, y):
        return np.array([0, 1, 0, 2 * x, y, 0, 3 * x * x, 2 * x * y, y * y, 0, 3 * x * x * y, y ** 3])

    def Py(x, y):
        return np.array([0, 0, 1, 0, x, 2 * y, 0, x * x, 2 * x * y, 3 * y * y, x ** 3, 3 * x * y * y])

    def B(x, y):
        return np.array([[0, 0, 0, 2, 0, 0, 6 * x, 2 * y, 0, 0, 6 * x * y, 0],
                         [0, 0, 0, 0, 0, 2, 0, 0, 2 * x, 6 * y, 0, 6 * x * y],
                         [0, 0, 0, 0, 2, 0, 0, 4 * x, 4 * y, 0, 6 * x * x, 6 * y * y]], float)

    C = np.array([row for x, y in nodes for row in (P(x, y), Px(x, y), Py(x, y))], float)
    g, w = np.polynomial.legendre.leggauss(3)
    k = np.zeros((12, 12))
    for gi, wi in zip(g, w):
        for gj, wj in zip(g, w):
            x, y = a * (gi + 1) / 2, b * (gj + 1) / 2
            Bm = B(x, y)
            k += wi * wj * Bm.T @ D @ Bm * a * b / 4
    Ci = np.linalg.inv(C)
    return Ci.T @ k @ Ci


class Plate:
    def __init__(self, box, mat, t, solid, offset=0):
        x0, y0, x1, y1 = box
        self.nx, self.ny = round((x1 - x0) / H), round((y1 - y0) / H)
        self.a, self.b = (x1 - x0) / self.nx, (y1 - y0) / self.ny
        self.x0, self.y0 = x0, y0
        cx = x0 + (np.arange(self.nx) + 0.5) * self.a
        cy = y0 + (np.arange(self.ny) + 0.5) * self.b
        X, Y = np.meshgrid(cx, cy, indexing='ij')
        self.active = solid(X, Y)
        used = np.zeros((self.nx + 1, self.ny + 1), bool)
        for di in (0, 1):
            for dj in (0, 1):
                used[di:self.nx + di, dj:self.ny + dj] |= self.active
        self.index = -np.ones(used.shape, int)
        self.index[used] = np.arange(used.sum()) + offset // 3
        self.ndof = 3 * int(used.sum())
        self.offset = offset
        self.ke = acm(self.a, self.b, mat['E'], mat['nu'], t)

    def triplets(self):
        ii, jj = np.nonzero(self.active)
        corner = [(0, 0), (1, 0), (1, 1), (0, 1)]
        nodes = np.stack([self.index[ii + di, jj + dj] for di, dj in corner], 1)
        dofs = (3 * nodes[:, :, None] + np.arange(3)).reshape(len(ii), 12)
        rows = np.repeat(dofs, 12, 1).ravel()
        cols = np.tile(dofs, (1, 12)).ravel()
        vals = np.tile(self.ke.ravel(), len(ii))
        return rows, cols, vals

    def node(self, x, y):
        """Nearest node that belongs to the plate."""
        i, j = round((x - self.x0) / self.a), round((y - self.y0) / self.b)
        best = None
        for di in range(-3, 4):
            for dj in range(-3, 4):
                p, q = i + di, j + dj
                if 0 <= p <= self.nx and 0 <= q <= self.ny and self.index[p, q] >= 0:
                    d = math.hypot(self.x0 + p * self.a - x, self.y0 + q * self.b - y)
                    if best is None or d < best[0]:
                        best = (d, self.index[p, q])
        assert best is not None, (x, y)
        return best[1]

    def edge_nodes(self, band=1.0):
        out = []
        for p in range(self.nx + 1):
            for q in range(self.ny + 1):
                if self.index[p, q] < 0:
                    continue
                x, y = p * self.a, q * self.b
                if min(x, y, self.nx * self.a - x, self.ny * self.b - y) <= band + 1e-9:
                    out.append(self.index[p, q])
        return out


def read_gerber_holes():
    """Holes and cuts of the main panel, from its exported files, in the panel frame."""
    g = HERE / 'fabrication/mainpanel/gerbers'
    ox, oy = ORIGIN
    holes, boxes = [], []
    tool = None
    tools = {}
    for line in (g / 'mainpanel-NPTH.drl').read_text().splitlines():
        m = re.fullmatch(r'T(\d+)C([\d.]+)', line.strip())
        if m:
            tools[m[1]] = float(m[2])
        m = re.fullmatch(r'T(\d+)', line.strip())
        if m:
            tool = tools.get(m[1])
        m = re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)', line.strip())
        if m and tool:
            holes.append((float(m[1]) - ox, float(m[2]) + oy, tool / 2))
    pos = None
    for line in (g / 'mainpanel-Edge_Cuts.gbr').read_text().splitlines():
        m = re.search(r'X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D0([12])\*', line)
        if not m:
            continue
        p = (int(m[1]) / 1e6 - ox, int(m[2]) / 1e6 + oy)
        if m[5] == '1' and m[3] is not None:
            c = (pos[0] + int(m[3]) / 1e6, pos[1] + int(m[4]) / 1e6)
            r = math.dist(pos, c)
            if r > 1:
                holes.append((*c, r))
        pos = p
    # Cuts from the DXF record, grown 0.1 mm a side as make_panels.py does; their 0.5 mm corner radii are left out
    geometry = json.loads((HERE.parent / 'visualization/blender-case-revision-7/panels/original-panels.json').read_text())
    for r in geometry['mainpanel']['rectangular_cutouts']:
        (x0, y0), (x1, y1) = r['bounds_mm']
        boxes.append((x0 - 0.1, y0 - 0.1, x1 + 0.1, y1 + 0.1))
    return sorted(set((round(x, 3), round(y, 3), round(r, 3)) for x, y, r in holes)), boxes


def panel_solid(holes, boxes):
    def solid(X, Y):
        keep = np.ones(X.shape, bool)
        for x, y, r in holes:
            keep &= (X - x) ** 2 + (Y - y) ** 2 > r * r
        for x0, y0, x1, y1 in boxes:
            keep &= ~((X > x0) & (X < x1) & (Y > y0) & (Y < y1))
        return keep
    return solid


def solve(K, fixed, loads, ledge=(), kpen=1e9):
    """Static solve with penalty supports. Ledge dofs resist only motion into the case (w > 0)."""
    n = K.shape[0]
    contact = set(ledge)
    for _ in range(30):
        pen = np.zeros(n)
        pen[list(fixed)] = kpen
        pen[list(contact)] = kpen
        lu = spla.splu((K + sp.diags(pen)).tocsc())
        u = lu.solve(loads)
        lifted = {d for d in contact if (u[d] if u.ndim == 1 else u[d].max()) < -1e-9}
        if not lifted:
            return u
        contact -= lifted
    raise RuntimeError('contact did not settle')


def unit_test():
    """Simply supported square plate, centre point load: w = 0.01160 P a^2 / D for nu = 0.3 (Timoshenko)."""
    global H
    saved, H = H, 2.0
    mat = dict(E=1000.0, nu=0.3)
    p = Plate((0, 0, 100, 100), mat, 1.0, lambda X, Y: np.ones(X.shape, bool))
    r, c, v = p.triplets()
    K = sp.coo_matrix((v, (r, c)), shape=(p.ndof, p.ndof)).tocsr()
    f = np.zeros(p.ndof)
    f[3 * p.node(50, 50)] = 1.0
    u = solve(K, {3 * n for n in p.edge_nodes(0.0)}, f)
    D = 1000 / (12 * (1 - 0.09))
    H = saved
    return u[3 * p.node(50, 50)], 0.01160 * 100 ** 2 / D


def model(panel_mat, panel_t, holes, boxes, ledge):
    panel = Plate((0, 0, 232.41, 163.2712), panel_mat, panel_t, panel_solid(holes, boxes))
    board = Plate(BOARD_BOX, *BOARD, lambda X, Y: np.ones(X.shape, bool), offset=panel.ndof)
    rows, cols, vals = [], [], []
    for p in (panel, board):
        r, c, v = p.triplets()
        rows.append(r); cols.append(c); vals.append(v)
    n = panel.ndof + board.ndof
    K = sp.coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
    # Standoffs: the board's w equals the panel's at the three middle mounts; corners are held by the case
    links = []
    for x, y in MIDDLE:
        a, b = 3 * panel.node(x, y), 3 * board.node(x, y)
        links.append((a, b))
    k = 1e9
    L = sp.lil_matrix((n, n))
    for a, b in links:
        L[a, a] += k; L[b, b] += k; L[a, b] -= k; L[b, a] -= k
    K = (K + L.tocsr()).tocsr()
    fixed = {3 * panel.node(x, y) for x, y in CORNERS} | {3 * board.node(x, y) for x, y in CORNERS}
    ledge_dofs = [3 * m for m in panel.edge_nodes(1.0)] if ledge else []
    return panel, board, K, fixed, ledge_dofs


def controls():
    geometry = json.loads((HERE.parent / 'visualization/blender-case-revision-7/panels/original-panels.json').read_text())['mainpanel']
    out = {}
    for r in geometry['rectangular_cutouts']:
        (x0, y0), (x1, y1) = r['bounds_mm']
        out[r['board_reference']] = ((x0 + x1) / 2, (y0 + y1) / 2)
    for c in geometry['circles']:
        if c['function'] != 'mount' and not c['board_reference'].startswith('LED'):
            out[c['board_reference']] = tuple(c['center_mm'])
    return out


def main():
    measured, exact = unit_test()
    print(f'unit test: {measured:.4f} against {exact:.4f}, {100 * (measured / exact - 1):+.2f} %')
    holes, boxes = read_gerber_holes()
    places = controls()
    probes = [(x, y) for x in np.arange(15, 230, 10.0) for y in np.arange(15, 160, 10.0)]
    record = dict(method=__doc__.strip().splitlines()[0], element_mm=H, unit_test=dict(model=measured, timoshenko=exact),
                  materials=dict(FR4=FR4, aluminium=ALU), switch_force_N=SWITCH_FORCE, firm_press_N=FIRM, results=[])
    for ledge in (False, True):
        for name, (mat, t) in PANELS.items():
            panel, board, K, fixed, ledge_dofs = model(mat, t, holes, boxes, ledge)
            n = K.shape[0]
            # Presses on the board: buttons and knobs, one at a time, firm force
            refs = sorted(places)
            F = np.zeros((n, len(refs)))
            for k_, ref in enumerate(refs):
                F[3 * board.node(*places[ref]), k_] = FIRM
            U = solve(K, fixed, F, ledge_dofs)
            press = {ref: dict(board_mm=float(U[3 * board.node(*places[ref]), k_]), panel_mm=float(U[3 * panel.node(*places[ref]), k_]))
                     for k_, ref in enumerate(refs)}
            worst = max(press, key=lambda r: press[r]['board_mm'])
            buttons = [r for r in refs if r.startswith('S') and int(r[1:]) >= 5]
            worst_button = max(buttons, key=lambda r: press[r]['board_mm'])
            # Presses on the panel itself, between holes
            pts = [(x, y) for x, y in probes if panel.index[round(x / panel.a), round(y / panel.b)] >= 0
                   and all(math.hypot(x - hx, y - hy) > hr + 2 for hx, hy, hr in holes)
                   and all(not (x0 - 2 < x < x1 + 2 and y0 - 2 < y < y1 + 2) for x0, y0, x1, y1 in boxes)]
            F = np.zeros((n, len(pts)))
            for k_, p in enumerate(pts):
                F[3 * panel.node(*p), k_] = FIRM
            U = solve(K, fixed, F, ledge_dofs)
            sag = [float(U[3 * panel.node(*p), k_]) for k_, p in enumerate(pts)]
            k_max = int(np.argmax(sag))
            row = dict(support='corners and ledge' if ledge else 'corners only', panel=name,
                       worst_button=worst_button, worst_button_board_mm=round(press[worst_button]['board_mm'], 4),
                       worst_button_panel_mm=round(press[worst_button]['panel_mm'], 4),
                       worst_control=worst, worst_control_board_mm=round(press[worst]['board_mm'], 4),
                       panel_press_worst_mm=round(sag[k_max], 4), panel_press_at=pts[k_max],
                       per_control_board_mm={r: round(v['board_mm'], 4) for r, v in press.items()},
                       per_control_panel_mm={r: round(v['panel_mm'], 4) for r, v in press.items()})
            record['results'].append(row)
            print(f"{row['support']:18} {name:24} button {worst_button} {row['worst_button_board_mm']:.3f} mm (panel {row['worst_button_panel_mm']:.3f}), "
                  f"control {worst} {row['worst_control_board_mm']:.3f}, panel press {row['panel_press_worst_mm']:.3f} mm at {pts[k_max]}", flush=True)
    (HERE / 'flex-check.json').write_text(json.dumps(record, indent=1) + '\n')


if __name__ == '__main__':
    sys.exit(main())
