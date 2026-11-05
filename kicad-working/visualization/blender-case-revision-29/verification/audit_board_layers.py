"""Check the saved mainboard layer meshes against a fresh KiCad export and the PCB file (read-only).

The shared model check leaves the board substrate out, so this one covers it. It re-exports the
layers with the options in the change record and compares each saved mesh with its export: vertices,
triangles, bounds and surface area. From the PCB file it then checks that every chip land has pad
geometry over it, that the do-not-place TO-92 JFETs keep their pads, and that a via stands at each of the
board's via positions. Nothing is written but this report.
"""
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np

H = Path(__file__).resolve().parent
R = H.parent
REPO = H.parents[3]
sys.path.insert(0, str(REPO / 'kicad-import/validation'))
sys.dont_write_bytecode = True
from verify_native_projects import children, one, parse_sexpr, property_value  # noqa: E402

record = json.loads((R / 'revision-29-change-record.json').read_text())
PCB = REPO / record['pcb']
FINAL = R / 'x0xb0x-populated-with-case.blend'
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
assert Path(bpy.data.filepath).resolve() == FINAL.resolve()
scene_hash, pcb_hash = sha(FINAL), sha(PCB)
checks = []


def check(name, passed, **details):
    checks.append(dict(check=name, passed=bool(passed), **details))


def geometry(obj):
    co = np.empty(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', co)
    m = np.array(obj.matrix_world)
    world = (co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]) * 1000
    obj.data.calc_loop_triangles()
    tri = np.empty(len(obj.data.loop_triangles) * 3, dtype=np.int64)
    obj.data.loop_triangles.foreach_get('vertices', tri)
    tri = tri.reshape(-1, 3)
    area = float(np.linalg.norm(np.cross(world[tri[:, 1]] - world[tri[:, 0]], world[tri[:, 2]] - world[tri[:, 0]]), axis=1).sum() / 2)
    return world, dict(vertices=len(world), triangles=len(tri), area_mm2=area, lo=world.min(0).tolist(), hi=world.max(0).tolist())


saved, world_of = {}, {}
for name in record['layer_changes']:
    world_of[name], saved[name] = geometry(bpy.data.objects[name])

tree = parse_sexpr(PCB.read_text(encoding='utf-8'))
atoms = lambda node: [x for x in node[1:] if not isinstance(x, list)]  # noqa: E731
pads, jfet_pads = {}, {}
for fp in children(tree, 'footprint'):
    ref = property_value(fp, 'Reference', 'reference')
    if ref not in {*(v['reference'] for v in record['added_references'].values()),
                   *(v['reference'] for v in record['removed_do_not_place_references'].values())}:
        continue
    at = atoms(one(fp, 'at'))
    fx, fy = float(at[0]), float(at[1])
    angle = math.radians(float(at[2]) if len(at) > 2 else 0.0)
    rows = []
    for pad in children(fp, 'pad'):
        pa = atoms(one(pad, 'at'))
        px, py = float(pa[0]), float(pa[1])
        rows.append(dict(number=str(pad[1]), x_mm=fx + px * math.cos(angle) + py * math.sin(angle), y_mm=fy - px * math.sin(angle) + py * math.cos(angle)))
    (pads if pad[2] == 'smd' else jfet_pads)[ref] = rows
vias = [atoms(one(v, 'at')) for v in children(tree, 'via')]
vias = [(float(a[0]), -float(a[1])) for a in vias]


def near(world, x, y, reach):
    return int((np.hypot(world[:, 0] - x, world[:, 1] - y) < reach).sum())


pad_world, via_world = world_of['MAINBOARD/PCB layers/mesh.001'], world_of['MAINBOARD/PCB layers/mesh.002']
land_rows = {f'{r}.{p["number"]}': near(pad_world, p['x_mm'], -p['y_mm'], 0.6) for r, rows in pads.items() for p in rows}
jfet_rows = {f'{r}.{p["number"]}': near(pad_world, p['x_mm'], -p['y_mm'], 0.9) for r, rows in jfet_pads.items() for p in rows}
via_rows = {f'{x:.3f},{y:.3f}': near(via_world, x, y, 0.45) for x, y in vias}
check('All 6 chip lands have pad geometry in the saved mesh', len(land_rows) == 6 and all(land_rows.values()), lands=land_rows)
check('All 6 holes of the do-not-place TO-92 JFETs keep their pads', len(jfet_rows) == 6 and all(jfet_rows.values()), pads=jfet_rows)
check('A via stands at every via position in the PCB file', via_rows and all(via_rows.values()), vias=len(via_rows), positions=via_rows)

work = Path(tempfile.mkdtemp(prefix='blender-layers-audit-'))
environment = dict(os.environ, XDG_CONFIG_HOME=str(work / 'config'), XDG_CACHE_HOME=str(work / 'cache'), KICAD_CONFIG_HOME=str(work / 'config'))
glb = work / 'layers.glb'
try:
    run = subprocess.run([CLI, 'pcb', 'export', 'glb', *record['exports']['layers']['options'], '-o', str(glb), str(PCB)],
                         capture_output=True, text=True, env=environment, timeout=1800)
    assert run.returncode == 0 and glb.is_file(), run.stderr[-400:]
    fresh_hash = sha(glb)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    bpy.context.view_layer.update()
    imported = [o for o in set(bpy.data.objects) - before if o.type == 'MESH']
    rows, worst = {}, dict(bounds_mm=0.0, area_relative=0.0)
    for name, change in record['layer_changes'].items():
        wanted = change['kicad_mesh']
        candidates = [o for o in imported if o.data.name.split('.')[0] == wanted]
        if change['side']:
            candidates = [o for o in candidates if ((o.matrix_world @ o.data.vertices[0].co).z > 0.755e-3) == (change['side'] == 'front')]
        (part,) = candidates
        _, fresh = geometry(part)
        s = saved[name]
        box = max(abs(a - b) for a, b in zip(s['lo'] + s['hi'], fresh['lo'] + fresh['hi']))
        ratio = abs(s['area_mm2'] - fresh['area_mm2']) / max(fresh['area_mm2'], 1e-12)
        worst['bounds_mm'], worst['area_relative'] = max(worst['bounds_mm'], box), max(worst['area_relative'], ratio)
        rows[name] = dict(kicad_mesh=wanted, saved=s, fresh=fresh, bounds_max_diff_mm=box, area_relative_diff=ratio,
                          identical=s['vertices'] == fresh['vertices'] and s['triangles'] == fresh['triangles'] and box < 1e-3 and ratio < 1e-4)
finally:
    shutil.rmtree(work, ignore_errors=True)
check('All 8 saved mainboard layer meshes match a fresh KiCad export', len(rows) == 8 and all(r['identical'] for r in rows.values()),
      max_differences=worst, fresh_glb_sha256=fresh_hash, recorded_glb_sha256=record['exports']['layers']['glb_sha256'])
check('The audit left the scene and the PCB unchanged', sha(FINAL) == scene_hash and sha(PCB) == pcb_hash)
failures = [c for c in checks if not c['passed']]
out = dict(passed=not failures, check_count=len(checks), checks=checks, failures=failures, layers=rows, stable_scene_sha256=scene_hash, pcb_sha256=pcb_hash,
           via_count=len(vias), read_only=True, physical_fit_qualified=False,
           scope='Mainboard layer meshes versus a fresh KiCad export and the PCB file. Visualisation only: copper was not checked electrically here.')
(H / 'board-layer-audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(dict(passed=out['passed'], failures=failures, max_differences=worst, vias=len(vias)), indent=2), flush=True)
assert not failures
