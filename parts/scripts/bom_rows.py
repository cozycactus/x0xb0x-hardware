"""x0xb0x parts order rows (one x0xb0x: mainboard + I/O board + mechanical).

Mouser stock and prices were re-read on 2026-11-05: see the block at the end of
this file. Other availability figures were read on 2026-10-17 from the named
distributor page, unless the cell says otherwise. "Mouser" figures are US-site stock
(read in a browser session); "Farnell" figures are uk.farnell.com stock;
"LCSC" figures are lcsc.com (marketplace "Other Suppliers" offers are
labelled as such). Mouser, Digi-Key and TME put up bot checks during the
session, so some rows could not be re-checked live; those say so.
"""

COLUMNS = ['line', 'section', 'description', 'qty', 'references', 'original_part',
           'footprint', 'proposed_mfr', 'proposed_mpn', 'distributor_pn', 'availability',
           'status', 'fit_flag', 'notes', 'sources']

M = 'https://www.mouser.com/c/?q='
MD = 'https://www.mouser.com/ProductDetail/'
LC = 'https://www.lcsc.com/search?q='
FN = 'https://uk.farnell.com/search?st='
BOM_PDF = ('kicad-working/validation/expanded-bom-review/sources/'
           'x0x-billofmaterials-adawiki-user-print.pdf')
PARTS_PAGE = ('kicad-working/visualization/blender-case-revision-7/'
              'bom-parts/original-parts-page-mirror.html')
MIDIBOX = 'https://forum.midibox.org/t/x0xb0x-rare-parts/9689'
RES_FP = '0207 axial, mounted standing; pads 5.08 mm apart, 1.0 mm drill'

ROWS = []


def row(section, description, qty, references, original_part, footprint, mfr, mpn, dpn,
        availability, status, fit_flag='none', notes='', sources='', check_refs=True):
    ROWS.append(dict(line=len(ROWS) + 1, section=section, description=description, qty=qty,
                     references=references, original_part=original_part, footprint=footprint,
                     proposed_mfr=mfr, proposed_mpn=mpn, distributor_pn=dpn,
                     availability=availability, status=status, fit_flag=fit_flag,
                     notes=notes, sources=sources, check_refs=check_refs))


# ---------------------------------------------------------------- resistors
RES = [
    ('10 ohm 5%', 'R164 R186', '10R', '42,882'),
    ('22 ohm 5%', 'R20 R150', '22R', '78,867'),
    ('27 ohm 5%', 'R6 R7', '27R', '7,843'),
    ('100 ohm 5%', 'R1 R95 R130 R132 R136 R152', '100R', '52,192'),
    ('220 ohm 5%', 'R13 R14 R15 R18 R19', '220R', '10,190'),
    ('470 ohm 5%', 'R12', '470R', '7,438'),
    ('1K 5%', 'R2 R17 R137 R161', '1K', '53,923'),
    ('1.5K 5%', 'R8', '1K5', '13,578'),
    ('1.8K 5%', 'R179', '1K8', '76,453'),
    ('2.2K 5%', 'R21 R22 R23 R24 R67 R68 R69 R70 R71 R98 R104 R107 R108 R124 R125 R126 R133 R162 R178',
     '2K2', '22,274'),
    ('4.7K 5%', 'R9 R135', '4K7', '14,031'),
    ('6.8K 5%', 'R3', '6K8', '12,621'),
    ('10K 5% (40 of them are LED series resistors)',
     'R10 R11 R34 R36 R47 R61 R64 R65 R94 R96 R97 R101 R105 R109 R112 R115 R116 R142 R143 R144 R145 '
     'R148 R149 R157 R158 R160 R201-R234 R237-R270', '10K', '118,300'),
    ('22K 5%', 'R45 R60 R110 R111 R117 R120 R129 R134 R146 R151', '22K', '6,914'),
    ('33K 5%', 'R159', '33K', '27,279'),
    ('47K 5%', 'R46 R119 R127 R155', '47K', '11,334'),
    ('68K 5%', 'R138', '68K', '6,894'),
    ('100K 5%', 'R25 R26 R27 R28 R35 R59 R66 R72 R73 R92 R93 R99 R102 R113 R114 R118 R122 R139 R140 '
     'R141 R153 R154 R156 R165', '100K', '17,559'),
    ('220K 5%', 'R62 R63 R103 R121 R128 R131 R235 R236', '220K', '4,062'),
    ('1MEG 5%', 'R91 R200', '1M', '16,471'),
    ('2.4K 1%', 'R5', '2K4', '18,735'),
    ('5.6K 1%', 'R4', '5K6', '8,306'),
    ('200K 1%', 'R74-R90', '200K', '619 (+80,000 expected 2026-12-08)'),
]
for desc, refs, code, stock in RES:
    n = 0
    for tok in refs.split():
        if '-' in tok:
            a, b = tok.split('-')
            n += int(b[1:]) - int(a[1:]) + 1
        else:
            n += 1
    fp = RES_FP
    flag = 'none'
    if any(r in refs.split() for r in ('R96', 'R97', 'R98', 'R115')):
        fp += '; R96 R97 R98 R115 standing on 2.54 mm pads (0207_2V)'
        flag = 'CHECK lead bend at 2.54 mm pads (R96 R97 R98 R115)'
    if 'R137' in refs or 'R201' in refs:
        fp += '; R137/R232 lie flat on 10.16 mm, R234 on 15.24 mm'
    note = ''
    if code == '100R':
        note = 'R16 is on line 115, at 150 ohm. The BOM PDF and the PCB say 100 ohm; the owner chose 150 ohm on 2026-11-05.'
    if code == '10K':
        note = ('Parts page: the 40 LED resistors (R203 R204 ... R268) may change with LED type '
                'and brightness; 10K suits the diffused red LED in line 72. Order 100 (cut-tape price break).')
    row('Resistors', desc + ' resistor', n, refs, 'Generic 5% (BOM)', fp,
        'YAGEO', f'MFR-25FBF52-{code}', f'Mouser 603-MFR-25FBF52-{code}',
        f'Mouser {stock} in stock', 'in stock', flag,
        note or '1/4 W 1% metal film, body 2.4 x 6.3 mm (Mouser parametrics); one family for every value.',
        M + f'MFR-25FBF52-{code}')

row('Resistors', '1.5MEG 5% resistor', 1, 'R123', 'Generic', RES_FP,
    'YAGEO', 'MFR-25FTE52-1M5', 'Mouser 603-MFR-25FTE52-1M5', 'Mouser 7,200 in stock',
    'in stock', 'none',
    'MFR-25FBF52-1M5 is not stocked (Mouser lists it non-stocked). Alternative KOA Speer '
    'MF1/4DCT52R1504F, Mouser 4,068 in stock.',
    M + 'MFR-25FTE52-1M5 ; ' + MD + 'KOA-Speer/MF1-4DCT52R1504F')
row('Resistors', '24K 1% resistor (BOM) / 27K on the PCB', 1, 'R106',
    'Generic; BOM PDF and parts page 24.0K 1%, PCB value 27K', RES_FP,
    'YAGEO', 'MFR-25FBF52-24K (and MFR-25FBF52-27K)', 'Mouser 603-MFR-25FBF52-24K / -27K',
    'Mouser 78,972 / 15,157 in stock', 'in stock', 'none',
    'Value conflict recorded in docs/expanded-bom-crosscheck.json; buy both (cents) and decide at '
    'assembly. Open question Q1.',
    M + 'MFR-25FBF52-24K ; ' + BOM_PDF)

# --------------------------------------------------------- PTC / trimmers / pots
row('Resistors', '1K PTC thermistor (VCO tempco)', 2, 'R100A R100B',
    'Micro-Ohm LPTC12T21001 (1/6 W, 1k, T2 = +3000 ppm/K)',
    'R-7,5: axial, pads 10.16 mm apart, 1.0 mm drill; original body 3.7 x 1.9 mm',
    'Panasonic (SMD) or generic THT tempco', 'ERA-S33J102V (0603, 1k, +3300 ppm/K) or a THT 1k '
    '+3500 ppm/K PTC', 'LCSC C20544305',
    'LPTC12 not found at Mouser or LCSC; ERA-S33J102V LCSC 0 in stock (orderable, $1.68); '
    'THT 1k 3500 ppm part listed at Electrokit (not checked for stock)',
    'hunt', 'CHECK TC differs (+3300/+3500 vs +3000 ppm/K); SMD part needs wire tails on 10.16 mm pads',
    'The tempco compensates the VCO expo converter; a different TC shifts tracking over temperature. '
    'Recheck tuning drift after warm-up. Mouser/Digi-Key stock of ERA-S33J102V not checked (bot block).',
    'kicad-working/validation/models-review-20/ptc-quality/sources/'
    'micro-ohm-precision-film-sensor-user.pdf ; ' + LC + 'ERA-S33J102V ; '
    'https://www.electrokit.com/ptc-motstand-1kohm-3500ppm ; '
    'http://www.openmusiclabs.com/2015/03/temperature-compensation-of-analog-exponential-converters/')

TRIM_FP = '306: 3 pads in a triangle (1 and 3 at 5.08 mm, wiper 2.54 mm offset), 6.4 x 6.4 mm outline'
for val, ref, code, stock, st in [
        ('2K (202)', 'TM6', '202', 'Mouser 2,722 in stock', 'in stock'),
        ('5K (502)', 'TM5', '502', 'Mouser 4,788 in stock', 'in stock'),
        ('50K (503)', 'TM4', '503', 'Mouser 0 in stock, 5,600 on order (2026-12-14); Bourns 3362P-1-503LF '
         'Farnell 522 in stock', 'substitute'),
        ('500K (504)', 'TM3', '504', 'Mouser 0 in stock, 199 on order (2026-10-30); Bourns 3362P-1-504LF '
         'Farnell 62 in stock', 'substitute')]:
    row('Trimmers & pots', f'{val} trim potentiometer', 1, ref,
        f'Vishay CT6EP{code} (Digi-Key 306UC{code}B)', TRIM_FP,
        'Nidec Copal', f'CT-6EP{code}', 'Mouser (order by MPN)', stock, st,
        'none' if st == 'in stock' else 'CHECK 3362P pin triangle against the 306 footprint',
        'CT-6EP is the same 6 mm top-adjust family as the BOM part (Vishay/Copal CT6EP). '
        'Parts page: any ceramic trimmer with the same pinout is OK.',
        MD + f'Nidec-Components/CT-6EP{code} ; ' + FN + '3362P-1-503LF')

EVU_FP = ('EVU: 3 pins at 2.5 mm pitch, pin row 7.0 mm behind two mounting lugs 9.144 mm apart '
          '(2.18 mm drill); 9.6 x 12.5 mm outline')
row('Trimmers & pots', '50K D (log) potentiometer', 3, 'VR3 VR5 VR8',
    'Panasonic EVU-F2LFL3D54 (Digi-Key P3L2503)', EVU_FP,
    'Alpha (9 mm vertical) or Alps RK09', '9 mm vertical 50K A (log) pot with 6 mm D shaft, '
    'e.g. Alpha RV09 family', '',
    'EVU-F2LFL3D54: Mouser obsolete. Replacement not checked live (Mouser/TME bot block)',
    'substitute', 'CHECK lug spacing / pin row offset / shaft length vs EVU footprint; D taper not available',
    'Panasonic left the pot business; no EVU-F2 stock. "D" taper has no current equivalent; A (log) is '
    'the nearest. Open questions Q4/Q5.',
    M + 'EVU-F2LFL3D54')
