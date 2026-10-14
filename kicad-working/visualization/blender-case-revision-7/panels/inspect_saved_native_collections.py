import bpy,json
from pathlib import Path
b=Path(__file__).resolve().parent
names=['IOBOARD/PCB layers/mesh.003','IOBOARD/PCB layers/mesh.005','IOBOARD/PCB layers/mesh.006','IOBOARD/PCB layers/mesh.007']
out={'collections':[{'name':c.name,'users':c.users,'fake_user':c.use_fake_user,'objects':len(c.objects)} for c in bpy.data.collections],
     'expected_original_objects':{name:({'present':True,'users':bpy.data.objects[name].users,'collections':[c.name for c in bpy.data.objects[name].users_collection],'vertices':len(bpy.data.objects[name].data.vertices),'polygons':len(bpy.data.objects[name].data.polygons)} if name in bpy.data.objects else {'present':False}) for name in names}}
(b/'saved-native-collection-diagnostic.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
