"""Replay the original DIN function proof against the revision-28 I/O board.

Revision 28 redraws the schematic and relinks footprints; pcb-relink-record.json and verify_redraw.py show that nothing else
in the board file changed. update_function_evidence.py carries the source evidence forward with the new file hashes.
"""
from pathlib import Path
import json, sys

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'kicad-working/validation/din-midi-review'))
from inspect_din_functions import verify  # noqa: E402

evidence = json.loads((HERE / 'current-function-source-evidence.json').read_text())
result = verify(evidence)
result['scope'] = ('Original source function/raw-record proof replayed against the current PCB. Revision 28 changes only the '
                   'schematic and the footprint path lines of the board; no circuit or physical hardware claim.')
print(json.dumps(result, indent=2))
assert result['passed']