row('Trimmers & pots', '50K B (linear) potentiometer', 2, 'VR2 VR7',
    'Panasonic EVU-F2LFL3B54 (Digi-Key P3K1503)', EVU_FP,
    'Alpha (9 mm vertical) or Alps RK09', '9 mm vertical 50K B pot with 6 mm D shaft', '',
    'EVU-F2LFL3B54: Mouser obsolete. Replacement not checked live',
    'substitute', 'CHECK lug spacing / pin row offset / shaft length vs EVU footprint',
    'Same footprint caveat as the 50K D row.', M + 'EVU-F2LFL3B54')
DUAL_FP = ('ALPHADUAL: 6 pins in one row at 2.0 mm pitch, row 11 mm behind two lugs 11 mm apart '
           '(2.18 mm drill); 13 x 17.6 mm outline')
row('Trimmers & pots', '50K B (linear) dual potentiometer', 1, 'VR4',
    'Alpha RV112BCF-40-25F-B54 (Mouser 317-2202-50K)', DUAL_FP,
    'Alpha (Taiwan)', 'RV112BCF-40-25F-B54 (B50K dual)', '',
    'Not confirmed: Mouser search for the exact part was blocked; same-family RV112BCF-40-25A-A50K '
    '(audio) 990 and -B100K 951 in stock',
    'substitute', 'none',
    'Same family as the original; confirm the B50K variant exists before ordering. Open question Q4.',
    M + 'RV112BCF-40-25F-B54')
row('Trimmers & pots', '1Meg A (log) dual potentiometer', 1, 'VR6',
    'Alpha RV112BCF-40-25F-A16 (Mouser 317-2102-1M)', DUAL_FP,
    'Alpha (Taiwan)', 'RV112BCF-40-25F-A16', 'Mouser 317-2102F-1M', 'Mouser 1,376 in stock',
    'in stock', 'none', 'Original part number still active.', MD + 'Alpha-Taiwan/RV112BCF-40-25F-A16')

# ------------------------------------------------------------- film capacitors
WIMA = 'https://www.wima.de/wp-content/uploads/media/e_WIMA_MKS_2.pdf'
FILM_NOTE_2P5 = ('Xicon PM/PF dipped polyester not found at Mouser (search returned nothing). Holes are '
                 'closer than 5 mm, so a 5 mm box cap does not drop in: use a 2.5 mm-pitch polyester '
                 '(WIMA MKS02 family) and spread the leads, or a dipped cap with formable leads.')
row('Capacitors - film', '.001uF (2A102K) polyester capacitor', 3, 'C34 C100 C101', 'Xicon PM2A102K',
    'C050-035X075: pads 3.556 mm apart, 5.08 x 2.54 mm outline',
    'WIMA', 'MKS02 or FKS2 1000 pF 100 V (2.5 mm pitch)', '', 'Not checked live',
    'substitute', 'CHECK pitch: 3.556 mm holes vs 2.5/5 mm parts', FILM_NOTE_2P5,
    M + 'PM2A102K ; ' + WIMA)
row('Capacitors - film', '.0068uF (2A682K) polyester capacitor', 1, 'C47', 'Xicon PF2A682K',
    'C050-075X075: pads 3.81 mm apart, 5.46 x 3.05 mm outline',
    'WIMA', 'MKS02 or FKS2 6800 pF 100 V (2.5 mm pitch)', '', 'Not checked live',
    'substitute', 'CHECK pitch: 3.81 mm holes', FILM_NOTE_2P5, M + 'PF2A682K ; ' + WIMA)
row('Capacitors - film', '.01uF (2A103K) polyester capacitor', 5, 'C10 C20 C21 C33 C46', 'Xicon PM2A103K',
    'C050-024X044: pads 4.064 mm apart, 6.10 x 3.30 mm outline',
    'WIMA', 'MKS2D021001A00KSSD (5 mm) or MKS02 0.01 uF 100 V (2.5 mm)', 'Farnell 1006017',
    'Farnell 4,991 in stock (MKS2D021001A00KSSD)', 'substitute',
    'CHECK pitch: 4.064 mm holes vs 5 mm rigid pins', FILM_NOTE_2P5,
    FN + 'MKS2D021001A00KSSD ; ' + WIMA)
row('Capacitors - film', '.018uF (2A183K) polyester capacitor', 1, 'C18', 'Xicon PF2A183K',
    'C050-025X075: pads 4.064 mm apart, 6.35 x 3.56 mm outline',
    'WIMA / other', '0.018 uF 100 V polyester, 2.5 mm pitch (E12 value: MKS2 only on request)', '',
    'Not checked live', 'substitute', 'CHECK pitch: 4.064 mm holes', FILM_NOTE_2P5 +
    ' WIMA lists MKS2 in E6 steps; 0.018 uF is "E12 on request".', M + 'PF2A183K ; ' + WIMA)
row('Capacitors - film', '.033uF (2A333K) polyester capacitor', 5, 'C19 C24 C26 C36 C201',
    'Xicon PM2A333K',
    'C050-025X075 (C19 C24 C36 C201): 4.064 mm; C075-032X103 (C26): 5.08 mm',
    'WIMA', 'MKS2D023301A00KSSD (C26) + MKS02 0.033 uF 100 V (others)', '', 'Not checked live',
    'substitute', 'CHECK pitch: 4 of 5 positions are 4.064 mm', FILM_NOTE_2P5,
    M + 'PM2A333K ; ' + WIMA)
row('Capacitors - film', '.047uF (2A473K) polyester capacitor', 1, 'C54', 'Xicon PM2A473K',
    'C050-055X075: pads 5.08 mm apart, 7.37 x 4.32 mm outline',
    'WIMA', 'MKS2D024701A00KSSD (2.5 x 6.5 x 7.2 mm, 5 mm)', '', 'Not checked live',
    'substitute', 'none', '5 mm pins fit 5.08 mm holes.', M + 'PM2A473K ; ' + WIMA)
row('Capacitors - film', '.068uF (2A683K) polyester capacitor', 1, 'C45', 'Xicon PF2A683K',
    'C050-050X075: pads 7.62 mm apart, 8.89 x 5.08 mm outline',
    'WIMA', 'MKS4 0.068 uF 100 V (7.5 mm pitch)', '', 'Not checked live',
    'substitute', 'CHECK pitch: 7.62 mm holes need a 7.5 mm part',
    'A 5 mm box cap cannot reach 7.62 mm holes.', M + 'PF2A683K')
row('Capacitors - film', '.1uF (2A104K) polyester capacitor', 3, 'C25 C27 C41', 'Xicon PM2A104K',
    'C050-030X075: pads 5.08 mm apart, 8.13 x 5.08 mm outline',
    'WIMA', 'MKS2D031001A00KSSD (2.5 x 6.5 x 7.2 mm, 5 mm)', '', 'Not checked live',
    'substitute', 'none', '5 mm pins fit 5.08 mm holes.', M + 'PM2A104K ; ' + WIMA)
row('Capacitors - film', '.22uF (2A224K) polyester capacitor', 1, 'C35', 'Xicon PM2A224K',
    'C050-045X075: pads 7.62 mm apart, 11.43 x 6.35 mm outline',
    'WIMA', 'MKS4 0.22 uF 100 V (7.5 mm pitch)', '', 'Not checked live',
    'substitute', 'CHECK pitch: 7.62 mm holes need a 7.5 mm part', '', M + 'PM2A224K')

# --------------------------------------------------- ceramic / tantalum caps
row('Capacitors - ceramic/tantalum', '.1uF (104) ceramic capacitor', 16,
    'C1 C2 C4 C6 C103 C104 C106 C107 C108 C109 C110 C111 C112 C113 C202 C204',
    'AVX SR205E104MAR (Mouser 581-SR205E104M)', 'C050H075X075: pads 2.54 mm apart, 4.57 x 2.54 mm outline',
    'KYOCERA AVX', 'SR205E104MAR', 'Mouser 581-SR205E104MAR',
    'Mouser 4,987 in stock (+35,000 on order)', 'in stock', 'none',
    'Original part still made. X7R alternative: KEMET C320C104K5R5TA (2.54 mm), Mouser 166,919.',
    M + 'SR205E104MAR ; ' + M + 'C320C104K5R5TA')
row('Capacitors - ceramic/tantalum', '1uF (105) tantalum capacitor', 2, 'C42 C62',
    'Kemet T350A105K035AT (Digi-Key 399-1429)', 'E2,5-7: pads 2.54 mm apart, 5.1 x 4.1 mm outline',
    'KEMET', 'T350A105K035AT', 'Mouser 80-T350A105K035AT', 'Mouser 114 in stock (+35,000 on order)',
    'in stock', 'none', 'Original part still made.', M + 'T350A105K035AT')

# ------------------------------------------------------ electrolytics
XRL = 'Original Xicon XRL not found at Mouser (search for the Mouser numbers returns other parts).'
row('Capacitors - electrolytic', '1uF 50V electrolytic', 13,
    'C11 C13 C14 C15 C17 C22 C23 C29 C38 C56 C58 C59 C105', 'Xicon XRL50V1.0 (Mouser 140-XRL50V1.0)',
    'E5-6: pads 2.54 mm, 5.33 mm circle (12 pcs); C17 E3,5-8: pads 3.556 mm',
    'KEMET', 'ESK105M050AC3AA (5 x 11 mm, 2.0 mm lead spacing)', 'Farnell 2069011',
    'Farnell 20,182 in stock, marked No Longer Manufactured', 'in stock (EOL)',
    'CHECK leads 2.0 -> 2.54 mm (as XRL); C17 needs 3.556 mm', XRL + ' Same 5 x 11 can as XRL; buy now.',
    FN + 'ESK105M050AC3AA')
row('Capacitors - electrolytic', '2.2uF 50V electrolytic', 1, 'C51', 'Xicon XRL50V2.2',
    'E5-6: pads 2.54 mm, 5.33 mm circle', 'KEMET', 'ESK225M050AC3AA (5 x 11 mm)', 'Farnell 2069012',
    'Farnell 3,128 in stock, No Longer Manufactured', 'in stock (EOL)',
    'CHECK leads 2.0 -> 2.54 mm', XRL, FN + 'ESK225M050AC3AA')
row('Capacitors - electrolytic', '10uF 16V (or 35V) electrolytic', 13,
    'C16 C30 C31 C32 C37 C40 C50 C52 C60 C61 C72 C203 C205', 'Xicon XRL16V10',
    'E5-6: pads 2.54 mm, 5.33 mm circle', 'KEMET', 'ESK106M035AC3AA (10 uF 35 V, 5 x 11 mm)',
    'Farnell 2068995', 'Farnell 3,934 in stock, No Longer Manufactured', 'in stock (EOL)',
    'CHECK leads 2.0 -> 2.54 mm', XRL + ' Parts page allows 16 V or 35 V. ESK106M016AC3AA is out of stock.',
    FN + 'ESK106M035AC3AA')
row('Capacitors - electrolytic', '47uF 16V electrolytic (parts page: 10V)', 4, 'C28 C44 C53 C55',
    'Xicon XRL16V47', 'E5-6: pads 2.54 mm, 5.33 mm circle', 'Panasonic', 'ECA-1CM470',
    'Mouser 667-ECA-1CM470', 'Mouser 6,774 in stock', 'in stock', 'CHECK can size is 5 x 11 before ordering',
    XRL + ' Farnell shows ECA-1CM470 as no longer manufactured; Mouser still stocks it.',
    M + 'ECA-1CM470')
