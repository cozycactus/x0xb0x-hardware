"""Independent read-only native STEP and actual Q22 nominal-section audit."""
from pathlib import Path
import hashlib
import json
import math
import sys

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part

HERE=Path(__file__).resolve().parent
STEP=HERE/'Mitsubishi_2SC2291_MaxBody_FormedP2p286.step'
MANIFEST=HERE/'legacy-quality-manifest.json'
PAD_INPUT=HERE/'independent-2sc2291-actual-pad-input.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs=json.loads(PAD_INPUT.read_text())
manifest=json.loads(MANIFEST.read_text())
watched=[STEP,MANIFEST,Path(inputs['pcb']),Path(inputs['cache'])]
before={str(p):sha(p) for p in watched}
checks=[]

def check(name,passed,evidence=None):
    checks.append({'name':name,'passed':bool(passed),'evidence':evidence})

def near(a,b,tol=1e-6):
    return abs(a-b)<=tol

def vecnear(a,b,tol=1e-6):
    return len(a)==len(b) and all(near(x,y,tol) for x,y in zip(a,b))

def bounds(shape):
    b=shape.BoundBox
    return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]

def exactbounds(shape):
    b=shape.optimalBoundingBox()
    return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]

shape=Part.read(str(STEP))
check('Native STEP valid',shape.isValid())
check('Final frozen STEP identity',before[str(STEP)]=='e77a4406c0eec3750b4db057ca88ac00c49cc46bdb9f72ee2ebd5b268029909b',before[str(STEP)])
check('Exact trimmed complete-component bounds',vecnear(exactbounds(shape),[-4.797,-1.4,-2.5,4.797,2.2,8.6]),{'exact_optimal_bounds_mm':exactbounds(shape),'conservative_ordinary_bounds_mm':bounds(shape)})
check('Manifest exact trimmed bounds agree',vecnear(exactbounds(shape),manifest['parts'][0]['exact_bounds_mm']),manifest['parts'][0]['exact_bounds_mm'])
check('Six separately colored geometry solids',len(shape.Solids)==6,len(shape.Solids))
for i,s in enumerate(shape.Solids):
    check('Solid%d valid and positive volume'%i,s.isValid() and s.Volume>0,{'volume_mm3':s.Volume,'bounds_mm':bounds(s)})
body=max(shape.Solids,key=lambda s:s.Volume)
leads=sorted([s for s in shape.Solids if not s.isSame(body)],key=lambda s:s.CenterOfMass.x)
check('Maximum body bounds',vecnear(bounds(body),[-4.05,-1.4,3,4.05,2.2,8.6]),bounds(body))
check('Maximum body volume with exact2x2 YZ rear bevel',near(body.Volume,8.1*(3.6*5.6-2)),body.Volume)
expected_profile=[(-1.4,3),(2.2,3),(2.2,6.6),(.2,8.6),(-1.4,8.6)]
actual_vertices=[list(v.Point) for v in body.Vertexes]
check('Body has ten extrusion vertices',len(actual_vertices)==10,actual_vertices)
for x in [-4.05,4.05]:
    for y,z in expected_profile:
        check('Body vertex%s'%([x,y,z]),any(vecnear(p,[x,y,z]) for p in actual_vertices))
bevel_faces=[]
for f in body.Faces:
    pts=[list(v.Point) for v in f.Vertexes]
    if len(pts)==4 and all(near(p[1]+p[2],8.8) for p in pts):
        bevel_faces.append({'vertices_mm':pts,'area_mm2':f.Area})
check('Single correct rear+Y YZ bevel face',len(bevel_faces)==1,bevel_faces)
check('Bevel face area',len(bevel_faces)==1 and near(bevel_faces[0]['area_mm2'],8.1*math.sqrt(8)),bevel_faces)
check('Actual reference SSIP5 F.Cu180deg',inputs['footprint']=='SSIP5' and inputs['layer']=='F.Cu' and near(inputs['orientation_deg'],180),{'footprint':inputs['footprint'],'layer':inputs['layer'],'angle_deg':inputs['orientation_deg']})
check('Actual board1.6mm thickness',near(inputs['board_thickness_mm'],1.6),inputs['board_thickness_mm'])
check('Actual five pad identities',[p['pin'] for p in inputs['pads']]==list('12345'))
check('Heterogeneous SSIP5 cache has zero model nodes',inputs['cache_model_nodes']==0,inputs['cache_model_nodes'])
check('Manifest assigns Q22 only',len(manifest['assignments'])==1 and manifest['assignments'][0]['references']==['Q22'])
check('Manifest STEP digest matches fresh import',manifest['parts'][0]['source_sha256']==before[str(STEP)])

