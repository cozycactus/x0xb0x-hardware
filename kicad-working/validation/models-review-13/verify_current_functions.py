"""Replay original DIN function proof against the current revision-13 model-only PCB update."""
from pathlib import Path
import json, sys

HERE = Path(__file__).resolve().parent; REPO = HERE.parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / 'kicad-working/validation/din-midi-review'))
from inspect_din_functions import verify  # noqa: E402

evidence = json.loads((HERE / 'current-function-source-evidence.json').read_text())
result = verify(evidence)
result['scope'] = ('Original source function/raw-record proof replayed against current PCB. Only the revision-13 '
                   'STEP-path changes are separately validated by installation-audit.json; no circuit or physical '
                   'hardware claim.')
print(json.dumps(result, indent=2))
assert result['passed']
