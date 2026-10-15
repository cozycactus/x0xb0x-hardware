"""Install the Xicon XRL electrolytic models; preserve every PCB, pad and model transform.

36 placements get datasheet-sized XRL bodies (29 mainboard E5-6, C43 on E5-5, six
ioboard E5-6 of which C7/C8 take the 6.3 x 11 mm body as an instance override), and
C17, C3 and C5 switch to recoloured copies of their revision-5 XRL models. Only model
path strings change; every other PCB and footprint node, and every model transform,
is checked identical.

Run from the repository root:
  python3 -I kicad-working/validation/models-review-21/install_electrolytic_models.py
"""
import copy
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parents[1]
R = W.parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
sys.dont_write_bytecode = True
sys.path.insert(0, str(R / 'kicad-import/validation'))
from verify_native_projects import parse_sexpr  # noqa: E402

Q = H / 'electrolytic-quality'
audit = json.loads((Q / 'electrolytic-model-audit.json').read_text())
assert audit['passed']
M = audit['models']
for v in M.values():
    assert sha(Q / v['output']) == v['output_sha256']
for name, v in audit['recoloured'].items():
    assert sha(Q / name) == v['output_sha256']
P = '${KIPRJMOD}/3dmodels/'
OLD_D5 = P + 'KiCad/Capacitor_THT.3dshapes/CP_Radial_D5.0mm_P2.50mm.step'
OLD_D10 = P + 'KiCad/Capacitor_THT.3dshapes/CP_Radial_D10.0mm_P5.00mm.step'
OLD_C17 = P + 'Revision5/passive-models/CP_Xicon_XRL1u50_P3.556_Illustration.step'
OLD_C3 = P + 'Revision5/passive-models/CP_Xicon_XRL2200u16_P5.08_Illustration.step'
LOCAL = 'Revision21/electrolytic-quality/'
D5, D63, D10 = (LOCAL + M[k]['output'] for k in ('XRL_D5', 'XRL_D6.3', 'XRL_D10'))
C17 = LOCAL + 'CP_Xicon_XRL1u50_P3.556_PhotoColours.step'
C3 = LOCAL + 'CP_Xicon_XRL2200u16_P5.08_PhotoColours.step'
ASSETS = {'mainboard': [M['XRL_D5']['output'], M['XRL_D10']['output'], Path(C17).name],
          'ioboard': [M['XRL_D5']['output'], M['XRL_D6.3']['output'], Path(C3).name]}
new_files = []
for board, names in ASSETS.items():
    for name in names:
        dest = W / board / '3dmodels' / LOCAL / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Q / name, dest)
        assert sha(dest) == sha(Q / name)
        new_files.append(f'{board}/3dmodels/{LOCAL}{name}')

# (file, {reference or '*': (old, new)}, expected replacements). '*' applies to every model node not named.
EDITS = [
    ('mainboard/mainboard.kicad_pcb', {'*': [(OLD_D5, P + D5), (OLD_D10, P + D10), (OLD_C17, P + C17)]}, 31),
    ('mainboard/mainboard-import-fps.pretty/E5-6.kicad_mod', {'*': [(OLD_D5, P + D5)]}, 1),
    ('mainboard/mainboard-import-fps.pretty/E5-5.kicad_mod', {'*': [(OLD_D10, P + D10)]}, 1),
    ('mainboard/mainboard-import-fps.pretty/E3,5-8.kicad_mod', {'*': [(OLD_C17, P + C17)]}, 1),
    ('ioboard/ioboard.kicad_pcb', {'C7': [(OLD_D5, P + D63)], 'C8': [(OLD_D5, P + D63)],
                                   '*': [(OLD_D5, P + D5), (OLD_C3, P + C3)]}, 8),
    ('ioboard/ioboard-import-fps.pretty/E5-6.kicad_mod', {'*': [(OLD_D5, P + D5)]}, 1),
    ('ioboard/ioboard-import-fps.pretty/E5-13.kicad_mod', {'*': [(OLD_C3, P + C3)]}, 1),
]


