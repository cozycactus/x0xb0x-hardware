"""Read-only native Blender regression: electrical DIN functions vs FONT text.

Load any saved scene in this repository and run with --python-exit-code 1.
JSON is printed to stdout, without saving the scene or changing its frame.
"""
import json
import sys
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from derive_midi_functions import derive, verify_original_evidence, sha


def verify():
    source = Path(bpy.data.filepath).resolve()
    digest = sha(source)
    connectivity = derive()
    evidence = json.loads((HERE / 'midi-connectivity-evidence.json').read_text())
    original = verify_original_evidence(connectivity, evidence)
    checks = []
    for ref, function in connectivity['functions'].items():
        label = bpy.data.objects.get(ref + ' label')
        body = label.data.body if label and label.type == 'FONT' else None
        checks.append(dict(reference=ref, object=ref + ' label',
            expected=function['expected_legend'], actual=body,
            passed=body == function['expected_legend'],
            electrical_function=function['function'],
            connectivity_evidence=function['evidence']))
    unchanged = sha(source) == digest
    return dict(passed=all(c['passed'] for c in checks) and unchanged,
        check_count=len(checks), failures=[c for c in checks if not c['passed']],
        scene_sha256=digest, pcb_sha256=connectivity['pcb_sha256'],
        original_eagle_sha256=connectivity['eagle_sha256'],
        original_connected_pad_comparison=original, checks=checks,
        read_only=unchanged, physical_fit_qualified=False,
        method=connectivity['method'])


if __name__ == '__main__':
    result = verify()
    print(json.dumps(result, indent=2))
    assert result['passed'], 'DIN legend text disagrees with electrical function'
