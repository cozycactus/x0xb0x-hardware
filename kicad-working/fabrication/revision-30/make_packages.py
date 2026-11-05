#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Export the fabrication packages of both boards from the KiCad working revision named by this folder.

For each board, kicad-cli writes into <board>/gerbers/ (the PCB files are only read):
  Gerbers of all layers selected in the board plot settings (copper, mask, paste,
  silkscreen, outline) with X2 attributes and the Gerber job file; Excellon drills
  with PTH and NPTH in separate files, metric; drill maps (PDF) and the drill report.
Into <board>/assembly/: the component position file (CSV, mm, both sides) and a BOM
keyed by reference (schematic values joined with the PCB footprints).
Each <board>/gerbers/ folder is then zipped (fixed timestamps, sorted names) to
<board>/x0xb0x-<board>-rev<N>-fabrication.zip; ZIPs are excluded from Git and are
reproduced byte for byte from the tracked files by this script's zip step alone:
  make_packages.py --zip-only
package-record.json records the commands, inputs, file hashes and kicad-cli statistics.
Run from the repository root:  python3 -I kicad-working/fabrication/revision-<N>/make_packages.py
"""
import csv
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
WORK = REPO / 'kicad-working'
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
PY = os.environ.get('KICAD_PYTHON', '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
BOARDS = ('mainboard', 'ioboard')
REV = int(HERE.name.split('-')[-1])
ZIP_TIME = (2026, 10, 17, 0, 0, 0)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731


def zip_name(b):
    return HERE / b / f'x0xb0x-{b}-rev{REV}-fabrication.zip'


def write_zip(b):
    src = HERE / b / 'gerbers'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for p in sorted(src.iterdir()):
            info = zipfile.ZipInfo(p.name, date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, p.read_bytes(), compresslevel=9)
    zip_name(b).write_bytes(buf.getvalue())
    return dict(file=zip_name(b).name, bytes=len(buf.getvalue()), sha256=sha(zip_name(b)),
                members=sorted(p.name for p in src.iterdir()))


if '--zip-only' in sys.argv:
    print(json.dumps({b: write_zip(b) for b in BOARDS}, indent=1))
    raise SystemExit(0)

tmp = Path(tempfile.mkdtemp(prefix='x0xb0x-package-'))
env = dict(os.environ, KICAD_CONFIG_HOME=str(tmp / 'config'), XDG_CACHE_HOME=str(tmp / 'cache'))
inputs = {b: {f'{b}.kicad_pcb': sha(WORK / b / f'{b}.kicad_pcb'), f'{b}.kicad_sch': sha(WORK / b / f'{b}.kicad_sch'),
              f'{b}.kicad_pro': sha(WORK / b / f'{b}.kicad_pro')} for b in BOARDS}


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, env=env)
    assert r.returncode == 0, (cmd, r.stdout[-500:], r.stderr[-800:])
    return [str(c).replace(str(tmp), '<temporary>').replace(str(REPO) + '/', '') for c in cmd]


def bom_rows(b, extract, sch_csv):
    sch = {r['Refs']: r for r in csv.DictReader(open(sch_csv, newline=''))}
    rows = []
    for fp in sorted(extract['footprints'], key=lambda f: (f['ref'].rstrip('0123456789'), len(f['ref']), f['ref'])):
        s = sch.get(fp['ref'])
        mount = '+'.join(fp['pad_kinds']) or 'none'
        printed = [t for t in fp['printed'] if not t.isdigit()]
        notes = []
        if s is None:
            notes.append('PCB only (no schematic symbol)')
        if mount == 'NPTH':
            notes.append('mounting hole, nothing to fit')
        if printed and not fp['reference_visible']:
            notes.append(f'silkscreen prints {printed[0]}')
        rows.append(dict(Reference=fp['ref'], Printed=printed[0] if printed and not fp['reference_visible'] else fp['ref'],
                         Value=(s or {}).get('Value', fp['value']), Footprint=fp['footprint'], Side=fp['side'],
                         Mount=mount, DNP='yes' if fp['dnp'] or (s and s['DNP']) else '', Note='; '.join(notes)))
    missing = sorted(set(sch) - {f['ref'] for f in extract['footprints']})
    for ref in missing:
        rows.append(dict(Reference=ref, Printed='', Value=sch[ref]['Value'], Footprint=sch[ref]['Footprint'],
                         Side='', Mount='', DNP=sch[ref]['DNP'], Note='schematic only (no PCB footprint)'))
    return rows, missing


commands, record = [], dict(schema=1, KiCad_revision=REV, kicad_cli=None, inputs=inputs, boards={})
record['kicad_cli'] = subprocess.check_output([CLI, '--version'], text=True, env=env).strip()
for b in BOARDS:
    pcb, sch = WORK / b / f'{b}.kicad_pcb', WORK / b / f'{b}.kicad_sch'
    gerbers, assembly = HERE / b / 'gerbers', HERE / b / 'assembly'
    for d in (gerbers, assembly):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    commands.append(run([CLI, 'pcb', 'export', 'gerbers', '--board-plot-params', '-o', f'{gerbers}/', pcb]))
    commands.append(run([CLI, 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th',
                         '--excellon-units', 'mm', '--generate-map', '--map-format', 'pdf', '--generate-report',
                         '--report-path', gerbers / f'{b}-drill-report.txt', '-o', f'{gerbers}/', pcb]))
    commands.append(run([CLI, 'pcb', 'export', 'pos', '--side', 'both', '--format', 'csv', '--units', 'mm',
                         '-o', assembly / f'{b}-positions.csv', pcb]))
    commands.append(run([CLI, 'pcb', 'export', 'stats', '--format', 'json', '--units', 'mm',
                         '-o', tmp / f'{b}-stats.json', pcb]))
    commands.append(run([CLI, 'sch', 'export', 'bom', '--fields', 'Reference,Value,Footprint,${DNP}',
                         '--labels', 'Refs,Value,Footprint,DNP', '--ref-range-delimiter', '',
                         '-o', tmp / f'{b}-sch-bom.csv', sch]))
    commands.append(run([PY, '-I', HERE / 'extract_board.py', pcb, tmp / f'{b}-extract.json']))
    extract = json.loads((tmp / f'{b}-extract.json').read_text())
    rows, sch_only = bom_rows(b, extract, tmp / f'{b}-sch-bom.csv')
    with open(assembly / f'{b}-bom.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    stats = json.loads((tmp / f'{b}-stats.json').read_text())
    files = {str(p.relative_to(HERE / b)): dict(bytes=p.stat().st_size, sha256=sha(p))
             for d in (gerbers, assembly) for p in sorted(d.iterdir())}
    record['boards'][b] = dict(files=files, zip=write_zip(b), kicad_cli_stats=stats,
                               bom=dict(rows=len(rows), schematic_only=sch_only,
                                        pcb_only=[r['Reference'] for r in rows if r['Note'].startswith('PCB only')]))
record['commands'] = commands
after = {b: {f'{b}.kicad_pcb': sha(WORK / b / f'{b}.kicad_pcb'), f'{b}.kicad_sch': sha(WORK / b / f'{b}.kicad_sch'),
             f'{b}.kicad_pro': sha(WORK / b / f'{b}.kicad_pro')} for b in BOARDS}
assert after == inputs, 'a KiCad project file changed during export'
(HERE / 'package-record.json').write_text(json.dumps(record, indent=1) + '\n')
shutil.rmtree(tmp)
print(json.dumps({b: dict(files=len(v['files']), zip=v['zip']['sha256'][:12], bom_rows=v['bom']['rows'])
                  for b, v in record['boards'].items()}, indent=1))
