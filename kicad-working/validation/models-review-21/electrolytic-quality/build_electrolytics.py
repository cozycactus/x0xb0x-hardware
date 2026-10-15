"""Xicon XRL electrolytic bodies at the exact 2.54/5.08 mm PCB pitch, and photo colours.

Builds three original CC0 can models from the XRL datasheet (XC-600178, 1/8/07):
5 x 11 mm (33 references), 6.3 x 11 mm (C7, C8) and 10 x 12.5 mm (C43). Each model
is built in the frame of the inherited KiCad model transform (offset -1.25 or -2.5 mm),
so the PCB footprints, pads and transforms stay unchanged and the leads land on the
original hole centres. The datasheet allows +/-0.5 mm on lead pitch, so straight
leads at 2.54/5.08 mm are within the drawing. The existing revision-5 XRL models of
C17 and C3/C5 are recoloured only: their two sleeve COLOUR_RGB entities change and
the B-rep is byte-identical.

Sleeve and stripe colours are sampled from the original kit photographs; the 0.5 mm
seat gap, vent cross and top disc are illustrations.

Run with FreeCAD's Python from the repository root:
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
      kicad-working/validation/models-review-21/electrolytic-quality/build_electrolytics.py
"""
import ast
import hashlib
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK.parent
V = App.Vector
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
sys.path.insert(0, str(REPO / 'kicad-import/validation'))
from verify_native_projects import children, one, parse_sexpr  # noqa: E402

# color_step() of the revision-5 generator names each MANIFOLD_SOLID_BREP and adds its colour.
GENERATOR = WORK / 'mainboard/3dmodels/Revision5/passive-models/provenance/generate_passive_illustrations.py'
# lead_shape() forms a round lead from its body exit to the hole with a Bezier above the board (finish z 0.45 mm).
nodes = [n for n in ast.parse(GENERATOR.read_text()).body if isinstance(n, ast.FunctionDef) and n.name in ('color_step', 'lead_shape')]
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(GENERATOR), 'exec'))

EVIDENCE = json.loads((HERE / 'sources/electrolytic-evidence.json').read_text())
assert sha(HERE / 'sources' / EVIDENCE['datasheet']['file']) == EVIDENCE['datasheet']['sha256']
SLEEVE = tuple(EVIDENCE['kit_photos']['chosen_colours']['sleeve_srgb'])
STRIPE = tuple(EVIDENCE['kit_photos']['chosen_colours']['negative_stripe_srgb'])
TOP_METAL = (0.70, 0.72, 0.74)      # revision-5 XRL top disc colour
LEAD = (0.68, 0.70, 0.73)           # revision-5 XRL lead colour
TAIL_Z = -2.5                       # revision-5 XRL lead tip (lead_shape)
INPUTS = [WORK / 'mainboard/mainboard.kicad_pcb', WORK / 'ioboard/ioboard.kicad_pcb',
          WORK / 'mainboard/mainboard-import-fps.pretty/E5-6.kicad_mod',
          WORK / 'mainboard/mainboard-import-fps.pretty/E5-5.kicad_mod',
          WORK / 'ioboard/ioboard-import-fps.pretty/E5-6.kicad_mod']
GUARDS = {str(p): sha(p) for p in INPUTS}

FIVE = ['C102', 'C105', 'C11', 'C13', 'C14', 'C15', 'C16', 'C22', 'C23', 'C28', 'C29', 'C30', 'C31', 'C32', 'C37',
        'C38', 'C40', 'C44', 'C48', 'C49', 'C50', 'C51', 'C52', 'C53', 'C55', 'C56', 'C58', 'C59', 'C72']
