# SPDX-License-Identifier: CC0-1.0
"""Eagle polygon outlines/settings vs KiCad zones (outline offset by width/2)."""
import json, math, sys
sys.path.insert(0, '.')
import eagle_model


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.hypot(a[0] + t * dx - p[0], a[1] + t * dy - p[1])


def poly_dist(p, poly):
    return min(seg_dist(p, poly[i - 1], poly[i]) for i in range(len(poly)))


def area(poly):
    return abs(sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))) / 2


def eagle_outline(p, step=2.0):
    pts = []
    vs = p['verts']
    for i, (v, curve) in enumerate(vs):
        nxt = vs[(i + 1) % len(vs)][0]
        pts.append(v)
        if curve:
            cx, cy, r = eagle_model.arc_center(v[0], v[1], nxt[0], nxt[1], curve)
            a0 = math.atan2(v[1] - cy, v[0] - cx)
            n = max(2, int(abs(curve) / step))
            for k in range(1, n):
                a = a0 + math.radians(curve) * k / n
                pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def run(K):
    from compare import EAGLE
    out = {}
    for b in ('mainboard', 'ioboard'):
        B = eagle_model.Board(EAGLE + f'{b}.brd')
        rows = []
        for p in [p for p in B.polygons if p['layer'] in (1, 16)]:
            eo = eagle_outline(p)
            best = None
            for zi, z in enumerate(K[b]['zones']):
                ko = z['outline'][0]
                dmax = max(poly_dist(v, ko) for v in eo)
                if best is None or dmax < best[0]:
                    best = (dmax, zi, z)
            dmax, zi, z = best
            ko = z['outline'][0]
            back = max(poly_dist(q, eo) for q in ko)
            rows.append(dict(eagle=dict(signal=p['signal'], layer=p['layer'], vertices=len(p['verts']),
                                        arc_vertices=sum(1 for v in p['verts'] if v[1]), width=p['width'],
                                        isolate=p['isolate'], orphans=p['orphans'], thermals=p['thermals'],
                                        rank=p['rank'], pour=p['pour'], spacing=p['spacing'],
                                        centreline_area_mm2=round(area(eo), 1)),
                             kicad=dict(zone_index=zi, net=z['net'], layer=z['layer'], priority=z['priority'],
                                        outline_points=len(ko), outline_area_mm2=round(area(ko), 1),
                                        clearance=z['clearance'], min_width=round(z['min_width'], 4),
                                        thermal_gap=round(z['thermal_gap'], 4), spoke=round(z['spoke'], 4),
                                        island_removal=z['island_mode'], fill_mode=z['fill_mode'],
                                        filled_area_mm2=z['filled_area_mm2']),
                             max_eagle_vertex_to_kicad_outline_mm=round(dmax, 4),
                             max_kicad_point_to_eagle_outline_mm=round(back, 4)))
        out[b] = dict(board_min_clearance_kicad=K[b]['board_clearance'], eagle_mdWireWire=B.rules.get('mdWireWire'),
                      polygons=rows)
    return out


if __name__ == '__main__':
    print(json.dumps(run(json.load(open(sys.argv[1]))), indent=1))
