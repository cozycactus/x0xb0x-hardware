# SPDX-License-Identifier: CC0-1.0
"""Layer-by-layer comparison of KiCad Gerber/Excellon output with the original
Eagle 4.13 board geometry (decoded binary -> staging XML, Eagle 4.13 CAM
semantics for restring and stop frame).

Usage: python3 compare.py <kicad-gerber-dir> <out.json>
"""
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
import eagle_model
import excellon
import gerber
import drills

EAGLE = str(Path(os.environ.get('X0X_EAGLE_XML', Path(__file__).resolve().parents[5] / 'kicad-import/validation/repaired-eagle-xml'))) + '/'
TOL = 0.002          # mm position tolerance (Gerber 4.6 vs Eagle 0.1 um)
WTOL = 0.0011        # mm size tolerance


def r3(v):
    return round(v, 4)


def kicad_xy(p):
    return [r3(p[0]), r3(-p[1])]


def loc(p):
    return dict(gerber_xy_mm=[r3(p[0]), r3(p[1])], kicad_xy_mm=kicad_xy(p))


def oriented(w, h, angle):
    a = round(angle) % 180
    if a == 0:
        return (w, h), True
    if a == 90:
        return (h, w), True
    return (w, h), False


def aperture_dims(ap):
    s, p = ap['shape'], ap['params']
    if s == 'C':
        return 'circle', p[0], p[0]
    if s == 'O':
        return ('oval' if abs(p[0] - p[1]) > 1e-6 else 'circle'), p[0], p[1]
    if s == 'R':
        return 'rect', p[0], p[1]
    return s, None, None


def match_flashes(expected, flashes, apertures, label):
    """expected: list of dict(kind, w, h, pos, ident). Flash shapes compared on axis-aligned dims."""
    by_pos = defaultdict(list)
    for i, f in enumerate(flashes):
        by_pos[(round(f['pos'][0], 2), round(f['pos'][1], 2))].append(i)
    used, diffs, matched = set(), [], 0
    for e in expected:
        x, y = e['pos']
        cand = []
        for dx in (-0.01, 0, 0.01):
            for dy in (-0.01, 0, 0.01):
                cand += by_pos.get((round(x + dx, 2), round(y + dy, 2)), [])
        best = None
        for i in set(cand):
            if i in used:
                continue
            d = math.hypot(flashes[i]['pos'][0] - x, flashes[i]['pos'][1] - y)
            if d < TOL and (best is None or d < best[0]):
                best = (d, i)
        if best is None:
            diffs.append(dict(type='missing_in_kicad', what=e['ident'], expected_shape=[e['kind'], r3(e['w']), r3(e['h'])],
                              **loc(e['pos'])))
            continue
        used.add(best[1])
        kind, w, h = aperture_dims(apertures[flashes[best[1]]['ap']])
        (ew, eh), axis = oriented(e['w'], e['h'], e['angle'])
        ekind = e['kind']
        if kind in ('rect',) and ekind == 'rect' or kind == ekind or (kind == 'circle' and ekind == 'circle'):
            if w is not None and axis and (abs(w - ew) > WTOL or abs(h - eh) > WTOL):
                diffs.append(dict(type='size', what=e['ident'], eagle=[ekind, r3(ew), r3(eh)], kicad=[kind, r3(w), r3(h)],
                                  **loc(e['pos'])))
            else:
                matched += 1
        else:
            diffs.append(dict(type='shape', what=e['ident'], eagle=[ekind, r3(ew), r3(eh), e['angle']],
                              kicad=[kind, w and r3(w), h and r3(h), apertures[flashes[best[1]]['ap']]['shape']],
                              **loc(e['pos'])))
    for i, f in enumerate(flashes):
        if i not in used:
            kind, w, h = aperture_dims(apertures[f['ap']])
            diffs.append(dict(type='extra_in_kicad', what=f['attrs'].get('.P', apertures[f['ap']]['function']),
                              kicad=[kind, w and r3(w), h and r3(h)], **loc(f['pos'])))
    return dict(layer=label, expected=len(expected), kicad_flashes=len(flashes), matched=matched, differences=diffs)


