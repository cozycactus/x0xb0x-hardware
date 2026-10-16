"""Carry the revision-23 DIN function evidence forward with the revision-24 I/O PCB hash.

Only the ioboard.kicad_pcb core-input row changes (model paths of IC23, IC24 and IC25); installation-audit.json proves that no other PCB node changed.
Run:  python3 -I kicad-working/validation/models-review-24/update_function_evidence.py
"""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[2]
evidence = json.loads((HERE.parent / 'models-review-23/current-function-source-evidence.json').read_text())
install = json.loads((HERE / 'installation-audit.json').read_text())
assert install['passed'] and 'ioboard/ioboard.kicad_pcb' in install['changed_previous_core_files']
for row in evidence['core_inputs']:
    path = REPO / row['path']
    if row['path'] == 'kicad-working/ioboard/ioboard.kicad_pcb':
        row.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], row['path']
evidence['current_revision_note'] = ('Original Eagle records unchanged; KiCad24 I/O differs only in the marked IC23, IC24 and IC25 '
                                     'STEP paths, validated by installation-audit.json.')
(HERE / 'current-function-source-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
print(json.dumps({'passed': True, 'core_inputs': len(evidence['core_inputs'])}))
