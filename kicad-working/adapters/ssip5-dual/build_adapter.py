#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Write the two SSIP5 dual-transistor adapter KiCad projects: common emitter (2SC1583 positions Q12, Q21, Q26) and
common base (2SC2291 position Q22). Stdlib only; the main boards are not touched. Usage: python3 -I build_adapter.py

The board stands on edge on five straight wires, which lap-solder to the long pads along the bottom edge. The chip is
a SOT-363 dual with pins 1 E1, 2 B1, 3 C2, 4 E2, 5 B2, 6 C1 (BCM847BS; onsemi BC847CDW1 has the same arrangement)."""
import json
import re
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIB = 'x0xb0x-adapter'
SYMBOLS = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols')
NS = uuid.UUID('6f3c7a52-0d7e-4c55-9b3a-5a1f4e1b2c30')

PITCH = 2.286
ROW_X = [-2 * PITCH, -PITCH, 0.0, PITCH, 2 * PITCH]
WIDTH, HEIGHT = 11.4, 7.8  # board, mm
HOLE_V, PAD_LEN, PAD_W, DRILL = 2.75, 3.2, 1.5, 0.8  # hook hole height above the bottom edge; oval lap pad spans v 0.35 to 3.55
CHIP_V = 5.6
PAD_X, PAD_SX, PAD_SY = 1.2, 1.4, 0.4
TRACK = 0.25
VIA_C2 = (-1.2, 4.25)  # collector jumps: both variants route the collectors the same way on the back
VIA_C1 = (1.2, 7.0)
ORIGIN = (100.0, 100.0)

VARIANTS = {
    'ce': dict(title='SSIP5 common-emitter adapter', sites='Q12 Q21 Q26', part='BCM847BS', replaces='2SC1583', row=['B1', 'C1', 'E', 'C2', 'B2'],
               letters='BCECB', chip={1: 'E', 2: 'B1', 3: 'C2', 4: 'E', 5: 'B2', 6: 'C1'}),
    'cb': dict(title='SSIP5 common-base adapter', sites='Q22', part='BCM847BS', replaces='2SC2291', row=['E1', 'C1', 'B', 'C2', 'E2'],
               letters='ECBCE', chip={1: 'E1', 2: 'B', 3: 'C2', 4: 'E2', 5: 'B', 6: 'C1'}),
}


def uid(*parts):
    return str(uuid.uuid5(NS, '/'.join(str(p) for p in parts)))


def px(x, v):
    """Board mm (x right, v up from the bottom edge, seen from the chip side) to KiCad page mm."""
    return round(ORIGIN[0] + x, 4), round(ORIGIN[1] + HEIGHT - v, 4)


def font(size, thick, mirror=False):
    j = ' (justify mirror)' if mirror else ''
    return f'(effects (font (size {size} {size}) (thickness {thick})){j})'


def fp_chip():
    """KiCad's stock SOT-363_SC-70-6 land pattern with the pads lengthened outward for an iron and the inner ends drawn
    back to leave a channel for one track under the body. The body sits at x +-0.63, leads reach +-1.05."""
    pads = [(1, -PAD_X, -0.65), (2, -PAD_X, 0), (3, -PAD_X, 0.65), (4, PAD_X, 0.65), (5, PAD_X, 0), (6, PAD_X, -0.65)]
    return pads


def fp_chip_text(nets=None, at=None, ref='Q1', value='BCM847BS', board=False):
    L = [f'(footprint "{LIB + ":" if board else ""}SOT-363_Hand"']
    if not board:
        L += ['\t(version 20260206)', '\t(generator "x0xb0x-build-adapter")']
    L += ['\t(layer "F.Cu")', '\t(descr "SOT-363 / SC-88, pads lengthened outward for hand soldering, 0.65 mm pitch, from KiCad SOT-363_SC-70-6")']
    if board:
        L += [f'\t(uuid "{uid(at, ref)}")', f'\t(at {at[0]} {at[1]})']
    L += [f'\t(property "Reference" "{ref}" (at 0 -2 0) (layer "F.Fab") (hide yes) {font(0.8, 0.12)})',
          f'\t(property "Value" "{value}" (at 0 2 0) (layer "F.Fab") (hide yes) {font(0.8, 0.12)})',
          '\t(attr smd)']
    for a, b in (((-0.63, -1.1), (0.63, -1.1)), ((0.63, -1.1), (0.63, 1.1)), ((0.63, 1.1), (-0.63, 1.1)), ((-0.63, 1.1), (-0.63, -1.1))):
        L.append(f'\t(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.1) (type solid)) (layer "F.Fab"))')
    for a, b in (((-0.45, -1.2), (0.45, -1.2)), ((-0.45, 1.2), (0.45, 1.2))):
        L.append(f'\t(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))')
    L.append('\t(fp_circle (center -1.45 -1.2) (end -1.33 -1.2) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS"))')
    L.append('\t(fp_rect (start -2.05 -1.3) (end 2.05 1.3) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))')
    for n, x, y in fp_chip():
        net = f' (net "/{nets[n]}")' if nets else ''
        u = f' (uuid "{uid(at, ref, n)}")' if board else ''
        L.append(f'\t(pad "{n}" smd roundrect (at {x} {y}) (size {PAD_SX} {PAD_SY}) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25){net}{u})')
    L.append('\t(model "${KICAD10_3DMODEL_DIR}/Package_TO_SOT_SMD.3dshapes/SOT-363_SC-70-6.step")')
    L.append(')')
    return '\n'.join(L)


def fp_row_text(nets=None, at=None, ref='J1', value='SSIP5 row', board=False):
    L = [f'(footprint "{LIB + ":" if board else ""}SSIP5_LapRow"']
    if not board:
        L += ['\t(version 20260206)', '\t(generator "x0xb0x-build-adapter")']
    L += ['\t(layer "F.Cu")', '\t(descr "Five oval lap pads at 2.286 mm for straight wires laid along the board, with a plated hook hole in each")']
    if board:
        L += [f'\t(uuid "{uid(at, ref)}")', f'\t(at {at[0]} {at[1]})']
    L += [f'\t(property "Reference" "{ref}" (at 0 -2 0) (layer "F.Fab") (hide yes) {font(0.8, 0.12)})',
          f'\t(property "Value" "{value}" (at 0 2 0) (layer "F.Fab") (hide yes) {font(0.8, 0.12)})',
          '\t(attr through_hole)',
          f'\t(fp_rect (start {ROW_X[0] - 1.0} -0.95) (end {ROW_X[4] + 1.0} 2.65) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))']
    # KiCad stores the pad at the hole; offset moves the copper shape from there, here down toward the board edge
    offset = round(HOLE_V - (0.35 + PAD_LEN / 2), 4)
    for i, x in enumerate(ROW_X):
        n = i + 1
        net = f' (net "/{nets[n]}")' if nets else ''
        u = f' (uuid "{uid(at, ref, n)}")' if board else ''
        L.append(f'\t(pad "{n}" thru_hole oval (at {x:.3f} 0) (size {PAD_W} {PAD_LEN}) (drill {DRILL} (offset 0 {offset})) (layers "*.Cu" "*.Mask") (remove_unused_layers no){net}{u})')
    L.append(')')
    return '\n'.join(L)


def seg(variant, a, b, layer, net):
    x1, y1 = px(*a)
    x2, y2 = px(*b)
    return f'\t(segment (start {x1} {y1}) (end {x2} {y2}) (width {TRACK}) (layer "{layer}") (net "/{net}") (uuid "{uid(variant, "seg", a, b, layer)}"))'


def text(variant, s, x, v, layer, size=0.9, thick=0.14, mirror=False):
    X, Y = px(x, v)
    return f'\t(gr_text "{s}" (at {X} {Y}) (layer "{layer}") (uuid "{uid(variant, "txt", s, x, v, layer)}") {font(size, thick, mirror)})'


def routes(variant):
    """Front (F.Cu) carries the base and emitter nets, the back (B.Cu) the two collector jumps. Row tracks end inside the pad, at the hook hole."""
    v = VARIANTS[variant]
    top, bot = CHIP_V + 0.65, CHIP_V - 0.65
    out = []
    F, B = 'F.Cu', 'B.Cu'
    if variant == 'ce':
        out += [seg(variant, (-PAD_X, top), (0, top), F, 'E'), seg(variant, (PAD_X, bot), (0, bot), F, 'E'), seg(variant, (0, top), (0, HOLE_V), F, 'E')]
        out += [seg(variant, (-PAD_X, CHIP_V), (ROW_X[0], CHIP_V), F, 'B1'), seg(variant, (ROW_X[0], CHIP_V), (ROW_X[0], HOLE_V), F, 'B1')]
        out += [seg(variant, (PAD_X, CHIP_V), (ROW_X[4], CHIP_V), F, 'B2'), seg(variant, (ROW_X[4], CHIP_V), (ROW_X[4], HOLE_V), F, 'B2')]
    else:
        out += [seg(variant, (-PAD_X, CHIP_V), (PAD_X, CHIP_V), F, 'B'), seg(variant, (0, CHIP_V), (0, HOLE_V), F, 'B')]
        out += [seg(variant, (-PAD_X, top), (ROW_X[0], top), F, 'E1'), seg(variant, (ROW_X[0], top), (ROW_X[0], HOLE_V), F, 'E1')]
        out += [seg(variant, (PAD_X, bot), (ROW_X[4], bot), F, 'E2'), seg(variant, (ROW_X[4], bot), (ROW_X[4], HOLE_V), F, 'E2')]
    # Collectors, identical in both variants: C2 from pin 3 to pin 4 of the row, C1 from pin 6 to pin 2 of the row
    out += [seg(variant, (-PAD_X, bot), VIA_C2, F, 'C2'), seg(variant, VIA_C2, (ROW_X[3], VIA_C2[1]), B, 'C2'), seg(variant, (ROW_X[3], VIA_C2[1]), (ROW_X[3], HOLE_V), B, 'C2')]
    out += [seg(variant, (PAD_X, top), VIA_C1, F, 'C1'), seg(variant, VIA_C1, (ROW_X[1], VIA_C1[1]), B, 'C1'), seg(variant, (ROW_X[1], VIA_C1[1]), (ROW_X[1], HOLE_V), B, 'C1')]
    for at, net in ((VIA_C2, 'C2'), (VIA_C1, 'C1')):
        X, Y = px(*at)
        out.append(f'\t(via (at {X} {Y}) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "/{net}") (uuid "{uid(variant, "via", at)}"))')
    return out


LAYERS = '''	(layers
		(0 "F.Cu" signal)
		(2 "B.Cu" signal)
		(9 "F.Adhes" user "F.Adhesive")
		(11 "B.Adhes" user "B.Adhesive")
		(13 "F.Paste" user)
		(15 "B.Paste" user)
		(5 "F.SilkS" user "F.Silkscreen")
		(7 "B.SilkS" user "B.Silkscreen")
		(1 "F.Mask" user)
		(3 "B.Mask" user)
		(17 "Dwgs.User" user "User.Drawings")
		(19 "Cmts.User" user "User.Comments")
		(25 "Edge.Cuts" user)
		(27 "Margin" user)
		(31 "F.CrtYd" user "F.Courtyard")
		(29 "B.CrtYd" user "B.Courtyard")
		(35 "F.Fab" user)
		(33 "B.Fab" user)
	)'''


def pcb(variant):
    v = VARIANTS[variant]
    row_nets = {i + 1: n for i, n in enumerate(v['row'])}
    L = ['(kicad_pcb', '\t(version 20260206)', '\t(generator "x0xb0x-build-adapter")', '\t(generator_version "10.0")', '\t(general (thickness 1.6) (legacy_teardrops no))', '\t(paper "A4")', LAYERS,
         '\t(setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no) (tenting (front yes) (back yes)))']
    L += ['\t' + x for x in fp_row_text(row_nets, px(0, HOLE_V), value='SSIP5 row', board=True).split('\n')]
    L += ['\t' + x for x in fp_chip_text(v['chip'], px(0, CHIP_V), value=v['part'], board=True).split('\n')]
    L += routes(variant)
    L.append(f'\t(gr_rect (start {px(-WIDTH / 2, HEIGHT)[0]} {px(0, HEIGHT)[1]}) (end {px(WIDTH / 2, 0)[0]} {px(0, 0)[1]}) (stroke (width 0.05) (type default)) (fill no) (layer "Edge.Cuts") (uuid "{uid(variant, "edge")}"))')
    L.append(text(variant, variant.upper(), -3.9, 7.0, 'F.SilkS'))
    L.append(text(variant, 'Q1', 3.9, 7.0, 'F.SilkS', 0.8, 0.12))
    L.append(text(variant, v['sites'], 0, 6.3, 'B.SilkS', 1.0, 0.15, True))
    L.append(text(variant, f"for {v['replaces']}", 0, 5.1, 'B.SilkS', 0.8, 0.12, True))
    for x, c in zip(ROW_X, v['letters']):
        L.append(text(variant, c, -x, 4.1, 'B.SilkS', 0.8, 0.12, True))  # seen from the back, so left and right swap
    L.append(')')
    return '\n'.join(L) + '\n'


def lib_symbol(lib_file, name):
    """One symbol block from KiCad's library, renamed lib:name as a schematic embeds it."""
    t = (SYMBOLS / lib_file).read_text()
    i = t.index(f'(symbol "{name}"')
    d, k, q = 0, i, False
    while True:
        c = t[k]
        if c == '"' and t[k - 1] != '\\':
            q = not q
        elif not q:
            d += c == '('
            d -= c == ')'
            if d == 0:
                break
        k += 1
    return t[i:k + 1].replace(f'(symbol "{name}"', f'(symbol "{lib_file[:-len(".kicad_sym")]}:{name}"', 1), t[i:k + 1]


