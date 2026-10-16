#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Regenerate the KiCad fabrication outputs and compare them with the original Eagle 4.13 boards.

Exports Gerbers and Excellon drills for both boards with kicad-cli into a temporary
folder (the PCB files are only read), reads texts/zones/islands with KiCad's Python,
and writes, next to this script:
  gerber-comparison.json       layer-by-layer differences with locations
  connection-gap-review.json   the DRC connection gaps against the Eagle source and cables
  source-decode-crosscheck.json the staging XML against an independent read of original-eagle/

Inputs outside the repository (the conversion workspace, as for earlier conversion checks):
  X0X_EAGLE_XML    default ../kicad-import/validation/repaired-eagle-xml (staging XML of the binaries)
  X0X_EAGLE_PARSER default ~/cozycactus/kicad/common/io/eagle/eagle_bin_parser.cpp (record table)
Run from the repository root:  python3 -I kicad-working/validation/models-review-25/fabrication-comparison/run_comparison.py
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import compare  # noqa: E402
import connection_gaps  # noqa: E402
import source_crosscheck  # noqa: E402

REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
PY = os.environ.get('KICAD_PYTHON', '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
EAGLE = Path(compare.EAGLE)
PARSER = Path(os.environ.get('X0X_EAGLE_PARSER', Path.home() / 'cozycactus/kicad/common/io/eagle/eagle_bin_parser.cpp'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731

tmp = Path(tempfile.mkdtemp(prefix='x0xb0x-fab-'))
env = dict(os.environ, KICAD_CONFIG_HOME=str(tmp / 'config'), XDG_CACHE_HOME=str(tmp / 'cache'))
before = {b: sha(WORK / b / f'{b}.kicad_pcb') for b in ('mainboard', 'ioboard')}
commands = []
for b in ('mainboard', 'ioboard'):
    pcb, out = WORK / b / f'{b}.kicad_pcb', tmp / 'gerbers' / b
    out.mkdir(parents=True)
    for cmd in ([CLI, 'pcb', 'export', 'gerbers', '--board-plot-params', '-o', f'{out}/', str(pcb)],
                [CLI, 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th',
                 '--excellon-units', 'mm', '-o', f'{out}/', str(pcb)]):
        r = subprocess.run(cmd, capture_output=True, text=True, env=env)
        assert r.returncode == 0, r.stderr[-500:]
        commands.append([c.replace(str(tmp), '<temporary>').replace(str(WORK), '<kicad-working>') for c in cmd])
extract_path = tmp / 'extract.json'
r = subprocess.run([PY, str(HERE / 'kicad_extract.py'), str(WORK), str(extract_path)], capture_output=True, text=True, env=env)
assert r.returncode == 0, r.stderr[-800:]
extract = json.loads(extract_path.read_text())
assert before == {b: sha(WORK / b / f'{b}.kicad_pcb') for b in ('mainboard', 'ioboard')}

inputs = dict(kicad_cli=subprocess.check_output([CLI, '--version'], text=True, env=env).strip(),
              kicad_pcb_sha256=before,
              original_eagle_sha256={f: sha(REPO / 'original-eagle' / f) for f in ('mainboard.brd', 'ioboard.brd')},
              eagle_staging_xml_sha256={f: sha(EAGLE / f) for f in ('mainboard.brd', 'ioboard.brd')},
              eagle_parser_record_table_sha256=sha(PARSER), commands=commands)
report = compare.run(str(tmp / 'gerbers'), extract)
gerber_files = {b: {p.name: dict(bytes=p.stat().st_size) for p in sorted((tmp / 'gerbers' / b).iterdir())} for b in report}
(HERE / 'gerber-comparison.json').write_text(json.dumps(dict(inputs=inputs, generated_files=gerber_files, boards=report),
                                                       indent=1, default=list) + '\n')
drc = {b: json.loads((HERE.parent / f'{b}-drc.json').read_text()) for b in ('mainboard', 'ioboard')}
gaps = connection_gaps.run(extract, EAGLE, drc)
(HERE / 'connection-gap-review.json').write_text(json.dumps(dict(inputs=inputs, **gaps), indent=1, default=list) + '\n')
cross = source_crosscheck.run(REPO, EAGLE, PARSER)
(HERE / 'source-decode-crosscheck.json').write_text(json.dumps(dict(inputs=inputs, boards=cross), indent=1) + '\n')
print(json.dumps(dict(passed=all(v['passed'] for v in cross.values()), output=str(HERE.relative_to(REPO))), indent=1))
