"""Canonical TL1100 manufacturer CAD candidates with bounded internal repair.

SPDX-License-Identifier: CC0-1.0 for this alignment/review script only.
Manufacturer source CAD retains original rights. Real projects stay read-only.
"""
from pathlib import Path
import hashlib,json,math,re,sys
import FreeCAD as App,Part,Mesh
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2];V=App.Vector
sys.path.insert(0,str(WORK.parent/'kicad-import/validation'))
from resolve_native_footprint_fields import parse,prop
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=HERE/'sources/TL1100Fxxxx-manufacturer.stp';SOURCEHASH='c8d75086238d6ab7716c6dc38c2d587c8d39ba9cc365655c49a244b4ca88d430';assert sha(source)==SOURCEHASH
raw=Part.Shape();raw.read(str(source));assert not raw.isValid()and len(raw.Solids)==1
bad=[(i,f)for i,f in enumerate(raw.Faces)if not f.isValid()];assert len(bad)==1 and abs(bad[0][1].Area)<1e-12
roi=Part.makeCylinder(1.5001,.035,V(0,0,-2.1925));repaired=raw.fuse(roi);assert repaired.isValid()and len(repaired.Solids)==1
bbox=lambda s:[s.BoundBox.XMin,s.BoundBox.YMin,s.BoundBox.ZMin,s.BoundBox.XMax,s.BoundBox.YMax,s.BoundBox.ZMax]
assert max(abs(a-b)for a,b in zip(bbox(raw),bbox(repaired)))<1e-10
volume_delta=repaired.Volume-raw.Volume;full=repaired.copy();full.translate(V(0,0,3.8825));assert abs(full.BoundBox.ZMax-7.3)<1e-10 and abs(full.BoundBox.ZMin+3.5)<1e-10
body=full.common(Part.makeBox(40,40,10,V(-20,-20,0)));assert body.isValid()and len(body.Solids)==1
# Remove a larger local ROI from both originals to confirm all outside geometry
# is equal as CAD boolean symmetric difference, independent of face ordering.
outer_roi=Part.makeBox(3.2,3.2,.1,V(-1.6,-1.6,-2.225));outside_before=raw.cut(outer_roi);outside_after=repaired.cut(outer_roi);outside_valid=outside_before.isValid()and outside_after.isValid();outside_diff=outside_before.cut(outside_after).Volume+outside_after.cut(outside_before).Volume;assert outside_valid and abs(outside_diff)<1e-8

lib=WORK/'mainboard/mainboard-import-fps.pretty/B3F-40XX.kicad_mod';l=parse(lib.read_text());pads=[]
for pad in l.children('pad'):
 at=[float(a.value)for a in pad.first('at').items[1:3]];dr=float(pad.first('drill').items[1].value);pads.append(dict(number=pad.items[1].value,canonical_xy_mm=[at[0],-at[1]],drill_mm=dr))
assert len(pads)==4 and all(abs(p['drill_mm']-1.1938)<1e-8 for p in pads)
refs=['S'+str(i)for i in range(5,28)];board=WORK/'mainboard/mainboard.kicad_pcb';pcb=parse(board.read_text());sourcepcbhash=sha(board);poses=[]
for fp in pcb.children('footprint'):
 ref=prop(fp,'Reference').value
 if ref in refs:
  poses.append(dict(reference=ref,at_mm_deg=[float(a.value)for a in fp.first('at').items[1:]],side=fp.first('layer').items[1].value))
