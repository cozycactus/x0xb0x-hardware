"""Independent primary-drawing reconstructions for three rear connectors.

SPDX-License-Identifier: CC0-1.0
Manufacturer drawings retain their respective rights. No downloaded CAD is
read or incorporated. Only this directory is written. Source projects are
guarded, read-only inputs. Millimetres; original footprint X,-Y,Z outward.
"""
from pathlib import Path
import hashlib, json, math, sys
sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part, Mesh, MeshPart
from step_appearance import face_colors

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
V = App.Vector
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
guards = {str(WORK / b / (b + '.kicad_pcb')):
          sha(WORK / b / (b + '.kicad_pcb'))
          for b in ['mainboard', 'ioboard']}
COLORS = {'housing': [.025, .028, .032], 'cover': [.047, .05, .054],
          'contact': [.62, .64, .67], 'bushing': [.55, .57, .60]}


def box(w, d, h, x=None, y=0, z=0):
    return Part.makeBox(w, d, h, V(-w / 2 if x is None else x, y, z))


def cy(r, d, y, z, direction=1, x=0):
    return Part.makeCylinder(r, d, V(x, y, z), V(0, direction, 0))


def yz_prism(points, x, w):
    pp = [V(x, y, z) for y, z in points]
    return Part.Face(Part.makePolygon(pp + [pp[0]])).extrude(V(w, 0, 0))


def fuse(parts):
    s = parts[0]
    for p in parts[1:]:
        s = s.fuse(p)
    return s.removeSplitter()


def cut(s, tool):
    return s.cut(tool).removeSplitter()


def bounds(s):
    if len(s.Solids) > 1:
        bb = [bounds(t) for t in s.Solids]
        return [min(b[i] for b in bb) for i in range(3)] + [
            max(b[i] for b in bb) for i in range(3, 6)]
    b = s.optimalBoundingBox(False, False)
    return [b.XMin, b.YMin, b.ZMin, b.XMax, b.YMax, b.ZMax]


def check(name, ok, **evidence):
    checks.append(dict(name=name, passed=bool(ok), **evidence))
    if not ok:
        print(json.dumps(checks[-1], indent=2), flush=True)
    assert ok, name


# The MJ drawing dimensions the full10 x15.8 x10 body and source aperture,
# bushing and axis. Unsized roof/recess/contact dimensions below are explicit
# visual reconstruction parameters, independent of PCB/case clearances.
mj_profile = [(0, 0), (15.8, 0), (15.8, 7.5), (10.0, 7.5),
              (2.3, 10.0), (0, 10.0)]
mj_housing = yz_prism(mj_profile, -5, 10)
mj_housing = cut(mj_housing, box(7.1, 13.8, 5, y=1.3, z=7.05))
# Published3.6mm bore enters the molded body, avoiding the old shallow blind
# cylinder. Fourteen millimetres is the depicted mating plug length, not a
# manufacturer bore-depth tolerance; the bore depth here is illustrative.
mj_housing = cut(mj_housing, cy(1.8, 14.15, -.05, 5.5))
for sign in [-1, 1]:
    mj_housing = cut(mj_housing,
                     box(.27, 3.3, .43, x=sign * 4.88 - .135,
                         y=6.35, z=5.45))
# Separate rear molded bridge, visibly retained within15.8mm outer depth.
mj_rear = box(7.1, .7, .45, y=15.1, z=7.05)
mj_bushing = fuse([cy(3.0, 2.8, -2.8, 5.5),
                   Part.makeCone(2.8, 3.0, .2, V(0, -3, 5.5), V(0, 1, 0))])
mj_bushing = cut(mj_bushing, cy(1.8, 3.2, -3.1, 5.5))
# Annular impression in the nonthreaded, nickel-plated front. This is an
# unsized appearance feature inside the full published diameter/projection.
mj_bushing = cut(mj_bushing, cut(cy(2.57, .08, -3.01, 5.5),
                               cy(2.45, .10, -3.02, 5.5)))
# Visible internal metal arch and rear leaf reflect the manufacturer isometric
# view; thickness and curvature are expressly unqualified visual details.
mj_arch = cut(cy(2.7, 4.1, 4.7, 5.5), cy(2.43, 4.3, 4.6, 5.5))
mj_arch = cut(mj_arch, box(8, 5, 8, y=4.3, z=-1.25))
mj_leaf = yz_prism([(9.6, 7.06), (11.4, 7.1), (13.5, 7.65),
                    (14.2, 7.25), (14.2, 7.54), (13.5, 7.95),
                    (11.35, 7.4), (9.6, 7.36)], -1.0, 2.0)
