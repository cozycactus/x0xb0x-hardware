"""Read-only installed rear-connector STEP cavity audit (millimetres).

SPDX-License-Identifier: CC0-1.0
This validates openings in illustrative source geometry, not plug fit.
"""
from pathlib import Path
import hashlib
import json
import math
import sys

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
sys.path.insert(0, str(REPO / 'kicad-import/validation'))
from verify_native_projects import children, one, parse_sexpr, property_value

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
pcb = WORK / 'ioboard/ioboard.kicad_pcb'
pcb_hash = sha(pcb)
fps = {property_value(f, 'Reference', 'reference'): f
       for f in children(parse_sexpr(pcb.read_text()), 'footprint')}

families = [
    dict(name='NYS216', references=['HEADPHONE0', 'MIXIN0', 'MIXOUT0'],
         front_y_mm=-8.5, front_direction=[0,-1,0], axis_z_mm=8.0,
         open_tests=[dict(name='unobstructed entrance within 6.35mm bore',
                          x=0,z=8,y=-8.51,length=8.50,radius=3.0),
                     dict(name='continuous central passage through housing',
                          x=0,z=8,y=-8.51,length=32.90,radius=1.4)],
         interpretation='Open front bore and central passage; reconstructed leaf contacts occupy one side. Nut/washer belong to scene hardware. No source correction required.'),
    dict(name='SDS50J', references=['DIN1','DIN2','DIN3','DIN4'],
         front_y_mm=0, front_direction=[0,-1,0], axis_z_mm=10.0,
         open_tests=[dict(name='open front mating recess',x=0,z=10,y=-.01,
                          length=5.70,radius=6.0)],
         interpretation='Open recessed insert with five open contact mouths. Each modeled contact hole is blind behind Y7.4, a documented unsized illustrative depth; this does not prove plug insertion depth. No front-face closure in source.'),
    dict(name='MJ3536N', references=['CV0','GATE0'],
         front_y_mm=-3,front_direction=[0,-1,0],axis_z_mm=5.5,
         open_tests=[dict(name='full-width entrance before interior contact leaf',
                          x=0,z=5.5,y=-3.01,length=12.50,radius=1.7),
                     dict(name='continuous central passage through contact zone',
                          x=0,z=5.5,y=-3.01,length=17.0,radius=1.4)],
         interpretation='Open 3.6mm bore through projecting bushing and housing to nominal depth14.1mm beyond front shoulder. Reconstructed leaf intrudes slightly into upper bore; blind rear floor and contact intrusion are not closed mating faces. No source correction required.'),
    dict(name='PJ202AH', references=['POWER0'],
         front_y_mm=0,front_direction=[0,1,0],axis_z_mm=6.5,
         open_tests=[dict(name='open front before recessed center pin',x=0,z=6.5,
                          y=-.70,length=.71,radius=3.0),
                     dict(name='continuous annular plug path beside center pin',
                          x=1.75,z=6.5,y=-8.70,length=8.71,radius=.5)],
         interpretation='Open 6.5mm entrance with recessed 2mm center pin. Center-axis ray correctly hits the mating pin; it is not evidence of closure. A clear annular passage exists. Source front+Y rotated by actual PCB180deg faces outward, as expected. No source correction required.'),
    dict(name='USB_TypeB',references=['USB0'],front_y_mm=0,
         front_direction=[0,-1,0],axis_z_mm=5.31,
         open_tests=[dict(name='open chamfered entrance before tongue',x=0,z=5,
                          y=-.01,length=1.20,radius=.6),
                     dict(name='continuous mating passage alongside tongue',
                          x=3,z=4.5,y=-.01,length=9.50,radius=.5)],
         interpretation='Open chamfered shell/insulator mouth; recessed central tongue is expected for USB-B. No source correction required. Generic original-BOM body, not exact PN61729 CAD.'),
]

checks = []
def check(name, ok, **evidence):
    checks.append(dict(name=name, passed=bool(ok), **evidence))

