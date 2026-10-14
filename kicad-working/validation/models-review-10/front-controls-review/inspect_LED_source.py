from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as A
import Part
H=Path(__file__).resolve().parent
p=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels/LED_THT.3dshapes/LED_D5.0mm.step')
s=Part.read(str(p));rows=[]
for index,solid in enumerate(s.Solids):
 b=solid.BoundBox
 rows.append({'solid':index,'bounds_mm':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],'volume_mm3':solid.Volume})
r={'source':str(p),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'solids':rows,'note':'Official generic LED package file; solid identity inferred from envelope only. Not an original-vendor LED dimensional specification.'}
(H/'generic-LED-source-bounds.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
planes=[]
for index,face in enumerate(s.Faces):
 b=face.BoundBox
 if abs(b.ZMax-b.ZMin)<1e-6:
  planes.append({'face_index':index,'z_mm':b.ZMin,'area_mm2':face.Area})
r['horizontal_faces']=planes
r['generic_LED_lens_lower_flange_datum_z_mm']=3.0
r['body_datum_evidence']='The large lower body/flange plane occurs atZ3mm. Below it the only occupied cross-section is the two leads.'
probes=[]
for z in [2.9,3.1]:
 slab=Part.makeBox(20,20,.001,A.Vector(-10,-10,z))
 probes.append({'z_mm':z,'slab_thickness_mm':.001,'approx_occupied_area_mm2':s.common(slab).Volume/.001})
r['body_datum_section_probes']=probes
(H/'generic-LED-source-bounds.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'planes':planes,'section_probes':probes},indent=2))
