"""Colour the TL1100F terminal legs as metal; geometry unchanged.

The publisher STEP is one grey solid. Revision 8 coloured faces by position and gave
the terminal colour only to faces lying wholly below the seat, so the leg faces that
leave the 12 x 12 mm housing and rise up to 1.45 mm above the board were coloured as
black housing. This script re-points only those faces' STYLED_ITEM entries to the
existing terminal style: a face becomes terminal metal if it lies wholly below the seat
or any part of it lies outside the housing outline (|x| or |y| > 6.0 mm). Every other
STEP entity, and therefore the B-rep, is byte-for-byte unchanged.

Run with FreeCAD's Python from the repository root:
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
      kicad-working/validation/models-review-17/tl1100-colour/recolour_tl1100.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App  # noqa: E402,F401
import Part  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
SOURCE = WORK / 'mainboard/3dmodels/Revision8/control-quality/TL1100F_ManufacturerCAD_FullNominalFreeState.step'
OUT = WORK / 'mainboard/3dmodels/Revision17/control-quality/TL1100F_ManufacturerCAD_FullNominalFreeState_MetalLegs.step'
HOUSING_HALF = 6.0
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731

text = SOURCE.read_text()
ent = {int(n): body for n, body in re.findall(r'#(\d+)\s*=\s*(.*?);', text, re.S)}
breps = [i for i, b in ent.items() if b.startswith('MANIFOLD_SOLID_BREP')]
assert len(breps) == 1
shell = int(re.findall(r'#(\d+)', ent[breps[0]])[0])
face_ids = list(map(int, re.findall(r'#(\d+)', ent[shell])))
shape = Part.Shape()
shape.read(str(SOURCE))
assert len(shape.Solids) == 1 and len(shape.Faces) == len(face_ids)

styled = {}
for i, b in ent.items():
    m = re.match(r"STYLED_ITEM\('(\w+)',\(#(\d+)\),#(\d+)\)", b.replace(' ', ''))
    if m:
        styled[int(m.group(3))] = (i, m.group(1), int(m.group(2)))
assert set(styled) == set(face_ids)
terminal_style = {s for _, (_, role, s) in styled.items() if role == 'terminals'}
assert len(terminal_style) == 1
terminal_style = terminal_style.pop()

# The face order in the shell is FreeCAD's face order (revision 8 coloured by the same pairing);
# confirm it on the faces already coloured as terminals: each must lie wholly below the seat.
for fid, face in zip(face_ids, shape.Faces):
    if styled[fid][1] == 'terminals':
        assert face.BoundBox.ZMax < 1e-7, 'shell/face order mismatch'

changes = []
new_text = text
for fid, face in zip(face_ids, shape.Faces):
    b = face.BoundBox
    outside = max(abs(b.XMin), abs(b.XMax), abs(b.YMin), abs(b.YMax)) > HOUSING_HALF + 1e-6
    item, role, style = styled[fid]
    if outside and role != 'terminals':
        old = re.search(rf'#{item}\s*=\s*STYLED_ITEM\(.*?\);', new_text, re.S).group(0)
        new = old.replace(f"STYLED_ITEM('{role}'", "STYLED_ITEM('terminals'").replace(f'(#{style})', f'(#{terminal_style})')
        assert new != old
        new_text = new_text.replace(old, new, 1)
        changes.append(dict(face=fid, previous_role=role, z_range_mm=[round(b.ZMin, 3), round(b.ZMax, 3)],
                            x_range_mm=[round(b.XMin, 3), round(b.XMax, 3)]))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(new_text)

checks = []


def check(name, ok, **detail):
    checks.append(dict(check=name, passed=bool(ok), **detail))


new_ent = {int(n): body for n, body in re.findall(r'#(\d+)\s*=\s*(.*?);', new_text, re.S)}
differing = sorted(i for i in ent if ent[i] != new_ent.get(i))
check('Only STYLED_ITEM entities differ; same entity set', set(ent) == set(new_ent)
      and all(ent[i].startswith('STYLED_ITEM') for i in differing), changed_entities=len(differing))
back = Part.Shape()
back.read(str(OUT))
check('Reloaded B-rep is identical to the revision-8 model',
      back.isValid() and back.exportBrepToString() == shape.exportBrepToString())
check('All recoloured faces lie outside the housing and reach above the seat',
      all(c['z_range_mm'][1] > 0 for c in changes) and len(changes) == 24, recoloured=len(changes))
roles = {}
for b in new_ent.values():
    m = re.match(r"STYLED_ITEM\('(\w+)'", b)
    if m:
        roles[m.group(1)] = roles.get(m.group(1), 0) + 1
check('Role counts move exactly 24 faces from housing to terminals',
      roles == {'actuator': 17, 'cover': 6, 'housing': 162 - 24, 'terminals': 64 + 24}, roles=roles)
report = dict(schema=1, revision=17, generator='recolour_tl1100.py', passed=all(c['passed'] for c in checks),
              check_count=len(checks), checks=checks, source=str(SOURCE.relative_to(WORK)), source_sha256=sha(SOURCE),
              output=str(OUT.relative_to(WORK)), output_sha256=sha(OUT), recoloured_faces=changes,
              rule='Terminal metal if wholly below the seat (revision 8) or any part outside the 12 x 12 mm housing outline',
              geometry_changed=False, physical_fit_qualified=False)
(HERE / 'tl1100-colour-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'check_count')}), roles)
for c in checks:
    if not c['passed']:
        print('FAIL', c)
assert report['passed']