assert len(poses)==23
sections=[]
# Exact lamination bounds of graphical native export are recorded separately;
# physical package-seat interval [-1.6,0] is used for conservative checking.
zs=sorted(set(round(-1.6+i*.025,8)for i in range(65))|{-3.49,-3.,-2.5,-2.,-1.9,-1.595,-.085,-.001})
for z in zs:
 for wire in full.slice(V(0,0,1),z):
  points=wire.discretize(Deflection=.0005);b=wire.BoundBox;center=[(b.XMin+b.XMax)/2,(b.YMin+b.YMax)/2];pad=min(pads,key=lambda p:math.hypot(center[0]-p['canonical_xy_mm'][0],center[1]-p['canonical_xy_mm'][1]));axis=pad['canonical_xy_mm'];rad=max(math.hypot(p.x-axis[0],p.y-axis[1])for p in points);sections.append(dict(z_mm=z,pad=pad['number'],section_center_xy_mm=center,section_bbox_xy_mm=[b.XMin,b.YMin,b.XMax,b.YMax],maximum_radius_from_actual_drill_axis_mm=rad,clearance_to_actual_1p1938mm_drill_mm=pad['drill_mm']/2-rad,clearance_to_hypothetical_1mm_drill_mm=.5-rad,clearance_to_manufacturer_1p3mm_drill_mm=.65-rad))
lam=[r for r in sections if -1.6<=r['z_mm']<=0];worst=max(lam,key=lambda r:r['maximum_radius_from_actual_drill_axis_mm']);straight=[r for r in lam if r['z_mm']>=-.025];tip=[r for r in sections if r['z_mm']==-3.49];axis_residual=math.hypot(6.25-6.2484,2.5-2.4892)
pin_report=dict(actual_pads=pads,manufacturer_nominal_pitch_xy_mm=[12.5,5],nominal_terminal_axes_to_actual_pad_centres_mm=axis_residual,manufacturer_recommended_drill_mm=1.3,actual_drill_mm=1.1938,conservative_lamination_interval_mm=[-1.6,0],native_graphical_lamination_interval_mm=[-1.595,-.085],sampling_step_mm=.025,wire_discretization_deflection_mm=.0005,sections=sections,worst_free_state_section=worst,minimum_straight_shoulder_clearance_mm=min(r['clearance_to_actual_1p1938mm_drill_mm']for r in straight),minimum_solder_tip_clearance_mm=min(r['clearance_to_actual_1p1938mm_drill_mm']for r in tip),free_state_kink_exceeds_actual_drill_radius_mm=max(0,-worst['clearance_to_actual_1p1938mm_drill_mm']),interpretation='Four nominal electricalterminal axes align closely with pads. Straight shoulders and narrow soldertips fit the actualdrill crosssection. The outward bowed/kinked portion is manufacturerfree-state retention geometry, not an installed compressedshape; it intersects the drilledvolume as a rigidrender. Elasticformation/assemblyforce/material/tolerance are unqualified. Actualdrill is smaller than the manufacturerrecommended1.3mm. No PCB/drill modification made.')
(HERE/'tl1100-pin-section-audit.json').write_text(json.dumps(pin_report,indent=2)+'\n')

PALETTE={'housing':[.035,.035,.04],'actuator':[.018,.018,.022],'cover':[.57,.59,.61],'terminals':[.6,.61,.63]}
def face_role(f):
 b=f.BoundBox;c=f.CenterOfMass
 if b.ZMax<1e-7:return'terminals'
 if b.ZMin>=4.39999:return'actuator'
 extent=max(abs(b.XMin),abs(b.XMax),abs(b.YMin),abs(b.YMax))
 if b.ZMin>=3.29999 and b.ZMax>=3.89999 and extent>3.5:return'cover'
 return'housing'
