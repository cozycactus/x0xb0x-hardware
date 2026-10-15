"""Assign original-kit colour bands to all 212 fixed resistors (read-only).

Reads the archived original parts page (revision-7 mirror) and both PCBs. Each band
list printed on the page must decode to its row's value. Every resistor gets bands
from, in order: its own parts-page row; the 10K row, whose printed reference list is
cut off (26 of 54 listed; the remaining 28 PCB references are all 10K); the LED-resistor
row ("value may vary"), which takes the PCB value; the 200K 1% row, whose bands are
read from its photograph. PCB value fields are never changed.

Run:  python3 -I kicad-working/validation/models-review-22/resistor-quality/extract_resistor_bands.py
"""
import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
MIRROR = WORK / 'visualization/blender-case-revision-7/bom-parts/original-parts-page-mirror.html'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
DIGIT = dict(Black=0, Brown=1, Red=2, Orange=3, Yellow=4, Green=5, Blue=6, Violet=7, Grey=8, White=9)
MULT = dict(DIGIT, Gold=-1, Silver=-2)
TOL = dict(Brown='1%', Gold='5%', Silver='10%')


def ohms(text):
    m = re.fullmatch(r'([0-9.]+)\s*(ohm|K|k|MEG|M)?', text.strip())
    assert m, text
    return round(float(m.group(1)) * {None: 1, 'ohm': 1, 'K': 1e3, 'k': 1e3, 'MEG': 1e6, 'M': 1e6}[m.group(2)], 6)


def decode(bands):
    *digits, mult, tol = bands
    value = int(''.join(str(DIGIT[d]) for d in digits)) * 10 ** MULT[mult]
    return round(value, 6), TOL[tol]


def encode(value, tol):
    n = 3 if tol == '1%' else 2
    exp = 0
    while round(value / 10 ** exp) >= 10 ** n:
        exp += 1
    while value / 10 ** exp < 10 ** (n - 1):
        exp -= 1
    digits = str(round(value / 10 ** exp))
    names = {v: k for k, v in DIGIT.items()}
    mult = {v: k for k, v in MULT.items()}[exp]
    return [names[int(c)] for c in digits] + [mult, {'1%': 'Brown', '5%': 'Gold'}[tol]]


text = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', MIRROR.read_text(errors='ignore'))))
COLOUR = 'Black|Brown|Red|Orange|Yellow|Green|Blue|Violet|Purple|Gray|Grey|White|Gold|GOld|Silver'
row_re = re.compile(r'([0-9.]+ ?(?:ohm|K|k|MEG|M)?) (1%|5%) resistor((?: (?:' + COLOUR + r'))*) (.*?) (\d+) (?:Generic|Any|Rare)')
rows, checks = [], []


def check(name, ok, **detail):
    checks.append(dict(check=name, passed=bool(ok), **detail))
    if not ok:
        print('FAIL', json.dumps(checks[-1]))


for m in row_re.finditer(text):
    printed = m.group(3).split()
    bands = ['Gold' if b == 'GOld' else 'Grey' if b == 'Gray' else 'Violet' if b == 'Purple' else b for b in printed]
    refs = [r.rstrip('*') for r in re.findall(r'R\d+\*?', m.group(4))]
    row = dict(value=m.group(1), ohms=ohms(m.group(1)), tolerance=m.group(2), printed_bands=printed, refs=refs, quantity=int(m.group(5)))
    if bands:
        row['bands'] = bands
        if printed != bands:
            row['band_spelling_normalised'] = True
        check(f'{row["value"]} {row["tolerance"]}: printed bands decode to the row value', decode(bands) == (row['ohms'], row['tolerance']),
              bands=bands)
    rows.append(row)
by_value = {(r['ohms'], r['tolerance']): r for r in rows}
r200 = by_value[(200000.0, '1%')]
assert 'bands' not in r200
r200.update(bands=['Red', 'Black', 'Black', 'Orange', 'Brown'], bands_source='Read from the row photograph 200.0K.jpg (red end first); the row prints no bands')
check('200K 1% bands read from the photograph decode to 200K 1%', decode(r200['bands']) == (200000.0, '1%'))
r4k7 = by_value[(4700.0, '5%')]
if len(r4k7['bands']) == 3:      # page prints "Yellow Violet Red GOld"; keep the normalised four bands
    r4k7['bands'].append('Gold')
led_match = re.search(r'5% resistor Value may vary depending on LED type and brightness ((?:R\d+ )+)(\d+) Generic', text)
LED = led_match.group(1).split()
check('LED-resistor row lists 40 references', len(LED) == int(led_match.group(2)) == 40)

