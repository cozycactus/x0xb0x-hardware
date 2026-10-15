"""Check IC3 and IC2 in the native KiCad revision-23 export (read-only).

In each reference frame (Z up from the board top): the socket housing is black and
reaches 5.10 mm from the board up, the tin contacts run to 3.0 mm below it, the chip body tops out at 8.78 mm,
and the chip keeps its KiCad body and pin colours.

Run:
  Blender --background --factory-startup --python-exit-code 1 \
      --python kicad-working/validation/models-review-23/socket-quality/check_native_sockets.py
"""
import hashlib
import json
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
linear = lambda c: np.array([((v + .055) / 1.055) ** 2.4 for v in c])  # noqa: E731
audit = json.loads((HERE / 'socket-model-audit.json').read_text())
record = json.loads((REVIEW / 'native-export-record.json').read_text())
glb = REVIEW / record['boards']['mainboard']['glb']
assert sha(glb) == record['boards']['mainboard']['glb_sha256']
COLOUR = {'housing': linear(audit['models']['IC3']['colours']['housing']), 'tin': linear(audit['models']['IC3']['colours']['tails']),
          'chip body': linear((0.148, 0.145, 0.145)), 'chip pins': linear((0.824, 0.82, 0.781))}
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(glb))
base = next(o for o in bpy.data.objects if o.parent is None)
roots = {o.name: o for o in base.children}
checks, rows = [], {}
for ref, m in audit['models'].items():
    root = roots[ref]
    inv = np.array(root.matrix_world.inverted())
    z = {k: [] for k in COLOUR}
    unknown = 0
    for obj in root.children_recursive:
        if obj.type != 'MESH':
            continue
        mat = inv @ np.array(obj.matrix_world)
        co = np.array([v.co[:] for v in obj.data.vertices])
        co = (co @ mat[:3, :3].T + mat[:3, 3]) * 1000
        obj.data.calc_loop_triangles()
        for t in obj.data.loop_triangles:
            c = np.array(obj.data.materials[t.material_index].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value[:3])
            role = next((k for k, v in COLOUR.items() if np.abs(c - v).max() < 2e-3), None)
            if role is None:
                unknown += 1
                continue
            z[role] += list(co[list(t.vertices), 2])
    rows[ref] = {k: [round(min(v), 3), round(max(v), 3)] if v else None for k, v in z.items()}
    ok = (unknown == 0 and all(z.values()) and abs(max(z['housing']) - 5.10) < 2e-3 and min(z['housing']) >= -1e-3
          and abs(min(z['tin']) + 3.0) < 2e-3 and abs(max(z['chip body']) - m['chip_top_above_board_mm']) < 2e-3 and min(z['chip pins']) > 0)
    checks.append(dict(check=f'{ref}: black housing on the board up to 5.10 mm, tin contact tails to 3.0 mm below, chip seated on the socket', passed=bool(ok),
                       unknown_colour_triangles=unknown, z_ranges_mm=rows[ref]))
report = dict(schema=1, revision=23, generator='check_native_sockets.py', passed=all(c['passed'] for c in checks), check_count=len(checks),
              checks=checks, glb_sha256=record['boards']['mainboard']['glb_sha256'], read_only=True)
(HERE / 'socket-native-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'check_count')}), json.dumps(rows))
if not report['passed']:
    raise SystemExit(1)