def nonmodels(node):
    if not isinstance(node, list):
        return node
    return [nonmodels(x) for x in node if not (isinstance(x, list) and x and x[0] == 'model')]


def transforms(node):
    if not isinstance(node, list):
        return []
    if node and node[0] == 'model':
        return [node[2:]]
    return [t for x in node for t in transforms(x)]


def parse(s):
    return parse_sexpr(s if s.lstrip().startswith('(kicad_pcb') else '(kicad_pcb ' + s + ')')


def apply(text, rules):
    """Replace model paths footprint by footprint so instance overrides go to the named references."""
    pieces = re.split(r'(?=\n\t\(footprint )', text) if text.lstrip().startswith('(kicad_pcb') else [text]
    count, out = 0, []
    for piece in pieces:
        ref = re.search(r'\(property "Reference" "([^"]*)"', piece)
        pairs = rules.get(ref.group(1) if ref else None, rules['*'])
        for old, new in pairs:
            n = piece.count(f'(model "{old}"')
            piece = piece.replace(f'(model "{old}"', f'(model "{new}"')
            count += n
        out.append(piece)
    return ''.join(out), count


files = []
for relative, rules, expected in EDITS:
    p = W / relative
    snapshot = H / 'input-snapshot' / relative
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        snapshot.write_bytes(p.read_bytes())
    before = snapshot.read_text()
    after, count = apply(before, rules)
    assert count == expected, (relative, count)
    assert p.read_text() in (before, after)
    assert nonmodels(parse(before)) == nonmodels(parse(after))
    assert transforms(parse(before)) == transforms(parse(after))
    p.write_text(after)
    files.append(dict(file=relative, before_sha256=sha(snapshot), after_sha256=sha(p), model_nodes_only=True,
                      replaced_model_path_count=count, non_model_nodes_identical=True, model_transforms_identical=True))

plan = json.loads((W / 'validation/models-review-20/combined-model-plan.json').read_text())
rows = plan['assignments']


def row_for(board, footprint):
    found = [a for a in rows if a['board'] == board and a['footprint'] == footprint]
    assert len(found) == 1, (board, footprint)
    return found[0]


EVIDENCE = json.loads((Q / 'sources/electrolytic-evidence.json').read_text())
COLOURS = EVIDENCE['kit_photos']['chosen_colours']
SOURCES = [EVIDENCE['bom']['parts_page']['url'], EVIDENCE['bom']['expanded_bom']['url'],
           EVIDENCE['datasheet']['also_cited_by_revision_5'], EVIDENCE['datasheet']['retrieved_from']]
LIMITS = audit['limitations']
updated = []


def install(row, key, local, refs=None):
    m = M[key]
    asset = W / row['board'] / '3dmodels' / local
    row.update(previous_local_model=row['local_model'], previous_source_sha256=row['source_sha256'],
               source_model=str(asset), source_sha256=sha(asset), local_model=local,
               source_kind='Original CC0 illustration from the Xicon XRL datasheet XC-600178 (1/8/07) and kit photographs',
               classification='Xicon XRL documented-family illustration at the exact board pitch',
               limitations=LIMITS, review_manifest='validation/models-review-21/electrolytic-quality/electrolytic-model-audit.json',
               source_urls=SOURCES, part=m['parts'], model_nominal_dimensions_mm=m['dimensions_mm'], model_frame=m['model_frame'],
               solid_count=5, part_ids=['Sleeve', 'NegativeStripe', 'TopMetal', 'Lead_Positive', 'Lead_Negative'],
               polarity_mapping={'positive_lead': '+', 'negative_stripe_and_lead': '-'})
    row.pop('review', None)
    if refs is not None:
        row['references'] = refs
    updated.append(copy.deepcopy(row))


