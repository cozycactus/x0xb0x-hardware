"""Replay the original DIN function proof against the revision-25 I/O board.

Revision 25 leaves every I/O project file unchanged, so the revision-24 source
evidence (which pins the I/O PCB and schematic hashes) applies as is.
"""
from pathlib import Path
import json, sys

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'kicad-working/validation/din-midi-review'))
from inspect_din_functions import verify  # noqa: E402

evidence = json.loads((HERE.parent / 'models-review-24/current-function-source-evidence.json').read_text())
result = verify(evidence)
result['scope'] = ('Original source function/raw-record proof replayed against current PCB. Revision 25 changes no '
                   'I/O file; the mainboard change is footprint jumper metadata, validated by installation-audit.json; '
                   'no circuit or physical hardware claim.')
print(json.dumps(result, indent=2))
assert result['passed']