pcb = {}
for board in ('mainboard', 'ioboard'):
    t = (WORK / board / f'{board}.kicad_pcb').read_text()
    for blk in re.split(r'\n\t\(footprint ', t)[1:]:
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        fp = blk.split('"')[1].split(':')[-1]
        if not fp.startswith('0207_'):
            continue
        pcb[ref] = dict(board=board, footprint=fp, pcb_value=re.search(r'\(property "Value" "([^"]*)"', blk).group(1),
                        model=re.findall(r'\(model "([^"]+)"', blk)[0])
check('212 fixed resistors on 0207 footprints, unique references across boards', len(pcb) == 212)
listed = {ref: r for r in rows for ref in r['refs']}
check('Every listed parts-page reference exists on a PCB', set(listed) <= set(pcb), extra=sorted(set(listed) - set(pcb)))
ten_k = by_value[(10000.0, '5%')]
assignments, differences = {}, []
for ref, item in sorted(pcb.items(), key=lambda kv: (kv[1]['board'], int(re.sub(r'\D', '', kv[0])))):
    value = ohms(item['pcb_value'])
    if ref in listed:
        row = listed[ref]
        source = 'parts-page row'
    elif ref in LED:
        row = dict(ohms=value, tolerance='5%', bands=encode(value, '5%'), value=item['pcb_value'])
        source = 'LED-resistor row (5%, value may vary); PCB value'
    else:
        assert value == 10000.0, (ref, value)
        row = ten_k
        source = 'parts-page 10K row; its printed reference list stops after 26 of 54'
    if row['ohms'] != value:
        differences.append(dict(reference=ref, board=item['board'], pcb_value=item['pcb_value'], parts_page=f'{row["value"]} {row["tolerance"]}'))
    assignments[ref] = dict(item, ohms=row['ohms'], tolerance=row['tolerance'], bands=row['bands'], source=source)
counts = Counter(a['source'].split(';')[0] for a in assignments.values())
check('The 28 references missing from the 10K row are all 10K on the PCB and complete its quantity',
      counts['parts-page 10K row'] == 28 and len(ten_k['refs']) + 28 == ten_k['quantity'] == 54)
check('Only R16 and R106 differ between PCB value and parts page',
      sorted(d['reference'] for d in differences) == ['R106', 'R16'], differences=differences)
check('Every assigned band list decodes to its assigned value and tolerance',
      all(decode(a['bands']) == (a['ohms'], a['tolerance']) for a in assignments.values()))
check('Twenty 1% references (R4, R5, R106, R74-R90)', sorted(r for r, a in assignments.items() if a['tolerance'] == '1%') ==
      sorted(['R4', 'R5', 'R106'] + [f'R{n}' for n in range(74, 91)]))
report = dict(schema=1, generator='extract_resistor_bands.py', passed=all(c['passed'] for c in checks), check_count=len(checks),
              checks=checks, parts_page=dict(url='https://www.ladyada.net/make/x0xb0x/fab/parts.html', local_mirror=str(MIRROR.relative_to(WORK)),
                                             sha256=sha(MIRROR)),
              rows=rows, led_references=LED, value_differences=differences,
              differences_resolution='Bands follow the parts page (the part supplied in the kit); PCB value fields stay unchanged.',
              photos=dict(source='Original parts page photographs, archived at https://github.com/x0xb0x/x0xb0x.github.io (assets/images/parts/)',
                          retained=False,
                          files={'2.4k_1p.jpg': 'a91aead043c56fec04431d4ab4fab4959e9e619f09890826d13120410e6b652a',
                                 '24.0K_1p.jpg': '4d0033b771abd9970785ccfb978c324ad7ccde496497829e4ed5d9d5804c5076',
                                 '5.60K.jpg': 'eae7b8812c0fac591fa35e7f63120d4549d39530fbb1263224685b32a8fb031e',
                                 '200.0K.jpg': 'ea6eb7a2273352dfec33426c491b90c0db07cf5e5a812612b950b6e529bb700a',
                                 'resleft_t.gif': '31af51eb6724e911b24330f9fab458c3939915b21572243d714a45fd8bbb9638'},
                          one_percent_body_srgb_median={'2.4k_1p.jpg': [93, 149, 175], '24.0K_1p.jpg': [95, 143, 173],
                                                        '5.60K.jpg': [111, 163, 184], '200.0K.jpg': [116, 162, 188]},
                          five_percent_body='No photograph; tan body sampled from the page band graphic resleft_t.gif, median [169, 118, 82]'),
              body_colours_srgb={'1%': [0.41, 0.61, 0.71], '5%': [0.66, 0.46, 0.32]},
              assignments=assignments, source_counts=dict(counts))
(HERE / 'sources/resistor-band-assignments.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(passed=report['passed'], check_count=len(checks), sources=dict(counts),
                      variants=len({(a['footprint'], tuple(a['bands'])) for a in assignments.values()})), indent=2))
assert report['passed']