mj_segments = [('SlopedOpenHousing', 'housing', mj_housing),
               ('RearMoldedBridge', 'cover', mj_rear),
               ('NonthreadedNickelBushing', 'bushing', mj_bushing),
               ('VisibleContactArch', 'contact', mj_arch),
               ('VisibleTipLeaf', 'contact', mj_leaf)]

# PJ bodyfrontY0 and rearY-14.4 follow the pre-existing canonical datum.
# Printedwidth9, height11, frontshoulder3.5, axis6.5 and bore6.5 govern.
pj_front = box(9, 3.5, 11, y=-3.5)
pj_round = fuse([box(9, 10.2, 6.5, y=-13.7),
                 cy(4.5, 10.2, -13.7, 6.5)])
pj_housing = fuse([pj_front, pj_round])
pj_housing = cut(pj_housing, cy(3.25, 9.1, .05, 6.5, -1))
for x in [-3.15, 1.65]:
    # Printedtopview depicts twin rim slots; dimensions1.5/1.0 require a
    # source/canonical view interpretation, so their exact placement is an
    # illustrative exterior detail, not a mechanical datum.
    pj_housing = cut(pj_housing, box(1.5, 1.0, 1.5,
                                      x=x, y=-2.5, z=9.5))
pj_cover = fuse([box(9, .7, 6.5, y=-14.4),
                 cy(4.5, .7, -14.4, 6.5)])
# Rearcover's stepped retention profile remains within the published envelope.
pj_cover = cut(pj_cover, box(1.6, .8, 2.3, x=-4.5, y=-14.45, z=6.5))
pj_cover = cut(pj_cover, box(1.6, .8, 2.3, x=2.9, y=-14.45, z=6.5))
pj_cover = cut(pj_cover, cy(.75, .9, -14.5, 3.0))
# Nominal2mm full diameter,9mm insertion cavity; rounded pin nose is an
# illustration within that diameter. This mating contact is not a PCB lead.
pj_pin = fuse([cy(1.0, 6.9, -8.9, 6.5),
               Part.makeSphere(1.0, V(0, -2.0, 6.5))])
pj_ring = cut(cy(3.19, .32, -2.10, 6.5),
              cy(2.86, .52, -2.2, 6.5))
# Lower spring occupies only the bore/cavity; no below-seat terminals.
pj_leaf = yz_prism([(-7.4, 3.4), (-6.5, 3.6), (-5.3, 4.18),
                    (-4.3, 3.75), (-4.2, 3.95), (-5.3, 4.43),
                    (-6.6, 3.84), (-7.4, 3.64)], -.8, 1.6)
pj_segments = [('RoundedMoldedHousing', 'housing', pj_housing),
               ('SteppedRearCover', 'cover', pj_cover),
               ('TwoMillimetreMatingPin', 'contact', pj_pin),
               ('RecessedMatingContactRing', 'contact', pj_ring),
               ('VisibleLowerLeaf', 'contact', pj_leaf)]

