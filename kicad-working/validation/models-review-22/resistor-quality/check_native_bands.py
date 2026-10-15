"""Read the colour bands of all 212 resistors back from the native KiCad revision-22 export.

For each reference, triangles are grouped by colour: body, leads and band colours.
Band triangles are grouped by touching axial extents along the body axis (upright: Z, first band at the top;
lying: X, first band at the pad-1 end) and the clusters' colours must read the
assigned band sequence. Body colour must be tan (5%) or light blue (1%).

Run:
  Blender --background --factory-startup --python-exit-code 1 \
      --python kicad-working/validation/models-review-22/resistor-quality/check_native_bands.py
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
audit = json.loads((HERE / 'resistor-model-audit.json').read_text())
assign = json.loads((HERE / 'sources/resistor-band-assignments.json').read_text())['assignments']
record = json.loads((REVIEW / 'native-export-record.json').read_text())
COLOURS = {k: linear(v) for k, v in audit['colours'].items()}
BODY = {k: linear(v) for k, v in audit['body_colours'].items()}
LEAD = linear(audit['lead_colour'])


def name_of(c):
    for table in (COLOURS, {'body ' + k: v for k, v in BODY.items()}, {'lead': LEAD}):
        for k, v in table.items():
            if np.abs(c - v).max() < 2e-3:
                return k
    return None


checks, rows = [], {}
for board in ('mainboard', 'ioboard'):
    glb = REVIEW / record['boards'][board]['glb']
    assert sha(glb) == record['boards'][board]['glb_sha256']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    base = next(o for o in bpy.data.objects if o.parent is None)
    roots = {o.name: o for o in base.children}
    for ref, a in sorted(assign.items()):
        if a['board'] != board:
            continue
        root = roots[ref]
        inv = np.array(root.matrix_world.inverted())
        upright = a['footprint'] in ('0207_5V', '0207_2V')
        bands, names = [], set()
        for obj in root.children_recursive:
            if obj.type != 'MESH':
                continue
            m = inv @ np.array(obj.matrix_world)
            co = np.array([v.co[:] for v in obj.data.vertices])
            co = (co @ m[:3, :3].T + m[:3, 3]) * 1000
            obj.data.calc_loop_triangles()
            for t in obj.data.loop_triangles:
                c = np.array(obj.data.materials[t.material_index].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value[:3])
                n = name_of(c)
                names.add(n)
                if n in COLOURS:
                    axial = -co[list(t.vertices), 2] if upright else co[list(t.vertices), 0]
                    bands.append((axial.min(), axial.max(), n))
        # Merge triangles whose axial extents touch: one group per band (bands are >= 0.3 mm apart).
        bands.sort()
        clusters = []
        for lo, hi, n in bands:
            if clusters and lo <= clusters[-1][1] + 0.01:
                clusters[-1][1] = max(clusters[-1][1], hi)
                clusters[-1][2].add(n)
            else:
                clusters.append([lo, hi, {n}])
        read = [sorted(c[2]) for c in clusters]
        ok = (None not in names and f'body {a["tolerance"]}' in names and 'lead' in names and
              all(len(r) == 1 for r in read) and [r[0] for r in read] == a['bands'])
        rows[f'{board}:{ref}'] = dict(read=[r[0] if len(r) == 1 else r for r in read], expected=a['bands'],
                                      body=f'body {a["tolerance"]}' in names)
        checks.append(dict(check=f'{board} {ref}: native bands read {"-".join(a["bands"])} on a {a["tolerance"]} body', passed=bool(ok),
                           read=rows[f'{board}:{ref}']['read']))
report = dict(schema=1, revision=22, generator='check_native_bands.py', passed=all(c['passed'] for c in checks), check_count=len(checks),
              checks=checks, glb_sha256={b: record['boards'][b]['glb_sha256'] for b in ('mainboard', 'ioboard')}, read_only=True)
(HERE / 'resistor-native-band-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'check_count')}))
for c in checks:
    if not c['passed']:
        print('FAIL', c)
if not report['passed']:
    raise SystemExit(1)
