"""Install the marked IC models; preserve every PCB node and model transform.

Each of the 17 marked ICs gets its marked model path. Footprint caches used by a single
placement (DIL40, DIL08_AT25 and DIL08 on the mainboard; DIL08, DIL06 and SQFP-S-7X7-32
on the I/O board) point to the same model; the shared DIL16/DIL14 caches keep their
unmarked KiCad body. Only model path strings change; every other node and every
transform is checked identical.

Run from the repository root:
  python3 -I kicad-working/validation/models-review-24/install_marking_models.py
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

Q = H / 'marking-quality'
audit = json.loads((Q / 'marking-model-audit.json').read_text())
assert audit['passed']
P = '${KIPRJMOD}/3dmodels/'
LOCAL = 'Revision24/marking-quality/'
new_files, by_ref = [], {}
for key, m in audit['models'].items():
    assert sha(Q / m['output']) == m['output_sha256']
    for board in sorted({r.split(':')[0] for r in m['references']}):
        dest = W / board / '3dmodels' / LOCAL / m['output']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Q / m['output'], dest)
        new_files.append(f'{board}/3dmodels/{LOCAL}{m["output"]}')
    for item in m['references']:
        by_ref[tuple(item.split(':'))] = (P + m['source'].split('/3dmodels/')[1], P + LOCAL + m['output'], key)
assert len(by_ref) == 17
CACHES = {('mainboard', 'DIL40'): 'IC3', ('mainboard', 'DIL08_AT25'): 'IC2', ('mainboard', 'DIL08'): 'IC11',
          ('ioboard', 'DIL08'): 'IC23', ('ioboard', 'DIL06'): 'IC24', ('ioboard', 'SQFP-S-7X7-32'): 'IC25'}


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


def write(relative, before, after, count):
    p = W / relative
    assert p.read_text() in (before, after)
    assert nonmodels(parse(before)) == nonmodels(parse(after)) and transforms(parse(before)) == transforms(parse(after))
    p.write_text(after)
    return dict(file=relative, before_sha256=sha(H / 'input-snapshot' / relative), after_sha256=sha(p), model_nodes_only=True,
                replaced_model_path_count=count, non_model_nodes_identical=True, model_transforms_identical=True)


def snapshot(relative):
    s = H / 'input-snapshot' / relative
    s.parent.mkdir(parents=True, exist_ok=True)
    if not s.exists():
        s.write_bytes((W / relative).read_bytes())
    return s.read_text()


files = []
for board in ('mainboard', 'ioboard'):
    relative = f'{board}/{board}.kicad_pcb'
    before = snapshot(relative)
    pieces, count = [], 0
    for piece in re.split(r'(?=\n\t\(footprint )', before):
        ref = re.search(r'\(property "Reference" "([^"]*)"', piece)
        if ref and (board, ref.group(1)) in by_ref:
            old, new, _ = by_ref[(board, ref.group(1))]
            assert piece.count(f'(model "{old}"') == 1, (board, ref.group(1))
            piece = piece.replace(f'(model "{old}"', f'(model "{new}"')
            count += 1
        pieces.append(piece)
    assert count == sum(1 for b, _ in by_ref if b == board)
    files.append(write(relative, before, ''.join(pieces), count))
for (board, fp), ref in sorted(CACHES.items()):
    relative = f'{board}/{board}-import-fps.pretty/{fp}.kicad_mod'
    before = snapshot(relative)
    old, new, _ = by_ref[(board, ref)]
    assert before.count(f'(model "{old}"') == 1, relative
    files.append(write(relative, before, before.replace(f'(model "{old}"', f'(model "{new}"'), 1))

plan = json.loads((W / 'validation/models-review-23/combined-model-plan.json').read_text())
rows, updated = plan['assignments'], []
for old in [a for a in rows if any((a['board'], r) in by_ref for r in a['references'])]:
    index = rows.index(old)
    rows.remove(old)
    groups = {}
    for r in old['references']:
        groups.setdefault(by_ref[(old['board'], r)][1] if (old['board'], r) in by_ref else None, []).append(r)
    for offset, (path, refs) in enumerate(sorted(groups.items(), key=lambda kv: kv[0] or '')):
        row = copy.deepcopy(old)
        row['references'] = sorted(refs)
        if path is not None:
            local = path[len(P):]
            key = by_ref[(old['board'], refs[0])][2]
            row.update(previous_local_model=old['local_model'], previous_source_sha256=old['source_sha256'],
                       source_model=str(W / old['board'] / '3dmodels' / local), source_sha256=sha(W / old['board'] / '3dmodels' / local),
                       local_model=local, marking_lines=audit['models'][key]['lines'],
                       marking_review='validation/models-review-24/marking-quality/marking-model-audit.json',
                       limitations=(old['limitations'] if isinstance(old['limitations'], list) else [old['limitations']]) + audit['limitations'])
            updated.append(copy.deepcopy(row))
        rows.insert(index + offset, row)
assert sum(len(a['references']) for a in rows) == plan['assigned_instance_count'] == 491
touched = {('mainboard', 'DIL16'), ('mainboard', 'DIL14')} | set(CACHES)
policies = [c for c in plan['cache_policies'] if (c['board'], c['footprint']) not in touched]
plan['cache_policies'] = policies
SHARED = {'DIL16': ['IC16', 'IC17', 'IC18', 'IC4', 'IC5', 'IC6', 'IC7', 'IC8', 'IC9'], 'DIL14': ['IC1', 'IC12']}
for fp, refs in SHARED.items():
    policies.append(dict(board='mainboard', footprint=fp, references=refs, cache_model_added=False,
                         reason='Footprint cache keeps the unmarked KiCad body; placed instances carry part-specific marked overrides.'))
for (board, fp), ref in sorted(CACHES.items()):
    policies.append(dict(board=board, footprint=fp, references=[ref], cache_model_added=True, reason='All placed instances use identical model and transform.'))
sources = []
for board in ('mainboard', 'ioboard'):
    record = dict(revision=24, baseline_revision=23,
                  models={Path(f).name: dict(local_model=f.split('/3dmodels/')[1], sha256=sha(W / f)) for f in new_files if f.startswith(board)},
                  references={k: [r.split(':')[1] for r in m['references'] if r.startswith(board)] for k, m in audit['models'].items()
                              if any(r.startswith(board) for r in m['references'])},
                  evidence='validation/models-review-24/marking-quality/sources/marking-evidence.json',
                  limitations=audit['limitations'], physical_fit_qualified=False)
    path = W / board / '3dmodels/REVISION-24-SOURCES.json'
    path.write_text(json.dumps(record, indent=2) + '\n')
    sources.append(f'{board}/3dmodels/REVISION-24-SOURCES.json')
new_files += sources
plan.update(base_revision=23, updated_assignments=updated, new_assignments=[], updated_instance_count=17, new_instance_count=0,
            files=files, new_files=new_files, model_transform_exceptions=[],
            review_manifests=['validation/models-review-24/marking-quality/marking-model-audit.json'],
            scope='17 ICs carry printed part markings transcribed from the kit photographs; chip and socket geometry, colours, '
                  'PCB values and model transforms unchanged.')
(H / 'combined-model-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
prior = json.loads((W / 'validation/working-validation-summary-revision-23.json').read_text())
changed = sorted(n for n, h in prior['outputs'].items() if sha(W / n) != h)
assert changed == sorted(f['file'] for f in files), changed
report = dict(passed=True, files=files, previous_core_file_count=len(prior['outputs']), changed_previous_core_files=changed,
              new_core_files=new_files, component_references_updated=17,
              references={k: m['references'] for k, m in audit['models'].items()}, total_fitted_model_references=491,
              copper_pads_nets_footprint_poses_schematics_and_project_rules_unchanged=True, model_transforms_unchanged=True,
              source_Eagle_files_unchanged=True, old_STEP_preserved=True, physical_fit_qualified=False)
(H / 'installation-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': True, 'changed_files': changed, 'new_files': len(new_files)}, indent=2))