SPECS = [
    dict(key='XRL_D5', name='CP_Xicon_XRL_D5.0x11_P2.54_KiCadFrame', diameter=5.0, length=11.0, lead_d=0.5,
         factory_pitch=2.0, pitch=2.54, offset=-1.25, vent=False, footprint='E5-6', seat=1.5,
         refs=[('mainboard', r) for r in FIVE] + [('ioboard', r) for r in ('C203', 'C205', 'C60', 'C61')],
         parts='1.0uF 50V, 2.2uF 50V, 10uF 16V, 47uF 16V and 100uF 10V (XRL 5 x 11)'),
    dict(key='XRL_D6.3', name='CP_Xicon_XRL_D6.3x11_P2.54_KiCadFrame', diameter=6.3, length=11.0, lead_d=0.5,
         factory_pitch=2.5, pitch=2.54, offset=-1.25, vent=True, footprint='E5-6', seat=0.5,
         refs=[('ioboard', 'C7'), ('ioboard', 'C8')], parts='100uF 25V (XRL 6.3 x 11)'),
    dict(key='XRL_D10', name='CP_Xicon_XRL_D10x12.5_P5.08_KiCadFrame', diameter=10.0, length=12.5, lead_d=0.6,
         factory_pitch=5.0, pitch=5.08, offset=-2.5, vent=True, footprint='E5-5', seat=0.5,
         refs=[('mainboard', 'C43')], parts='1000uF 10V (XRL 10 x 12.5)'),
]
RECOLOUR = [
    dict(board='mainboard', refs=['C17'], source='Revision5/passive-models/CP_Xicon_XRL1u50_P3.556_Illustration.step',
         output='CP_Xicon_XRL1u50_P3.556_PhotoColours.step'),
    dict(board='ioboard', refs=['C3', 'C5'], source='Revision5/passive-models/CP_Xicon_XRL2200u16_P5.08_Illustration.step',
         output='CP_Xicon_XRL2200u16_P5.08_PhotoColours.step'),
]
checks = []


def check(name, ok, **detail):
    checks.append(dict(check=name, passed=bool(ok), **detail))
    if not ok:
        print('FAIL', json.dumps(checks[-1]), flush=True)


def footprints(board):
    tree = parse_sexpr((WORK / board / f'{board}.kicad_pcb').read_text())
    out = {}
    for fp in children(tree, 'footprint'):
        ref = next(p[2] for p in children(fp, 'property') if p[1] == 'Reference')
        out[ref] = fp
    return out


FPS = {b: footprints(b) for b in ('mainboard', 'ioboard')}


def pad_record(board, ref, spec):
    fp = FPS[board][ref]
    assert fp[1].split(':')[-1] == spec['footprint'], (ref, fp[1])
    pads = {p[1]: p for p in children(fp, 'pad')}
    assert set(pads) == {'+', '-'}, (ref, set(pads))
    rows = {n: dict(x=float(one(p, 'at')[1]), y=float(one(p, 'at')[2]), drill=float(one(p, 'drill')[1])) for n, p in pads.items()}
    model = one(fp, 'model')
    offset = [float(v) for v in one(one(model, 'offset'), 'xyz')[1:]]
    rotate = [float(v) for v in one(one(model, 'rotate'), 'xyz')[1:]]
    scale = [float(v) for v in one(one(model, 'scale'), 'xyz')[1:]]
    return dict(pads=rows, offset=offset, rotate=rotate, scale=scale, model=model[1])


def build(spec):
    r, h, cx, SEAT = spec['diameter'] / 2, spec['length'], -spec['offset'], spec['seat']
    sleeve = Part.makeCylinder(r, h - 0.2, V(0, 0, SEAT), V(0, 0, 1), 320)
    sleeve.rotate(V(0, 0, 0), V(0, 0, 1), 20)
    stripe = Part.makeCylinder(r, h - 0.2, V(0, 0, SEAT), V(0, 0, 1), 40)
    stripe.rotate(V(0, 0, 0), V(0, 0, 1), -20)
    top = Part.makeCylinder(r - 0.1, 0.2, V(0, 0, SEAT + h - 0.2))
    if spec['vent']:
        # Datasheet: vent on the top for diameter >= 6.3 mm. Cross shape and 0.08 mm depth are illustrations.
        arm = 0.62 * (r - 0.1)
        z = SEAT + h - 0.08
        groove = Part.makeBox(2 * arm, 0.25, 0.2, V(-arm, -0.125, z)).fuse(Part.makeBox(0.25, 2 * arm, 0.2, V(-0.125, -arm, z)))
        top = top.cut(groove).removeSplitter()
    parts = [('Sleeve', sleeve, SLEEVE), ('NegativeStripe', stripe, STRIPE), ('TopMetal', top, TOP_METAL)]
    # Leads leave the seal at the factory pitch when the board pitch is outside the +/-0.5 mm drawing
    # tolerance (5 mm can: 2.0 -> 2.54 mm) and are formed to the hole above the board; otherwise straight.
    formed = abs(spec['pitch'] - spec['factory_pitch']) > 0.5
    exit_pitch = spec['factory_pitch'] if formed else spec['pitch']
    for name, sign in (('Lead_Positive', -1), ('Lead_Negative', 1)):
        lead = lead_shape(sign * exit_pitch / 2, sign * spec['pitch'] / 2, SEAT + 0.05, spec['lead_d'] / 2)
        parts.append((name, lead, LEAD))
    for _, shape, _ in parts:
        shape.translate(V(cx, 0, 0))
    return [(n, s.Solids[0], c) for n, s, c in parts]


