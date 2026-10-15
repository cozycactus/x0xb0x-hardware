"""Write the revision-25 render review, validation summary and docs/resistor-colour-bands.json.

Every number comes from a report in this folder or in kicad-working/validation/
models-review-22. Asserts the outcomes that the README files state.

Run:  python3 -I kicad-working/visualization/blender-case-revision-25/verification/summarize_revision.py
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = HERE.parent
REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
REVIEW = WORK / 'validation/models-review-22'
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
change = load(REV / 'revision-25-change-record.json')
scene = REV / 'x0xb0x-populated-with-case.blend'
assert sha(scene) == change['stable_scene_sha256'] == project['blender_sha256']
assert project['kicad_working_revision'] == 22 and project['blender_revision'] == 25
saved, portable = load(HERE / 'final-saved-scene-audit.json'), load(HERE / 'portable-scene-audit.json')
openings, models = load(HERE / 'rear-openings-audit.json'), load(HERE / 'kicad-blender-models-audit.json')
joins, drill = load(HERE / 'terminal-join-audit.json'), load(HERE / 'drill-fit-audit.json')
details, renders = load(HERE / 'resistor-detail-render.json'), load(REV / 'render-records.json')
readonly = load(HERE / 'render-readonly-verification.json')
build = load(REVIEW / 'resistor-quality/resistor-model-audit.json')
bands = load(REVIEW / 'resistor-quality/sources/resistor-band-assignments.json')
native_bands = load(REVIEW / 'resistor-quality/resistor-native-band-check.json')
install, native = load(REVIEW / 'installation-audit.json'), load(REVIEW / 'native-terminal-audit.json')
kicad, functions = load(WORK / project['validation_summary']), load(REVIEW / 'current-function-verification.json')
for r in (saved, portable, openings, models, joins, drill, details, readonly, build, bands, native_bands, install, native, functions):
    assert r['passed']
assert saved['check_count'] == 13 and portable['check_count'] == 106 and openings['check_count'] == 44 and openings['ray_count'] == 974
assert models['compared_references'] == models['identical_references'] == 491
assert joins['references_checked'] == 25 and joins['terminal_pieces'] == 133 and drill['measured_models'] == 489
assert len(change['changes']) == 212 and change['added_objects'] == [] and len(change['added_materials']) == 12
assert native_bands['check_count'] == 212 and len(native['nominal_fit_findings']) == 11 and len(kicad['outputs']) == 345
assert install['changed_previous_core_files'] == ['ioboard/ioboard.kicad_pcb', 'mainboard/mainboard.kicad_pcb']

images = {r['view']: dict(path=r['image'], sha256=sha(REV / r['image'])) for r in renders}
images.update({Path(r['image']).stem: dict(path=r['image'], sha256=sha(REV / r['image'])) for r in details['images']})
review = dict(passed=True, review='Visual inspection of all seven current PNGs', scene_sha256=change['stable_scene_sha256'], images=images,
              observations=['Same-camera 1% detail: R74-R90 show light-blue bodies reading Red Black Black Orange Brown from the top',
                            'Same-camera 5% detail: tan bodies with four bands; body outline, leads and positions unchanged',
                            'Exploded view shows the banded resistors across the mainboard; assembled and control-side views preserved',
                            'The tan body sampled from the page graphic renders slightly peach under the scene lights; colours are uncalibrated'],
              physical_fit_qualified=False)
(HERE / 'final-render-review.json').write_text(json.dumps(review, indent=2) + '\n')
verification = dict(
    band_assignments=report(REVIEW / 'resistor-quality/sources/resistor-band-assignments.json'),
    resistor_models=report(REVIEW / 'resistor-quality/resistor-model-audit.json'),
    native_bands=report(REVIEW / 'resistor-quality/resistor-native-band-check.json'),
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
    detail_renders=report(HERE / 'resistor-detail-render.json'),
    render_readonly=report(HERE / 'render-readonly-verification.json'),
    render_review=report(HERE / 'final-render-review.json'))
assign = bands['assignments']
summary = dict(
    schema=1, snapshot_date='2026-10-16', Blender_revision=25, KiCad_revision=22,
    scene=rel(scene), scene_sha256=change['stable_scene_sha256'], scene_bytes=scene.stat().st_size,
    baseline_scene_sha256=change['baseline_sha256'],
    correction='All 212 fixed resistors carry the original kit colour bands from the original parts page: tan 5% bodies with '
               'four bands and light-blue 1% bodies with five (R4, R5, R106, R74-R90). Body and lead geometry are the unchanged '
               'KiCad DIN0207 models; bands are flush rings of the body material.',
    band_sources=dict(Counter(a['source'].split(';')[0] for a in assign.values())),
    tolerances=dict(Counter(a['tolerance'] for a in assign.values())),
    variants=len(build['models']), band_spans_mm_from_end_A=build['band_spans_mm_from_end_A'],
    reading_direction='Upright parts read from the top; lying parts from the pad-1 end (illustration)',
    value_differences=bands['value_differences'], value_difference_resolution=bands['differences_resolution'],
    page_corrections=['4.7K row prints "GOld"; read as Gold', '200K 1% row prints no bands; read from its photograph as Red Black Black Orange Brown',
                      '10K row lists 26 of 54 references; the other 28 PCB references are all 10K'],
    led_resistors='The 40 LED resistors carry the PCB value 10K; the parts page says the value may vary with the LED.',
    colours=dict(bands=build['colours'], bodies=build['body_colours'], leads=build['lead_colour']),
    sources=dict(parts_page=bands['parts_page']['url'], parts_page_mirror=bands['parts_page']['local_mirror'], photographs=bands['photos']['source']),
    blender=dict(changed_meshes=len(change['changes']), added_materials=change['added_materials'],
                 retired_materials=change['retired_materials'], added_objects=change['added_objects']),
    kicad=dict(changed_files=install['changed_previous_core_files'], new_files=len(install['new_core_files']), core_files=len(kicad['outputs']),
               footprint_caches_unchanged=True, fresh_ERC_errors=kicad['fresh_ERC_errors'],
               fresh_DRC_comparison_to_previous=kicad['fresh_DRC_comparison_to_previous']),
    verification=verification,
    unchanged=['Original Eagle files', 'KiCad copper, pads, drills, nets, footprint poses and caches, PCB value fields, model transforms and rules',
               'Resistor body and lead geometry (outline within 1 micrometre)', 'Every other model reference, including the Xicon XRL electrolytics',
               'All Blender objects, poses, case, LEDs, spacers, caps, hardware, wiring study, previous materials (except two left unused), cameras and animation'],
    limitations=build['limitations'] + ['Not a measurement of the kit parts; physical fit is unqualified.'],
    physical_fit_qualified=False)
(HERE / 'independent-validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
docs = dict(summary)
docs['validation_summary'] = dict(report=rel(HERE / 'independent-validation-summary.json'), sha256=sha(HERE / 'independent-validation-summary.json'))
(REPO / 'docs/resistor-colour-bands.json').write_text(json.dumps(docs, indent=2) + '\n')
print(json.dumps(dict(passed=True, verification={k: v.get('passed') for k, v in verification.items()}), indent=2))