COMMON = [
    'Original independent parameterized reconstruction from primary manufacturer drawings, not redistributed manufacturer CAD.',
    'Published nominal envelopes/apertures retained at unity scale. Original canonical front/body-seat datum, offset0, rotation0 and native footprint pose are preserved.',
    'Below-seat terminals, solder lugs and locators are omitted. These candidates do not demonstrate PCB lead fit or installed seating.',
    'Roof slopes, recess/slot positions, cover seams, contact-arch/leaf/ring shapes and stock gauges are unsized visual interpretations within the printed envelopes; no tolerance or electrical-contact qualification.',
    'Exact historical supplied revision, mold, plating and physical fit remain unverified. Contemporary datasheets are references for a family illustration.',
]
groups = [dict(
    id='MJ3536N_DrawingDerived_DetailedBody', footprint='MJ-3536N',
    references=['CV0', 'GATE0'], segments=mj_segments,
    canonical_frame='Original F.Cu footprint X,-Y,Z outward, mm. FrontY0, bodyinto+Y, axisZ5.5.',
    source_urls=['https://www.sameskydevices.com/product/resource/mj-3536n.pdf',
                 'https://static.chipdip.ru/lib/247/DOC011247072.pdf',
                 'https://www.mouser.com/datasheet/2/670/mj-3536n-1311426.pdf',
                 'https://ladyada.net/make/x0xb0x/fab/parts.html'],
    dimensions=dict(body_width_mm=10, body_depth_mm=15.8, body_height_mm=10,
                    bushing_diameter_mm=6, bushing_projection_mm=3,
                    bore_diameter_mm=3.6, socket_axis_z_mm=5.5),
    expected_bounds=[-5, -3, 0, 5, 15.8, 10],
    improvements=['Sloping side rails and open recessed center replace flat solid box.',
                  'Full nonthreaded nickel bushing with restrained front molding detail.',
                  'Separate molded bridge and visible arch/leaf contacts inside top window.'],
    limitations=COMMON + [
        '2010 revisionB and2020 revision1.02 dimension-lines imply nominal terminal positions(0,2.3),(0,16),(5.2,13.5), consistent with the current drawing; 11.2 is terminal1-to-terminal3, not terminal1-to-terminal2.',
        'The source records reengineering in2023 and2024. Equal printed nominal dimensions do not prove unchanged mold or terminal tolerances.',
        'Original PCB rounddrills2.54 and slightly displaced center positions differ from manufacturer slotted-hole recommendations; no leads were narrowed or shifted to fit.',
        'No nut or thread is added: MJ-3536N is the nonthreaded6mm-bushing family, distinct from threaded sibling variants.',
        'Roof height7.5, slope breakpoints2.3/10.0, recessed window7.1wide, contactstock0.27/0.30 and14.1mm internal bore depth are visual assumptions, not manufacturer callouts.'
    ]), dict(
    id='PJ202AH_DrawingDerived_DetailedBody', footprint='PJ-202AH',
    references=['POWER0'], segments=pj_segments,
    canonical_frame='Original F.Cu footprint X,-Y,Z outward, mm. FrontY0, bodyinto-Y, axisZ6.5. Root applies actual POWER0 angle180.',
    source_urls=['https://www.sameskydevices.com/product/resource/pj-202ah.pdf',
                 'https://datasheet.octopart.com/PJ-202AH-CUI-datasheet-62089902.pdf',
                 'https://ladyada.net/make/x0xb0x/fab/parts.html'],
    dimensions=dict(body_width_mm=9, body_depth_mm=14.4, body_height_mm=11,
                    front_shoulder_depth_mm=3.5, socket_axis_z_mm=6.5,
                    mating_pin_diameter_mm=2, bore_diameter_mm=6.5,
                    insertion_cavity_depth_mm=9),
    expected_bounds=[-4.5, -14.4, 0, 4.5, 0, 11],
    improvements=['Separate rounded housing and stepped rearcover with retention relief.',
                  'Top rim recesses follow manufacturer appearance.',
                  'Full2mm centerpin, recessed mating ring and visible cavity leaf replace isolated blunt pin.'],
    limitations=COMMON + [
        'The recovered2015 revision1.01 and current2025 revision1.05 retain printed9x14.4x11mm, axis6.5, bore6.5, pin2.0 and terminalspacing nominal dimensions; the current drawing adds finer views/tolerances.',
        'Nominal terminal3 width3.0 exceeds original P$3 rounddrill2.8 before considering gauge, forming or offset; manufacturer recommends a3.0x1.0 slot. Terminals are omitted rather than thinned.',
        'Rearcover thickness0.7, retention cutout dimensions, cavity ring0.32stock, rounded pin nose and spring dimensions are unsized illustration choices.',
        'OriginalPOWER0 placementangle180 is external to this canonical asset; no mirror, scale or boardtranslation is baked into the model.'
    ])]

