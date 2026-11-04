#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Run ERC and DRC on both adapter projects, export their fabrication files, read the exports back and write
verification.json. The mainboard is only read. Usage: python3 -I make_package.py [--check]
--check verifies the stored files against the projects without exporting anything."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
LAYERS = 'F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts'
PITCH = 2.286
# Pin roles at the mainboard, by pad number, from the schematic export the simulation uses
SITES = dict(ce=('Q12', 'Q21', 'Q26'), cb=('Q22',))
CHIP = {1: ('E', 1), 2: ('B', 1), 3: ('C', 2), 4: ('E', 2), 5: ('B', 2), 6: ('C', 1)}  # SOT-363 pins of BCM847BS
OTHER_CHIP = {1: ('E', 2), 2: ('B', 2), 3: ('C', 1), 4: ('E', 1), 5: ('B', 1), 6: ('C', 2)}  # onsemi BC847CDW1, style 1
ROW_ROLE = dict(ce='BCECB', cb='ECBCE')
checks = []


def check(name, ok, **info):
    checks.append(dict(name=name, passed=bool(ok), **info))
    print(('ok  ' if ok else 'FAIL'), name, info if not ok else '')


def run(*args):
    return subprocess.run([CLI, *map(str, args)], cwd=HERE, check=True, capture_output=True, text=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def erc_drc(v, out):
    prj = f'{v}/ssip5-{v}'
    run('sch', 'erc', '--severity-all', '--format', 'json', '-o', out / 'erc.json', prj + '.kicad_sch')
    run('pcb', 'drc', '--schematic-parity', '--severity-all', '--format', 'json', '-o', out / 'drc.json', prj + '.kicad_pcb')
    erc = json.loads((out / 'erc.json').read_text())
    drc = json.loads((out / 'drc.json').read_text())
    check(f'{v}: ERC has no finding', sum(len(s['violations']) for s in erc['sheets']) == 0)
    check(f'{v}: DRC has no violation, no unconnected item, no schematic mismatch', not drc['violations'] and not drc['unconnected_items'] and not drc['schematic_parity'])


def nets_from_netlist(v, tmp):
    path = tmp / f'{v}.net'
    run('sch', 'export', 'netlist', '-o', path, f'{v}/ssip5-{v}.kicad_sch')
    t = path.read_text()
    out = {}
    for m in re.finditer(r'\(net\s+\(code "\d+"\)\s+\(name "([^"]+)"\).*?(?=\(net\s+\(code|\Z)', t, re.S):
        for n in re.finditer(r'\(ref "(\w+)"\)\s+\(pin "(\d+)"\)', m[0]):
            out[(n[1], int(n[2]))] = m[1]
    return out


def electrical(v, tmp):
    """Walk from each mainboard pad through the adapter's row pin to the chip, and compare the role with the schematic of the mainboard."""
    nets = nets_from_netlist(v, tmp)
    parts = json.loads((WORK / 'validation/vcf-simulation/fullchain-parts.json').read_text())['components']
    for name, chip in (('BCM847BS', CHIP), ('BC847CDW1', OTHER_CHIP)):
        for site in SITES[v]:
            roles = {int(n): p['func'][0] for n, p in parts[site]['pins'].items()}
            good = True
            for pad, role in roles.items():
                net = nets[('J1', pad)]
                pins = [n for (ref, n), x in nets.items() if ref == 'Q1' and x == net]
                # Every chip pin on this row pin must have the role the mainboard expects there
                good &= bool(pins) and all(chip[n][0] == role for n in pins) and ROW_ROLE[v][pad - 1] == role
            # Pad pairs must stay with one transistor: base and collector on the same side of the row
            good &= {chip[n][1] for (ref, n), x in nets.items() if ref == 'Q1' and x in (nets[('J1', 1)], nets[('J1', 2)])} in ({1}, {2})
            check(f'{v}: {name} at {site}: every row pin reaches the chip pin the mainboard expects', good, roles=''.join(roles[i] for i in range(1, 6)))


def mainboard_row(site, text):
    i = text.index(f'(property "Reference" "{site}"')
    start = text.rfind('(footprint "', 0, i)
    block = text[start:text.find('\n\t(footprint "', i)]
    pads = re.findall(r'\(pad "(\d)" thru_hole \w+\s+\(at (-?[\d.]+) (-?[\d.]+)[^)]*\)\s+\(size ([\d.]+) ([\d.]+)\)\s+\(drill ([\d.]+)\)', block)
    return [(int(n), float(x), float(y), float(d)) for n, x, y, _, _, d in pads]


def gerbers(v, out):
    g = out / 'gerbers'
    if g.exists():
        shutil.rmtree(g)
    g.mkdir(parents=True)
    pcb = f'{v}/ssip5-{v}.kicad_pcb'
    run('pcb', 'export', 'gerbers', '--no-protel-ext', '--layers', LAYERS, '-o', f'{g}/', pcb)
    run('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '--excellon-units', 'mm', '--generate-report', '--report-path', g / f'ssip5-{v}-drill-report.txt', '-o', f'{g}/', pcb)
    files = sorted(p for p in g.iterdir() if p.is_file())
    with zipfile.ZipFile(out / f'x0xb0x-ssip5-{v}-fabrication.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.writestr(zipfile.ZipInfo(f.name, (2026, 11, 4, 0, 0, 0)), f.read_bytes(), zipfile.ZIP_DEFLATED)
    return files


def drill_hits(path):
    tools, hits, tool = {}, [], None
    for line in Path(path).read_text().splitlines():
        if m := re.fullmatch(r'T(\d+)C([\d.]+)', line):
            tools[m[1]] = float(m[2])
        elif m := re.fullmatch(r'T(\d+)', line):
            tool = m[1]
        elif m := re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)', line):
            hits.append((float(m[1]), float(m[2]), tools[tool]))
    return hits


def read_back(v, out, main_text):
    g = out / 'gerbers'
    prefix = f'ssip5-{v}'
    pth = drill_hits(g / f'{prefix}-PTH.drl')
    row = sorted(h for h in pth if abs(h[2] - 0.8) < 1e-6)
    vias = [h for h in pth if abs(h[2] - 0.3) < 1e-6]
    check(f'{v}: drill file has 5 row holes of 0.8 mm and 2 vias of 0.3 mm', len(row) == 5 and len(vias) == 2 and len(pth) == 7)
    spacing = [round(b[0] - a[0], 3) for a, b in zip(row, row[1:])]
    check(f'{v}: row holes read back at {PITCH} mm on one line', all(abs(s - PITCH) < 0.002 for s in spacing) and len({h[1] for h in row}) == 1, spacing=spacing)
    for site in SITES[v]:
        pads = sorted(mainboard_row(site, main_text))
        d = [abs(((pads[i + 1][1] - pads[i][1]) ** 2 + (pads[i + 1][2] - pads[i][2]) ** 2) ** 0.5 - s) for i, s in enumerate(spacing)]
        check(f'{v}: row spacing equals the mainboard holes at {site}', len(pads) == 5 and max(d) < 0.002 and all(p[3] == 1.0 for p in pads), worst_mm=round(max(d), 4))
    # The long pad must run from the hole toward the bottom edge: read it from the plotted copper
    text = (g / f'{prefix}-F_Cu.gbr').read_text()
    fmt = re.search(r'%FSLAX(\d)(\d)Y', text)
    scale = 10 ** int(fmt[2])
    apertures = dict(re.findall(r'%ADD(\d+)([^*]*)\*%', text))
    current, flashes = None, []
    for m in re.finditer(r'D(\d+)\*|X(-?\d+)Y(-?\d+)D03\*', text):
        if m[1]:
            current = m[1]
        else:
            flashes.append((int(m[2]) / scale, int(m[3]) / scale, apertures[current]))
    oval = sorted(f for f in flashes if f[2].startswith('O,'))
    check(f'{v}: 5 oval pads of 1.5 x 3.2 mm are plotted', len(oval) == 5 and all(f[2].startswith('O,1.5') and 'X3.2' in f[2] for f in oval), found=[f[2] for f in oval][:2])
    edge = (g / f'{prefix}-Edge_Cuts.gbr').read_text()
    ys = [int(y) / scale for y in re.findall(r'Y(-?\d+)D0[12]', edge)]
    xs = [int(x) / scale for x in re.findall(r'X(-?\d+)Y-?\d+D0[12]', edge)]
    bottom = min(ys)  # plotted Y grows upward, so the board's bottom edge has the smallest Y
    pad_low = oval[0][1] - 1.6
    hole_y = row[0][1]
    check(f'{v}: pads stop 0.35 mm from the bottom edge, with the hook hole near their top', abs(pad_low - bottom - 0.35) < 0.01 and abs(hole_y - bottom - 2.75) < 0.01, pad_low_above_edge=round(pad_low - bottom, 3), hole_above_edge=round(hole_y - bottom, 3))
    check(f'{v}: outline is 11.4 x 7.8 mm', abs(max(xs) - min(xs) - 11.4) < 0.01 and abs(max(ys) - min(ys) - 7.8) < 0.01, size=[round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3)])


def main():
    only_check = '--check' in sys.argv
    main_text = (WORK / 'mainboard/mainboard.kicad_pcb').read_text()
    summary = json.loads((WORK / 'validation/working-validation-summary-revision-27.json').read_text())
    check('Mainboard board and schematic are the recorded revision 27 files', all(sha(WORK / n) == summary['outputs'][n] for n in ('mainboard/mainboard.kicad_pcb', 'mainboard/mainboard.kicad_sch')))
    record = dict(kicad_cli=run('--version').stdout.strip(), checks=checks, inputs={}, files={})
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        for v in SITES:
            out = HERE / 'fabrication' / v
            out.mkdir(parents=True, exist_ok=True)
            erc_drc(v, tmp if only_check else out)
            electrical(v, tmp)
            if not only_check:
                gerbers(v, out)
            read_back(v, out, main_text)
    for p in sorted(HERE.rglob('*')):
        rel = p.relative_to(HERE).as_posix()
        if p.is_file() and p.suffix in ('.kicad_pcb', '.kicad_sch', '.kicad_pro', '.kicad_mod'):
            record['inputs'][rel] = sha(p)
        elif p.is_file() and rel.startswith('fabrication/') and '/gerbers/' in rel:
            record['files'][rel] = sha(p)
    fit = json.loads((HERE / 'fit-check.json').read_text())
    check('Fit check found at least 0.3 mm at every site', fit['passed'] and set(fit['sites']) == {'Q12', 'Q21', 'Q22', 'Q26'}, smallest={k: s['smallest_gap_mm'] for k, s in fit['sites'].items()})
    record['passed'] = all(c['passed'] for c in checks)
    record['scope'] = 'Design checks only: nothing has been built or measured.'
    # Gerber files carry their creation time, so a fresh export changes these hashes and nothing else
    if only_check:
        stored = json.loads((HERE / 'verification.json').read_text())
        check('Project files match the recorded hashes', stored['inputs'] == record['inputs'])
        check('Fabrication files match the recorded hashes', stored['files'] == record['files'])
        record['passed'] = all(c['passed'] for c in checks)
    else:
        (HERE / 'verification.json').write_text(json.dumps(record, indent=1) + '\n')
    print('PASSED' if record['passed'] else 'FAILED', sum(c['passed'] for c in checks), 'of', len(checks))
    raise SystemExit(0 if record['passed'] else 1)


if __name__ == '__main__':
    main()
