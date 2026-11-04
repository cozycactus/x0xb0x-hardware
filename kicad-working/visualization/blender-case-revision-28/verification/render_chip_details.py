"""Read-only same-camera before/after details of the four SMD sites (exploded frame 80).

One orthographic view of each site, framed on the chip in revision 28, is rendered from revisions 27
and 28 with identical cameras. Tall neighbours hide Q112, Q121 and Q122 from any slant, so those three look
straight down the board normal and clip everything above 1.35 mm over the board: the cut parts show open.
Camera and light objects exist only in memory; neither scene file is written.
"""
import bpy, hashlib, json
from pathlib import Path
from mathutils import Vector
H = Path(__file__).resolve().parent
R = H.parent
baseline = R.parent / 'blender-case-revision-27/x0xb0x-populated-with-case.blend'
current = R / 'x0xb0x-populated-with-case.blend'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
guards = {str(p): sha(p) for p in (baseline, current)}
VIEWS = {f'smd-{r.lower()}': r for r in ('Q112', 'Q121', 'Q122', 'Q126')}
SCALE = .014
DISTANCE = .12
CENTRE_HEIGHT = .0006     # target above the chip's seat, metres
CLIP_HEIGHT = .00135      # clipping plane above the chip's seat, metres, in the straight-down views
SLANTED = {'smd-q126'}
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
        for inst in bpy.context.evaluated_depsgraph_get().object_instances:
            name = inst.object.original.name
            for label, ref in VIEWS.items():
                if name == f'MAINBOARD/{ref}/mesh':
                    m = inst.matrix_world.copy()
                    found[label] = (m @ Vector((0, 0, CENTRE_HEIGHT)), (m.to_3x3() @ Vector((0, 0, 1))).normalized())
        assert len(found) == 4
        for label, (centre, normal) in found.items():
            view = hero.matrix_world.translation - centre
            side = (view - normal * view.dot(normal)).normalized()
            direction = (normal * .82 + side * .57).normalized() if label in SLANTED else (normal + side * .001).normalized()
            cameras[label] = (centre + direction * DISTANCE, centre)
    for label in VIEWS:
        location, target = cameras[label]
        data = bpy.data.cameras.new('TEMP ' + label)
        clip = .001 if label in SLANTED else DISTANCE - (CLIP_HEIGHT - CENTRE_HEIGHT)
        data.type, data.ortho_scale, data.clip_start, data.clip_end = 'ORTHO', SCALE, clip, 1.
        cam = bpy.data.objects.new('TEMP ' + label, data)
        scene.collection.objects.link(cam)
        cam.location = location
        cam.rotation_euler = (target - location).to_track_quat('-Z', 'Y').to_euler()
        light = bpy.data.lights.new('TEMP detail light', 'AREA')
        light.energy, light.size = 1.5, .08
        lamp = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(lamp)
        lamp.location, lamp.rotation_euler = location, cam.rotation_euler
        scene.camera = cam
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1200, 800, 100
        out = R / f'{label}-{tag}.png'
        scene.render.filepath = str(out)
        bpy.ops.render.render(write_still=True)
        records.append(dict(image=out.name, view=label, scene=tag, frame=80, source_scene_sha256=sha(path), sha256=sha(out),
                            camera_location=list(location), camera_target=list(target), ortho_scale_m=SCALE,
                            clipped_above_seat_m=None if label in SLANTED else CLIP_HEIGHT))
        bpy.data.objects.remove(cam)
        bpy.data.objects.remove(lamp)
assert guards == {str(p): sha(p) for p in (baseline, current)}
(H / 'chip-detail-render.json').write_text(json.dumps(dict(passed=True, images=sorted(records, key=lambda r: r['image']), same_camera_before_after=True,
                                                            read_only=True, saved_scenes_unchanged=True), indent=2) + '\n')
print(json.dumps(sorted(r['image'] for r in records)))
