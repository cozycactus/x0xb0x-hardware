#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Run DRC on both panels, export their fabrication files, read the exports back and write verification.json.

Geometry is checked from the exported Gerber and drill files, not from the generator. The boards are only read.
Previews need Pillow, so run it with the Python of ../../../x0xb0x-si-emc/.venv, or any other that has Pillow:
  python -I make_package.py
"""
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
SOURCE = WORK / 'visualization/blender-case-revision-7'
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
LAYERS = 'F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts'
ORIGIN = dict(mainpanel=(20.0, 190.0), iopanel=(20.0, 90.0))
GEOMETRY = json.loads((SOURCE / 'panels/original-panels.json').read_text())
LABELS = json.loads((SOURCE / 'source-review/original-photo-label-map.json').read_text())['labels']
ALIGNMENT = json.loads((SOURCE / 'panels/board-panel-alignment.json').read_text())

# JLCPCB's published limits, read 2026-11-05
ROUTED = 0.2  # non-plated slots and routed holes, either way
DRILLED_PLUS, DRILLED_MINUS = 0.13, 0.08  # through-holes; the page lists no separate figure for plain drilled holes
MIN_SILK_LINE, MIN_SILK_HEIGHT = 0.15, 1.0
SILK_TO_EDGE = 0.3  # our own limit, to survive the routing tolerance

# What passes through each hole: (references, part, part diameter at its largest, axis offset from the hole, source)
ROUND_FITS = [
    ([f'LED{n}' for n in range(1, 41)], 'WP7113ID lens', 5.25, 0.0, 'Kingbright drawing: 5 mm, +/-0.25'),
    (['S1'], 'B12AB bushing', 6.2, 0.0, 'NKK 6 mm in the model record; RS lists a 6.2 mm cutout'),
    (['S2'], '290VAA5F201B2 bushing', 7.0, 0.0, 'CTS drawing, model record'),
    (['S3', 'S4'], '25LB22-H bushing', 9.525, 0.0, 'Grayhill drawing: 3/8-32'),
    (['VR2', 'VR3', 'VR5', 'VR7', 'VR8', 'VR4', 'VR6'], 'pot sleeve', 9.0, 0.0, 'model record, largest sleeve of the pots'),
    (['U$2', 'U$27', 'U$28', 'U$24', 'U$23', 'U$25', 'U$29'], '4-40 screw', 2.845, 0.2455, 'ASME thread size; offset from the board alignment record'),
    (['HEADPHONE0', 'MIXIN0', 'MIXOUT0'], 'NYS216 nose', 11.0, 0.082, 'REAN drawing: M11; offset from the rear datum record'),
    (['CV0', 'GATE0'], 'MJ-3536N bushing', 6.0, 0.166, 'CUI drawing, model record; offset from the rear datum record'),
    (['DIN1', 'DIN2', 'DIN3', 'DIN4'], 'SDS-50J shell', 14.2, 0.018, 'CUI drawing, rear seating record'),
]
# Rectangular cuts: (references, part, width, height, clearance in the DXF left, bottom, offset, source)
CAP = (12.1, 5.9)
checks = []
fits = []


def check(name, ok, **info):
    checks.append(dict(name=name, passed=bool(ok), **info))
    print('ok  ' if ok else 'FAIL', name, info if info else '')


def run(*args):
    return subprocess.run([CLI, *map(str, args)], cwd=HERE, check=True, capture_output=True, text=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_gerber(path, name):
    """Return round-aperture segments and arcs in panel coordinates, y up."""
    ox, oy = ORIGIN[name]
    apertures, width, mode, pos = {}, None, 'G01', (0.0, 0.0)
    segments, arcs = [], []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        m = re.match(r'%ADD(\d+)C,([\d.]+)', line)
        if m:
            apertures[int(m[1])] = float(m[2])
            continue
        m = re.fullmatch(r'D(\d+)\*', line)
        if m and int(m[1]) >= 10:
            width = apertures.get(int(m[1]))
            continue
        if line.startswith(('G01', 'G02', 'G03')):
            mode = line[:3]
        m = re.search(r'X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D0([123])\*', line)
        if not m:
            continue
        x, y = int(m[1]) / 1e6 - ox, int(m[2]) / 1e6 + oy
        if m[5] == '1':
            if m[3] is not None and mode in ('G02', 'G03'):
                centre = (pos[0] + int(m[3]) / 1e6, pos[1] + int(m[4]) / 1e6)
                arcs.append((pos, (x, y), centre, width))
            else:
                segments.append((pos, (x, y), width))
        pos = (x, y)
    return segments, arcs


def read_drill(path, name):
    ox, oy = ORIGIN[name]
    tools, tool, hits = {}, None, []
    if not path.exists():
        return hits
    for line in path.read_text().splitlines():
        m = re.fullmatch(r'T(\d+)C([\d.]+)', line.strip())
        if m:
            tools[m[1]] = float(m[2])
            continue
        m = re.fullmatch(r'T(\d+)', line.strip())
        if m:
            tool = tools.get(m[1])
            continue
        m = re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)', line.strip())
        if m and tool:
            hits.append((float(m[1]) - ox, float(m[2]) + oy, tool))
    return hits


def edge_shapes(segments, arcs):
    """Circles, and bounding boxes of the closed paths made of lines and quarter arcs."""
    circles, pieces = set(), []
    for a, b, c, _ in arcs:
        r = math.dist(a, c)
        # KiCad plots a circle as two half arcs
        if math.dist(a, b) < 1e-6 or abs(math.dist(a, b) - 2 * r) < 1e-3:
            circles.add((round(c[0], 4), round(c[1], 4), round(r, 4)))
        else:
            pieces.append((a, b))
    circles = sorted(circles)
    pieces += [(a, b) for a, b, _ in segments]
    parent = {}

    def find(p):
        while parent.setdefault(p, p) != p:
            p = parent[p]
        return p

    key = lambda p: (round(p[0], 3), round(p[1], 3))
    for a, b in pieces:
        parent[find(key(a))] = find(key(b))
    groups = {}
    for p in list(parent):
        groups.setdefault(find(p), []).append(p)
    boxes = [(min(p[0] for p in g), min(p[1] for p in g), max(p[0] for p in g), max(p[1] for p in g)) for g in groups.values()]
    boxes.sort(key=lambda b: -(b[2] - b[0]) * (b[3] - b[1]))
    return circles, boxes


def clearance(point, circles, cuts, outer):
    best = min((outer_gap(point, outer),), default=1e9)
    for x, y, r in circles:
        best = min(best, math.dist(point, (x, y)) - r)
    for x0, y0, x1, y1 in cuts:
        dx = max(x0 - point[0], 0, point[0] - x1)
        dy = max(y0 - point[1], 0, point[1] - y1)
        best = min(best, math.hypot(dx, dy) if dx or dy else -min(point[0] - x0, x1 - point[0], point[1] - y0, y1 - point[1]))
    return best


def outer_gap(p, outer):
    return min(p[0] - outer[0], outer[2] - p[0], p[1] - outer[1], outer[3] - p[1])


def silk_margin(segments, circles, cuts, outer):
    worst = (1e9, None)
    for a, b, w in segments:
        for k in range(max(2, int(math.dist(a, b) / 0.05) + 1)):
            t = k / max(1, max(2, int(math.dist(a, b) / 0.05) + 1) - 1)
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            g = clearance(p, circles, cuts, outer) - (w or 0) / 2
            if g < worst[0]:
                worst = (g, (round(p[0], 2), round(p[1], 2)))
    return worst


def footprints(path):
    out = {}
    for block in re.split(r'\n\t\(footprint ', path.read_text())[1:]:
        at = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)', block)
        ref = re.search(r'\(property "Reference" "([^"]+)"', block)
        if at and ref:
            out[ref[1]] = (float(at[1]), float(at[2]))
    return out


def texts(board):
    return re.findall(r'\(gr_text "([^"]*)" \(at [-\d.]+ [-\d.]+ 0\) \(layer "F\.SilkS"\)', board)


def fit_round(ref_list, part, size, offset, source, diameters, routed):
    for ref in ref_list:
        d = diameters[ref]
        minus = ROUTED if routed[ref] else DRILLED_MINUS
        fits.append(dict(reference=ref, part=part, hole_mm=round(d, 3), part_mm=size, axis_offset_mm=offset, source=source,
                         nominal_margin_mm=round((d - size) / 2 - offset, 3), worst_margin_mm=round((d - minus - size) / 2 - offset, 3)))


def preview(name, silk, circles, drills, cuts, outer, back=False):
    scale = 300 / 25.4
    pad = 6
    w, h = outer[2], outer[3]
    im = Image.new('RGB', (round((w + 2 * pad) * scale), round((h + 2 * pad) * scale)), (216, 216, 216))
    d = ImageDraw.Draw(im)

    def xy(p):
        x = w - p[0] if back else p[0]
        return (x + pad) * scale, (h - p[1] + pad) * scale

    d.rectangle([xy((0, h)), xy((w, 0))] if not back else [xy((w, h)), xy((0, 0))], fill=(18, 18, 18))
    for x, y, r in [*circles, *[(a, b, c / 2) for a, b, c in drills]]:
        cx, cy = xy((x, y))
        d.ellipse([cx - r * scale, cy - r * scale, cx + r * scale, cy + r * scale], fill=(216, 216, 216))
    for x0, y0, x1, y1 in cuts:
        a, b = xy((x0, y1)) if not back else xy((x1, y1)), xy((x1, y0)) if not back else xy((x0, y0))
        d.rounded_rectangle([a, b], radius=0.5 * scale, fill=(216, 216, 216))
    for a, b, width in silk:
        px = max(1, round((width or 0.2) * scale))
        d.line([xy(a), xy(b)], fill=(245, 245, 245), width=px)
        for p in (a, b):
            cx, cy = xy(p)
            d.ellipse([cx - px / 2, cy - px / 2, cx + px / 2, cy + px / 2], fill=(245, 245, 245))
    (HERE / 'previews').mkdir(exist_ok=True)
    im.save(HERE / 'previews' / f'{name}-{"back" if back else "front"}.png', dpi=(300, 300), optimize=True)


def package(name, record):
    pcb = f'{name}/{name}.kicad_pcb'
    out = HERE / 'fabrication' / name
    g = out / 'gerbers'
    if g.exists():
        shutil.rmtree(g)
    g.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / 'drc.json'
        run('pcb', 'drc', '--severity-all', '--format', 'json', '-o', report, pcb)
        drc = json.loads(report.read_text())
    check(f'{name}: DRC has no violation and no unconnected item', not drc['violations'] and not drc['unconnected_items'],
          violations=len(drc['violations']))
    run('pcb', 'export', 'gerbers', '--no-protel-ext', '--layers', LAYERS, '-o', f'{g}/', pcb)
    run('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '--excellon-units', 'mm', '--generate-report',
        '--report-path', g / f'{name}-drill-report.txt', '-o', f'{g}/', pcb)
    # Read the exports back
    edge_seg, edge_arc = read_gerber(g / f'{name}-Edge_Cuts.gbr', name)
    silk, _ = read_gerber(g / f'{name}-F_Silkscreen.gbr', name)
    back_silk, _ = read_gerber(g / f'{name}-B_Silkscreen.gbr', name)
    drills = read_drill(g / f'{name}-NPTH.drl', name)
    pth = read_drill(g / f'{name}-PTH.drl', name)
    circles, boxes = edge_shapes(edge_seg, edge_arc)
    outer, cuts = boxes[0], boxes[1:]
    panel = GEOMETRY[name]
    (_, _), (w, h) = panel['outer_profile']['bounds_mm']
    check(f'{name}: outline is the DXF outline', abs(outer[0]) < 1e-3 and abs(outer[1]) < 1e-3 and abs(outer[2] - w) < 1e-3 and abs(outer[3] - h) < 1e-3,
          outline_mm=[round(outer[2], 3), round(outer[3], 3)])
    check(f'{name}: no plated holes', not pth)
    # Every DXF hole is present at its own centre
    found = [(x, y, 2 * r, True) for x, y, r in circles] + [(x, y, d, False) for x, y, d in drills]
    diameters, routed, worst = {}, {}, 0.0
    for c in panel['circles']:
        x, y = c['center_mm']
        near = min(found, key=lambda f: math.dist((f[0], f[1]), (x, y)))
        worst = max(worst, math.dist((near[0], near[1]), (x, y)))
        diameters[c['board_reference']] = near[2]
        routed[c['board_reference']] = near[3]
    check(f'{name}: every round hole of the DXF is exported at its centre', len(found) == len(panel['circles']) and worst < 2e-3,
          holes=len(found), largest_offset_mm=round(worst, 4), drilled=len(drills), routed=len(circles))
    changed = {r: (round(GEOMETRY[name]['circles'][i]['radius_mm'] * 2, 3), round(diameters[r], 3))
               for i, r in enumerate(c['board_reference'] for c in panel['circles'])
               if abs(GEOMETRY[name]['circles'][i]['radius_mm'] * 2 - diameters[r]) > 2e-3}
    record['changed_holes'] = {f'{a}->{b}': sorted(k for k, v in changed.items() if v == (a, b)) for a, b in sorted(set(changed.values()))}
    # Every DXF cut is present, grown only by what README lists
    grown = {}
    for r in panel['rectangular_cutouts']:
        (x0, y0), (x1, y1) = r['bounds_mm']
        mid = ((x0 + x1) / 2, (y0 + y1) / 2)
        box = min(cuts, key=lambda b: math.dist(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2), mid))
        grown[r['board_reference']] = tuple(round(v, 2) for v in (x0 - box[0], box[2] - x1, y0 - box[1], box[3] - y1))
    check(f'{name}: every rectangular cut of the DXF is exported, with rounded corners',
          len(cuts) == len(panel['rectangular_cutouts']) and all(v >= 0 for g_ in grown.values() for v in g_)
          and sum(abs(math.dist(a, c) - 0.5) < 1e-3 and math.dist(a, b) < 1 for a, b, c, _ in edge_arc) == 4 * len(cuts),
          cuts=len(cuts), growth_left_right_bottom_top_mm=sorted(set(grown.values())))
    # Silkscreen
    margin, where = silk_margin(silk, circles + [(x, y, d / 2) for x, y, d in drills], cuts, outer)
    check(f'{name}: silkscreen stays {SILK_TO_EDGE} mm from every hole, cut and edge', margin >= SILK_TO_EDGE, smallest_mm=round(margin, 3), at=where)
    check(f'{name}: silkscreen lines are at least {MIN_SILK_LINE} mm', min(s[2] for s in silk) >= MIN_SILK_LINE, thinnest_mm=min(s[2] for s in silk))
    margin, where = silk_margin(back_silk, circles + [(x, y, d / 2) for x, y, d in drills], cuts, outer)
    check(f'{name}: the credit on the back stays clear too', margin >= SILK_TO_EDGE, smallest_mm=round(margin, 3), at=where)
    if name == 'mainpanel':
        # The "5" of the bank ring, in the smallest text size
        x, y = 60.325 + 15.3, 108.458
        ys = [p[1] for a, b, _ in silk for p in (a, b) if abs(a[0] - x) < 1.6 and abs(a[1] - y) < 1.6 and abs(b[0] - x) < 1.6 and abs(b[1] - y) < 1.6]
        height = max(ys) - min(ys)
        check(f'{name}: the smallest text is at least {MIN_SILK_HEIGHT} mm high', height >= MIN_SILK_HEIGHT, height_mm=round(height, 2))
    board = (HERE / pcb).read_text()
    words = Counter(texts(board))
    if name == 'mainpanel':
        expected = Counter(row['text'] for row in LABELS)
    else:
        expected = Counter(row['text'] for row in LABELS if row['id'].startswith('top-port-label'))
    check(f'{name}: every word on the panel comes from the label map, once for each place', words == expected, words=sum(words.values()))
    # Copper
    copper = 0.0
    for side in ('F_Cu', 'B_Cu'):
        lines, halves = read_gerber(g / f'{name}-{side}.gbr', name)
        area = sum(math.pi * math.dist(a, c) * (w_ or 0) for a, _, c, w_ in halves)
        rings = {(round(c[0], 3), round(c[1], 3)) for _, _, c, _ in halves}
        copper = max(copper, area)
        check(f'{name}: {side} holds only the rings', not lines and 0 < len(rings) <= 7, rings=len(rings), area_mm2=round(area, 1))
    record['copper_mm2_each_side'] = round(copper, 1)
    # Package
    names = sorted(p.name for p in g.iterdir())
    with zipfile.ZipFile(out / f'x0xb0x-{name}-rev1-fabrication.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for fname in names:
            z.writestr(zipfile.ZipInfo(fname, (2026, 11, 5, 0, 0, 0)), (g / fname).read_bytes(), zipfile.ZIP_DEFLATED)
    needed = {f'{name}-{layer}.gbr' for layer in ('F_Cu', 'B_Cu', 'F_Mask', 'B_Mask', 'F_Silkscreen', 'B_Silkscreen', 'Edge_Cuts')}
    check(f'{name}: ZIP holds all seven layers', needed <= set(names), files=len(names))
    record['zip_sha256'] = sha(out / f'x0xb0x-{name}-rev1-fabrication.zip')
    preview(name, silk, circles, drills, cuts, outer)
    preview(name, back_silk, circles, drills, cuts, outer, back=True)
    return dict(diameters=diameters, routed=routed, circles=circles, drills=drills, cuts=cuts, silk=silk, grown=grown, outer=outer)


def main():
    version = run('--version').stdout.strip()
    record = dict(kicad_cli=version, status='Nothing ordered, made or fitted. Margins come from drawings and published tolerances.',
                  jlcpcb_limits_read='2026-11-05', panels={})
    results = {}
    for name in ('mainpanel', 'iopanel'):
        record['panels'][name] = dict(pcb_sha256=sha(HERE / name / f'{name}.kicad_pcb'))
        results[name] = package(name, record['panels'][name])
    # The panels against the current boards
    main_fp = footprints(WORK / 'mainboard/mainboard.kicad_pcb')
    io_fp = footprints(WORK / 'ioboard/ioboard.kicad_pcb')
    moved = [c['ref'] for c in ALIGNMENT['mainboard']['correspondences']
             if math.dist(main_fp[c['ref']], c['board_pcb_xy_mm']) > 0.01 and c['kind'] != 'button']
    check('mainboard: controls, LEDs and mounts stand where the panel alignment record has them', not moved, moved=moved)
    res = results['mainpanel']
    worst = {}
    centres = {c['board_reference']: c['center_mm'] for c in GEOMETRY['mainpanel']['circles']}
    for c in ALIGNMENT['mainboard']['correspondences']:
        if c['kind'] == 'button':
            continue
        x, y = c['board_pcb_xy_mm']
        panel_xy = (234.95 - x, -y - 12.7)
        worst[c['kind']] = max(worst.get(c['kind'], 0), math.dist(panel_xy, centres[c['ref']]))
    check('main panel: LEDs and controls are on their holes, mounts within 0.246 mm as in the original',
          worst['LED'] < 1e-3 and worst['control'] < 1e-3 and worst['mount'] < 0.246, residual_mm={k: round(v, 4) for k, v in worst.items()})
    centres = {c['board_reference']: c['center_mm'] for c in GEOMETRY['iopanel']['circles']}
    for r in GEOMETRY['iopanel']['rectangular_cutouts']:
        (x0, _), (x1, _) = r['bounds_mm']
        centres[r['board_reference']] = ((x0 + x1) / 2, 0)
    offset = {ref: abs(io_fp[ref][0] + 2.286 - centres[ref][0]) for ref in centres}
    check('rear panel: jacks line up with their holes across the board', max(offset.values()) < 1e-3, largest_mm=round(max(offset.values()), 4))
    # Fits
    for name in results:
        for refs, part, size, off, source in ROUND_FITS:
            present = [r for r in refs if r in results[name]['diameters']]
            fit_round(present, part, size, off, source, results[name]['diameters'], results[name]['routed'])
    grown = results['mainpanel']['grown']
    cut_rows = []
    for n in range(5, 28):
        ref = f'S{n}'
        short = min(6.35 + grown[ref][0] + grown[ref][1], 6.35 + grown[ref][2] + grown[ref][3])
        long_ = max(6.35 + grown[ref][0] + grown[ref][1], 12.7 + grown[ref][2] + grown[ref][3], 12.7 + grown[ref][0] + grown[ref][1])
        cut_rows.append(dict(reference=ref, part='PE cap, 12.1 x 5.9 mm', worst_short_side_mm=round((short - ROUTED - CAP[1]) / 2 - 0.0916, 3),
                             worst_long_side_mm=round((long_ - ROUTED - CAP[0]) / 2 - 0.0916, 3)))
    # DXF clearance from the rear datum record: sides, bottom, top
    for ref, sides, top in (('USB0', 0.33, 1.064), ('POWER0', 0.326, 0.684)):
        g_ = results['iopanel']['grown'][ref]
        cut_rows.append(dict(reference=ref, part='jack body, rear datum record', worst_side_mm=round(sides + min(g_[:2]) - ROUTED, 3),
                             worst_bottom_mm=round(g_[2] - ROUTED, 3), worst_top_mm=round(top + g_[3] - ROUTED, 3)))
    worst_round = min(f['worst_margin_mm'] for f in fits)
    worst_cut = min(v for row in cut_rows for k, v in row.items() if k.startswith('worst'))
    check('every part clears its hole at the worst factory tolerance', worst_round >= 0, smallest_mm=worst_round,
          at=sorted({f['part'] for f in fits if f['worst_margin_mm'] == worst_round}))
    check('every part clears its cut at the worst factory tolerance', worst_cut >= 0, smallest_mm=worst_cut)
    flange = results['mainpanel']['diameters']['LED1'] + DRILLED_PLUS
    check('the LED flange cannot pass the hole', flange < 5.9 - 0.25, largest_hole_mm=round(flange, 2), smallest_flange_mm=5.65)
    # Summarise the fits by kind
    summary = {}
    for f in fits:
        row = summary.setdefault(f['part'], dict(part=f['part'], references=[], hole_mm=f['hole_mm'], part_mm=f['part_mm'], axis_offset_mm=f['axis_offset_mm'],
                                                 nominal_margin_mm=f['nominal_margin_mm'], worst_margin_mm=f['worst_margin_mm'], source=f['source']))
        row['references'].append(f['reference'])
    record['round_fits'] = list(summary.values())
    record['cut_fits'] = dict(buttons=min((r for r in cut_rows if r['reference'].startswith('S')), key=lambda r: r['worst_short_side_mm']),
                              jacks=[r for r in cut_rows if not r['reference'].startswith('S')])
    record['checks'] = checks
    record['passed'] = all(c['passed'] for c in checks)
    (HERE / 'verification.json').write_text(json.dumps(record, indent=2) + '\n')
    failed = [c['name'] for c in checks if not c['passed']]
    print(f'{len(checks) - len(failed)} of {len(checks)} checks pass')
    if failed:
        raise SystemExit('failed: ' + '; '.join(failed))


if __name__ == '__main__':
    main()