def section_centres(shape, z):
    sec = shape.section(Part.makePlane(60, 60, V(-30, -30, z)))
    wires = []
    edges = list(sec.Edges)
    while edges:
        group = Part.__sortEdges__(edges)
        wires.append(Part.Wire(group))
        edges = [e for e in edges if not any(e.isSame(g) for g in group)]
    out = []
    for w in wires:
        b = w.BoundBox
        out.append(dict(centre=[(b.XMin + b.XMax) / 2, (b.YMin + b.YMax) / 2], size=[b.XLength, b.YLength]))
    return sorted(out, key=lambda s: s['centre'][0])


models = {}
for spec in SPECS:
    parts = build(spec)
    name, cx, SEAT = spec['name'], -spec['offset'], spec['seat']
    formed = abs(spec['pitch'] - spec['factory_pitch']) > 0.5
    for n, s, _ in parts:
        check(f'{name}: {n} is one valid solid', s.isValid() and len(s.Solids) == 1)
    body = Part.makeCompound([s for n, s, _ in parts if not n.startswith('Lead')])
    b = body.BoundBox
    check(f'{name}: datasheet can diameter and length', abs(b.XLength - spec['diameter']) < 1e-6 and
          abs(b.YLength - spec['diameter']) < 1e-6 and abs(b.ZLength - spec['length']) < 1e-6,
          bounds_mm=[round(v, 6) for v in (b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax)])
    check(f'{name}: can centred between the holes and seated {SEAT} mm above the board',
          abs((b.XMin + b.XMax) / 2 - cx) < 1e-6 and abs((b.YMin + b.YMax) / 2) < 1e-6 and abs(b.ZMin - SEAT) < 1e-6)
    stripe = next(s for n, s, _ in parts if n == 'NegativeStripe')
    check(f'{name}: negative stripe faces the negative lead (+X)', stripe.CenterOfMass.x > cx)
    leads = {n: s for n, s, _ in parts if n.startswith('Lead')}
    can = Part.makeCompound([s for n, s, _ in parts if n in ('Sleeve', 'NegativeStripe')])
    for n, s in leads.items():
        check(f'{name}: {n} joins the can', s.common(can).Volume > 1e-6)
    check(f'{name}: leads do not touch each other', leads['Lead_Positive'].distToShape(leads['Lead_Negative'])[0] > 1.0)
    start = {n: max(s.Faces, key=lambda f: f.CenterOfMass.z) for n, s in leads.items()}   # planar start face in the can
    exits = [start[n].CenterOfMass.x - cx for n in ('Lead_Positive', 'Lead_Negative')]
    holes = [section_centres(leads[n], -0.8)[0]['centre'][0] - cx for n in ('Lead_Positive', 'Lead_Negative')]
    check(f'{name}: leads leave the seal at the ' + ('factory pitch and are formed to' if formed else 'board pitch, within the +/-0.5 mm drawing tolerance of')
          + ' the exact board pitch', abs(exits[1] - exits[0] - (spec['factory_pitch'] if formed else spec['pitch'])) < 1e-6 and
          abs(holes[1] - holes[0] - spec['pitch']) < 1e-6 and abs(exits[1] - exits[0] - spec['factory_pitch']) <= 0.5 + 1e-9,
          exit_pitch_mm=round(exits[1] - exits[0], 6), board_pitch_mm=round(holes[1] - holes[0], 6))
    for n, s in leads.items():
        check(f'{name}: {n} keeps its full {spec["lead_d"]} mm section at the seal, board faces and tip',
              abs(start[n].Area - math.pi * spec['lead_d'] ** 2 / 4) < 1e-6 and abs(start[n].CenterOfMass.z - SEAT - 0.05) < 1e-9 and
              all(abs(max(sec['size']) - spec['lead_d']) < 1e-6 for z in (0.0, -1.6, TAIL_Z + 0.05)
                  for sec in section_centres(s, z)))
    fused = parts[0][1]
    for _, s, _ in parts[1:]:
        fused = fused.fuse(s)
    check(f'{name}: all parts fuse to one connected solid', fused.isValid() and len(fused.Solids) == 1)
    out = HERE / f'{name}.step'
    doc = App.newDocument(name.replace('.', '_'))
    objs = []
    for n, s, _ in parts:
        o = doc.addObject('Part::Feature', n)
        o.Shape = s
        objs.append(o)
    doc.recompute()
    Part.export(objs, str(out))
    App.closeDocument(doc.Name)
    color_step(out, parts)
    out.write_text('\n'.join(line.rstrip() for line in out.read_text().splitlines()) + '\n')
    back = Part.read(str(out))
    check(f'{name}: saved STEP has five valid solids with the same volumes and centroids',
          back.isValid() and len(back.Solids) == 5 and all(
              abs(a.Volume - s.Volume) < 1e-6 and (a.CenterOfMass - s.CenterOfMass).Length < 1e-6
              for a, (_, s, _) in zip(back.Solids, parts)))
    names = re.findall(r"MANIFOLD_SOLID_BREP\('(\w+)'", out.read_text())
    check(f'{name}: named solids in order', names == [n for n, _, _ in parts], names=names)
    # Leads are checked in the PCB footprint frame for every placed reference: model frame + transform offset.
    sections = {z: section_centres(back, z) for z in (0.0, -0.05, -0.8, -1.5, -1.6)}
    placements = []
    for board, ref in spec['refs']:
        rec = pad_record(board, ref, spec)
        check(f'{name}: {board} {ref} keeps the inherited transform', rec['offset'] == [spec['offset'], 0, 0] and
              rec['rotate'] == [0, 0, 0] and rec['scale'] == [1, 1, 1], transform=rec)
        rows = []
        for z, secs in sections.items():
            lead_secs = [s for s in secs if max(s['size']) < spec['lead_d'] + 1e-6]
            ok = len(lead_secs) == 2
            for pad, s in zip(('+', '-'), lead_secs):
                p = rec['pads'][pad]
                x = s['centre'][0] + rec['offset'][0]
                ok = ok and abs(x - p['x']) < 1e-6 and abs(s['centre'][1] - p['y']) < 1e-6 and \
                    abs(s['size'][0] - spec['lead_d']) < 1e-6
                rows.append(dict(z_mm=z, pad=pad, hole_centre_mm=[p['x'], p['y']], lead_centre_mm=[round(x, 6), round(s['centre'][1], 6)],
                                 radial_margin_mm=round(p['drill'] / 2 - spec['lead_d'] / 2, 4)))
            check(f'{name}: {board} {ref} leads centred in pads + and - at z={z}', ok)
        placements.append(dict(board=board, reference=ref, pad_centres_mm={k: [v['x'], v['y']] for k, v in rec['pads'].items()},
                               drill_mm=rec['pads']['+']['drill'], previous_model=rec['model'], sections=rows[:2]))
    models[spec['key']] = dict(name=name, output=out.name, output_sha256=sha(out), parts=spec['parts'],
                               dimensions_mm=dict(diameter=spec['diameter'], length=spec['length'], lead_diameter=spec['lead_d'],
                                                  factory_pitch=spec['factory_pitch'], board_pitch=spec['pitch'], leads_formed=formed,
                                                  seat_gap=SEAT, lead_tip_z=TAIL_Z, top_z=SEAT + spec['length']),
                               model_frame=f'Inherited KiCad transform offset ({spec["offset"]}, 0, 0); can centre at model x={-spec["offset"]}',
                               vent=spec['vent'], references=[f'{b}:{r}' for b, r in spec['refs']], placements=placements,
                               colours=dict(Sleeve=SLEEVE, NegativeStripe=STRIPE, TopMetal=TOP_METAL, Leads=LEAD))