install(row_for('mainboard', 'E5-6'), 'XRL_D5', D5)
install(row_for('mainboard', 'E5-5'), 'XRL_D10', D10)
io = row_for('ioboard', 'E5-6')
assert sorted(io['references']) == ['C203', 'C205', 'C60', 'C61', 'C7', 'C8']
split = copy.deepcopy(io)
install(io, 'XRL_D5', D5, refs=['C203', 'C205', 'C60', 'C61'])
install(split, 'XRL_D6.3', D63, refs=['C7', 'C8'])
rows.insert(rows.index(io) + 1, split)
for board, footprint, local, name in (('mainboard', 'E3,5-8', C17, Path(C17).name), ('ioboard', 'E5-13', C3, Path(C3).name)):
    row = row_for(board, footprint)
    asset = W / board / '3dmodels' / local
    row.update(previous_local_model=row['local_model'], previous_source_sha256=row['source_sha256'], source_model=str(asset),
               source_sha256=sha(asset), local_model=local,
               colour_revision=dict(revision=21, sleeve_srgb=COLOURS['sleeve_srgb'], negative_stripe_srgb=COLOURS['negative_stripe_srgb'],
                                    note='Sleeve and negative stripe recoloured from the kit photographs; B-rep byte-identical to revision 5',
                                    review_manifest='validation/models-review-21/electrolytic-quality/electrolytic-model-audit.json'))
    updated.append(copy.deepcopy(row))
assert sum(len(a['references']) for a in rows) == plan['assigned_instance_count'] == 491
policies = plan['cache_policies']
assert not any(c['board'] == 'ioboard' and c['footprint'] == 'E5-6' for c in policies)
policies.append(dict(board='ioboard', footprint='E5-6', references=['C203', 'C205', 'C60', 'C61', 'C7', 'C8'],
                     cache_model_added=False,
                     reason='Footprint cache keeps its existing model node, now the 5 x 11 mm XRL body used by C60, C61, C203 '
                            'and C205; C7 and C8 carry part-specific 6.3 x 11 mm instance overrides (100uF 25V).'))
sources_files = []
for board in ('mainboard', 'ioboard'):
    record = dict(revision=21, baseline_revision=20,
                  models={n: dict(local_model=LOCAL + n, sha256=sha(W / board / '3dmodels' / LOCAL / n)) for n in ASSETS[board]},
                  references={a['local_model'].split('/')[-1]: a['references'] for a in updated if a['board'] == board},
                  datasheet=audit['source'], evidence='validation/models-review-21/electrolytic-quality/sources/electrolytic-evidence.json',
                  limitations=LIMITS, physical_fit_qualified=False)
    path = W / board / '3dmodels/REVISION-21-SOURCES.json'
    path.write_text(json.dumps(record, indent=2) + '\n')
    sources_files.append(f'{board}/3dmodels/REVISION-21-SOURCES.json')
new_files += sources_files
plan.update(base_revision=20, updated_assignments=updated, new_assignments=[], updated_instance_count=39, new_instance_count=0,
            files=files, new_files=new_files, model_transform_exceptions=[],
            review_manifests=['validation/models-review-21/electrolytic-quality/electrolytic-model-audit.json'],
            scope='36 electrolytic placements get Xicon XRL datasheet bodies at the exact 2.54/5.08 mm pitch; C17, C3 and C5 '
                  'keep their revision-5 XRL geometry with photo-sampled sleeve colours. Original PCB/model transforms preserved.')
(H / 'combined-model-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
prior = json.loads((W / 'validation/working-validation-summary-revision-20.json').read_text())
changed = sorted(n for n, h in prior['outputs'].items() if sha(W / n) != h)
assert changed == sorted(f['file'] for f in files), changed
references = {a['board'] + ':' + a['local_model'].split('/')[-1]: sorted(a['references']) for a in updated}
report = dict(passed=True, files=files, previous_core_file_count=len(prior['outputs']), changed_previous_core_files=changed,
              new_core_files=new_files, component_references_updated=sum(len(v) for v in references.values()),
              references=references, total_fitted_model_references=491,
              copper_pads_nets_footprint_poses_schematics_and_project_rules_unchanged=True, model_transforms_unchanged=True,
              source_Eagle_files_unchanged=True, old_STEP_preserved=True, physical_fit_qualified=False)
assert report['component_references_updated'] == 39
(H / 'installation-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': True, 'updated_references': 39, 'changed_files': changed, 'new_files': len(new_files)}, indent=2))