records = []
for family in families:
    assignments = []
    models = []
    for ref in family['references']:
        fp = fps[ref]
        model = children(fp,'model')[0]
        model_path = Path(model[1].replace('${KIPRJMOD}',str(WORK/'ioboard')))
        at = list(map(float,one(fp,'at')[1:]))
        angle = at[2] if len(at)>2 else 0
        a = math.radians(angle)
        direction = family['front_direction']
        world_direction = [math.cos(a)*direction[0]-math.sin(a)*direction[1],
                           math.sin(a)*direction[0]+math.cos(a)*direction[1],0]
        transforms = {key:list(map(float,one(one(model,key),'xyz')[1:]))
                      for key in ['offset','rotate','scale']}
        check(ref+':canonical transforms preserved',
              transforms==dict(offset=[0,0,0],rotate=[0,0,0],scale=[1,1,1]),
              transforms=transforms)
        check(ref+':front points toward native negativeY rear edge',
              abs(world_direction[0])<1e-9 and abs(world_direction[1]+1)<1e-9,
              footprint_angle_deg=angle, native_front_direction=world_direction)
        assignments.append(dict(reference=ref,model=str(model_path.relative_to(REPO)),
                                sha256=sha(model_path),footprint_pose=at,
                                native_front_direction=world_direction,
                                transforms=transforms))
        models.append(model_path)
    check(family['name']+':all assignments use identical STEP bytes',
          len({sha(p) for p in models})==1)
    shape = Part.Shape()
    shape.read(str(models[0]))
    check(family['name']+':valid positive solids',
          shape.isValid() and all(s.isValid() and s.Volume>0 for s in shape.Solids),
          solids=len(shape.Solids))
    probes = []
    tests = list(family['open_tests'])
    if family['name']=='SDS50J':
        for i,angle in enumerate([25,155,225,270,315],1):
            a = math.radians(angle)
            tests.append(dict(name=f'contact{i} open to modeled blind floor',
                              x=3.5*math.cos(a),z=10+3.5*math.sin(a),
                              y=-.01,length=7.35,radius=.35))
    for test in tests:
        cylinder = Part.makeCylinder(test['radius'],test['length'],
                                     App.Vector(test['x'],test['y'],test['z']),
                                     App.Vector(0,1,0))
        intersections = [s.common(cylinder).Volume for s in shape.Solids]
        hit = sum(intersections)
        check(family['name']+':'+test['name'],hit<1e-7,
              material_intersection_mm3=hit,probe=test)
        probes.append(dict(**test,material_intersection_mm3=hit,passed=hit<1e-7))
    # The deliberately solid tongue/pin must remain present: a central ray is
    # not a valid openness criterion for these two families.
    expected_features=[]
    if family['name']=='PJ202AH':
        points=[(0,-2,6.5)]
    elif family['name']=='USB_TypeB':
        points=[(0,2,5)]
    else:
        points=[]
    for point in points:
        present=any(s.isInside(App.Vector(*point),1e-7,True) for s in shape.Solids)
        check(family['name']+':expected central mating feature retained',present,
              canonical_point_mm=point)
        expected_features.append(dict(canonical_point_mm=point,present=present))
    if family['name']=='MJ3536N':
        wide_probe=Part.makeCylinder(1.65,17.0,App.Vector(0,-3.01,5.5),
                                    App.Vector(0,1,0))
        hit_solids=[dict(index=i,volume_mm3=s.common(wide_probe).Volume)
                    for i,s in enumerate(shape.Solids)]
        # Record the actual contact intrusion separately instead of weakening
        # an entrance test or interpreting contact stock as a closed socket.
        positive=[h for h in hit_solids if h['volume_mm3']>1e-7]
        check('MJ3536N:wide internal probe meets only one small contact leaf',
              len(positive)==1 and 0<positive[0]['volume_mm3']<.1,
              intersections=hit_solids,
              note='A wider axial cylinder intersects upper contact leaf by0.08309mm3; clear entrance and central channel verified independently.')
        expected_features.append(dict(illustrative_contact_intrusion=hit_solids))
    bb=shape.optimalBoundingBox()
    records.append({k:v for k,v in family.items() if k!='open_tests'} | dict(
        assignments=assignments,valid=shape.isValid(),
        bounds_mm=[bb.XMin,bb.YMin,bb.ZMin,bb.XMax,bb.YMax,bb.ZMax],
        open_cylinder_probes=probes,expected_central_features=expected_features))

