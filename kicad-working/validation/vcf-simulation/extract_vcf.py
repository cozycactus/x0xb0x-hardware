#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Export the simulated parts and their nets from the KiCad mainboard schematic to vcf-parts.json.

--check compares the current schematic with vcf-parts.json without writing anything, and fails if a
simulated part's value or net has changed. Needs kicad-cli (or the KICAD_CLI environment variable).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import vcfdeck

ROOT = HERE.parents[2]
SCHEMATIC = ROOT / 'kicad-working' / 'mainboard' / 'mainboard.kicad_sch'
OUTPUT = HERE / 'vcf-parts.json'
# The "(VCF)" section of the expanded BOM, kept in ../expanded-bom-review/.
VCF_BOM = ('R47 R61 R64 R65 R94 R96 R97 R109 R112 R115 R116 R95 R67 R68 R69 R70 R71 R98 R108 R124 R125 R126 '
           'R110 R111 R46 R66 R72 R73 R99 R113 R114 R62 R63 '
           'C19 C24 C26 C25 C27 C18 C13 C14 C15 C17 C22 C23 C29 C16 C30 C28 '
           'Q9 Q10 Q11 Q13 Q14 Q15 Q16 Q17 Q18 Q19 Q20 Q23 Q12 Q21 Q22 D24 TM3 VR3 VR5 VR4').split()


def tokens(text):
    return re.findall(r'"(?:[^"\\]|\\.)*"|\(|\)|[^\s()"]+', text)


def parse(items):
    stack, cur = [], []
    for t in items:
        if t == '(':
            stack.append(cur)
            cur = []
        elif t == ')':
            stack[-1].append(cur)
            cur = stack.pop()
        else:
            cur.append(t[1:-1] if t.startswith('"') else t)
    return cur[0]


def find(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def read_schematic():
    cli = os.environ.get('KICAD_CLI') or shutil.which('kicad-cli') or '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
    with tempfile.TemporaryDirectory() as d:
        net = Path(d) / 'mainboard.net'
        subprocess.run([cli, 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '--output', str(net), str(SCHEMATIC)], check=True, capture_output=True)
        tree = parse(tokens(net.read_text()))
    comps = {}
    for c in find(find(tree, 'components')[0], 'comp'):
        comps[find(c, 'ref')[0][1]] = dict(value=find(c, 'value')[0][1] if find(c, 'value') else '', pins={})
    for n in find(find(tree, 'nets')[0], 'net'):
        name = find(n, 'name')[0][1]
        for item in find(n, 'node'):
            ref, pin = find(item, 'ref')[0][1], find(item, 'pin')[0][1]
            func = find(item, 'pinfunction')[0][1] if find(item, 'pinfunction') else pin
            if ref in comps:
                comps[ref]['pins'][pin] = dict(net=name, func=func)
    wanted = sorted(set(vcfdeck.ALL_PARTS) | set(VCF_BOM))
    missing = [r for r in wanted if r not in comps]
    assert not missing, missing
    return {r: dict(value=comps[r]['value'], pins=dict(sorted(comps[r]['pins'].items()))) for r in wanted}


def check():
    """True if vcf-parts.json still describes the current schematic."""
    return json.loads(OUTPUT.read_text())['components'] == read_schematic()


if __name__ == '__main__':
    if '--check' in sys.argv:
        same = check()
        print('vcf-parts.json matches the schematic' if same else 'vcf-parts.json differs from the schematic')
        raise SystemExit(0 if same else 1)
    project = json.loads((ROOT / 'PROJECT.json').read_text())
    comps = read_schematic()
    OUTPUT.write_text(json.dumps(dict(source='kicad-working/mainboard/mainboard.kicad_sch', kicad_working_revision=project['kicad_working_revision'],
                                      vcf_bom_references=len(VCF_BOM), components=comps), indent=1) + '\n')
    print(len(comps), 'parts written;', len(VCF_BOM), 'of them on the expanded BOM VCF list')
