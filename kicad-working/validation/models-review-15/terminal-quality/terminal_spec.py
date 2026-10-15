"""Terminal specification for the 12 previously pinless STEP models (revision 15).

Revision 15 adds formed legs (FORMED_LEGS) so that every terminal joins its body:
the drawings show these terminals leaving the edge of the base and turning down to
the board, while revisions 13-14 modelled only the part below the seat.

Revision 14 corrects four entries against the drawings (see CHANGED): the Alpha and
Panasonic overall tab dimensions run between the outer slot edges, PJ-202AH terminal 2
is the 2.50 mm blade, and the period CUI SDS-50J drawing (rev D, 2006) gives the pin
sections. The other eight entries are unchanged from revision 13.

Coordinates are millimetres in each model's own frame (KiCad model frame:
X across, Y = -footprint Y, Z up from the seating/mounting plane at Z=0).
Positions and lengths come from the manufacturer drawing dimensions; section
sizes not dimensioned are measured from the drawn geometry ("drawn") or are
assumptions ("assumed"). Each entry records that provenance.
"""

R = 'kicad-working/'
POT = R + 'visualization/blender-case-revision-7/quality-model-sources/potentiometer-quality/sources/'
ROT = R + 'visualization/blender-case-revision-7/quality-model-sources/rotary-quality/sources/'
REAR = R + 'visualization/blender-case-revision-7/quality-model-sources/rear-quality/source/'
CONN = R + 'validation/models-review-10/rear-connector-quality/sources/'
REV14 = R + 'validation/models-review-14/terminal-quality/sources/'
CHANGED = ('SDS50J', 'MJ3536N', 'CTS290', 'AlphaRV112', 'PanasonicEVU', 'NKKB12AB')

TIN = (0.74, 0.75, 0.76)


def blade(name, pad, x, y, w, t, length, face, tip='square', eyelet=None, top=0.4, note=''):
    """Flat terminal: width w lies in the face plane ('xz' => along X, 'yz' => along Y)."""
    return dict(name=name, pad=pad, kind='blade', x=x, y=y, w=w, t=t, z_top=top, z_tip=-length,
                face=face, tip=tip, eyelet=eyelet, note=note)


def pin(name, pad, x, y, d, length, top=0.4, note=''):
    return dict(name=name, pad=pad, kind='round', x=x, y=y, d=d, z_top=top, z_tip=-length, note=note)


def square(name, pad, x, y, a, length, top=0.4, note=''):
    return dict(name=name, pad=pad, kind='blade', x=x, y=y, w=a, t=a, z_top=top, z_tip=-length,
                face='xz', tip='square', eyelet=None, note=note)


NYS216_FRONT_PROFILE = [(8.0, 0.4), (8.0, -0.334), (7.912, -0.617), (7.912, -2.633), (8.0, -2.916), (8.0, -4.0),
                        (8.4, -4.0), (8.4, -2.916), (8.242, -2.407), (8.242, -0.843), (8.4, -0.334), (8.4, 0.4)]

