"""Write the revision-27 render review, validation summary and docs/ic-markings.json.

Every number comes from a report in this folder or in kicad-working/validation/
models-review-24. Asserts the outcomes that the README files state.

Run:  python3 -I kicad-working/visualization/blender-case-revision-27/verification/summarize_revision.py
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = HERE.parent
REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
REVIEW = WORK / 'validation/models-review-24'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
load = lambda p: json.loads(Path(p).read_text())  # noqa: E731
rel = lambda p: str(Path(p).resolve().relative_to(REPO))  # noqa: E731


def report(path, **extra):
    data = load(path)
    row = dict(report=rel(path), sha256=sha(path))
    for key in ('passed', 'check_count', 'ray_count'):
        if key in data:
            row[key] = data[key]
    row.update(extra)
    return row


project = load(REPO / 'PROJECT.json')
change = load(REV / 'revision-27-change-record.json')
scene = REV / 'x0xb0x-populated-with-case.blend'
assert sha(scene) == change['stable_scene_sha256'] == project['blender_sha256']
assert project['kicad_working_revision'] == 24 and project['blender_revision'] == 27
saved, portable = load(HERE / 'final-saved-scene-audit.json'), load(HERE / 'portable-scene-audit.json')
openings, models = load(HERE / 'rear-openings-audit.json'), load(HERE / 'kicad-blender-models-audit.json')
joins, drill = load(HERE / 'terminal-join-audit.json'), load(HERE / 'drill-fit-audit.json')
neighbours, details = load(HERE / 'marking-neighbour-audit.json'), load(HERE / 'marking-detail-render.json')
renders, readonly = load(REV / 'render-records.json'), load(HERE / 'render-readonly-verification.json')
build = load(REVIEW / 'marking-quality/marking-model-audit.json')
native_check = load(REVIEW / 'marking-quality/marking-native-check.json')
evidence = load(REVIEW / 'marking-quality/sources/marking-evidence.json')
install, native = load(REVIEW / 'installation-audit.json'), load(REVIEW / 'native-terminal-audit.json')
kicad, functions = load(WORK / project['validation_summary']), load(REVIEW / 'current-function-verification.json')
for r in (saved, portable, openings, models, joins, drill, neighbours, details, readonly, build, native_check, install, native, functions):
    assert r['passed']
assert saved['check_count'] == 12 and portable['check_count'] == 106 and openings['check_count'] == 44 and openings['ray_count'] == 974
assert models['compared_references'] == models['identical_references'] == 491
assert joins['references_checked'] == 25 and joins['terminal_pieces'] == 133 and drill['measured_models'] == 489
assert len(change['changes']) == 17 and change['added_objects'] == [] and len(change['added_materials']) == 1
assert not neighbours['new_contacts'] and native_check['check_count'] == 17 and len(native['nominal_fit_findings']) == 11 and len(kicad['outputs']) == 361
images = {r['view']: dict(path=r['image'], sha256=sha(REV / r['image'])) for r in renders}
images.update({Path(r['image']).stem: dict(path=r['image'], sha256=sha(REV / r['image'])) for r in details['images']})
review = dict(passed=True, review='Visual inspection of all nine current PNGs', scene_sha256=change['stable_scene_sha256'], images=images,
              observations=['Same-camera details show P0418SB / MM74HC595N on the 74HC595s, L0434 / 4N37 on IC24 and FT232BM / 425-1 '
                            'on the underside IC25, all in light-grey ink and readable (IC25 is a proper rotation, not mirrored)',
                            'Assembled, exploded and control-side views preserved; nothing else changes'],
              physical_fit_qualified=False)
(HERE / 'final-render-review.json').write_text(json.dumps(review, indent=2) + '\n')
verification = dict(
    marking_models=report(REVIEW / 'marking-quality/marking-model-audit.json'),
    native_marking_check=report(REVIEW / 'marking-quality/marking-native-check.json'),
    kicad_installation=report(REVIEW / 'installation-audit.json'),
    native_lead_and_fit_audit=report(REVIEW / 'native-terminal-audit.json'),
    kicad_validation_summary=report(WORK / project['validation_summary'], passed=True),
    midi_function_replay=report(REVIEW / 'current-function-verification.json'),
    saved_scene_preservation=report(HERE / 'final-saved-scene-audit.json'),
    kicad_blender_models=report(HERE / 'kicad-blender-models-audit.json'),
    drill_fit=report(HERE / 'drill-fit-audit.json'),
    terminal_joins=report(HERE / 'terminal-join-audit.json'),
    rear_openings=report(HERE / 'rear-openings-audit.json'),
    scene_portability=report(HERE / 'portable-scene-audit.json'),
    marking_neighbours=report(HERE / 'marking-neighbour-audit.json'),
    detail_renders=report(HERE / 'marking-detail-render.json'),
    render_readonly=report(HERE / 'render-readonly-verification.json'),
    render_review=report(HERE / 'final-render-review.json'))
summary = dict(
    schema=1, snapshot_date='2026-10-16', Blender_revision=27, KiCad_revision=24,
    scene=rel(scene), scene_sha256=change['stable_scene_sha256'], scene_bytes=scene.stat().st_size,
    baseline_scene_sha256=change['baseline_sha256'],
    correction='The 17 ICs carry printed part markings transcribed from the original kit photographs (part number and code '
               'lines, logos omitted), raised 0.03 mm in light-grey ink on the unchanged chip tops; the 74HC165s carry their part '
               'number only. The ATmega162 text runs across the body as photographed; the underside FT232BM reads from below.',
    markings={k: dict(lines=v['lines'], references=v['references'], cap_height_mm=v['cap_height_mm']) for k, v in build['models'].items()},
    photos=evidence['photos'], font=evidence['font'], pcb_value_differences=evidence['pcb_value_differences'],
    neighbour_contacts=dict(new=neighbours['new_contacts']),
    blender=dict(changed_meshes=len(change['changes']), added_materials=change['added_materials'], retired_materials=change['retired_materials']),
    kicad=dict(changed_files=install['changed_previous_core_files'], new_files=len(install['new_core_files']), core_files=len(kicad['outputs']),
               fresh_ERC_errors=kicad['fresh_ERC_errors'], fresh_DRC_comparison_to_previous=kicad['fresh_DRC_comparison_to_previous']),
    verification=verification,
    unchanged=['Original Eagle files', 'KiCad copper, pads, drills, nets, footprint poses, PCB value fields, model transforms and rules',
               'Every other model reference', 'All Blender objects, poses, case, LEDs, spacers, caps, hardware, wiring study, previous materials, cameras and animation'],
    limitations=build['limitations'], physical_fit_qualified=False)
(HERE / 'independent-validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
docs = dict(summary)
docs['validation_summary'] = dict(report=rel(HERE / 'independent-validation-summary.json'), sha256=sha(HERE / 'independent-validation-summary.json'))
(REPO / 'docs/ic-markings.json').write_text(json.dumps(docs, indent=2) + '\n')
print(json.dumps(dict(passed=True, verification={k: v.get('passed') for k, v in verification.items()}), indent=2))