row('Capacitors - electrolytic', '100uF 10V electrolytic', 3, 'C48 C49 C102',
    'Xicon XRL (BOM PDF lists 140-xrl25v100 here: transposed)', 'E5-6: pads 2.54 mm, 5.33 mm circle',
    'KEMET', 'ESK107M010AC3AA (5 x 11 mm)', 'Farnell 2068947',
    'Farnell 11,585 in stock, No Longer Manufactured', 'in stock (EOL)', 'CHECK leads 2.0 -> 2.54 mm',
    'The BOM PDF swaps the two 100 uF Mouser numbers (docs/expanded-bom-crosscheck.json); '
    'descriptions are right. PCB values: C48/C49 100/6.3, C102 100/10.', FN + 'ESK107M010AC3AA')
row('Capacitors - electrolytic', '100uF 25V electrolytic', 2, 'C7 C8',
    'Xicon XRL (BOM PDF lists 140-xrl10v100 here: transposed)',
    'E5-6: pads 2.54 mm, 5.33 mm circle (original XRL is 6.3 x 11 mm)', 'KEMET',
    'ESK107M025AE3AA (6.3 x 11 mm, 2.5 mm)', 'Farnell 2068981',
    'Farnell 25,742 in stock, No Longer Manufactured', 'in stock (EOL)', 'none',
    'Same 6.3 mm can as the original XRL; overhangs the 5.33 mm silkscreen like the original.',
    FN + 'ESK107M025AE3AA')
row('Capacitors - electrolytic', '1000uF 10V electrolytic (PCB: 1000/6.3)', 1, 'C43', 'Xicon XRL10V1000',
    'E5-5: pads 5.08 mm, 10.85 mm circle', 'Nichicon', 'UVR1A102MPD (10 x 12.5 mm, 5 mm)',
    'Mouser 647-UVR1A102MPD', 'Mouser 2,660 in stock', 'in stock', 'none',
    'Same 10 x 12.5 mm can as the original XRL.', M + 'UVR1A102MPD')
row('Capacitors - electrolytic', '2200uF 16V electrolytic', 2, 'C3 C5', 'Xicon XRL16V2200',
    'E5-13: pads 5.08 mm, 12.7 mm circle', 'Nichicon', 'UVR1C222MHD (12.5 x 20 mm, 5 mm)',
    'Mouser 647-UVR1C222MHD', 'Mouser 50 in stock (+1,000 expected 2026-10-26); taped -1TO 987',
    'in stock', 'CHECK height 20 mm vs I/O-board clearance',
    'I/O board; compare the can height with the repo model of the original XRL before ordering.',
    M + 'UVR1C222MHD')

# ------------------------------------------------------------- diodes / LEDs
row('Diodes & LEDs', '1N4001', 4, 'D40 D41 D42 D43', 'Generic 1N4001',
    'DO41-10: pads 11.18 mm apart, 1.2 mm drill', 'onsemi', '1N4001G', 'Mouser 863-1N4001G',
    'Mouser 52,592 in stock', 'in stock', 'none', '', M + '1N4001G')
row('Diodes & LEDs', '1N4148', 29,
    'D1 D2 D3 D4 D5 D6 D7 D8 D9 D10 D24 D25 D26 D27 D28 D29 D30 D31 D32 D33 D34 D35 D36 D37 '
    'D44 D45 D46 D47 D48', 'Generic 1N4148', 'DO35-10: pads 7.11 mm apart', 'Vishay', '1N4148-TAP',
    'Mouser (order by MPN)', 'Mouser 114,924 in stock', 'in stock', 'none', '',
    MD + 'Vishay-Semiconductors/1N4148-TAP')
row('Diodes & LEDs', 'Red 5mm LED', 40, 'LED1-LED40', 'Generic',
    'LED5MM: pads 2.54 mm, 5.7 mm outline', 'Kingbright', 'WP7113ID (diffused, 625 nm)',
    'Mouser 604-WP7113ID', 'Mouser 31,378 in stock', 'in stock', 'none',
    'Brightness sets the 10K LED resistor value (parts page); try one before soldering 40.',
    M + 'WP7113ID')
row('Diodes & LEDs', '0.24" LED standoff', 40, 'LED1-LED40 (spacers)', 'VCC STD240B (Mouser 593-STD240B)',
    'Spacer 6.10 mm long, 5.08 mm OD, 2.54 mm lead holes (repo led-spacer record)',
    'Essentra or Bivar', '0.240 in (6.1 mm) two-lead 5 mm LED spacer, e.g. Essentra LEDS2M-240-01', '',
    'STD240B not found at Mouser (no matching rows); replacement not checked live',
    'substitute', 'CHECK length 6.1 mm sets LED height in the panel holes',
    'LED tip height under the front panel depends on this length; keep 6.1 mm.',
    M + 'STD240B ; docs/led-spacer-completion.json', check_refs=False)

# ---------------------------------------------------------------- transistors
TO92_FP = 'TO92 / 2SC536F: 3 pads in line at 2.54 mm; pad order E-C-B (E -2.54, C 0, B +2.54)'
row('Transistors', '2SA733P PNP, TO-92', 10, 'Q1 Q2 Q8 Q9 Q10 Q27 Q31 Q33 Q36 Q38',
    'Fairchild 2SA733P (Mouser)', TO92_FP, 'onsemi', 'KSA992FTA (E-C-B, hFE 300-600)',
    'Mouser 512-KSA992FTA', 'Mouser 105,363 in stock', 'substitute',
    'CHECK flat-side orientation vs silkscreen (pinout E-C-B matches)',
    'Original: Renesas 2SA733 old stock only via LCSC marketplace (38,000, min 100, ~$1.95). '
    'A 2008 batch of 2SA733P measured hFE 340-350 (midibox); KSA992F (300-600) is the nearest gain grade. '
    'Alt: MCC 2SA1015-GR-AP (E-C-B, 200-400), Mouser 14,354, EOL. Q1/Q2 are the VCA pair: match hFE.',
    'https://www.onsemi.com/pdf/datasheet/ksa992-d.pdf ; ' + M + 'KSA992FTA ; ' + MIDIBOX + '?page=5 ; ' + LC + '2SA733')
row('Transistors', '2SC536F NPN, TO-92', 24,
    'Q3 Q4 Q5 Q11 Q13 Q14 Q15 Q16 Q17 Q18 Q19 Q20 Q23 Q24 Q25 Q29 Q30 Q32 Q34 Q35 Q37 Q40 Q41 Q50',
    'NEC 2SC536F ("Rare")', TO92_FP + '; Q17 Q19 Q23 use 2SC536_UNEVEN (E pad at -3.30 mm)',
    'onsemi', 'KSC1815YTA or KSC945CYTA (both E-C-B, hFE 120-240)', 'Mouser (order by MPN)',
    'Mouser 123,238 / 13,925 in stock', 'substitute',
    'CHECK KSC945 must be the -C (centre collector) suffix; plain KSC945 is E-B-C',
    'Community lists 2SC945P as the 2SC536F alternative (midibox group buy, 2008). For a closer gain '
    'grade: Toshiba 2SC1815-GR (200-400) TO-92, LCSC marketplace 1,745; Renesas 2SC945A old stock on '
    'LCSC marketplace. Q3/Q4 are the VCA pair: match hFE; the VCF ladder (Q11-Q20) benefits from matching.',
    'https://www.onsemi.com/pdf/datasheet/ksc945-d.pdf ; https://www.onsemi.com/pdf/datasheet/ksc1815-d.pdf ; ' + M + 'KSC945CYTA ; ' + MIDIBOX
    + '?page=4 ; ' + LC + '2SC1815')
row('Transistors', 'JFET on the board, in place of the 2SK30A at Q28 (O grade) and Q39 (Y grade)', 2, 'Q128 Q139',
    'Toshiba 2SK30A-O / 2SK30A-Y at Q28 and Q39 ("Rare")',
    'x0x-smd:SC-59_Hand on the mainboard since KiCad revision 30: 3 lands, 1.9 mm pitch',
    'Toshiba', '2SK208-O at Q128 and 2SK208-Y at Q139, S-Mini (SC-59)',
    'Mouser 757-2SK208OTE85LF / 757-2SK208-YTE85LF', 'Mouser 9,313 / 9,475 in stock', 'substitute',
    'CHECK SMD part: needs a 3-pin adapter wired S-G-D to the footprint',
    'On paper the 2SK208 is the 2SK30A in another package: Toshiba\'s 2SK208 sheet and the 2SK30A sheet (Tiger\'s copy of Toshiba\'s) '
    'give the same ratings, the same Idss grades, Vgs(off), |Yfs|, Ciss, Crss and noise figure. Not measured here. The sites sit beside '
    'Q28 and Q39, whose holes stay. Through-hole option in those holes: QNHCHIP 2SK30A-Y/-GR (LCSC 960/1,140 in stock, clone brand, '
    'measure Idss). midibox: the Y grade at Q39 matters most. 2N5457/J201 have different pinouts and Idss.',
    M + '2SK208 ; https://forum.pedalpcb.com/goto/post?id=319954 ; ' + MIDIBOX + '?page=4 ; ' + LC + '2SK30A')
row('Transistors', 'Dual NPN on the board, in place of the 2SC1583 at Q12 and Q26 and the 2SC2291 at Q22', 3, 'Q112 Q122 Q126',
    'Mitsubishi 2SC1583 at Q12 and Q26, 2SC2291 at Q22 ("Rare"); those SIP positions are do-not-place',
    'x0x-smd:SOT-363_Hand on the mainboard since KiCad revision 29: 6 lands, 0.65 mm pitch',
    'Nexperia', 'BCM847BS,135', 'Mouser 771-BCM847BS135',
    'Mouser 2,018 at $0.51. Also at Mouser: 771-BCM847BS-T/R 1,508 at $0.76, Diotec 637-BCM847BS 7,100 at $0.39, '
    'Diodes 621-BCM847BS-7 238 at $0.36. Digi-Key: Diotec 12,587, Nexperia and Diodes none. Read 2026-11-04',
    'substitute', 'CHECK fit: solder before the neighbours, 0.65 mm pitch by hand. Q126 touches the R100A model',
    'Owner chose chips on the board (Q2). Buy 5 in all for the 3 sites, as spares for hand soldering. Fit a chip or '
    'its SIP part, never both. Vbe matching counts at Q112 and Q126: Nexperia states 2 mV at 2 mA, but the ladder runs '
    'at 3 to 27 uA, so measure a chip before relying on it. The Diotec and Diodes matching figures were not compared. '
    'The model shows no effect from Q122. All of this is simulated; nothing is built yet. '
    'Original only as NOS/pulls (eBay; 2007 midibox reports of paired 2SC1583/2SC2291 sets). '
    'Brian Castro (via sequencer.de) notes SMD equivalents exist but must be sorted on a curve tracer. '
    'The SSIP5 adapters remain a fallback for a site whose chip is left off.',
    'kicad-working/smd-sites/README.md ; '
    'kicad-working/adapters/ssip5-dual/README.md ; '
    'kicad-working/validation/2sc1583-review/sources/mitsubishi-2sc1583.pdf ; '
    + M + 'BCM847BS ; ' + MIDIBOX + ' ; https://www.sequencer.de/synthesizer/threads/303.123942/post-1463815 ; '
    'https://www.ebay.de/itm/177515067274')
