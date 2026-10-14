"""Detailed exact-family drawing-derived rear connector candidates.

SPDX-License-Identifier: CC0-1.0
No project, existing model or Blender scene is changed. Published nominal outer
sizes govern; unsized internal/molding details are explicit reconstructions.
"""
from pathlib import Path
import hashlib,json,math,re
import FreeCAD as App
import Part,Mesh
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];V=App.Vector
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
GUARDS={str(WORK/b/(b+'.kicad_pcb')):sha(WORK/b/(b+'.kicad_pcb'))for b in ['mainboard','ioboard']}
COLORS={'housing':[.025,.027,.03],'cover':[.045,.047,.05],'contact':[.6,.61,.63],'bronze':[.57,.42,.21]}

def box(w,d,h,y=0,z=0,x=None):return Part.makeBox(w,d,h,V(-w/2 if x is None else x,y,z))
def cy(r,d,y,z,x=0):return Part.makeCylinder(r,d,V(x,y,z),V(0,1,0))
def prism(points,y,d):
 vv=[V(x,y,z)for x,z in points];return Part.Face(Part.makePolygon(vv+[vv[0]])).extrude(V(0,d,0))
def fuse(parts):
 s=parts[0]
 for p in parts[1:]:s=s.fuse(p)
 return s.removeSplitter()
def cut(s,t):return s.cut(t).removeSplitter()
def bbox(s):
 b=s.BoundBox;return dict(min_mm=[b.XMin,b.YMin,b.ZMin],max_mm=[b.XMax,b.YMax,b.ZMax],size_mm=[b.XLength,b.YLength,b.ZLength])

def face_colors(path,palette):
 raw=path.read_text();ent={int(n):body for n,body in re.findall(r'#(\d+)\s*=\s*(.*?);',raw,re.S)};breps=[int(n)for n in re.findall(r'#(\d+)\s*=\s*MANIFOLD_SOLID_BREP',raw)];assert len(breps)==len(palette)
 extra=[];next_id=max(ent)+1
 def add(body):
  nonlocal next_id
  i=next_id;next_id+=1;extra.append(f'#{i} = {body};');return i
 roles=[]
 for brep,rgb in zip(breps,palette):
  shell=int(re.findall(r'#(\d+)',ent[brep])[0]);faces=list(map(int,re.findall(r'#(\d+)',ent[shell])));assert all(ent[f].lstrip().startswith('ADVANCED_FACE')for f in faces)
  context=None
  for body in ent.values():
   if body.startswith(('SHAPE_REPRESENTATION','ADVANCED_BREP_SHAPE_REPRESENTATION')):
    rr=list(map(int,re.findall(r'#(\d+)',body)))
    if brep in rr:context=rr[-1];break
  if context is None:context=next(i for i,b in ent.items()if 'GEOMETRIC_REPRESENTATION_CONTEXT(3)'in b)
  c=add("COLOUR_RGB('',"+','.join(map(str,rgb))+')');f=add(f"FILL_AREA_STYLE_COLOUR('',#{c})");f=add(f"FILL_AREA_STYLE('',(#{f}))");f=add(f'SURFACE_STYLE_FILL_AREA(#{f})');f=add(f"SURFACE_SIDE_STYLE('',(#{f}))");f=add(f'SURFACE_STYLE_USAGE(.BOTH.,#{f})');f=add(f'PRESENTATION_STYLE_ASSIGNMENT((#{f}))');styles=[add(f"STYLED_ITEM('',(#{f}),#{face})")for face in faces];add("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',("+','.join('#'+str(i)for i in styles)+f'),#{context})');roles.append(dict(brep=brep,faces=len(faces),color=rgb))
 pos=raw.rfind('ENDSEC;');path.write_text(raw[:pos]+'\n'+'\n'.join(extra)+'\n'+raw[pos:]);return roles

