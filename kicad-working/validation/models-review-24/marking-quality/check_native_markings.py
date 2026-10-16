"""Check the printed markings of the 17 ICs in the native KiCad revision-24 export (read-only).

For each reference: ink-coloured triangles exist, all lie in the 0.03 mm layer on the
chip top, and the inked area sits inside the chip's top outline; every other triangle
keeps a colour the reference already had in the revision-23 export.

Run:
  Blender --background --factory-startup --python-exit-code 1 \
      --python kicad-working/validation/models-review-24/marking-quality/check_native_markings.py
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
audit = json.loads((HERE / 'marking-model-audit.json').read_text())
INK = linear(audit['models']['74HC595']['ink'])


def triangles(review, board, refs):
    record = json.loads((review / 'native-export-record.json').read_text())
    glb = review / record['boards'][board]['glb']
    assert sha(glb) == record['boards'][board]['glb_sha256']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb))
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
            co = np.array([v.co[:] for v in obj.data.vertices])
            co = (co @ m[:3, :3].T + m[:3, 3]) * 1000
            obj.data.calc_loop_triangles()
            for t in obj.data.loop_triangles:
                c = np.array(obj.data.materials[t.material_index].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value[:3])
                rows.append((co[list(t.vertices)], c))
        out[ref] = rows
    return out, record['boards'][board]['glb_sha256']


checks, hashes = [], {}
for board in ('mainboard', 'ioboard'):
    refs = {r.split(':')[1]: k for k, m in audit['models'].items() for r in m['references'] if r.startswith(board)}
    new, hashes[board] = triangles(REVIEW, board, refs)
    old, _ = triangles(REVIEW.parent / 'models-review-23', board, refs)
    for ref, key in sorted(refs.items()):
        m = audit['models'][key]
        ink = [tri for tri, c in new[ref] if np.abs(c - INK).max() < 2e-3]
        other = {tuple(np.round(c, 4)) for tri, c in new[ref] if np.abs(c - INK).max() >= 2e-3}
        before = {tuple(np.round(c, 4)) for _, c in old[ref]}
        body = np.vstack([tri for tri, c in old[ref]])
        top = m['top_z_mm']
        zs = np.vstack(ink)[:, 2] if ink else np.zeros(0)
        near_top = body[np.abs(body[:, 2] - top) < 1e-3]
        lo, hi = near_top[:, :2].min(0), near_top[:, :2].max(0)
        xy = np.vstack(ink)[:, :2] if ink else np.zeros((0, 2))
        ok = (bool(ink) and zs.min() > top - 1e-3 and zs.max() < top + m['raise_mm'] + 1e-3 and other <= before and
              bool((xy >= lo - 1e-3).all() and (xy <= hi + 1e-3).all()))
        checks.append(dict(check=f'{board} {ref}: {" / ".join(m["lines"])} inked on the chip top; other colours unchanged',
                           passed=bool(ok), ink_triangles=len(ink), ink_z_mm=[round(float(zs.min()), 3), round(float(zs.max()), 3)] if ink else None))
report = dict(schema=1, revision=24, generator='check_native_markings.py', passed=all(c['passed'] for c in checks), check_count=len(checks),
              checks=checks, glb_sha256=hashes, read_only=True)
(HERE / 'marking-native-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'check_count')}))
for c in checks:
    if not c['passed']:
        print('FAIL', c)
if not report['passed']:
    raise SystemExit(1)
