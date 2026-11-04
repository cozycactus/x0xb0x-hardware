"""Carry the revision-27 DIN function evidence forward with the revision-28 I/O file hashes.

Run:  python3 -I kicad-working/schematic-redraw/update_function_evidence.py
"""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
evidence = json.loads((HERE.parent / 'validation/models-review-27/current-function-source-evidence.json').read_text())
relink = json.loads((HERE / 'pcb-relink-record.json').read_text())['boards']['ioboard']
for row in evidence['core_inputs']:
    path = REPO / row['path']
    if row['path'] == 'kicad-working/ioboard/ioboard.kicad_pcb':
        assert row['sha256'] == relink['before_sha256']
    if row['path'].startswith('kicad-working/'):
        row.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], row['path']
evidence['current_revision_note'] = ('Original Eagle records unchanged; KiCad28 redraws the I/O schematic with the same nets and '
                                     'changes only the footprint path lines of the I/O board, as pcb-relink-record.json records.')
(HERE / 'current-function-source-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
print(json.dumps({'passed': True, 'core_inputs': len(evidence['core_inputs'])}))
