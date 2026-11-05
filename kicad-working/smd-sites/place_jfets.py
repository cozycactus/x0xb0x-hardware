#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Put two SC-59 2SK208 sites on the mainboard, next to the TO-92 rows of Q28 and Q39. Tracks are routed by hand in KiCad.

Usage: place_jfets.py        run once, on the revision 29 board, with KiCad closed

Adds the footprint to the project library, copies the 3D model and places Q128 and Q139 with their pad nets. Q28, Q39, their
holes and all existing copper stay. Run finish_jfets.py after the routing.

Pads follow the Toshiba 2SK208 drawing (S-Mini, JEITA SC-59): 1 source and 2 drain on one side, 1.9 mm apart, 3 gate on the
other. Body 2.9 x 1.5 mm, 2.5 mm across the leads (3.0 at most), leads 0.4 mm wide. The lands run from 0.75 to 1.95 mm off
centre, so a hand-soldered lead has 0.45 mm of toe at the widest part. They're 0.7 mm wide.
"""
import shutil
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent / 'mainboard'
NS = uuid.UUID('1b3f7a52-9d1e-4f0a-8a6b-2e7c5d9f4a10')
LIB = 'x0x-smd'
NAME = 'SC-59_Hand'
STOCK = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels/Package_TO_SOT_SMD.3dshapes/SC-59.step')
MODEL = '${KIPRJMOD}/3dmodels/KiCad/Package_TO_SOT_SMD.3dshapes/SC-59.step'

# Pins: 1 source, 2 drain, 3 gate. Q28's gate is the VCO's timing node, so its track stays short and runs inside the pour.
SITES = {
    'Q128': dict(at=(161.4, -157.1), rot=90, value='2SK208-O', text=(158.4, -154.05, 90), nets={1: 'N$108', 2: '+12V', 3: 'N$113'}),
    'Q139': dict(at=(208.1, -156.0), rot=270, value='2SK208-Y', text=(210.7, -158.7, 0), nets={1: 'GND', 2: 'N$53', 3: 'GND'}),
}
PADS = [(1, -1.35, -0.95), (2, -1.35, 0.95), (3, 1.35, 0)]
PAD_SIZE = (1.2, 0.7)
COURTYARD = [(-2.1, -1.45), (-0.9, -1.45), (-0.9, -1.6), (0.9, -1.6), (0.9, -0.5), (2.1, -0.5), (2.1, 0.5), (0.9, 0.5), (0.9, 1.6), (-0.9, 1.6), (-0.9, 1.45), (-2.1, 1.45)]


def uid(*parts):
    return str(uuid.uuid5(NS, '/'.join(map(str, parts))))


def effects(size=0.8, thick=0.12):
    return f'(effects (font (size {size} {size}) (thickness {thick})))'


def local(rot, dx, dy):
    """A board offset in the footprint's frame, for a footprint turned by a multiple of 90 degrees."""
    return {0: (dx, dy), 90: (-dy, dx), 180: (-dx, -dy), 270: (dy, -dx)}[rot]


def footprint(ref=None, site=None):
    """The library footprint with no ref, or the placed footprint with its nets."""
    head = f'{LIB}:{NAME}' if ref else NAME
    rot = site['rot'] if ref else 0
    L = [f'(footprint "{head}"', '\t(layer "F.Cu")']
    if ref:
        x, y = site['at']
        L += [f'\t(uuid "{uid(ref)}")', f'\t(at {x} {y}' + (f' {rot}' if rot else '') + ')']
    else:
        L += ['\t(version 20260206)', '\t(generator "x0xb0x-smd-sites")']
    L += ['\t(descr "SC-59 / S-Mini for the Toshiba 2SK208, lands 1.2 x 0.7 mm running from 0.75 to 1.95 mm off centre for hand soldering, 1.9 mm pitch")']
    if ref:
        tx, ty, angle = site['text']
        lx, ly = local(rot, tx - x, ty - y)
        L += [f'\t(property "Reference" "{ref}" (at {round(lx, 3)} {round(ly, 3)} {angle}) (layer "F.SilkS") (uuid "{uid(ref, "r")}") {effects()})',
              f'\t(property "Value" "{site["value"]}" (at 0 2.5 {rot}) (layer "F.Fab") (hide yes) (uuid "{uid(ref, "v")}") {effects()})']
    else:
        L += [f'\t(property "Reference" "REF**" (at 0 -2.5 0) (layer "F.SilkS") {effects()})', f'\t(property "Value" "{NAME}" (at 0 2.5 0) (layer "F.Fab") (hide yes) {effects()})']
    L.append('\t(attr smd)')
    hx, hy = 0.75, 1.45
    for a, b in (((-hx, -hy), (hx, -hy)), ((hx, -hy), (hx, hy)), ((hx, hy), (-hx, hy)), ((-hx, hy), (-hx, -hy))):
        L.append(f'\t(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.1) (type solid)) (layer "F.Fab")' + (f' (uuid "{uid(ref, a, b, "f")}")' if ref else '') + ')')
    # Short marks only: on Q128 the body sits between the silkscreen of R105 and C33 with 0.1 mm to spare on each side.
    for a, b in (((-0.85, -0.45), (-0.85, 0.45)), ((0.85, -1.4), (0.85, -0.5)), ((0.85, 0.5), (0.85, 1.4))):
        L.append(f'\t(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width 0.12) (type solid)) (layer "F.SilkS")' + (f' (uuid "{uid(ref, a, b, "s")}")' if ref else '') + ')')
    L.append('\t(fp_circle (center -1.6 -1.5) (end -1.5 -1.5) (stroke (width 0.1) (type solid)) (fill yes) (layer "F.SilkS")' + (f' (uuid "{uid(ref, "dot")}")' if ref else '') + ')')
    # Narrow around the gate land, so that R105's hole beside Q128 stays outside it.
    court = ' '.join(f'(xy {a} {b})' for a, b in COURTYARD)
    L.append(f'\t(fp_poly (pts {court}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd")' + (f' (uuid "{uid(ref, "cy")}")' if ref else '') + ')')
    for n, x_, y_ in PADS:
        at = f'(at {x_} {y_}' + (f' {rot}' if rot else '') + ')'
        net = f' (net "{site["nets"][n]}")' if ref else ''
        u = f' (uuid "{uid(ref, "pad", n)}")' if ref else ''
        L.append(f'\t(pad "{n}" smd roundrect {at} (size {PAD_SIZE[0]} {PAD_SIZE[1]}) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25){net}{u})')
    L.append(f'\t(model "{MODEL}")')
    L.append(')')
    return '\n'.join(L)


def main():
    (PROJECT / f'{LIB}.pretty' / f'{NAME}.kicad_mod').write_text(footprint() + '\n')
    model = PROJECT / '3dmodels' / 'KiCad' / 'Package_TO_SOT_SMD.3dshapes' / STOCK.name
    shutil.copyfile(STOCK, model)
    pcb = PROJECT / 'mainboard.kicad_pcb'
    text = pcb.read_text()
    assert 'Q128' not in text, 'already placed'
    block = '\n'.join('\t' + line for ref, site in SITES.items() for line in footprint(ref, site).split('\n'))
    first = text.index('\n\t(footprint ')
    pcb.write_text(text[:first + 1] + block + '\n' + text[first + 1:])
    print('placed', ', '.join(SITES))


if __name__ == '__main__':
    main()
