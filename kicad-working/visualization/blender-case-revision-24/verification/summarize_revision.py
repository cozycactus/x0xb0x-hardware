"""Write the revision-24 render review, validation summary and docs/electrolytic-xrl-correction.json.

Every number comes from a report in this folder or in kicad-working/validation/
models-review-21. Asserts the outcomes that the README files state.

Run:  python3 -I kicad-working/visualization/blender-case-revision-24/verification/summarize_revision.py
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = HERE.parent
REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
REVIEW = WORK / 'validation/models-review-21'
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
change = load(REV / 'revision-24-change-record.json')
scene = REV / 'x0xb0x-populated-with-case.blend'
assert sha(scene) == change['stable_scene_sha256'] == project['blender_sha256']
assert project['kicad_working_revision'] == 21 and project['blender_revision'] == 24
saved, portable = load(HERE / 'final-saved-scene-audit.json'), load(HERE / 'portable-scene-audit.json')
openings, models = load(HERE / 'rear-openings-audit.json'), load(HERE / 'kicad-blender-models-audit.json')
joins, drill = load(HERE / 'terminal-join-audit.json'), load(HERE / 'drill-fit-audit.json')
neighbours, details = load(HERE / 'electrolytic-neighbour-audit.json'), load(HERE / 'electrolytic-detail-render.json')
renders, readonly = load(REV / 'render-records.json'), load(HERE / 'render-readonly-verification.json')
build = load(REVIEW / 'electrolytic-quality/electrolytic-model-audit.json')
colours = load(REVIEW / 'electrolytic-quality/electrolytic-native-colour-check.json')
install, native = load(REVIEW / 'installation-audit.json'), load(REVIEW / 'native-terminal-audit.json')
kicad, functions = load(WORK / project['validation_summary']), load(REVIEW / 'current-function-verification.json')
evidence = load(REVIEW / 'electrolytic-quality/sources/electrolytic-evidence.json')
for r in (saved, portable, openings, models, joins, drill, neighbours, details, readonly, build, colours, install, native, functions):
    assert r['passed']
assert saved['check_count'] == 12 and portable['check_count'] == 106 and openings['check_count'] == 44 and openings['ray_count'] == 974
assert models['compared_references'] == models['identical_references'] == 491
assert joins['references_checked'] == 25 and joins['terminal_pieces'] == 133 and drill['measured_models'] == 489
assert len(change['changes']) == 39 and change['added_objects'] == [] and len(change['added_materials']) == 4
assert len(native['nominal_fit_findings']) == 11 and len(kicad['outputs']) == 305
assert [(c['target'], c['other']) for c in neighbours['new_contacts']] == [('IOBOARD/C8', 'IOBOARD/TM6/mesh.001')]
assert not neighbours['removed_contacts'] and len(neighbours['retained_contacts']) == 2
fits = {k: sorted({(p['pad'], p['result'], p['margin_mm']) for v in refs.values() for p in v['pads']})
        for k, refs in native['models'].items() if k.startswith('XRL')}
assert sum(len(native['models'][k]) for k in fits) == 39 and all(r == 'fits' for v in fits.values() for _, r, _ in v)

images = {r['view']: dict(path=r['image'], sha256=sha(REV / r['image'])) for r in renders}
images.update({Path(r['image']).stem: dict(path=r['image'], sha256=sha(REV / r['image'])) for r in details['images']})
review = dict(passed=True, review='Visual inspection of all seven current PNGs', scene_sha256=change['stable_scene_sha256'],
              images=images,
              observations=['Exploded view shows the light-blue XRL cans across the mainboard and the I/O power section',
                            'Same-camera mainboard detail: the 5 mm cans now stand 12.5 mm tall in place of the 5 mm-tall '
                            'generic bodies, with the dark negative stripe on the negative side',
                            'Same-camera I/O detail: C7/C8 show the 6.3 mm cans with the vent cross; C3/C5 keep their '
                            'geometry in the photo colours',
                            'Assembled panel appearance and control-side inspection remain preserved',
                            'Detail lighting is temporary and uncalibrated; colours are photo-sampled, not measured'],
              physical_fit_qualified=False)
(HERE / 'final-render-review.json').write_text(json.dumps(review, indent=2) + '\n')
verification = dict(
    electrolytic_models=report(REVIEW / 'electrolytic-quality/electrolytic-model-audit.json'),
    native_colours=report(REVIEW / 'electrolytic-quality/electrolytic-native-colour-check.json'),
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
    electrolytic_neighbours=report(HERE / 'electrolytic-neighbour-audit.json'),
    detail_renders=report(HERE / 'electrolytic-detail-render.json'),
    render_readonly=report(HERE / 'render-readonly-verification.json'),
    render_review=report(HERE / 'final-render-review.json'))
dims = {k: v['dimensions_mm'] for k, v in build['models'].items()}
summary = dict(
    schema=1, snapshot_date='2026-10-16', Blender_revision=24, KiCad_revision=21,
    scene=rel(scene), scene_sha256=change['stable_scene_sha256'], scene_bytes=scene.stat().st_size,
    baseline_scene_sha256=change['baseline_sha256'],
    correction='All 39 radial electrolytics are Xicon XRL bodies sized from the XRL datasheet XC-600178 (1/8/07) and '
               'coloured from the original kit photographs. 36 placements replace generic KiCad cans (5 x 5 mm and '
               '10 x 10 mm visual bodies at 2.50/5.00 mm pitch) with 5 x 11, 6.3 x 11 and 10 x 12.5 mm cans whose leads '
               'land on the original 2.54/5.08 mm holes; C17 and C3/C5 keep their revision-5 XRL geometry, recoloured.',
    references={v['name']: v['references'] for v in build['models'].values()} |
               {k: [f"{v['board']}:{r}" for r in v['references']] for k, v in build['recoloured'].items()},
    dimensions_mm=dims,
    lead_fit={k: [dict(pad=p, result=r, radial_margin_mm=m) for p, r, m in v] for k, v in fits.items()},
    sources=dict(datasheet=evidence['datasheet']['title'], datasheet_file=rel(REVIEW / 'electrolytic-quality/sources/xicon-xrl-XC-600178.pdf'),
                 parts_page=evidence['bom']['parts_page']['url'], expanded_bom=evidence['bom']['expanded_bom']['url'],
                 expanded_bom_status=evidence['bom']['expanded_bom']['status'], kit_photographs=evidence['kit_photos']['source']),
    interferences=dict(new=neighbours['new_contacts'], retained_unchanged=neighbours['retained_contacts'],
                       minimum_headroom_above_can_top_mm=neighbours['minimum_headroom_mm'],
                       note='Recorded, not corrected: placement and model transforms are original. C8 is the 6.3 mm '
                            '100uF 25V can; the E5-6 silkscreen (5.33 mm) was drawn for a 5 mm can.'),
    pcb_value_differences=evidence['pcb_value_differences'],
    blender=dict(changed_meshes=len(change['changes']), added_materials=change['added_materials'],
                 retired_materials=change['retired_materials'], added_objects=change['added_objects']),
    kicad=dict(changed_files=install['changed_previous_core_files'], new_files=install['new_core_files'],
               core_files=len(kicad['outputs']), fresh_ERC_errors=kicad['fresh_ERC_errors'],
               fresh_DRC_comparison_to_previous=kicad['fresh_DRC_comparison_to_previous']),
    verification=verification,
    unchanged=['Original Eagle files', 'KiCad copper, pads, drills, nets, footprint poses, PCB value fields, model transforms and rules',
               'Every other model reference', 'All Blender objects, poses, case, LEDs, spacers, caps, hardware, wiring study, '
               'previous materials (except eight left unused by the replaced meshes), cameras and animation'],
    limitations=build['limitations'] + ['Not manufacturer CAD; physical fit is unqualified.'],
    physical_fit_qualified=False)
(HERE / 'independent-validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
docs = dict(summary)
docs['validation_summary'] = dict(report=rel(HERE / 'independent-validation-summary.json'), sha256=sha(HERE / 'independent-validation-summary.json'))
(REPO / 'docs/electrolytic-xrl-correction.json').write_text(json.dumps(docs, indent=2) + '\n')
print(json.dumps(dict(passed=True, verification={k: v.get('passed') for k, v in verification.items()}), indent=2))
