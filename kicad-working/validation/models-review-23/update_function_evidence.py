"""Carry the revision-22 DIN function evidence forward unchanged into revision 23.

Revision 23 changes only mainboard model paths (IC3, IC2 and their footprint caches); the
I/O inputs of the function proof are byte-identical, which this script asserts.
Run:  python3 -I kicad-working/validation/models-review-23/update_function_evidence.py
"""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[2]
evidence = json.loads((HERE.parent / 'models-review-22/current-function-source-evidence.json').read_text())
for row in evidence['core_inputs']:
    assert hashlib.sha256((REPO / row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
evidence['current_revision_note'] = ('Original Eagle records unchanged; KiCad23 changes only mainboard IC3/IC2 socket STEP paths; '
                                     'the I/O inputs are byte-identical to revision 22.')
(HERE / 'current-function-source-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
print(json.dumps({'passed': True, 'core_inputs': len(evidence['core_inputs'])}))
