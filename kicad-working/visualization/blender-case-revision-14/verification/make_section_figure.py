"""Draw the revision 13 / 14 rear-plate section comparison (standard library only).

Inputs are sections-revision-13.json and sections.json from
extract_sections.py and the two seating reports from measure_rear_seating.py.
Each loop of exact plane/triangle segments is chained and filled (even-odd);
open chains are stroked. Text values are read from the measurement files.
Writes ../rear-datum-sections.svg; the PNG is made with
  rsvg-convert -o rear-datum-sections.png rear-datum-sections.svg

Run:  python3 -I make_section_figure.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCALE = 30.0           # px per mm
WIN_Y = (-9.0, 9.5)    # mm relative to plate inner face
WIN_Z = (-10.0, 10.0)  # mm relative to port axis
STYLE = {
    'case': ('#d9d6cf', '#9c988f'),
    'plate': ('#9fb3c8', '#38506a'),
    'pcb': ('#5f9e6e', '#2c5a37'),
    'hardware': ('#4b4b4b', '#222222'),
    'component': ('#c9c9c9', '#7a7a7a'),
    'focus': ('#e3a64a', '#8a5a12'),
    'downloaded': ('#b39ddb', '#5e35b1'),
    'other': ('#e0e0e0', '#9e9e9e'),
}
ORDER = ['case', 'plate', 'pcb', 'component', 'other', 'hardware', 'focus', 'downloaded']


def load(name):
    return json.loads((HERE / name).read_text())


def chains(segments, tol=1e-5):
    key = lambda p: (round(p[0] / tol), round(p[1] / tol))
    adj, pts = {}, {}
    for i, (a, b) in enumerate(segments):
        for p in (a, b):
            pts[key(p)] = p
        adj.setdefault(key(a), []).append((i, key(b)))
        adj.setdefault(key(b), []).append((i, key(a)))
    used, out = set(), []
    for i, (a, b) in enumerate(segments):
        if i in used:
            continue
        used.add(i)
        line = [key(a), key(b)]
        for direction in (0, 1):
            while True:
                tip = line[-1]
                step = next(((j, k) for j, k in adj.get(tip, []) if j not in used), None)
                if step is None:
                    break
                used.add(step[0])
                line.append(step[1])
                if step[1] == line[0]:
                    break
            if line[-1] == line[0] and len(line) > 2:
                break
            line.reverse()
        out.append(([pts[k] for k in line], line[0] == line[-1] and len(line) > 3))
    return out


ZOOM_SCALE = 110.0      # px per mm in detail insets
ZOOM = {  # (y window rel. plate inner face, z window rel. port axis), mm
    'HEADPHONE0': ((-1.1, 1.1), (6.0, 8.2)),
    'DIN1': ((-1.1, 1.1), (7.8, 10.0)),
    'CV0': ((-1.1, 1.1), (3.2, 5.4)),
}


def draw(section, x0, y0, win_y, win_z, scale, focus_ref, stroke_scale=1.0):
    """Draw one clipped section view; return SVG parts, mappers and PCB edge."""
    inner = section['plate_inner_y_mm']
    ax_z = section['axis_world_mm'][2]
    w = (win_y[1] - win_y[0]) * scale
    h = (win_z[1] - win_z[0]) * scale
    X = lambda y: x0 + (y - inner - win_y[0]) * scale
    Y = lambda z: y0 + (win_z[1] - (z - ax_z)) * scale
    clip = f'clip{abs(hash((x0, y0, scale)))}'
    parts = [f'<clipPath id="{clip}"><rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}"/></clipPath>',
             f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" fill="#ffffff" stroke="#bbbbbb"/>',
             f'<g clip-path="url(#{clip})">']
    focus = lambda g: 'focus' if g['name'] == f'IOBOARD/{focus_ref}/mesh' else g['cls']
    pcb_edge = None
    for g in sorted(section['groups'], key=lambda g: ORDER.index(focus(g))):
        cls = focus(g)
        fill, stroke = STYLE[cls]
        if cls == 'pcb':
            edge = max(p[0] for seg in g['segments'] for p in seg)
            pcb_edge = edge if pcb_edge is None else max(pcb_edge, edge)
        closed, opened = [], []
        for loop, is_closed in chains(g['segments']):
            d = 'M' + ' L'.join(f'{X(p[0]):.2f},{Y(p[1]):.2f}' for p in loop)
            (closed if is_closed else opened).append(d + (' Z' if is_closed else ''))
        sw = 0.8 * stroke_scale
        if closed:
            parts.append(f'<path d="{" ".join(closed)}" fill="{fill}" fill-opacity="0.85" '
                         f'fill-rule="evenodd" stroke="{stroke}" stroke-width="{sw}"/>')
        if opened:
            parts.append(f'<path d="{" ".join(opened)}" fill="none" stroke="{stroke}" '
                         f'stroke-width="{sw * 1.6}"/>')
    xi = X(inner)
    parts.append(f'<line x1="{xi:.1f}" y1="{y0:.1f}" x2="{xi:.1f}" y2="{y0 + h:.1f}" stroke="#1565c0" '
                 'stroke-width="1.4" stroke-dasharray="6 4"/>')
    parts.append('</g>')
    return parts, X, Y, w, h, pcb_edge


def cell(section, x0, y0, notes, focus_ref):
    parts, X, Y, w, h, pcb_edge = draw(section, x0, y0, WIN_Y, WIN_Z, SCALE, focus_ref)
    inner = section['plate_inner_y_mm']
    ax_z = section['axis_world_mm'][2]
    xi = X(inner)
    parts.append(f'<text x="{xi + 4:.1f}" y="{y0 + 16:.1f}" font-size="13" fill="#1565c0">plate inner face</text>')
    if pcb_edge is not None:
        xe = X(pcb_edge)
        parts.append(f'<line x1="{xe:.1f}" y1="{y0 + h - 60:.1f}" x2="{xe:.1f}" y2="{y0 + h:.1f}" '
                     'stroke="#2e7d32" stroke-width="1.4" stroke-dasharray="3 3"/>')
        parts.append(f'<text x="{xe - 4:.1f}" y="{y0 + h - 64:.1f}" font-size="13" fill="#2e7d32" '
                     f'text-anchor="end">PCB rear edge ({pcb_edge - inner:+.3f} mm)</text>')
    sx, sy = x0 + 12, y0 + h - 14
    parts.append(f'<line x1="{sx}" y1="{sy}" x2="{sx + 5 * SCALE}" y2="{sy}" stroke="#333" stroke-width="2"/>')
    parts.append(f'<text x="{sx + 2.5 * SCALE}" y="{sy - 5}" font-size="12" text-anchor="middle" fill="#333">5 mm</text>')
    # Detail inset at the plate contact, with its footprint marked on the main view.
    zy, zz = ZOOM[section['reference']]
    bx0, bx1 = X(inner + zy[0]), X(inner + zy[1])
    by0, by1 = Y(ax_z + zz[1]), Y(ax_z + zz[0])
    parts.append(f'<rect x="{bx0:.1f}" y="{by0:.1f}" width="{bx1 - bx0:.1f}" height="{by1 - by0:.1f}" '
                 'fill="none" stroke="#c62828" stroke-width="1.6"/>')
    ix0, iy0 = x0 + w + 18, y0
    inset, IX, IY, iw, ih, _ = draw(section, ix0, iy0, zy, zz, ZOOM_SCALE, focus_ref, stroke_scale=1.4)
    parts += inset
    parts.append(f'<rect x="{ix0:.1f}" y="{iy0:.1f}" width="{iw:.1f}" height="{ih:.1f}" fill="none" '
                 'stroke="#c62828" stroke-width="1.6"/>')
    if pcb_edge is not None and zy[0] <= pcb_edge - inner <= zy[1]:
        xe = IX(pcb_edge)
        parts.append(f'<line x1="{xe:.1f}" y1="{iy0:.1f}" x2="{xe:.1f}" y2="{iy0 + ih:.1f}" '
                     'stroke="#2e7d32" stroke-width="1.2" stroke-dasharray="3 3"/>')
    parts.append(f'<line x1="{ix0 + 10}" y1="{iy0 + ih - 10}" x2="{ix0 + 10 + 0.5 * ZOOM_SCALE}" '
                 f'y2="{iy0 + ih - 10}" stroke="#333" stroke-width="2"/>')
    parts.append(f'<text x="{ix0 + 10 + 0.25 * ZOOM_SCALE}" y="{iy0 + ih - 15}" font-size="12" '
                 'text-anchor="middle" fill="#333">0.5 mm</text>')
    parts.append(f'<text x="{ix0}" y="{iy0 + ih + 18}" font-size="12" fill="#c62828">detail at plate contact</text>')
    parts.append(f'<text x="{x0}" y="{y0 - 12}" font-size="15" font-weight="600" fill="#111">{notes[0]}</text>')
    for i, note in enumerate(notes[1:]):
        parts.append(f'<text x="{x0}" y="{y0 + h + 20 + 17 * i}" font-size="13" fill="#333">{note}</text>')
    return '\n'.join(parts), w + 18 + iw


def legend(x0, y0):
    items = [('plate', 'rear plate'), ('focus', 'sectioned port (native model)'), ('pcb', 'I/O PCB'),
             ('hardware', 'washer / nut'), ('component', 'other component'), ('case', 'case')]
    parts, x = [], x0
    for cls, text in items:
        fill, stroke = STYLE[cls]
        parts.append(f'<rect x="{x}" y="{y0 - 11}" width="14" height="14" fill="{fill}" stroke="{stroke}"/>')
        parts.append(f'<text x="{x + 20}" y="{y0}" font-size="13" fill="#333">{text}</text>')
        x += 34 + 7.2 * len(text)
    return '\n'.join(parts)


def svg(width, height, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" font-family="Helvetica, Arial, sans-serif">\n'
            f'<rect width="100%" height="100%" fill="#fafafa"/>\n{body}\n</svg>\n')


def port_row(data, ref):
    return next(p for p in data['ports'] if p['reference'] == ref)


def main():
    base = load('sections-revision-13.json')
    cand = load('sections.json')
    sb, sc = load('rear-seating-revision-13.json'), load('rear-seating-audit.json')
    h = (WIN_Z[1] - WIN_Z[0]) * SCALE
    margin, row_gap, top = 50, 150, 150
    labels = {'HEADPHONE0': 'NYS216 audio (HEADPHONE0)', 'DIN1': 'SDS-50J DIN (DIN1, drawing-derived)',
              'CV0': 'MJ-3536N (CV0)'}
    body, width = [], 0
    for row, ref in enumerate(['HEADPHONE0', 'DIN1', 'CV0']):
        y0 = top + row * (h + row_gap) + 30
        x0 = margin
        for sec_data, seat, name in [(base, sb, 'Blender 13 — PCB edge on plate inner face'),
                                     (cand, sc, 'Blender 14 — plate on Eagle strip datum')]:
            section = next(s for s in sec_data['sections'] if s['reference'] == ref)
            port = port_row(seat, ref)
            shoulder = port['shoulder_minus_panel_inner_plane_mm']
            vol = port['actual_panel_material_intersection']['volume_mm3']
            word = 'flange front' if ref == 'DIN1' else 'housing shoulder'
            state = (f'{word} {shoulder:.3f} mm inside plate' if shoulder > 0.001 else
                     f'{word} {-shoulder:.3f} mm behind plate' if shoulder < -0.001 else
                     f'{word} on inner face (within 0.001 mm)')
            notes = [f'{labels[ref]} — {name}', state,
                     f'mesh overlap with plate {vol:.3f} mm³ (contact threshold 0.01)',
                     f'mating face beyond plate exterior {port["mating_face_projection_beyond_panel_exterior_mm"]:+.3f} mm']
            part, cw = cell(section, x0, y0, notes, ref)
            body.append(part)
            x0 += cw + margin
        width = max(width, x0)
    head = [f'<text x="{margin}" y="44" font-size="24" font-weight="700" fill="#111">'
            'Rear plate datum: Blender 13 vs Blender 14</text>',
            f'<text x="{margin}" y="72" font-size="14" fill="#444">Exact vertical sections through '
            'each port axis of the saved meshes, frame 1. Revision 14 moves only the I/O board '
            '0.508 mm forward, so the plate inner face lies on the original Eagle strip datum.</text>',
            f'<text x="{margin}" y="92" font-size="14" fill="#444">Case front is left, outside is right. '
            'Nominal illustration geometry; not a physical-fit qualification.</text>',
            legend(margin, 122)]
    height = int(top + 3 * (h + row_gap) + 20)
    (HERE.parent / 'rear-datum-sections.svg').write_text(svg(int(width), height, '\n'.join(head + body)))
    print('figure written')


main()