def seg_key(p1, p2):
    a = (round(p1[0], 3), round(p1[1], 3))
    b = (round(p2[0], 3), round(p2[1], 3))
    return tuple(sorted([a, b]))


def near(a, b, tol=TOL):
    return math.hypot(a[0] - b[0], a[1] - b[1]) <= tol


def match_draws(expected, draws, apertures, label, ignore_zero=False):
    """expected: dict(p1,p2,width,center or None, ident). Draws with circular apertures."""
    pool = defaultdict(list)
    for i, d in enumerate(draws):
        pool[seg_key(d['p1'], d['p2'])].append(i)
    used, diffs, matched = set(), [], 0
    loose = []
    for e in expected:
        k = seg_key(e['p1'], e['p2'])
        cands = [i for i in pool.get(k, []) if i not in used]
        if not cands:
            loose.append(e)
            continue
        hit = None
        for i in cands:
            d = draws[i]
            w = apertures[d['ap']]['params'][0]
            if abs(w - e['width']) <= WTOL and ((d['center'] is None) == (e['center'] is None)) and \
                    (e['center'] is None or near(d['center'], e['center'], 0.01)):
                hit = i
                break
        if hit is None:
            d = draws[cands[0]]
            used.add(cands[0])
            diffs.append(dict(type='width_or_arc', what=e['ident'], eagle_width=r3(e['width']),
                              kicad_width=r3(apertures[d['ap']]['params'][0]),
                              eagle_arc_centre=e['center'] and [r3(e['center'][0]), r3(e['center'][1])],
                              kicad_arc_centre=d['center'] and [r3(d['center'][0]), r3(d['center'][1])],
                              **loc(e['p1'])))
            continue
        used.add(hit)
        matched += 1
    # second pass: tolerance-based for rounding at 3 decimals
    for e in loose:
        hit = None
        for i, d in enumerate(draws):
            if i in used:
                continue
            if ((near(d['p1'], e['p1']) and near(d['p2'], e['p2'])) or (near(d['p1'], e['p2']) and near(d['p2'], e['p1']))) \
                    and abs(apertures[d['ap']]['params'][0] - e['width']) <= WTOL:
                hit = i
                break
        if hit is not None:
            used.add(hit)
            matched += 1
        else:
            zero = near(e['p1'], e['p2'], 1e-6)
            diffs.append(dict(type='missing_in_kicad' + ('_zero_length' if zero else ''), what=e['ident'],
                              width=r3(e['width']), p2=[r3(e['p2'][0]), r3(e['p2'][1])],
                              arc=e['center'] is not None, **loc(e['p1'])))
    for i, d in enumerate(draws):
        if i not in used:
            diffs.append(dict(type='extra_in_kicad', width=r3(apertures[d['ap']]['params'][0]),
                              p2=[r3(d['p2'][0]), r3(d['p2'][1])], net=d['attrs'].get('.N'),
                              arc=d['center'] is not None, **loc(d['p1'])))
    return dict(layer=label, expected=len(expected), kicad_draws=len(draws), matched=matched, differences=diffs)


def wire_expect(B, layers, kinds=('signal', 'plain', 'package')):
    out = []
    for w in B.wires:
        if w['layer'] not in layers:
            continue
        src = 'signal' if w['signal'] else ('package' if w['element'] else 'plain')
        if src not in kinds:
            continue
        c = None
        if w['curve']:
            cx, cy, _ = eagle_model.arc_center(*w['p1'], *w['p2'], w['curve'])
            c = (cx, cy)
        out.append(dict(p1=w['p1'], p2=w['p2'], width=w['width'], center=c,
                        ident=f"{src}:{w['signal'] or w['element'] or ''} L{w['layer']}"))
    return out


