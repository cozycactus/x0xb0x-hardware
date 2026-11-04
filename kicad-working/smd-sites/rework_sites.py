#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Clear Q112's and Q126's first routing so that they can be routed again by hand. Run once, with KiCad closed. Don't run it again.

Removes their 0.25 mm tracks and their vias, restores the original N$121 segment that the first routing split, moves the two chips
to their second positions and shortens the lands of all four chips. Q121's and Q122's tracks end inside the shorter lands.

Usage: rework_sites.py <revision 28 board, for the original segment>
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent / 'mainboard'
MOVES = {'Q112': (85.24, -114.7), 'Q126': (156.55, -144.9)}
NETS = {'N$127', 'N$60', 'N$118', 'N$124', 'N$121', 'N$101', '+5.333V', 'N$113', 'N$99', 'N$98'}
CHIPS = ('Q112', 'Q121', 'Q122', 'Q126')
TEXT = {'Q112': (82.6, -113.2), 'Q126': (154.9, -142.6)}
TRACK, VIA = '0.25', '0.8'


def blocks(text, head):
    out, i, start = [], 0, f'\n\t({head}'
    while (j := text.find(start, i)) >= 0:
        k = text.find('\n\t)', j)
        out.append((j, k + 3))
        i = k
    return out


def footprint_span(text, ref):
    i = text.index(f'(property "Reference" "{ref}"')
    return text.rindex('\n\t(footprint ', 0, i), text.index('\n\t)\n', i)


def shorter_lands(f):
    """Pads from 0.5 to 1.6 mm off centre, instead of to 1.9, with the courtyard and pin 1 dot brought in to match."""
    f = re.sub(r'(\(pad "\d" smd roundrect\s+\(at )-1\.2 ', r'\g<1>-1.05 ', f)
    f = re.sub(r'(\(pad "\d" smd roundrect\s+\(at )1\.2 ', r'\g<1>1.05 ', f)
    f = re.sub(r'\(size 1\.4 0\.39\)', '(size 1.1 0.39)', f)
    f = f.replace('(start -2.05 -1.3)', '(start -1.75 -1.3)').replace('(end 2.05 1.3)', '(end 1.75 1.3)')
    f = f.replace('(center -2.1 -0.65)', '(center -1.8 -0.65)').replace('(end -1.98 -0.65)', '(end -1.68 -0.65)')
    return f


def main():
    path = PROJECT / 'mainboard.kicad_pcb'
    text = path.read_text()
    original = Path(sys.argv[1]).read_text()
    removed = dict(segments=0, vias=0)
    for head, key in (('segment', 'segments'), ('via', 'vias')):
        for a, b in reversed(blocks(text, head)):
            item = text[a:b]
            net = re.search(r'\(net "([^"]*)"\)', item)[1]
            new = re.search(r'\(width 0\.25\)', item) if head == 'segment' else re.search(r'\(size 0\.8\)', item)
            if new and net in NETS:
                text = text[:a] + text[b:]
                removed[key] += 1

    # The first routing split this original track where it joined it.
    whole = [original[a:b] for a, b in blocks(original, 'segment') if '(start 82.931 -114.808)' in original[a:b] and '(end 82.931 -117.094)' in original[a:b]]
    assert len(whole) == 1
    found = []
    for a, b in reversed(blocks(text, 'segment')):
        item = text[a:b]
        s = re.search(r'\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)', item)
        if '(net "N$121")' in item and '(layer "B.Cu")' in item and float(s[1]) == 82.931 == float(s[3]) and -117.094 <= min(float(s[2]), float(s[4])) and max(float(s[2]), float(s[4])) <= -114.808:
            found.append(item)
            text = text[:a] + text[b:]
    assert sum(abs(float(re.search(r'\(start [-\d.]+ ([-\d.]+)\)', i)[1]) - float(re.search(r'\(end [-\d.]+ ([-\d.]+)\)', i)[1])) for i in found) > 2.28, found
    first = blocks(text, 'segment')[0][0]
    text = text[:first] + whole[0] + text[first:]

    for ref in CHIPS:
        a, b = footprint_span(text, ref)
        f = shorter_lands(text[a:b])
        if ref in MOVES:
            x, y = MOVES[ref]
            f, n = re.subn(r'(\n\t\t\(at )[-\d.]+ [-\d.]+', rf'\g<1>{x} {y}', f, count=1)
            assert n == 1
            at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', f)
            tx, ty = TEXT[ref]
            dx, dy = tx - x, ty - y
            lx, ly = (dx, dy) if not at[3] else (-dy, dx)
            f, n = re.subn(rf'(\(property "Reference" "{ref}"\s+\(at )[-\d.]+ [-\d.]+', rf'\g<1>{round(lx, 3)} {round(ly, 3)}', f, count=1)
            assert n == 1
        text = text[:a] + f + text[b:]
    path.write_text(text)

    lib = PROJECT / 'x0x-smd.pretty' / 'SOT-363_Hand.kicad_mod'
    lib.write_text(shorter_lands(lib.read_text()).replace('pads lengthened outward for hand soldering and narrowed to 0.39 mm', 'pads lengthened outward to 1.6 mm off centre for hand soldering and narrowed to 0.39 mm'))
    print('removed', removed, 'restored the original N$121 segment from', len(found), 'pieces')


if __name__ == '__main__':
    main()
