"""Write the revision-18 validation summary and docs/terminal-join-correction.json.

Every number comes from a report in this folder or in kicad-working/validation/
models-review-15. Asserts the outcomes that the README files state.

Run:  python3 -I kicad-working/visualization/blender-case-revision-18/verification/summarize_revision.py
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = HERE.parent
REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
REVIEW = WORK / 'validation/models-review-15'
PREVIOUS = WORK / 'validation/models-review-14'
FIRST = WORK / 'validation/models-review-13'


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
    change = load(REV / 'revision-18-change-record.json')
    scene = REV / 'x0xb0x-populated-with-case.blend'
    baseline = REV.parent / 'blender-case-revision-17/x0xb0x-populated-with-case.blend'
    assert sha(scene) == change['stable_scene_sha256'] == project['blender_sha256']
    assert sha(baseline) == change['baseline_sha256']
    assert project['kicad_working_revision'] == 15 and project['blender_revision'] == 18
    saved, portable = load(HERE / 'final-saved-scene-audit.json'), load(HERE / 'portable-scene-audit.json')
    openings, models = load(HERE / 'rear-openings-audit.json'), load(HERE / 'kicad-blender-models-audit.json')
    renders, readonly = load(REV / 'render-records.json'), load(HERE / 'render-readonly-verification.json')
    sheet, review = load(HERE / 'terminal-views.json'), load(HERE / 'final-render-review.json')
    assert saved['passed'] and portable['passed'] and openings['passed'] and models['passed']
    assert readonly['passed'] and review['passed'] and sheet['saved_scene_unchanged']
    assert portable['check_count'] == 106 and openings['check_count'] == 44 and openings['ray_count'] == 974
    assert models['compared_references'] == models['identical_references'] == 491 and models['declared_scene']
    assert models['scene_sha256'] == change['stable_scene_sha256']
    assert all(r['source_scene_sha256'] == change['stable_scene_sha256'] for r in renders) and len(renders) == 5
    assert review['image_sha256'] == {**{r['image']: r['sha256'] for r in renders},
                                      'terminal-models.png': sha(REV / 'terminal-models.png')}
    assert not saved['added_objects'] and saved['replaced_mesh_objects'] == 15 and saved['native_reference_count'] == 491

    terminals = load(REVIEW / 'terminal-quality/terminal-model-audit.json')
    earlier = {**load(FIRST / 'terminal-quality/terminal-model-audit.json')['models'],
               **load(PREVIOUS / 'terminal-quality/terminal-model-audit.json')['models']}
    previous_native = load(PREVIOUS / 'native-terminal-audit.json')
    joins = load(REVIEW / 'terminal-quality/terminal-join-audit.json')
    native_joins = load(HERE / 'terminal-join-audit.json')
    assert joins['passed'] and joins['terminals'] == 62 and native_joins['passed'] and native_joins['terminal_pieces'] == 133
    assert sorted(terminals['models']) == ['AlphaRV112', 'CTS290', 'MJ3536N', 'NKKB12AB', 'PanasonicEVU', 'SDS50J']
    all_models = {**earlier, **terminals['models']}
    native = load(REVIEW / 'native-terminal-audit.json')
    install = load(REVIEW / 'installation-audit.json')
    kicad = load(WORK / project['validation_summary'])
    functions = load(REVIEW / 'current-function-verification.json')
    assert terminals['passed'] and native['passed'] and install['passed'] and functions['passed']
    assert all(not b['missing'] for b in native['boards'].values())
    assert sum(b['fitted_models'] for b in native['boards'].values()) == 491
    assert len(kicad['outputs']) == 287 and len(install['changed_previous_core_files']) == 8
    assert all(v for b in kicad['fresh_DRC_comparison_to_previous'].values()
               for k, v in b.items() if k != 'unconnected_items_raw')
    assert kicad['fresh_ERC_errors'] == {'mainboard': 0, 'ioboard': 0}

    table = []
    for key, m in all_models.items():
        fit = next(iter(native['models'][key].values()))
        results = [p['result'] for p in fit['pads']]
        margins = [p['margin_mm'] for p in fit['pads'] if 'margin_mm' in p]
        table.append(dict(model=key, references=sorted(native['models'][key]), board=m['board'],
                          revision=15 if key in terminals['models'] else (14 if key in ('PJ202AH',) else 13),
                          drawing=m['drawing'], terminals_added=m['terminal_solids'],
                          original_solids_retained=m['original_solids'], step=m['output'],
                          drilled_pads_fitting=results.count('fits'),
                          drilled_pads_nominal_interference=results.count('interferes'),
                          drilled_pads_empty_by_design=results.count('empty by design'),
                          smallest_margin_mm=min(margins), lead_protrusion_mm=fit['lead_protrusion_beyond_far_face_mm'],
                          provenance=m['provenance']))
    assert sum(r['terminals_added'] for r in table) == 62 and sum(len(r['references']) for r in table) == 25
    findings = native['nominal_fit_findings']
    assert len(findings) == 11 and len(previous_native['nominal_fit_findings']) == 11
    assert {f['model'] for f in findings} == {'NYS216', 'SDS50J', 'USB', 'PJ202AH'}
    corrections = [dict(model=k, references=sorted(native['models'][k]), drawing=terminals['models'][k]['drawing'],
                        formed_legs=[dict(terminal=r['name'], pad=r['pad'], **r['formed_leg'])
                                     for r in terminals['models'][k]['terminals'] if r['formed_leg']])
                   for k in sorted(terminals['models'])]
    assert sum(len(c['formed_legs']) for c in corrections) == 24

    verification = dict(
        terminal_models=report(REVIEW / 'terminal-quality/terminal-model-audit.json'),
        terminal_models_revision14=report(PREVIOUS / 'terminal-quality/terminal-model-audit.json'),
        terminal_join_audit=report(REVIEW / 'terminal-quality/terminal-join-audit.json'),
        native_terminal_joins=report(HERE / 'terminal-join-audit.json', terminal_pieces=native_joins['terminal_pieces']),
        kicad_installation=report(REVIEW / 'installation-audit.json'),
        native_lead_and_fit_audit=report(REVIEW / 'native-terminal-audit.json'),
        kicad_validation_summary=report(WORK / project['validation_summary'], passed=True),
        midi_function_replay=report(REVIEW / 'current-function-verification.json'),
        saved_scene_preservation=report(HERE / 'final-saved-scene-audit.json'),
        kicad_blender_models=report(HERE / 'kicad-blender-models-audit.json',
                                    identical_references=models['identical_references']),
        rear_openings=report(HERE / 'rear-openings-audit.json'),
        scene_portability=report(HERE / 'portable-scene-audit.json'),
        terminal_sheet=report(HERE / 'terminal-views.json', passed=True),
        render_readonly=report(HERE / 'render-readonly-verification.json'),
        render_review=report(HERE / 'final-render-review.json', view_count=review['view_count']))
    summary = dict(
        schema=1, snapshot_date='2026-10-15', Blender_revision=18, KiCad_revision=15,
        scene=rel(scene), scene_sha256=change['stable_scene_sha256'], scene_bytes=scene.stat().st_size,
        baseline_scene_sha256=change['baseline_sha256'],
        correction='Formed legs join 24 previously free-standing terminals of six models (15 placed references) to '
                   'their bodies: the drawings show these terminals leaving the base edge and turning down, while '
                   'revisions 13-14 modelled only the part below the seat. Pin positions, holes and the 11 recorded '
                   'nominal interferences are unchanged; every one of the 62 terminals now joins its body.',
        corrections=corrections,
        found_by='User inspection of the KiCad 3D viewer; confirmed by isolated edge-on renders and a solid '
                 'distance audit (24 terminals 0.03-2.4 mm from their bodies).',
        lead_presence=dict(boards=native['boards'],
                           statement='Every fitted model has a lead in every drilled hole except the four Grayhill '
                                     'MT bracket holes, whose legs the drawing does not define.'),
        models=table, nominal_fit_findings=findings,
        nominal_fit_method=native['method'],
        kicad=dict(changed_files=install['changed_previous_core_files'], new_files=install['new_core_files'],
                   core_files=len(kicad['outputs']), fresh_ERC_errors=kicad['fresh_ERC_errors'],
                   fresh_DRC_comparison_to_previous=kicad['fresh_DRC_comparison_to_previous'],
                   unconnected_track_end_note=kicad['projects']['mainboard']['unconnected_track_end_note'],
                   model_transforms_unchanged=install['model_transforms_unchanged']),
        blender=dict(added_objects=len(change['added_objects']),
                     replaced_part_meshes=len(change['replaced_mesh_objects']),
                     replaced_objects=change['replaced_mesh_objects'],
                     terminal_material=change['terminal_material'],
                     body_meshes='Body part tessellations matched the native export byte for byte and were kept.',
                     terminal_join_check='scripts/verify_terminal_joins.py: 133 terminal pieces at 25 references join their bodies'),
        verification=verification,
        unchanged=['Original Eagle files', 'KiCad copper, pads, drills, nets, footprint poses, model transforms and '
                   'rules', 'Previous body solids of all 12 models', 'Pin positions and the six other terminal models',
                   'All other 466 model references',
                   'All Blender poses, case, plate, LEDs, caps, hardware, wiring study, materials and views'],
        limitations=['Formed-leg heights and bends are assumptions: the drawings show the path but do not dimension it.',
                     'Terminal thicknesses, bends and several widths are labelled assumptions; LPTC leads have no '
                     'manufacturer data at all.',
                     'Drawing/footprint disagreements are recorded as nominal interference; neither source was '
                     'altered to fit.',
                     'NYS216 rows remain 0.35 mm from the footprint rows with no source explaining the Eagle datum; '
                     'the USB board-lock interference is a designed press fit; the fitted USB part is unresolved.',
                     'Grayhill MT bracket legs and SDS-50J locating pegs remain omitted.',
                     'Historical part variants, tolerances and physical fit are unqualified.'],
        physical_fit_qualified=False)
    (HERE / 'independent-validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    docs = dict(summary)
    docs['validation_summary'] = dict(report=rel(HERE / 'independent-validation-summary.json'),
                                      sha256=sha(HERE / 'independent-validation-summary.json'))
    (REPO / 'docs/terminal-join-correction.json').write_text(json.dumps(docs, indent=2) + '\n')
    print(json.dumps(dict(passed=True, verification={k: v.get('passed') for k, v in verification.items()},
                          findings=len(findings)), indent=2))


main()
