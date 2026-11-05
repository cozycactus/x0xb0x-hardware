#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Cross-check flex_check.py with other software: Gmsh meshes the real outlines, CalculiX solves with shells.

Uses the Gmsh and CalculiX that come with FreeCAD. The panel's holes and cuts follow the exported files, with
their 0.5 mm corner radii; elements are 8-node shells (S8R, 6-node S6 where Gmsh can't make quads). The cases
are those of flex_check.py with the largest results, plus the panel's middle. On the ledge, the edge is held
both ways here, where flex_check.py lets it lift. Needs flex-check.json first. Writes flex-ccx.json.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flex_check as fc  # noqa: E402

HERE = Path(__file__).resolve().parent
BIN = Path(os.environ.get('FREECAD_BIN', '/Applications/FreeCAD.app/Contents/Resources/bin'))
SIZE = 2.0
Z_BOARD = -13.48


def geo(path, outline, holes, boxes, points):
    x0, y0, x1, y1 = outline
    L = ['SetFactory("OpenCASCADE");', f'Rectangle(1) = {{{x0}, {y0}, 0, {x1 - x0}, {y1 - y0}}};']
    tools = []
    for k, (x, y, r) in enumerate(holes, 10):
        L.append(f'Disk({k}) = {{{x}, {y}, 0, {r}}};')
        tools.append(k)
    for k, (a, b, c, d) in enumerate(boxes, 10 + len(holes)):
        L.append(f'Rectangle({k}) = {{{a}, {b}, 0, {c - a}, {d - b}, 0.5}};')
        tools.append(k)
    if tools:
        L.append(f'BooleanDifference(1000) = {{ Surface{{1}}; Delete; }}{{ Surface{{{",".join(map(str, tools))}}}; Delete; }};')
        surf = 1000
    else:
        surf = 1
    for k, (x, y) in enumerate(points, 5000):
        L.append(f'Point({k}) = {{{x}, {y}, 0, {2 * SIZE}}};')
    L.append(f'Point{{{",".join(str(5000 + k) for k in range(len(points)))}}} In Surface{{{surf}}};')
    # All-quad mesh: Gmsh splits each element in four, so the base size is twice the final one
    L += [f'Mesh.CharacteristicLengthMax = {2 * SIZE};', 'Mesh.RecombineAll = 1;', 'Mesh.Algorithm = 8;', 'Mesh.SubdivisionAlgorithm = 1;',
          'Mesh.ElementOrder = 2;', 'Mesh.SecondOrderIncomplete = 1;', 'Mesh.MshFileVersion = 2.2;']
    path.write_text('\n'.join(L) + '\n')


def read_msh(path):
    lines = path.read_text().splitlines()
    i = lines.index('$Nodes')
    n = int(lines[i + 1])
    nodes = {}
    for line in lines[i + 2:i + 2 + n]:
        k, x, y, z = line.split()
        nodes[int(k)] = (float(x), float(y))
    j = lines.index('$Elements')
    quads, tris = [], []
    for line in lines[j + 2:j + 2 + int(lines[j + 1])]:
        v = list(map(int, line.split()))
        typ, ntags = v[1], v[2]
        conn = v[3 + ntags:]
        if typ == 16:
            quads.append(conn)
        elif typ == 9:
            tris.append(conn)
    return nodes, quads, tris


def nearest(nodes, x, y, used):
    return min((k for k in nodes if k in used), key=lambda k: (nodes[k][0] - x) ** 2 + (nodes[k][1] - y) ** 2)


def mesh(work, name, outline, holes, boxes, points):
    g = work / f'{name}.geo'
    geo(g, outline, holes, boxes, points)
    subprocess.run([str(BIN / 'gmsh'), str(g), '-2', '-o', str(work / f'{name}.msh')], check=True, capture_output=True)
    return read_msh(work / f'{name}.msh')


def run_case(work, label, panel_mat, panel_t, ledge, loads, P, B, probes):
    (pn, pq, pt), (bn, bq, bt) = P, B
    off = max(pn) + 1
    used_p = {k for e in pq + pt for k in e}
    used_b = {k for e in bq + bt for k in e}
    L = ['*HEADING', label, '*NODE, NSET=NALL']
    L += [f'{k}, {x}, {y}, 0' for k, (x, y) in pn.items() if k in used_p]
    L += [f'{k + off}, {x}, {y}, {Z_BOARD}' for k, (x, y) in bn.items() if k in used_b]
    eid = 1
    sets = {}
    for name, quads, tris, o in (('P', pq, pt, 0), ('B', bq, bt, off)):
        for typ, els in (('S8R', quads), ('S6', tris)):
            if not els:
                continue
            L.append(f'*ELEMENT, TYPE={typ}, ELSET={name}{typ}')
            for e in els:
                L.append(f'{eid}, ' + ', '.join(str(k + o) for k in e))
                eid += 1
            sets.setdefault(name, []).append(f'{name}{typ}')
    for name, mat, t in (('P', panel_mat, panel_t), ('B', fc.BOARD[0], fc.BOARD[1])):
        L += [f'*ELSET, ELSET={name}ALL', ', '.join(sets[name]), f'*MATERIAL, NAME=M{name}', '*ELASTIC', f'{mat["E"]}, {mat["nu"]}',
              f'*SHELL SECTION, ELSET={name}ALL, MATERIAL=M{name}', f'{t}']
    fixed = [nearest(pn, x, y, used_p) for x, y in fc.CORNERS] + [nearest(bn, x, y, used_b) + off for x, y in fc.CORNERS]
    L += ['*NSET, NSET=FIX', ', '.join(map(str, fixed)), '*BOUNDARY', 'FIX, 1, 3']
    if ledge:
        x1, y1 = 232.41, 163.2712
        edge = [k for k, (x, y) in pn.items() if k in used_p and min(x, y, x1 - x, y1 - y) < 1e-6]
        L += ['*NSET, NSET=LEDGE'] + [', '.join(map(str, edge[i:i + 12])) for i in range(0, len(edge), 12)] + ['*BOUNDARY', 'LEDGE, 3, 3']
    L.append('*EQUATION')
    for x, y in fc.MIDDLE:
        a, b = nearest(pn, x, y, used_p), nearest(bn, x, y, used_b) + off
        L += ['2', f'{a}, 3, 1.0, {b}, 3, -1.0']
    probe_nodes = {}
    for key, (plate, x, y) in probes.items():
        probe_nodes[key] = nearest(pn, x, y, used_p) if plate == 'panel' else nearest(bn, x, y, used_b) + off
    L += ['*NSET, NSET=PROBES', ', '.join(map(str, sorted(set(probe_nodes.values()))))]
    for k, (plate, x, y) in enumerate(loads):
        node = probe_nodes[(plate, x, y)]
        L += ['*STEP', '*STATIC', '*CLOAD, OP=NEW', f'{node}, 3, {fc.FIRM}', '*NODE PRINT, NSET=PROBES', 'U', '*END STEP']
    job = work / label.replace(' ', '_').replace('.', '_')
    (job.with_suffix('.inp')).write_text('\n'.join(L) + '\n')
    r = subprocess.run([str(BIN / 'ccx'), '-i', job.name], cwd=work, capture_output=True, text=True)
    out = (job.with_suffix('.dat')).read_text() if job.with_suffix('.dat').exists() else ''
    assert 'displacements' in out, r.stdout[-2000:] + r.stderr[-2000:]
    blocks = out.split('displacements')[1:]
    results = []
    for k, (plate, x, y) in enumerate(loads):
        vals = {int(m[1]): float(m[2]) for m in re.finditer(r'^\s*(\d+)\s+\S+\s+\S+\s+(\S+)\s*$', blocks[k], re.M)}
        results.append(vals[probe_nodes[(plate, x, y)]])
    return results


def main():
    record = json.loads((HERE / 'flex-check.json').read_text())
    holes, boxes = fc.read_gerber_holes()
    places = fc.controls()
    cases = []
    for row in record['results']:
        if row['panel'] not in ('FR-4 1.6 mm', 'aluminium 1.575 mm'):
            continue
        loads = [('board', *places[row['worst_button']]), ('board', *places[row['worst_control']]), ('panel', *row['panel_press_at'])]
        expect = [row['worst_button_board_mm'], row['worst_control_board_mm'], row['panel_press_worst_mm']]
        cases.append((row, loads, expect))
    panel_points = list({(x, y) for _, loads, _ in cases for p, x, y in loads if p == 'panel'}) + fc.CORNERS + fc.MIDDLE
    board_points = list({(x, y) for _, loads, _ in cases for p, x, y in loads if p == 'board'}) + fc.CORNERS + fc.MIDDLE
    out = dict(method=__doc__.strip().splitlines()[0], element_mm=SIZE, firm_press_N=fc.FIRM, cases=[])
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        P = mesh(work, 'panel', (0, 0, 232.41, 163.2712), holes, boxes, panel_points)
        B = mesh(work, 'board', fc.BOARD_BOX, [], [], board_points)
        out['elements'] = dict(panel_quads=len(P[1]), panel_triangles=len(P[2]), board_quads=len(B[1]), board_triangles=len(B[2]))
        print(out['elements'], flush=True)
        for row, loads, expect in cases:
            mat, t = fc.PANELS[row['panel']]
            probes = {(p, x, y): (p, x, y) for p, x, y in loads}
            got = run_case(work, f"{row['support']} {row['panel']}", mat, t, row['support'] != 'corners only', loads, P, B, probes)
            names = [f"button {row['worst_button']}", f"control {row['worst_control']}", f"panel at {row['panel_press_at']}"]
            for n_, g, e in zip(names, got, expect):
                out['cases'].append(dict(support=row['support'], panel=row['panel'], press=n_, calculix_mm=round(abs(g), 4),
                                         flex_check_mm=e, difference_percent=round(100 * (abs(g) / e - 1), 1)))
                print(f"{row['support']:18} {row['panel']:20} {n_:26} CalculiX {abs(g):.3f}  own model {e:.3f}  {100 * (abs(g) / e - 1):+.1f} %", flush=True)
    (HERE / 'flex-ccx.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