checks = []
parts, assignments = [], []
for g in groups:
    doc = App.newDocument(g['id'])
    objs, features, palette = [], [], []
    for name, role, shape in g['segments']:
        check(g['id'] + ':' + name + ':valid-solid',
              shape.isValid() and shape.Volume > 0 and len(shape.Solids) == 1,
              volume_mm3=shape.Volume, faces=len(shape.Faces))
        mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=.025,
                                     AngularDeflection=.10, Relative=False)
        stl = HERE / (g['id'] + '--' + name + '.stl')
        mesh.write(str(stl))
        check(g['id'] + ':' + name + ':closedmesh', mesh.isSolid(),
              facets=mesh.CountFacets)
        o = doc.addObject('PartDesign::Feature', name)
        o.Shape = shape
        objs.append(o)
        features.append(dict(name=name, role=role, stl=str(stl), units='mm',
                             color_rgb=COLORS[role], rgba=COLORS[role]+[1],
                             exact_bounds_mm=bounds(shape), volume_mm3=shape.Volume,
                             sha256=sha(stl), triangles=mesh.CountFacets))
        palette.extend([COLORS[role]] * len(shape.Solids))
    combined = Part.makeCompound([o.Shape for o in objs])
    b = bounds(combined)
    check(g['id'] + ':nominal-bounds',
          max(abs(a-c) for a, c in zip(b, g['expected_bounds'])) < 2e-6,
          actual_mm=b, expected_mm=g['expected_bounds'])
    step = HERE / (g['id'] + '.step')
    doc.recompute()
    Part.export(objs, str(step))
    plain = Part.Shape()
    plain.read(str(step))
    color_roles = face_colors(step, palette)
    restored = Part.Shape()
    restored.read(str(step))
    check(g['id'] + ':STEP-roundtrip', restored.isValid() and
          len(restored.Solids) == len(combined.Solids) and
          abs(restored.Volume-combined.Volume) < 1e-5,
          solids=len(restored.Solids), volume_mm3=restored.Volume)
    check(g['id'] + ':colors-only',
          plain.exportBrepToString() == restored.exportBrepToString())
    stl = HERE / (g['id'] + '.stl')
    # STEP preserves separate material solids. The single STL represents their
    # exterior union, so coincident contact/material boundaries cannot create
    # duplicate internal triangle sheets in that monochrome interchange file.
    exterior = fuse([o.Shape for o in objs])
    mesh = MeshPart.meshFromShape(Shape=exterior, LinearDeflection=.025,
                                 AngularDeflection=.10, Relative=False)
    mesh.write(str(stl))
    check(g['id'] + ':combined-closedmesh', mesh.isSolid())
    doc.saveAs(str(HERE / (g['id'] + '.FCStd')))
    App.closeDocument(doc.Name)
    row = {k: v for k, v in g.items() if k not in ['segments', 'expected_bounds']}
    row.update(board='ioboard', step=str(step), source_model=str(step),
               source_sha256=sha(step), stl=str(stl), stl_sha256=sha(stl),
               units='mm', features=features, mesh_parts=features,
               exact_bounds_mm=b, valid=True, solid_count=len(restored.Solids),
               faces=len(restored.Faces), volume_mm3=restored.Volume,
               color_roles=color_roles, triangles=mesh.CountFacets,
               combined_stl_representation='Exterior boolean union of material solids; per-feature STLs and colored STEP retain separate materials',
               offset_mm=[0, 0, 0], rotation_deg=[0, 0, 0], scale=[1, 1, 1],
               classification='Detailed exact-family drawing-derived body/contact illustration; below-seat terminals omitted, installed fit unqualified',
               source_kind='Independent parameterized reconstruction from original/current manufacturer drawings; explicitly unsized appearance details')
    parts.append(row)
    assignments.append({k: row[k] for k in [
        'board', 'references', 'footprint', 'source_model', 'source_sha256',
        'offset_mm', 'rotation_deg', 'scale', 'classification', 'source_kind',
        'source_urls', 'limitations', 'canonical_frame', 'units']})

check('source-PCBs-unchanged', guards == {p: sha(p) for p in guards})
sources = []
for p in sorted((HERE / 'sources').glob('*')):
    if p.suffix in ['.pdf', '.html']:
        sources.append(dict(filename=str(p.relative_to(HERE)),
                            sha256=sha(p), bytes=p.stat().st_size))
manifest = dict(date='2026-10-14', scope='Two families,3reference instances; candidate only, no project or scene edits',
                parts=parts, assignments=assignments, instance_count=3,
                body_only=True, physical_fit_qualified=False,
                geometry_license='CC0-1.0 applies to original reconstruction geometry/scripts only; manufacturer drawings/branding retain respective rights.',
                manufacturer_CAD_incorporated=False,
                manufacturer_CAD_zip_distribution='Exclude sources/Same_Sky_MJ-3536N.zip from all delivery archives; no express redistribution grant found and no CAD data was read or incorporated.',
                source_project_hashes=guards, source_projects_unchanged=True,
                sources=sources)
(HERE / 'rear-connector-quality-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
(HERE / 'rear-connector-quality-review.json').write_text(json.dumps(dict(
    passed=all(c['passed'] for c in checks), checks_count=len(checks), checks=checks,
    source_projects_unchanged=True, assigned_transforms_unchanged=True,
    manufacturer_CAD_incorporated=False), indent=2)+'\n')
print(json.dumps(dict(passed=True, families=2, references=3,
                     checks=len(checks), model_hashes={p['id']:p['source_sha256'] for p in parts}), indent=2))
