"""Check the TL1100F colours in the native KiCad revision-17 export (read-only).

For all 23 placed TL1100F switches, every triangle with a vertex outside the 12 x 12 mm
housing outline (model frame) must use the terminal colour, and the triangle geometry
must equal the revision-16 export (colour-only change).

Run:
  Blender --background --factory-startup --python-exit-code 1 \
      --python kicad-working/validation/models-review-17/tl1100-colour/check_native_colours.py
"""
import hashlib
import json
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
TERMINAL = tuple(((c + .055) / 1.055) ** 2.4 for c in (.6, .61, .63))   # sRGB STEP colour as linear glTF base colour
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731


def triangles(glb_path, refs):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    base = next(o for o in bpy.data.objects if o.parent is None)
    roots = {o.name: o for o in base.children}
    out = {}
    for ref in refs:
        root = roots[ref]
        inv = np.array(root.matrix_world.inverted())
        rows = []
        for obj in root.children_recursive:
            if obj.type != 'MESH':
                continue
            m = inv @ np.array(obj.matrix_world)
            obj.data.calc_loop_triangles()
            co = np.array([v.co[:] for v in obj.data.vertices])
            co = (co @ m[:3, :3].T + m[:3, 3]) * 1000
            for t in obj.data.loop_triangles:
                mat = obj.data.materials[t.material_index]
                colour = tuple(mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value[:3])
                rows.append((tuple(np.round(co[list(t.vertices)], 4).ravel()), colour))
        out[ref] = sorted(rows)
    return out


refs = json.loads((REVIEW / 'installation-audit.json').read_text())['references']['TL1100F']
record = json.loads((REVIEW / 'native-export-record.json').read_text())
previous = json.loads((REVIEW.parent / 'models-review-16/native-export-record.json').read_text())
new = triangles(REVIEW / record['boards']['mainboard']['glb'], refs)
old = triangles(REVIEW.parent / 'models-review-16' / previous['boards']['mainboard']['glb'], refs)
checks, rows = [], {}


def close(a, b):
    return max(abs(x - y) for x, y in zip(a, b)) < 2e-3


for ref in refs:
    outside = [c for tri, c in new[ref] if np.max(np.abs(np.array(tri).reshape(3, 3)[:, :2])) > 6.0 + 1e-3]
    same_geometry = [t for t, _ in new[ref]] == [t for t, _ in old[ref]]
    recoloured = sum(1 for (t, a), (_, b) in zip(new[ref], old[ref]) if not close(a, b))
    rows[ref] = dict(triangles=len(new[ref]), outside_housing=len(outside), recoloured_triangles=recoloured)
    checks.append(dict(check=f'{ref}: triangles outside the housing are terminal metal; geometry unchanged',
                       passed=bool(outside) and all(close(c, TERMINAL) for c in outside) and same_geometry
                       and all(close(a, TERMINAL) for (t, a), (_, b) in zip(new[ref], old[ref]) if not close(a, b)),
                       **rows[ref]))
report = dict(schema=1, revision=17, generator='check_native_colours.py', passed=all(c['passed'] for c in checks),
              check_count=len(checks), checks=checks,
              glb_sha256={'revision17': sha(REVIEW / record['boards']['mainboard']['glb']),
                          'revision16': previous['boards']['mainboard']['glb_sha256']},
              read_only=True)
(HERE / 'tl1100-native-colour-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'check_count')}), rows[refs[0]])
if not report['passed']:
    raise SystemExit(1)
