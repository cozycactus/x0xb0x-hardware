"""Check the electrolytic colours in the native KiCad revision-21 export (read-only).

For all 39 XRL references, every triangle must carry one of the four STEP colours
(sleeve, negative stripe, top metal, leads) as KiCad's linear glTF base colour, the
sleeve and stripe must be present, and stripe triangles must lie on the negative-pad
side of the can axis in the footprint frame.

Run:
  Blender --background --factory-startup --python-exit-code 1 \
      --python kicad-working/validation/models-review-21/electrolytic-quality/check_native_colours.py
"""
import hashlib
import json
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
linear = lambda c: tuple(((v + .055) / 1.055) ** 2.4 for v in c)  # noqa: E731
audit = json.loads((HERE / 'electrolytic-model-audit.json').read_text())
record = json.loads((REVIEW / 'native-export-record.json').read_text())
colours = audit['models']['XRL_D5']['colours']
EXPECTED = {role: linear(colours[role]) for role in ('Sleeve', 'NegativeStripe', 'TopMetal', 'Leads')}
REFS = {'mainboard': {}, 'ioboard': {}}
for key, model in audit['models'].items():
    for item in model['references']:
        board, ref = item.split(':')
        REFS[board][ref] = (key, -model['dimensions_mm']['board_pitch'] / 2, model['dimensions_mm']['board_pitch'] / 2)
for name, item in audit['recoloured'].items():
    for ref in item['references']:
        REFS[item['board']][ref] = (name, None, None)
assert sum(len(v) for v in REFS.values()) == 39


def role_of(colour):
    for role, value in EXPECTED.items():
        if max(abs(a - b) for a, b in zip(colour, value)) < 2e-3:
            return role
    return None


checks, rows = [], {}
for board, refs in REFS.items():
    glb = REVIEW / record['boards'][board]['glb']
    assert sha(glb) == record['boards'][board]['glb_sha256']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    base = next(o for o in bpy.data.objects if o.parent is None)
    roots = {o.name: o for o in base.children}
    for ref, (key, _, _) in sorted(refs.items()):
        root = roots[ref]
        inv = np.array(root.matrix_world.inverted())
        counts, stripe_x = {}, []
        unknown = 0
        for obj in root.children_recursive:
            if obj.type != 'MESH':
                continue
            m = inv @ np.array(obj.matrix_world)
            co = np.array([v.co[:] for v in obj.data.vertices])
            co = (co @ m[:3, :3].T + m[:3, 3]) * 1000
            obj.data.calc_loop_triangles()
            for t in obj.data.loop_triangles:
                mat = obj.data.materials[t.material_index]
                role = role_of(tuple(mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value[:3]))
                if role is None:
                    unknown += 1
                    continue
                counts[role] = counts.get(role, 0) + 1
                if role == 'NegativeStripe':
                    stripe_x.append(co[list(t.vertices)][:, 0].mean())
        # The negative pad is at +X in every E5-6/E5-5/E3,5-8/E5-13 footprint frame.
        rows[f'{board}:{ref}'] = dict(model=key, triangles=counts, unknown_colour_triangles=unknown,
                                      stripe_min_x_mm=round(float(min(stripe_x)), 4) if stripe_x else None)
        checks.append(dict(check=f'{board} {ref}: only XRL colours; sleeve, stripe, top and leads present; stripe on the negative side',
                           passed=bool(unknown == 0 and set(counts) == set(EXPECTED) and stripe_x and min(stripe_x) > 0),
                           **rows[f'{board}:{ref}']))
report = dict(schema=1, revision=21, generator='check_native_colours.py', passed=all(c['passed'] for c in checks),
              check_count=len(checks), checks=checks, expected_linear_colours=EXPECTED,
              glb_sha256={b: record['boards'][b]['glb_sha256'] for b in REFS}, read_only=True)
(HERE / 'electrolytic-native-colour-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'check_count')}))
for c in checks:
    if not c['passed']:
        print('FAIL', c)
if not report['passed']:
    raise SystemExit(1)
