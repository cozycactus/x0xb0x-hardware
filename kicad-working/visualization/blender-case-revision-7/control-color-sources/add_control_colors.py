#!/usr/bin/env python3
"""Append AP214 face appearance to immutable control STEP copies only.

SPDX-License-Identifier: CC0-1.0
Run with FreeCAD's bundled Python. Never reexport, rescale or alter original
geometry entities; source control STEP files and all real projects stay read-only.
"""
from pathlib import Path
import copy,hashlib,json,re,sys
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
SOURCE=WORK/'validation/models-review-6/control-body-illustrations'
manifest=json.loads((SOURCE/'control-body-manifest.json').read_text())
REPORT=[]
PARTS=[]
ASSIGNMENTS=[]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
INPUTS={str(p):sha(p) for p in [WORK/'mainboard/mainboard.kicad_pcb',WORK/'ioboard/ioboard.kicad_pcb']}

def entities(text):
    return {int(n):body for n,body in re.findall(r'#(\d+)\s*=\s*(.*?);',text,re.S)}

def bounds(s):
    b=s.BoundBox
    return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]

for part in manifest['parts']:
    source=Path(part['step']);raw=source.read_text();original=entities(raw)
    assert sha(source)==part['source_sha256']
    assert 'COLOUR_RGB' not in raw and 'STYLED_ITEM' not in raw
    breps=[int(n) for n in re.findall(r'#(\d+)\s*=\s*MANIFOLD_SOLID_BREP',raw)]
    src=Part.read(str(source))
    assert src.isValid() and len(src.Solids)==len(breps)==len(part['mesh_parts'])
    extra=[];next_id=max(original)+1
    def add(body):
        global next_id
        ident=next_id;next_id+=1;extra.append(f'#{ident} = {body};');return ident
    role_rows=[]
    for brep,solid,segment in zip(breps,src.Solids,part['mesh_parts']):
        expected_bounds=segment['bounds']['min_mm']+segment['bounds']['max_mm']
        # Original segment bounds were recorded after tessellation; circular
        # chord extrema differ by up to0.0015mm. This verifies role ordering,
        # while exact BRep equality below verifies geometry without tolerance.
        role_bounds_residual=max(abs(a-b) for a,b in zip(bounds(solid),expected_bounds))
        assert role_bounds_residual<.002
        shell=int(re.findall(r'#(\d+)',original[brep])[0])
        faces=list(map(int,re.findall(r'#(\d+)',original[shell])))
        assert all(original[f].lstrip().startswith('ADVANCED_FACE') for f in faces)
        context=None
        for body in original.values():
            if body.startswith(('SHAPE_REPRESENTATION','ADVANCED_BREP_SHAPE_REPRESENTATION')):
                refs=list(map(int,re.findall(r'#(\d+)',body)))
                if brep in refs:context=refs[-1];break
        assert context is not None
        color=part['material_color_suggestions'][segment['material']]['rgba'][:3]
        rgb=add("COLOUR_RGB('"+segment['material']+"',"+','.join(map(str,color))+')')
        fill_color=add(f"FILL_AREA_STYLE_COLOUR('',#{rgb})")
        fill=add(f"FILL_AREA_STYLE('',(#{fill_color}))")
        surface=add(f'SURFACE_STYLE_FILL_AREA(#{fill})')
        side=add(f"SURFACE_SIDE_STYLE('',(#{surface}))")
        usage=add(f'SURFACE_STYLE_USAGE(.BOTH.,#{side})')
        assignment=add(f'PRESENTATION_STYLE_ASSIGNMENT((#{usage}))')
        styled=[add(f"STYLED_ITEM('{segment['name']}',(#{assignment}),#{face})") for face in faces]
        add("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',("+
            ','.join('#'+str(n) for n in styled)+f'),#{context})')
        role_rows.append({'segment':segment['name'],'role':segment['role'],
            'material':segment['material'],'rgb_srgb':color,'solid_entity':brep,
            'face_entities':faces,'styled_faces':len(faces),'bounds_mm':bounds(solid),
            'source_mesh_bounds_maximum_chord_residual_mm':role_bounds_residual})
    marker=raw.rfind('ENDSEC;')
    assert marker>0
    target=HERE/(source.stem+'_Colors.step')
    modified=raw[:marker]+'\n'+'\n'.join(extra)+'\n'+raw[marker:]
    target.write_text(modified)
    written=entities(modified)
    assert all(written[n]==body for n,body in original.items())
    assert set(written)-set(original)==set(range(max(original)+1,max(written)+1))
    reread=Part.read(str(target))
    assert reread.isValid()
    source_brep=src.exportBrepToString();target_brep=reread.exportBrepToString()
    assert source_brep==target_brep, 'Canonical BRep serialization changed'
    assert bounds(src)==bounds(reread)
    topology=lambda s:{'solids':len(s.Solids),'shells':len(s.Shells),
        'faces':len(s.Faces),'wires':len(s.Wires),'edges':len(s.Edges),'vertices':len(s.Vertexes)}
    assert topology(src)==topology(reread)
    assert abs(src.Volume-reread.Volume)<1e-10
    row={'id':part['id'],'source_step':str(source),'source_sha256':sha(source),
        'corrected_step':str(target),'corrected_sha256':sha(target),
        'classification':'Color-only AP214 presentation addition to original nominal body illustration',
        'all_original_STEP_entities_verbatim_unchanged':True,
        'original_entity_count':len(original),'appended_presentation_entity_count':len(extra),
        'canonical_BRep_serialization_equal':True,
        'canonical_BRep_sha256':hashlib.sha256(source_brep.encode()).hexdigest(),
        'bounds_mm':bounds(src),'topology':topology(src),'volume_mm3':src.Volume,
        'roles':role_rows,'source_valid':True,'corrected_valid':True}
    REPORT.append(row)
    new=copy.deepcopy(part)
    new.update(step=str(target),source_sha256=sha(target),
        original_step=str(source),original_step_sha256=sha(source),
        source_kind='Color-only AP214 face appearance on unchanged original body illustration',
        step_colors='Explicit AP214 face styles. Source palette values are sRGB; native GLB factors are linear.',
        color_roles=role_rows,
        color_limitations=['Colors are presentation suggestions from the original illustration manifest; exact historical resin or finish is not established.',
                           'STEP diffuse color does not encode the Blender metallic/roughness suggestions. Mixed-material housing envelopes retain their existing unsplit geometry.'])
    PARTS.append(new)
    assignment={k:new[k] for k in ['board','references','footprint','source_sha256',
        'offset_mm','scale','rotation_deg','source_kind','classification','source_urls']}
    assignment.update(source_model=str(target),limitations=new['limitations']+new['color_limitations'],
        replaces_source_sha256=sha(source),color_only=True)
    ASSIGNMENTS.append(assignment)