def pad_expect(B, copper_layer, mask=False, paste=False):
    """Expected flashes for a side ('top'/'bottom')."""
    out = []
    eag_layer = 1 if copper_layer == 'top' else 16
    if not paste:
        for p in B.pads:
            kind, w, h, a = B.pad_geometry(p)
            if mask:
                if not p['stop']:
                    continue
                f = B.stop_frame(min(w, h))
                w, h = w + 2 * f, h + 2 * f
            out.append(dict(kind=kind, w=w, h=h, angle=a, pos=p['pos'], ident=f"pad {p['element']}.{p['name']}"))
        if not mask:
            for v in B.vias:
                d = B.via_diameter(v['drill'], v['lib_diameter'])
                out.append(dict(kind='circle', w=d, h=d, angle=0, pos=v['pos'], ident=f"via {v['signal']}"))
    for s in B.smds:
        if s['layer'] != eag_layer:
            continue
        w, h = s['dx'], s['dy']
        if mask:
            if not s['stop']:
                continue
            f = B.stop_frame(min(w, h))
            w, h = w + 2 * f, h + 2 * f
        if paste and not s['cream']:
            continue
        out.append(dict(kind='rect', w=w, h=h, angle=s['angle'], pos=s['pos'], ident=f"smd {s['element']}.{s['name']}"))
    return out


def summarize(res):
    c = Counter(d['type'] for d in res['differences'])
    return dict(layer=res['layer'], expected=res['expected'], matched=res['matched'],
                kicad_objects=res.get('kicad_flashes', res.get('kicad_draws')), difference_counts=dict(c))


def run(gdir, extract):
    global KTEXTS, ZONES
    import zones
    KTEXTS = {b: v['texts'] for b, v in extract.items()}
    ZONES = zones.run({b: v['zones'] for b, v in extract.items()})
    report = {}
    for b in ('mainboard', 'ioboard'):
        B = eagle_model.Board(EAGLE + b + '.brd')
        g = {k: gerber.Gerber(f'{gdir}/{b}/{b}-{k}.gbr') for k in
             ('F_Cu', 'B_Cu', 'F_Mask', 'B_Mask', 'F_Paste', 'B_Paste', 'F_Silkscreen', 'B_Silkscreen', 'Edge_Cuts')}
        res = {}
        # drills
        k = excellon.read(f'{gdir}/{b}/{b}-PTH.drl')
        kn = excellon.read(f'{gdir}/{b}/{b}-NPTH.drl')
        e = [('pad', p['element'] + '.' + p['name'], p['pos'], p['drill']) for p in B.pads] + \
            [('via', v['signal'], v['pos'], v['drill']) for v in B.vias]
        en = [('hole', h['element'], h['pos'], h['drill']) for h in B.holes]
        uE, uK, sz = drills.match(e, k)
        uEn, uKn, szn = drills.match(en, kn)
        res['drills'] = dict(eagle_plated=len(e), kicad_plated=len(k), eagle_nonplated=len(en), kicad_nonplated=len(kn),
                             unmatched_eagle=uE + uEn, unmatched_kicad=uK + uKn, size_differences=sz + szn,
                             tool_sizes_kicad=sorted({h['drill'] for h in k + kn}),
                             tool_sizes_eagle=sorted({round(x[3], 4) for x in e + en}),
                             max_position_error_mm=r3(max(min(math.hypot(h['pos'][0] - x[2][0], h['pos'][1] - x[2][1])
                                                             for h in k + kn) for x in e + en)))
        # copper
        for side, gl, el in (('top', 'F_Cu', 1), ('bottom', 'B_Cu', 16)):
            G = g[gl]
            fl = [f for f in G.flashes]
            res[gl + ' pads/vias'] = match_flashes(pad_expect(B, side), fl, G.apertures, gl + ' flashes')
            exp = wire_expect(B, {el, 17 if el == 1 else 18})
            res[gl + ' tracks'] = match_draws(exp, G.draws, G.apertures, gl + ' draws')
            res[gl + ' fills'] = dict(layer=gl + ' regions', kicad_regions=len(G.regions),
                                      eagle_polygons=[dict(signal=p['signal'], vertices=len(p['verts']), width=p['width'],
                                                           isolate=p['isolate'], spacing=p['spacing'], orphans=p['orphans'],
                                                           thermals=p['thermals'], rank=p['rank'], pour=p['pour'])
                                                      for p in B.polygons if p['layer'] == el])
        for side, gl in (('top', 'F_Mask'), ('bottom', 'B_Mask')):
            G = g[gl]
            exp = pad_expect(B, side, mask=True)
            for h in B.holes:
                d = h['drill'] + 2 * B.stop_frame(h['drill'])
                exp.append(dict(kind='circle', w=d, h=d, angle=0, pos=h['pos'], ident=f"hole {h['element']}"))
            res[gl] = match_flashes(exp, G.flashes, G.apertures, gl)
            res[gl]['kicad_draws'] = len(G.draws)
            res[gl]['kicad_regions'] = len(G.regions)
            res[gl]['eagle_stop_layer_objects'] = sum(1 for w in B.wires if w['layer'] in (29, 30)) + \
                sum(1 for r in B.rects if r['layer'] in (29, 30)) + sum(1 for c in B.circles if c['layer'] in (29, 30))
        for side, gl in (('top', 'F_Paste'), ('bottom', 'B_Paste')):
            G = g[gl]
            res[gl] = match_flashes(pad_expect(B, side, paste=True), G.flashes, G.apertures, gl)
        # outline
        exp = wire_expect(B, {20}, kinds=('plain', 'package'))
        res['Edge_Cuts'] = match_draws(exp, g['Edge_Cuts'].draws, g['Edge_Cuts'].apertures, 'Edge_Cuts')
        res['Edge_Cuts']['eagle_dimension_circles'] = [dict(pos=c['pos'], r=c['radius']) for c in B.circles if c['layer'] == 20]
        # silkscreen (Eagle CAM silk = tPlace+tNames / bPlace+bNames)
        import silk
        for gl, pl, nl, kl in (('F_Silkscreen', 21, 25, 'F.Silkscreen'), ('B_Silkscreen', 22, 26, 'B.Silkscreen')):
            res[gl] = silk.check(B, g[gl], pl, nl, gl, KTEXTS[b], kl)
        # copper pours
        res['F_Cu fills']['polygon_vs_zone'] = ZONES[b]['polygons']
        res['F_Cu fills']['board_min_clearance_kicad'] = ZONES[b]['board_min_clearance_kicad']
        res['F_Cu fills']['eagle_mdWireWire'] = ZONES[b]['eagle_mdWireWire']
        report[b] = res
    return report


