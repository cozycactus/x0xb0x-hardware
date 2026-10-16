"""Printed part markings on the 17 IC models, transcribed from the original kit photographs.

Each output STEP is the current model of the chip (the installed KiCad DIP/LQFP STEP, or
the revision-23 socketed IC3/IC2 model) with its solids and face colours unchanged, plus
raised marking text: Source Code Pro Medium glyphs, 0.03 mm proud of the flat chip top,
light-grey ink. DIP text reads from the notch end with the pin-1 row at the bottom; the
ATmega162 text runs across the body as photographed; the FT232BM text reads with its
pin-1 dimple at the top left. Model frames and PCB transforms stay unchanged.

Run with FreeCAD's Python from the repository root:
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
      kicad-working/validation/models-review-24/marking-quality/build_markings.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
V = App.Vector
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
EVIDENCE = json.loads((HERE / 'sources/marking-evidence.json').read_text())
FONT = EVIDENCE['font']['file']
assert sha(FONT) == EVIDENCE['font']['sha256']
INK = (0.75, 0.75, 0.72)
RAISE = 0.03
KD = 'KiCad/Package_DIP.3dshapes/'
SPECS = {   # key: (board holding the source, source model relative to <board>/3dmodels, frame, cap height mm)
    '74HC595': ('mainboard', KD + 'DIP-16_W7.62mm.step', 'dip', 1.0),
    '74AC174': ('mainboard', KD + 'DIP-16_W7.62mm.step', 'dip', 1.0),
    '74HC165': ('mainboard', KD + 'DIP-16_W7.62mm.step', 'dip', 1.0),
    '74HC126': ('mainboard', KD + 'DIP-14_W7.62mm.step', 'dip', 1.0),
    '4066': ('mainboard', KD + 'DIP-14_W7.62mm.step', 'dip', 1.0),
    'AN6562': ('mainboard', KD + 'DIP-8_W7.62mm.step', 'dip', 0.9),
    'ATmega162': ('mainboard', 'Revision23/socket-quality/DIP-40_W15.24mm_in_1-390262-5_Socket_KiCadFrame.step', 'across', 1.0),
    'EEPROM': ('mainboard', 'Revision23/socket-quality/DIP-8_W7.62mm_in_1-390261-2_Socket_KiCadFrame.step', 'dip', 0.9),
    '4N37': ('ioboard', KD + 'DIP-6_W7.62mm.step', 'dip', 0.9),
    'FT232BM': ('ioboard', 'KiCad/Package_QFP.3dshapes/LQFP-32_7x7mm_P0.8mm.step', 'qfp', 0.75),
}
FRAMES = {'dip': (V(0, -1, 0), V(1, 0, 0)), 'across': (V(1, 0, 0), V(0, 1, 0)), 'qfp': (V(1, 0, 0), V(0, 1, 0))}
checks = []


def check(name, ok, **detail):
    checks.append(dict(check=name, passed=bool(ok), **detail))
    if not ok:
        print('FAIL', json.dumps(checks[-1]), flush=True)


def entities(text):
    return {int(n): b for n, b in re.findall(r'#(\d+)\s*=\s*(.*?);', text, re.S)}


def solid_face_colours(path):
    """Per solid (file order), the colour of every face in shell order."""
    ent = entities(Path(path).read_text())
    styled = {}
    for b in ent.values():
        m = re.match(r"STYLED_ITEM\('[^']*',\(#(\d+)\),#(\d+)\)", b.replace(' ', ''))
        if m:
            styled[int(m.group(2))] = int(m.group(1))
    out = []
    for n in sorted(n for n, b in ent.items() if b.startswith('MANIFOLD_SOLID_BREP')):
        shell = int(re.findall(r'#(\d+)', ent[n])[0])
        colours = []
        for f in map(int, re.findall(r'#(\d+)', ent[shell])):
            c = int(re.findall(r'#(\d+)', ent[styled[f]])[0])
            while not ent[c].startswith('COLOUR_RGB'):
                c = int(re.findall(r'#(\d+)', ent[c])[-1])
            colours.append(tuple(round(float(v), 6) for v in ent[c].rstrip(')').split(',')[1:]))
        out.append(colours)
    return out


SOCKET_BUILDER = WORK / 'validation/models-review-23/socket-quality/build_sockets.py'
src = SOCKET_BUILDER.read_text()
exec(compile(src[src.index('def add_face_styles'):src.index('def sections')], str(SOCKET_BUILDER), 'exec'))


def glyph_line(text, size):
    faces = [Part.makeFace(ws, 'Part::FaceMakerBullseye') for ws in Part.makeWireString(text, FONT, size, 0) if ws]
    return faces


ratio = Part.makeCompound(glyph_line('M', 10.0)).BoundBox.YLength / 10.0      # cap height per unit size
models = {}
for key, (board, source, frame, cap) in SPECS.items():
    path = WORK / board / '3dmodels' / source
    shape = Part.Shape()
    shape.read(str(path))
    colours = solid_face_colours(path)
    solids = list(shape.Solids)
    check(f'{key}: source solids and face colours read in file order', len(solids) == len(colours) and
          all(len(s.Faces) == len(c) for s, c in zip(solids, colours)), solids=len(solids))
    zt = max(f.BoundBox.ZMax for f in shape.Faces)
    top = max((f for f in shape.Faces if abs(f.BoundBox.ZMax - zt) < 1e-6 and f.BoundBox.ZLength < 1e-6), key=lambda f: f.Area)
    tb = top.BoundBox
    lines = EVIDENCE['markings'][key]['lines']
    size = cap / ratio
    pitch = cap * 1.6
    reading, up = FRAMES[frame]
    # Fit: the block must stay 0.6 mm inside the top face and 1.2 mm clear of each end along the reading axis.
    along = tb.XLength if abs(reading.x) > .5 else tb.YLength
    across = tb.YLength if abs(reading.x) > .5 else tb.XLength
    widths = [Part.makeCompound(glyph_line(t, size)).BoundBox.XLength for t in lines]
    scale = min(1.0, (along - 2.4) / max(widths), (across - 1.2) / (cap + pitch * (len(lines) - 1)))
    size, cap, pitch = size * scale, cap * scale, pitch * scale
    glyphs = []
    for i, text in enumerate(lines):
        faces = glyph_line(text, size)
        lb = Part.makeCompound(faces).BoundBox
        for f in faces:
            f.translate(V(-lb.XLength / 2 - lb.XMin, -i * pitch, 0))
            glyphs.append((i, f))
    block = Part.makeCompound([f for _, f in glyphs]).BoundBox
    centre = V((tb.XMin + tb.XMax) / 2, (tb.YMin + tb.YMax) / 2, zt)
    mats = App.Matrix(reading.x, up.x, 0, 0, reading.y, up.y, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
    marks = []
    for i, f in glyphs:
        f.translate(V(0, -(block.YMin + block.YMax) / 2, 0))
        f = f.transformGeometry(mats)
        f.translate(centre)
        marks.append((i, f.extrude(V(0, 0, RAISE))))
    text_solids = [s for _, m in marks for s in m.Solids]
    check(f'{key}: every glyph is a valid solid on the chip top', all(s.isValid() for s in text_solids) and
          all(abs(s.BoundBox.ZMin - zt) < 1e-6 and abs(s.BoundBox.ZMax - zt - RAISE) < 1e-6 for s in text_solids), glyph_solids=len(text_solids))
    mb = Part.makeCompound(text_solids).BoundBox
    inside = (mb.XMin >= tb.XMin + 0.6 - 1e-6 and mb.XMax <= tb.XMax - 0.6 + 1e-6 and mb.YMin >= tb.YMin + 0.6 - 1e-6 and mb.YMax <= tb.YMax - 0.6 + 1e-6)
    check(f'{key}: marking block lies inside the top face with margin', inside, block=[round(v, 3) for v in (mb.XMin, mb.XMax, mb.YMin, mb.YMax)],
          top=[round(v, 3) for v in (tb.XMin, tb.XMax, tb.YMin, tb.YMax)])
    first = [m for i, m in marks if i == 0]
    proj = [(s.CenterOfMass - centre).dot(reading) for m in first for s in m.Solids]
    rows = [sum((s.CenterOfMass - centre).dot(up) for m in [mm for i, mm in marks if i == k] for s in m.Solids) /
            max(1, sum(len(mm.Solids) for i, mm in marks if i == k)) for k in range(len(lines))]
    check(f'{key}: text reads along the intended direction with line 1 on top', proj[0] < proj[-1] and all(a > b for a, b in zip(rows, rows[1:])))
    out = HERE / f'{Path(source).stem}_Marked_{key}.step'
    doc = App.newDocument('M' + hashlib.md5(key.encode()).hexdigest()[:8])
    objs = []
    names = []
    for k, s in enumerate(solids):
        o = doc.addObject('Part::Feature', f'Body{k + 1}')
        o.Shape = s
        objs.append(o)
        names.append(f'Body{k + 1}')
    for k, s in enumerate(text_solids):
        o = doc.addObject('Part::Feature', f'Marking{k + 1}')
        o.Shape = s
        objs.append(o)
        names.append(f'Marking{k + 1}')
    doc.recompute()
    Part.export(objs, str(out))
    App.closeDocument(doc.Name)
    back = Part.read(str(out))
    check(f'{key}: saved STEP keeps every solid, face count and volume in order', len(back.Solids) == len(solids) + len(text_solids) and
          all(len(a.Faces) == len(b.Faces) and abs(a.Volume - b.Volume) < 1e-6 for a, b in zip(back.Solids, solids + text_solids)))
    add_face_styles(out, colours + [[INK] * len(s.Faces) for s in text_solids], names)
    out.write_text('\n'.join(line.rstrip() for line in out.read_text().splitlines()) + '\n')
    check(f'{key}: chip and socket face colours carried over unchanged', solid_face_colours(out)[:len(colours)] == colours)
    models[key] = dict(output=out.name, output_sha256=sha(out), source=f'{board}/3dmodels/{source}', source_sha256=sha(path),
                       references=EVIDENCE['markings'][key]['refs'], lines=lines, cap_height_mm=round(cap, 3), frame=frame,
                       glyph_solids=len(text_solids), top_z_mm=round(zt, 3), ink=INK, raise_mm=RAISE)
report = dict(schema=1, revision=24, generator='build_markings.py', passed=all(c['passed'] for c in checks), check_count=len(checks),
              checks=checks, models=models, evidence=dict(file='sources/marking-evidence.json', sha256=sha(HERE / 'sources/marking-evidence.json')),
              limitations=['Marking text is transcribed from one set of kit photographs; date and lot codes varied between kits.',
                           'Logos are omitted; Source Code Pro approximates the vendors\' marking fonts; ink colour is illustrative.',
                           'The 74HC165 has no photograph and carries its part number only.',
                           'Chip and socket geometry, colours and transforms are unchanged; physical fit is unqualified.'],
              physical_fit_qualified=False)
(HERE / 'marking-model-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(passed=report['passed'], check_count=len(checks), models={k: (v['cap_height_mm'], v['glyph_solids']) for k, v in models.items()}), indent=2))
assert report['passed']
