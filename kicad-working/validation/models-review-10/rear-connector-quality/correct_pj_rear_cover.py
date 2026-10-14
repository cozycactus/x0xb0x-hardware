"""Remove a terminal-eye feature incorrectly interpreted as a molded recess.

SPDX-License-Identifier: CC0-1.0
Frozen candidates are preserved. Writes a separately named corrected PJ family
and a new manifest. No PCB, existing model or scene is changed.
"""
from pathlib import Path
import json,hashlib,sys,copy
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part,MeshPart
from step_appearance import face_colors
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=json.loads((H/'rear-connector-quality-manifest.json').read_text())
old=source['parts'][1]
new=copy.deepcopy(old)
new['id']='PJ202AH_DrawingDerived_DetailedBody_Corrected'
doc=App.openDocument(str(H/(old['id']+'.FCStd')))
objects=[o for o in doc.Objects if hasattr(o,'Shape')]
cover=next(o for o in objects if o.Name=='SteppedRearCover')
before=cover.Shape.copy()
fill=Part.makeCylinder(.75,.7,App.Vector(0,-14.4,3),App.Vector(0,1,0))
cover.Shape=cover.Shape.fuse(fill).removeSplitter()
assert cover.Shape.isValid() and len(cover.Shape.Solids)==1
assert abs((cover.Shape.Volume-before.Volume)-fill.Volume)<1e-7

def bounds(s):
    b=s.optimalBoundingBox(False,False)
    return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]

checks=[]
for o,f in zip(objects,new['features']):
    assert o.Name==f['name']
    if o.Name!='SteppedRearCover':
        continue
    stl=H/(new['id']+'--'+o.Name+'.stl')
    mesh=MeshPart.meshFromShape(Shape=o.Shape,LinearDeflection=.025,
                              AngularDeflection=.1,Relative=False)
    mesh.write(str(stl));assert mesh.isSolid()
    f.update(stl=str(stl),sha256=sha(stl),exact_bounds_mm=bounds(o.Shape),
             volume_mm3=o.Shape.Volume,triangles=mesh.CountFacets)
new['mesh_parts']=copy.deepcopy(new['features'])
combined=Part.makeCompound([o.Shape for o in objects])
step=H/(new['id']+'.step')
Part.export(objects,str(step))
plain=Part.Shape();plain.read(str(step))
palette=[f['color_rgb']for f in new['features']]
new['color_roles']=face_colors(step,palette)
restored=Part.Shape();restored.read(str(step))
assert restored.isValid() and len(restored.Solids)==len(objects)
assert plain.exportBrepToString()==restored.exportBrepToString()
bb=[bounds(o.Shape)for o in objects]
overall=[min(b[k]for b in bb)for k in range(3)]+[max(b[k]for b in bb)for k in range(3,6)]
assert max(abs(a-b)for a,b in zip(overall,[-4.5,-14.4,0,4.5,0,11]))<1e-7
exterior=objects[0].Shape.copy()
for o in objects[1:]:exterior=exterior.fuse(o.Shape)
exterior=exterior.removeSplitter()
mesh=MeshPart.meshFromShape(Shape=exterior,LinearDeflection=.025,
                          AngularDeflection=.1,Relative=False)
stl=H/(new['id']+'.stl');mesh.write(str(stl));assert mesh.isSolid()
new.update(step=str(step),source_model=str(step),source_sha256=sha(step),
           stl=str(stl),stl_sha256=sha(stl),triangles=mesh.CountFacets,
           exact_bounds_mm=overall,volume_mm3=restored.Volume,
           faces=len(restored.Faces),supersedes_source_sha256=old['source_sha256'],
           source_correction='Removed rear plastic recess: manufacturer Ø1.5 callout is a terminal eye, not a molded cover hole. Below-seat terminal geometry remains omitted.')
new['limitations'].append(new['source_correction'])
doc.recompute();doc.saveAs(str(H/(new['id']+'.FCStd')))
App.closeDocument(doc.Name)
newmanifest=copy.deepcopy(source)
newmanifest['parts'][1]=new
assignment=copy.deepcopy(source['assignments'][1])
for key in ['source_model','source_sha256','limitations']:
    assignment[key]=new[key]
newmanifest['assignments'][1]=assignment
newmanifest['superseded_candidates']=[dict(id=old['id'],source_sha256=old['source_sha256'],source_model=old['source_model'],reason=new['source_correction'],distribute=False)]
newmanifest['active_manifest']='rear-connector-quality-corrected-manifest.json'
newmanifest['manufacturer_CAD_zip_distribution']=source['manufacturer_CAD_zip_distribution']
out=H/'rear-connector-quality-corrected-manifest.json'
out.write_text(json.dumps(newmanifest,indent=2)+'\n')
report=dict(passed=True,decision='Remove unsupported plastic recess; preserve superseded frozen candidate outside active portable assets.',
            unchanged_family='MJ3536N_DrawingDerived_DetailedBody',
            unchanged_MJ_sha256=source['parts'][0]['source_sha256'],
            superseded_PJ_sha256=old['source_sha256'],
            final_PJ_sha256=new['source_sha256'],
            final_PJ_step=new['source_model'],
            correction=new['source_correction'],
            exact_bounds_mm=overall,valid_positive_solids=True,
            closed_corrected_cover_STL=True,closed_combined_exterior_STL=True,
            colored_STEP_roundtrip_geometry_identical=True,
            cover_filled_volume_mm3=fill.Volume,
            native_audit_pending=True,
            unchanged_frozen_original_files=True)
(H/'pj-rear-cover-correction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
