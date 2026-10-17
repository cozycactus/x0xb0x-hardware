#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Re-import the packaged Gerbers and drills and check them against the KiCad board files.

1. Every Gerber and drill file is parsed (the revision-26 comparison readers) and compared
   with the PCB as KiCad's Python reads it: each copper pad by reference, pad number,
   position, net and aperture; vias; every track and arc (ends, width, net); zone fill area
   per net; mask and paste openings; drills (PTH and NPTH, position and size); outline
   contours; silkscreen widths and extent.  The Gerber job file must describe the board.
2. gerbv (an independent reader) re-exports every file; its output must carry the same
   flashes, draws, regions and drill hits.  gerbv also renders top and bottom previews.
3. The Gerber/drill files must have the byte sizes of the export that this revision's
   fabrication comparison compared object by object with the original Eagle boards, the
   copper should be unchanged when kicad-cli checks and refills the zones, and KiCad's DRC
   of the copper as saved (no refill) must find no copper violation.
4. Minimum copper clearance, hole clearance, hole-to-hole and copper-to-edge distances are
   measured with KiCad's DRC on temporary copies whose rules are raised until fewer than
   199 (KiCad's per-type report limit) violations remain; track widths, drills and annular
   rings come from the PCB.
Writes verification.json and the previews next to this script; the PCB files are only read.
Run from the repository root:  python3 -I kicad-working/fabrication/revision-<N>/verify_packages.py
"""
import collections
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = REPO / 'kicad-working'
REV = int(HERE.name.split('-')[-1])
# Gerber and Excellon readers of the revision-26 comparison; the export it compared, if any
sys.path.insert(0, str(WORK / 'validation' / 'models-review-26' / 'fabrication-comparison'))
COMPARISON = WORK / 'validation' / f'models-review-{REV}' / 'fabrication-comparison'
sys.dont_write_bytecode = True
import excellon  # noqa: E402
from gerber import Gerber, contour_points  # noqa: E402

CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
PY = os.environ.get('KICAD_PYTHON', '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
GERBV = os.environ.get('GERBV', shutil.which('gerbv') or '/opt/homebrew/bin/gerbv')
BOARDS = ('mainboard', 'ioboard')
LAYERS = ('F_Cu', 'B_Cu', 'F_Mask', 'B_Mask', 'F_Paste', 'B_Paste', 'F_Silkscreen', 'B_Silkscreen', 'Edge_Cuts')
TOL = 0.001
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
tmp = Path(tempfile.mkdtemp(prefix='x0xb0x-verify-'))
env = dict(os.environ, KICAD_CONFIG_HOME=str(tmp / 'config'), XDG_CACHE_HOME=str(tmp / 'cache'))


def run(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=env, **kw)
    assert r.returncode == 0, (cmd, r.stdout[-500:], r.stderr[-800:])
    return r


def key(p, nd=3):
    return (round(p[0], nd) + 0.0, round(p[1], nd) + 0.0)


def area(contours):
    total = 0.0
    for c in contours:
        pts = contour_points(c, 2.0)
        total += 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return abs(total)


def ap_dims(g, ap):
    a = g.apertures[ap]
    if a['shape'] == 'C':
        return ('C', a['params'][0], a['params'][0])
    if a['shape'] in ('R', 'O'):
        return (a['shape'], a['params'][0], a['params'][1])
    return (a['shape'], None, None)


def check(name, passed, **detail):
    return dict(check=name, passed=bool(passed), **detail)


def multiset_match(expected, found, tol=TOL):
    """expected/found: lists of (x, y, payload). Returns unmatched of each side."""
    cell = lambda v: math.floor(v * 10)  # noqa: E731
    grid = collections.defaultdict(list)
    for i, (x, y, _) in enumerate(found):
        grid[(cell(x), cell(y))].append(i)
    used, missing = set(), []
    for x, y, pay in expected:
        hit = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in grid.get((cell(x) + dx, cell(y) + dy), ()):
                    if i not in used and math.hypot(found[i][0] - x, found[i][1] - y) <= tol and \
                            (pay is None or found[i][2] is None or found[i][2] == pay):
                        hit = i
                        break
                if hit is not None:
                    break
            if hit is not None:
                break
        if hit is None:
            missing.append((x, y, pay))
        else:
            used.add(hit)
    return missing, [found[i] for i in range(len(found)) if i not in used]


def loops(draws):
    """Chain outline segments into contours; returns [(closed, bbox, n)]."""
    segs = [(key(d['p1'], 4), key(d['p2'], 4)) for d in draws]
    left, out = list(range(len(segs))), []
    while left:
        i = left.pop(0)
        chain, start, end = [i], segs[i][0], segs[i][1]
        grown = True
        while grown and end != start:
            grown = False
            for j in list(left):
                a, b = segs[j]
                if a == end or b == end:
                    end = b if a == end else a
                    chain.append(j)
                    left.remove(j)
                    grown = True
                    break
        pts = [p for k in chain for p in segs[k]]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        out.append(dict(closed=end == start, segments=len(chain),
                        bbox=[min(xs), min(ys), max(xs), max(ys)],
                        size=[round(max(xs) - min(xs), 4), round(max(ys) - min(ys), 4)]))
    return sorted(out, key=lambda c: -c['size'][0] * c['size'][1])


def verify_board(b, X):
    G = HERE / b / 'gerbers'
    gb = {L: Gerber(G / f'{b}-{L}.gbr') for L in LAYERS}
    checks, info = [], {}
    # the reader lists aperture-macro body lines that follow a line break; they are not commands
    unknown = {L: [u for u in g.unknown if not re.match(r'^\s*[\d$]', u)] for L, g in gb.items()}
    checks.append(check('Every Gerber parses with only known commands', not any(unknown.values()),
                        unknown={L: u[:5] for L, u in unknown.items() if u}))
    heads = {L: re.search(r'%TF.FileFunction,([^*]+)\*%', (G / f'{b}-{L}.gbr').read_text()).group(1) for L in LAYERS}
    info['file_functions'] = heads

    # Copper: pads by reference/pad number, vias, tracks, zone fills
    for L, side in (('F_Cu', 'F.Cu'), ('B_Cu', 'B.Cu')):
        g = gb[L]
        exp = [(p['pos'][0], p['pos'][1], (p['ref'], p['num'])) for p in X['pads']
               if side in p['layers'] and p['attr'] != 'NPTH']
        got = [(f['pos'][0], f['pos'][1], tuple(f['attrs']['.P'].split(',')[:2])) for f in g.flashes if '.P' in f['attrs']]
        got += [(sum(x for x, _ in contour_points(r['contours'][0])) / len(contour_points(r['contours'][0])),
                 sum(y for _, y in contour_points(r['contours'][0])) / len(contour_points(r['contours'][0])),
                 tuple(r['attrs']['.P'].split(',')[:2])) for r in g.regions if '.P' in r['attrs']]
        miss, extra = multiset_match(exp, got)
        nets = {(p['ref'], p['num'], key(p['pos'])): p['net'] or 'N/C' for p in X['pads']}
        net_bad = [f['attrs'] for f in g.flashes if '.P' in f['attrs'] and
                   nets.get((*f['attrs']['.P'].split(',')[:2], key(f['pos']))) not in (f['attrs'].get('.N'), None)]
        size_bad, macro = [], 0
        bypos = collections.defaultdict(list)
        for p in X['pads']:
            if side in p['layers']:
                bypos[key(p['pos'])].append(p)
        for f in g.flashes:
            if '.P' not in f['attrs']:
                continue
            shape, w, h = ap_dims(g, f['ap'])
            if w is None:
                macro += 1
                continue
            cand = [p for p in bypos[key(f['pos'])] if (p['ref'], p['num']) == tuple(f['attrs']['.P'].split(',')[:2])]
            if not any(sorted((round(w, 4), round(h, 4))) == sorted((round(p['size'][0], 4), round(p['size'][1], 4)))
                       for p in cand):
                size_bad.append((f['attrs']['.P'], f['pos'], shape, w, h, [c['size'] for c in cand]))
        checks.append(check(f'{L}: every pad flashed at its position with its reference, pad number and net',
                            not miss and not extra and not net_bad, expected=len(exp), found=len(got),
                            missing=miss[:10], extra=extra[:10], net_mismatch=net_bad[:10]))
        checks.append(check(f'{L}: pad aperture sizes equal the PCB pad sizes', not size_bad,
                            compared=len(got) - macro, macro_apertures_not_sized=macro, differences=size_bad[:10]))
        vias = [(f['pos'][0], f['pos'][1], round(ap_dims(g, f['ap'])[1], 4)) for f in g.flashes
                if g.apertures[f['ap']]['function'] == 'ViaPad']
        miss, extra = multiset_match([(v['pos'][0], v['pos'][1], round(v['width'], 4)) for v in X['vias']], vias)
        checks.append(check(f'{L}: via pads', not miss and not extra, expected=len(X['vias']), found=len(vias),
                            missing=miss, extra=extra))
        tr = [t for t in X['tracks'] if t['layer'] == side]
        draws = [d for d in g.draws if g.apertures[d['ap']]['function'] == 'Conductor']
        exp_t = collections.Counter((frozenset((key(t['start']), key(t['end']))), round(t['width'], 4), t['net'], t['arc'])
                                    for t in tr)
        got_t = collections.Counter((frozenset((key(d['p1']), key(d['p2']))), round(ap_dims(g, d['ap'])[1], 4),
                                     d['attrs'].get('.N'), d['interp'] != 'G01') for d in draws)
        other = [d for d in g.draws if g.apertures[d['ap']]['function'] != 'Conductor']
        checks.append(check(f'{L}: every track and arc (ends, width, net)', exp_t == got_t and not other,
                            expected=len(tr), found=len(draws), non_conductor_draws=len(other),
                            missing=[list(k[0]) + [k[1], k[2]] for k in (exp_t - got_t)][:10],
                            extra=[list(k[0]) + [k[1], k[2]] for k in (got_t - exp_t)][:10]))
        fills = collections.defaultdict(float)
        for r in g.regions:
            if '.P' not in r['attrs']:
                fills[r['attrs'].get('.N')] += area(r['contours']) * (1 if r['polarity'] == 'D' else -1)
        exp_f = collections.defaultdict(float)
        for z in X['zones']:
            if z['layer'] == side:
                exp_f[z['net']] += z['area_mm2']
        bad = {n: (round(fills.get(n, 0), 2), round(a, 2)) for n, a in exp_f.items() | fills.items()
               if abs(fills.get(n, 0) - exp_f.get(n, 0)) > max(0.5, 0.002 * exp_f.get(n, 0))}
        checks.append(check(f'{L}: zone fill area per net equals the saved fill (0.2 %)', not bad,
                            gerber_mm2={n: round(a, 1) for n, a in fills.items()},
                            pcb_mm2={n: round(a, 1) for n, a in exp_f.items()}, differences=bad))

    # Mask and paste openings
    for L, side in (('F_Mask', 'F.Mask'), ('B_Mask', 'B.Mask'), ('F_Paste', 'F.Paste'), ('B_Paste', 'B.Paste')):
        g = gb[L]
        exp = [(p['pos'][0], p['pos'][1], None) for p in X['pads'] if side in p['layers']]
        exp += [(v['pos'][0], v['pos'][1], None) for v in X['vias'] if side in v['mask']]
        got = [(f['pos'][0], f['pos'][1], None) for f in g.flashes]
        got += [(sum(x for x, _ in contour_points(r['contours'][0])) / len(contour_points(r['contours'][0])),
                 sum(y for _, y in contour_points(r['contours'][0])) / len(contour_points(r['contours'][0])), None)
                for r in g.regions]
        miss, extra = multiset_match(exp, got, tol=0.01)
        checks.append(check(f'{L}: one opening per pad on the layer, none for the tented vias',
                            not miss and not extra and not g.draws, expected=len(exp), found=len(got),
                            draws=len(g.draws), missing=miss[:10], extra=extra[:10]))
    tented = all(not v['mask'] for v in X['vias'])
    checks.append(check('All vias tented on both sides (board setting)', tented and X['tenting'] == dict(front=True, back=True),
                        vias=len(X['vias']), tenting=X['tenting']))

    # Drills
    for kind, fname in (('PTH', f'{b}-PTH.drl'), ('NPTH', f'{b}-NPTH.drl')):
        holes = excellon.read(G / fname)
        exp = [(p['pos'][0], p['pos'][1], round(p['drill'][0], 3)) for p in X['pads'] if p['attr'] == kind]
        if kind == 'PTH':
            exp += [(v['pos'][0], v['pos'][1], round(v['drill'], 3)) for v in X['vias']]
        slots = [p for p in X['pads'] if p['attr'] == kind and abs(p['drill'][0] - p['drill'][1]) > 1e-6]
        got = [(h['pos'][0], h['pos'][1], round(h['drill'], 3)) for h in holes]
        miss, extra = multiset_match(exp, got, tol=0.0006)
        text = (G / fname).read_text()
        ff = 'Plated' if kind == 'PTH' else 'NonPlated'
        checks.append(check(f'{fname}: every {kind} hole at its position and size', not miss and not extra and
                            not slots and f'TF.FileFunction,{ff}' in text, expected=len(exp), found=len(got),
                            slots=len(slots), missing=miss[:10], extra=extra[:10]))
        info[f'{kind}_tools'] = dict(sorted(collections.Counter(h['drill'] for h in holes).items()))

    # Outline
    edge = gb['Edge_Cuts']
    lp = loops(edge.draws)
    checks.append(check('Edge_Cuts draws equal the PCB Edge.Cuts segments and form closed contours',
                        len(edge.draws) == X['outline']['segments'] and all(c['closed'] for c in lp) and not edge.flashes,
                        draws=len(edge.draws), pcb_segments=X['outline']['segments'], contours=lp))
    checks.append(check('Edge_Cuts holds exactly one contour (the board)', len(lp) == 1, contours=len(lp),
                        note='a second contour would be routed by the fab as a separate shape'))
    board = lp[0]['bbox']
    info['board_size_mm'] = lp[0]['size']

    # Silkscreen
    for L in ('F_Silkscreen', 'B_Silkscreen'):
        g = gb[L]
        widths = sorted({round(ap_dims(g, d['ap'])[1], 4) for d in g.draws if ap_dims(g, d['ap'])[1] is not None})
        zero = sum(1 for d in g.draws if ap_dims(g, d['ap'])[1] == 0)
        off = []
        for d in g.draws:
            w = (ap_dims(g, d['ap'])[1] or 0) / 2
            for x, y in (d['p1'], d['p2']):
                if x - w < board[0] - 1e-6 or x + w > board[2] + 1e-6 or y - w < board[1] - 1e-6 or y + w > board[3] + 1e-6:
                    off.append([round(x, 3), round(y, 3)])
                    break
        info[L] = dict(draws=len(g.draws), flashes=len(g.flashes), regions=len(g.regions),
                       line_widths_mm=widths, min_nonzero_width_mm=min([w for w in widths if w > 0], default=None),
                       zero_width_draws=zero, draws_past_board_outline=len(off), first_past_outline=off[:8])

    # Gerber job file
    job = json.loads((G / f'{b}-job.gbrjob').read_text())
    gs = job['GeneralSpecs']
    listed = [f['Path'] for f in job['FilesAttributes']]
    checks.append(check('Gerber job file: 2 copper layers, 1.6 mm, PCB edge size, every listed file present',
                        gs['LayerNumber'] == 2 and abs(gs['BoardThickness'] - 1.6) < 1e-9 and
                        all((G / p).is_file() for p in listed) and
                        abs(gs['Size']['X'] - X['outline']['width']) < 0.01 and abs(gs['Size']['Y'] - X['outline']['height']) < 0.01,
                        job_size=gs['Size'], pcb_edge_bbox_including_stroke=[X['outline']['width'], X['outline']['height']], job_layers=gs['LayerNumber'], job_thickness=gs['BoardThickness'],
                        files=listed, design_rules=job.get('DesignRules')))
    return checks, info, gb


def gerbv_roundtrip(b, gb):
    G = HERE / b / 'gerbers'
    out, checks = tmp / 'gerbv' / b, []
    out.mkdir(parents=True)
    for L, g in gb.items():
        src = G / f'{b}-{L}.gbr'
        if not (g.flashes or g.draws or g.regions):
            # gerbv takes a file without apertures for RS-274D and exports nothing
            checks.append(check(f'gerbv re-export {L}: empty layer, nothing to compare', True, objects=0))
            continue
        r = run([GERBV, '-x', 'rs274x', '-o', out / f'{L}.gbr', src])
        text = (out / f'{L}.gbr').read_text()
        assert '%MOIN*%' in text
        (out / f'{L}-mm.gbr').write_text(text.replace('%MOIN*%', '%MOMM*%'))
        h = Gerber(out / f'{L}-mm.gbr')
        s = 25.4
        fl_k = [(f['pos'][0], f['pos'][1], None) for f in g.flashes]
        fl_g = [(f['pos'][0] * s, f['pos'][1] * s, None) for f in h.flashes]
        miss, extra = multiset_match(fl_k, fl_g, tol=0.002)
        ends_k = [(*d[q], None) for d in g.draws for q in ('p1', 'p2')]
        ends_g = [(d[q][0] * s, d[q][1] * s, None) for d in h.draws for q in ('p1', 'p2')]
        ends_miss, ends_extra = multiset_match(ends_k, ends_g, tol=0.002)
        ar_k = sum(area(r['contours']) for r in g.regions)
        ar_g = sum(area([[(c[0], c[1] * s, c[2] * s) + ((c[3][0] * s, c[3][1] * s),) if len(c) > 3 and c[3] else
                          (c[0], c[1] * s, c[2] * s) for c in cont] for cont in r['contours']]) for r in h.regions)
        ok = not miss and not extra and not ends_miss and not ends_extra and len(g.draws) == len(h.draws) and \
            len(g.regions) == len(h.regions) and abs(ar_k - ar_g) <= max(0.01, 1e-4 * ar_k) and not r.stderr.strip()
        checks.append(check(f'gerbv re-export {L}: same flashes, draws and regions', ok,
                            flashes=[len(g.flashes), len(h.flashes)], draws=[len(g.draws), len(h.draws)],
                            draw_ends_unmatched=len(ends_miss) + len(ends_extra), regions=[len(g.regions), len(h.regions)],
                            region_area_mm2=[round(ar_k, 2), round(ar_g, 2)], flash_missing=miss[:5], flash_extra=extra[:5],
                            stderr=r.stderr.strip()[:300]))
    for kind in ('PTH', 'NPTH'):
        src = G / f'{b}-{kind}.drl'
        r = run([GERBV, '-x', 'drill', '-o', out / f'{kind}.drl', src])
        k = excellon.read(src)
        text = (out / f'{kind}.drl').read_text()
        tools, holes, cur = {}, [], None
        for line in text.splitlines():
            m = re.match(r'^T(\d+)C([\d.]+)', line)
            if m:
                tools[int(m.group(1))] = float(m.group(2)) * 25.4
                continue
            m = re.match(r'^T(\d+)$', line)
            if m:
                cur = int(m.group(1))
                continue
            m = re.match(r'^X(-?\d+)Y(-?\d+)$', line)
            if m:
                holes.append((int(m.group(1)) / 1e4 * 25.4, int(m.group(2)) / 1e4 * 25.4, tools[cur]))
        assert text.startswith('M48') and 'INCH' in text
        miss, extra = multiset_match([(h['pos'][0], h['pos'][1], None) for h in k],
                                     [(x, y, None) for x, y, _ in holes], tol=0.003)
        size_ok = collections.Counter(round(h['drill'] / 25.4, 3) for h in k) == \
            collections.Counter(round(d / 25.4, 3) for _, _, d in holes)
        checks.append(check(f'gerbv re-export {kind} drill: same hits and tool sizes', not miss and not extra and size_ok,
                            hits=[len(k), len(holes)], missing=miss[:5], extra=extra[:5]))
    previews = {}
    for side, files in (('top', ['Edge_Cuts', 'F_Silkscreen', 'F_Cu']), ('bottom', ['Edge_Cuts', 'B_Silkscreen', 'B_Cu'])):
        png = HERE / b / f'{b}-preview-{side}.png'
        cmd = [GERBV, '-x', 'png', '-o', png, '-D', '150', '-a', '-B', '2', '-b', '#0b3d1a']
        # gerbv draws the first file on top: holes, outline, silkscreen, copper
        layer_files = [G / f'{b}-{kind}.drl' for kind in ('PTH', 'NPTH')] + [G / f'{b}-{L}.gbr' for L in files]
        for c in ('#000000ff', '#000000ff', '#ffff00ff', '#f2f2f2ff', '#c8a040ff'):
            cmd += ['-f', c]
        if side == 'bottom':
            cmd += ['-m', 'Y']
        run(cmd + layer_files)
        previews[side] = png.name
    return checks, previews


def comparison_sizes(b):
    if not (COMPARISON / 'gerber-comparison.json').is_file():
        return check(f'Files have the byte sizes of the revision-{REV} Eagle comparison export', False,
                     note='no fabrication comparison recorded for this revision')
    rec = json.loads((COMPARISON / 'gerber-comparison.json').read_text())
    sizes = rec['generated_files'][b]
    same_pcb = rec['inputs']['kicad_pcb_sha256'][b] == sha(WORK / b / f'{b}.kicad_pcb')
    diff = {n: (v['bytes'], (HERE / b / 'gerbers' / n).stat().st_size if (HERE / b / 'gerbers' / n).is_file() else None)
            for n, v in sizes.items()
            if not (HERE / b / 'gerbers' / n).is_file() or (HERE / b / 'gerbers' / n).stat().st_size != v['bytes']}
    return check(f'Files have the byte sizes of the revision-{REV} Eagle comparison export (same PCB hash)',
                 same_pcb and not diff, files_compared=len(sizes), differences=diff, same_pcb_hash=same_pcb)


def zone_refill(b, gb):
    out = tmp / 'refill' / b
    out.mkdir(parents=True)
    run([CLI, 'pcb', 'export', 'gerbers', '--board-plot-params', '--check-zones', '-l', 'F.Cu,B.Cu', '-o', f'{out}/',
         WORK / b / f'{b}.kicad_pcb'])
    res, regions = {}, {}
    for L in ('F_Cu', 'B_Cu'):
        strip = lambda t: re.sub(r'(TF\.CreationDate|G04 Created by)[^*]*\*', '', t)  # noqa: E731
        a = strip((HERE / b / 'gerbers' / f'{b}-{L}.gbr').read_text())
        c = strip((out / f'{b}-{L}.gbr').read_text())
        res[L] = a == c
        if res[L]:
            continue
        refilled = Gerber(out / f'{b}-{L}.gbr')
        rows = []
        for ra, rc in zip([r for r in gb[L].regions if '.P' not in r['attrs']],
                          [r for r in refilled.regions if '.P' not in r['attrs']]):
            pa = {key(p[1:3], 2) for c_ in ra['contours'] for p in c_}
            pc = {key(p[1:3], 2) for c_ in rc['contours'] for p in c_}
            moved = collections.Counter((5 * round(x / 5), 5 * round(y / 5)) for x, y in pa - pc)
            rows.append(dict(net=ra['attrs'].get('.N'), saved_mm2=round(area(ra['contours']), 2),
                             refilled_mm2=round(area(rc['contours']), 2), vertices_changed=len(pa - pc),
                             changed_near_5mm_grid=[list(k) + [n] for k, n in moved.most_common(12) if n >= 5]))
        regions[L] = rows
    # advisory: an older fill blocks ordering only if the DRC of the saved copper fails
    return check('Copper identical after kicad-cli --check-zones (saved zone fill is current)', all(res.values()),
                 advisory=True, layers=res, regions=regions)


IGNORED_DRC = ('silk_over_copper', 'silk_overlap', 'silk_edge_clearance', 'track_dangling', 'lib_footprint_issues')


def drc_saved(b):
    """DRC of the copper exactly as saved (and plotted): no zone refill, the board's own rules."""
    d = tmp / 'drc-saved' / b
    d.mkdir(parents=True)
    for ext in ('kicad_pcb', 'kicad_pro'):
        shutil.copy(WORK / b / f'{b}.{ext}', d)
    rep = {}
    for mode, extra in (('saved', []), ('refilled', ['--refill-zones'])):
        run([CLI, 'pcb', 'drc', '--format', 'json', '--units', 'mm', '--severity-all', *extra, '-o', d / f'{mode}.json',
             d / f'{b}.kicad_pcb'])
        rep[mode] = [v for v in json.loads((d / f'{mode}.json').read_text())['violations'] if v['type'] not in IGNORED_DRC]
    rows = [dict(type=v['type'], description=v['description'],
                 items=[[i['description'], [i['pos']['x'], -i['pos']['y']]] for i in v['items']]) for v in rep['saved']]
    return check('DRC of the saved copper as plotted (no zone refill): no clearance or other copper violation',
                 not rep['saved'], violations=len(rep['saved']), types=dict(collections.Counter(v['type'] for v in rep['saved'])),
                 first=rows[:30], violations_after_refill=len(rep['refilled']),
                 ignored_types=list(IGNORED_DRC))


def drc_minimums(b):
    d = tmp / 'drc' / b
    d.mkdir(parents=True)
    shutil.copy(WORK / b / f'{b}.kicad_pcb', d)
    pro0 = json.loads((WORK / b / f'{b}.kicad_pro').read_text())
    rules0 = pro0['board']['design_settings']['rules']
    nc = max(c.get('clearance', 0) for c in pro0['net_settings']['classes'])
    spec = {'clearance': ['min_clearance', max(rules0['min_clearance'], nc)],
            'hole_clearance': ['min_hole_clearance', rules0['min_hole_clearance']],
            'hole_to_hole': ['min_hole_to_hole', rules0['min_hole_to_hole']],
            'copper_edge_clearance': ['min_copper_edge_clearance', rules0['min_copper_edge_clearance']]}
    state = {t: dict(lo=v[1], hi=None, x=v[1] + 0.25, done=None, runs=[]) for t, v in spec.items()}
    for it in range(14):
        active = [t for t, s in state.items() if s['done'] is None]
        if not active:
            break
        pro = json.loads(json.dumps(pro0))
        for t, s in state.items():
            pro['board']['design_settings']['rules'][spec[t][0]] = round(s['x'], 4)
        for c in pro['net_settings']['classes']:
            c['clearance'] = round(state['clearance']['x'], 4)
        (d / f'{b}.kicad_pro').write_text(json.dumps(pro, indent=2))
        run([CLI, 'pcb', 'drc', '--format', 'json', '--units', 'mm', '--severity-all', '-o', d / 'drc.json', d / f'{b}.kicad_pcb'])
        rep = json.loads((d / 'drc.json').read_text())
        for t in active:
            s = state[t]
            vs = [v for v in rep['violations'] if v['type'] == t]
            s['runs'].append([round(s['x'], 4), len(vs)])
            if 0 < len(vs) < 199:
                best = min(vs, key=lambda v: float(re.search(r'actual ([\d.]+) mm', v['description']).group(1)))
                s['done'] = dict(min_mm=float(re.search(r'actual ([\d.]+) mm', best['description']).group(1)),
                                 rule_tested_mm=round(s['x'], 4), violations_at_that_rule=len(vs),
                                 items=[[i['description'], [i['pos']['x'], -i['pos']['y']]] for i in best['items']])
            elif not vs:
                s['lo'] = s['x']
                s['x'] = (s['x'] + s['hi']) / 2 if s['hi'] else s['x'] + 0.5
                if s['x'] > 6:
                    s['done'] = dict(min_mm=None, note=f'no violation up to {s["lo"]} mm')
            else:
                s['hi'] = s['x']
                s['x'] = (s['lo'] + s['x']) / 2
    return {t: dict(board_rule_mm=spec[t][1], runs=s['runs'], **(s['done'] or dict(min_mm=None, note='not converged')))
            for t, s in state.items()}


report = dict(schema=1, kicad_cli=run([CLI, '--version']).stdout.strip(),
              gerbv=run([GERBV, '--version']).stdout.strip().splitlines()[0], boards={})
for b in BOARDS:
    xpath = tmp / f'{b}-extract.json'
    run([PY, '-I', HERE / 'extract_board.py', WORK / b / f'{b}.kicad_pcb', xpath])
    X = json.loads(xpath.read_text())
    checks, info, gb = verify_board(b, X)
    gchecks, previews = gerbv_roundtrip(b, gb)
    checks += gchecks
    checks.append(comparison_sizes(b))
    checks.append(zone_refill(b, gb))
    checks.append(drc_saved(b))
    rings = [p for p in X['pads'] if p['ring'] is not None]
    pr = min(rings, key=lambda p: p['ring'])
    vr = min(X['vias'], key=lambda v: v['width'] - v['drill'])
    tw = min(X['tracks'], key=lambda t: t['width'])
    measured = dict(
        board_size_mm=info['board_size_mm'], copper_layers=X['copper_layers'], thickness_mm=X['thickness_mm'],
        min_track_width_mm=round(tw['width'], 4), min_track_width_count=sum(1 for t in X['tracks'] if abs(t['width'] - tw['width']) < 1e-6),
        min_drill_mm=min([round(p['drill'][0], 4) for p in X['pads'] if p['attr'] != 'SMD'] + [v['drill'] for v in X['vias']]),
        min_pad_drill_mm=min(round(p['drill'][0], 4) for p in X['pads'] if p['attr'] == 'PTH'),
        max_drill_mm=max(round(p['drill'][0], 4) for p in X['pads'] if p['attr'] != 'SMD'),
        min_pad_annular_ring_mm=dict(value=round(pr['ring'], 4), at=f"{pr['ref']}.{pr['num']}", pad=pr['size'], drill=pr['drill']),
        min_via_annular_ring_mm=round((vr['width'] - vr['drill']) / 2, 4),
        holes=dict(PTH_pads=sum(1 for p in X['pads'] if p['attr'] == 'PTH'), vias=len(X['vias']),
                   PTH_total=sum(1 for p in X['pads'] if p['attr'] == 'PTH') + len(X['vias']),
                   NPTH=sum(1 for p in X['pads'] if p['attr'] == 'NPTH'), slots=0),
        smd_pads=sum(1 for p in X['pads'] if p['attr'] == 'SMD'),
        footprints=dict(total=len(X['footprints']),
                        top=sum(1 for f in X['footprints'] if f['side'] == 'top'),
                        bottom=sum(1 for f in X['footprints'] if f['side'] == 'bottom')),
        drc_measured_minimums=drc_minimums(b))
    report['boards'][b] = dict(pcb_sha256=sha(WORK / b / f'{b}.kicad_pcb'), passed=all(c['passed'] for c in checks),
                               blocking_failures=[c['check'] for c in checks if not c['passed'] and not c.get('advisory')],
                               checks=checks, info=info, measured=measured, previews=previews)
shutil.rmtree(tmp)
(HERE / 'verification.json').write_text(json.dumps(report, indent=1) + '\n')
summary = {b: dict(passed=r['passed'], checks=len(r['checks']), blocking_failures=r['blocking_failures'],
                   advisory_failures=[c['check'] for c in r['checks'] if not c['passed'] and c.get('advisory')])
           for b, r in report['boards'].items()}
print(json.dumps(summary, indent=1))
