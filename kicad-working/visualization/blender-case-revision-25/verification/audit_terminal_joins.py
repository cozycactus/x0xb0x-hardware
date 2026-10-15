"""Replay the repository terminal-join check and keep its report beside the scene."""
import json
import runpy
from pathlib import Path
HERE = Path(__file__).resolve().parent
namespace = runpy.run_path(str(HERE.parents[3] / 'scripts/verify_terminal_joins.py'))
report = namespace['result']
assert report['passed'] and report['references_checked'] == 25 and report['terminal_pieces'] == 133
(HERE / 'terminal-join-audit.json').write_text(json.dumps(report, indent=2) + '\n')
