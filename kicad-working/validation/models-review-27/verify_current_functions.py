"""Replay the original DIN function proof against the revision-27 I/O board.

Revision 27 moves four I/O rear-plate datum lines off Edge.Cuts only; the source evidence is
carried forward with the new I/O PCB hash by update_function_evidence.py.
"""
from pathlib import Path
import json, sys

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'kicad-working/validation/din-midi-review'))
from inspect_din_functions import verify  # noqa: E402

evidence = json.loads((HERE / 'current-function-source-evidence.json').read_text())
result = verify(evidence)
result['scope'] = ('Original source function/raw-record proof replayed against current PCB. Revision 27 changes only '
                   'the layer of four rear-plate datum lines on the I/O board and the saved pour fill on the mainboard, '
                   'validated by installation-audit.json; no circuit or physical hardware claim.')
print(json.dumps(result, indent=2))
assert result['passed']
