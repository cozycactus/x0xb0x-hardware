"""Build photo-qualified bent IC20 / full-size KK1 illustrations in isolation.

All published body dimensions are retained. Installation pose is illustrative.
No project, footprint, old model or Blender scene is modified.
"""
from pathlib import Path
import ast, hashlib, json, re, shutil, sys
sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part, Import, MeshPart, Mesh
H = Path(__file__).resolve().parent
W = H.parents[2]
V = App.Vector
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
reg_source = W/'validation/models-review-6/misc-body-illustrations/MC78M05_TO220_BodyOnlyIllustration.step'
heat_source = W/'validation/models-review-9/heatsink-quality/Aavid_574502B00000G_DrawingDerived_FoldedSpring.step'
assert sha(reg_source) == 'f65e974128af6b8e5f9f74b815aada33c296f1ae113dac9fc6f7a341599e65a8'
assert sha(heat_source) == '36ea5130eb331e8c740748c697559dfd79671284869be83e8251dd4c944e4336'
# Reuse only the audited AP214 color function, without executing the old builder.
old = W/'validation/models-review-6/misc-body-illustrations/generate_misc_bodies.py'
module = ast.parse(old.read_text())
node = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == 'add_step_face_colors')
exec(compile(ast.Module(body=[node], type_ignores=[]), str(old), 'exec'))

def bounds(shape):
    b = shape.BoundBox
    return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]

def rotate_install(shape):
    s = shape.copy()
    s.rotate(V(0,0,0), V(1,0,0), -90)
    s.translate(V(0,0,2.0))
    return s

original_reg = Part.read(str(reg_source))
reg_features = []
for solid in original_reg.Solids:
    plastic = solid.BoundBox.ZLength > 8
    reg_features.append(('PlasticBody' if plastic else 'MetalTab', rotate_install(solid), (.06,.06,.065) if plastic else (.70,.72,.74)))
original_heat = Part.read(str(heat_source))
heat_in_ic_frame = original_heat.copy()
# Original independent source hole/backplane alignment expressed in IC20 frame.
# KK1 native origin lies +1.27 mm along nativeY from IC20.
heat_in_ic_frame.translate(V(0,-7.51,3.9))
heat_installed = rotate_install(heat_in_ic_frame)
heat_installed.translate(V(0,-1.27,0))
heat_features = [('BlackAnodizedSpring', heat_installed, (.055,.060,.065))]