row('Transistors', 'Dual NPN on the board, in place of the 2SC1583 at Q21', 1, 'Q121',
    'Mitsubishi 2SC1583 at Q21 ("Rare"); that SIP position is do-not-place',
    'x0x-smd:SOT-363_Hand on the mainboard since KiCad revision 29: 6 lands, 0.65 mm pitch',
    'onsemi', 'BC847CDW1T1G', 'Mouser 863-BC847CDW1T1G', 'Mouser 14,336 at $0.19; Digi-Key 48,000. Read 2026-11-04',
    'substitute', 'CHECK fit: solder before R110; its land ends 0.07 mm from the R110 model',
    'Owner chose chips on the board (Q2). Buy 3 for this one site, as spares for hand soldering. Fit it or Q21, never '
    'both. In the model Q21 gain sets the resonance: top Q 28.3 with this part, 18.1 with BCM847BS, 26.1 for an original '
    'at hFE 400, so do not swap it with line 61. It has no matching figure, so measure a chip before relying on it. '
    'Avoid Diodes DMMT3904W at Q21: only a minimum hFE of 100 at 10 mA was confirmed. All of this is simulated; nothing '
    'is built yet.',
    'kicad-working/smd-sites/README.md ; '
    + M + 'BC847CDW1T1G ; https://www.digikey.ie/en/products/detail/onsemi/BC847CDW1T1G/1476009')

# ------------------------------------------------------------------- ICs
row('ICs', 'AN6562 8-DIP dual op-amp', 2, 'IC11 IC23', 'Panasonic AN6562 ("Rare")',
    'DIL08: 300 mil DIP-8, standard dual op-amp pinout (OUT1 -IN1 +IN1 V- +IN2 -IN2 OUT2 V+)',
    'Texas Instruments', 'LM358P', 'Mouser 595-LM358P', 'Mouser 34,834 in stock', 'substitute', 'none',
    'Panasonic: AN6562 = AN1358, a 358-class dual op-amp with inputs to 0 V; midibox (TheAncientOne, '
    '2007) reports LM358 working. A 4558 is not single-supply and is not the same class.',
    'https://html.alldatasheet.com/html-pdf/13277/PANASONIC/AN6562S/406/1/AN6562S.html ; ' + MIDIBOX
    + ' ; ' + M + 'LM358P')
row('ICs', '4066 analog switch', 1, 'IC12', 'Generic 4066', 'DIL14', 'Texas Instruments', 'CD4066BE',
    'Mouser 595-CD4066BE', 'Mouser 10,418 in stock', 'in stock', 'none', '', M + 'CD4066BE')
row('ICs', '74HC174 / 74AC174', 1, 'IC9', 'Generic (parts page: HC or AC)', 'DIL16', 'Texas Instruments',
    'SN74HC174N', 'Mouser 595-SN74HC174N', 'Mouser 540 in stock', 'in stock', 'none',
    'No 74AC174 in DIP at Mouser; parts page allows HC.', M + 'SN74HC174N')
row('ICs', '74HC126', 1, 'IC1', 'Generic', 'DIL14', 'Texas Instruments', 'SN74HC126N',
    'Mouser 595-SN74HC126N', 'Mouser 1,146 in stock', 'in stock', 'none', '', M + 'SN74HC126N')
row('ICs', '74AC165 / 74HC165', 3, 'IC16 IC17 IC18', 'Generic (parts page: AC or HC)', 'DIL16',
    'Texas Instruments', 'SN74HC165N', 'Mouser 595-SN74HC165N', 'Mouser 4,559 in stock', 'in stock', 'none',
    'No 74AC165 in DIP at Mouser.', M + 'SN74HC165N')
row('ICs', '74HC595', 5, 'IC4 IC5 IC6 IC7 IC8', 'Generic', 'DIL16', 'Texas Instruments', 'SN74HC595N',
    'Mouser 595-SN74HC595N', 'Mouser 8,644 in stock', 'in stock', 'none', '', M + 'SN74HC595N')
row('ICs', '4N37 optoisolator', 1, 'IC24', 'Generic 4N37 (Mouser 512-4N37, onsemi: now obsolete)',
    'DIL06', 'Lite-On', '4N37', 'Mouser 859-4N37', 'Mouser 6,678 in stock (Vishay 78-4N37: 5,189)',
    'in stock', 'none', 'The BOM Mouser number (onsemi) is obsolete; Lite-On and Vishay make the same part.',
    M + '4N37')
row('ICs', '25C33 SPI EEPROM, 32 Kbit', 1, 'IC2', 'CSI/onsemi CAT25C33P (parts page: CAT2532 / AT25320)',
    'DIL08_AT25: DIP-8, 25xxx SPI pinout', 'Microchip', '25LC320A-I/P', 'Mouser 579-25LC320A-I/P',
    'Mouser 841 in stock (25AA320A-I/P: 826)', 'substitute', 'none',
    'CAT25C33 no longer listed. 25LC320A is the same 4K x 8 SPI EEPROM in the standard 25xxx pinout; '
    'check its write-page size against the firmware (open question Q7).', M + '25LC320A-I/P')
row('ICs', 'ATmega162 microcontroller', 1, 'IC3', 'Atmel ATmega162-16PU (BOM PDF: -40PI)', 'DIL40 (600 mil)',
    'Microchip', 'ATMEGA162-16PU', 'Mouser 556-ATMEGA162-16PU', 'Mouser 390 in stock', 'in stock', 'none',
    'Blank part: needs the bootloader/firmware programmed over ISP.', MD + 'Microchip-Technology/ATMEGA162-16PU')
row('ICs', 'LA4140 9-SIP headphone amplifier', 1, 'IC14', 'Sanyo LA4140 ("Rare")',
    'SIP9: 9 pads at 2.54 mm, 0.9 mm drill, 23 x 3 mm outline', '-', 'LA4140 NOS/pull', '',
    'Not at Mouser or LCSC', 'hunt', 'none for an original part; any replacement amp needs an adapter',
    'Secondary market only (eBay, Vintage Planet, Cricklewood were the 2007-2008 sources). '
    'Only feeds the headphone jack (open question Q6).',
    MIDIBOX + ' ; ' + LC + 'LA4140')
row('ICs', 'BA6110 9-SIP OTA (VCA)', 1, 'IC15B', 'Rohm BA6110 ("Rare")',
    'SIP9 at IC15B: 9 pads at 2.54 mm; IC15A is the alternative BA662 footprint (pins 1-4 differ)',
    '-', 'BA6110 NOS/pull', '', 'Not at Mouser or LCSC', 'hunt',
    'CHECK a BA662 or a clone goes in IC15A, not IC15B, with Q1-Q4 left off',
    'Secondary market only; a 2010 forum warning about a seller of defective BA6110s. Alternative: Open '
    'Music Labs BA662 clone (matched-pair replica) in IC15A; BA662 vs BA6110: ~3-7 dB level and control '
    'threshold differences (subatomicglue). TI LM13700N is obsolete and not pin-compatible.',
    'http://www.openmusiclabs.com/projects/ba662-clone/ ; https://www.subatomicglue.com/x0xl0g/ba662a-analysis/ ; '
    'https://www.diystompboxes.com/smfforum/index.php?msg=950824 ; ' + MIDIBOX)
row('ICs', 'BA662A 9-SIP OTA (optional, not in kit)', 0, '', 'Roland/Rohm BA662A ("Extremely rare")',
    'SIP9 at IC15A', '-', 'not ordered', '', '-', 'not ordered', 'none',
    'Leave IC15A empty when BA6110 is fitted in IC15B. With a BA662 or a clone in IC15A, leave IC15B and Q1-Q4 off: Q1-Q4 are the BA6110 current mirror, and Q3 would sit across the BA662 control input.', BOM_PDF, check_refs=False)
row('ICs', '7805 regulator, TO-220', 1, 'IC20', 'onsemi MC78M05CT (Mouser 512-MC78M05CT)',
    '78XXS: TO-220 lying flat, IN-GND-OUT at 2.54 mm', 'onsemi', 'MC78M05CTG', 'Mouser (order by MPN)',
    'Mouser 3,701 in stock', 'in stock', 'none', 'Lead-free version of the BOM part.', MD + 'onsemi/MC78M05CTG')
row('ICs', '78L06 regulator, TO-92', 1, 'IC21', 'JRC NJM78L06A (Mouser 513-NJM78L06A)',
    'TO-92_x0x: 3 pads at 2.54 mm', 'Texas Instruments', 'UA78L06ACLP', 'Mouser 595-UA78L06ACLP',
    'Mouser 1,363 in stock', 'substitute', 'CHECK pin order OUT-GND-IN against the silkscreen',
    'NJM78L06A and ST L78L06ACZ: Mouser obsolete. onsemi MC78L06ACP: 7,304 in stock but EOL.',
    M + 'UA78L06ACLP ; ' + MD + 'Nisshinbo/NJM78L06A')
row('ICs', 'LM336Z-5.0 reference, TO-92', 1, 'IC22', 'National LM336Z-5.0', 'TO-92_x0x',
    'Texas Instruments', 'LM336Z-5.0/NOPB', 'Mouser (order by MPN)', 'Mouser 4,032 in stock',
    'in stock', 'none', '', MD + 'Texas-Instruments/LM336Z-5.0-NOPB')
row('ICs', 'FT232BM USB UART', 1, 'IC25', 'FTDI FT232BM (Mouser)',
    'SQFP-S-7X7-32: LQFP-32, 7 x 7 mm body, 0.8 mm pitch (SMD)', 'FTDI', 'FT232BL (pin-compatible lead-free '
    'B-series)', 'LCSC C15916 / C18968', 'Mouser: FT232BM and FT232BL-REEL obsolete; LCSC marketplace '
    'FT232BL 304 at ~$105 each, FT232BL-Reel 710 at ~$45 each', 'hunt',
    'none for FT232BL; FT232R/FT232RL are not pin-compatible',
    'Needed for USB; MIDI and ISP do not need it (open question Q3). Expect old stock or pulls.',
    MD + 'FTDI/FT232BM ; ' + MD + 'FTDI/FT232BL-REEL ; ' + LC + 'FT232BL')
row('ICs', '6MHz ceramic resonator', 1, 'XTL2', 'Abracon AWCR-6.00MD', 'Resonator_6MHz_x0x: 3 pads at 2.54 mm',
    'Murata', 'CSTLS6M00G53-B0', 'Mouser 81-CSTS0600MG03', 'Mouser 1,874 in stock, End of Life',
    'in stock (EOL)', 'CHECK 2.5 mm lead pitch into 2.54 mm holes',
    'AWCR-6.00MD and ECS ZTT-6.00MT: Mouser obsolete.', M + 'CSTLS6M00G53-B0 ; ' + MD + 'ABRACON/AWCR-6.00MD')
row('ICs', '16MHz ceramic resonator', 1, 'XTL1', 'Abracon AWCR-16.00MD', '2SC2021 footprint: 3 pads at 2.54 mm',
    'Murata', 'CSTLS16M0X53-B0', 'Mouser 81-CSTLS16M0X53-B0', 'Mouser 16,361 in stock, End of Life',
    'in stock (EOL)', 'CHECK 2.5 mm lead pitch into 2.54 mm holes',
    'AWCR-16.00MD and ECS ZTT-16.00MX: Mouser obsolete.', M + 'CSTLS16M0X53-B0')

# --------------------------------------------------------- sockets / heat sink
row('Mechanical - board', '40-pin DIP socket', 1, 'IC3 (socket)', 'TE AMP 390262-5 (Mouser 571-3902625)',
    'DIL40 600 mil', 'Mill-Max', '110-44-640-41-001000', 'Mouser (order by MPN)', 'Mouser 3,962 in stock',
    'substitute', 'CHECK machined-pin socket is lower than the 5.1 mm TE ladder socket',
    'TE 390262-5 and 1-390262-5: Mouser obsolete. Parts page: any 40-pin socket will do.',
    MD + 'Mill-Max/110-44-640-41-001000 ; ' + MD + 'TE-Connectivity-AMP/390262-5', check_refs=False)
