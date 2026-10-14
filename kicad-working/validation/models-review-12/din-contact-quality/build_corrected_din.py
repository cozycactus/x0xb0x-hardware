"""Correct the two outer SDS-50J contact centers and slot directions.

Original reconstruction geometry and code: CC0-1.0.
Manufacturer drawings retain their own rights. No downloaded CAD is copied.
Run using the bundled FreeCAD Python runtime; no GUI or source PCB mutation.
"""
from pathlib import Path
import ast
import hashlib
import json
import math
import sys

sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
import Mesh

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
REPO=WORK.parent
LEGACY=WORK/'visualization/blender-case-revision-7/quality-model-sources/rear-quality/build_rear_quality.py'
OLD=WORK/'ioboard/3dmodels/Revision8/rear-quality/SDS50J_DatasheetDerived_DetailedBody.step'
PDF=WORK/'visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/sds50j.pdf'
V=App.Vector
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
guards={str(p):sha(p) for p in [OLD,PDF,WORK/'mainboard/mainboard.kicad_pcb',WORK/'ioboard/ioboard.kicad_pcb']}
# Reuse only the retained helper definitions, never the old generator's
# top-level model construction, export paths or stale contact-angle table.
names={'box','cy','fuse','cut','bbox','face_colors'}
module=ast.parse(LEGACY.read_text())
functions=[node for node in module.body if isinstance(node,ast.FunctionDef) and node.name in names]
assert len(functions)==len(names)
import re
exec(compile(ast.Module(body=functions,type_ignores=[]),str(LEGACY),'exec'))
old=Part.Shape();old.read(str(OLD));assert len(old.Solids)==8 and old.isValid()
housing,cover=old.Solids[:2]
assert abs(housing.BoundBox.XLength-20)<1e-7
assert abs(housing.BoundBox.ZLength-21.1)<1e-7

# The PDF's 25 degree leader describes the tilt of the outer elongated
# slots. Their round contact centers lie ON the horizontal centerline.
# Coordinates and the slot's long-axis tilt are independent quantities.
contacts=[dict(pin='1',center_mm=[3.5,10.],slot_tilt_from_vertical_deg=-25.),
          dict(pin='3',center_mm=[-3.5,10.],slot_tilt_from_vertical_deg=25.),
          dict(pin='5',center_mm=[-3.5/math.sqrt(2),10-3.5/math.sqrt(2)],slot_tilt_from_vertical_deg=45.),
          dict(pin='2',center_mm=[0.,6.5],slot_tilt_from_vertical_deg=0.),
          dict(pin='4',center_mm=[3.5/math.sqrt(2),10-3.5/math.sqrt(2)],slot_tilt_from_vertical_deg=-45.)]
insert=cy(6.65,1.6,5.8,10)
for c in contacts:
    x,z=c['center_mm']
    tool=box(1.55,1.9,3.0,y=5.65,z=z-1.5,x=x-.775)
    tool.rotate(V(x,0,z),V(0,1,0),c['slot_tilt_from_vertical_deg'])
    insert=cut(insert,tool)
insert=cut(insert,box(2.2,1.9,1.5,y=5.65,z=15.2))
insert=cut(insert,box(1.1,1.9,1.3,y=5.65,z=3.4))
sleeves=[]
for i,c in enumerate(contacts):
    x,z=c['center_mm']
    if i<2:sleeves.append(cut(cy(.72,1.3,5.95,z,x),cy(.43,1.5,5.85,z,x)))
    else:
        sleeve=old.Solids[3+i]
        center=sleeve.BoundBox.Center
        assert math.hypot(center.x-x,center.z-z)<1e-7
        sleeves.append(sleeve)
segments=[('Housing','housing',housing),('RearCover','cover',cover),('SocketInsert','housing',insert)]
segments += [(f'MatingSocket{i+1}','contact',s) for i,s in enumerate(sleeves)]
colors={'housing':[.025,.027,.03],'cover':[.045,.047,.05],'contact':[.6,.61,.63]}
doc=App.newDocument('SDS50J_CorrectedContactPattern');objects=[];part_records=[]
for name,role,shape in segments:
    assert shape.isValid() and shape.Volume>0,name
    o=doc.addObject('PartDesign::Feature',name);o.Shape=shape
    o.addProperty('App::PropertyString','SourceBasis');o.SourceBasis='Same Sky SDS-J page 3; corrected contact centers and independent slot tilts'
    objects.append(o)
    mesh=Mesh.Mesh(shape.tessellate(.035));stl=HERE/(name+'.stl');mesh.write(str(stl))
    part_records.append(dict(name=name,role=role,bounds=bbox(shape),stl=stl.name,
        stl_sha256=sha(stl),triangles=mesh.CountFacets,color=colors[role]))
