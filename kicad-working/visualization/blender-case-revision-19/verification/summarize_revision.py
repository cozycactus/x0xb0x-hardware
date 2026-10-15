"""Write the revision-19 validation summary and docs/grayhill-25l-rebuild.json.

Every number comes from a report in this folder or in kicad-working/validation/
models-review-16. Asserts the outcomes that the README files state.

Run:  python3 -I kicad-working/visualization/blender-case-revision-19/verification/summarize_revision.py
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = HERE.parent
REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
REVIEW = WORK / 'validation/models-review-16'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def rel(path):
    return str(Path(path).resolve().relative_to(REPO))


def report(path, **extra):
    data = load(path)
    row = dict(report=rel(path), sha256=sha(path))
    for key in ('passed', 'check_count', 'checks_count', 'ray_count'):
        if key in data:
            row[key] = data[key]
    row.update(extra)
    return row


def main():
    project = load(REPO / 'PROJECT.json')
    change = load(REV / 'revision-19-change-record.json')
    scene = REV / 'x0xb0x-populated-with-case.blend'
    assert sha(scene) == change['stable_scene_sha256'] == project['blender_sha256']
    assert sha(REV.parent / 'blender-case-revision-18/x0xb0x-populated-with-case.blend') == change['baseline_sha256']
    assert project['kicad_working_revision'] == 16 and project['blender_revision'] == 19
    saved, portable = load(HERE / 'final-saved-scene-audit.json'), load(HERE / 'portable-scene-audit.json')
    openings, models = load(HERE / 'rear-openings-audit.json'), load(HERE / 'kicad-blender-models-audit.json')
    joins, review = load(HERE / 'terminal-join-audit.json'), load(HERE / 'final-render-review.json')
    renders, readonly = load(REV / 'render-records.json'), load(HERE / 'render-readonly-verification.json')
    sheet, close = load(HERE / 'terminal-views.json'), load(HERE / 'grayhill-render.json')
    assert saved['passed'] and portable['passed'] and openings['passed'] and models['passed'] and joins['passed']
    assert readonly['passed'] and review['passed'] and sheet['saved_scene_unchanged'] and close['saved_scene_unchanged']
    assert portable['check_count'] == 106 and openings['check_count'] == 44 and openings['ray_count'] == 974
    assert models['compared_references'] == models['identical_references'] == 491 and models['declared_scene']
    assert joins['terminal_pieces'] == 133 and len(renders) == 5
    assert len(change['added_objects']) == 8 and len(change['removed_objects']) == 2
    body = load(REVIEW / 'grayhill-quality/grayhill-model-audit.json')
    terminals = load(REVIEW / 'terminal-quality/terminal-model-audit.json')
    join_audit = load(REVIEW / 'terminal-quality/terminal-join-audit.json')
    native = load(REVIEW / 'native-terminal-audit.json')
    install = load(REVIEW / 'installation-audit.json')
    kicad = load(WORK / project['validation_summary'])
    functions = load(REVIEW / 'current-function-verification.json')
    assert body['passed'] and terminals['passed'] and join_audit['passed'] and native['passed'] and install['passed']
    assert functions['passed'] and len(kicad['outputs']) == 289
    assert install['changed_previous_core_files'] == ['mainboard/mainboard-import-fps.pretty/GH3074.kicad_mod',
                                                      'mainboard/mainboard.kicad_pcb']
    assert len(native['nominal_fit_findings']) == 11
    fit = native['models']['Grayhill25L']
    assert all(p['result'] in ('fits', 'empty by design') for v in fit.values() for p in v['pads'])

    verification = dict(
        grayhill_body=report(REVIEW / 'grayhill-quality/grayhill-model-audit.json'),
        terminal_model=report(REVIEW / 'terminal-quality/terminal-model-audit.json'),
        terminal_join_audit=report(REVIEW / 'terminal-quality/terminal-join-audit.json'),
        kicad_installation=report(REVIEW / 'installation-audit.json'),
        native_lead_and_fit_audit=report(REVIEW / 'native-terminal-audit.json'),
        kicad_validation_summary=report(WORK / project['validation_summary'], passed=True),
        midi_function_replay=report(REVIEW / 'current-function-verification.json'),
        saved_scene_preservation=report(HERE / 'final-saved-scene-audit.json'),
        kicad_blender_models=report(HERE / 'kicad-blender-models-audit.json'),
        native_terminal_joins=report(HERE / 'terminal-join-audit.json'),
        rear_openings=report(HERE / 'rear-openings-audit.json'),
        scene_portability=report(HERE / 'portable-scene-audit.json'),
        terminal_sheet=report(HERE / 'terminal-views.json', passed=True),
        grayhill_render=report(HERE / 'grayhill-render.json', passed=True),
        render_readonly=report(HERE / 'render-readonly-verification.json'),
        render_review=report(HERE / 'final-render-review.json', view_count=review['view_count']))
    summary = dict(
        schema=1, snapshot_date='2026-10-15', Blender_revision=19, KiCad_revision=16,
        scene=rel(scene), scene_sha256=change['stable_scene_sha256'], scene_bytes=scene.stat().st_size,
        baseline_scene_sha256=change['baseline_sha256'],
        correction='Grayhill 25LB22-H (S3, S4) rebuilt from the Series 25L drawing and a product photograph: round '
                   'drum top with lock lugs, white 8-4-2-1-C label band, green output board with gold lands and '
                   'solder joints, and the non-turn tab on the centre line opposite the pins (drawing front view).',
        printed_dimensions_kept=body['printed_dimensions_kept'], photo_derived=body['photo_derived'],
        pins=dict(positions='unchanged (0.100 in pitch, 0.500 in from the shaft)', protrusion_above_board_mm=0.8,
                  fit=[dict(pad=p['pad'], result=p['result'], margin_mm=p.get('margin_mm'))
                       for p in next(iter(fit.values()))['pads']]),
        mounting_holes='MT1-MT4 stay empty: they serve the optional 25J5155 bracket and the BOM part 25LB22-H has no '
                       '-Z (with bracket) suffix.',
        blender=dict(added_objects=change['added_objects'], removed_objects=change['removed_objects'],
                     replaced_part_meshes=len(change['replaced_mesh_objects']), added_materials=change['added_materials'],
                     retired_materials='Two materials used only by the old Grayhill board and land parts are dropped'),
        kicad=dict(changed_files=install['changed_previous_core_files'], core_files=len(kicad['outputs']),
                   fresh_ERC_errors=kicad['fresh_ERC_errors'],
                   fresh_DRC_comparison_to_previous=kicad['fresh_DRC_comparison_to_previous']),
        verification=verification,
        unchanged=['Original Eagle files', 'KiCad copper, pads, drills, nets, footprint poses, model transforms and rules',
                   'Every other model reference', 'All Blender poses, case, plate, LEDs, caps, hardware, wiring study, '
                   'previous materials and views'],
        limitations=['Drum diameter and height, lug size, label layout and colours come from the photograph, not printed '
                     'dimensions.', 'The photograph is user-supplied and not retained; its period and source are not '
                     'recorded.', 'Not manufacturer CAD; physical fit is unqualified.'],
        physical_fit_qualified=False)
    (HERE / 'independent-validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    docs = dict(summary)
    docs['validation_summary'] = dict(report=rel(HERE / 'independent-validation-summary.json'),
                                      sha256=sha(HERE / 'independent-validation-summary.json'))
    (REPO / 'docs/grayhill-25l-rebuild.json').write_text(json.dumps(docs, indent=2) + '\n')
    print(json.dumps(dict(passed=True, verification={k: v.get('passed') for k, v in verification.items()}), indent=2))


main()