row('Mechanical - board', '8-pin DIP socket', 1, 'IC2 (socket)', 'TE AMP 390261-2 (Mouser 571-3902612)',
    'DIL08 300 mil', 'Mill-Max', '110-44-308-41-001000', 'Mouser (order by MPN)', 'Mouser 12,646 in stock',
    'substitute', 'none', 'TE 390261-2 and 1-390261-2: Mouser obsolete.',
    MD + 'Mill-Max/110-44-308-41-001000', check_refs=False)
row('Mechanical - board', 'Heat sink (TO-220)', 1, 'KK1 (on IC20)', 'Aavid 574502B00000G (Mouser 532-574502B00)',
    'D03S outline 13.7 x 7.6 mm', 'Boyd/Aavid', '574502B00000G', 'Mouser 532-574502B00',
    'Mouser 24,205 in stock', 'in stock', 'none', '', MD + 'Aavid/574502B00000G', check_refs=False)

# ------------------------------------------------------------- connectors
row('Connectors', '1/4" stereo jack', 3, 'MIXOUT MIXIN HEADPHONE', 'Neutrik/REAN NYS216 (Mouser 568-NYS216)',
    'REAN_1_4STERO: 6 pads, 1.6 mm drill, 18.2 x 32.7 mm outline', 'REAN (Neutrik)',
    'NYS216 (backordered) or NYS216-U (in stock)', 'Mouser 568-NYS216 / 568-NYS216-U',
    'Mouser 0 in stock, 6,800 on order; NYS216-U 805 and NYS216G 217 in stock',
    'substitute', 'CHECK NYS216-U pin layout before using it instead',
    'Original part active but backordered; -U ("Phone Connectors 1/4 STEREO JACK .322") is a variant.',
    M + 'NYS216', check_refs=False)
row('Connectors', '1/8" jack', 2, 'CV GATE', 'CUI MJ-CP3536N (Digi-Key CP-3536N)',
    'MJ-3536N: 3 slotted pads, 2.54 mm drill, 10.2 x 17.8 mm outline', 'Same Sky (CUI)', 'MJ-3536N',
    'Mouser 490-MJ-3536N', 'Mouser 8,441 in stock', 'in stock', 'none', '', M + 'MJ-3536N', check_refs=False)
row('Connectors', '2.1mm power jack', 1, 'POWER', 'CUI PJ-202AH (Digi-Key CP-202A)',
    'PJ-202AH: 3 slotted pads 2.8/3.2 mm', 'Same Sky (CUI)', 'PJ-202AH', 'Mouser (order by MPN)',
    'Mouser 4,007 in stock', 'in stock', 'none', '', MD + 'Same-Sky/PJ-202AH', check_refs=False)
row('Connectors', 'USB type-B jack', 1, 'USB', 'Kobiconn 154-2442-E (Mouser)',
    'PN61729: signal pins 2.5 x 2.0 mm, board locks 12.19 mm apart (2.2 mm drill)', 'Amphenol FCI',
    '61729-0010BLF', 'Mouser (order by MPN)', 'Mouser 26,341 in stock', 'substitute', 'none',
    'Kobiconn 154-2442-E: Mouser obsolete. The board footprint is named after the FCI 61729 itself.',
    MD + 'Amphenol-FCI/61729-0010BLF ; ' + MD + 'Kobiconn/154-2442-E', check_refs=False)
row('Connectors', 'MIDI/DINSYNC 5-pin DIN jack', 4, 'DIN1 DIN2 DIN3 DIN4', 'CUI SDS-50J (Digi-Key CP-2350)',
    'CP-2350: 5 pins on a 7 mm circle + 2 shield pins, 1.32 mm drill', 'Same Sky (CUI)', 'SDS-50J',
    'Mouser (order by MPN)', 'Mouser 21,883 in stock', 'in stock', 'none', '', MD + 'Same-Sky/SDS-50J')

# ------------------------------------------------------------- switches
row('Switches', 'Toggle switch (saw/square)', 1, 'S1', 'NKK B12AB-RO (Mouser 633-B12AB)',
    'NKKTOGGLE: 3 pins at 2.54 mm + 4 bracket pins', 'NKK', 'B12AB', 'Mouser 633-B12AB',
    'Mouser 3,046 in stock', 'in stock', 'none', 'Parts page says B12AB-RO; the BOM PDF Mouser number is B12AB.',
    M + 'B12AB')
row('Switches', 'Rotary encoder (tempo)', 1, 'S2', 'CTS 290VAA5F201B2 (Digi-Key CT3011)',
    'PEC11-S: A-C-B at 2.5 mm, switch pins 5 mm, lugs 11.4 mm apart (2.8 mm)', 'CTS', '290VAA5F201B2',
    'Mouser (order by MPN)', 'Mouser 513 in stock', 'in stock',
    'CHECK the board footprint is Bourns PEC11, not CTS 290',
    'Original still made (15 mm flatted, 20 detents). Footprint-native alternative: Bourns '
    'PEC11R-4215F-S0024, Mouser 10,167 in stock (24 detents: firmware tempo step feel changes).',
    MD + 'CTS-Electronic-Components/290VAA5F201B2 ; ' + MD + 'Bourns/PEC11R-4215F-S0024')
row('Switches', '16-position rotary switch (bank/mode)', 2, 'S3 S4', 'Grayhill 25LB22-H (Digi-Key GH3074)',
    'GH3074: C,1,2,4,8 at 2.54 mm, 12.7 mm from shaft; MT1-MT4 take no bracket, only the anchor wire', 'Grayhill',
    '25LB22-H', 'Mouser 706-25LB22-H', 'Mouser 60 in stock ($33.63 each)', 'in stock', 'none',
    'Original still made. The BOM anchors S3 and S4 with ~20 AWG wire but gives no route. On S3 use two separate '
    'wires, MT1-MT4 and MT2-MT3: MT1/MT4 are analog ground and MT2/MT3 digital, so any other route bridges the '
    'ground split.', M + '25LB22-H')
row('Switches', 'Tact switch 12 mm', 23, 'S5-S27', 'E-Switch TL1100F160Q (Digi-Key EG1821)',
    'B3F-40XX: 4 pins 12.5 x 5.0 mm, 1.19 mm drill', 'E-Switch', 'TL1100F160Q', 'Mouser 612-TL1100',
    'Mouser 3,436 in stock', 'in stock', 'none', '', M + 'TL1100F160Q')

# -------------------------------------------------- caps, knobs (front panel)
row('Mechanical - panel', 'Switch cap (white)', 8, '(on S5-S27)', 'ITT PE/WHT (Digi-Key 401-1155)',
    'Cap 12.1 x 5.9 x 11 mm', 'C&K', 'PEWH', 'Digi-Key 401-1155-ND',
    'Digi-Key shows Active, 3,045 in stock (search-index snapshot, not re-checked live)', 'in stock',
    'none', '', 'https://www.digikey.com/en/products/detail/c-k/PEWH/417706', check_refs=False)
row('Mechanical - panel', 'Switch cap (black)', 15, '(on S5-S27)', 'ITT PE/BLK (Digi-Key 401-1152)',
    'Cap 12.1 x 5.9 x 11 mm', 'C&K', 'PEBK', 'Digi-Key 401-1152-ND', 'Not re-checked live', 'in stock',
    'none', 'Same family as PEWH.', 'https://www.digikey.com/en/products/detail/c-k/PEBK/417703',
    check_refs=False)
row('Mechanical - panel', 'Potentiometer knob', 8, '(on VR2-VR8, S2)', 'Eagle Plastic Devices 450-4760 (Mouser)',
    '6 mm D shaft; 13.2 mm body', 'Eagle Plastic Devices', '450-4760 soft-touch knob', 'Mouser 450-4760',
    'Mouser ~4,423 in stock (search-index snapshot, not re-checked live)', 'in stock',
    'CHECK replacement pots must have 6 mm D shafts', '', 'https://www.mouser.com/ProductDetail/450-4760',
    check_refs=False)
row('Mechanical - panel', 'Switch knob', 2, '(on S3 S4)', 'Davies 1510AH (Mouser 5164-1510)',
    '0.75 in dia x 0.56 in', 'Davies Molding', '1510AH', 'Mouser 5164-1510 (BOM number)', 'Mouser 4,054 in stock',
    'in stock', 'none', '', MD + 'Davies-Molding/1510AH', check_refs=False)

# ------------------------------------------------------- wiring / hardware
row('Mechanical - wiring', 'Board-to-board jumper ribbon (0.1 in)', '4 x 6-wire, or 2 x 9 + 1 x 6',
    'J3 J4 J5 J6 J7 (both boards)', 'Molex jumpers (Digi-Key WM09-06 / WM06-06 / WM03-06)',
    'MA12-1 + 4 x MA03-1: 0.100 in pitch, 1.016 mm drill, 24 conductors per board', '-',
    '0.1 in pitch flat jumper / ribbon, solder both ends', '', 'Digi-Key codes not resolved; not checked',
    'generic', 'none',
    'The WM09-06 etc. codes could not be matched to a current Molex part. 24 conductors of 0.1 in ribbon '
    'or wire do the job (open question Q8).', BOM_PDF, check_refs=False)
row('Mechanical - wiring', 'Wire links J1 (12.7 mm) and J2 (15.24 mm)', 2, 'J1 J2', 'Not in BOM',
    '2 pads each, 1.0 mm drill', '-', 'resistor lead offcuts', '', '-', 'generic', 'none',
    'Mainboard wire links (footprints 12 and 15).', '')
row('Mechanical - wiring', 'Solid ~20 AWG wire (anchor S3, S4)', 1, '', 'Generic (supply yourself)', '-',
    '-', 'solid 20 AWG tinned copper', '', '-', 'generic',
    'CHECK S3: separate wires MT1-MT4 and MT2-MT3, or the ground split is bridged (check 15)',
    'See line 91 for the S3 route.', BOM_PDF, check_refs=False)

HW = 'Generic McMaster hardware; not checked'
row('Mechanical - enclosure', 'ABS case', 1, '', 'PacTec PT-10', '-', 'PacTec',
    '82404-501-000 (PT-10 production unit, black)', 'Mouser 616-82404-501-000', 'Mouser 160 in stock',
    'in stock', 'CHECK colour/version vs the original x0xb0x case',
    'PacTec lists only black and PC bone. The original kit case was fitted with Adafruit panels.',
    MD + 'PacTec/82404-501-000', check_refs=False)
row('Mechanical - enclosure', 'Set of main and I/O panels', 1, '', 'Custom (Adafruit)', '-', '-',
    'fabricated from kicad-working/panels', '', 'JLCPCB $22.30 main + $9.60 rear for 5 of each, before shipping. Both ZIPs uploaded, read 2026-11-05', 'custom', 'FR-4, black with white legends. Designed, not made or fitted: kicad-working/panels/README.md', 'FR-4 panels drawn from the original DXFs.', PARTS_PAGE + ' ; kicad-working/panels/README.md',
    check_refs=False)
row('Mechanical - enclosure', 'Set of main and I/O PCBs', 1, '', 'Custom (Adafruit)', '-', '-',
    'fabricated from kicad-working/fabrication/revision-30', '',
    'JLCPCB $26.80 mainboard + $9.90 I/O for 5 of each, before shipping. Mainboard: revision 30 ZIP uploaded, read 2026-11-05. I/O: revision 29 ZIP, read 2026-11-04',
    'custom', 'none',
    'FR-4, 1.6 mm, 1 oz, lead-free HASL, green, white, tented vias. Not ordered. Packages of revision 29 and earlier no longer match.',
    PARTS_PAGE + ' ; kicad-working/fabrication/revision-30/README.md', check_refs=False)
