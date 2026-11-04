#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Compare a redrawn schematic's netlist with the board copper and with the original Eagle schematic.

Usage: check_nets.py <mainboard|ioboard> <netlist.net> [--partial]

Pins are grouped by net on all sides, and names must match too. A pad with no net on the board must be an unconnected pin on
the sheet. --partial limits the comparison to the parts placed so far, while the sheets are being drawn.
"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RENAMED = {'IC15A0': 'IC15A', 'IC15B0': 'IC15B', 'R100A0': 'R100A', 'R100B0': 'R100B', 'CV0': 'CV', 'GATE0': 'GATE', 'HEADPHONE0': 'HEADPHONE', 'MIXIN0': 'MIXIN', 'MIXOUT0': 'MIXOUT', 'POWER0': 'POWER', 'USB0': 'USB'}


def read_netlist(path):
    text = open(path).read()
    pins = {}
    for m in re.finditer(r'\(net\s+\(code "?\d+"?\)\s+\(name "([^"]*)"\)(.*?)(?=\(net\s+\(code|\Z)', text, re.S):
        for ref, pad in re.findall(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)', m[2]):
            pins[f'{ref}.{pad}'] = m[1]
    return pins


def groups(pins):
    out = collections.defaultdict(set)
    for p, n in pins.items():
        out[n].add(p)
    return {frozenset(v) for v in out.values()}


def compare(name, sch, other, limit=30):
    missing = sorted(set(other) - set(sch))
    extra = sorted(set(sch) - set(other))
    names = sorted((p, sch[p], other[p]) for p in set(sch) & set(other) if sch[p] != other[p])
    a, b = groups({p: sch[p] for p in other if p in sch}), groups({p: other[p] for p in sch if p in other})
    diff = a ^ b
    print(f'{name}: pins {len(other)}, nets {len(b)}; missing {len(missing)}, extra {len(extra)}, names differing {len(names)}, differing groups {len(diff)}')
    for line in missing[:limit] + extra[:limit] + names[:limit]:
        print('   ', line)
    for g in sorted(diff, key=lambda s: sorted(s))[:limit]:
        print('    group', sorted(g))
    return not (missing or extra or names or diff)


def main():
    board, netlist = sys.argv[1:3]
    partial = '--partial' in sys.argv
    sch = read_netlist(netlist)
    parts = json.load(open(HERE / 'data' / f'{board}_parts.json'))
    placed = {p.rsplit('.', 1)[0] for p in sch}
    copper = {}
    open_pads = set()
    for r, p in parts.items():
        if not p['path'] and r.startswith('U$'):
            continue  # Mounting holes have no symbol on the original sheet either.
        if partial and r not in placed:
            continue
        for q in p['pads']:
            if q['net'] is None:
                open_pads.add(f'{r}.{q["num"]}')
            else:
                copper[f'{r}.{q["num"]}'] = q['net']
    wrongly_joined = sorted(p for p in open_pads if p in sch and not sch[p].startswith('unconnected-'))
    linked = {p: n for p, n in sch.items() if p not in open_pads}
    ok = compare('against the copper', linked, copper)
    print('pads open on the board but joined on the sheet:', wrongly_joined[:20], len(wrongly_joined))
    bad_nc = sorted(p for p, n in sch.items() if n.startswith('unconnected-') and p not in open_pads)
    print('pads on a net on the board but unconnected on the sheet:', bad_nc[:20], len(bad_nc))
    source = {}
    back = {v: k for k, v in RENAMED.items()}
    for reference, pad, net in json.load(open(HERE / 'data' / f'{board}_eagle_nets.json'))['pins']:
        ref = back.get(reference, reference)
        if partial and ref not in placed:
            continue
        source[f'{ref}.{pad}'] = net
    ok2 = compare('against the Eagle schematic', {p: n for p, n in sch.items() if p in source}, source)
    print('RESULT', 'OK' if ok and ok2 and not wrongly_joined and not bad_nc else 'FAIL')


if __name__ == '__main__':
    main()
