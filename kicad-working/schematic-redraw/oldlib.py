#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Read symbols from the Eagle-import libraries kept in each KiCad project, for the parts that keep their original graphics."""
import re
from pathlib import Path

WORK = Path(__file__).resolve().parent.parent


def blocks(text, head):
    out, i, h = [], 0, '(' + head
    while True:
        j = text.find(h, i)
        if j < 0:
            return out
        if text[j + len(h)] not in ' \n\t':
            i = j + 1
            continue
        d, k, q = 0, j, False
        while True:
            c = text[k]
            if q and c == '\\':
                k += 2
                continue
            if c == '"':
                q = not q
            elif not q:
                d += c == '('
                d -= c == ')'
                if d == 0:
                    break
            k += 1
        out.append(text[j:k + 1])
        i = k + 1


def load(board):
    """A dict of symbol name to its text, from <board>-eagle-import.kicad_sym."""
    text = (WORK / board / f'{board}-eagle-import.kicad_sym').read_text()
    out = {}
    i = text.find('(symbol "')
    for s in blocks(text[i:], 'symbol'):
        out[re.match(r'\(symbol "([^"]+)"', s)[1]] = s
    return out


def units(sym):
    """{unit: [(number, name, x, y, angle, length, type)]}, with x and y as the library stores them (y up)."""
    name = re.match(r'\(symbol "([^"]+)"', sym)[1]
    out = {}
    body = sym[sym.find('\n') + 1:]
    for part in blocks(body, 'symbol'):
        m = re.match(r'\(symbol "(.+)_(\d+)_(\d+)"', part)
        unit = int(m[2])
        for p in blocks(part, 'pin'):
            pm = re.match(r'\(pin (\w+) (\w+)\s+\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s+\(length ([-\d.]+)\)', re.sub(r'\s+', ' ', p))
            pn = re.search(r'\(name "([^"]*)"', p)[1]
            num = re.search(r'\(number "([^"]*)"', p)[1]
            out.setdefault(unit, []).append((num, pn, float(pm[3]), float(pm[4]), float(pm[5] or 0), float(pm[6]), pm[1]))
    return out


if __name__ == '__main__':
    import sys
    lib = load(sys.argv[1])
    for n in sys.argv[2:]:
        for u, pins in sorted(units(lib[n]).items()):
            print(n, 'unit', u, ' '.join(f'{p[0]}[{p[1]}]@{p[2]:g},{p[3]:g}/{p[4]:g}' for p in pins))
