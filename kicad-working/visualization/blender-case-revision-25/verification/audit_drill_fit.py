"""Measure all native-model terminals against current PCB drills."""
import json,runpy
from pathlib import Path
HERE=Path(__file__).resolve().parent
report=runpy.run_path(str(HERE.parents[3]/'scripts/verify_drill_fit.py'))['result']
assert report['passed'] and report['measured_models']==489
(HERE/'drill-fit-audit.json').write_text(json.dumps(report,indent=2)+'\n')
