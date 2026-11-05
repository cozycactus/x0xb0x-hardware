"""Read-only same-camera before/after details of the two JFET sites (exploded frame 80).

One orthographic view of each site, framed between the chip and the holes it stands beside, is
rendered from revisions 28 and 29 with identical cameras, on a slant towards the hero camera, turned
around the board normal and tilted by SLANT so that the standing neighbours don't hide the chip. Camera and
light objects exist only in memory; neither scene file is written. Pass --draft to render at a
quarter of the size without writing the record, for framing.
"""
import bpy, hashlib, json, math, sys
from pathlib import Path
from mathutils import Matrix, Vector
H = Path(__file__).resolve().parent
R = H.parent
baseline = R.parent / 'blender-case-revision-28/x0xb0x-populated-with-case.blend'
current = R / 'x0xb0x-populated-with-case.blend'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
guards = {str(p): sha(p) for p in (baseline, current)}
change = json.loads((R / 'revision-29-change-record.json').read_text())
VIEWS = {f'jfet-{v["reference"].lower()}': v for v in change['added_references'].values()}
assert sorted(VIEWS) == ['jfet-q128', 'jfet-q139']
draft = '--draft' in sys.argv
out_dir = Path(next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), R))
SCALE = .018
DISTANCE = .12
CENTRE_HEIGHT = .0006     # target above the chip's seat, metres
# Per view: degrees around the board normal from the hero camera's side, the view direction's normal and side parts, and the lamp's energy.
SLANT = {'jfet-q128': (-45, .90, .43, 1.), 'jfet-q139': (-120, .82, .57, .75)}
records = []
cameras = {}
for path, tag in ((current, 'after'), (baseline, 'before')):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    for marker in scene.timeline_markers:
        marker.camera = None
    scene.frame_set(80)
    bpy.context.view_layer.update()
    hero = bpy.data.objects['Camera / assembled and exploded']
    if not cameras:      # cameras come from the chips' displayed pose and are reused unchanged
        found = {}
        board = bpy.data.objects['Node_0']
        for inst in bpy.context.evaluated_depsgraph_get().object_instances:
            name = inst.object.original.name
            for label, row in VIEWS.items():
                if name == row['mesh_object']:
                    # Board frame to world in this frame: the chip's instance, back through its saved pose, then the board's.
                    to_world = inst.matrix_world @ inst.object.original.matrix_world.inverted() @ board.matrix_world
                    held = change['removed_do_not_place_references']['MAINBOARD/' + row['replaces']]['frame']
                    held_xy = Vector((held[0][3], held[1][3], row['frame'][2][3]))
                    chip_xyz = Vector((row['frame'][0][3], row['frame'][1][3], row['frame'][2][3]))
                    normal = (to_world.to_3x3() @ Vector((0, 0, 1))).normalized()
                    found[label] = (to_world @ ((chip_xyz + held_xy) / 2) + normal * CENTRE_HEIGHT, normal)
        assert len(found) == 2
        for label, (centre, normal) in found.items():
            view = hero.matrix_world.translation - centre
            side = (view - normal * view.dot(normal)).normalized()
            azimuth, up, across, _ = SLANT[label]
            side = Matrix.Rotation(math.radians(azimuth), 3, normal) @ side
            direction = (normal * up + side * across).normalized()
            cameras[label] = (centre + direction * DISTANCE, centre)
    for label in VIEWS:
        location, target = cameras[label]
        data = bpy.data.cameras.new('TEMP ' + label)
        data.type, data.ortho_scale, data.clip_start, data.clip_end = 'ORTHO', SCALE, .001, 1.
        cam = bpy.data.objects.new('TEMP ' + label, data)
        scene.collection.objects.link(cam)
        cam.location = location
        cam.rotation_euler = (target - location).to_track_quat('-Z', 'Y').to_euler()
        light = bpy.data.lights.new('TEMP detail light', 'AREA')
        light.energy, light.size = SLANT[label][3], .08
        lamp = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(lamp)
        lamp.location, lamp.rotation_euler = location, cam.rotation_euler
        scene.camera = cam
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1200, 800, 50 if draft else 100
        out = out_dir / f'{label}-{tag}.png'
        scene.render.filepath = str(out)
        bpy.ops.render.render(write_still=True)
        records.append(dict(image=out.name, view=label, scene=tag, frame=80, source_scene_sha256=sha(path), sha256=sha(out),
                            camera_location=list(location), camera_target=list(target), ortho_scale_m=SCALE, slant=SLANT[label]))
        bpy.data.objects.remove(cam)
        bpy.data.objects.remove(lamp)
assert guards == {str(p): sha(p) for p in (baseline, current)}
if not draft:
    (H / 'chip-detail-render.json').write_text(json.dumps(dict(passed=True, images=sorted(records, key=lambda r: r['image']), same_camera_before_after=True,
                                                                read_only=True, saved_scenes_unchanged=True), indent=2) + '\n')
print(json.dumps(sorted(r['image'] for r in records)))
