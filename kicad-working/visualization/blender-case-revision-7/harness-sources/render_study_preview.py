from pathlib import Path
import bpy,hashlib,json
here=Path(__file__).resolve().parents[1]
s=bpy.context.scene
for marker in s.timeline_markers:marker.camera=None
s.frame_set(160);s.camera=bpy.data.objects['Camera / wiring routing study']
s.render.resolution_percentage=75
s.view_settings.exposure=-2.5
s.render.filepath=str(here/'harness-routing-study-preview.png')
bpy.ops.render.render(write_still=True)
print('STUDY PREVIEW RENDERED',s.render.filepath)
