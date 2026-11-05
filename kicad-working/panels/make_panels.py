#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Write the main and rear panels as KiCad boards, to be made as FR-4 PCBs.

Holes and cuts come from the original DXF geometry in
../visualization/blender-case-revision-7/panels/original-panels.json. Wording comes from the label map
in ../visualization/blender-case-revision-7/source-review/original-photo-label-map.json; label positions
are set here from the features they name. Every change from the DXF is in WIDER_HOLES and WIDER_CUTS, and
README.md gives the reason for each.

Usage: python3 -I make_panels.py
"""
import json
import math
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'visualization/blender-case-revision-7'
GEOMETRY = json.loads((SOURCE / 'panels/original-panels.json').read_text())
WORDS = {row['id']: row['text'] for row in json.loads((SOURCE / 'source-review/original-photo-label-map.json').read_text())['labels']}
NS = uuid.UUID('2f9a6a0e-7b43-4f0e-8a51-3d3f6c1b7e21')
LIB = 'x0xb0x-panel'
ORIGIN = dict(mainpanel=(20.0, 190.0), iopanel=(20.0, 90.0))
REVISION = 1

# Drills stop below this size; JLCPCB routes anything larger, so those holes go on Edge.Cuts
MAX_DRILL = 6.3
CUT_RADIUS = 0.5
BIG, MEDIUM, SMALL = 2.2, 2.0, 1.5
LINE = {BIG: 0.22, MEDIUM: 0.2, SMALL: 0.17}

# Diameters different from the DXF, by reference. Reasons: README.md
WIDER_HOLES = {**{f'LED{n}': 5.4 for n in range(1, 41)}, 'S1': 6.6, 'CV0': 6.8, 'GATE0': 6.8}
# Growth of each side of a cut (left, right, bottom, top). Reasons: README.md
WIDER_CUTS = {**{f'S{n}': (0.1, 0.1, 0.1, 0.1) for n in range(5, 28)}, 'USB0': (0.3, 0.3, 0.4, 0.3), 'POWER0': (0.3, 0.3, 0.4, 0.3)}

# Unconnected copper on both faces, because a fab may refuse a board with none. Each ring sits under a screw
# head or a nut: main panel, all seven mounts; rear panel, the three 1/4 in jacks. (radius, width), mm
RINGS = dict(mainpanel=dict(radius=2.3, width=0.5, refs=None), iopanel=dict(radius=6.55, width=0.5, refs=('HEADPHONE0', 'MIXIN0', 'MIXOUT0')))
# Rear jacks, in the order of the top-edge labels of the main panel
PORTS = ('DIN4', 'MIXIN0', 'DIN3', 'DIN2', 'DIN1', 'MIXOUT0', 'USB0', 'CV0', 'GATE0', 'HEADPHONE0', 'POWER0')


def uid(*parts):
    return str(uuid.uuid5(NS, '/'.join(map(str, parts))))


def fmt(v):
    return f'{v:.4f}'.rstrip('0').rstrip('.')


class Board:
    def __init__(self, name):
        self.name = name
        self.ox, self.oy = ORIGIN[name]
        self.items = []
        self.count = 0

    def at(self, x, y):
        return fmt(self.ox + x), fmt(self.oy - y)

    def next(self, *tag):
        self.count += 1
        return uid(self.name, self.count, *tag)

    def text(self, x, y, s, size, justify=None, layer='F.SilkS', mirror=False):
        X, Y = self.at(x, y)
        flags = ' '.join(filter(None, (justify, 'mirror' if mirror else None)))
        just = f' (justify {flags})' if flags else ''
        thick = LINE.get(size, 0.18)
        self.items.append(f'\t(gr_text "{s}" (at {X} {Y} 0) (layer "{layer}") (uuid "{self.next(s)}") '
                          f'(effects (font (size {size} {size}) (thickness {thick})){just}))')

    def line(self, a, b, layer, width):
        ax, ay = self.at(*a)
        bx, by = self.at(*b)
        self.items.append(f'\t(gr_line (start {ax} {ay}) (end {bx} {by}) (stroke (width {width}) (type solid)) (layer "{layer}") (uuid "{self.next()}"))')

    def arc(self, a, mid, b):
        ax, ay = self.at(*a)
        mx, my = self.at(*mid)
        bx, by = self.at(*b)
        self.items.append(f'\t(gr_arc (start {ax} {ay}) (mid {mx} {my}) (end {bx} {by}) (stroke (width 0.05) (type solid)) (layer "Edge.Cuts") (uuid "{self.next()}"))')

    def circle(self, x, y, r, layer, width=0.05):
        cx, cy = self.at(x, y)
        ex, ey = self.at(x + r, y)
        self.items.append(f'\t(gr_circle (center {cx} {cy}) (end {ex} {ey}) (stroke (width {width}) (type solid)) (fill no) (layer "{layer}") (uuid "{self.next()}"))')

    def rounded_cut(self, x0, y0, x1, y1, r=CUT_RADIUS):
        k = r * (1 - math.sqrt(0.5))
        self.line((x0 + r, y0), (x1 - r, y0), 'Edge.Cuts', 0.05)
        self.arc((x1 - r, y0), (x1 - k, y0 + k), (x1, y0 + r))
        self.line((x1, y0 + r), (x1, y1 - r), 'Edge.Cuts', 0.05)
        self.arc((x1, y1 - r), (x1 - k, y1 - k), (x1 - r, y1))
        self.line((x1 - r, y1), (x0 + r, y1), 'Edge.Cuts', 0.05)
        self.arc((x0 + r, y1), (x0 + k, y1 - k), (x0, y1 - r))
        self.line((x0, y1 - r), (x0, y0 + r), 'Edge.Cuts', 0.05)
        self.arc((x0, y0 + r), (x0 + k, y0 + k), (x0 + r, y0))

    def outline(self, w, h):
        ax, ay = self.at(0, h)
        bx, by = self.at(w, 0)
        self.items.append(f'\t(gr_rect (start {ax} {ay}) (end {bx} {by}) (stroke (width 0.05) (type solid)) (fill no) (layer "Edge.Cuts") (uuid "{self.next()}"))')

    def drilled(self, ref, x, y, d):
        X, Y = self.at(x, y)
        self.items.append(footprint(d, at=(X, Y), ref=ref, tag=(self.name, ref)))


def footprint(d, at=None, ref='REF**', tag=()):
    name = f'NPTH_{d:g}'
    on_board = at is not None
    L = [f'\t(footprint "{LIB}:{name}"' if on_board else f'(footprint "{name}"']
    if not on_board:
        L += ['\t(version 20260206)', '\t(generator "x0xb0x-make-panels")', '\t(generator_version "10.0")']
    L.append('\t\t(layer "F.Cu")')
    L.append(f'\t\t(descr "Plain drilled hole of {d:g} mm in a panel")')
    if on_board:
        L.append(f'\t\t(uuid "{uid(*tag)}")')
        L.append(f'\t\t(at {at[0]} {at[1]})')
    L.append(f'\t\t(property "Reference" "{ref}" (at 0 {fmt(-d / 2 - 1)} 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))')
    L.append(f'\t\t(property "Value" "{name}" (at 0 {fmt(d / 2 + 1)} 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))')
    L.append('\t\t(attr exclude_from_pos_files exclude_from_bom)')
    pad_tag = f' (uuid "{uid(*tag, "pad")}")' if on_board else ''
    L.append(f'\t\t(pad "" np_thru_hole circle (at 0 0) (size {d:g} {d:g}) (drill {d:g}) (layers "*.Cu" "*.Mask"){pad_tag})')
    L.append('\t)' if on_board else ')')
    return '\n'.join(L)


def features(panel):
    """Centres of holes and cuts of one DXF panel, by board reference."""
    out = {c['board_reference']: tuple(c['center_mm']) for c in panel['circles']}
    for r in panel['rectangular_cutouts']:
        (x0, y0), (x1, y1) = r['bounds_mm']
        out[r['board_reference']] = ((x0 + x1) / 2, (y0 + y1) / 2)
    return out


def holes_and_cuts(b, panel):
    for c in panel['circles']:
        ref = c['board_reference']
        x, y = c['center_mm']
        d = WIDER_HOLES.get(ref, round(c['radius_mm'] * 2, 4))
        if d < MAX_DRILL:
            b.drilled(ref, x, y, d)
        else:
            b.circle(x, y, d / 2, 'Edge.Cuts')
    for r in panel['rectangular_cutouts']:
        (x0, y0), (x1, y1) = r['bounds_mm']
        left, right, bottom, top = WIDER_CUTS.get(r['board_reference'], (0, 0, 0, 0))
        b.rounded_cut(x0 - left, y0 - bottom, x1 + right, y1 + top)


def rings(b, panel):
    spec = RINGS[b.name]
    for c in panel['circles']:
        ref = c['board_reference']
        if ref in (spec['refs'] or ()) or (spec['refs'] is None and c['function'] == 'mount'):
            for layer in ('F.Cu', 'B.Cu'):
                b.circle(*c['center_mm'], spec['radius'], layer, spec['width'])


def main_panel_labels(b, at):
    for ref, word in (('VR2', 'TUNE'), ('VR3', 'CUTOFF'), ('VR4', 'RESONANCE'), ('VR5', 'ENV-MOD'), ('VR6', 'DECAY'), ('VR7', 'ACCENT')):
        b.text(at[ref][0], at[ref][1] - 10.7, WORDS[f'{ref}-{word}'], BIG)
    for ref, word in (('S2', 'TEMPO'), ('VR8', 'VOLUME')):
        b.text(at[ref][0], at[ref][1] - 11.2, WORDS[f'{ref}-{word}'], BIG)
    b.text(at['S1'][0], at['S1'][1] + 5.8, WORDS['S1-SAW'], BIG)
    b.text(at['S1'][0], at['S1'][1] - 5.8, WORDS['S1-SQR'], BIG)
    # Bank selector: sixteen numbers on a ring, one at the top, clockwise
    for n in range(1, 17):
        a = math.radians(22.5 * (n - 1))
        b.text(at['S3'][0] + 15.3 * math.sin(a), at['S3'][1] + 15.3 * math.cos(a), WORDS[f'S3-position-{n}'], SMALL)
    # Mode selector: the first and ninth above and below it, the rest in two columns
    x, y = at['S4']
    b.text(x, y + 16, WORDS['S4-mode-1'], SMALL)
    b.text(x, y - 16, WORDS['S4-mode-9'], SMALL)
    for row, n in enumerate(range(2, 9)):
        b.text(x + 15.5, y + (3 - row) * 3.9, WORDS[f'S4-mode-{n}'], SMALL, justify='left')
    for row, n in enumerate(range(10, 17)):
        b.text(x - 15.5, y + (row - 3) * 3.9, WORDS[f'S4-mode-{n}'], SMALL, justify='right')
    # Step numbers under the sixteen sequence LEDs, then the line under them
    for n in range(1, 17):
        led = at[f'LED{n + 1}']
        b.text(led[0], led[1] - 4.46, WORDS[f'step-LED-{n}'], MEDIUM)
    b.line((12.2, 74.7), (220.6, 74.7), 'F.SilkS', 0.2)
    # Keyboard notes above their LEDs
    for n in (*range(20, 25), *range(30, 38)):
        led = at[f'LED{n}']
        b.text(led[0], led[1] + 4.5, WORDS[f'LED{n}-note'], MEDIUM)
    # Button names under the cuts: the wide buttons, then the tall ones
    for n in (5, 6, 14, 15, 16):
        b.text(at[f'S{n}'][0], at[f'S{n}'][1] - 7.49, WORDS[f'S{n}-function'], MEDIUM)
    for n in (12, 13, 25, 26, 27):
        b.text(at[f'S{n}'][0], at[f'S{n}'][1] - 9.3, WORDS[f'S{n}-function'], MEDIUM)
    for n in range(17, 25):
        b.text(at[f'S{n}'][0], at[f'S{n}'][1] - 9.3, WORDS[f'S{n}-step'], MEDIUM)
    # Rear port names along the top edge, each straight in front of its jack
    rear = features(GEOMETRY['iopanel'])
    middle = (GEOMETRY['mainpanel']['outer_profile']['bounds_mm'][1][0] + GEOMETRY['iopanel']['outer_profile']['bounds_mm'][1][0]) / 2
    for n, ref in enumerate(PORTS, 1):
        b.text(middle - rear[ref][0], 159.6, WORDS[f'top-port-label-{n}'], MEDIUM)


def rear_panel_labels(b, at):
    for n, ref in enumerate(PORTS, 1):
        b.text(at[ref][0], 28.5, WORDS[f'top-port-label-{n}'], MEDIUM)


LAYERS = '''\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t)'''

STACKUP = '''\t(setup
\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "White"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color "Black") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "core") (color "FR4 natural") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color "Black") (thickness 0.01))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
\t\t\t(copper_finish "HAL lead-free")
\t\t\t(dielectric_constraints no)
\t\t)
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(tenting (front yes) (back yes))
\t)'''


def pcb(b):
    return '\n'.join(['(kicad_pcb', '\t(version 20260206)', '\t(generator "x0xb0x-make-panels")', '\t(generator_version "10.0")',
                      '\t(general (thickness 1.6) (legacy_teardrops no))', '\t(paper "A3")', LAYERS, STACKUP,
                      '\t(net 0 "")', *b.items, ')']) + '\n'


def pro(name):
    return json.dumps({
        'board': {'design_settings': {
            'defaults': {'silk_text_size_h': MEDIUM, 'silk_text_size_v': MEDIUM, 'silk_text_thickness': LINE[MEDIUM]},
            'rules': {'min_clearance': 0.15, 'min_connection': 0.0, 'min_copper_edge_clearance': 0.3, 'min_hole_clearance': 0.25,
                      'min_hole_to_hole': 0.25, 'min_silk_clearance': 0.0, 'min_text_height': 1.0, 'min_text_thickness': 0.15,
                      'min_through_hole_diameter': 0.3, 'min_track_width': 0.15, 'min_via_annular_width': 0.13, 'min_via_diameter': 0.5,
                      'solder_mask_to_copper_clearance': 0.0}}},
        'meta': {'filename': f'{name}.kicad_pro', 'version': 3},
        'net_settings': {'classes': [{'name': 'Default', 'clearance': 0.2, 'track_width': 0.25, 'via_diameter': 0.6, 'via_drill': 0.3,
                                      'microvia_diameter': 0.3, 'microvia_drill': 0.1, 'diff_pair_gap': 0.25, 'diff_pair_via_gap': 0.25,
                                      'diff_pair_width': 0.2, 'bus_width': 12, 'wire_width': 6, 'line_style': 0, 'priority': -1,
                                      'schematic_color': 'rgba(0, 0, 0, 0.000)', 'pcb_color': 'rgba(0, 0, 0, 0.000)'}], 'meta': {'version': 5}},
        'sheets': [[uid(name, 'sheet'), 'Root']],
    }, indent=2) + '\n'


def build(name, labels, title, credit_at):
    panel = GEOMETRY[name]
    (_, _), (w, h) = panel['outer_profile']['bounds_mm']
    b = Board(name)
    b.outline(w, h)
    holes_and_cuts(b, panel)
    rings(b, panel)
    labels(b, features(panel))
    x, y = credit_at
    b.text(x, y + 3, f'{title} - FR-4 panel revision {REVISION}', SMALL, layer='B.SilkS', mirror=True)
    b.text(x, y, 'Panel drawing (c) Limor Fried and Adafruit Industries, MIT license', SMALL, layer='B.SilkS', mirror=True)
    d = HERE / name
    d.mkdir(exist_ok=True)
    (d / f'{name}.kicad_pcb').write_text(pcb(b))
    (d / f'{name}.kicad_pro').write_text(pro(name))
    (d / 'fp-lib-table').write_text(f'(fp_lib_table\n\t(version 7)\n\t(lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/../{LIB}.pretty")(options "")(descr "Panel holes"))\n)\n')


def library():
    d = HERE / f'{LIB}.pretty'
    d.mkdir(exist_ok=True)
    sizes = set()
    for panel in GEOMETRY.values():
        for c in panel['circles']:
            size = WIDER_HOLES.get(c['board_reference'], round(c['radius_mm'] * 2, 4))
            if size < MAX_DRILL:
                sizes.add(size)
    for size in sorted(sizes):
        (d / f'NPTH_{size:g}.kicad_mod').write_text(footprint(size) + '\n')


def main():
    library()
    build('mainpanel', main_panel_labels, 'x0xb0x main panel', (116.205, 88.0))
    build('iopanel', rear_panel_labels, 'x0xb0x rear panel', (108.966, 40.0))


if __name__ == '__main__':
    main()