# SDS-50J nominal envelope and exact printed mating/mounting patterns.
flange=box(20,1.8,21.1)
main=cy(9,10.3,1.8,9)
main=fuse([main,box(15,10.3,1.8,y=1.8)])
housing=fuse([flange,main])
housing=cut(housing,cy(7.1,7.5,-.1,10))
# Traced keyed mating cavity and the lower ground relief; unsized details.
housing=cut(housing,box(2.6,7.5,1.8,y=-.1,z=15.5))
housing=cut(housing,box(2.0,2.0,2.0,y=-.1,z=1.8))
mount=[]
for angle in [90,205,335]:
 a=math.radians(angle);x=9.5*math.cos(a);z=10+9.5*math.sin(a);mount.append([x,z]);housing=cut(housing,cy(.8,2,-.1,z,x));housing=cut(housing,cy(1.0,.25,-.05,z,x))
cover=fuse([box(15,1.4,13.6,y=12.1),box(3.6,2.3,11.0,y=13.5,z=2.5)])
insert=cy(6.65,1.6,5.8,10)
# Source contact PCD7 and25/45deg orientations. Elongated sockets trace the
# figure, with a central bore and rectangular outer keyway; no terminals.
contact_centers=[];sockets=[]
for angle in [25,155,225,270,315]:
 a=math.radians(angle);x=3.5*math.cos(a);z=10+3.5*math.sin(a);contact_centers.append([x,z]);tool=box(1.55,1.9,3.0,y=5.65,z=z-1.5,x=x-.775);tool.rotate(V(x,0,z),V(0,1,0),-(angle-90));insert=cut(insert,tool)
 ring=cut(cy(.72,1.3,5.95,z,x),cy(.43,1.5,5.85,z,x));sockets.append(ring)
# Source key orientation: notch at top, one lower center key relief.
insert=cut(insert,box(2.2,1.9,1.5,y=5.65,z=15.2));insert=cut(insert,box(1.1,1.9,1.3,y=5.65,z=3.4))
sds_segments=[('Housing','housing',housing),('RearCover','cover',cover),('SocketInsert','housing',insert)]+[(f'MatingSocket{i+1}','contact',s)for i,s in enumerate(sockets)]

# NYS216 rib stations and 17mm-wide top windows traced from primaryDXF at2:1.
# Printed33±0.5overall and15.5bodyheight govern instead of conflicting unsized
# rawDXF overall33.75 and drawn ribheight15.3. No scene fit is used to set them.
body=box(20,22.45,15.5)
for start,end in [(2.25,7.5),(8.6,13.85),(14.95,20.2)]:
 body=cut(body,box(17,end-start,8.0,y=start,z=7.6))
 # Side circular molding/retention marks visible in the manufacturer view.
 for sign in [-1,1]:
  tool=Part.makeCylinder(.5,1.7,V(sign*10.1,(start+end)/2,5.0),V(-sign,0,0));body=cut(body,tool)
rear=box(9.2,2.05,9.2,y=22.45,z=3.4)
body=fuse([body,rear]);body=cut(body,cy(3.175,24.7,-.1,8))
# Thread3/8-32UNEF: nominal9.525major and0.79375pitch. Circular grooves illustrate
# the pitch; they are not a manufacturable helical thread or tolerance model.
nose=cut(cy(9.525/2,8.5,-8.5,8),cy(3.175,8.7,-8.6,8))
for i in range(10):
 y=-8.15+i*(25.4/32);torus=Part.makeTorus(9.525/2,.12,V(0,y,8),V(0,1,0));nose=cut(nose,torus)
# Bowed leaf contacts are three visible reconstructed sheet strips, contained
# inside windows. Their unsized curvature/stock is illustrative, not lead-fit.
leaves=[]
for start,end in [(2.25,7.5),(8.6,13.85),(14.95,20.2)]:
 pts=[(start+.35,8.05),(start+1.25,9.25),(start+2.55,10.15),(end-.5,8.5),(end-.25,8.7),(start+2.55,10.48),(start+1.1,9.5),(start+.1,8.25)]
 vv=[V(-2.9,y,z)for y,z in pts];leaf=Part.Face(Part.makePolygon(vv+[vv[0]])).extrude(V(1.35,0,0));leaves.append(leaf)