def pin_points(block, unit):
    """{pin number: (x, y)} of the connection points of one unit, in symbol coordinates (y up)."""
    out = {}
    for m in re.finditer(r'\(symbol "[^"]*_(\d+)_\d+"', block):
        if int(m[1]) != unit and int(m[1]) != 0:
            continue
        d, k, q = 0, m.start(), False
        while True:
            c = block[k]
            if c == '"':
                q = not q
            elif not q:
                d += c == '('
                d -= c == ')'
                if d == 0:
                    break
            k += 1
        for p in re.finditer(r'\(pin \w+ \w+\s+\(at (-?[\d.]+) (-?[\d.]+) \d+\).*?\(number "(\d+)"', block[m.start():k], re.S):
            out[int(p[3])] = (float(p[1]), float(p[2]))
    return out


def sch(variant):
    v = VARIANTS[variant]
    q_lib, q_raw = lib_symbol('Transistor_BJT.kicad_sym', 'Q_Dual_NPN_NPN_E1B1C2E2B2C1')
    j_lib, j_raw = lib_symbol('Connector_Generic.kicad_sym', 'Conn_01x05')
    root = uid(variant, 'sheet')
    prj = f'ssip5-{variant}'
    L = ['(kicad_sch', '\t(version 20260306)', '\t(generator "x0xb0x-build-adapter")', '\t(generator_version "10.0")', f'\t(uuid "{root}")', '\t(paper "A5")',
         f'\t(title_block (title "{v["title"]}") (comment 1 "Replaces {v["replaces"]} at {v["sites"]}. Mainboard unchanged."))',
         '\t(lib_symbols', q_lib, j_lib, '\t)']

    def inst(lib, ref, unit, x, y, value, fp):
        return (f'\t(symbol (lib_id "{lib}") (at {x} {y} 0) (unit {unit}) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid(variant, ref, unit)}")\n'
                f'\t\t(property "Reference" "{ref}" (at {x + 2.54} {y - 6} 0) {font(1.27, 0.15)})\n'
                f'\t\t(property "Value" "{value}" (at {x + 2.54} {y - 3.5} 0) {font(1.27, 0.15)})\n'
                f'\t\t(property "Footprint" "{LIB}:{fp}" (at {x} {y} 0) (hide yes) {font(1.27, 0.15)})\n'
                f'\t\t(property "Datasheet" "" (at {x} {y} 0) (hide yes) {font(1.27, 0.15)})\n'
                f'\t\t(instances (project "{prj}" (path "/{root}" (reference "{ref}") (unit {unit})))))')
    labels = []

    def label(name, x, y):
        labels.append(f'\t(label "{name}" (at {x} {y} 0) (fields_autoplaced yes) {font(1.27, 0.15)} (uuid "{uid(variant, "lbl", name, x, y)}"))')
    jx, jy = 60.96, 60.96
    for n, (x, y) in pin_points(j_raw, 1).items():
        label(v['row'][n - 1], round(jx + x, 3), round(jy - y, 3))
    qa, qb = (101.6, 50.8), (101.6, 71.12)
    pts = {}
    for pos, unit in ((qa, 1), (qb, 2)):
        for n, (x, y) in pin_points(q_raw, unit).items():
            pts[n] = (round(pos[0] + x, 3), round(pos[1] - y, 3))
    assert sorted(pts) == [1, 2, 3, 4, 5, 6], pts
    for n, (x, y) in pts.items():
        label(v['chip'][n], x, y)
    L += labels
    L.append(inst('Connector_Generic:Conn_01x05', 'J1', 1, jx, jy, 'SSIP5 row', 'SSIP5_LapRow'))
    L.append(inst('Transistor_BJT:Q_Dual_NPN_NPN_E1B1C2E2B2C1', 'Q1', 1, *qa, v['part'], 'SOT-363_Hand'))
    L.append(inst('Transistor_BJT:Q_Dual_NPN_NPN_E1B1C2E2B2C1', 'Q1', 2, *qb, v['part'], 'SOT-363_Hand'))
    L.append(f'\t(text "Row pins seen on the mainboard: {" ".join(v["row"])}, pin 1 to 5. Rotating the adapter 180 degrees only swaps the two halves." (exclude_from_sim yes) (at 40 90 0) {font(1.27, 0.15)} (uuid "{uid(variant, "note")}"))')
    L += [f'\t(sheet_instances (path "/" (page "1")))', ')']
    return '\n'.join(L) + '\n'