source_documents=[
    dict(path='kicad-working/visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/nys-216-manufacturer.dxf',
         url='https://www.rean-connectors.com/media/12224/download/nys-216-1.dxf?v=1',
         evidence='Drawing3102ST2201 revC2007:3/8-32UNEF thread,33mm overall,8mm axis. Canonical source actually follows this older drawing.'),
    dict(path='kicad-working/visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/nys216.pdf',
         url='https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1',
         evidence='Drawing3102ST2201 rev2015: same family but M11x1.25 thread; historical/current revision discrepancy. Do not use current nut dimensions to qualify older3/8 source or claim interchangeability.'),
    dict(path='kicad-working/visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/sds50j.pdf',
         url='https://www.sameskydevices.com/product/resource/sds-j.pdf',
         evidence='Page3 SDS50J front view shows five socket mouths in a recessed insert,7mm PCD and correct25/45degree pattern. Actual modeled blind-depth not dimensioned.'),
    dict(path='kicad-working/validation/models-review-10/rear-connector-quality/sources/mj-3536n-current.pdf',
         url='https://www.sameskydevices.com/product/resource/mj-3536n.pdf',
         evidence='Page2 shows open3.6mm bushing,6mm outside diameter and side/top spring contacts; depth reconstruction remains illustrative.'),
    dict(path='kicad-working/validation/models-review-10/rear-connector-quality/sources/pj-202ah-current.pdf',
         url='https://www.sameskydevices.com/product/resource/pj-202ah.pdf',
         evidence='Page2 shows open6.5mm mouth,2mm center pin and9mm maximum plug insertion. Pin intentionally blocks center-axis ray.'),
    dict(path='kicad-working/ioboard/3dmodels/Revision6/rear-body-illustrations/provenance/source/kc-301021-web-extract.json',
         url='https://www.mouser.com/catalog/specsheets/KC-301021.pdf',
         evidence='Retained primaryPDF text extraction only; local binaryPDF unavailable. Generic chamfered USB-B opening and tongue, exact historicalPN61729 fit unqualified.'),
]
for source in source_documents:
    source['sha256']=sha(REPO/source['path'])
check('source PCB unchanged',sha(pcb)==pcb_hash)
for record in records:
    for assignment in record['assignments']:
        check(assignment['reference']+':source STEP unchanged',
              sha(REPO/assignment['model'])==assignment['sha256'])
result=dict(passed=all(c['passed'] for c in checks),checks_count=len(checks),
            failed_checks=[c for c in checks if not c['passed']],
            scope='Read-only installed STEP audit, five families, eleven rear connector references. Does not audit scene proxies or qualify physical plug fit.',
            method='Read installed STEP with FreeCAD1.0.1/OpenCascade; exact BRep cylinder-common probes through entrance and mating channels; validate actual zero/native assignments and outward direction.',
            PCB_sha256=pcb_hash,records=records,checks=checks,
            source_documents=source_documents,
            source_visual_review='Visually inspected freshly rendered SDS50J page3 and NYS216 PDF, retained olderNYS216DXF render, and currentMJ/PJ page2 drawings.',
            source_model_corrections_required=False,
            limitations=['All source bores/internal contacts are illustrations with documented unsized details. Passing probes show a continuous visible opening only.',
                         'SDS50J socket depth is shallow and unqualified; all five contact mouths are open but blind at nominal Y7.4.',
                         'No scene, mesh, project, source geometry, placement or routing was changed.'])
(HERE/'source-opening-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['passed','checks_count','failed_checks']},indent=2))