recoloured = {}
for item in RECOLOUR:
    src = WORK / item['board'] / '3dmodels' / item['source']
    text = src.read_text()
    ent = {int(n): body for n, body in re.findall(r'#(\d+)\s*=\s*(.*?);', text, re.S)}
    names = re.findall(r"#(\d+)\s*=\s*MANIFOLD_SOLID_BREP\('(\w+)'", text)
    styled = {int(b): int(a) for a, b in re.findall(r"STYLED_ITEM\('[^']*',\(#(\d+)\),#(\d+)\)", text)}
    colour_of = {}
    for brep, role in names:
        assignment = styled[int(brep)]
        chain = int(re.findall(r'#(\d+)', ent[assignment])[0])          # SURFACE_STYLE_USAGE
        for _ in range(4):                                             # side -> fill -> area -> area colour
            chain = int(re.findall(r'#(\d+)', ent[chain])[-1])
        colour_of[role] = int(re.findall(r'#(\d+)', ent[chain])[0])
    for role in colour_of:
        assert ent[colour_of[role]].startswith('COLOUR_RGB')
    new_text = text
    changes = {}
    for role, rgb in (('Sleeve', SLEEVE), ('NegativeStripe', STRIPE)):
        entity = colour_of[role]
        old = re.search(rf'#{entity}\s*=\s*COLOUR_RGB\(.*?\);', new_text).group(0)
        new = f"#{entity} = COLOUR_RGB('',{rgb[0]},{rgb[1]},{rgb[2]});"
        new_text = new_text.replace(old, new, 1)
        changes[role] = dict(entity=entity, old=old, new=new)
    out = HERE / item['output']
    out.write_text(new_text)
    new_ent = {int(n): body for n, body in re.findall(r'#(\d+)\s*=\s*(.*?);', new_text, re.S)}
    differing = sorted(i for i in ent if ent[i] != new_ent.get(i))
    a, b = Part.Shape(), Part.Shape()
    a.read(str(src))
    b.read(str(out))
    check(f'{item["output"]}: only the sleeve and stripe COLOUR_RGB entities differ',
          set(ent) == set(new_ent) and differing == sorted(c['entity'] for c in changes.values()), changed=differing)
    check(f'{item["output"]}: reloaded B-rep identical to revision 5', b.isValid() and a.exportBrepToString() == b.exportBrepToString())
    recoloured[item['output']] = dict(board=item['board'], references=item['refs'], source=item['source'], source_sha256=sha(src),
                                      output=out.name, output_sha256=sha(out), colour_changes=changes,
                                      geometry_changed=False)

