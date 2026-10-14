#!/usr/bin/env python3
"""Qualified historical Sanyo NP2003A illustrations from primary No.333H.

SPDX-License-Identifier: CC0-1.0
Original reconstruction code and geometry. Manufacturer PDFs/photos retain
publisher rights. This generator writes only its own candidate directory.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
import Import
import Mesh
import MeshPart
from step_appearance import face_colors

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
ROOT = WORK.parent
SOURCE = HERE.parent / 'transistor-research'
V = App.Vector
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
sys.path.insert(0, str(ROOT / 'kicad-import/validation'))
from verify_native_projects import tokens, children, one, property_value


def tree(text):
    roots, stack = [], []
    for token, quoted in tokens(text):
        if token == '(' and not quoted:
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif token == ')' and not quoted:
            stack.pop()
        else:
            stack[-1].append(token)
    assert len(roots) == 1 and not stack
    return roots[0]


def bounds(shape):
    b = shape.optimalBoundingBox(False, False)
    return [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax]


checks = []


def check(name, condition, **evidence):
    row = dict(name=name, passed=bool(condition), **evidence)
    checks.append(row)
    if not condition:
        print(json.dumps(row, indent=2), flush=True)
        raise AssertionError(name)


def np_body(cx, seat):
    # Published typical limits are 5 wide x 4 deep x 5 high. The four profile
    # curves, flat-face datum -1.5, chamfers and shallow mould recess are visual
    # interpretations of the unsized profile and original unscaled photograph.
    p = lambda x, y: V(cx + x, y, seat)
    edges = [Part.makeLine(p(-2, -1.5), p(2, -1.5)),
             Part.makeLine(p(2, -1.5), p(2.5, -1.15)),
             Part.makeLine(p(2.5, -1.15), p(2.5, 0))]
    for poles in [[(2.5, 0), (2.5, 1.45), (1.35, 2.5), (0, 2.5)],
                  [(0, 2.5), (-1.35, 2.5), (-2.5, 1.45), (-2.5, 0)]]:
        c = Part.BezierCurve()
        c.setPoles([p(x, y) for x, y in poles])
        edges.append(c.toShape())
    edges.extend([Part.makeLine(p(-2.5, 0), p(-2.5, -1.15)),
                  Part.makeLine(p(-2.5, -1.15), p(-2, -1.5))])
    body = Part.Face(Part.Wire(edges)).extrude(V(0, 0, 5))
    # The photo has subtle vertical edge lips. This 0.035 mm recess is cosmetic,
    # not a dimension inferred from pixel measurement, and keeps every envelope.
    recess = Part.makeBox(3.76, .05, 4.64,
                          V(cx - 1.88, -1.515, seat + .18))
    return body.cut(recess).removeSplitter()


def formed_lead(factory_x, pad_x, seat, tail):
    # A constant 0.45 mm-wide ribbon in XZ, extruded 0.44 mm in Y. Union of
    # segment strips and radius-0.225 joining disks never thins the source stock.
    # Board-through portions stay vertical at the exact original pad axes.
    # Bend positions are qualified installation choices; root factory pitch1.3.
    pts = [(pad_x, tail), (pad_x, .45),
           (factory_x, seat - .55), (factory_x, seat + .12)]
    pieces = []
    r = .225
    for (x1, z1), (x2, z2) in zip(pts, pts[1:]):
        dx, dz = x2 - x1, z2 - z1
        length = math.hypot(dx, dz)
        ox, oz = r * dz / length, -r * dx / length
        poly = [V(x1 + ox, -.22, z1 + oz), V(x2 + ox, -.22, z2 + oz),
                V(x2 - ox, -.22, z2 - oz), V(x1 - ox, -.22, z1 - oz)]
        pieces.append(Part.Face(Part.makePolygon(poly + [poly[0]])).extrude(V(0, .44, 0)))
    for x, z in pts[1:-1]:
        pieces.append(Part.makeCylinder(r, .44, V(x, -.22, z), V(0, 1, 0)))
    lead = pieces[0].multiFuse(pieces[1:]).removeSplitter()
    return lead, pts


boards = {b: tree((WORK / b / (b + '.kicad_pcb')).read_text())
          for b in ['mainboard', 'ioboard']}
guards = {str(WORK / b / (b + '.kicad_pcb')):
          sha(WORK / b / (b + '.kicad_pcb')) for b in boards}
baseline = json.loads((WORK / 'validation/models-review-10/combined-model-plan.json').read_text())
rows = [a for a in baseline['assignments']
        if a['footprint'] in ['2SC536F', '2SC536_UNEVEN']]
check('exact24references', sum(len(a['references']) for a in rows) == 24 and len(rows) == 3)

# Independently inspect the imported symbol pin names, including the uneven form.
for board in boards:
    sch = tree((WORK / board / (board + '.kicad_sch')).read_text())
    for symbol in children(one(sch, 'lib_symbols'), 'symbol'):
        if '2SC536F' not in symbol[1]:
            continue
        names = {}
        for unit in children(symbol, 'symbol'):
            for pin in children(unit, 'pin'):
                names[one(pin, 'number')[1]] = one(pin, 'name')[1]
        check(board + ':' + symbol[1] + ':original-BCE-mapping',
              names == {'1': 'B', '2': 'C', '3': 'E'}, actual=names)

specs = [dict(id='Sanyo_2SC536_NP2003A_Typical_InlineForm_Illustration',
              footprint='2SC536F', cx=2.54, seat=2.5, tail=-2.7,
              pad_x=[5.08, 2.54, 0], offset_mm=[-2.54, 0, 0]),
         dict(id='Sanyo_2SC536_NP2003A_Typical_AsymmetricForm_Illustration',
              footprint='2SC536_UNEVEN', cx=0, seat=3.2, tail=-2.5,
              pad_x=[2.54, 0, -3.302], offset_mm=[0, 0, 0])]
urls = ['https://www.bitsavers.org/components/sanyo/_dataBooks/1985_Sanyo_Semiconductor_Handbook_-_Transistors.pdf',
        'https://www.ladyada.net/make/x0xb0x/fab/parts.html',
        'https://raw.githubusercontent.com/x0xb0x/x0xb0x.github.io/1910f746d2d8758f2651596b00c08f76c847c926/assets/images/parts/2sc536.jpg']
limitations = [
    'Independent original reconstruction from historical Sanyo No.333H, not redistributed manufacturer CAD or proof of the actually fitted manufacturer/mould.',
    'The original BOM explicitly calls 2SC536F TO-92. No333H identifies NP2003A as TO-92; the original nearly-square front photo is consistent with this family. Exact fitted vendor and rear profile are unverified.',
    'Published NP body5x4x5mm, factory1.3mm pitch and0.45x0.44mm lead section are TYPICAL, not maximum toleranced clearance envelopes. F is a160-320 gain rank, not package identification.',
    'Body curve poles/chamfers, flat-faceYdatum-1.5mm, shallow front recess, colors and smooth appearance are unsized illustrative interpretations; no body is shrunk to fit silk or other components.',
    'Original normal model seat2.5mm/tail-2.7mm and asymmetric seat3.2mm/tail-2.5mm are retained as installation choices. Factory14mm lead length is not an installed tail-length specification.',
    'Full0.45x0.44mm ribbon leads retain source stock, with qualified bend positions and rounded joining regions. Factory1.3mm exits are formed to existing2.54mm/asymmetric2.54-3.302mm pad axes without moving or thinning board-through leads.',
    'Bottom-view B-C-E mapping is checked against the original symbols and preserved pad numbers1-2-3. Flat side remains negativeSTEPY/positivePCB-Y under unchanged original transforms.',
    'Nominal drill margins are geometry checks only; source tolerances, actual lead forming, installed clearances, soldering and physical fit remain unqualified.'
]
parts, assignments = [], []
for spec in specs:
    name = spec['id']; cx, seat, tail = spec['cx'], spec['seat'], spec['tail']
    body = np_body(cx, seat)
    check(name + ':valid-one-solid-body', body.isValid() and len(body.Solids) == 1)
    expected_body = [cx-2.5, -1.5, seat, cx+2.5, 2.5, seat+5]
    check(name + ':published-typical-body-envelope',
          max(abs(a-b) for a,b in zip(bounds(body), expected_body)) < 1e-6,
          expected_mm=expected_body, actual_mm=bounds(body))
    leads, paths = [], []
    for pin, pad_x in enumerate(spec['pad_x'], 1):
        factory_x = cx + {1: 1.3, 2: 0, 3: -1.3}[pin]
        lead, path = formed_lead(factory_x, pad_x, seat, tail)
        check(name + f':pin{pin}:valid-one-connected-lead', lead.isValid() and len(lead.Solids) == 1)
        for z in [-1.6, -.8, -.05, 0]:
            slab = lead.common(Part.makeBox(20, 20, .001, V(cx-10, -10, z)))
            b = bounds(slab)
            check(name + f':pin{pin}:full-section-Z{z}',
                  max(abs(a-bb) for a,bb in zip(b, [pad_x-.225, -.22, z, pad_x+.225, .22, z+.001])) < 1e-6,
                  actual_bounds_mm=b, pad_axis_source_mm=[pad_x, 0],
                  section_mm=[.45, .44])
        upper = lead.common(Part.makeBox(20, 20, .001, V(cx-10, -10, seat-.2)))
        check(name + f':pin{pin}:factory1.3exit',
              abs((bounds(upper)[0]+bounds(upper)[3])/2-factory_x)<1e-6,
              factory_axis_mm=[factory_x, 0])
        leads.append(lead); paths.append(path)
    union = body.multiFuse(leads).removeSplitter()
    check(name + ':one-connected-assembly', union.isValid() and len(union.Solids) == 1)
    for i in range(3):
        for j in range(i+1, 3):
            check(name + f':lead{i+1}-lead{j+1}:no-short', leads[i].common(leads[j]).Volume < 1e-9)
    doc = App.newDocument(name)
    features = []
    objects = []
    palette = [[.075, .08, .085]] + [[.72, .73, .75]]*3
    labels = ['MouldedNPBody', 'BaseFullWidthLead', 'CollectorFullWidthLead', 'EmitterFullWidthLead']
    for label, shape, color in zip(labels, [body]+leads, palette):
        obj = doc.addObject('PartDesign::Feature', label)
        obj.Shape = shape; objects.append(obj)
        path = HERE / (name + '--' + label + '.stl')
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.012, AngularDeflection=.08, Relative=False)
        mesh.write(str(path))
        check(name + ':' + label + ':closed-mesh', mesh.isSolid())
        features.append(dict(name=label, role='body' if label==labels[0] else 'lead',
                             stl=str(path), sha256=sha(path), units='mm',
                             color_rgb=color, exact_bounds_mm=bounds(shape), volume_mm3=shape.Volume))
    doc.recompute()
    step = HERE / (name+'.step')
    Import.export(objects, str(step)); face_colors(step, palette)
    restored = Part.read(str(step)); compound = Part.makeCompound([body]+leads)
    check(name + ':STEP-roundtrip', restored.isValid() and len(restored.Solids)==4 and
          abs(restored.Volume-compound.Volume)/compound.Volume < 1e-7 and
          max(abs(a-b) for a,b in zip(bounds(restored), bounds(compound))) < 1e-6,
          restored_bounds_mm=bounds(restored), relative_volume_error=abs(restored.Volume-compound.Volume)/compound.Volume)
    stl = HERE/(name+'.stl')
    mesh = MeshPart.meshFromShape(Shape=union, LinearDeflection=.012, AngularDeflection=.08, Relative=False)
    mesh.write(str(stl)); check(name+':closed-exterior-STL', mesh.isSolid())
    doc.saveAs(str(HERE/(name+'.FCStd')));App.closeDocument(doc.Name)
    source_refs = []
    for row in [r for r in rows if r['footprint']==spec['footprint']]:
        for ref in row['references']:
            fp = next(f for f in children(boards[row['board']], 'footprint')
                      if property_value(f,'Reference','reference')==ref)
            model = children(fp,'model')[0]
            trans = {key:[float(v) for v in one(one(model,field),'xyz')[1:]]
                     for key,field in [('offset_mm','offset'),('rotation_deg','rotate'),('scale','scale')]}
            check(row['board']+':'+ref+':unchanged-transforms',
                  trans==dict(offset_mm=spec['offset_mm'], rotation_deg=[0,0,0],scale=[1,1,1]), actual=trans)
            pads = []
            for pad in children(fp,'pad'):
                pin=int(pad[1]); p=one(pad,'at'); x,y=map(float,p[1:3])
                drill=float(one(pad,'drill')[1]); expected_x=spec['pad_x'][pin-1]+spec['offset_mm'][0]
                margin=drill/2-math.hypot(.45,.44)/2
                check(row['board']+':'+ref+f':pin{pin}:axis-full-stock-hole',
                      abs(x-expected_x)<1e-9 and abs(y)<1e-9 and margin>0,
                      center_pcb_mm=[x,y], lead_section_mm=[.45,.44], drill_mm=drill,
                      nominal_radial_margin_mm=margin, pin_name={1:'B',2:'C',3:'E'}[pin])
                pads.append(dict(pad=str(pin), pin_name={1:'B',2:'C',3:'E'}[pin],
                                 center_mm=[x,y],drill_mm=drill,nominal_radial_margin_mm=margin))
            source_refs.append(dict(board=row['board'],reference=ref,footprint=spec['footprint'],
                                    input_board_sha256=guards[str(WORK/row['board']/(row['board']+'.kicad_pcb'))],pads=pads))
        assignments.append(dict(board=row['board'],references=row['references'],footprint=row['footprint'],
                                source_model=str(step),source_sha256=sha(step),
                                local_model='Revision11/transistor-quality/'+step.name,
                                offset_mm=spec['offset_mm'],rotation_deg=[0,0,0],scale=[1,1,1],
                                classification='Qualified historical Sanyo NP2003A primary-typical package illustration',
                                source_kind='Independent CC0 reconstruction from historical primary manufacturer drawing',
                                source_urls=urls,limitations=limitations,source_refs=source_refs,
                                previous_local_model=row['local_model'], previous_source_sha256=row['source_sha256']))
    parts.append(dict(id=name,step=str(step),stl=str(stl),units='mm',
                      source_sha256=sha(step),stl_sha256=sha(stl),segments=features,
                      geometry=dict(valid=restored.isValid(),solids=len(restored.Solids),exact_bounds_mm=bounds(restored),
                                    volume_mm3=restored.Volume,union_solids=len(union.Solids),STL_closed=mesh.isSolid()),
                      body_bounds_mm=expected_body,board='mainboard',
                      boards=sorted({p['board'] for p in source_refs}),
                      references_by_board={b: [p['reference'] for p in source_refs if p['board']==b]
                                           for b in sorted({p['board'] for p in source_refs})},
                      references=[p['reference'] for p in source_refs],footprint=spec['footprint'],
                      dimensions=dict(body_typical_mm=[5,4,5],body_seat_Z_mm=seat,tail_minimum_Z_mm=tail,
                                      lead_stock_section_mm=[.45,.44],factory_pitch_mm=1.3,
                                      factory_length_mm=14,source_pad_axes_mm=[[x,0] for x in spec['pad_x']],
                                      factory_axes_mm=[[cx+1.3,0],[cx,0],[cx-1.3,0]],bend_centerlines_XZ_mm=paths),
                      source_urls=urls,limitations=limitations,source_refs=source_refs,
                      canonical_frame='STEPY=-PCB-Y; flatfaceSTEPY-1.5; originaloffset/rotation retained; pin1B onpositiveX.'))

for path,digest in guards.items():
    check('source-project-unchanged:'+Path(path).parent.name,sha(path)==digest)
manifest=dict(date='2026-10-14',parts=parts,assignments=assignments,
              generator='build_transistors.py',license='Original reconstruction code and geometry CC0-1.0; source documents and photos retain publisher copyright.',
              geometry_audit='transistor-quality-geometry-review.json',native_export_audit='native-export-audit.json',
              documentation='README.md',source_review='../transistor-research/transistor-source-review.json')
(HERE/'transistor-quality-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(HERE/'transistor-quality-geometry-review.json').write_text(json.dumps(dict(
    passed=True,check_count=len(checks),failure_count=0,physical_fit_qualified=False,
    source_projects_unchanged=True,checks=checks),indent=2)+'\n')
print(json.dumps(dict(passed=True,checks=len(checks),models={p['id']:p['source_sha256'] for p in parts}),indent=2),flush=True)