row('Mechanical - enclosure', '9 V AC wall adapter, 300-500 mA, 2.1 mm plug', 1, '', 'Generic (Jameco)', '-',
    '-', '9 V AC (not DC) adapter, >= 500 mA, 2.1 mm barrel', '', 'Not checked (choose for your mains)',
    'generic', 'none', 'Must be AC: the supply is a voltage doubler (D40-D43).', PARTS_PAGE, check_refs=False)
row('Mechanical - enclosure', '15/32" x 1/4" hex 4-40 standoff', 3, '', 'Generic (McMaster)', '-', '-',
    'aluminium hex standoff, female-female, 4-40, 15/32 in', '', HW, 'generic', 'none',
    '15/32 in is not a common length; McMaster carries it.', BOM_PDF, check_refs=False)
row('Mechanical - enclosure', '3/8" x 1/4" hex 4-40 standoff', 4, '', 'Generic (McMaster)', '-', '-',
    'aluminium hex standoff, female-female, 4-40, 3/8 in', '', HW, 'generic', 'none', '', BOM_PDF,
    check_refs=False)
row('Mechanical - enclosure', '4-40 lock washer', 7, '', 'Generic (McMaster)', '-', '-', '#4 split lock washer',
    '', HW, 'generic', 'none', '', BOM_PDF, check_refs=False)
row('Mechanical - enclosure', '4-40 washer', 4, '', 'Generic (McMaster)', '-', '-', '#4 flat washer', '', HW,
    'generic', 'none', '', BOM_PDF, check_refs=False)
row('Mechanical - enclosure', '4-40 x 1/4" hex button screw', 7, '', 'Generic (McMaster)', '-', '-',
    '4-40 x 1/4 in button head hex drive', '', HW, 'generic', 'none', '', BOM_PDF, check_refs=False)
row('Mechanical - enclosure', '4-40 x 1/4" phillips button screw', 7, '', 'Generic (McMaster)', '-', '-',
    '4-40 x 1/4 in button head Phillips', '', HW, 'generic', 'none', '', BOM_PDF, check_refs=False)
row('Mechanical - enclosure', '4-40 x 1/2" phillips cheesehead screw + 4 rubber feet', 4, '',
    'Comes with case', '-', 'PacTec', 'included with PT-10', '', '-', 'in stock', 'none',
    'BOM PDF says 1/4 in, parts page 1/2 in; both say they come with the case.', PARTS_PAGE, check_refs=False)

# --------------------------------------------- optional, from the SI/EMC study (not on the BOM)
SI_NOTE = ('Optional, not in the original design, and from a model that has not been measured. Buy them with '
           'the rest so that they are on hand; fit them only if the scope check in the study calls for them. ')
row('Optional - SI study', '100 pF C0G ceramic, IC9 clock', 1, 'IC9 pin 9 to pin 8', 'Not in BOM',
    'Existing pads 7.62 mm apart', 'TDK', 'FG28C0G1H101JNT06 (5 mm leads)', 'Mouser 810-FG28C0G1H101JNT6',
    'Mouser 3,813 in stock at $0.23. Read 2026-11-05', 'in stock',
    'CHECK fit: leads formed to the pads; only the pad spacing was checked',
    SI_NOTE + 'With the 1 nF on the next line, the model removes the false clock on IC9 during rests.',
    'x0xb0x-si-emc/REPORT.md section 1.2 ; ' + M + 'FG28C0G1H101JNT06', check_refs=False)
row('Optional - SI study', '1 nF C0G ceramic, across the ground split', 1, 'IC9 pin 8 to S3 MT3', 'Not in BOM',
    'Existing pads 6.03 mm apart', 'TDK', 'FG28C0G1H102JNT06 (5 mm leads)', 'Mouser 810-FG28C0G1H102JNT6',
    'Mouser 12,277 in stock at $0.27. Read 2026-11-05', 'in stock',
    'CHECK fit: leads formed to the pads; S3 MT3 also takes the anchor wire (check 15)',
    SI_NOTE + 'Joins analog and digital ground at high frequency only, so the star ground stays at DC.',
    'x0xb0x-si-emc/REPORT.md section 1.2 ; ' + M + 'FG28C0G1H102JNT06', check_refs=False)
row('Optional - SI study', '0.1 uF X7R ceramic, 595 LED driver decoupling', 3, 'IC4 IC5 IC7, pin 16 to pin 13', 'Not in BOM',
    'Existing pads 7.62 mm apart', 'TDK', 'FG28X7R1H104KNT06 (5 mm leads)', 'Mouser 810-FG28X7R1H104KNT6',
    'Mouser 103,402 in stock at $0.27. Read 2026-11-05', 'in stock',
    'CHECK fit: leads formed to the pads; only the pad spacing was checked',
    SI_NOTE + 'The nearest 0.1 uF to these ICs is 28-31 mm of copper away.',
    'x0xb0x-si-emc/REPORT.md section 1.2 ; ' + M + 'FG28X7R1H104KNT06', check_refs=False)
row('Optional - SI study', '0.1 uF X7R ceramic, MCU decoupling', 1, 'IC3 pin 40 to C101 pad 1', 'Not in BOM',
    'Existing pads 3.64 mm apart', 'TDK', 'FG18X7R1H104KNT06 (2.5 mm leads)', 'Mouser 810-FG18X7R1H104KNT6',
    'Mouser 25,459 in stock at $0.27. Read 2026-11-05', 'in stock',
    'CHECK fit: leads formed to the pads; only the pad spacing was checked',
    SI_NOTE + 'IC3 pins 40 and 20 are 50.6 mm apart, so this joins pin 40 to the nearest ground pad instead.',
    'x0xb0x-si-emc/REPORT.md section 1.2 ; ' + M + 'FG18X7R1H104KNT06', check_refs=False)

# ------------------------------------------------------ owner's choice, 2026-11-05 (kept last: line numbers are fixed)
row('Resistors', '150 ohm 5% resistor', 1, 'R16', 'Parts page: 150 ohm in newer kits, 100 ohm in older ones; BOM PDF and PCB 100 ohm', RES_FP,
    'YAGEO', 'MFR-25FBF52-150R', 'Mouser 603-MFR-25FBF52-150R',
    'Mouser 6,535 +30,000 expected 2026-12-03 at $0.10. Read 2026-11-05', 'in stock', 'none',
    'Owner\'s choice over the PCB\'s 100 ohm. With 100 ohm, MIDI IN from a 5 V sender needs a 4N37 CTR of about 133 %, against a '
    'guaranteed 100 %; with 150 ohm it needs about 89 %. That is a model, not measured: x0xb0x-si-emc/REPORT.md section 12.5.',
    'x0xb0x-si-emc/REPORT.md section 12.5 ; ' + PARTS_PAGE + ' ; ' + M + 'MFR-25FBF52-150R')


# ---------------------------------------------------------- Mouser re-read, 2026-11-05
# Stock and one-piece prices read from mouser.com in a browser session on 2026-11-05. These replace what the
# rows above say for the same line. Line numbers are fixed by the order of the rows above. '+N' is on order.
READ = '. Read 2026-11-05'


def _stock(n, price, on_order=None):
    return f'Mouser {n}' + (f' +{on_order} on order' if on_order else '') + f' at ${price}' + READ


_RESISTORS = {1: ('35,242', '0.10'), 2: ('78,658', '0.11'), 3: ('7,783', '0.10'), 4: ('46,691', '0.10', '40,000'),
              5: ('6,873', '0.10', '10,000'), 6: ('4,633', '0.11', '10,000'), 7: ('45,172', '0.10', '130,000'),
              8: ('13,163', '0.12', '10,000'), 9: ('75,848', '0.10'), 10: ('18,395', '0.10', '20,000'),
              11: ('10,110', '0.11', '20,000'), 12: ('11,462', '0.10', '10,000'), 13: ('110,107', '0.10', '70,000'),
              14: ('6,224', '0.10', '10,000'), 15: ('26,679', '0.10'), 16: ('9,325', '0.10', '10,000'),
              17: ('6,050', '0.12', '10,000'), 18: ('12,970', '0.10', '70,000'), 19: ('3,559', '0.10', '10,000'),
              20: ('14,847', '0.10', '50,000'), 21: ('18,733', '0.10'), 22: ('6,715', '0.10', '10,000'),
              23: ('500', '0.11', '80,000'), 24: ('7,176', '0.11', '5,000')}
_SIMPLE = {34: ('Mouser 317-2102F-1M', '1,276', '2.49'), 40: ('Mouser 505-MKS2.047/100/10', '10,123', '0.62'),
           42: ('Mouser 505-MKS2.1/100/10', '9,619', '0.58'), 49: ('Mouser 667-ECA-1CM470', '6,521', '0.23'),
           52: ('Mouser 647-UVR1A102MPD', '2,630', '0.62'), 53: ('Mouser 647-UVR1C222MHD', '922', '0.93'),
           54: ('Mouser 863-1N4001G', '47,613', '0.27'), 55: ('Mouser 78-1N4148-TAP', '111,783', '0.26'),
           56: ('Mouser 604-WP7113ID', '26,977', '0.21', '81,000'), 58: ('Mouser 512-KSA992FTA', '101,160', '0.34'),
           63: ('Mouser 595-LM358P', '39,792', '0.33'), 64: ('Mouser 595-CD4066BE', '19,069', '0.99'),
           65: ('Mouser 595-SN74HC174N', '526', '1.72'), 66: ('Mouser 595-SN74HC126N', '1,139', '0.97'),
           67: ('Mouser 595-SN74HC165N', '3,954', '1.64'), 68: ('Mouser 595-SN74HC595N', '10,480', '1.86'),
           69: ('Mouser 859-4N37', '6,678', '0.44'), 70: ('Mouser 579-25LC320A-I/P', '740', '0.90'),
           71: ('Mouser 556-ATMEGA162-16PU', '380', '6.18'), 75: ('Mouser 863-MC78M05CTG', '3,441', '0.78'),
           76: ('Mouser 595-UA78L06ACLP', '1,360', '1.20'), 77: ('Mouser 926-LM336Z-50/NOPB', '4,888', '0.83'),
           81: ('Mouser 575-11044640', '3,801', '3.22'), 82: ('Mouser 575-144308', '8,752', '0.89'),
           83: ('Mouser 532-574502B00', '21,205', '1.98'), 85: ('Mouser 490-MJ-3536N', '7,424', '1.09', '12,500'),
           86: ('Mouser 490-PJ-202AH', '3,610', '0.86'), 87: ('Mouser 649-61729-0010BLF', '24,974', '1.61'),
           88: ('Mouser 490-SDS-50J', '20,799', '2.65'), 89: ('Mouser 633-B12AB', '2,996', '7.04'),
           90: ('Mouser 774-290VAA5F201B2', '472', '4.96'), 91: ('Mouser 706-25LB22-H', '60', '33.63'),
           92: ('Mouser 612-TL1100', '3,126', '0.51', '12,000'), 93: ('Mouser 611-PEWH', '2,338', '0.93'),
           94: ('Mouser 611-PEBK', '1,999', '0.84'), 96: ('Mouser 5164-1510AH', '4,030', '1.73'),
           100: ('Mouser 616-82404-501-000', '160', '18.85', '23')}
_ESK = {46: ('80-ESK105M050AC3AA', '37,659', '0.16', '22,500'), 47: ('80-ESK225M050AC3AA', '5,627', '0.20'),
        48: ('80-ESK106M035AC3AA', '38,171', '0.17'), 50: ('80-ESK107M010AC3AA', '11,251', '0.18'),
        51: ('80-ESK107M025AE3AA', '12,105', '0.22')}
