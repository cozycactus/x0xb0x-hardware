"""Replay the repository KiCad-vs-Blender model check against this loaded saved scene."""
import json
import runpy
from pathlib import Path
HERE = Path(__file__).resolve().parent
namespace = runpy.run_path(str(HERE.parents[3] / 'scripts/verify_kicad_blender_models.py'))
report = namespace['result']
assert report['passed'] and report['compared_references'] == report['identical_references'] == 491
(HERE / 'kicad-blender-models-audit.json').write_text(json.dumps(report, indent=2) + '\n')
