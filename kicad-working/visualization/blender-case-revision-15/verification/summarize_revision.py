"""Write the revision-15 validation summary and docs/rear-height-datum-correction.json.

Every number comes from a report in this folder or the retained original
rear-panel DXF hole table. Asserts the outcomes that the README files state.

Run:  python3 -I kicad-working/visualization/blender-case-revision-15/verification/summarize_revision.py
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = HERE.parent
REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
MEASURED = 'measurement; outcomes asserted by summarize_revision.py'
AXIS = {'HEADPHONE0': 8.0, 'MIXIN0': 8.0, 'MIXOUT0': 8.0, 'CV0': 5.5, 'GATE0': 5.5,
        'DIN1': 10.0, 'DIN2': 10.0, 'DIN3': 10.0, 'DIN4': 10.0}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def rel(path):
    return str(Path(path).resolve().relative_to(REPO))


def report(name, **extra):
    path = HERE / name
    data = load(path)
    row = dict(report=rel(path), sha256=sha(path))
    for key in ('passed', 'check_count', 'ray_count'):
        if key in data:
            row[key] = data[key]
    row.update(extra)
    return row


def main():
    project = load(REPO / 'PROJECT.json')
    change = load(REV / 'revision-15-change-record.json')
    scene = REV / 'x0xb0x-populated-with-case.blend'
    baseline = REV.parent / 'blender-case-revision-14/x0xb0x-populated-with-case.blend'
    assert sha(scene) == change['stable_scene_sha256'] == project['blender_sha256']
    assert sha(baseline) == change['baseline_sha256']
    saved, portable = load(HERE / 'final-saved-scene-audit.json'), load(HERE / 'portable-scene-audit.json')
    openings = load(HERE / 'rear-openings-audit.json')
    s14, s15 = load(HERE / 'rear-seating-revision-14.json'), load(HERE / 'rear-seating-audit.json')
    c14, c15 = load(HERE / 'io-contacts-revision-14.json'), load(HERE / 'io-contacts.json')
    renders, readonly = load(REV / 'render-records.json'), load(HERE / 'render-readonly-verification.json')
    review = load(HERE / 'final-render-review.json')
    assert saved['passed'] and portable['passed'] and openings['passed'] and readonly['passed'] and review['passed']
    assert portable['check_count'] == 106 and openings['check_count'] == 44 and openings['ray_count'] == 974
    assert all(r['source_scene_sha256'] == change['stable_scene_sha256'] for r in renders) and len(renders) == 7
    assert review['image_sha256'] == {r['image']: r['sha256'] for r in renders}
    assert s14['saved_scene_bytes_unchanged'] and s15['saved_scene_bytes_unchanged']
    assert c14['scene_bytes_unchanged'] and c15['scene_bytes_unchanged']
    assert s14['scene_sha256'] == c14['scene_sha256'] == change['baseline_sha256']
    assert s15['scene_sha256'] == c15['scene_sha256'] == change['stable_scene_sha256']
    assert abs(change['mounting_plane_after_mm'] - 6.35) < 1e-5

    source = load(WORK / 'validation/rear-seating-review/source-audit/seating-source-audit.json')['rear_panel']
    holes = [dict(reference=c['board_reference'], hole_center_above_plate_edge_mm=c['center_mm'][1],
                  hole_center_in=round(c['center_mm'][1] / 25.4, 4),
                  above_0_250in_datum_mm=round(c['center_mm'][1] - 6.35, 4),
                  modelled_axis_mm=AXIS[c['board_reference']],
                  datum_axis_difference_mm=round(c['center_mm'][1] - 6.35 - AXIS[c['board_reference']], 4))
             for c in source['circles']]
    rects = [dict(reference=r['board_reference'], bottom_edge_mm=r['bounds_mm'][0][1],
                  bottom_edge_in=round(r['bounds_mm'][0][1] / 25.4, 4)) for r in source['rectangular_cutouts']]
    assert all(r['bottom_edge_mm'] == 6.35 for r in rects)
    by_hole = {h['reference']: h for h in holes}
    assert all(abs(by_hole[r]['datum_axis_difference_mm']) <= 0.001 for r in ('HEADPHONE0', 'MIXIN0', 'MIXOUT0'))
    assert all(abs(by_hole[r]['datum_axis_difference_mm']) < 0.02 for r in ('DIN1', 'DIN2', 'DIN3', 'DIN4'))
    assert all(abs(by_hole[r]['datum_axis_difference_mm'] + 0.166) < 1e-3 for r in ('CV0', 'GATE0'))

    def port(data, ref):
        return next(p for p in data['ports'] if p['reference'] == ref)

    def vertical(p):
        cut = p['actual_cutout']
        return (cut.get('axis_minus_hole_center_mm') or cut.get('axis_minus_rectangle_center_mm'))[1]
    ports = []
    for row in s14['ports']:
        ref = row['reference']
        a, b = row, port(s15, ref)
        entry = dict(reference=ref, axis_minus_cutout_center_mm=[vertical(a), vertical(b)],
                     plate_mesh_overlap_mm3=[a['actual_panel_material_intersection']['volume_mm3'],
                                             b['actual_panel_material_intersection']['volume_mm3']],
                     shoulder_or_flange_minus_plate_inner_mm=[a.get('shoulder_minus_panel_inner_plane_mm'),
                                                             b.get('shoulder_minus_panel_inner_plane_mm')])
        if 'body_envelope_clearance_to_rectangle_mm' in a:
            entry['rectangle_clearance_mm'] = [a['body_envelope_clearance_to_rectangle_mm'],
                                               b['body_envelope_clearance_to_rectangle_mm']]
        if 'native_bushing_outer_envelope_radial_margin_to_panel_mm' in a:
            entry['bushing_to_faceted_hole_wall_mm'] = [a['native_bushing_outer_envelope_radial_margin_to_panel_mm'],
                                                        b['native_bushing_outer_envelope_radial_margin_to_panel_mm']]
        ports.append(entry)
    by = {p['reference']: p for p in ports}
    for ref in ('POWER0', 'USB0'):
        assert abs(by[ref]['rectangle_clearance_mm'][0]['bottom'] + 0.081) < 1e-3
        assert abs(by[ref]['rectangle_clearance_mm'][1]['bottom']) < 1e-3
        assert by[ref]['plate_mesh_overlap_mm3'][0] > 1 and by[ref]['plate_mesh_overlap_mm3'][1] < 0.01
    for ref in ('HEADPHONE0', 'MIXIN0', 'MIXOUT0'):
        assert abs(by[ref]['axis_minus_cutout_center_mm'][1]) < 0.002
        assert abs(by[ref]['shoulder_or_flange_minus_plate_inner_mm'][1]) < 1e-3
    for ref in ('CV0', 'GATE0'):
        assert 0 < by[ref]['bushing_to_faceted_hole_wall_mm'][1] < 0.01
    assert not s15['summary']['native_ports_with_substantial_panel_material_overlap']
    assert not s15['summary']['native_port_case_intersections']
    hardware = [dict(reference=h['reference'],
                     washer_eccentricity_mm=h['parts']['black ABS washer proxy']['outer_center_eccentricity_mm'],
                     nut_eccentricity_mm=h['parts']['black PA6 nut proxy']['outer_center_eccentricity_mm'],
                     nose_tip_beyond_nut_mm=h['native_nose_tip_beyond_nut_front_mm'])
                for h in s15['audio_hardware']]
    assert all(h['washer_eccentricity_mm'] < 0.002 and h['nut_eccentricity_mm'] < 0.002 for h in hardware)
    key = lambda x: (x['io'], x['other'])
    before, after = {key(x) for x in c14['contact_pairs']}, {key(x) for x in c15['contact_pairs']}
    assert not after - before

    verification = dict(
        saved_scene_preservation=report('final-saved-scene-audit.json'),
        rear_openings=report('rear-openings-audit.json'),
        scene_portability=report('portable-scene-audit.json'),
        rear_seating_revision14=report('rear-seating-revision-14.json', kind=MEASURED),
        rear_seating=report('rear-seating-audit.json', kind=MEASURED),
        io_contacts_revision14=report('io-contacts-revision-14.json', kind=MEASURED, contact_pairs=len(before)),
        io_contacts=report('io-contacts.json', kind=MEASURED, contact_pairs=len(after), new_pairs=0),
        render_readonly=report('render-readonly-verification.json'),
        render_review=dict(report=rel(HERE / 'final-render-review.json'),
                           sha256=sha(HERE / 'final-render-review.json'), passed=True, view_count=len(renders)))
    summary = dict(
        schema=1, snapshot_date='2026-10-15', Blender_revision=15, KiCad_revision=12,
        scene=rel(scene), scene_sha256=change['stable_scene_sha256'], scene_bytes=scene.stat().st_size,
        baseline_scene_sha256=change['baseline_sha256'],
        correction='I/O component mounting plane raised onto the original rear-DXF height datum, 0.250 in '
                   '(6.350 mm) above the rear plate lower edge; the three audio nuts follow the jack axes.',
        evidence=dict(rectangular_cutout_bottoms=rects, circular_holes=holes,
                      interpretation='Both rectangles start at 0.250 in. Audio and DIN holes sit their modelled '
                                     'axis heights above it within 0.001 and 0.018 mm. Only the MJ-3536N holes '
                                     'differ, 0.166 mm below a 5.5 mm axis.',
                      nominal_feasible_window_mm='POWER/USB bodies clear their cutouts at 6.350 mm or above; '
                                                 '3.0 mm CV/GATE bushings clear 3.175 mm holes up to about '
                                                 '6.359 mm. Gravity rests the POWER/USB bodies on the cutout bottoms.'),
        change=dict(world_delta_mm=change['world_delta_mm'],
                    mounting_plane_mm=[change['mounting_plane_before_mm'], change['mounting_plane_after_mm']],
                    moved_objects=len(change['moved_objects']), moved_hardware=change['moved_hardware'],
                    conductors_end_blended=len(change['wires']),
                    conductor_blend_length_mm=change['wire_end_blend_length_mm'],
                    revision14_axial_datum_retained=True),
        ports=ports, columns='[revision 14, revision 15]', audio_hardware=hardware,
        io_contacts=dict(revision14_pairs=len(before), revision15_pairs=len(after), new_pairs=[],
                         removed_pairs=[list(k) for k in sorted(before - after)]),
        nut_finding='Raising only the board left the three audio nut proxies 0.081 mm off the jack axes and the '
                    'rear-opening verifier failed their bushing clearance in a local trial; the nuts thread onto '
                    'the jacks, so they move with the board.',
        verification=verification,
        unchanged=['Original Eagle files', 'KiCad revision-12 projects, copper, footprints and placement',
                   'All meshes, materials, keyframes, case, plate, washers and mainboard poses',
                   'Revision 14 axial plate datum', 'Blender revisions 7-14 baselines'],
        limitations=['The original CV/GATE holes imply a 5.334 mm (0.21 in) jack axis; the current MJ-3536N '
                     'drawing gives 5.5 mm, so the modelled bushings clear the holes by only about 0.005 mm.',
                     'USB envelope axis 5.31 mm remains a generic choice, not a recovered datum.',
                     'Historical part variants, terminal registration, tolerances and physical fit are unqualified.'],
        physical_fit_qualified=False)
    (HERE / 'independent-validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    docs = dict(summary)
    docs['validation_summary'] = dict(report=rel(HERE / 'independent-validation-summary.json'),
                                      sha256=sha(HERE / 'independent-validation-summary.json'))
    (REPO / 'docs/rear-height-datum-correction.json').write_text(json.dumps(docs, indent=2) + '\n')
    print(json.dumps(dict(passed=True, verification={k: v.get('passed', v.get('kind')) for k, v in verification.items()},
                          contacts=[len(before), len(after)]), indent=2))


main()
