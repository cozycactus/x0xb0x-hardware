"""Mitsubishi 2SC2291 primary-dimension candidate with explicit formed leads.

SPDX-License-Identifier: CC0-1.0
No actual project, footprint cache or delivered Blender scene is edited.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import shutil
import sys

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
import MeshPart
from step_colors import set_step_colors

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
sys.path.insert(0, str(WORK.parent/'kicad-import/validation'))
from verify_native_projects import children, one, parse_sexpr, property_value
V = App.Vector
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_pdf = HERE/'2SC2291-downloaded.pdf'
pcb = WORK/'mainboard/mainboard.kicad_pcb'
cache = WORK/'mainboard/mainboard-import-fps.pretty/SSIP5.kicad_mod'
old = next(r for r in json.loads((WORK/'validation/models-review-8/combined-model-plan.json')
                               .read_text())['assignments'] if r['references'] == ['Q22'])
source_hashes = {str(p): sha(p) for p in [source_pdf, pcb, cache,
                                       Path(old['source_model'])]}
tree = parse_sexpr(pcb.read_text())
fp = next(f for f in children(tree, 'footprint')
          if property_value(f, 'Reference', 'reference') == 'Q22')
assert fp[1].split(':')[-1] == 'SSIP5' and one(fp, 'layer')[1] == 'F.Cu'
pads = sorted(children(fp, 'pad'), key=lambda p: int(p[1]))
assert [p[1] for p in pads] == ['1','2','3','4','5']
actual_pads = [{'pin': p[1], 'canonical_xy_mm': [float(one(p,'at')[1]),
               -float(one(p,'at')[2])], 'drill_mm': float(one(p,'drill')[1])}
               for p in pads]
for i, pad in enumerate(actual_pads):
    assert math.dist(pad['canonical_xy_mm'], [(i-2)*2.286,0]) < 1e-8
    assert pad['drill_mm'] == 1
cache_has_no_model = not re.search(r'^\s*\(model\b', cache.read_text(), re.M)
assert cache_has_no_model, 'Heterogeneous SSIP5 cache must remain unassigned'

P = {'body_width_MAX_mm': 8.1, 'body_depth_MAX_mm': 3.6,
     'body_height_MAX_mm': 5.6, 'rear_top_bevel_yz_mm': [2,2],
     'lead_row_from_flat_face_mm': 1.4, 'nominal_package_pitch_mm': 1.25,
     'nominal_lead_diameter_mm': .45, 'factory_lead_length_MIN_mm': 10.5,
     'actual_PCB_pitch_mm': 2.286, 'actual_PCB_drill_mm': 1,
     'assumed_body_standoff_mm': 3,
     'assumed_trimmed_tail_z_mm': -2.5,
     'assumed_lead_embed_into_body_mm': .12,
     'assumed_fanout_curve_z_limits_mm': [.4,2.65],
     'assumed_fanout_bend_center_radius_mm': .65}
bottom = P['assumed_body_standoff_mm']
top = bottom+P['body_height_MAX_mm']
# The side view gives 1.4 from the flat face to the lead row. The opposite
# side has the printed 2-by-2 top bevel. No XY-outline bevel is substituted.
profile = [(-1.4,bottom), (2.2,bottom), (2.2,top-2),
           (.2,top), (-1.4,top)]
points = [V(-4.05,y,z) for y,z in profile]
body = Part.Face(Part.makePolygon(points+[points[0]])).extrude(V(8.1,0,0))


def formed_lead(x0, x1):
    entry = V(x0,0,3.12)
    start = V(x0,0,2.65)
    end = V(x1,0,.4)
    tail = V(x1,0,-2.5)
    radius = .65
    dx = abs(x1-x0)
    height = start.z-end.z
    angle = 0
    straight_length = height
    bend_points = [start,end]
    if dx < 1e-10:
        edges = [Part.makeLine(entry,tail)]
    else:
        # Tangent circular bends produce analytic toroidal surfaces. They
        # avoid conservative B-spline control-hull bounds while preserving
        # full lead diameter and exact source/PCB endpoint axes.
        low, high = 1e-10, math.pi/2
        for unused in range(100):
            angle = (low+high)/2
            vertical = dx/math.tan(angle)+2*radius*math.tan(angle/2)
            if vertical > height:
                low = angle
            else:
                high = angle
        sign = 1 if x1 > x0 else -1
        straight_length = (dx-2*radius*(1-math.cos(angle)))/math.sin(angle)
        a = V(x0+sign*radius*(1-math.cos(angle)),0,
              start.z-radius*math.sin(angle))
        mid_a = V(x0+sign*radius*(1-math.cos(angle/2)),0,
                  start.z-radius*math.sin(angle/2))
        b = a+V(sign*straight_length*math.sin(angle),0,
                -straight_length*math.cos(angle))
        center_b = b+V(-sign*radius*math.cos(angle),0,
                       -radius*math.sin(angle))
        mid_b = center_b+V(sign*radius*math.cos(angle/2),0,
                           radius*math.sin(angle/2))
        edges = [Part.makeLine(entry,start),
                 Part.Arc(start,mid_a,a).toShape(),
                 Part.makeLine(a,b), Part.Arc(b,mid_b,end).toShape(),
                 Part.makeLine(end,tail)]
        bend_points = [start,a,b,end]
    path = Part.Wire(edges)
    section = Part.Wire(Part.makeCircle(.225,entry,V(0,0,1)))
    solid = path.makePipeShell([section],True,False)
    assert solid.isValid() and len(solid.Solids) == 1
    return solid, {'package_root_x_mm':x0,'board_tail_x_mm':x1,
                   'path_centerline_length_including_embed_mm':path.Length,
                   'formed_trimmed_length_from_body_mm':path.Length-.12,
                   'minimum_factory_length_mm':10.5,
                   'minimum_trimmed_remainder_mm':10.5-(path.Length-.12),
                   'bend_center_radius_mm':radius if dx else None,
                   'bend_angle_deg':math.degrees(angle),
                   'between_bends_straight_length_mm':straight_length,
                   'bend_endpoint_positions_mm':[list(v) for v in bend_points]}


doc = App.newDocument('Mitsubishi2SC2291Candidate')
objects = []
colors = {}
features = []


def bbox(shape):
    # Ordinary BoundBox conservatively overbounds trimmed toroidal sweeps.
    # OCC's optimal BRep box evaluates the actual trimmed surfaces.
    b = shape.optimalBoundingBox()
    return [b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]


def add(label, shape, color):
    obj = doc.addObject('Part::Feature',label)
    obj.Shape = shape
    obj.Label = label
    objects.append(obj)
    colors[label] = color
    return obj


add('Mitsubishi2291_MaxBody_YZBevel',body,[.065,.068,.075])
lead_records = []
pinout = ['E1','C1','B_common','C2','E2']
for i, pad in enumerate(actual_pads):
    lead, record = formed_lead((i-2)*1.25,pad['canonical_xy_mm'][0])
    add('Pin'+str(i+1)+'_'+pinout[i]+'_IllustratedForming',lead,[.72,.74,.77])
    record.update({'pin':str(i+1),'function':pinout[i]})
    lead_records.append(record)
joined = objects[0].Shape
for obj in objects[1:]:
    joined = joined.fuse(obj.Shape)
assert joined.isValid() and len(joined.Solids) == 1
key = 'Mitsubishi_2SC2291_MaxBody_FormedP2p286'
step = HERE/(key+'.step')
stl = HERE/(key+'.stl')
Part.export(objects,str(step))
uncolored = Part.read(str(step))
presentation = set_step_colors(step,colors,objects)
reimported = Part.read(str(step))
assert reimported.isValid() and len(reimported.Solids) == 6
assert uncolored.exportBrepToString() == reimported.exportBrepToString()
MeshPart.meshFromShape(Shape=joined,LinearDeflection=.015,
                       AngularDeflection=.08,Relative=False).write(str(stl))
for obj in objects:
    file = HERE/(key+'--'+obj.Label+'.stl')
    MeshPart.meshFromShape(Shape=obj.Shape,LinearDeflection=.015,
                           AngularDeflection=.08,Relative=False).write(str(file))
    features.append({'name':obj.Label,'stl':str(file),'color_rgb':colors[obj.Label],
                     'exact_bounds_mm':bbox(obj.Shape),'volume_mm3':obj.Shape.Volume})
App.closeDocument(doc.Name)

limits = [
    'Specific Mitsubishi 2SC2291 four-page primary scan is the package '
    'authority; no 2SC1583 body identity is borrowed from a shared footprint.',
    'Body uses the published 8.1 x3.6 x5.6 mm maxima. The 2 x2 mm YZ bevel, '
    '1.4 mm flat-face-to-lead-row datum, 1.25 mm row pitch and 0.45 mm '
    'round leads follow the drawing. Untoleranced dimensions are representative '
    'per the manufacturer note; actual supplied part tolerances are unknown.',
    'Canonical flat face is -Y, opposite bevel is +Y. Pin1 is -X and '
    'pin5 +X before the unchanged Q22 footprint angle180 is applied.',
    'Body bottom Z3.0 mm, tangent circular lead fanout bends of radius0.65mm, '
    '0.12 mm internal model '
    'embed and 2.5 mm cut tails are installed illustration choices. They '
    'are not a published lead forming or stand-off specification.',
    'The 10.5 mm factory lead length is a minimum before trimming. This '
    'candidate depicts explicitly trimmed formed leads; no claim is made '
    'that its shortened installed tails are supplied that way.',
    'Nominal 1.25 mm package pitch fans above the board to original '
    '2.286 mm PCB pitch. Full 0.45 mm lead diameter is retained, and '
    'straight tails are checked through nominal full 1.6 mm lamination.',
    'Bend stress, springback, forming process, material temper, drill plating, '
    'body/lead tolerance, installed clearance and physical hardware fit remain '
    'unqualified. No package scaling or PCB pad movement was used.',
    'Assignment is Q22-specific. Heterogeneous SSIP5 footprint cache remains '
    'unassigned; this candidate must not replace other SSIP5 devices.',
    'Black epoxy and silver lead colors are presentation choices; no embossed '
    'manufacturer text or unverified mold details are added.',
]
urls = [
    'https://www.diyaudio.com/community/attachments/2sc2291-pdf.1587249/',
    'https://ladyada.net/make/x0xb0x/fab/parts.html',
    'https://github.com/x0xb0x/x0xb0x.github.io/blob/1910f746d2d8758f2651596b00c08f76c847c926/assets/images/parts/2SC2291.jpg',
]
assignment = {k:v for k,v in old.items() if k not in ['local_model','review_manifest']}
assignment.update({'source_model':str(step),'source_sha256':sha(step),
                   'source_kind':'Specific Mitsubishi primary package drawing-derived '
                                 'body and explicitly illustrated formed leads',
                   'classification':'Maximum package body with nominal full-diameter '
                                    'leads; installed forming/stand-off illustration',
                   'limitations':limits,'source_urls':urls,
                   'per_instance_override':True,
                   'replaces_source_model':old['source_model'],
                   'replaces_source_sha256':old['source_sha256']})
assert all(sha(p) == digest for p,digest in source_hashes.items())
manifest = {
    'date':'2026-10-14','parts':[{
        'id':key,'board':'mainboard','references':['Q22'],'footprint':'SSIP5',
        'step':str(step),'stl':str(stl),'units':'mm',
        'source_sha256':sha(step),'stl_sha256':sha(stl),
        'classification':assignment['classification'],
        'canonical_frame':'Original F.Cu footprint X, -Y, outward Z. Flat side -Y, '
                          'opposite rear-top YZ bevel +Y, pin1 -X before native pose.',
        'dimensions':P,'source_urls':urls,'limitations':limits,
        'features':features,'material_color_suggestions':colors,
        'exact_bounds_mm':bbox(reimported),
        'body_exact_bounds_mm':bbox(body),
        'geometry':{'valid':True,'solids':6,'fully_joined_union_solids':1,
                    'faces':len(reimported.Faces),'volume_mm3':reimported.Volume,
                    'AP214_presentation':presentation,
                    'roundtrip_geometry_unchanged_by_colors':True},
    }],'assignments':[assignment],
    'primary_pdf':str(source_pdf),'primary_pdf_sha256':sha(source_pdf),
    'publisher':'Mitsubishi Semiconductor; header 三菱半導体〈トランジスタ〉',
    'source_page':1,'source_pinout':['1:E1','2:C1','3:B common','4:C2','5:E2'],
    'actual_source_Q22_at_mm_deg':list(map(float,one(fp,'at')[1:])),
    'actual_source_pads':actual_pads,'lead_forming_records':lead_records,
    'source_file_hashes':source_hashes,'source_files_unchanged':True,
    'heterogeneous_cache_policy':{'footprint':'SSIP5','model_nodes_in_cache':0,
                                'per_instance_Q22_only':True},
    'generator':Path(__file__).name,
    'license':'Original parametric model and code CC0-1.0; manufacturer scan '
              'retains publisher rights.',
}
(HERE/'legacy-quality-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(HERE/'frozen-candidate-hashes.json').write_text(json.dumps(
    {step.name:sha(step),stl.name:sha(stl)},indent=2)+'\n')
print(json.dumps({'source_pdf_sha256':sha(source_pdf),
                  'source_step_sha256':sha(step),
                  'bounds_mm':bbox(reimported),'valid':True,
                  'formed_leads':lead_records},indent=2))
