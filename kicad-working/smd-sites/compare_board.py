#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""What changed on the mainboard against the previous revision's board? Read-only.

Usage: compare_board.py <old board> <new board>
For revision 29:  git show 8d172d1:kicad-working/mainboard/mainboard.kicad_pcb > /tmp/old.kicad_pcb
For revision 30:  git show 1ba31be:kicad-working/mainboard/mainboard.kicad_pcb > /tmp/old.kicad_pcb

Compares footprints, tracks, arcs and vias item by item, ignoring uuids, formatting and the order of items. New copper must lie
near the chips. An old track may only have been split where a new one joins it. Existing footprints may differ only in their
links to symbols, the do-not-place mark on the parts the chips replace, and KiCad's trimming of unused layers from keepouts. Exits nonzero
otherwise. Pour fills are compared by compare_gerbers.py, since a refill moves points without moving copper.
"""
import math
import re
import sys
from collections import Counter
from pathlib import Path

SITES = {'Q112': (85.24, -114.7), 'Q121': (61.6, -121.7), 'Q122': (62.2, -104.9), 'Q126': (156.55, -144.9), 'Q128': (161.4, -157.1), 'Q139': (208.1, -156.0)}
SIP = ('Q12', 'Q21', 'Q22', 'Q26', 'Q28', 'Q39')
NEAR = 14.0  # mm from a chip


def blocks(text, head):
    """Top-level expressions of a kind, found by their indentation, which KiCad keeps exact."""
    out = []
    start = f'\n\t({head}'
    i = 0
    while (j := text.find(start, i)) >= 0:
        k = text.find('\n\t)', j)
        out.append(text[j + 1:k + 3])
        i = k
    return out


def clean(block):
    block = re.sub(r'\s*\(uuid "[^"]*"\)', '', block)
    block = re.sub(r'\s+', ' ', block)
    block = re.sub(r'\s+\)', ')', block)
    return re.sub(r'\(layers "F\.Cu" "B\.Cu"(?: "In\d+\.Cu")*\)', '(layers "F.Cu" "B.Cu")', block).strip()


def items(text):
    foots = {re.search(r'\(property "Reference" "([^"]+)"', f)[1]: f for f in blocks(text, 'footprint')}
    return Counter(map(clean, blocks(text, 'segment'))), Counter(map(clean, blocks(text, 'arc'))), Counter(map(clean, blocks(text, 'via'))), foots


def points(item):
    return [(float(a), float(b)) for a, b in re.findall(r'\((?:start|end|mid|at) ([-\d.]+) ([-\d.]+)', item)]


def near_site(item):
    return all(min(math.dist(p, s) for s in SITES.values()) < NEAR for p in points(item))


def fields(seg):
    (a, b) = points(seg)
    width = re.search(r'\(width ([\d.]+)\)', seg)[1]
    layer = re.search(r'\(layer "([^"]+)"\)', seg)[1]
    net = re.search(r'\(net "([^"]*)"\)', seg)[1]
    return a, b, width, layer, net


def split_of(removed, added):
    """The added segments of the same width, layer and net that lie along a removed one and cover it."""
    a, b, width, layer, net = fields(removed)
    length = math.dist(a, b)
    pieces, covered = [], 0.0
    for seg in added:
        p, q, w, ly, n = fields(seg)
        if (w, ly, n) != (width, layer, net):
            continue
        on = all(abs(math.dist(a, r) + math.dist(r, b) - length) < 0.002 for r in (p, q))
        if on:
            pieces.append(seg)
            covered += math.dist(p, q)
    return pieces if abs(covered - length) < 0.002 else None


def main():
    old_text, new_text = (Path(p).read_text() for p in sys.argv[1:3])
    old, new = items(old_text), items(new_text)
    problems = []
    for name, a, b in (('track segment', old[0], new[0]), ('track arc', old[1], new[1]), ('via', old[2], new[2])):
        gone, added = a - b, b - a
        for x in list(gone):
            pieces = split_of(x, list(added.elements())) if name == 'track segment' else None
            if pieces:
                print('   split where a new track joins it:', x[:110])
                gone -= Counter([x])
                added -= Counter(pieces)
        far = [x for x in added if not near_site(x)]
        print(f'{name}: {sum(a.values())} -> {sum(b.values())}; removed {sum(gone.values())}, added {sum(added.values())}, added away from the chips {len(far)}')
        print('   added widths', dict(Counter(re.findall(r'\(width ([\d.]+)\)', ' '.join(added.elements())))))
        if gone:
            problems.append(f'{sum(gone.values())} {name}s removed')
        if far:
            problems.append(f'{len(far)} {name}s added away from the chips')
    a, b = old[3], new[3]
    print('footprints:', len(a), '->', len(b), 'added', sorted(set(b) - set(a)), 'removed', sorted(set(a) - set(b)))
    if set(a) - set(b) or set(b) - set(a) - set(SITES):
        problems.append('footprints added or removed other than the chips')
    changed = []
    for ref in sorted(set(a) & set(b)):
        link = r'\n\t\t\((?:path|sheetname|sheetfile) "[^"]*"\)'
        x, y = re.sub(link, '', a[ref]), re.sub(link, '', b[ref])
        if ref in SIP:
            x, y = x.replace('\n\t\t(attr dnp)', '', 1), y.replace('\n\t\t(attr dnp)', '', 1)
        if clean(x) != clean(y):
            changed.append(ref)
    print('existing footprints that differ apart from links:', changed)
    if changed:
        problems.append(f'existing footprints changed: {changed[:8]}')
    print('RESULT', 'only the new sites changed' if not problems else problems)
    raise SystemExit(1 if problems else 0)


if __name__ == '__main__':
    main()