def add_face_colors(step,shape):
 text=step.read_text();ent={int(n):body for n,body in re.findall(r'#(\d+)\s*=\s*(.*?);',text,re.S)};breps=[int(n)for n in re.findall(r'#(\d+)\s*=\s*MANIFOLD_SOLID_BREP',text)];assert len(breps)==1
 shell=int(re.findall(r'#(\d+)',ent[breps[0]])[0]);faces=list(map(int,re.findall(r'#(\d+)',ent[shell])));assert len(faces)==len(shape.Faces)
 context=next(i for i,b in ent.items()if 'GEOMETRIC_REPRESENTATION_CONTEXT(3)'in b);extra=[];nextid=max(ent)+1
 def add(body):
  nonlocal nextid
  i=nextid;nextid+=1;extra.append(f'#{i} = {body};');return i
 grouped={};styles=[]
 for faceid,f in zip(faces,shape.Faces):grouped.setdefault(face_role(f),[]).append(faceid)
 for role,ids in grouped.items():
  rgb=add("COLOUR_RGB('"+role+"',"+','.join(map(str,PALETTE[role]))+')');p=add(f"FILL_AREA_STYLE_COLOUR('',#{rgb})");p=add(f"FILL_AREA_STYLE('',(#{p}))");p=add(f'SURFACE_STYLE_FILL_AREA(#{p})');p=add(f"SURFACE_SIDE_STYLE('',(#{p}))");p=add(f'SURFACE_STYLE_USAGE(.BOTH.,#{p})');p=add(f'PRESENTATION_STYLE_ASSIGNMENT((#{p}))');styles.extend(add(f"STYLED_ITEM('{role}',(#{p}),#{fid})")for fid in ids)
 add("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',("+','.join('#'+str(i)for i in styles)+f'),#{context})');pos=text.rfind('ENDSEC;');step.write_text(text[:pos]+'\n'+'\n'.join(extra)+'\n'+text[pos:]);return grouped

oldplan=json.loads((WORK/'validation/models-review-7/combined-model-plan.json').read_text());oldrow=next(r for r in oldplan['assignments']if r['board']=='mainboard'and'S5'in r['references']);parts=[]
for variant,shape in [('FullNominalFreeState',full),('BodyOnly',body)]:
 ident='TL1100F_ManufacturerCAD_'+variant;step=HERE/(ident+'.step');stl=HERE/(ident+'.stl');shape.exportStep(str(step));read=Part.Shape();read.read(str(step));assert read.isValid();colors=add_face_colors(step,read);colored=Part.Shape();colored.read(str(step));assert colored.isValid()and colored.exportBrepToString()==read.exportBrepToString();mesh=Mesh.Mesh(shape.tessellate(.035));mesh.write(str(stl));role_meshes=[]
 for role in colors:
  faces=[f for f in read.Faces if face_role(f)==role];surfaces=Part.makeCompound(faces);out=HERE/(ident+'_'+role+'.stl');mm=Mesh.Mesh(surfaces.tessellate(.035));mm.write(str(out));role_meshes.append(dict(role=role,stl=str(out),units='mm',rgba=PALETTE[role]+[1],surface_subset=True,not_standalone_closed_solid=True,faces=len(faces),triangles=mm.CountFacets,sha256=sha(out)))
 limits=['Publisher TL1100Fxxxx familyCAD aligns to publishedTL1100F160Q7.3mmactuator height; force/plating options and exacthistoricmold revision are not established.','The originalpublisherCAD has one invalidzeroarea internalcylindricalface. A localizedinternalunion repair adds0.035684mm3 while preservingexactexternalbounds; repairedsourceisvalid. Sourcefile remains byteunchanged.','Housing/cover/actuator/terminalfacecolors are inferredpresentation roles; originalpublisherSTEP is singlegrey. Geometry is not resized tofit.','Manufacturerrecommendeddrill1.30mm differs from originalB3F-40XX1.1938mmdrill; existingPCBgeometryis unchanged.','Nominalterminalaxes residual0.010918mm; straightterminalshoulders/tips fit sampledactualdrillsections, butfree-state retentionkinks exceedthehole. Thefullvariantis nominalfree-stateCAD, not deformedinstalledpins orfitqualification.','Elasticcompression, materialstress, insertionforce, tolerances, capsocket and fullassemblyfit are unqualified.']
 if variant=='BodyOnly':limits+=['Only manufacturergeometry at canonicalZ>=0 is retained; solderterminal free-stategeometry omitted below the seatingdatum.']
 row=dict(id=ident,variant=variant,board='mainboard',references=refs,footprint='B3F-40XX',source_model=str(step),source_sha256=sha(step),step=str(step),stl=str(stl),stl_sha256=sha(stl),units='mm',offset_mm=[0,0,0],scale=[1,1,1],rotation_deg=[0,0,0],canonical_frame='Original F.Cu footprint X,-Y,Z outward; seatingdatumZ0, actuator tipZ7.3. No placedboardpose baked in.',source_kind='PublisherCAD with localizedhiddenvalidityrepair andrigidcanonicalorigin translation',classification='Manufacturer nominal/free-state familyCAD; locally repaired; installedterminalfit unqualified'if variant=='FullNominalFreeState'else'Manufacturer body-only familyCAD; locally repaired; terminals omitted',limitations=limits,source_urls=['https://configured-product-images.s3.amazonaws.com/stp3dmodels/TL1100Fxxxx.stp','https://configured-product-images.s3.amazonaws.com/2D/specs/TL1100F160Q.pdf'],publisher_source=str(source),publisher_source_sha256=SOURCEHASH,publisher_to_canonical_translation_mm=[0,0,3.8825],publisher_to_canonical_rotation_deg=[0,0,0],bounds_mm=bbox(colored),mesh_bounds_mm=bbox(shape),source_actuator_height_mm=7.3,valid=True,solid_count=len(shape.Solids),faces=len(shape.Faces),triangles=mesh.CountFacets,mesh_parts=role_meshes,color_roles={r:len(v)for r,v in colors.items()},replaces_source_sha256=oldrow['source_sha256'],replaces_source_model=oldrow['source_model'])
 parts.append(row)