assert sum(len(p['references']) for p in PARTS)==34
assert INPUTS=={p:sha(p) for p in INPUTS}
assert all(sha(Path(p['step']))==p['source_sha256'] for p in manifest['parts'])
result={'date':'2026-10-14','scope':'Color-only corrected copies of six original control body families for34 references; no project edits.',
    'diagnosis':'Original headless Part.export files have no AP214 presentation data, so native KiCad GLB omits primitive materials and uses default white.',
    'parts':PARTS,'assignments':ASSIGNMENTS,'instance_count':34,'family_count':6,
    'units':'mm','canonical_coordinate_convention':manifest['canonical_coordinate_convention'],
    'geometry_license':manifest['geometry_license'],'source_document_rights':manifest['source_document_rights'],
    'source_manifest':str(SOURCE/'control-body-manifest.json'),
    'source_manifest_sha256':sha(SOURCE/'control-body-manifest.json'),
    'input_project_hashes':INPUTS,'input_projects_and_original_models_unchanged':True,
    'project_hash_guard_scope':'Generation-time evidence; later authorized model-path integration is expected and does not invalidate the immutable probe/model proof.'}
(HERE/'control-color-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
(HERE/'control-color-geometry-audit.json').write_text(json.dumps({
    'passed':True,'families':REPORT,'family_count':6,'instance_count':34,
    'input_projects_and_original_models_unchanged':True},indent=2)+'\n')
print(json.dumps({'passed':True,'families':6,'instances':34,'original_entities_preserved':True,'BRep_serializations_equal':True}))
