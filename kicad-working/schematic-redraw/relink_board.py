#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Point a board's footprints at the redrawn symbols. Nothing else in the board file changes.

Usage: relink_board.py <project folder> <board>

KiCad ties a footprint to its symbol by the symbol's path, and the path changes when a sheet moves into a hierarchy. This is
what KiCad's "Re-link footprints to schematic symbols" does: it rewrites each footprint's path (and sheetname and sheetfile,
where a footprint has them), found by reference, and leaves copper, nets, placement and text alone. A footprint with no path
yet, such as a mounting hole, gets one where KiCad writes it. Footprints with no symbol keep their fields.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'


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
        out.append((j, k + 1))
        i = k + 1


def components(project, board):
    with tempfile.TemporaryDirectory() as d:
        net = Path(d) / 'n.net'
        subprocess.run([CLI, 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', str(net), str(project / f'{board}.kicad_sch')], check=True, capture_output=True)
        text = net.read_text()
    out = {}
    for a, b in blocks(text, 'comp'):
        c = text[a:b]
        ref = re.search(r'\(ref "([^"]+)"\)', c)[1]
        names = re.search(r'\(sheetpath\s+\(names "([^"]*)"\)\s+\(tstamps "([^"]*)"\)', c)
        ids = re.findall(r'"([^"]+)"', re.search(r'\(tstamps ((?:"[^"]+"\s*)+)\)', re.sub(r'\(sheetpath\s+\(names "[^"]*"\)\s+\(tstamps "[^"]*"\)\s*\)', '', c))[1])
        file = re.search(r'\(property\s+\(name "Sheetfile"\)\s+\(value "([^"]*)"\)', c)
        out[ref] = dict(path=names[2] + ids[0], units={names[2] + u for u in ids}, sheetname=names[1], sheetfile=file[1] if file else '')
    return out


def main():
    project, board = Path(sys.argv[1]), sys.argv[2]
    comps = components(project, board)
    path = project / f'{board}.kicad_pcb'
    pcb = path.read_text()
    parts, last, changed, kept = [], 0, 0, []
    for a, b in blocks(pcb, 'footprint'):
        f = pcb[a:b]
        ref = re.search(r'\(property "Reference" "([^"]*)"', f)[1]
        parts.append(pcb[last:a])
        last = b
        if ref not in comps:
            kept.append(ref)
            parts.append(f)
            continue
        c = comps[ref]
        n = f
        # A part with several units may link to any of them, and KiCad's first unit depends on the order of items on the sheet. A link that is already right stays.
        linked = re.search(r'\n\t\t\(path "([^"]*)"\)', f)
        for field, value in (('path', linked[1] if linked and linked[1] in c['units'] else c['path']), ('sheetname', c['sheetname']), ('sheetfile', c['sheetfile'])):
            n, count = re.subn(rf'(\n\t\t)\({field} "[^"]*"\)', rf'\1({field} "{value}")', n, count=1)  # Not the sheetname of a zone inside the footprint
            if field == 'path' and not count:
                n, count = re.subn(r'(\n\t\t)\(duplicate_pad_numbers_are_jumpers', rf'\1(path "{value}")\1(duplicate_pad_numbers_are_jumpers', n, count=1)
            assert count == 1 or field != 'path', (ref, field)
        changed += 1
        parts.append(n)
    parts.append(pcb[last:])
    path.write_text(''.join(parts))
    print(f'{board}: {changed} footprints relinked; no symbol, left as they are: {kept}')


if __name__ == '__main__':
    main()