def pro(variant):
    return json.dumps({
        'board': {'design_settings': {'defaults': {'silk_text_size_h': 0.9, 'silk_text_size_v': 0.9, 'silk_text_thickness': 0.14},
                                      'rules': {'min_clearance': 0.15, 'min_connection': 0.0, 'min_copper_edge_clearance': 0.3, 'min_hole_clearance': 0.25, 'min_hole_to_hole': 0.25, 'min_silk_clearance': 0.0, 'min_text_height': 0.8, 'min_text_thickness': 0.08,
                                                'min_through_hole_diameter': 0.3, 'min_track_width': 0.15, 'min_via_annular_width': 0.13, 'min_via_diameter': 0.5, 'solder_mask_to_copper_clearance': 0.0}}},
        'meta': {'filename': f'ssip5-{variant}.kicad_pro', 'version': 3},
        'net_settings': {'classes': [{'name': 'Default', 'clearance': 0.2, 'track_width': TRACK, 'via_diameter': 0.6, 'via_drill': 0.3, 'microvia_diameter': 0.3, 'microvia_drill': 0.1, 'diff_pair_gap': 0.25, 'diff_pair_via_gap': 0.25, 'diff_pair_width': 0.2, 'bus_width': 12, 'wire_width': 6, 'line_style': 0, 'priority': -1, 'schematic_color': 'rgba(0, 0, 0, 0.000)', 'pcb_color': 'rgba(0, 0, 0, 0.000)'}], 'meta': {'version': 5}},
        'sheets': [[uid(variant, 'sheet'), 'Root']],
    }, indent=2) + '\n'


def main():
    lib = HERE / f'{LIB}.pretty'
    lib.mkdir(exist_ok=True)
    (lib / 'SOT-363_Hand.kicad_mod').write_text(fp_chip_text() + '\n')
    (lib / 'SSIP5_LapRow.kicad_mod').write_text(fp_row_text() + '\n')
    for variant in VARIANTS:
        d = HERE / variant
        d.mkdir(exist_ok=True)
        (d / f'ssip5-{variant}.kicad_pcb').write_text(pcb(variant))
        (d / f'ssip5-{variant}.kicad_sch').write_text(sch(variant))
        (d / f'ssip5-{variant}.kicad_pro').write_text(pro(variant))
        (d / 'fp-lib-table').write_text(f'(fp_lib_table\n\t(version 7)\n\t(lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/../{LIB}.pretty")(options "")(descr "SSIP5 adapter footprints"))\n)\n')
    print('wrote', ', '.join(VARIANTS))


if __name__ == '__main__':
    main()
