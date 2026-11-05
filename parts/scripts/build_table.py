"""Build the x0xb0x parts order table (CSV + Markdown) from bom_rows.py.

Run from the repository root: python3 -I parts/scripts/build_table.py
Reads work/footprints.json (written by extract_footprints.py) to check that
every reference in the table exists on the KiCad boards and that the
quantities add up.
"""
import csv, json, re, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from bom_rows import ROWS, COLUMNS  # noqa: E402

fps = json.load(open(ROOT / 'work' / 'footprints.json'))
board_refs = {f['ref'].replace('A0', 'A').replace('B0', 'B') if f['ref'].startswith(('R100', 'IC15')) else f['ref']
              for f in fps}


def expand(refs):
    out = []
    for tok in re.split(r'[ ,;]+', refs):
        tok = tok.strip()
        if not tok or not re.match(r'^[A-Z]+\d', tok):
            continue
        m = re.match(r'^([A-Z]+)(\d+)-(?:[A-Z]+)?(\d+)$', tok)
        if m:
            out += [f'{m.group(1)}{i}' for i in range(int(m.group(2)), int(m.group(3)) + 1)]
        else:
            out.append(tok)
    return out


problems = []
seen = Counter()
for r in ROWS:
    refs = expand(r['references'])
    if not r.get('check_refs', True):
        continue
    for x in refs:
        seen[x] += 1
    if refs:
        missing = [x for x in refs if x not in board_refs]
        if missing:
            problems.append(f"line {r['line']}: refs not on boards: {missing}")
        if str(len(refs)) != str(r['qty']).split()[0]:
            problems.append(f"line {r['line']}: qty {r['qty']} but {len(refs)} refs")
dups = [k for k, v in seen.items() if v > 1]
if dups:
    problems.append(f'references listed twice: {dups}')
# Every populated board part (not mounting holes, headers, the heat-sink outline,
# the optional BA662 position or the SIP pairs that are do-not-place since KiCad
# revision 29) must appear in exactly one checked row.
skip = re.compile(r'^(U\$|KK|IC15A$|Q12$|Q21$|Q22$|Q26$|Q28$|Q39$|J[3-7]$|MIXOUT|MIXIN|HEADPHONE|CV|GATE|POWER|USB|DIN)')
uncovered = sorted(x for x in board_refs if not skip.match(x) and x not in seen)
if uncovered:
    problems.append(f'board parts missing from the table: {uncovered}')

with open(ROOT / 'x0xb0x-parts-order.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction='ignore')
    w.writeheader()
    for r in ROWS:
        w.writerow(r)


def md(s):
    return str(s).replace('|', '\\|').replace('\n', ' ')


head = ['#', 'Original description', 'Qty', 'References', 'Original part', 'Footprint constraint',
        'Order now (MPN / distributor no.)', 'Checked 2026-11-05', 'Status', 'Fit flag']
lines = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
for r in ROWS:
    lines.append('| ' + ' | '.join(md(x) for x in [
        r['line'], r['description'], r['qty'], r['references'], r['original_part'], r['footprint'],
        f"{r['proposed_mpn']} ({r['proposed_mfr']})" + (f" / {r['distributor_pn']}" if r['distributor_pn'] else ''),
        r['availability'], r['status'], r['fit_flag']]) + ' |')
(ROOT / 'work' / 'table.md').write_text('\n'.join(lines) + '\n')
MEANING = [
    ('in stock', 'The original part, or an identical current version, is stocked at a major distributor.'),
    ('in stock (EOL)', 'Stocked now, but marked End of Life or No Longer Manufactured. Buy these first.'),
    ('substitute', 'A different current part with a stated fit check, or the original is backordered.'),
    ('hunt', 'No new equivalent exists. You need old stock, the secondary market, or an adapter.'),
    ('generic', 'Screws, standoffs, wire, wall adapter: any equivalent.'),
    ('custom', 'Panels and PCBs, made to order.'),
    ('not ordered', 'Optional BA662A position, left empty.'),
]
lines_n, parts_n = Counter(), Counter()
for r in ROWS:
    lines_n[r['status']] += 1
    q = str(r['qty']).split()[0]
    parts_n[r['status']] += int(q) if q.isdigit() else 0
summary = ['| Status | BOM lines | Parts | Meaning |', '|---|---|---|---|']
summary += [f'| {k} | {lines_n[k]} | {parts_n[k]} | {v} |' for k, v in MEANING if lines_n[k]]
assert sum(lines_n.values()) == sum(lines_n[k] for k, _ in MEANING)
template = (ROOT / 'scripts' / 'report_template.md').read_text()
(ROOT / 'x0xb0x-parts-order.md').write_text(
    template.replace('<!-- TABLE -->', '\n'.join(lines)).replace('<!-- SUMMARY -->', '\n'.join(summary)))

status = Counter(r['status'] for r in ROWS)
print('rows', len(ROWS), dict(status))
print('\n'.join(problems) if problems else 'reference/quantity check passed')