ESK_NOTE = ' Farnell marked this No Longer Manufactured on 2026-10-17; Mouser shows no such mark on 2026-11-05.'
_FOOTPRINT_CHECK = ' Not compared with the board footprint: see check 5.'
_REFRESH = {
    25: dict(availability='Mouser 78,937 / 13,839 at $0.10' + READ),
    26: dict(proposed_mfr='TE Connectivity', proposed_mpn='LT7330002A1K0JTE (LT73, 3000, 1K0, 5%, SMD)',
             distributor_pn='Mouser 279-LT7330002A1K0JTE',
             availability='Mouser 3,645 at $1.22, End of Life. ERA-S33J102V (667-ERA-S33J102V): Restricted Availability, '
                          'End of Life' + READ, status='substitute',
             notes='Listed as a PTC thermistor. Its name gives 3000, the original\'s +3000 ppm/K, but the datasheet was '
                   'not read: confirm the TC and package before buying. An SMD part needs wire tails across the '
                   '10.16 mm pads, and a small part keeps clear of Q126. Recheck tuning drift after warm-up. '
                   'It is End of Life, so buy spares.'),
    27: dict(proposed_mfr='Bourns', proposed_mpn='3362P-1-202LF', distributor_pn='Mouser 652-3362P-1-202LF',
             availability='Mouser 151 +6,750 on order at $1.25. CT-6EP202 (229-CT-6EP202): 0' + READ, status='substitute',
             fit_flag='CHECK pin triangle against the 306 footprint (check 8)'),
    28: dict(proposed_mfr='Bourns', proposed_mpn='3362P-1-502 (or CT-6EP502 / 3362P-1-502LF when they arrive)',
             distributor_pn='Mouser 652-3362P-1-502',
             availability='Mouser 194 at $1.68, not the LF part. CT-6EP502 (229-CT-6EP502): 0 +7,000 on order. '
                          '3362P-1-502LF: 0 +23,500 on order' + READ, status='substitute',
             fit_flag='CHECK pin triangle against the 306 footprint (check 8)'),
    29: dict(distributor_pn='Mouser 229-CT-6EP503', availability=_stock('887', '1.10'), status='in stock'),
    30: dict(distributor_pn='Mouser 229-CT-6EP504', availability=_stock('199', '1.10'), status='in stock'),
    31: dict(proposed_mfr='Bourns', proposed_mpn='PTV09A-5020F-A503 (audio taper, 6 mm D shaft, 20 mm)',
             distributor_pn='Mouser 652-PTV09A-5020FA503',
             availability='Mouser 119 at $2.16. Alpha RV09AF-40-20K-A54 (317-2080F-50K) 620 at $1.32 has a knurled shaft, '
                          'which does not suit the D knob. EVU-F2LFL3D54: Obsolete' + READ),
    32: dict(proposed_mfr='Bourns', proposed_mpn='PTV09A-4020F-B503 (linear, 6 mm D shaft, 20 mm)',
             distributor_pn='Mouser 652-PTV09A-4020FB503',
             availability='Mouser 771 at $0.89. EVU-F2LFL3B54: Obsolete' + READ),
    33: dict(proposed_mpn='RV112BCF-40-25A-B50K (11 mm linear 50K dual, 6 mm D shaft, 25 mm)',
             distributor_pn='Mouser 317-2202F-50K', availability=_stock('135', '2.49'),
             notes='Same family as the original and as line 34, with the same shaft. Open question Q4.'),
    35: dict(proposed_mfr='KEMET', proposed_mpn='C320C102J1G5TA (1000 pF C0G ceramic, 100 V, 2.54 mm)',
             distributor_pn='Mouser 80-C320C102J1G',
             availability='Mouser 2,418 at $0.52. WIMA MKS02 at 1000 pF: not found at Mouser. '
                          'FKP2D011001D00HO00 film 5,979 at $0.68 needs 5 mm' + READ,
             notes='Ceramic C0G in place of polyester, because no 2.5 mm film part was found at this value. '
                   'Pads are 3.556 mm apart: spread the leads.'),
    36: dict(proposed_mpn='MKS0F016800B00MSSD (6800 pF, 250 V, 2.5 mm)', distributor_pn='Mouser 505-MKS026800/250/20',
             availability='Mouser 513 at $0.84, marked Factory Special Order' + READ),
    37: dict(distributor_pn='Mouser 505-MKS2.01/100/10 (5 mm); 505-MKS02-.01/63/20A (2.5 mm)',
             availability='Mouser 9,735 at $0.63 (5 mm, 100 V); 2,477 at $0.86 (2.5 mm, 63 V, Factory Special Order)' + READ),
    38: dict(proposed_mfr='KEMET', proposed_mpn='C320C183J1G5TA (0.018 uF C0G ceramic, 100 V, 2.54 mm)',
             distributor_pn='Mouser 80-C320C183J1G5TA',
             availability='Mouser 356 at $0.68. Film with 5 mm leads: R82EC2180SH50J 52,973 at $0.34' + READ,
             notes='Ceramic C0G in place of polyester, because no 2.5 mm film part was found at this value. '
                   'Pads are 4.064 mm apart. C18 stands over Q112, so a smaller body helps there.'),
    39: dict(distributor_pn='Mouser 505-MKS2.033/100/10 (C26); 505-MKS020.033/63/20 (others)',
             proposed_mpn='MKS2D023301A00KSSD (C26) + MKS02 0.033/63/20 (others, 2.5 mm, 63 V)',
             availability='Mouser 9,706 at $0.61 (C26); 9,748 at $0.73 (others, Factory Special Order)' + READ),
    41: dict(proposed_mpn='MKS4D026802A00KSSD (0.068 uF, 100 V); confirm 7.5 mm pitch', distributor_pn='Mouser 505-MKS4.068/100/10',
             availability='Mouser 515 +5,000 on order at $0.95. MKS4D026803C00KSSD (505-MKS4.068/100/10P) 2,710 at $0.67' + READ),
    43: dict(proposed_mpn='MKS4D032202B00KSSD (0.22 uF, 100 V); confirm 7.5 mm pitch', distributor_pn='Mouser 505-MKS4.22/100/10',
             availability='Mouser 8,288 at $0.60. MKS4D032203C00KSSD (505-MKS4.22/100/10P) 2,067 at $0.67' + READ),
    44: dict(proposed_mpn='SR205E104MARAP1 (the same part, ammo packaging)', distributor_pn='Mouser 581-SR205E104MARAP1',
             availability='Mouser 13,783 at $0.44. 581-SR205E104MAR: 0 +51,480 on order. '
                          'X7R alternative FG18X7R1H104KNT06 (810-FG18X7R1H104KNT6) 25,459 at $0.27' + READ),
    45: dict(availability=_stock('114', '3.22', '35,000')),
    57: dict(proposed_mfr='Bivar', proposed_mpn='ELM 1-240 (5 mm LED mount, black, 0.240 in)', distributor_pn='Mouser 749-ELM-1-240',
             availability='Mouser 9,900 at $0.38. Essentra LEDS2M-240-01 (144-LEDS2M-240-01): Non-Stocked' + READ,
             fit_flag='CHECK against the spacer drawing: 6.10 mm long, 5.08 mm OD, 2.54 mm lead holes',
             notes='LED tip height under the front panel depends on this length; keep 6.1 mm. The Bivar part has not been '
                   'compared with the spacer drawing: it is a self-retaining mount, and it is black.'),
    59: dict(distributor_pn='Mouser 512-KSC1815YTA / 512-KSC945CYTA', availability='Mouser 119,521 / 13,603 at $0.31' + READ),
    60: dict(availability='Mouser 9,313 / 9,454 at $0.66' + READ),
    61: dict(availability='Mouser 2,018 +10,000 on order at $0.51. Also at Mouser: 771-BCM847BS-T/R 1,508 at $0.76, Diotec '
                          '637-BCM847BS 7,100 at $0.39, Diodes 621-BCM847BS-7 238 at $0.36 (those read 2026-11-04). '
                          'Digi-Key: Diotec 12,587, Nexperia and Diodes none (2026-11-04)' + READ),
    62: dict(availability='Mouser 14,086 +60,000 on order at $0.19; Digi-Key 48,000 (2026-11-04)' + READ),
    72: dict(availability='Not at Mouser: no match for LA4140' + READ),
    73: dict(availability='Not at Mouser: no match for BA6110' + READ),
    78: dict(availability='Mouser: FT232BM (895-FT232BM) Obsolete, no match for FT232BL' + READ +
                          '. LCSC marketplace figures are from 2026-10-17'),
    79: dict(availability=_stock('1,770', '0.21') + ', End of Life'),
    80: dict(availability=_stock('15,541', '0.34') + ', End of Life'),
    84: dict(availability='Mouser NYS216 0 +6,800 on order at $0.72; NYS216-U 801 at $0.61' + READ),
    95: dict(availability='Mouser 3 +4,000 on order at $1.88: need 8. Same range: 450-4765 (black/grey) 3,732 at $1.66; '
                          'plain 450-BA600 (black, 16 mm, D shaft) 8,541 at $1.85' + READ, status='substitute',
             fit_flag='CHECK replacement pots must have 6 mm D shafts. Choose: wait for 450-4760, or a different look'),
}
for _line, _v in _RESISTORS.items():
    ROWS[_line - 1]['availability'] = _stock(*_v)
for _line, (_dpn, *_v) in _SIMPLE.items():
    ROWS[_line - 1].update(distributor_pn=_dpn, availability=_stock(*_v))
for _line, (_dpn, *_v) in _ESK.items():
    ROWS[_line - 1].update(distributor_pn='Mouser ' + _dpn, availability=_stock(*_v), status='in stock')
    ROWS[_line - 1]['notes'] = (ROWS[_line - 1]['notes'] + ESK_NOTE).strip()
for _line, _v in _REFRESH.items():
    ROWS[_line - 1].update(_v)
for _line in (31, 32):
    ROWS[_line - 1]['notes'] = (ROWS[_line - 1]['notes'] + _FOOTPRINT_CHECK).strip()


# ---------------------------------------------- substitutes compared with their datasheets, 2026-11-05
# Each was compared with the footprint on the board and, for the pots, with the Panasonic drawing of the original.
_TAB_NOTE = ('Compared with the Bourns PTV09 and Panasonic EVU drawings: same 2.5 mm pins, pin row 7.0 mm behind the tabs, tabs '
             '10.6 mm apart. The board holes are 9.144 mm apart at 2.18 mm, so a tab corner is about 0.2 mm tight, against '
             '0.34 mm for the original pot: press or nudge the tabs in. Shaft 25 mm from the board with a 12 mm flat, the '
             'same height as the dual pots VR4 and VR6 and 5 mm shorter than the original singles. It stands 11.5 mm above '
             'the panel, which is 13.5 mm from the board.')
