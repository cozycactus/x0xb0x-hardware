"""Carry the original DIN function evidence forward to revision 17 (I/O PCB unchanged).

Writes current-function-source-evidence.json and current-function-verification.json.
The revision-15 evidence is carried forward with only the I/O PCB hash and size
updated, and only after installation-audit.json shows that file changed in model
nodes alone and its before-hash equals the revision-15 evidence. Use
verify_current_functions.py for the read-only replay.
"""
from pathlib import Path
import copy, hashlib, json, sys

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'kicad-working/validation/din-midi-review'))
from inspect_din_functions import verify  # noqa: E402

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
PCB = 'kicad-working/ioboard/ioboard.kicad_pcb'
previous = json.loads((HERE.parent / 'models-review-16/current-function-source-evidence.json').read_text())
install = json.loads((HERE / 'installation-audit.json').read_text())
old = next(r for r in previous['core_inputs'] if r['path'] == PCB)
assert install['passed']
# Revision 17 changes only the mainboard; the I/O PCB and the evidence carry over unchanged.
assert not any(r['file'] == 'ioboard/ioboard.kicad_pcb' for r in install['files'])
assert old['sha256'] == sha(REPO / PCB)
evidence = copy.deepcopy(previous)
evidence['current_revision_note'] = ('Original Eagle raw records and function graphs preserved; the I/O PCB is unchanged '
                                     'in revision 17 (mainboard-only model colour update).')
assert {k: v for k, v in evidence.items() if k not in ('core_inputs', 'current_revision_note')} == \
       {k: v for k, v in previous.items() if k not in ('core_inputs', 'current_revision_note')}
(HERE / 'current-function-source-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
result = verify(evidence)
result['scope'] = ('Original source function/raw-record proof replayed against current PCB. Only the revision-17 '
                   'STEP-path changes are separately validated by installation-audit.json; no circuit or physical '
                   'hardware claim.')
(HERE / 'current-function-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('passed', 'checks_count')}))
assert result['passed']