MODELS = {
    'NYS216': dict(
        board='ioboard', source_step='ioboard/3dmodels/Revision8/rear-quality/NYS216_DrawingDerived_DetailedBody.step',
        output='NYS216_DrawingDerived_DetailedBody_Terminals.step',
        drawing=dict(file=REAR + 'nys-216-manufacturer.dxf', title='REAN NYS216 3102 ST 22 01 rev C (2007)'),
        provenance=dict(
            positions='PCB-layout dimensions: rows 4.00 + 2 x 6.35 behind the shoulder, rows 16.50 apart (x = +-8.25)',
            section='DXF drawn geometry: leg 1.30 wide (side view, semicircular tip), 0.40 thick with tear-drop waist (front view)',
            length='DXF drawn geometry: tip 4.00 below the body floor',
            conflict='The drawn side-view legs sit 0.875 mm behind the dimensioned holes; dimensions are used.'),
        terminals=[dict(name=f'{side}{i}', pad=pad, kind='nys_leg', x=side_x, y=y, w=1.30, t=0.40,
                        z_top=0.4, z_tip=-4.0)
                   for i, y in enumerate((4.00, 10.35, 16.70))
                   for side, side_x, pad in (('L', -8.25, ('SN', 'RN', 'TN')[i]), ('R', 8.25, ('S', 'R', 'T')[i]))]),
    'SDS50J': dict(
        board='ioboard', source_step='ioboard/3dmodels/Revision12/din-contact-quality/SDS50J_CorrectedContactPattern.step',
        output='SDS50J_CorrectedContactPattern_Terminals.step',
        drawing=dict(file=REV14 + 'sds50j-cui-rev-d-2006.pdf',
                     title='CUI SDS-50J rev D (2006-08-22); positions also on Same Sky SDS-J page 3 (2024-09-12)',
                     url='https://datasheet.octopart.com/SDS-50J-CUI-datasheet-86818.pdf'),
        provenance=dict(
            positions='Dimensioned PCB layout and side view: E at 2.5, pins 1-3 at 12.5, pins 4-5 at 15.0 from the front; x 2.5/5.0/7.5',
            section='Period drawing (2006): signal pins dimensioned 1.0 deep, drawn 0.5 wide; earth legs dimensioned '
                    '1.0 wide, drawn 0.32 thick, pointed (revision 13 used 0.70 x 1.00 and 1.00 x 0.21 drawn on the 2024 sheet)',
            length='Dimensioned 3.5 below the body (both drawings)',
            omitted='Locating pegs are not added: the 2006 part shows screw bosses, not pegs, and the Eagle package has no holes for them'),
        terminals=[blade('1', '1', 7.5, 12.5, 0.50, 1.00, 3.5, 'xz'),
                   blade('2', '2', 0.0, 12.5, 0.50, 1.00, 3.5, 'xz'),
                   blade('3', '3', -7.5, 12.5, 0.50, 1.00, 3.5, 'xz'),
                   blade('4', '4', 5.0, 15.0, 0.50, 1.00, 3.5, 'xz'),
                   blade('5', '5', -5.0, 15.0, 0.50, 1.00, 3.5, 'xz'),
                   blade('E1', 'PE', -2.5, 2.5, 1.00, 0.32, 3.5, 'xz', tip='point'),
                   blade('E2', 'PE@', 2.5, 2.5, 1.00, 0.32, 3.5, 'xz', tip='point')]),
    'MJ3536N': dict(
        board='ioboard', source_step='ioboard/3dmodels/Revision10/rear-connector-quality/MJ3536N_DrawingDerived_DetailedBody.step',
        output='MJ3536N_DrawingDerived_DetailedBody_Terminals.step',
        drawing=dict(file=CONN + 'mj3536n-2020.pdf', title='CUI MJ-3536N rev 1.02 (2020; mechanics unchanged since 2005)'),
        provenance=dict(
            positions='Dimensioned: terminal 1 at 2.3, terminal 3 at 13.5 (5.2 off axis), terminal 2 at 16.0 from the shoulder',
            section='Dimensioned widths 2.2 (terminal 1) and 2.0 (terminal 3); drawn thicknesses 0.40 / 0.20 / 0.34; '
                    'terminal 2 width assumed equal to terminal 1 (hidden in the front view)',
            length='Dimensioned 4.5 below the body; dia 1.0 eyelets (3 places) in the rounded ends'),
        terminals=[blade('1', 'SLEEVE', 0.0, 2.3, 2.2, 0.40, 4.5, 'xz', tip='round', eyelet=1.0),
                   blade('2', 'TIP', 0.0, 16.0, 2.2, 0.20, 4.5, 'xz', tip='round', eyelet=1.0),
                   blade('3', 'TIPSHUNT', 5.2, 13.5, 2.0, 0.34, 4.5, 'yz', tip='round', eyelet=1.0)]),
    'PJ202AH': dict(
        board='ioboard', source_step='ioboard/3dmodels/Revision10/rear-connector-quality/PJ202AH_DrawingDerived_DetailedBody_Corrected.step',
        output='PJ202AH_DrawingDerived_DetailedBody_Terminals.step',
        drawing=dict(file=CONN + 'pj202ah-2015.pdf', title='CUI PJ-202AH (2015-01-08); Same Sky PJ-202AH (2025-07-24)'),
        provenance=dict(
            positions='Dimensioned: terminal 2 at 7.7, terminal 3 at 10.7 (4.7 off axis), terminal 1 at 13.7 behind the front face',
            section='Terminal 1 3.00 and terminal 2 2.50 wide (dimensioned on the 2025 front view, nested outlines drawn '
                    'in 2015; layout slots 3.5 and 3.0); terminal 3 2.50; drawn 0.40 thickness; dia 1.50 eyelet',
            length='Dimensioned 3.5 below the body'),
        terminals=[blade('1', 'P$1', 0.0, -13.7, 3.0, 0.40, 3.5, 'xz', tip='round'),
                   blade('2', 'P$2', 0.0, -7.7, 2.5, 0.40, 3.5, 'xz', tip='round'),
                   blade('3', 'P$3', -4.7, -10.7, 2.5, 0.40, 3.5, 'yz', tip='round', eyelet=1.5)]),
    'USB': dict(
        board='ioboard', source_step='ioboard/3dmodels/Revision6/rear-body-illustrations/USB_TypeB-body-illustration.step',
        output='USB_TypeB-body-illustration_Terminals.step',
        drawing=dict(file='FCI 61729 drawing rev V (2008), via RS 61729-0011BLF product sheet',
                     title='FCI/Amphenol 61729 USB receptacle B type (matches footprint PN61729)'),
        provenance=dict(
            positions='Dimensioned: board locks 10.28 behind the mating face, signal rows 2.71 and 4.71 behind them, '
                      'pitch 2.50, lock holes 12.04 apart',
            section='Drawn 0.40 square signal pins; board-lock fork drawn about 2.4 wide, assumed 0.30 thick with a 0.6 slot',
            length='Dimensioned 2.84 (signal) and 2.63 (board lock) below the seating plane',
            identity='Original BOM names Kobiconn 154-2442-E; its drawing could not be retrieved. The footprint is PN61729.'),
        terminals=[square('1', '1', 1.25, 14.99, 0.40, 2.84), square('2', '2', -1.25, 14.99, 0.40, 2.84),
                   square('3', '3', -1.25, 12.99, 0.40, 2.84), square('4', '4', 1.25, 12.99, 0.40, 2.84),
                   blade('L1', 'M2', -6.02, 10.28, 2.4, 0.30, 2.63, 'yz', tip='fork'),
                   blade('L2', 'P$2', 6.02, 10.28, 2.4, 0.30, 2.63, 'yz', tip='fork')]),
    'MC78M05': dict(
        board='ioboard', source_step='ioboard/3dmodels/Revision10/heatsink-fit-research/MC78M05_TO220_BentBack_PhotoQualified_BodyOnly.step',
        output='MC78M05_TO220_BentBack_PhotoQualified_Terminals.step',
        drawing=dict(file=R + 'validation/models-review-10/heatsink-fit-research/sources/onsemi-mc78m00.pdf',
                     title='onsemi TO-220 case 221AB issue A (2010)'),
        provenance=dict(
            section='Nominal of printed ranges: D 0.76 wide, J 0.55 thick, L 1.335 shoulder width, G 2.54 pitch',
            path='Lead plane R 2.415 above the tab back (z 3.795); leaves the lead face at y 3.0, 90 degree bend '
                 '(1.0 centreline radius, assumed) above the holes at y -2.54; total length K 13.485 from the body',
            limits='Bend radius, shoulder length (1.0) and formed path are illustration assumptions, like the body pose'),
        terminals=[dict(name=n, pad=p, kind='bent_lead', x=x, y_body=3.0, y_hole=-2.54, z_plane=1.38 + 2.415,
                        w=0.76, t=0.55, shoulder_w=1.335, shoulder_len=1.0, bend_r=1.0, length=13.485)
                   for n, p, x in (('1', 'IN', -2.54), ('2', 'GND', 0.0), ('3', 'OUT', 2.54))]),
    'LPTC': dict(
        board='mainboard', source_step='mainboard/3dmodels/Revision6/misc-body-illustrations/Microohm_LPTC12T21001_ApproxBody.step',
        output='Microohm_LPTC12T21001_ApproxBody_Terminals.step',
        drawing=dict(file='none recovered', title='Micro-Ohm LPTC12T21001 (no manufacturer mechanical data found)'),
        provenance=dict(
            all='ASSUMED: no manufacturer drawing exists in the project or online (micro-ohm.com page returns 404). '
                'Axial dia 0.5 tinned leads leave the body ends at its axis, bend (0.75 centreline radius) into the '
                'existing holes and protrude 1.5 below the board.'),
        terminals=[dict(name=n, pad=p, kind='axial_lead', x_body=sx * 3.5, x_hole=sx * 5.08, z_axis=1.67,
                        d=0.5, bend_r=0.75, z_tip=-3.1)
                   for n, p, sx in (('1', '1', -1), ('2', '2', 1))]),
    'CTS290': dict(
        board='mainboard', source_step='mainboard/3dmodels/Revision8/rotary-quality/CTS_290VAA5F201B2_DetailedCandidate.step',
        output='CTS_290VAA5F201B2_DetailedCandidate_Terminals.step',
        drawing=dict(file=ROT + 'cts290-datasheet.pdf', title='CTS Series 290 MC-290V (2025-10-21 rev A)'),
        provenance=dict(
            positions='Dimensioned: A/C/B at 2.5 pitch 7.5 from centre, switch pins 5.00 apart 7.0 from centre, '
                      'mounting tabs 11.10 apart',
            section='Dimensioned 0.8 +-0.1 pin width; 0.3 thickness and 0.6 x 2.2 tab section assumed from the 1.8 x 2.6 slots',
            length='Dimensioned 3.5 below the mounting surface'),
        terminals=[blade('A', 'A', -2.5, -7.5, 0.8, 0.3, 3.5, 'xz'), blade('C', 'C', 0.0, -7.5, 0.8, 0.3, 3.5, 'xz'),
                   blade('B', 'B', 2.5, -7.5, 0.8, 0.3, 3.5, 'xz'),
                   blade('S1', 'SW1', -2.5, 7.0, 0.8, 0.3, 3.5, 'xz'), blade('S2', 'SW2', 2.5, 7.0, 0.8, 0.3, 3.5, 'xz'),
                   blade('T1', 'P$2', -5.55, 0.0, 2.2, 0.6, 3.5, 'yz'), blade('T2', 'P$1', 5.55, 0.0, 2.2, 0.6, 3.5, 'yz')]),
    'AlphaRV112': dict(
        board='mainboard', source_step='mainboard/3dmodels/Revision9/potentiometer-quality/Alpha_RV112BCF40_25_DetailedCandidate.step',
        output='Alpha_RV112BCF40_25_DetailedCandidate_Terminals.step',
        drawing=dict(file=POT + 'alpha-insulated-rv112b-primary.pdf', title='Alpha RV112BCF-40 11 mm dual snap-in'),
        provenance=dict(
            positions='Dimensioned: six pins at 2.0 pitch, 11.0 from the tab line; snap-in tab slots 2.0 wide with 13.0 '
                      'across their outer edges, so tab centres at +-5.5 (revision 13 misread 13.0 as the centre spacing)',
            section='Drawn 0.8 pin width; 0.3 thickness and 0.6 x 1.9 tab section assumed from the 2.0 x 2.1 slots',
            length='Dimensioned 3.5 (pins) and 3.2 (tabs) below the mounting surface'),
        terminals=[blade(n, p, x, -11.0, 0.8, 0.3, 3.5, 'xz')
                   for n, p, x in (('2A', '2A', -5.0), ('1A', '1A', -3.0), ('1B', '1B', -1.0),
                                   ('2B', '2B', 1.0), ('3B', '3B', 3.0), ('3A', '3A', 5.0))]
                  + [blade('M1', 'M1', -5.5, 0.0, 1.9, 0.6, 3.2, 'yz'), blade('M2', 'M2', 5.5, 0.0, 1.9, 0.6, 3.2, 'yz')]),
    'PanasonicEVU': dict(
        board='mainboard', source_step='mainboard/3dmodels/Revision9/potentiometer-quality/Panasonic_EVUF2LFL3_DetailedCandidate.step',
        output='Panasonic_EVUF2LFL3_DetailedCandidate_Terminals.step',
        drawing=dict(file=POT + 'panasonic-evu-primary-mirror.pdf', title='Panasonic EVUF2L No. 8 (2005)'),
        provenance=dict(
            positions='Dimensioned piercing plan: #1-#3 at 2.5 pitch 7.00 from the tab line; tab slots 1.6 wide with 10.60 '
                      'across their outer edges, so tab centres at +-4.50 (revision 13 misread 10.60 as the centre spacing)',
            section='Sister-type dimension 0.8 terminal width; 0.3 thickness and 0.6 x 2.0 tab section assumed from 1.6 x 2.2 slots',
            length='Dimensioned 3.7 below the mounting surface'),
        terminals=[blade('1', '1', -2.5, -7.0, 0.8, 0.3, 3.7, 'xz'), blade('2', '2', 0.0, -7.0, 0.8, 0.3, 3.7, 'xz'),
                   blade('3', '3', 2.5, -7.0, 0.8, 0.3, 3.7, 'xz'),
                   blade('M1', 'M1', -4.50, 0.0, 2.0, 0.6, 3.7, 'yz'), blade('M2', 'M2', 4.50, 0.0, 2.0, 0.6, 3.7, 'yz')]),
    'NKKB12AB': dict(
        board='mainboard', source_step='mainboard/3dmodels/Revision8/rotary-quality/NKK_B12AB_DetailedCandidate.step',
        output='NKK_B12AB_DetailedCandidate_Terminals.step',
        drawing=dict(file=ROT + 'nkk-btoggles.pdf', title='NKK Series B B12AB straight PC with bracket'),
        provenance=dict(
            positions='Reference dimensions: pins 2.54 pitch 1.0 off centre; bracket legs 10.16 apart in columns 2.54 apart',
            section='Dimensioned 0.6 dia pins; bracket legs 0.6 wide x 0.4 thick',
            length='Reference 3.1 below the body'),
        terminals=[pin('1', '1', -1.0, 2.54, 0.6, 3.1), pin('2', '2', -1.0, 0.0, 0.6, 3.1), pin('3', '3', -1.0, -2.54, 0.6, 3.1)]
                  + [blade(n, p, x, y, 0.6, 0.4, 3.1, 'xz')
                     for n, p, x, y in (('M1', 'M1', -1.0, -5.08), ('M2', 'M2', 1.54, -5.08),
                                        ('M3', 'M3', 1.54, 5.08), ('M4', 'M4', -1.0, 5.08))]),
    'Grayhill25L': dict(
        board='mainboard', source_step='mainboard/3dmodels/Revision8/rotary-quality/Grayhill_25LB22H_DetailedCandidate.step',
        output='Grayhill_25LB22H_DetailedCandidate_Terminals.step',
        drawing=dict(file=ROT + 'grayhill25l.pdf', title='Grayhill Series 25L'),
        provenance=dict(
            positions='Dimensioned: 0.100 in pitch, row 0.500 in from the shaft centre',
            section='Dimensioned 0.025 in (0.64) square pins',
            length='Dimensioned 0.250 in (6.35) below the base',
            omitted='MT1-MT4 belong to the separate 25J5155 mounting bracket; no drawing, so no legs are added'),
        terminals=[square(n, p, x, -12.7, 0.64, 6.35, top=1.14)
                   for n, p, x in (('8', 'P$8', -5.08), ('4', 'P$4', -2.54), ('2', 'P$2', 0.0),
                                   ('1', 'P$1', 2.54), ('C', 'C', 5.08))]),
}