check('Original PCBs and footprint files unchanged by the build', GUARDS == {str(p): sha(p) for p in INPUTS})
report = dict(schema=1, revision=21, generator='build_electrolytics.py', passed=all(c['passed'] for c in checks),
              check_count=len(checks), checks=checks, models=models, recoloured=recoloured,
              source=dict(datasheet=EVIDENCE['datasheet']['file'], datasheet_sha256=EVIDENCE['datasheet']['sha256'],
                          evidence='sources/electrolytic-evidence.json', evidence_sha256=sha(HERE / 'sources/electrolytic-evidence.json')),
              limitations=['Original CC0 illustrations from the XRL datasheet table and drawing; not manufacturer CAD or a measurement of the fitted historical parts.',
                           'Expanded-BOM part numbers come from search-engine extracts of a page that could not be read directly; the 100uF 10V/25V assignment is inferred from the parts page and its photographs.',
                           'Sleeve and stripe colours are sampled from uncalibrated photographs; printed value text is omitted.',
                           'The seat gaps (1.5 mm for 5 mm cans, whose leads are formed from 2.0 to 2.54 mm; 0.5 mm otherwise), lead forming, top disc, vent cross and 2.5 mm lead tip are illustrations; the datasheet allows +/-1 mm diameter and +/-1.5 mm length.',
                           'PCB value fields (47/16, 100/6.3, 1000/6.3) differ from the parts page and are left unchanged.'],
              physical_fit_qualified=False)
(HERE / 'electrolytic-model-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(passed=report['passed'], check_count=len(checks), models={k: v['output_sha256'][:12] for k, v in models.items()}), indent=2))
assert report['passed']
