"""Fresh source-body, continuous full-width leads, actual pad/drill/polarity audit."""
from pathlib import Path
import hashlib,json,math,sys
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part,Mesh
H=Path(__file__).resolve().parent;W=H.parents[2];V=A.Vector
sys.path.insert(0,str(W.parent/'kicad-import/validation'))
from verify_native_projects import parse_sexpr,children,one,property_value
m=json.loads((H/'led-assembly-manifest.json').read_text());p=m['parts'][0];assignment=m['assignments'][0]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=Part.read(p['step']);stock=Part.read(p['stock_source_step']);checks=[]
def check(name,value,detail=None):checks.append({'check':name,'passed':bool(value),'detail':detail})
check('Final STEP hash matches manifest',sha(Path(p['step']))==p['source_sha256'])
check('STEP valid positive volume',r.isValid() and r.Volume>0)
check('Three separate color-role solids',len(r.Solids)==3)
check('Complete union is one connected valid solid',len(r.Solids[0].multiFuse(r.Solids[1:]).removeSplitter().Solids)==1)
head=max(r.Solids,key=lambda s:s.Volume);old_head=stock.common(Part.makeBox(20,20,20,V(-8,-10,3)))
inverse=head.copy();inverse.translate(V(0,0,-3.096));ab=inverse.cut(old_head).Volume;ba=old_head.cut(inverse).Volume
check('Exact generic source head preserved under inverse translation',ab<1e-7 and ba<1e-7,{'new_minus_source_mm3':ab,'source_minus_new_mm3':ba})
check('Head volume unchanged',abs(head.Volume-old_head.Volume)<1e-7)
check('Lower body at selected BOM6.096mm datum',abs(head.BoundBox.ZMin-6.096)<1e-7)
check('Complete source body height8.6mm retained',abs(head.BoundBox.ZLength-8.6)<1e-7)
leads=sorted((s for s in r.Solids if s.Volume<10),key=lambda s:s.CenterOfMass.x)
for i,(s,x) in enumerate(zip(leads,[0,2.54])):
 b=s.BoundBox
 check('Lead'+str(i)+' full0.4squarewidth unchanged',abs(b.XLength-.4)<1e-7 and abs(b.YLength-.4)<1e-7)
 check('Lead'+str(i)+' fullheight continuous toPCB tail',abs(b.ZMin+2.5)<1e-7 and abs(b.ZMax-6.096)<1e-7)
 check('Lead'+str(i)+' axis preserved',abs(s.CenterOfMass.x-x)<1e-7 and abs(s.CenterOfMass.y)<1e-7)
 for z in [-2.499,-1.6,-.8,0,.8,3,5.9]:
  section=s.common(Part.makeBox(2,2,.001,V(x-1,-1,z)))
  check('Lead'+str(i)+' section atZ'+str(z),abs(section.Volume-.00016)<1e-8,{'slab_volume_mm3':section.Volume})
check('Complete STL closed',Mesh.Mesh(p['stl']).isSolid())
for seg in p['segments']:check(seg['name']+' STL closed',Mesh.Mesh(str(H/seg['stl'])).isSolid())
board=W/'validation/models-review-10/input-snapshot/mainboard/mainboard.kicad_pcb'
if not board.exists():board=W/'mainboard/mainboard.kicad_pcb'
ast=parse_sexpr(board.read_text())
fps={property_value(f,'Reference','reference'):f for f in children(ast,'footprint')};rows=[]
for ref in assignment['references']:
 f=fps[ref];pads={p[1]:p for p in children(f,'pad')};model=one(f,'model')
 assert len(children(f,'model'))==1
 actual={'offset_mm':list(map(float,one(one(model,'offset'),'xyz')[1:])),
 'rotation_deg':list(map(float,one(one(model,'rotate'),'xyz')[1:])),
 'scale':list(map(float,one(one(model,'scale'),'xyz')[1:]))}
 check(ref+' native model transforms retained',all(actual[k]==assignment[k] for k in actual))
 # Existing source offset plus180deg rotation maps sourceX0->K(+1.27), X2.54->A(-1.27).
 for pin,x in [('K',0),('A',2.54)]:
  transformed=[1.27-x,0];pad=pads[pin];xy=list(map(float,one(pad,'at')[1:3]));drill=float(one(pad,'drill')[1]);residual=math.dist(transformed,xy);margin=drill/2-math.sqrt(2)*.2
  check(ref+'.'+pin+' polarity/axis matches originalpad',residual<1e-7)
  check(ref+'.'+pin+' unthinned square lead fits nominal actual drill',margin>0,{'drill_mm':drill,'corner_radius_mm':math.sqrt(2)*.2,'radial_margin_mm':margin})
  rows.append({'reference':ref,'pin':pin,'layer':one(f,'layer')[1],'source_lead_axis_X_mm':x,'mapped_footprint_axis_mm':transformed,'actual_footprint_pad_axis_mm':xy,'axis_residual_mm':residual,'original_drill_mm':drill,'nominal_square_lead_corner_margin_mm':margin})
check('All40LED refs and80originalpad holes checked',len(rows)==80 and len(assignment['references'])==40)
report={'passed':all(c['passed'] for c in checks),'checks_passed':sum(c['passed'] for c in checks),'checks':checks,'pad_checks':rows,'source_head_symmetry_mm3':[ab,ba],
 'board_input':str(board),'board_input_sha256':sha(board),'geometry_step_sha256':sha(Path(p['step'])),
 'source_conflict':{'selected_BOM_STD240B_height_mm':6.096,'sequencer_table_alternative_mm':5.588,'source_height_choice_is_measured_fit':False},
 'limits':p['limitations']}
(H/'led-assembly-geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'checks_passed':report['checks_passed'],'pad_checks':len(rows),'minimum_nominal_drill_margin_mm':min(r['nominal_square_lead_corner_margin_mm'] for r in rows)},indent=2));assert report['passed']
