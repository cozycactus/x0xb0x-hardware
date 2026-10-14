"""Fresh 11/12 actual glyph-to-panel measurements in all four inspection poses."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent.parent / 'blender-case-revision-11/x0xb0x-populated-with-case.blend'
FINAL = HERE.parent / 'x0xb0x-populated-with-case.blend'
LABELS = {r + ' label' for r in ['POWER0', 'HEADPHONE0', 'MIXIN0', 'MIXOUT0',
          'CV0', 'GATE0', 'USB0', 'DIN1', 'DIN2', 'DIN3', 'DIN4']}
CHANGED = {'DIN1 label', 'DIN2 label', 'DIN3 label'}
FRAMES = (1, 80, 120, 160)
import hashlib


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matrix(m):
    return [list(row) for row in m]


def measure(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    initial_frame = scene.frame_current
    frames = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        panel = bpy.data.objects['Rear panel — original DXF']
        rear = bpy.data.objects['Rear faces — presentation proxies']
        inv = panel.matrix_world.inverted()
        panel_points, glyphs, panel_instances = [], {name: [] for name in LABELS}, 0
        native_din_centers = {}
        for instance in bpy.context.evaluated_depsgraph_get().object_instances:
            obj, name = instance.object, instance.object.original.name
            for ref in ('DIN1', 'DIN2', 'DIN3', 'DIN4'):
                if obj.type == 'MESH' and name == 'IOBOARD/' + ref + '/mesh':
                    assert ref not in native_din_centers
                    native_din_centers[ref] = list(inv @ instance.matrix_world @ Vector((0, 0, .010)) * 1000)
            if obj.type == 'MESH' and instance.parent and instance.parent.name == panel.name:
                panel_instances += 1
                panel_points.extend(inv @ instance.matrix_world @ v.co * 1000 for v in obj.data.vertices)
            if name in LABELS and obj.type == 'FONT':
                mesh = obj.to_mesh()
                points = [inv @ instance.matrix_world @ v.co * 1000 for v in mesh.vertices]
                glyphs[name].append(dict(
                    local_bounds_mm=[min(v.co[i] * 1000 for v in mesh.vertices) for i in range(3)]
                                    + [max(v.co[i] * 1000 for v in mesh.vertices) for i in range(3)],
                    automatic_texture_space=dict(enabled=obj.data.use_auto_texspace,
                        location_mm=[v * 1000 for v in obj.data.texspace_location],
                        size_mm=[v * 1000 for v in obj.data.texspace_size]),
                    bounds_mm=[min(p[i] for p in points) for i in range(3)]
                              + [max(p[i] for p in points) for i in range(3)],
                    actual_instance_matrix=matrix(instance.matrix_world),
                    text_origin_panel_mm=list(inv @ instance.matrix_world.translation * 1000),
                    vertex_count=len(points)))
                obj.to_mesh_clear()
        exterior = max(p.z for p in panel_points)
        frames[str(frame)] = dict(panel_exterior_normal_mm=exterior,
            panel_instance_count=panel_instances, native_din_axis_panel_mm=native_din_centers, panel_matrix=matrix(panel.matrix_world),
            rear_legend_instancer_matrix=matrix(rear.matrix_world),
            labels={name: dict(instance_count=len(rows), **rows[0],
                        minimum_gap_mm=rows[0]['bounds_mm'][2] - exterior,
                        maximum_gap_mm=rows[0]['bounds_mm'][5] - exterior)
                    for name, rows in sorted(glyphs.items())})
    scene.frame_set(initial_frame)
    bpy.context.view_layer.update()
    return frames


hashes = {str(p): sha(p) for p in (BASELINE, FINAL)}
before, after = measure(BASELINE), measure(FINAL)
checks = []


def check(name, passed, **details):
    checks.append(dict(check=name, passed=bool(passed), **details))


check('Eleven unique evaluated FONT labels in each of four frames',
      all(set(row['labels']) == LABELS and all(x['instance_count'] == 1 for x in row['labels'].values())
          for frames in (before, after) for row in frames.values()))
check('One real rear panel mesh in each frame',
      all(row['panel_instance_count'] == 1 for frames in (before, after) for row in frames.values()))
check('Label instancer retains exactly the actual panel pose in all four frames',
      all(row['panel_matrix'] == row['rear_legend_instancer_matrix']
          for frames in (before, after) for row in frames.values()))
check('Panel and legend instancer matrices remain exact from11 to12',
      all(before[f]['panel_matrix'] == after[f]['panel_matrix']
          and before[f]['rear_legend_instancer_matrix'] == after[f]['rear_legend_instancer_matrix'] for f in after))
check('Every actual glyph instance matrix remains exact from11 to12',
      all(before[f]['labels'][n]['actual_instance_matrix'] == row['actual_instance_matrix']
          for f, frame in after.items() for n, row in frame['labels'].items()))
check('Every MIDI/SYNC text origin aligns with its corresponding actual native DIN axis',
      all(abs(frame['labels'][ref + ' label']['text_origin_panel_mm'][0] - center[0]) < .0001
          for frame in after.values() for ref, center in frame['native_din_axis_panel_mm'].items())
      and all(len(frame['native_din_axis_panel_mm']) == 4 for frame in after.values()),
      comparison_axis='actual evaluated panel horizontal X', tolerance_mm=.0001,
      qualification='CENTER text alignment uses font advance metrics; individual ink bounds can be asymmetric.')
check('Every actual MIDI/SYNC glyph is horizontally nearest its named native port',
      all(min(frame['native_din_axis_panel_mm'], key=lambda candidate:
              abs((frame['labels'][ref + ' label']['bounds_mm'][0]
                  + frame['labels'][ref + ' label']['bounds_mm'][3]) / 2
                  - frame['native_din_axis_panel_mm'][candidate][0])) == ref
          for frame in after.values() for ref in frame['native_din_axis_panel_mm']))
gaps = [row['minimum_gap_mm'] for frame in after.values() for row in frame['labels'].values()]
check('All44 actual glyph backs sit .01mm outside the panel',
      all(abs(gap - .01) < .0001 for gap in gaps),
      minimum_gap_mm=min(gaps), maximum_gap_mm=max(gaps), numeric_tolerance_mm=.0001)
thickness = [row['maximum_gap_mm'] - row['minimum_gap_mm'] for frame in after.values() for row in frame['labels'].values()]
check('All44 full glyph extrusion thicknesses remain .012mm',
      all(abs(t - .012) < .0001 for t in thickness),
      minimum_thickness_mm=min(thickness), maximum_thickness_mm=max(thickness))
error = max(abs(before[f]['labels'][n]['bounds_mm'][i] - row['bounds_mm'][i])
            for f, frame in after.items() for n, row in frame['labels'].items()
            if n not in CHANGED for i in (0, 1, 3, 4))
check('Automatic FONT texture-space XY caches match actual regenerated glyph bounds',
      all(row['automatic_texture_space']['enabled']
          and all(abs(row['automatic_texture_space']['location_mm'][i]
                      - (row['local_bounds_mm'][i] + row['local_bounds_mm'][i + 3]) / 2) < .00001
                  and abs(row['automatic_texture_space']['size_mm'][i]
                      - (row['local_bounds_mm'][i + 3] - row['local_bounds_mm'][i]) / 2) < .00001
                  for i in (0, 1))
          for frames in (before, after) for frame in frames.values()
          for name, row in frame['labels'].items() if name in CHANGED),
      qualification='With automatic texture space enabled, changed body strings regenerate these cached XY bounds. Font/style/material settings remain unchanged.')
check('Every unchanged legend retains actual in-plane glyph extents', error < .0001,
      maximum_in_plane_error_mm=error)
check('Only corrected text may change generated in-plane glyph bounds',
      all(all(abs(before[f]['labels'][n]['bounds_mm'][i] - row['bounds_mm'][i]) < .0001
              for i in (2, 5))
          for f, frame in after.items() for n, row in frame['labels'].items()),
      allowed_changed_text=sorted(CHANGED))
check('Read-only measurement preserves both saved scene bytes',
      all(sha(Path(path)) == digest for path, digest in hashes.items()))
failures = [row for row in checks if not row['passed']]
out = dict(passed=not failures, check_count=len(checks), failures=failures,
           baseline_scene_sha256=hashes[str(BASELINE)], scene_sha256=hashes[str(FINAL)],
           unique_rear_legend_count=11, frame_count=4, evaluated_glyph_pose_count=44,
           baseline_frames=before, frames=after, checks=checks, read_only=True,
           physical_fit_qualified=False,
           method='Actual evaluated FONT glyph vertices and real panel mesh vertices in evaluated panel coordinates, using collection-instance matrices. FONT/MESH conversion representations are counted once. Changed string widths are allowed; every object/instance pose and glyph normal plane must remain exact.')
(HERE / 'rear-legend-plane-audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: v for k, v in out.items() if k not in {'checks', 'frames', 'baseline_frames'}}, indent=2))
assert not failures, 'Actual glyph/panel plane audit failed'
