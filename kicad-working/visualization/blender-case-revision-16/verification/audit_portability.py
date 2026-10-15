"""Replay the repository portability verifier against this loaded saved scene."""
import json
import runpy
from pathlib import Path
HERE = Path(__file__).resolve().parent
namespace = runpy.run_path(str(HERE.parents[3] / 'scripts/verify_blender_scene.py'))
report = namespace['result']
assert report['passed'] and report['check_count'] == 106
(HERE / 'portable-scene-audit.json').write_text(json.dumps(report, indent=2) + '\n')
