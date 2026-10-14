"""Read-only actual assembled LED/cap/panel close-up; no scene is saved."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
H=Path(__file__).resolve().parent;W=H.parents[2]
path=W/'visualization/blender-case-revision-7/x0xb0x-populated-with-case.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=sha(path);bpy.ops.wm.open_mainfile(filepath=str(path))
s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update()
panel=bpy.data.objects['Top panel — original DXF'];matrix=panel.matrix_world.copy()
for o in bpy.data.objects:
    if o.type=='FONT':o.hide_render=True
for marker in s.timeline_markers:marker.camera=None
bpy.ops.object.camera_add()
c=bpy.context.object;c.name='Independent attachment inspection camera'
target=matrix@Vector((.0127,.05918,-.002))
c.location=matrix@Vector((.043,.017,.033))
c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
c.data.type='ORTHO';c.data.ortho_scale=.041
c.data.clip_start=.001;c.data.clip_end=10;s.camera=c
s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=True
s.render.resolution_x=1500;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.render.filepath=str(H/'final-front-attachment-closeup.png')
bpy.ops.render.render(write_still=True)
assert sha(path)==before
r=dict(passed=True,scene=str(path),scene_sha256=before,
       scene_hash_unchanged=True,image=Path(s.render.filepath).name,
       image_sha256=sha(s.render.filepath),
       proof='Actual saved frame1 assembled interface geometry, showing raised native LED lenses and switch caps at original panel openings. Camera and text visibility adjusted in memory for inspection. No model geometry, placement or source scene was edited/saved.',
       limitations=['Spacer outer mold and button cap socket/retention remain unmodeled.','This is a geometric illustration; it does not qualify physical fitted height or mechanical tolerances.'])
(H/'final-closeup-render-record.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