base_limits = [
    'Original author assembly instruction explicitly says to bend IC20 back before fitting the heatsink; the original place/soldered/measure photos show the body and tab approximately parallel to the PCB and extending beyond its edge.',
    'The exact 90 degree angle, bend datum and 2.0 mm vertical placement are illustration assumptions, not measurements from the photograph or a manufacturer formed-lead specification.',
    'All IC20 leads remain omitted. The prior nominal published lead width/hole fit was unresolved; no terminals were thinned, displaced or invented to conceal it.',
    'The paired seat uses source-consistent through-hole and contact-plane alignment, inherited from the nominal generic TO220 body. Actual original regulator vendor/suffix, lead forming, cut lengths and installed seat require physical confirmation.',
    'The complete revision 9 heatsink is only rigidly rotated and translated. No fold, spring finger, wall, source envelope or neighboring component is trimmed or shrunk.',
    'Free-state reconstructed spring fingers retain a nominal 1.729422 mm3 regulator intersection. This is a documented geometric overlap, not a simulation or certification of elastic clamping, contact force or thermal performance.',
    'Case placement, board seat and neighboring package models remain qualified visual geometry. A clear surface screen does not establish tolerance or physical fit.'
]
urls = [
    'https://www.ladyada.net/make/x0xb0x/fab/powersupply.html',
    'https://ladyada.net/make/x0xb0x/fab/parts.html',
    'https://www.onsemi.com/download/data-sheet/pdf/mc78m00-d.pdf',
    'https://info.boydcorp.com/hubfs/Thermal/Air-Cooling/Boyd-Board-Level-Cooling-Slide-On-5744.pdf'
]
parts=[]; assignments=[]
for ref, footprint, key, features, source in [
    ('IC20','78XXS','MC78M05_TO220_BentBack_PhotoQualified_BodyOnly',reg_features,reg_source),
    ('KK1','D03S','Aavid_574502B00000G_BentBack_PhotoQualified',heat_features,heat_source)]:
    doc=App.newDocument(key); objects=[]
    for label,shape,color in features:
        assert shape.isValid() and shape.Volume > 0
        # Identity compound wrapper preserves placed source geometry during STEP export.
        obj=doc.addObject('PartDesign::Feature',label);obj.Shape=Part.makeCompound([shape]);objects.append(obj)
    doc.recompute();step=H/(key+'.step');stl=H/(key+'.stl')
    Import.export(objects,str(step));add_step_face_colors(step,features)
    united=features[0][1] if len(features)==1 else features[0][1].multiFuse([f[1] for f in features[1:]]).removeSplitter()
    MeshPart.meshFromShape(Shape=united,LinearDeflection=.02,AngularDeflection=.10,Relative=False).write(str(stl))
    segments=[]
    for label, shape, color in features:
        segment=H/(key+'--'+label+'.stl')
        MeshPart.meshFromShape(Shape=shape,LinearDeflection=.02,AngularDeflection=.10,Relative=False).write(str(segment))
        segments.append({'name':label,'stl':segment.name,'color_rgb':list(color)})
    reloaded=Part.read(str(step));mesh=Mesh.Mesh(str(stl))
    assert reloaded.isValid() and mesh.isSolid()
    assert abs(reloaded.Volume-united.Volume)<1e-5
    raw=Part.makeCompound([f[1] for f in features])
    assert max(abs(a-b) for a,b in zip(bounds(reloaded),bounds(raw)))<1e-5, (ref,bounds(reloaded),bounds(raw))
    original=Part.read(str(source))
    assert abs(original.Volume-reloaded.Volume)<1e-5
    classification='Original assembly photo-qualified bent-back '+('nominal MC78M05 TO220 body-only illustration' if ref=='IC20' else 'full-size drawing-derived folded spring illustration')
    part={'id':key,'board':'ioboard','references':[ref],'footprint':footprint,'step':str(step),'stl':str(stl),'units':'mm',
          'source_sha256':sha(step),'stl_sha256':sha(stl),'canonical_frame':'Original footprint X, minus footprint Y, outward Z. The installation illustration is baked into geometry; native model transform stays zero/unity.',
          'classification':classification,'source_urls':urls,'limitations':base_limits,'segments':segments,
          'geometry':{'valid':reloaded.isValid(),'solids':len(reloaded.Solids),'faces':len(reloaded.Faces),'volume_mm3':reloaded.Volume,'exact_bounds_mm':bounds(reloaded),'STL_closed':mesh.isSolid(),'STL_facets':mesh.CountFacets,'AP214_styled_faces':step.read_text().count('STYLED_ITEM')},
          'rigid_source':str(source),'rigid_source_sha256':sha(source),'source_volume_preserved':True}
    parts.append(part)
    assignments.append({'board':'ioboard','references':[ref],'footprint':footprint,'source_model':str(step),'source_sha256':sha(step),
      'offset_mm':[0,0,0],'rotation_deg':[0,0,0],'scale':[1,1,1],'source_kind':'Primary original-author assembly-photo qualified rigid installation of source-dimensional reconstruction',
      'classification':classification,'source_urls':urls,'limitations':base_limits,'replaces_source_model':str(source),'replaces_source_sha256':sha(source)})
    App.closeDocument(doc.Name)

sources=[
 (W/'validation/models-review-6/misc-body-illustrations/reference/onsemi-mc78m00.pdf',H/'sources/onsemi-mc78m00.pdf'),
 (W/'validation/models-review-9/heatsink-quality/sources/boyd-5740-manufacturer.pdf',H/'sources/boyd-5740-manufacturer.pdf'),
 (W/'validation/models-review-9/heatsink-quality/sources/boyd-574502B00000G-exact-drawing.png',H/'sources/boyd-574502B00000G-exact-drawing.png')]
for source,dest in sources:shutil.copy2(source,dest)
report={'date':'2026-10-14','parts':parts,'assignments':assignments,'installation_assumptions':{'IC20_rotation_about_footprint_X_deg':-90,'post_rotation_vertical_translation_mm':2.0,
 'KK1_pre_rotation_translation_in_IC20_frame_mm':[0,-7.51,3.9],'KK1_post_rotation_origin_translation_from_IC20_to_KK1_frame_mm':[0,-1.27,0]},
 'published_dimensions_preserved':{'IC20_body_width_mm':10,'IC20_plastic_depth_mm':4.455,'IC20_body_and_tab_total_height_mm':15.5,'IC20_tab_thickness_mm':1.27,'IC20_hole_diameter_mm':3.66,
 'KK1_full_shape_source_dimensions_mm':[21.84,10.03,19.05],'KK1_thickness_mm':.63,'KK1_hole_diameter_mm':3.81,'KK1_hole_height_mm':11.81},
 'source_document_hashes':{str(p.relative_to(H)):sha(p) for p in (H/'sources').iterdir() if p.is_file()},
 'generator':'build_bent_pair.py','license':'Original rigid installation reconstruction CC0-1.0; source photos and manufacturer drawings retain publisher rights.'}
(H/'bent-pair-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'parts':[{k:p[k] for k in ['references','source_sha256','geometry']} for p in parts]},indent=2))