# Terminals that leave the body edge and turn down to the board. Each gets a formed leg with
# its own cross-section, running horizontally from the pin into the nearest body edge at the
# lowest height where body material exists there (leg height and bend are assumptions; the
# drawings show the path but do not dimension it).
FORMED_LEGS = {
    'SDS50J': dict(terminals=('4', '5'),
                   source='Pins 4 and 5 drop from the rear of the housing behind the outer contacts '
                          '(2006 CUI rev D side view)'),
    'MJ3536N': dict(terminals=('2', '3'),
                    source='Tip and tip-shunt blades leave the housing walls (rev 1.02 side and front views)'),
    'CTS290': dict(terminals=('A', 'C', 'B', 'S1', 'S2', 'T1', 'T2'),
                   source='Encoder and switch terminals leave the base edge and bend down; bracket tabs leave '
                          'the can sides (MC-290V views)'),
    'AlphaRV112': dict(terminals=('2A', '1A', '1B', '2B', '3B', '3A'),
                       source='The six terminals leave the bottom edge of the rear wafers and run to the pin row '
                              '11.0 from the tab line (RV112BCF-40 front view, 8.7 to the body edge)'),
    'PanasonicEVU': dict(terminals=('1', '2', '3'),
                         source='Terminals leave the rear wafer edge and turn down at the 7.00 piercing row '
                                '(EVUF2L No. 8)'),
    'NKKB12AB': dict(terminals=('M1', 'M2', 'M3', 'M4'),
                     source='Bracket legs leave the cage sides and step out to the 10.16 mm leg spacing '
                            '(Series B straight PC with bracket)'),
}
