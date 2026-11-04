#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Put the four SOT-363 duals on the mainboard, next to the SSIP5 rows they can replace. Tracks are routed by hand in KiCad.

Usage: place_chips.py        run once, on the revision 28 board, from anywhere

Adds the footprints with their pad nets, the project library for them and the 3D model, and sets the Default net class to the
track and via used for these routes: no track on the board uses that class's width, and its clearance only rises to the board's
own minimum. The SSIP5 footprints, their holes and all existing copper stay.
"""
import json
import re
import shutil
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent / 'mainboard'
NS = uuid.UUID('1b3f7a52-9d1e-4f0a-8a6b-2e7c5d9f4a10')
LIB = 'x0x-smd'
STOCK = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels/Package_TO_SOT_SMD.3dshapes/SOT-363_SC-70-6.step')
MODEL = '${KIPRJMOD}/3dmodels/KiCad/Package_TO_SOT_SMD.3dshapes/SOT-363_SC-70-6.step'

# Pins: 1 E1, 2 B1, 3 C2, 4 E2, 5 B2, 6 C1. Each transistor goes with the base and collector pads on one side of the row.
SITES = {
    'Q112': dict(at=(87.6, -114.2), rot=0, value='BCM847BS', text=(84.6, -115.65), nets={1: 'N$127', 2: 'N$60', 3: 'N$118', 4: 'N$127', 5: 'N$124', 6: 'N$121'}),
    'Q121': dict(at=(61.6, -121.7), rot=0, value='BC847CDW1T1G', text=(58.3, -121.0), nets={1: 'N$139', 2: 'N$141', 3: 'N$140', 4: 'N$139', 5: 'N$138', 6: 'N$148'}),
    'Q122': dict(at=(62.2, -104.9), rot=0, value='BCM847BS', text=(65.7, -105.7), nets={1: 'N$120', 2: 'N$115', 3: 'N$122', 4: 'N$143', 5: 'N$115', 6: 'N$122'}),
    'Q126': dict(at=(156.55, -145.2), rot=90, value='BCM847BS', text=(155.4, -148.1), nets={1: 'N$101', 2: '+5.333V', 3: 'N$113', 4: 'N$101', 5: 'N$99', 6: 'N$98'}),
}
PADS = [(1, -1.2, -0.65), (2, -1.2, 0), (3, -1.2, 0.65), (4, 1.2, 0.65), (5, 1.2, 0), (6, 1.2, -0.65)]
TRACK, VIA, DRILL, CLEARANCE = 0.25, 0.8, 0.39, 0.254


def uid(*parts):
    return str(uuid.uuid5(NS, '/'.join(map(str, parts))))


def effects(size=0.8, thick=0.12):
    return f'(effects (font (size {size} {size}) (thickness {thick})))'


def footprint(ref=None, site=None):
    """The library footprint with no ref, or the placed footprint with its nets."""
    head = f'{LIB}:SOT-363_Hand' if ref else 'SOT-363_Hand'
    rot = site['rot'] if ref else 0
    L = [f'(footprint "{head}"', '\t(layer "F.Cu")']
    if ref:
        x, y = site['at']
        L += [f'\t(uuid "{uid(ref)}")', f'\t(at {x} {y}' + (f' {rot}' if rot else '') + ')']
    else:
        L += ['\t(version 20260206)', '\t(generator "x0xb0x-smd-sites")']
    L += ['\t(descr "SOT-363 / SC-88, pads lengthened outward for hand soldering and narrowed to 0.39 mm to keep 0.254 mm between them, 0.65 mm pitch, from KiCad SOT-363_SC-70-6")']
    if ref:
        tx, ty = site['text']
        # Text positions are stored in the footprint's frame; these footprints turn only by 0 or 90 degrees.
        dx, dy = tx - x, ty - y
        lx, ly = (dx, dy) if rot == 0 else (-dy, dx)
        L += [f'\t(property "Reference" "{ref}" (at {round(lx, 3)} {round(ly, 3)} {rot}) (layer "F.SilkS") (uuid "{uid(ref, "r")}") {effects()})',
              f'\t(property "Value" "{site["value"]}" (at 0 2 {rot}) (layer "F.Fab") (hide yes) (uuid "{uid(ref, "v")}") {effects()})']
    else:
        L += [f'\t(property "Reference" "REF**" (at 0 -2 0) (layer "F.SilkS") {effects()})', f'\t(property "Value" "SOT-363_Hand" (at 0 2 0) (layer "F.Fab") (hide yes) {effects()})']
    L.append('\t(attr smd)')
    for a, b in (((-0.63, -1.1), (0.63, -1.1)), ((0.63, -1.1), (0.63, 1.1)), ((0.63, 1.1), (-0.63, 1.1)), ((-0.63, 1.1), (-0.63, -1.1))):
        L.append(f'\t(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.1) (type solid)) (layer "F.Fab")' + (f' (uuid "{uid(ref, a, b, "f")}")' if ref else '') + ')')
    for a, b in (((-0.45, -1.2), (0.45, -1.2)), ((-0.45, 1.2), (0.45, 1.2))):
        L.append(f'\t(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.12) (type solid)) (layer "F.SilkS")' + (f' (uuid "{uid(ref, a, b, "s")}")' if ref else '') + ')')
    L.append('\t(fp_circle (center -2.1 -0.65) (end -1.98 -0.65) (stroke (width 0.12) (type solid)) (fill yes) (layer "F.SilkS")' + (f' (uuid "{uid(ref, "dot")}")' if ref else '') + ')')
    L.append('\t(fp_rect (start -2.05 -1.3) (end 2.05 1.3) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd")' + (f' (uuid "{uid(ref, "cy")}")' if ref else '') + ')')
    for n, x_, y_ in PADS:
        at = f'(at {x_} {y_}' + (f' {rot}' if rot else '') + ')'
        net = f' (net "{site["nets"][n]}")' if ref else ''
        u = f' (uuid "{uid(ref, "pad", n)}")' if ref else ''
        L.append(f'\t(pad "{n}" smd roundrect {at} (size 1.4 0.39) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25){net}{u})')
    L.append(f'\t(model "{MODEL}")')
    L.append(')')
    return '\n'.join(L)


def main():
    lib = PROJECT / f'{LIB}.pretty'
    lib.mkdir(exist_ok=True)
    (lib / 'SOT-363_Hand.kicad_mod').write_text(footprint() + '\n')
    model = PROJECT / '3dmodels' / 'KiCad' / 'Package_TO_SOT_SMD.3dshapes' / STOCK.name
    model.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(STOCK, model)

    table = PROJECT / 'fp-lib-table'
    text = table.read_text()
    if f'"{LIB}"' not in text:
        text = text.rstrip()
        assert text.endswith(')')
        table.write_text(text[:-1].rstrip() + f'\n  (lib (name "{LIB}") (type "KiCad") (uri "${{KIPRJMOD}}/{LIB}.pretty") (options "") (descr "Hand-soldering footprints for the SMD sites"))\n)\n')

    pro = PROJECT / 'mainboard.kicad_pro'
    text = pro.read_text()
    data = json.loads(text)
    cls = data['net_settings']['classes'][0]
    assert cls['name'] == 'Default'
    for key, old, new in (('clearance', cls['clearance'], CLEARANCE), ('track_width', cls['track_width'], TRACK), ('via_diameter', cls['via_diameter'], VIA), ('via_drill', cls['via_drill'], DRILL)):
        text, n = re.subn(rf'("{key}": ){re.escape(json.dumps(old))}(,)', rf'\g<1>{new}\g<2>', text, count=1)
        assert n == 1, key
    pro.write_text(text)

    pcb = PROJECT / 'mainboard.kicad_pcb'
    text = pcb.read_text()
    assert 'Q112' not in text, 'already placed'
    block = '\n'.join('\t' + line for ref, site in SITES.items() for line in footprint(ref, site).split('\n'))
    first = text.index('\n\t(footprint ')
    pcb.write_text(text[:first + 1] + block + '\n' + text[first + 1:])
    print('placed', ', '.join(SITES))


if __name__ == '__main__':
    main()