planes=[-.001,-.1,-.4,-.8,-1.2,-1.5,-1.599]
records=[]
for i,(lead,pad) in enumerate(zip(leads,inputs['pads'])):
    expected_tail=[(i-2)*2.286,0]
    actual_pad=pad['canonical_xy_mm']
    check('Pin%d actual pad retains2.286mm pitch'%(i+1),vecnear(actual_pad,expected_tail),actual_pad)
    check('Pin%d actual round drill1mm'%(i+1),vecnear(pad['drill_xy_mm'],[1,1]) and pad['drill_shape']==1,pad['drill_xy_mm'])
    for z in planes+[2.9]:
        wires=lead.slice(App.Vector(0,0,1),z)
        check('Pin%d Z%s single closed section'%(i+1,z),len(wires)==1 and wires[0].isClosed(),{'wire_count':len(wires)})
        if len(wires)!=1:
            continue
        face=Part.Face(wires[0])
        center=face.CenterOfMass
        expected=[(i-2)*1.25,0] if z==2.9 else actual_pad
        points=[p for e in wires[0].Edges for p in e.discretize(257)]
        radii=[math.hypot(p.x-expected[0],p.y-expected[1]) for p in points]
        center_error=math.hypot(center.x-expected[0],center.y-expected[1])
        maxradius=max(radii)
        minradius=min(radii)
        radius=math.sqrt(face.Area/math.pi)
        margin=pad['drill_xy_mm'][0]/2-maxradius if z!=2.9 else None
        record={'pin':pad['pin'],'z_mm':z,'purpose':'nominal package root pitch' if z==2.9 else 'straight tail inside board lamination','measured_center_xy_mm':[center.x,center.y],'expected_xy_mm':expected,'center_error_mm':center_error,'section_area_mm2':face.Area,'area_equivalent_diameter_mm':2*radius,'sampled_radius_min_max_mm':[minradius,maxradius],'nominal_hole_radial_margin_mm':margin,'section_bounds_mm':bounds(face)}
        records.append(record)
        check('Pin%d Z%s center'%(i+1,z),center_error<1e-6,center_error)
        check('Pin%d Z%s fullD.45 circular section'%(i+1,z),near(face.Area,math.pi*.225**2,1e-6) and abs(minradius-.225)<1e-5 and abs(maxradius-.225)<1e-5,record)
        if margin is not None:
            check('Pin%d Z%s circle inside actual nominal drill'%(i+1,z),margin>0 and near(margin,.275,1e-5),margin)

joined=shape.Solids[0]
for s in shape.Solids[1:]:
    joined=joined.fuse(s)
check('Body and five lead roots form one valid joined solid',joined.isValid() and len(joined.Solids)==1,{'solids':len(joined.Solids),'volume_mm3':joined.Volume})
after={str(p):sha(p) for p in watched}
check('Model manifest and actual project/cache unchanged during independent audit',before==after,{'before':before,'after':after})
check('Actual board/cache match fresh native pad extraction',all(after[p]==digest for p,digest in inputs['source_sha256_before'].items()))
report={'passed':all(c['passed'] for c in checks),'check_count':len(checks),'failed_checks':[c for c in checks if not c['passed']],'scope':'Fresh independent FreeCAD STEP geometry and native pcbnew actual-pad nominal fit audit; no model/project edits.','step':str(STEP),'step_sha256':before[str(STEP)],'manifest_sha256':before[str(MANIFEST)],'body_bounds_mm':bounds(body),'whole_component_optimal_bounds_mm':exactbounds(shape),'whole_component_conservative_ordinary_bounds_mm':bounds(shape),'bounds_method':'FreeCAD optimalBoundingBox for exact trimmed analytic BRep extrema; ordinary BoundBox reported separately as conservative.','supersedes_step_sha256':'17b749a4af12772c552d83ee7ab597cf29e9157b21eb846c455e64ba00d9c41c','body_volume_mm3':body.Volume,'bevel_faces':bevel_faces,'tail_planes_z_mm':planes,'package_root_plane_z_mm':2.9,'actual_Q22':inputs,'section_measurements':records,'minimum_tail_nominal_radial_margin_mm':min(r['nominal_hole_radial_margin_mm'] for r in records if r['nominal_hole_radial_margin_mm'] is not None),'limits':['8.1x3.6x5.6 body dimensions are manufacturer maxima;1.25pitch/.45diameter/2x2bevel are representative unless otherwise toleranced.','Z3 body stand-off, curved fanout and trimmed tails are reconstruction choices, not manufacturer installed forming specifications.','Nominal circle-in-drill checks exclude actual lead/drill/plating tolerances, stress, springback, soldering and mechanical process/hardware proof.','This audit checks canonical model and actual unmodified footprint coordinates; native KiCad import and saved Blender pose require separate final integration review.'],'checks':checks,'source_sha256_after':after}
(HERE/'independent-2sc2291-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['passed','check_count','failed_checks','step_sha256','body_bounds_mm','body_volume_mm3','minimum_tail_nominal_radial_margin_mm']},indent=2))
if not report['passed']:
    sys.exit(1)