def match_rects(rects, regions, label):
    used, diffs, matched = set(), [], 0
    rc = []
    for r in regions:
        pts = gerber.contour_points(r['contours'][0])
        rc.append(pts)
    for r in rects:
        cx = sum(p[0] for p in r['corners']) / 4
        cy = sum(p[1] for p in r['corners']) / 4
        hit = None
        for i, pts in enumerate(rc):
            if i in used:
                continue
            if all(any(near(c, q, 0.003) for q in pts) for c in r['corners']):
                hit = i
                break
        if hit is None:
            diffs.append(dict(type='missing_in_kicad', what=f"rect {r['element']}", **loc((cx, cy))))
        else:
            used.add(hit)
            matched += 1
    for i, pts in enumerate(rc):
        if i not in used:
            cx = sum(p[0] for p in pts) / len(pts)
            cy = sum(p[1] for p in pts) / len(pts)
            diffs.append(dict(type='extra_in_kicad', vertices=len(pts), **loc((cx, cy))))
    return dict(layer=label + ' filled rectangles', expected=len(rects), kicad_regions=len(regions), matched=matched,
                differences=diffs)


if __name__ == '__main__':
    rep = run(sys.argv[1], json.load(open(sys.argv[3])))
    json.dump(rep, open(sys.argv[2], 'w'), indent=1, default=lambda o: list(o) if isinstance(o, tuple) else str(o))
    for b, res in rep.items():
        print('==', b)
        d = res['drills']
        print('  drills', {k: (len(v) if isinstance(v, list) else v) for k, v in d.items() if 'tool' not in k})
        for k, v in res.items():
            if k == 'drills':
                continue
            if 'Silkscreen' in k:
                print(' ', k, {kk: (vv.get('matched'), vv.get('eagle', vv.get('expected'))) if isinstance(vv, dict) and 'matched' in vv else (len(vv) if isinstance(vv, list) else (vv if not isinstance(vv, dict) else {a: (len(b_) if isinstance(b_, list) else b_) for a, b_ in vv.items()})) for kk, vv in v.items()})
                continue
            if 'matched' in v:
                print(' ', k, summarize(v))
            else:
                print(' ', k, {kk: (vv if not isinstance(vv, list) else len(vv)) for kk, vv in v.items()})
