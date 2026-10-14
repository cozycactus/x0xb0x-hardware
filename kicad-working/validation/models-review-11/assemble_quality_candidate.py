"""Integrate revision-11 reviewed models; preserve physical PCB design nodes."""
from pathlib import Path
import argparse, copy, hashlib, json, shutil, sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
sys.path.insert(0, str(WORK.parent / 'kicad-import/validation'))
from resolve_native_footprint_fields import parse, prop
from verify_native_projects import tokens

def parse_sexpr(text):
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

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def clean(node):
    if not isinstance(node, list):
        return node
    return [clean(x) for x in node if not isinstance(x, list) or not x or x[0] != 'model']

def model_edits(model, row):
    atom=model.items[1]
    assert atom.value == '${KIPRJMOD}/3dmodels/'+row['previous_local_model']
    edits=[(atom.start,atom.end,json.dumps('${KIPRJMOD}/3dmodels/'+row['local_model']))]
    xyz=model.first('offset').first('xyz')
    assert [float(x.value) for x in xyz.items[1:]]==row['previous_offset_mm']
    for atom,old,new in zip(xyz.items[1:],row['previous_offset_mm'],row['offset_mm']):
        if old!=new:edits.append((atom.start,atom.end,format(new,'.12g')))
    return edits

args = argparse.ArgumentParser()
args.add_argument('manifests', nargs='+', type=Path)
args = args.parse_args()
target = HERE / 'candidate'
assert not target.exists()
previous = json.loads((HERE.parent / 'models-review-10/combined-model-plan.json').read_text())
oldrows = previous['assignments']
old = {(r['board'], ref): r for r in oldrows for ref in r['references']}
updates = []
for manifest in args.manifests:
    for raw in json.loads(manifest.read_text())['assignments']:
        row = copy.deepcopy(raw)
        source = Path(row['source_model'])
        assert digest(source) == row['source_sha256']
        priors = [old[row['board'], ref] for ref in row['references']]
        prior = priors[0]
        assert all(x == prior for x in priors)
        assert set(row['references']) == set(prior['references'])
        assert row['footprint'] == prior['footprint']
        assert all(row[key] == prior[key] for key in ['scale', 'rotation_deg'])
        row['previous_offset_mm'] = prior['offset_mm']
        assert row['offset_mm'] == prior['offset_mm'], 'No model transform exceptions authorized in revision11'
        assert not row.get('reviewed_model_only_seating_change')
        row['local_model'] = 'Revision11/' + manifest.parent.name + '/' + source.name
        row['review_manifest'] = str(manifest.resolve().relative_to(HERE.resolve()))
        row['previous_source_sha256'] = prior['source_sha256']
        row['previous_local_model'] = prior['local_model']
        updates.append(row)
byref = {(r['board'], ref): r for r in updates for ref in r['references']}
assert len(byref) == sum(len(r['references']) for r in updates)
rows = [next((r for r in updates if r['board'] == oldrow['board'] and set(r['references']) == set(oldrow['references'])), oldrow) for oldrow in oldrows]

for board in ['mainboard', 'ioboard']:
    shutil.copytree(HERE / 'input-snapshot' / board, target / board)
    selected = [r for r in updates if r['board'] == board]
    if not selected:
        continue
    project = target / board
    pcb = project / (board + '.kicad_pcb')
    before = pcb.read_text()
    edits = []
    seen = set()
    for fp in parse(before).children('footprint'):
        ref = prop(fp, 'Reference').value
        if (board, ref) not in byref:
            continue
        row = byref[board, ref]
        model = fp.children('model')
        assert len(model) == 1
        edits.extend(model_edits(model[0],row))
        seen.add(ref)
    assert seen == {ref for r in selected for ref in r['references']}
    after = before
    for start, end, value in sorted(edits, reverse=True):
        after = after[:start] + value + after[end:]
    assert clean(parse_sexpr(before)) == clean(parse_sexpr(after))
    pcb.write_text(after)
    for row in selected:
        library = project / (board + '-import-fps.pretty') / (row['footprint'] + '.kicad_mod')
        policy = next((x for x in previous['cache_policies'] if x['board']==board and x['footprint']==row['footprint']), None)
        if policy and not policy['cache_model_added']:
            assert not parse(library.read_text()).children('model'), 'Shared heterogeneous cache must remain unassigned'
        else:
            before = library.read_text()
            model = parse(before).children('model')
            assert len(model) == 1
            after=before
            for start,end,value in sorted(model_edits(model[0],row),reverse=True):
                after=after[:start]+value+after[end:]
            assert clean(parse_sexpr(before)) == clean(parse_sexpr(after))
            library.write_text(after)
        dest = project / '3dmodels' / row['local_model']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(row['source_model'], dest)
    provenance = project / '3dmodels/MODEL-PROVENANCE.json'
    metadata = json.loads(provenance.read_text())
    for row in selected:
        metadata['models'][row['local_model']] = dict(source=row['source_model'], sha256=row['source_sha256'],
            source_kind=row['source_kind'], source_urls=row['source_urls'], classification=row['classification'],
            limitations=row['limitations'], review_manifest=row['review_manifest'],
            change='Detailed source-qualified model replacement; all PCB design nodes preserved; any model-only seating offset exception explicitly recorded',
            previous_local_model=row['previous_local_model'], offset_mm=row['offset_mm'], previous_offset_mm=row['previous_offset_mm'], model_seating_review=row.get('model_seating_review'))
    metadata['reviews_directory'] = 'validation/models-review-11'
    provenance.write_text(json.dumps(metadata, indent=2) + '\n')
    (project / '3dmodels/REVISION-11-SOURCES.json').write_text(json.dumps(dict(updates=selected), indent=2) + '\n')
    readme = project / '3dmodels/README.md'
    readme.write_text(readme.read_text() + '\nRevision11 replaces selected coarse models with independent drawing-derived illustrations. Published dimensions, package-selection inferences and undimensioned details are recorded per model; PCB geometry is unchanged. All native assignment offsets, rotations and scales are unchanged. Previous model assets are retained.\n')

inputs = json.loads((HERE / 'input-manifest.json').read_text())['files']
changes = []
added = {}
for relative, sha in inputs.items():
    p = target / relative
    if digest(p) != sha:
        changes.append(dict(file=relative, before_sha256=sha, after_sha256=digest(p),
                            model_nodes_only=p.suffix in ['.kicad_pcb', '.kicad_mod'],
                            model_metadata_only='/3dmodels/' in relative))
for p in target.rglob('*'):
    if p.is_file() and str(p.relative_to(target)) not in inputs:
        added[str(p.relative_to(target))] = digest(p)
plan = dict(base_revision=10, assignments=rows, updated_assignments=updates, new_assignments=[],
            assigned_instance_count=491, new_instance_count=0, updated_instance_count=len(byref),
            historical_added_body_count=66, files=changes, new_files=added,
            model_transform_exceptions=[r for r in updates if r.get('reviewed_model_only_seating_change')], cache_policies=previous['cache_policies'], review_manifests=[str(m.resolve().relative_to(HERE.resolve())) for m in args.manifests])
(HERE / 'combined-model-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
print(json.dumps(dict(models=491, detailed_model_updated_references=len(byref), changed_files=len(changes), new_files=len(added)), indent=2))
