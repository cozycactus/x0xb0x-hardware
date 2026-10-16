#!/usr/bin/env python3
"""Cross-check the expanded x0xb0x BOM against the assignments the models rely on (read-only).

The AdaWiki "x0x:billofmaterials" page (last modified 2016-01-28) blocks automated
fetches; the repository owner printed it to PDF in a browser on 2026-10-16 and the
print is kept byte-for-byte in sources/. This script extracts its text with Poppler's
pdftotext and compares:

* every electrolytic row with the revision-21 Xicon XRL assignment,
* every fixed-resistor row with the revision-22 band assignments,
* the socket and IC rows with revisions 23 and 24,

and checks the electrical argument for the transposed 100uF part numbers against the
PCB nets. It writes docs/expanded-bom-crosscheck.json and changes nothing else.

Run from the repository root (needs pdftotext on PATH):
  python3 -I kicad-working/validation/expanded-bom-review/crosscheck_expanded_bom.py
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
REPO = WORK.parent
PDF = HERE / 'sources/x0x-billofmaterials-adawiki-user-print.pdf'
PDF_SHA = '11f260bfddb9e09d31fe245b343de8639d4655accddb0757afc8d4cf67a89545'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
assert sha(PDF) == PDF_SHA
text = subprocess.run(['pdftotext', '-layout', str(PDF), '-'], capture_output=True, text=True, check=True).stdout
flat = re.sub(r'\s+', ' ', text)
checks = []


def check(name, ok, **detail):
    checks.append(dict(check=name, passed=bool(ok), **detail))


def refs_in(s):
    s = re.sub(r'\([^)]*\)', ' ', s)
    out = [f'{p}{i}' for p, a, b in re.findall(r'([A-Z]+)(\d+)\s*-\s*[A-Z]*(\d+)', s) for i in range(int(a), int(b) + 1)]
    return out + re.findall(r'[A-Z]+\d+', re.sub(r'[A-Z]+\d+\s*-\s*[A-Z]*\d+', ' ', s))


check('Page is the expanded BOM, last modified 2016-01-28', 'Expanded Bill of Materials' in flat and 'Last modified: 2016/01/28' in flat)

# Electrolytics: description, Mouser number, references, from the flattened text (part numbers and
# reference lists wrap across lines and interleave with the description column).
lines = text.split('\n')
flat2 = re.sub(r'140- Mouser ((?:(?!140-).)*?) capacitor (xrl[\w.]+)', r'140-\2 Mouser \1', flat)   # number wrapped after the references
flat2 = re.sub(r'140-\s+(?:capacitor\s+)?(xrl)', r'140-\1', flat2)
starts = list(re.finditer(r'(\d[\d.]*uF(?: \d+V)?)(?: (?:electrolytic|electolytic))?(?: capacitor)? (\d+) (140-xrl[\w.]+?)\s+Mouser', flat2))
rows = []
for k, m in enumerate(starts):
    end = starts[k + 1].start() if k + 1 < len(starts) else len(flat2)
    seg = flat2[m.end():end]
    cut = re.search(r' (?:\d[\d.]*|\.\d+)uF\b| 4066 | 74[A-Z]{2}\d+ ', seg)
    seg = seg[:cut.start()] if cut else seg
    rows.append(dict(description=m.group(1), quantity=int(m.group(2)), part=m.group(3).lower(),
                     references=sorted(set(r for r in refs_in(seg) if r.startswith('C')), key=lambda x: int(x[1:]))))
check('Every electrolytic row lists as many references as its quantity', all(len(r['references']) == r['quantity'] for r in rows) and len(rows) == 8,
      rows={r['description']: len(r['references']) for r in rows})
evidence = json.loads((WORK / 'validation/models-review-21/electrolytic-quality/sources/electrolytic-evidence.json').read_text())
extracts = {k.split(' / ')[0]: v for k, v in evidence['bom']['expanded_bom']['search_engine_extracts'].items()}
found = {r['part'] for r in rows}
for part in ('140-xrl50v1.0', '140-xrl50v2.2', '140-xrl16v10', '140-xrl16v47', '140-xrl10v1000', '140-xrl16v2200'):
    check(f'{part}: search-engine extract confirmed by the page', part in found and part in extracts)
r100 = {r['description']: r for r in rows if r['description'].startswith('100uF')}
check('100uF 10V row: C48, C49, C102 with Mouser 140-xrl25v100', r100.get('100uF 10V', {}).get('references') == ['C48', 'C49', 'C102']
      and r100['100uF 10V']['part'] == '140-xrl25v100')
check('100uF 25V row: C7, C8 with Mouser 140-xrl10v100', r100.get('100uF 25V', {}).get('references') == ['C7', 'C8']
      and r100['100uF 25V']['part'] == '140-xrl10v100')
build = json.loads((WORK / 'validation/models-review-21/electrolytic-quality/electrolytic-model-audit.json').read_text())
size = {r.split(':')[1]: m['dimensions_mm']['diameter'] for m in build['models'].values() for r in m['references']}
modelled = {r.split(':')[1] for m in build['models'].values() for r in m['references']} | {r for v in build['recoloured'].values() for r in v['references']}
check('The electrolytic rows name exactly the 39 electrolytics modelled in revision 21', {r for row in rows for r in row['references']} == modelled,
      modelled=len(modelled))
check('Revision 21 sizes follow the descriptions: 5 mm cans at C48/C49/C102, 6.3 mm at C7/C8',
      all(size[r] == 5.0 for r in ('C48', 'C49', 'C102')) and all(size[r] == 6.3 for r in ('C7', 'C8')))


def pcb_nets(board):
    t = (WORK / board / f'{board}.kicad_pcb').read_text()
    fps = {}
    for blk in re.split(r'\n\t\(footprint ', t)[1:]:
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk).group(1)
        pads = {}
        for pad in re.findall(r'\(pad .*?\n\t\t\)', blk, re.S):
            name = re.match(r'\(pad "([^"]*)"', pad).group(1)
            net = re.search(r'\(net (?:\d+ )?"([^"]*)"\)', pad)
            pads[name] = net.group(1) if net else None
        fps[ref] = pads
    return fps


io, main = pcb_nets('ioboard'), pcb_nets('mainboard')
doubler = (io['C5']['-'] == io['C3']['+'] == io['IC20']['IN'] and io['C3']['-'] == 'GND' and io['R1']['2'] == io['R2']['1'] == io['C5']['+']
           and io['C8']['+'] == io['R1']['1'] == io['IC23']['8'] and io['C7']['+'] == io['R2']['2'])
check('C7/C8 hang off the rail stacked on the rectified input by C5 (above 10 V), so the 25 V description is right', doubler,
      rails=dict(rectified_input=io['C3']['+'], stacked=io['C5']['+'], C7=io['C7']['+'], C8=io['C8']['+']))
check('C48/C49/C102 sit on low-voltage nets (+6V, +5V, LA4140), so the 10 V description is right',
      main['C49']['+'] == '+6V' and main['C102']['+'] == '+5V' and main['C48']['+'] in main['IC14'].values())

# Resistors.
res_rows = []
cur = None
for ln in lines:
    m = re.match(r'^\s*(\d[\d.]*\s?(?:ohm|K|MEG))\s+(1%|5%)\s+resistor.*?(\d+)\s+Generic\s+(.*)$', ln)
    if m:
        cur = dict(value=m.group(1), tolerance=m.group(2), quantity=int(m.group(3)), refs=m.group(4))
        res_rows.append(cur)
        continue
    if cur is None:
        continue
    if re.match(r'^\s{20,}\S', ln) and not re.search(r'trim|potentiometer|Description', ln):
        cur['refs'] += ' ' + ln.strip()
    elif ln.strip() and not (re.match(r'^\s*\(?[a-z]', ln) and len(ln.strip()) < 30):
        cur = None
ohms = lambda v: round(float(re.match(r'[\d.]+', v).group()) * {'ohm': 1, 'K': 1e3, 'MEG': 1e6}[re.search(r'ohm|K|MEG', v).group()], 6)  # noqa: E731
expanded = {}
for r in res_rows:
    r['references'] = refs_in(r['refs'])
    for ref in r['references']:
        expanded[ref] = (ohms(r['value']), r['tolerance'])
bands = json.loads((WORK / 'validation/models-review-22/resistor-quality/sources/resistor-band-assignments.json').read_text())['assignments']
ours = {r: (a['ohms'], a['tolerance']) for r, a in bands.items()}
differ = sorted((r for r in set(ours) & set(expanded) if ours[r] != expanded[r]), key=lambda x: int(x[1:]))
unlisted = sorted(set(ours) - set(expanded), key=lambda x: int(x[1:]))
ten_k = next(r for r in res_rows if r['value'] == '10K')
check('Every resistor the page lists is one of the 212 banded resistors', set(expanded) <= set(ours), listed=len(expanded))
check('Listed values and tolerances match the band assignments except R16', differ == ['R16'],
      differences={r: dict(bands=ours[r], expanded_bom=expanded[r]) for r in differ})
check('R106 is 24K 1% on the page, as banded (PCB value 27K)', expanded.get('R106') == (24000.0, '1%') == ours['R106'])
check('The three unlisted resistors are 10K and fill the 10K row quantity (94 stated, 91 listed)',
      unlisted == ['R157', 'R158', 'R160'] and all(ours[r] == (10000.0, '5%') for r in unlisted)
      and ten_k['quantity'] - len(ten_k['references']) == 3, unlisted=unlisted)
check('The 40 LED resistors appear in the 10K row (R201-R234, R237-R270)',
      all(expanded.get(r) == (10000.0, '5%') for r, a in bands.items() if a['source'].startswith('LED-resistor row')))

# Sockets and ICs.
check('Socket Mouser numbers 571-3902625 / 571-3902612 are AMP 390262-5 / 390261-2', '571-3902625' in flat and '571-3902612' in flat)
check('EEPROM row is cat25c33p (Catalyst, the CSI marking photographed)', 'cat25c33p' in flat)
check('4N37 row is Mouser 512-4n37 and FT232 row is FT232BM', '512-4n37' in flat and 'FT232BM' in flat)
report = dict(
    schema=1, generator='crosscheck_expanded_bom.py', passed=all(c['passed'] for c in checks), check_count=len(checks), checks=checks,
    source=dict(page='https://www.ladyada.net/wiki/x0x/billofmaterials', last_modified='2016-01-28',
                file='kicad-working/validation/expanded-bom-review/sources/x0x-billofmaterials-adawiki-user-print.pdf', sha256=PDF_SHA,
                retrieval='Printed to PDF in a browser by the repository owner on 2026-10-16; the page blocks automated fetches.'),
    electrolytic_rows=rows,
    findings=dict(
        electrolytics='All seven XRL part numbers are confirmed. The two 100uF Mouser numbers are transposed relative to their '
                      'descriptions; the descriptions, references, parts page, kit photographs and circuit agree, so C48/C49/C102 '
                      'are 10 V (5 x 11 mm) and C7/C8 are 25 V (6.3 x 11 mm). Revision-21 models unchanged.',
        resistors='208 of the 209 listed resistors match the revision-22 bands, including R106 at 24K 1%. R157, R158 and R160 are '
                  'unlisted but are 10K (parts page and PCB) and fill the 10K row quantity. R16 is 100 ohm on this page and on the PCB; '
                  'the parts page gives 100 ohm for older kits and 150 ohm for newer kits, and revision 22 shows the newer 150 ohm.',
        sockets_and_ics='Socket, EEPROM, 4N37 and FT232BM rows agree with revisions 23 and 24. The page lists IC16-IC18 as 74AC165 '
                        '(the parts page allows 74AC165 or 74HC165; the revision-24 marking shows 74HC165N) and the microcontroller '
                        'as Atmega162-40PI (the photographed part reads ATMEGA162 16PI).'),
    corrections_to_earlier_records=['Revision 22 recorded R16 as a PCB/parts-page value difference; the parts page actually lists '
                                    'R16 as 100 ohm in older kits and 150 ohm in newer kits.'],
    models_changed=False)
(REPO / 'docs/expanded-bom-crosscheck.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(passed=report['passed'], check_count=len(checks)), indent=2))
for c in checks:
    if not c['passed']:
        print('FAIL', json.dumps(c))
assert report['passed']
