"""Write the revision-14 validation summary and docs/rear-plate-datum-correction.json.

Every number comes from a report in this folder, the current I/O PCB and
footprint files or the received-mesh terminal sections, except the SDS-50J
PCB layout, which is read from the retained manufacturer drawing (page 3) and
marked so. Asserts the outcomes that the README files state.

Run:  python3 -I kicad-working/visualization/blender-case-revision-14/verification/summarize_revision.py
"""
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REV = HERE.parent
REPO = HERE.parents[3]
WORK = REPO / 'kicad-working'
MEASURED = 'measurement; outcomes asserted by summarize_revision.py'


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
    change = load(REV / 'revision-14-change-record.json')
    scene = REV / 'x0xb0x-populated-with-case.blend'
    baseline = REV.parent / 'blender-case-revision-13/x0xb0x-populated-with-case.blend'
    assert sha(scene) == change['stable_scene_sha256'] == project['blender_sha256']
    assert sha(baseline) == change['baseline_sha256']
    saved, portable = load(HERE / 'final-saved-scene-audit.json'), load(HERE / 'portable-scene-audit.json')
    openings = load(HERE / 'rear-openings-audit.json')
    s13, s14 = load(HERE / 'rear-seating-revision-13.json'), load(HERE / 'rear-seating-audit.json')
    c13, c14 = load(HERE / 'io-contacts-revision-13.json'), load(HERE / 'io-contacts.json')
    downloaded = load(HERE / 'downloaded-din-plate-datum.json')
    renders, readonly = load(REV / 'render-records.json'), load(HERE / 'render-readonly-verification.json')
    review = load(HERE / 'final-render-review.json')
    assert saved['passed'] and portable['passed'] and openings['passed'] and readonly['passed'] and review['passed']
    assert portable['check_count'] == 106 and openings['check_count'] == 44 and openings['ray_count'] == 974
    assert all(r['source_scene_sha256'] == change['stable_scene_sha256'] for r in renders) and len(renders) == 7
    assert review['image_sha256'] == {r['image']: r['sha256'] for r in renders}
    for data in (s13, s14, c13, c14):
        assert data['scene_bytes_unchanged'] if 'scene_bytes_unchanged' in data else data['saved_scene_bytes_unchanged']
    assert s13['scene_sha256'] == change['baseline_sha256'] and s14['scene_sha256'] == change['stable_scene_sha256']
    assert c13['scene_sha256'] == change['baseline_sha256'] and c14['scene_sha256'] == change['stable_scene_sha256']

    # Original Eagle evidence carried by the current I/O PCB.
    board = (WORK / 'ioboard/ioboard.kicad_pcb').read_text()
    strip = [tuple(map(float, m.groups())) for m in re.finditer(
        r'\(gr_line\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*'
        r'\(stroke\s*\(width [-\d.]+\)\s*\(type \w+\)\s*\)\s*\(layer "Edge\.Cuts"\)', board)]
    strip_y = sorted({y for _, y1, _, y2 in strip for y in (y1, y2) if y > 0})
    origins = {}
    for m in re.finditer(r'\(footprint "ioboard-import-fps:(REAN_1_4STERO|CP-2350|MJ-3536N)"\s*\(layer[^)]*\)\s*'
                         r'\(uuid[^)]*\)\s*\(at ([-\d.]+) ([-\d.]+)', board):
        ref = re.search(r'"Reference" "(\w+)"', board[m.end():m.end() + 600]).group(1)
        origins[ref] = float(m.group(3))
    assert strip_y[:2] == [0.508, 2.159], strip_y
    assert all(origins[r] == 0.508 for r in ('HEADPHONE0', 'MIXIN0', 'MIXOUT0'))
    assert all(origins[r] == 0.0 for r in ('DIN1', 'DIN2', 'DIN3', 'DIN4', 'CV0', 'GATE0'))

    # DIN pin patterns measured from the connector front datum (mm).
    fp = (WORK / 'ioboard/ioboard-import-fps.pretty/CP-2350.kicad_mod').read_text()
    eagle = {p: (float(x), -float(y)) for p, x, y in
             re.findall(r'\(pad "([^"]+)" thru_hole \w+\s*\(at ([-\d.]+) ([-\d.]+)', fp)}
    datasheet = {'1': (7.5, 12.5), '2': (0.0, 12.5), '3': (-7.5, 12.5), '4': (5.0, 15.0),
                 '5': (-5.0, 15.0), 'PE': (-2.5, 2.5), 'PE@': (2.5, 2.5)}
    terminals = load(WORK / 'validation/models-review-12/downloaded-terminal-sections.json')
    received = [tuple(c['center_xy_mm']) for c in terminals['sections'][0]['components']]
    pins = []
    for pad, (ex, ey) in sorted(eagle.items()):
        dx, dy = datasheet[pad]
        near = min(received, key=lambda c: math.dist(c, (dx, dy + 0.2)))
        pins.append(dict(pad=pad, eagle_pad_mm=[ex, ey], datasheet_layout_mm=[dx, dy],
                         received_terminal_mm=list(near),
                         eagle_minus_datasheet_mm=[round(ex - dx, 4), round(ey - dy, 4)],
                         received_minus_datasheet_mm=[round(near[0] - dx, 4), round(near[1] - dy, 4)]))
    assert {p['received_minus_datasheet_mm'][1] for p in pins} == {0.2}
    assert all(p['received_minus_datasheet_mm'][0] == 0 for p in pins)
    assert max(math.hypot(*p['eagle_minus_datasheet_mm']) for p in pins) < 0.19

    def port(data, ref):
        return next(p for p in data['ports'] if p['reference'] == ref)
    ports = []
    for row in s13['ports']:
        ref = row['reference']
        a, b = row, port(s14, ref)
        ports.append(dict(
            reference=ref,
            shoulder_or_flange_minus_plate_inner_mm=[a.get('shoulder_minus_panel_inner_plane_mm'),
                                                    b.get('shoulder_minus_panel_inner_plane_mm')],
            mating_face_beyond_plate_exterior_mm=[a['mating_face_projection_beyond_panel_exterior_mm'],
                                                  b['mating_face_projection_beyond_panel_exterior_mm']],
            plate_mesh_overlap_mm3=[a['actual_panel_material_intersection']['volume_mm3'],
                                    b['actual_panel_material_intersection']['volume_mm3']],
            rectangle_bottom_clearance_mm=[x.get('body_envelope_clearance_to_rectangle_mm', {}).get('bottom')
                                           for x in (a, b)]))
    by = {p['reference']: p for p in ports}
    for ref in ('HEADPHONE0', 'MIXIN0', 'MIXOUT0'):
        assert abs(by[ref]['shoulder_or_flange_minus_plate_inner_mm'][0] - 0.508) < 1e-3
        assert abs(by[ref]['shoulder_or_flange_minus_plate_inner_mm'][1]) < 1e-3
        assert by[ref]['plate_mesh_overlap_mm3'][0] > 100 and by[ref]['plate_mesh_overlap_mm3'][1] < 0.01
    for ref in ('DIN1', 'DIN2', 'DIN3', 'DIN4', 'CV0', 'GATE0'):
        assert abs(by[ref]['shoulder_or_flange_minus_plate_inner_mm'][1] + 0.508) < 1e-3
    for ref in ('POWER0', 'USB0'):
        assert by[ref]['rectangle_bottom_clearance_mm'][0] == by[ref]['rectangle_bottom_clearance_mm'][1]
    assert not s14['summary']['native_port_case_intersections']
    nose = [h['native_nose_tip_beyond_nut_front_mm'] for h in s14['audio_hardware']]
    assert all(abs(x - 0.7252) < 1e-3 for x in nose)

    key = lambda x: (x['io'], x['other'])
    before = {key(x) for x in c13['contact_pairs']}
    after = {key(x) for x in c14['contact_pairs']}
    assert not after - before
    flange = {r['variant']: r['max_signed_flange_penetration_mm'] for r in downloaded['variants']}
    assert flange['pin-fitted-original'] == 0.12 and flange['pin-fitted-panel-datum'] == -0.388

    verification = dict(
        saved_scene_preservation=report('final-saved-scene-audit.json'),
        rear_openings=report('rear-openings-audit.json'),
        scene_portability=report('portable-scene-audit.json'),
        rear_seating_revision13=report('rear-seating-revision-13.json', kind=MEASURED),
        rear_seating=report('rear-seating-audit.json', kind=MEASURED),
        io_contacts_revision13=report('io-contacts-revision-13.json', kind=MEASURED, contact_pairs=len(before)),
        io_contacts=report('io-contacts.json', kind=MEASURED, contact_pairs=len(after), new_pairs=0),
        downloaded_din_plate_datum=report('downloaded-din-plate-datum.json', kind=MEASURED),
        render_readonly=report('render-readonly-verification.json'),
        render_review=dict(report=rel(HERE / 'final-render-review.json'),
                           sha256=sha(HERE / 'final-render-review.json'), passed=True, view_count=len(renders)))
    summary = dict(
        schema=1, snapshot_date='2026-10-15', Blender_revision=14, KiCad_revision=12,
        scene=rel(scene), scene_sha256=change['stable_scene_sha256'], scene_bytes=scene.stat().st_size,
        baseline_scene_sha256=change['baseline_sha256'],
        correction='Rear plate inner face moved onto the original Eagle I/O detached Dimension strip datum '
                   '(KiCad Y=+0.508 mm, the three REAN footprint origins) by moving only the I/O board '
                   'placement 0.508 mm toward the case front.',
        evidence=dict(
            original_eagle_detached_strip_y_mm=strip_y, strip_depth_mm=round(strip_y[1] - strip_y[0], 4),
            original_plate_thickness_mm=1.5748, strip_width_mm=222.25, plate_width_mm=217.932,
            footprint_origin_y_mm={r: origins[r] for r in sorted(origins)},
            manuals='Original finishing manual attaches the rear plate through the three 1/4-inch jacks; '
                    'I/O manual step 9 keeps DIN faces flush with the PCB edge.',
            interpretation='Plate clamped against the audio shoulders; shoulders at the footprint origin '
                           '(2007 NYS216 drawing registration); strip drawn from exactly that line.'),
        change=dict(world_delta_mm=change['world_delta_mm'], moved_objects=len(change['moved_objects']),
                    conductors_end_blended=len(change['wires']),
                    conductor_blend_length_mm=change['wire_end_blend_length_mm'],
                    hidden_strip_reference_follows_board=True),
        seating=dict(columns='[revision 13, revision 14]', ports=ports, audio_nose_tip_beyond_nut_mm=nose),
        io_contacts=dict(revision13_pairs=len(before), revision14_pairs=len(after), new_pairs=[],
                         removed_pairs=[list(k) for k in sorted(before - after)]),
        din_pin_patterns=dict(
            frame='x across connector, y = distance from connector front datum, mm',
            datasheet_source='Same Sky SDS-J datasheet 09/12/2024 page 3 (retained PDF '
                             'kicad-working/visualization/blender-case-revision-7/quality-model-sources/'
                             'rear-quality/source/sds50j.pdf); values read from the drawing',
            pins=pins, received_rows_offset_from_datasheet_mm=0.2,
            received_minus_datasheet_flange_thickness_mm=0.2,
            datasheet_locator_holes='2 x dia 2.4 mm at x=+-7.5, y=7.5; absent from the original Eagle package',
            interpretation='Received terminals equal the datasheet pattern measured from the back of a 0.2 mm '
                           'thicker flange. Eagle pads are an imperial-grid approximation within 0.18 mm, inside '
                           'the +-0.3 mm part tolerance, so pads cannot fix the axial datum.'),
        downloaded_din_flange_penetration_mm=flange,
        verification=verification,
        unchanged=['Original Eagle files', 'KiCad revision-12 projects, copper, footprints and placement',
                   'All meshes, materials, keyframes, case, plate, hardware and mainboard poses',
                   'Blender revisions 7-13 baselines'],
        limitations=['Reading the strip as the plate section is an interpretation; it is 4.318 mm wider than the plate.',
                     'Current-family NYS216 lead depths would put its body front near KiCad Y=+0.158 mm; '
                     'that alternative needs a model re-registration and is untested.',
                     'POWER0/USB0 bodies remain 0.081 mm below their rectangular cutouts (vertical datum).',
                     'The 0.167 mm MJ-3536N versus NYS216 axis-height disagreement remains.',
                     'Historical part variants, terminal registration, tolerances and physical fit are unqualified.'],
        physical_fit_qualified=False)
    (HERE / 'independent-validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    docs = dict(summary)
    docs['validation_summary'] = dict(report=rel(HERE / 'independent-validation-summary.json'),
                                      sha256=sha(HERE / 'independent-validation-summary.json'))
    (REPO / 'docs/rear-plate-datum-correction.json').write_text(json.dumps(docs, indent=2) + '\n')
    print(json.dumps(dict(passed=True, verification={k: v.get('passed') for k, v in verification.items()},
                          contacts=[len(before), len(after)], flange=flange), indent=2))


main()