assert sha(board)==sourcepcbhash and sha(source)==SOURCEHASH
repair=dict(source_valid=False,source_faces=len(raw.Faces),invalid_face_index=bad[0][0],invalid_face_area=bad[0][1].Area,repair_tool_publisher_frame=dict(kind='cylinder union',radius_mm=1.5001,height_mm=.035,start_mm=[0,0,-2.1925]),source_volume_mm3=raw.Volume,repaired_volume_mm3=repaired.Volume,added_volume_mm3=volume_delta,added_volume_percent=volume_delta/raw.Volume*100,external_bounds_exactly_preserved=True,publisher_bounds_mm=bbox(raw),geometry_outside_local_3p2x3p2x0p1mm_ROI_valid=True,outside_ROI_symmetric_difference_volume_mm3=outside_diff,full_valid=True,body_only_valid=True,canonical_translation_mm=[0,0,3.8825])
assignment={k:parts[0][k]for k in ['board','references','footprint','source_model','source_sha256','offset_mm','scale','rotation_deg','source_kind','classification','limitations','source_urls','replaces_source_sha256','replaces_source_model']}
manifest=dict(date='2026-10-14',scope='Publisher TL1100Fxxxx exactfamilyCAD candidates for23referenceinstances; realprojects/scenes untouched.',parts=parts,assignments=[assignment],default_variant='FullNominalFreeState',alternate_models=[parts[1]],repair=repair,pin_section_audit='tl1100-pin-section-audit.json',actual_footprint_library=str(lib),actual_footprint_sha256=sha(lib),reference_poses=poses,source_board_sha256=sourcepcbhash,source_board_unchanged=True,source_manufacturer_CAD_unchanged=True,license='ManufacturerCAD retainsitsoriginalrights; alignment/repair/reviewcode isCC0-1.0.')
(HERE/'control-quality-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(dict(passed=True,variants=[dict(id=p['id'],valid=p['valid'],bounds=p['bounds_mm'],triangles=p['triangles'])for p in parts],repair_volume_mm3=volume_delta,nominal_pin_axis_residual_mm=axis_residual,actual_drill_mm=1.1938,worst_free_state_radius_mm=worst['maximum_radius_from_actual_drill_axis_mm']),indent=2))
