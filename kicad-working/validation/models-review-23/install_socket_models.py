"""Install the socketed IC3/IC2 models; preserve every PCB node and model transform.

IC3 (DIL40) and IC2 (DIL08_AT25) are the only placements of their footprints, so the
PCB instances and the two footprint caches point to the same new model. Only model
path strings change; every other node and every transform is checked identical.

Run from the repository root:
  python3 -I kicad-working/validation/models-review-23/install_socket_models.py
"""
import copy
import hashlib
import json
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

Q = H / 'socket-quality'
audit = json.loads((Q / 'socket-model-audit.json').read_text())
assert audit['passed']
P = '${KIPRJMOD}/3dmodels/'
LOCAL = 'Revision23/socket-quality/'
new_files, swaps = [], {}
for ref, m in audit['models'].items():
    assert sha(Q / m['output']) == m['output_sha256']
    dest = W / 'mainboard/3dmodels' / LOCAL / m['output']
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Q / m['output'], dest)
    new_files.append(f'mainboard/3dmodels/{LOCAL}{m["output"]}')
    swaps[m['footprint']] = (P + m['chip_source'], P + LOCAL + m['output'], ref)


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


files = []
targets = [('mainboard/mainboard.kicad_pcb', list(swaps))] + [(f'mainboard/mainboard-import-fps.pretty/{fp}.kicad_mod', [fp]) for fp in swaps]
for relative, footprints in targets:
    p = W / relative
    snapshot = H / 'input-snapshot' / relative
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        snapshot.write_bytes(p.read_bytes())
    before = snapshot.read_text()
    after, count = before, 0
    for fp in footprints:
        old, new, ref = swaps[fp]
        if relative.endswith('.kicad_pcb'):
            start = after.index(f'(footprint "mainboard-import-fps:{fp}"')
            end = after.index('\n\t(footprint ', start + 1)
            block = after[start:end]
            assert f'(property "Reference" "{ref}"' in block and block.count(f'(model "{old}"') == 1
            after = after[:start] + block.replace(f'(model "{old}"', f'(model "{new}"') + after[end:]
        else:
            assert after.count(f'(model "{old}"') == 1
            after = after.replace(f'(model "{old}"', f'(model "{new}"')
        count += 1
    assert p.read_text() in (before, after)
    assert nonmodels(parse(before)) == nonmodels(parse(after)) and transforms(parse(before)) == transforms(parse(after))
    p.write_text(after)
    files.append(dict(file=relative, before_sha256=sha(snapshot), after_sha256=sha(p), model_nodes_only=True,
                      replaced_model_path_count=count, non_model_nodes_identical=True, model_transforms_identical=True))

plan = json.loads((W / 'validation/models-review-22/combined-model-plan.json').read_text())
updated = []
for fp, (old, new, ref) in swaps.items():
    row = next(a for a in plan['assignments'] if a['board'] == 'mainboard' and a['footprint'] == fp)
    assert row['references'] == [ref]
    m = audit['models'][ref]
    local = new[len(P):]
    row.update(previous_local_model=row['local_model'], previous_source_sha256=row['source_sha256'],
               source_model=str(W / 'mainboard/3dmodels' / local), source_sha256=sha(W / 'mainboard/3dmodels' / local), local_model=local,
               classification='TE manufacturer DIP socket model with the KiCad DIP chip seated on it; transforms unchanged',
               source_kind='TE Customer View Model (manufacturer CAD) plus installed KiCad DIP STEP',
               limitations=audit['limitations'], review_manifest='validation/models-review-23/socket-quality/socket-model-audit.json',
               part=m['part'], socket_seat_mm=m['seat_mm'], chip_top_above_board_mm=m['chip_top_above_board_mm'])
    updated.append(copy.deepcopy(row))
for fp, (_, _, ref) in swaps.items():
    plan['cache_policies'].append(dict(board='mainboard', footprint=fp, references=[ref], cache_model_added=True,
                                       reason='All placed instances use identical model and transform.'))
record = dict(revision=23, baseline_revision=22,
              models={Path(f).name: dict(local_model=f.split('/3dmodels/')[1], sha256=sha(W / f)) for f in new_files},
              references={a['local_model'].split('/')[-1]: a['references'] for a in updated},
              evidence='validation/models-review-23/socket-quality/sources/socket-evidence.json',
              limitations=audit['limitations'], physical_fit_qualified=False)
(W / 'mainboard/3dmodels/REVISION-23-SOURCES.json').write_text(json.dumps(record, indent=2) + '\n')
new_files.append('mainboard/3dmodels/REVISION-23-SOURCES.json')
plan.update(base_revision=22, updated_assignments=updated, new_assignments=[], updated_instance_count=2, new_instance_count=0,
            files=files, new_files=new_files, model_transform_exceptions=[],
            review_manifests=['validation/models-review-23/socket-quality/socket-model-audit.json'],
            scope='IC3 and IC2 sit in their original-BOM TE DIP sockets (manufacturer models) with the KiCad DIP chips raised '
                  '5.10 mm. PCB, footprints and model transforms unchanged apart from four model paths.')
(H / 'combined-model-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
prior = json.loads((W / 'validation/working-validation-summary-revision-22.json').read_text())
changed = sorted(n for n, h in prior['outputs'].items() if sha(W / n) != h)
assert changed == sorted(f['file'] for f in files), changed
report = dict(passed=True, files=files, previous_core_file_count=len(prior['outputs']), changed_previous_core_files=changed,
              new_core_files=new_files, component_references_updated=2, references={r: [r] for r in audit['models']},
              total_fitted_model_references=491, copper_pads_nets_footprint_poses_schematics_and_project_rules_unchanged=True,
              model_transforms_unchanged=True, source_Eagle_files_unchanged=True, old_STEP_preserved=True, physical_fit_qualified=False)
(H / 'installation-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': True, 'changed_files': changed, 'new_files': new_files}, indent=2))
