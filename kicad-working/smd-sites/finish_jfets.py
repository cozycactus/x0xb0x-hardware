#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Route Q128 and Q139 and finish the mainboard: run once, after place_jfets.py, with KiCad closed.

Writes the nine track segments of the drawn routes, marks Q28 and Q39 do-not-place and adds the two chips to the schematic
scripts' parts data. No existing track, pad or pour is touched; refill the pours afterwards.

These tracks were not drawn with the mouse, unlike revision 29's: the screen was locked when they were routed, so the paths were
drawn by hand on the copper map, checked for clearance and written here. KiCad's DRC then checks them like any other track.
"""
import json
import re
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent / 'mainboard'
DATA = HERE.parent / 'schematic-redraw' / 'data' / 'mainboard_parts.json'
NS = uuid.UUID('1b3f7a52-9d1e-4f0a-8a6b-2e7c5d9f4a10')
CHIPS = ('Q128', 'Q139')
WIDTH = 0.25
# Each route runs from a chip's pad centre to a pad centre on the same net. All of them are on F.Cu, inside the ground pour.
ROUTES = (
    ('N$113', [(161.4, -158.45), (164.592, -155.258), (164.592, -155.067)]),      # Q128 gate to C33, the VCO's timing node
    ('N$108', [(160.45, -155.75), (160.45, -154.989), (159.766, -154.305)]),      # Q128 source to R105
    ('+12V', [(162.35, -155.75), (162.35, -154.1), (165.1, -151.35), (165.1, -150.9268)]),  # Q128 drain to Q28's drain hole
    ('N$53', [(207.15, -157.35), (206.2, -157.35), (205.5876, -157.9626)]),       # Q139 drain to Q39's drain hole
)


def footprint_span(text, ref):
    i = text.index(f'(property "Reference" "{ref}"')
    return text.rindex('\n\t(footprint ', 0, i), text.index('\n\t)\n', i)


def segment(net, a, b):
    uid = uuid.uuid5(NS, f'track/{net}/{a}/{b}')
    return (f'\t(segment\n\t\t(start {a[0]} {a[1]})\n\t\t(end {b[0]} {b[1]})\n\t\t(width {WIDTH})\n\t\t(layer "F.Cu")\n'
            f'\t\t(net "{net}")\n\t\t(uuid "{uid}")\n\t)\n')


def main():
    path = PROJECT / 'mainboard.kicad_pcb'
    text = path.read_text()
    assert 'Q128' in text and str(uuid.uuid5(NS, f'track/N$53/{ROUTES[3][1][0]}/{ROUTES[3][1][1]}')) not in text, 'place first, and run once'
    for ref in ('Q28', 'Q39'):
        a, b = footprint_span(text, ref)
        f = text[a:b]
        assert '(attr' not in f.split('(fp_', 1)[0], ref
        n, count = re.subn(r'(\n\t\t)\(duplicate_pad_numbers_are_jumpers', r'\1(attr dnp)\1(duplicate_pad_numbers_are_jumpers', f, count=1)
        assert count == 1, ref
        text = text[:a] + n + text[b:]
    tracks = ''.join(segment(net, p, q) for net, pts in ROUTES for p, q in zip(pts, pts[1:]))
    first = text.index('\n\t(segment') + 1
    path.write_text(text[:first] + tracks + text[first:])

    parts = json.loads(DATA.read_text())
    for ref in CHIPS:
        a, b = footprint_span(text, ref)
        f = text[a:b]
        value = re.search(r'\(property "Value" "([^"]*)"', f)[1]
        pads = [dict(num=n, net=net, fn='') for n, net in re.findall(r'\(pad "(\d)" smd roundrect.*?\(net "([^"]*)"\)', f, re.S)]
        assert len(pads) == 3, (ref, pads)
        parts[ref] = dict(val=value, value=value, fp='x0x-smd:SC-59_Hand', path=None, board_only=False, pads=pads)
    DATA.write_text(json.dumps(parts, indent=0, sort_keys=True))
    print('routed and finished', CHIPS)


if __name__ == '__main__':
    main()
