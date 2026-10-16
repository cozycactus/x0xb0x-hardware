# SPDX-License-Identifier: CC0-1.0
"""Silkscreen: Eagle tPlace/tNames (bPlace/bNames) vs KiCad silkscreen Gerber.

Non-text geometry is matched primitive by primitive. Text is compared as
strings and anchors (Eagle text records vs KiCad text objects), and every
remaining Gerber stroke must fall inside a plotted KiCad text box.
"""
import math
import gerber
from compare import match_draws, wire_expect, match_rects, near, loc, r3


def check(B, G, pl, nl, label, ktexts, klayer):
    exp = wire_expect(B, {pl, nl}, kinds=('plain', 'package'))
    lines = match_draws(exp, G.draws, G.apertures, label + ' lines/arcs')
    other = [d for d in lines['differences'] if d['type'] != 'extra_in_kicad']
    extra = [d for d in lines['differences'] if d['type'] == 'extra_in_kicad']
    ex = [dict(p1=tuple(d['gerber_xy_mm']), p2=tuple(d['p2']), width=d['width'], arc=d['arc']) for d in extra]
    # circles: KiCad plots a circle as two 180-degree arcs
    arcs = [d for d in G.draws if d['center'] is not None]
    used, circ_missing, circ_matched = set(), [], 0
    for c in (c for c in B.circles if c['layer'] in (pl, nl)):
        rad, wid = (c['radius'], c['width']) if c['width'] > 0 else (c['radius'] / 2, c['radius'])
        hits = [i for i, d in enumerate(arcs) if i not in used and near(d['center'], c['pos'], 0.002)
                and abs(math.hypot(d['p1'][0] - d['center'][0], d['p1'][1] - d['center'][1]) - rad) < 0.002
                and abs(G.apertures[d['ap']]['params'][0] - wid) < 0.0011]
        if len(hits) >= 2:
            used.update(hits[:2])
            circ_matched += 1
        else:
            circ_missing.append(dict(what=f"circle {c['element']}", radius=c['radius'], width=c['width'], **loc(c['pos'])))
    usedkeys = {(round(arcs[i]['p1'][0], 4), round(arcs[i]['p1'][1], 4), round(arcs[i]['p2'][0], 4), round(arcs[i]['p2'][1], 4)) for i in used}
    ex = [d for d in ex if not (d['arc'] and (round(d['p1'][0], 4), round(d['p1'][1], 4), round(d['p2'][0], 4), round(d['p2'][1], 4)) in usedkeys)]
    # filled rectangles and polygons
    rects = [r for r in B.rects if r['layer'] in (pl, nl)]
    polys = [dict(corners=[v[0] for v in p['verts']], element=p['element']) for p in B.polygons if p['layer'] in (pl, nl)]
    rr = match_rects(rects + polys, G.regions, label)
    # remaining strokes must be KiCad text glyphs
    kt = [t for t in ktexts if t['layer'] == klayer]
    def in_box(p, bx, m=0.15):
        return bx[0] - m <= p[0] <= bx[2] + m and bx[1] - m <= p[1] <= bx[3] + m
    stray = [d for d in ex if not any(in_box(d['p1'], t['bbox']) and in_box(d['p2'], t['bbox']) for t in kt)]
    # text records
    et = [t for t in B.texts if t['layer'] in (pl, nl) and t['text']]
    res_t = dict(same_anchor=0, moved=[], missing_in_kicad=[], extra_in_kicad=[])
    pool = list(range(len(kt)))
    for t in et:
        cands = [i for i in pool if kt[i]['text'] == t['text'] and (t['element'] is None or kt[i]['ref'] in (t['element'], t['element'] + '0') or kt[i]['kind'] == 'gr_text')]
        if not cands:
            res_t['missing_in_kicad'].append(dict(text=t['text'], element=t['element'], eagle_layer=t['layer'], **loc(t['pos'])))
            continue
        i = min(cands, key=lambda i: math.hypot(kt[i]['pos'][0] - t['pos'][0], kt[i]['pos'][1] - t['pos'][1]))
        pool.remove(i)
        d = math.hypot(kt[i]['pos'][0] - t['pos'][0], kt[i]['pos'][1] - t['pos'][1])
        if d < 0.01:
            res_t['same_anchor'] += 1
        else:
            res_t['moved'].append(dict(text=t['text'], element=t['element'], smashed=bool(t.get('smashed')),
                                       eagle_anchor=[r3(t['pos'][0]), r3(t['pos'][1])], eagle_angle=t['angle'],
                                       kicad_anchor=[r3(kt[i]['pos'][0]), r3(kt[i]['pos'][1])], kicad_angle=kt[i]['angle'],
                                       offset_mm=r3(d)))
    for i in pool:
        res_t['extra_in_kicad'].append(dict(text=kt[i]['text'], ref=kt[i]['ref'], kind=kt[i]['kind'],
                                            gerber_xy_mm=[r3(v) for v in kt[i]['pos']]))
    return dict(layer=label,
                lines_arcs=dict(eagle=len(exp), matched=lines['matched'], differences=other),
                circles=dict(eagle=sum(1 for c in B.circles if c['layer'] in (pl, nl)), matched=circ_matched, missing_in_kicad=circ_missing),
                filled_shapes=dict(expected=rr['expected'], matched=rr['matched'], differences=rr['differences']),
                text_strokes_in_gerber=len(ex) - len(stray), strokes_not_inside_any_text=[dict(p1=list(map(r3, d['p1'])), p2=list(map(r3, d['p2'])), width=d['width']) for d in stray],
                texts=dict(eagle=len(et), kicad=len(kt), same_anchor=res_t['same_anchor'], moved_count=len(res_t['moved']),
                           moved_smashed_names=sum(1 for m in res_t['moved'] if m['smashed']), moved=res_t['moved'],
                           missing_in_kicad=res_t['missing_in_kicad'], extra_in_kicad=res_t['extra_in_kicad']))
