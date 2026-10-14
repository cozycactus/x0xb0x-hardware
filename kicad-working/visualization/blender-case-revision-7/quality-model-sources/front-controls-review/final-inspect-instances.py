"""Read-only actual rendered-instance transform diagnostic."""
from pathlib import Path
import bpy,json,hashlib
H=Path(__file__).resolve().parent;W=H.parents[2]
path=W/'visualization/blender-case-revision-7/x0xb0x-populated-with-case.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
before=sha(path);bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
rows=[]
for f in [1,80,120,160]:
    s.frame_set(f);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    entries=[]
    for ins in deps.object_instances:
        n=ins.object.original.name
        if n.startswith(('S5 / switch cap','S27 / switch cap'))or n=='MAINBOARD/LED1/mesh':
            entries.append(dict(name=n,is_instance=ins.is_instance,
                                instance_parent=ins.parent.original.name if ins.parent else None,
                                matrix_world=[list(r)for r in ins.matrix_world],
                                object_world=[list(r)for r in ins.object.original.matrix_world],
                                object_parent=ins.object.original.parent.name if ins.object.original.parent else None,
                                collections=[c.name for c in ins.object.original.users_collection]))
    rows.append(dict(frame=f,instances=entries))
out=dict(read_only=True,scene=str(path),scene_sha256=before,
         scene_hash_unchanged=sha(path)==before,frames=rows)
(H/'final-instance-diagnostic.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