nys_segments=[('RibbedHousing','housing',body),('ThreadedNose','housing',nose)]+[(f'VisibleLeafContact{i+1}','bronze',s)for i,s in enumerate(leaves)]

SOURCES={
 'sds':dict(url='https://www.sameskydevices.com/product/resource/sds-j.pdf',filename='source/sds50j.pdf',sha256=sha(HERE/'source/sds50j.pdf'),page=3,date='2024-09-12'),
 'nys_dxf':dict(url='https://www.rean-connectors.com/media/12224/download/nys-216-1.dxf?v=1',filename='source/nys-216-manufacturer.dxf',sha256=sha(HERE/'source/nys-216-manufacturer.dxf'),drawing='3102ST2201',revision='C2007; original2004',drawing_to_physical_scale=.5),
 'nys_pdf':dict(url='https://www.rean-connectors.com/media/9014/download/nys-216.pdf?v=1',filename='source/nys216.pdf',sha256=sha(HERE/'source/nys216.pdf'))}
common=['Detailed body reconstruction from primary manufacturer drawings; not recovered manufacturer3DCAD.','Canonical original F.Cu footprint frame X,-Y,Z outward, no placed board/case pose baked in; all native assignment transforms remain zero offset/rotation and unity scale.','Unconfirmed solder terminals and locators are omitted; visible mating/contact illustrations are not electrical lead geometry.','Unsized details are traced/interpreted within published nominal envelopes; no factorytolerance, terminalfit, historicalrevision or enclosurefit qualification.']
groups=[dict(id='SDS50J_DatasheetDerived_DetailedBody',footprint='CP-2350',references=['DIN1','DIN2','DIN3','DIN4'],segments=sds_segments,sources=[SOURCES['sds']],dimensions=dict(width_mm=20,depth_max_mm=15.8,height_mm=21.1,flange_thickness_mm=1.8,contact_pcd_mm=7,mounting_pcd_mm=19,mounting_hole_diameter_mm=1.6,mounting_angles_deg=[90,205,335],contact_angles_deg=[25,155,225,270,315]),improvements=['Correct printed25/45degree contact orientations and25degree lower mountingholes.','Keyed mating cavity, elongated socket recesses and separate visible tin/contact sleeves.','Separated molded housing/rearcover/insert with source-derived step profile; current-family fullenvelope retained.'],limits=common+['CurrentSDS-J drawing differs from historical2005CUI drawing in flange detail/thickness; candidate is exactSDS50J currentfamily, not proven identical2005mold.','Mating cavity14.2diameter, socket dimensions, minor reliefs and rearcover steps are unsized visual reconstructions; outerenvelope and printed PCD/holepatterns are authoritative.']),dict(id='NYS216_DrawingDerived_DetailedBody',footprint='REAN_1_4STERO',references=['HEADPHONE0','MIXIN0','MIXOUT0'],segments=nys_segments,sources=[SOURCES['nys_dxf'],SOURCES['nys_pdf']],dimensions=dict(width_mm=20,overall_depth_mm=33,body_depth_mm=24.5,ribbed_body_depth_mm=22.45,body_height_mm=15.5,socket_axis_z_mm=8,nose_projection_mm=8.5,thread_major_diameter_mm=9.525,thread_pitch_mm=25.4/32,mating_bore_diameter_mm=6.35,window_width_mm=17,window_stations_y_mm=[[2.25,7.5],[8.6,13.85],[14.95,20.2]]),improvements=['Three open contactwindows and source-derived rib stations replace the former solid box.','Separate rearprojection, matingbore,3/8-32nominalnose andvisible leafcontactstrips.','Bodyheight15.5 and threadedmajor9.525 followprintedmanufacturerbody/threadcallouts; prior16.5/11 coarse envelope values were conservative/approximate, not exactbody dimensions.'],limits=common+['ManufacturerDXF modelspace is drawing2:1, normalizedby0.5; rawoveralloutline33.75 conflicts with printed33±0.5; printed33nominal governs reconstructed outerlength.','DXF drawnribheight15.3 differs from printed15.5bodyheight; printed15.5nominal governs.16.5 is also shown forfront/hardware orPCBpitch, not uniformly solidhousingheight.','Official currentproductpage reports8.2mmtoPCB while drawingaxisis8.0; actualbodyseat/feetgap is unmeasured and candidate retainsdrawingaxis8.0.','Circular threadgrooves are visual pitch markers, not a truehelix. Leafcontactcurves, stockthickness, topwindowdepth and side marks are unsized reconstructions.','Nut/washer omitted because existingscene providesseparateexteriorhardware; do not duplicateorclaimcompatibility fromtheseillustrations.'])]
parts=[];assignments=[];audit=[]
for g in groups:
 doc=App.newDocument(g['id']);objects=[];segments=[];palette=[]
 for name,material,shape in g['segments']:
  assert shape.isValid()and shape.Volume>0,name
  o=doc.addObject('PartDesign::Feature',name);o.Shape=shape;objects.append(o);stl=HERE/(g['id']+'_'+name+'.stl');mesh=Mesh.Mesh(shape.tessellate(.035));mesh.write(str(stl));segments.append(dict(name=name,role=material,stl=str(stl),units='mm',rgba=COLORS[material]+[1],bounds=bbox(shape),triangles=mesh.CountFacets,sha256=sha(stl)));palette.extend([COLORS[material]]*len(shape.Solids))
 doc.recompute();combined=Part.makeCompound([o.Shape for o in objects]);stl=HERE/(g['id']+'.stl');mesh=Mesh.Mesh(combined.tessellate(.035));mesh.write(str(stl));step=HERE/(g['id']+'.step');Part.export(objects,str(step));original=Part.Shape();original.read(str(step));roles=face_colors(step,palette);reread=Part.Shape();reread.read(str(step));assert reread.isValid()and original.exportBrepToString()==reread.exportBrepToString();doc.saveAs(str(HERE/(g['id']+'.FCStd')));App.closeDocument(doc.Name)
 row={k:v for k,v in g.items()if k!='segments'};row.update(board='ioboard',classification='Detailed exact-family drawing-derived body illustration; not manufacturerCAD, terminalfit unqualified',step=str(step),source_model=str(step),source_sha256=sha(step),stl=str(stl),stl_sha256=sha(stl),units='mm',bounds=bbox(combined),mesh_parts=segments,valid=True,solid_count=len(reread.Solids),triangles=mesh.CountFacets,color_roles=roles,source_urls=[s['url']for s in g['sources']],canonical_frame='Original F.Cu footprint X,-Y,Z outward; millimetres; sourcefrontY0, bodyinto+Y. No placed transform baked in.',offset_mm=[0,0,0],scale=[1,1,1],rotation_deg=[0,0,0],source_kind='Original parameterized primary-drawing reconstruction with explicit unsized details',limitations=g['limits'])
 parts.append(row);assignments.append({k:row[k]for k in ['board','references','footprint','source_model','source_sha256','offset_mm','scale','rotation_deg','source_kind','classification','limitations','source_urls','units']});audit.append(dict(id=g['id'],valid=True,step_geometry_unchanged_by_color_styles=True,solid_count=len(reread.Solids),bounds=bbox(reread),triangles=mesh.CountFacets,volume_mm3=reread.Volume))
assert GUARDS=={p:sha(p)for p in GUARDS}
out=dict(date='2026-10-14',scope='Two detailed rearconnector body candidates for7references; no sourceprojects/scenes/models edited.',manufacturer_CAD_recovered=False,canonical_frame='Original F.Cu footprint X,-Y,Z outward',parts=parts,assignments=assignments,instance_count=7,geometry_license='CC0-1.0 original generated reconstruction only; manufacturerdrawingrights retained.',source_availability='source/cad-availability.json',source_project_hashes=GUARDS,source_projects_unchanged=True,audit=audit)
(HERE/'rear-quality-manifest.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(passed=True,families=2,instances=7,triangles=sum(r['triangles']for r in audit),bounds=[r['bounds']for r in audit]),indent=2))