_VERIFIED = {
    26: dict(notes='TE LT73 datasheet: 3000 ppm/C +/-10%, 0805 (2.0 x 1.25 mm), 1K0 +/-5%, 0.1 W, -40 to +125 C. That is the '
                   'original\'s +3000 ppm/K. TE lists this part as obsolete and Mouser as End of Life, so buy spares. Solder wire '
                   'tails to it to span the 10.16 mm pads. Recheck tuning drift after warm-up.',
             fit_flag='CHECK by hand: an 0805 chip on wire tails across the 10.16 mm pads'),
    27: dict(fit_flag='CHECK at assembly: the body corner reaches C8\'s 6.3 mm can by 0.17 mm. Form C8 0.3 mm away from TM6',
             notes='Bourns drawing: pins 1 and 3 are 5.08 mm apart and pin 2 is 2.54 mm off that line, the same as the 306 '
                   'footprint in the same orientation. Body 6.60 x 6.99 x 4.88 mm. Tin-plated LF terminals.'),
    28: dict(fit_flag='none',
             notes='Bourns drawing: the same pin triangle as the 306 footprint. TM5 clears its neighbours: the nearest is a pad '
                   '0.19 mm from the body. This part has tin/lead terminals; the LF version is on order.'),
    31: dict(proposed_mpn='PTV09A-5025F-A503 (audio taper, 6 mm D shaft, 25 mm, plastic bushing)',
             distributor_pn='Mouser 652-PTV09A-5025FA503',
             availability='Mouser 831 at $1.75. Alpha RV09AF-40-20K-A54 (317-2080F-50K) 620 at $1.32 has a knurled shaft, which '
                          'does not suit the D knob. EVU-F2LFL3D54: Obsolete' + READ,
             fit_flag='none',
             notes=_TAB_NOTE + ' The 7.9 mm bushing passes the 9.35 mm panel hole. Audio is the nearest taper to the original D.'),
    32: dict(proposed_mpn='PTV09A-4025F-B503 (linear, 6 mm D shaft, 25 mm)', distributor_pn='Mouser 652-PTV09A-4025FB503',
             availability='Mouser 1,040 at $0.89. EVU-F2LFL3B54: Obsolete' + READ, fit_flag='none', notes=_TAB_NOTE),
    33: dict(notes='Alpha catalog and Mouser: RV112BCF-40 family with a 6 mm D shaft, 25 mm, the same pins and tabs as line 34. '
                   'Open question Q4 is settled.', fit_flag='none'),
    35: dict(fit_flag='none',
             notes='Ceramic C0G in place of polyester, because Mouser has no 2.5 mm film part at this value. Body 5.08 x 3.18 mm, '
                   '0.64 mm wider than the outline and clear of its neighbours. Pads are 3.556 mm apart: spread the leads.'),
    36: dict(fit_flag='none', notes='Body 4.6 x 2.5 x 7 mm, inside the outline. Pads are 3.81 mm apart: spread the leads.'),
    37: dict(proposed_mpn='MKS0C021000B00JSSD (0.01 uF, 63 V, 5%, 2.5 mm)', distributor_pn='Mouser 505-MKS02.01/63/5',
             availability='Mouser 5,478 at $1.13, marked Factory Special Order' + READ, fit_flag='none',
             notes='Body 4.6 x 2.5 x 7 mm, inside the outline. Pads are 4.064 mm apart: spread the leads. 63 V is enough on 12 V '
                   'rails. A 7.2 mm MKS2 would overrun the outline.'),
    38: dict(fit_flag='none',
             notes='Ceramic C0G in place of polyester, because Mouser has no 2.5 mm film part at this value; 5% against the '
                   'original 10%. Pads are 4.064 mm apart. C18 is beside Q112: this 5.08 x 3.18 mm body clears the chip by 0.1 mm '
                   'and its lands by 0.25 mm, where the model of the original overhung it.'),
    39: dict(proposed_mpn='MKS2D023301A00KSSD (C26) + MKS0C023300B00KSSD (others, 2.5 mm, 63 V, 10%)',
             distributor_pn='Mouser 505-MKS2.033/100/10 (C26); 505-MKS0C023300BKSSD (others)',
             availability='Mouser 9,706 at $0.61 (C26); 2,698 at $0.81 (others)' + READ, fit_flag='none',
             notes='C26 has 5.08 mm pads and takes the 5 mm MKS2. The others have 4.064 mm pads: spread the leads of the 4.6 x 2.5 x 7 mm '
                   'body. 10% matches the original. 63 V is enough on 12 V rails.'),
    41: dict(proposed_mpn='MKS4D026802A00KSSD (0.068 uF, 100 V, 7.5 mm)', fit_flag='none',
             notes='Pitch confirmed at 7.5 mm for the 7.62 mm pads. The 10 mm body overruns the 8.89 mm outline, and it clears its '
                   'nearest neighbour C47 by 1.1 mm.'),
    43: dict(proposed_mpn='MKS4D032202B00KSSD (0.22 uF, 100 V, 7.5 mm)', fit_flag='none',
             notes='Pitch confirmed at 7.5 mm for the 7.62 mm pads. Body 10 x 3 x 8.5 mm, inside the outline.'),
    44: dict(notes='Mouser: 2.54 mm straight leads and the same 5.08 x 3.18 x 5.08 mm body as the bulk part.'),
    57: dict(fit_flag='none',
             notes='Bivar drawing: 5.1 mm OD, 0.240 +/-0.005 in (6.1 mm) long, two lead slots on 2.54 mm centres, black PVC. That matches '
                   'the 6.10 mm, 5.08 mm OD original STD240BLK. No pad lies within 3.2 mm of any LED centre.'),
    95: dict(proposed_mpn='450-4765 soft-touch knob (grey pointer line)', distributor_pn='Mouser 450-4765',
             availability='Mouser 3,732 at $1.66. 450-4760 (white line, the original): 3 +4,000 on order at $1.88. '
                          'Plain 450-BA600: 8,541 at $1.85' + READ,
             fit_flag='none',
             notes='Mouser lists the same knob as 450-4760 but for the pointer colour: 14 mm wide, 16 mm tall, rubber, 6 mm D shaft. '
                   'Choose 450-4760 once restocked for the white line.'),
    111: dict(fit_flag='CHECK by hand: leads formed from 5 mm to 7.62 mm, on the solder side',
              notes=SI_NOTE + 'With the 1 nF on the next line, the model removes the false clock on IC9 during rests. The nearest '
                              'bottom-side part is 18 mm away.'),
    112: dict(fit_flag='CHECK by hand: leads formed to 6.03 mm; S3 MT3 also takes the anchor wire (check 15)',
              notes=SI_NOTE + 'Joins analog and digital ground at high frequency only, so the star ground stays at DC. The route '
                              'clears S3\'s body.'),
    113: dict(fit_flag='CHECK by hand: on the solder side, with leads arched clear of the joints of pins 14 and 15',
              notes=SI_NOTE + 'The nearest 0.1 uF to these ICs is 28-31 mm of copper away. Bottom-side parts are at least 14.7 mm '
                              'away, and the 5.5 mm body fits the 11.9 mm gap to the panel.'),
    114: dict(fit_flag='CHECK by hand: leads formed from 2.5 mm to 3.64 mm, on the solder side',
              notes=SI_NOTE + 'IC3 pins 40 and 20 are 50.6 mm apart, so this joins pin 40 to the nearest ground pad instead. No '
                              'bottom-side part is on the route.'),
}
for _line, _v in _VERIFIED.items():
    ROWS[_line - 1].update(_v)
for _line in (46, 47, 48, 50, 51):
    ROWS[_line - 1]['notes'] = ROWS[_line - 1]['notes'].strip()


# ------------------------------------------------- older CHECK flags, resolved on paper 2026-11-05
# 'At assembly' is a step to do when building. 'CHECK' is left only on what is still undecided.
_FLAGS = {
    10: 'At assembly: bend the leads for the 2.54 mm pads (R96 R97 R98 R115)',
    13: 'At assembly: bend the leads for the 2.54 mm pads (R96 R97 R98 R115)',
    26: 'At assembly: an 0805 chip on wire tails across the 10.16 mm pads',
    27: 'At assembly: the body corner reaches C8\'s 6.3 mm can by 0.17 mm. Form C8 0.3 mm away from TM6',
    29: 'none', 30: 'none',
    46: 'At assembly: form the leads from 2.0 to 2.54 mm; C17 needs 3.556 mm',
    47: 'At assembly: form the leads from 2.0 to 2.54 mm',
    48: 'At assembly: form the leads from 2.0 to 2.54 mm',
    49: 'none',
    50: 'At assembly: form the leads from 2.0 to 2.54 mm',
    53: 'none', 58: 'none', 59: 'none',
    60: 'At assembly: O grade at Q128, Y grade at Q139; solder them before the neighbours. Fit a chip or its TO-92 part, never both',
    61: 'At assembly: solder before the neighbours, 0.65 mm pitch by hand. Q126 touches the R100A model',
    62: 'At assembly: solder before R110; its land ends 0.07 mm from the R110 model',
    73: 'At assembly: a BA662 or a clone goes in IC15A, not IC15B, with Q1-Q4 left off',
    76: 'none', 79: 'none', 80: 'none', 81: 'none', 84: 'none', 90: 'none',
    99: 'At assembly: separate wires MT1-MT4 and MT2-MT3, or the ground split is bridged (check 15)',
    100: 'Black, the owner\'s choice on 2026-11-06, to match the black FR-4 panels. Bone is Mouser 616-82404-501-039, 24 at $18.85, read 2026-11-05. No kit needed: this unit has both covers, the assembly screws and the feet, and the panels are line 101',
    111: 'At assembly: form the leads from 5 mm to 7.62 mm, on the solder side',
    112: 'At assembly: form the leads to 6.03 mm; S3 MT3 also takes the anchor wire (check 15)',
    113: 'At assembly: on the solder side, with the leads arched clear of the joints of pins 14 and 15',
    114: 'At assembly: form the leads from 2.5 mm to 3.64 mm, on the solder side',
}
_NOTES = {
    49: 'Mouser: 5 x 11 mm, 2 mm leads.',
    53: 'Same 12.5 x 20 mm as the modelled XRL, with 4.37 mm of headroom under the case. C3 and C5 stand 0.28 mm apart at nominal '
        'size, as on the original board.',
    58: 'onsemi: 1 emitter, 2 collector, 3 base, leads formed to 2.54 mm, and the FTA part is active. This order and the '
        'footprint\'s flat side match.',
    59: 'onsemi KSC1815: 1 emitter, 2 collector, 3 base, hFE 120-240. If you use KSC945, take the -C suffix only: plain KSC945 is E-B-C.',
    60: 'Toshiba: 1 source, 2 drain, 3 gate, Idss Y 1.2-3.0 mA and O 0.6-1.4 mA. The lands follow that drawing.',
    76: 'TI: 1 output, 2 common, 3 input, which matches the nets on the footprint\'s pads.',
    79: 'A 2.5 mm lead pitch is 0.04 mm from the 2.54 mm holes.',
    80: 'A 2.5 mm lead pitch is 0.04 mm from the 2.54 mm holes.',
    81: 'A lower socket changes only the chip-top height.',
    90: 'The CTS 290 drawing was checked in revision 13: all 7 pins and tabs fit the PEC11-S holes, smallest margin 0.07 mm. '
        'Cheaper, with 24 detents: PEC11R-4220F-S0024 (652-PEC11R-4220F-S0024) 1,330 at $2.23.',
}
for _line, _flag in _FLAGS.items():
    ROWS[_line - 1]['fit_flag'] = _flag
for _line, _note in _NOTES.items():
    _old = ROWS[_line - 1]['notes'].strip()
    ROWS[_line - 1]['notes'] = (_old + ' ' + _note).strip()
ROWS[84 - 1].update(proposed_mpn='NYS216-U (the same jack, with nut and washer loose)', distributor_pn='Mouser 568-NYS216-U',
                    availability='Mouser 801 at $0.61. NYS216: 0 +6,800 on order at $0.72' + READ, status='in stock',
                    notes='REAN: stereo 3 pole, 8.2 mm distance to PCB, the same as NYS216 with washer and nut not assembled.')
