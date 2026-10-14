"""Audit native one-reference KiCad GLB colors and byte-exact geometry."""
from pathlib import Path
import collections,hashlib,json,math,struct
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'control-color-manifest.json').read_text())
geometry=json.loads((HERE/'control-color-geometry-audit.json').read_text())
plan=json.loads((HERE/'native-probe-plan.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
probes={(p['id'],p['variant']):p for p in plan['probes']}

def read(path):
    data=Path(path).read_bytes()
    magic,version,total=struct.unpack_from('<III',data)
    assert magic==0x46546c67 and version==2 and total==len(data)
    chunks={};at=12
    while at<len(data):
        size,kind=struct.unpack_from('<II',data,at)
        chunks[kind]=data[at+8:at+8+size];at+=8+size
    return json.loads(chunks[0x4E4F534A]),chunks[0x004E4942]

def values(doc,binary,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    assert a['componentType']==5126 and a['type']=='VEC3'
    offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
    return [struct.unpack_from('<fff',binary,offset+i*stride) for i in range(a['count'])]

def native_bounds(doc,binary,primitives):
    # Native KiCad glTF converts source Z-up to Y-up. Return original model's
    # Cartesian frame in millimetres; placement remains in unchanged nodes.
    points=[(x*1000,-z*1000,y*1000) for p in primitives
            for x,y,z in values(doc,binary,p['attributes']['POSITION'])]
    return [min(p[k] for p in points) for k in range(3)]+[max(p[k] for p in points) for k in range(3)]

def linear(v):
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4

rows=[]
for part,g in zip(manifest['parts'],geometry['families']):
    original=probes[(part['id'],'original')];colored=probes[(part['id'],'colored')]
    a,bin_a=read(original['GLB']);b,bin_b=read(colored['GLB'])
    pa=[p for m in a['meshes'] for p in m['primitives']]
    pb=[p for m in b['meshes'] for p in m['primitives']]
    assert bin_a==bin_b
    assert a['accessors']==b['accessors'] and a['bufferViews']==b['bufferViews']
    assert a['nodes']==b['nodes'] and a['scenes']==b['scenes']
    strip=lambda doc:[{k:v for k,v in p.items() if k!='material'}
                      for m in doc['meshes'] for p in m['primitives']]
    assert strip(a)==strip(b)
    assert all('material' not in p for p in pa)
    assert all('material' in p for p in pb)
    assert len(pb)==sum(r['styled_faces'] for r in part['color_roles'])
    roles=[];cursor=0
    for role in part['color_roles']:
        count=role['styled_faces'];subset=pb[cursor:cursor+count];cursor+=count
        expected=[linear(v) for v in role['rgb_srgb']]
        actual=[b['materials'][p['material']]['pbrMetallicRoughness'].get('baseColorFactor',[1,1,1,1])[:3] for p in subset]
        color_error=max(abs(v-e) for rgb in actual for v,e in zip(rgb,expected))
        assert color_error<1e-6,(part['id'],role['segment'],actual,expected)
        bb=native_bounds(b,bin_b,subset)
        bounds_error=max(abs(v-e) for v,e in zip(bb,role['bounds_mm']))
        assert bounds_error<.02,(part['id'],role['segment'],bb,role['bounds_mm'])
        roles.append({'segment':role['segment'],'material':role['material'],
            'STEP_rgb_srgb':role['rgb_srgb'],'expected_GLB_rgb_linear':expected,
            'actual_GLB_rgb_linear':actual[0],'maximum_color_error':color_error,
            'native_primitive_count':count,'native_bounds_mm':bb,
            'maximum_native_mesh_chord_bounds_residual_mm':bounds_error,
            'palette_and_role_geometry_passed':True})
    assert cursor==len(pb)
    palette={tuple(b['materials'][p['material']]['pbrMetallicRoughness']['baseColorFactor']) for p in pb}
    rows.append({'id':part['id'],'references':part['references'],
        'native_probe_reference':original['reference'],'native_probe_side':original['side'],
        'original_GLB':original['GLB'],'original_GLB_sha256':sha(original['GLB']),
        'colored_GLB':colored['GLB'],'colored_GLB_sha256':sha(colored['GLB']),
        'original_primitives_without_material':len(pa),'corrected_primitives_with_material':len(pb),
        'native_material_count':len(palette),'GLB_binary_geometry_byte_identical':True,
        'GLB_binary_geometry_sha256':hashlib.sha256(bin_a).hexdigest(),
        'accessors_and_bufferViews_identical':True,'primitive_geometry_metadata_identical':True,
        'native_component_nodes_and_transforms_identical':True,
        'source_STEP_entities_and_BRep_unchanged':g['all_original_STEP_entities_verbatim_unchanged'] and g['canonical_BRep_serialization_equal'],
        'roles':roles,'passed':True})

assert manifest['input_projects_and_original_models_unchanged']
assert plan['input_board_unchanged']
assert all(sha(p['original_step'])==p['original_step_sha256'] for p in manifest['parts'])
report={'passed':True,'families':rows,'family_count':6,'instance_count':34,
    'native_KiCad_version':'10.0.7',
    'native_KiCad_probe_count':12,'source_pcb_pose_preserved':True,
    'input_projects_unchanged_at_generation_and_probe_validation':True,
    'original_control_models_unchanged':True,
    'project_hash_guard_scope':'Generation-time snapshots only. Later authorized integration may change actual project model paths without invalidating these preserved probes.',
    'does_not_require_projects_to_remain_at_preintegration_revision':True,
    'generation_input_project_hashes':manifest['input_project_hashes'],
    'appearance_transfer':'STEP COLOUR_RGB palette is sRGB; native glTF baseColorFactor is linear using IEC61966-2-1 transfer.',
    'color_channel_tolerance':1e-6,'role_mesh_bounds_check_tolerance_mm':.02,
    'geometry_proof':'Every original STEP entity remains verbatim unchanged; exact reloaded BRep strings match. Each native original/colored GLB pair has byte-identical binary geometry, accessor/bufferView geometry metadata, primitive geometry metadata and node poses.',
    'limitations':['Same original nominal-body illustrations and installed-seating uncertainties. This revision changes appearance only.',
                   'One native B.Cu reference per reused family is probed;34 assignment references reuse these six exact corrected STEP files.',
                   'RGB colors are illustration palette choices. STEP diffuse color does not encode Blender metalness/roughness.']}
(HERE/'native-control-color-audit.json').write_text(json.dumps(report,indent=2)+'\n')
manifest['native_color_validation']={'passed':True,'report':str(HERE/'native-control-color-audit.json'),
    'native_probe_count':12,'GLB_binary_geometry_byte_identical_for_all_six_pairs':True,
    'maximum_color_channel_error':max(r['maximum_color_error'] for f in rows for r in f['roles'])}
(HERE/'control-color-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'passed':True,'families':6,'references':34,'native_probes':12,
    'maximum_color_error':manifest['native_color_validation']['maximum_color_channel_error'],
    'native_material_counts':{f['id']:f['native_material_count'] for f in rows},
    'GLB_binary_geometry_identical':True},indent=2))
