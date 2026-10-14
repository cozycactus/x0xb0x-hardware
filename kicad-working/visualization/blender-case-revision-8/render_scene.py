import bpy,sys,json,hashlib,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;scene=bpy.context.scene
SOURCE=Path(bpy.data.filepath);source_sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
draft='--draft' in sys.argv
rear_only='--rear-only' in sys.argv
scene.render.resolution_percentage=50 if draft else 100
if hasattr(scene,'eevee') and hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=32 if draft else 96
hero=bpy.data.objects['Camera / assembled and exploded'];rear=bpy.data.objects['Camera / rear connections']
jobs=[('preview-assembled',1,hero)] if draft else [('assembled',1,hero),('rear',1,rear),('exploded',80,hero)]
if not draft and 'Camera / control side inspection' in bpy.data.objects:jobs.append(('control-side',120,bpy.data.objects['Camera / control side inspection']))
if not draft and 'Camera / wiring routing study' in bpy.data.objects:jobs.append(('wiring-study',160,bpy.data.objects['Camera / wiring routing study']))
if rear_only:jobs=[job for job in jobs if job[0]=='rear']
# Bound timeline cameras otherwise override an explicitly selected rear camera
# when rendering evaluates the same frame again. These changes stay in memory.
for marker in scene.timeline_markers:marker.camera=None
records=json.loads((HERE/'render-records.json').read_text()) if rear_only else []
for label,frame,camera in jobs:
 scene.frame_set(frame);scene.camera=camera;output=HERE/(label+'.png');scene.render.filepath=str(output);start=time.time();bpy.ops.render.render(write_still=True)
 records=[r for r in records if r['view']!=label]
 records.append(dict(source_scene_sha256=source_sha,view=label,frame=frame,camera=camera.name,image=output.name,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),seconds=time.time()-start,resolution_percentage=scene.render.resolution_percentage))
scene.frame_set(1);scene.camera=hero;scene.render.resolution_percentage=100
# Rendering is read-only with respect to the saved scene. Do not overwrite inspection files.
(HERE/('preview-render-record.json' if draft else 'render-records.json')).write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))

assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_sha, 'Rendering changed the saved scene'
(HERE/'verification/render-readonly-verification.json').write_text(json.dumps(dict(passed=True,stable_scene_sha256=source_sha,view_count=len(records),views=[r['view']for r in records],saved_scene_unchanged=True),indent=2)+'\n')