doc.recompute()
step=HERE/'SDS50J_CorrectedContactPattern.step'
Part.export(objects,str(step))
before_color=Part.Shape();before_color.read(str(step))
face_colors(step,[colors[role] for _,role,s in segments for _ in s.Solids])
saved=Part.Shape();saved.read(str(step))
assert saved.isValid() and len(saved.Solids)==8
assert saved.exportBrepToString()==before_color.exportBrepToString()
doc.saveAs(str(HERE/'SDS50J_CorrectedContactPattern.FCStd'));App.closeDocument(doc.Name)
checks=[]
def check(name,passed,**details):checks.append(dict(check=name,passed=bool(passed),**details))
def volume(shape,x,z,radius=.35):
    cylinder=Part.makeCylinder(radius,7.35,V(x,-.01,z),V(0,1,0))
    return sum(s.common(cylinder).Volume for s in shape.Solids)
check('Saved valid positive solids',saved.isValid() and all(s.Volume>0 and s.isValid() for s in saved.Solids))
check('STEP color injection preserves exact geometry',saved.exportBrepToString()==before_color.exportBrepToString())
for i in [0,1,5,6,7]:
    a=old.Solids[i];b=saved.Solids[i]
    delta=a.cut(b).Volume+b.cut(a).Volume
    check('Unchanged housing/cover/lower sleeve '+str(i),delta<1e-7,symmetric_difference_mm3=delta)
baseline_failures=[]
for c in contacts:
    x,z=c['center_mm'];prior=volume(old,x,z);now=volume(saved,x,z)
    check('Contact '+c['pin']+' bore at printed center',now<1e-7,center_mm=[x,z],intersection_mm3=now)
    if prior>1e-7:baseline_failures.append(c['pin'])
    theta=math.radians(c['slot_tilt_from_vertical_deg']);axis=[math.sin(theta),math.cos(theta)]
    normal=[math.cos(theta),-math.sin(theta)]
    for sign in [-1,1]:
        point=[x+sign*1.2*axis[0],z+sign*1.2*axis[1]];hit=volume(saved,*point,radius=.10)
        check('Contact '+c['pin']+' elongated slot end '+str(sign),hit<1e-7,point_mm=point,intersection_mm3=hit)
    point=[x+1.05*normal[0],z+1.05*normal[1]];hit=volume(saved,*point,radius=.10)
    check('Contact '+c['pin']+' retains material beside slot',hit>.01,point_mm=point,intersection_mm3=hit)
check('Regression catches both original misplaced outer contacts',baseline_failures==['1','3'],baseline_failures=baseline_failures)
check('Source boards, old STEP and PDF unchanged',all(sha(Path(p))==h for p,h in guards.items()))
report=dict(passed=all(c['passed'] for c in checks),check_count=len(checks),checks=checks,
    model=step.name,model_sha256=sha(step),model_bytes=step.stat().st_size,
    old_model=str(OLD.relative_to(REPO)),old_model_sha256=guards[str(OLD)],
    source_PDF=str(PDF.relative_to(REPO)),source_PDF_sha256=sha(PDF),source_page=3,
    source_url='https://www.sameskydevices.com/product/resource/sds-j.pdf',
    retained_helper_generator=str(LEGACY.relative_to(REPO)),helper_sha256=sha(LEGACY),
    contact_centers_and_slot_tilts=contacts,parts=part_records,bounds=bbox(saved),
    corrected_references=['DIN1','DIN2','DIN3','DIN4'],unchanged_source_solids=[0,1,5,6,7],
    changed_source_solids=[2,3,4],downloaded_CAD_geometry_incorporated=False,
    limitations=['Only two contact positions and their independent slot tilts are corrected from the primary drawing.',
        'Existing unsized slot widths, sleeve dimensions, cavity depth, keys and minor molding details remain illustrations.',
        'Solder terminals and locators remain omitted; the supplied mesh has a separately documented registration uncertainty.',
        'Printed nominal body envelope is preserved. No placement, routing, copper, pad, enclosure or historical physical-fit qualification.'],
    physical_fit_qualified=False)
(HERE/'corrected-model-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['checks','parts']},indent=2),flush=True)
assert report['passed'],[r for r in checks if not r['passed']]
