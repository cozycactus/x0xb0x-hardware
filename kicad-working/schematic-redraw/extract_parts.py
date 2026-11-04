#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Export what the redrawn sheets need from a board and from the sheet they replace. Reads only.

Usage: extract_parts.py <mainboard|ioboard> <baseline netlist.net>

Writes data/<board>_parts.json: for each footprint its board value, the value the baseline schematic gives it, its footprint
name and, for each pad, the copper's net and the baseline schematic's pin name. Values and pin names are kept because the BOM
and the simulation's extract_vcf.py read them. The baseline is the single-sheet schematic of revision 27. The wires of the
sheets do not come from this file.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parent


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


def main():
    board, netlist = sys.argv[1:3]
    pcb = (WORK / board / f'{board}.kicad_pcb').read_text()
    functions = {}
    text = open(netlist).read()
    for m in re.finditer(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"\)(?:\s+\(pinfunction "([^"]*)"\))?', text):
        functions[f'{m[1]}.{m[2]}'] = m[3] or ''
    values = {m[1]: m[2] for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)\s+\(value "([^"]*)"\)', text)}
    parts = {}
    for f in blocks(pcb, 'footprint'):
        name = re.match(r'\(footprint "([^"]+)"', f)[1]
        ref = re.search(r'\(property "Reference" "([^"]*)"', f)[1]
        value = re.search(r'\(property "Value" "([^"]*)"', f)[1]
        path = re.search(r'\(path "([^"]*)"\)', f)
        board_only = '(attr' in f and 'board_only' in re.search(r'\(attr[^)]*\)', f)[0]
        pads = []
        for p in blocks(f, 'pad'):
            num = re.match(r'\(pad "([^"]*)"', p)[1]
            net = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', p)
            pads.append(dict(num=num, net=net[1] if net else None, fn=functions.get(f'{ref}.{num}', '')))
        parts[ref] = dict(val=value, value=values.get(ref, value), fp=name, path=path[1] if path else None, board_only=bool(board_only), pads=pads)
    out = HERE / 'data' / f'{board}_parts.json'
    out.write_text(json.dumps(parts, indent=0, sort_keys=True))
    print(board, len(parts), 'footprints,', sum(len(p['pads']) for p in parts.values()), 'pads')


if __name__ == '__main__':
    main()
