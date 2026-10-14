import bpy,json
from pathlib import Path
s=bpy.context.scene;s.frame_set(1)
x={"scene_objects":[{"name":o.name,"type":o.type,"instance":o.instance_collection.name if o.instance_collection else None,"hide_render":o.hide_render,"matrix":[list(r) for r in o.matrix_world],"action":o.animation_data.action.name if o.animation_data and o.animation_data.action else None} for o in s.objects],"collections":[c.name for c in bpy.data.collections]}
Path(__file__).with_name("scene-inventory.json").write_text(json.dumps(x,indent=2))
print("SCENE INVENTORY",len(x["scene_objects"]))
