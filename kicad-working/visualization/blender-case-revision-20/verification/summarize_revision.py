"""Write the revision-20 validation summary and docs/tl1100f-leg-colour.json.

Every number comes from a report in this folder or in kicad-working/validation/
models-review-17. Asserts the outcomes that the README files state.

Run:  python3 -I kicad-working/visualization/blender-case-revision-20/verification/summarize_revision.py
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = HERE.parent
REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
REVIEW = WORK / 'validation/models-review-17'


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
    change = load(REV / 'revision-20-change-record.json')
    scene = REV / 'x0xb0x-populated-with-case.blend'
    assert sha(scene) == change['stable_scene_sha256'] == project['blender_sha256']
    assert sha(REV.parent / 'blender-case-revision-19/x0xb0x-populated-with-case.blend') == change['baseline_sha256']
    assert project['kicad_working_revision'] == 17 and project['blender_revision'] == 20
    saved, portable = load(HERE / 'final-saved-scene-audit.json'), load(HERE / 'portable-scene-audit.json')
    openings, models = load(HERE / 'rear-openings-audit.json'), load(HERE / 'kicad-blender-models-audit.json')
    joins, review = load(HERE / 'terminal-join-audit.json'), load(HERE / 'final-render-review.json')
    readonly, close = load(HERE / 'render-readonly-verification.json'), load(HERE / 'tl1100f-render.json')
    assert saved['passed'] and portable['passed'] and openings['passed'] and models['passed'] and joins['passed']
    assert readonly['passed'] and review['passed'] and close['saved_scene_unchanged']
    assert portable['check_count'] == 106 and openings['check_count'] == 44 and openings['ray_count'] == 974
    assert models['compared_references'] == models['identical_references'] == 491 and models['declared_scene']
    assert saved['replaced_mesh_objects'] == 23 and not saved['added_objects']
    colour = load(REVIEW / 'tl1100-colour/tl1100-colour-audit.json')
    native_colour = load(REVIEW / 'tl1100-colour/tl1100-native-colour-check.json')
    install = load(REVIEW / 'installation-audit.json')
    kicad = load(WORK / project['validation_summary'])
    functions = load(REVIEW / 'current-function-verification.json')
    native = load(REVIEW / 'native-terminal-audit.json')
    assert colour['passed'] and not colour['geometry_changed'] and len(colour['recoloured_faces']) == 24
    assert native_colour['passed'] and native_colour['check_count'] == 23
    assert install['passed'] and functions['passed'] and native['passed'] and len(kicad['outputs']) == 291
    verification = dict(
        step_recolour=report(REVIEW / 'tl1100-colour/tl1100-colour-audit.json'),
        native_colour_check=report(REVIEW / 'tl1100-colour/tl1100-native-colour-check.json'),
        kicad_installation=report(REVIEW / 'installation-audit.json'),
        native_lead_and_fit_audit=report(REVIEW / 'native-terminal-audit.json'),
        kicad_validation_summary=report(WORK / project['validation_summary'], passed=True),
        midi_function_replay=report(REVIEW / 'current-function-verification.json'),
        saved_scene_preservation=report(HERE / 'final-saved-scene-audit.json'),
        kicad_blender_models=report(HERE / 'kicad-blender-models-audit.json'),
        native_terminal_joins=report(HERE / 'terminal-join-audit.json'),
        rear_openings=report(HERE / 'rear-openings-audit.json'),
        scene_portability=report(HERE / 'portable-scene-audit.json'),
        tl1100f_render=report(HERE / 'tl1100f-render.json', passed=True),
        render_readonly=report(HERE / 'render-readonly-verification.json'),
        render_review=report(HERE / 'final-render-review.json', view_count=review['view_count']))
    summary = dict(
        schema=1, snapshot_date='2026-10-15', Blender_revision=20, KiCad_revision=17,
        scene=rel(scene), scene_sha256=change['stable_scene_sha256'], scene_bytes=scene.stat().st_size,
        baseline_scene_sha256=change['baseline_sha256'],
        correction='TL1100F tact switches (23 references) show metal legs: the 24 leg faces per switch that leave '
                   'the 12 x 12 mm housing and rise up to 1.45 mm above the board were coloured as black housing by '
                   'revision 8 and are now terminal metal. Geometry unchanged.',
        found_by='User inspection of the KiCad 3D viewer.',
        rule=colour['rule'], recoloured_faces_per_switch=len(colour['recoloured_faces']),
        native_triangles_recoloured_per_switch=native_colour['checks'][0]['recoloured_triangles'],
        references=install['references']['TL1100F'],
        kicad=dict(changed_files=install['changed_previous_core_files'], core_files=len(kicad['outputs']),
                   fresh_ERC_errors=kicad['fresh_ERC_errors'],
                   fresh_DRC_comparison_to_previous=kicad['fresh_DRC_comparison_to_previous']),
        blender=dict(replaced_meshes=len(change['replaced_mesh_objects']), added_objects=0, added_materials=0),
        verification=verification,
        unchanged=['TL1100F geometry (identical B-rep)', 'Original Eagle files, copper, footprint poses and rules',
                   'Every other model reference', 'All Blender objects, poses, materials and views'],
        limitations=['The legs keep the publisher free-state shape; their drill-fit allowance is unchanged.',
                     'Not fit qualified.'],
        physical_fit_qualified=False)
    (HERE / 'independent-validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    docs = dict(summary)
    docs['validation_summary'] = dict(report=rel(HERE / 'independent-validation-summary.json'),
                                      sha256=sha(HERE / 'independent-validation-summary.json'))
    (REPO / 'docs/tl1100f-leg-colour.json').write_text(json.dumps(docs, indent=2) + '\n')
    print(json.dumps(dict(passed=True, verification={k: v.get('passed') for k, v in verification.items()}), indent=2))


main()
