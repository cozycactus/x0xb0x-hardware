import bpy,json
from pathlib import Path
base=Path(__file__).resolve().parent.parent
p=json.loads((base/'review-models/grayhill-world-orientation-audit.json').read_text())
o={}
for r in p['transforms']:
 obj=bpy.data.objects[r['reference']+' / separate Grayhill review envelope'];expected=r['component_to_native_world_matrix']
 for i in range(3):expected[i][3]*=.001
 actual=[list(row) for row in obj.matrix_basis]
 o[r['reference']]={'parent':obj.parent.name if obj.parent else None,'actual':actual,'expected':expected,'maximum_absolute_error':max(abs(actual[i][j]-expected[i][j]) for i in range(4) for j in range(4))}
(base/'panels/review-matrix-diagnostic.json').write_text(json.dumps(o,indent=2)+'\n')
print(json.dumps(o,indent=2))
