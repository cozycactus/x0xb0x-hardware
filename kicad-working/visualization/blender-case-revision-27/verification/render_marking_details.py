"""Read-only same-camera before/after IC marking detail renders (exploded frame 80).

Three orthographic views, over the 74HC595 row, the I/O optocoupler IC24 and the underside
FT232BM (IC25), are rendered from revision 26 and revision 27 with
identical cameras. Camera and light objects exist only in memory; neither scene file
is written.
"""
import bpy, hashlib, json
from pathlib import Path
from mathutils import Vector
H = Path(__file__).resolve().parent
R = H.parent
baseline = R.parent / 'blender-case-revision-26/x0xb0x-populated-with-case.blend'
current = R / 'x0xb0x-populated-with-case.blend'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
guards = {str(p): sha(p) for p in (baseline, current)}
VIEWS = {'markings-mainboard': (['MAINBOARD/IC4', 'MAINBOARD/IC5'], .045), 'markings-ioboard': (['IOBOARD/IC24'], .025),
         'markings-ic25-underside': (['IOBOARD/IC25'], .020)}
CLIP = {'markings-ic25-underside': .09}   # IC25 sits on the I/O board underside; clip the case floor below it
ENERGY = {'markings-ic25-underside': 12.}  # the underside gets no studio light
records = []


def pose(refs):
    """Centre and board normal of the displayed instances of refs at frame 80."""
    pts, normal = [], None
    wanted = {r + '/mesh' for r in refs}
    for inst in bpy.context.evaluated_depsgraph_get().object_instances:
        if inst.object.original.name in wanted and inst.object.type == 'MESH':
            m = inst.matrix_world.copy()
            pts += [m @ v.co for v in inst.object.data.vertices]
            normal = (m.to_3x3() @ Vector((0, 0, 1))).normalized()
    centre = Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
    return centre, normal


cameras = {}
for path, tag in ((baseline, 'before'), (current, 'after')):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    for marker in scene.timeline_markers:
        marker.camera = None
    scene.frame_set(80)
    bpy.context.view_layer.update()
    hero = bpy.data.objects['Camera / assembled and exploded']
    for label, (refs, scale) in VIEWS.items():
        if label not in cameras:      # cameras come from the baseline pose and are reused unchanged
            centre, normal = pose(refs)
            view = (hero.matrix_world.translation - centre)
            side = (view - normal * view.dot(normal)).normalized()
            direction = (normal * 0.62 + side * 0.78).normalized()
            cameras[label] = (centre + direction * .12, centre, scale)
        location, target, scale = cameras[label]
        data = bpy.data.cameras.new('TEMP ' + label)
        data.type, data.ortho_scale, data.clip_start, data.clip_end = 'ORTHO', scale, CLIP.get(label, .001), 1.
        cam = bpy.data.objects.new('TEMP ' + label, data)
        scene.collection.objects.link(cam)
        cam.location = location
        cam.rotation_euler = (target - location).to_track_quat('-Z', 'Y').to_euler()
        light = bpy.data.lights.new('TEMP detail light', 'AREA')
        light.energy, light.size = ENERGY.get(label, 1.5), .08
        lamp = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(lamp)
        # Under the board the case floor would shadow a light at the camera; place it 3 cm from the chip instead.
        lamp.location = target + (location - target).normalized() * .03 if label in CLIP else location
        lamp.rotation_euler = cam.rotation_euler
        scene.camera = cam
        scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1500, 1000, 100
        out = R / f'{label}-{tag}.png'
        scene.render.filepath = str(out)
        bpy.ops.render.render(write_still=True)
        records.append(dict(image=out.name, view=label, scene=tag, frame=80, source_scene_sha256=sha(path), sha256=sha(out),
                            camera_location=list(location), camera_target=list(target), ortho_scale_m=scale))
        bpy.data.objects.remove(cam)
        bpy.data.objects.remove(lamp)
assert guards == {str(p): sha(p) for p in (baseline, current)}
(H / 'marking-detail-render.json').write_text(json.dumps(dict(passed=True, images=records, same_camera_before_after=True,
                                                                     read_only=True, saved_scenes_unchanged=True), indent=2) + '\n')
print(json.dumps([r['image'] for r in records]))
