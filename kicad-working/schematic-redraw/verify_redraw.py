#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Check the redrawn schematics on the files in the project. Writes docs/schematic-redraw.json.

Usage: verify_redraw.py [--mutation]

Checks that the generator reproduces the installed files, that they are in the format this KiCad writes, that sheet instances
name the project's top-level sheet with pages in order, that every pin is on the same net as on the board copper and in the
original Eagle schematic, that every footprint has a symbol and links to its own, that ERC is clean, that DRC and schematic parity
report what they reported before the redraw apart from the mounting holes, and that the board files differ from revision 27 only in their links to the symbols.
The format, instance and link checks cover what the KiCad editor reads and kicad-cli's other commands don't report. --mutation
also leaves one wire out of each sheet in turn and confirms that the net comparison then fails, which shows it can. Says nothing
about real hardware.
"""
import collections
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build  # noqa: E402
import check_nets as C  # noqa: E402
import x0x_draw as X  # noqa: E402

WORK = HERE.parent
ROOT = WORK.parent
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
# As at revision 27, except the mainboard's seven mounting holes: their 7 extra_footprint warnings became 14 mismatches, 2 per hole, on value and BOM flag.
BEFORE = {'mainboard': dict(violations=335, unconnected=1, parity=127, parity_types={'footprint_symbol_mismatch': 84, 'net_conflict': 43, 'extra_footprint': 0}),
          'ioboard': dict(violations=254, unconnected=1, parity=45, parity_types={'net_conflict': 38, 'footprint_symbol_mismatch': 7})}
results = []


def check(name, ok, **detail):
    results.append(dict(check=name, passed=bool(ok), **detail))
    print('PASS' if ok else 'FAIL', name, detail if not ok else '')
    return ok


def run(*cmd):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True)


def netlist(sch, out):
    run(CLI, 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', out, sch)
    return C.read_netlist(out)


def net_state(board, sch):
    """Pins, nets and differences against the copper and the Eagle schematic."""
    parts = json.load(open(HERE / 'data' / f'{board}_parts.json'))
    copper, open_pads = {}, set()
    for r, p in parts.items():
        if not p['path'] and r.startswith('U$'):
            continue
        for q in p['pads']:
            if q['net'] is None:
                open_pads.add(f'{r}.{q["num"]}')
            else:
                copper[f'{r}.{q["num"]}'] = q['net']
    back = {v: k for k, v in C.RENAMED.items()}
    eagle = {}
    for reference, pad, net in json.load(open(HERE / 'data' / f'{board}_eagle_nets.json'))['pins']:
        eagle[f'{back.get(reference, reference)}.{pad}'] = net
    linked = {p: n for p, n in sch.items() if p not in open_pads}

    def differ(a, b):
        return dict(missing=len(set(b) - set(a)), extra=len(set(a) - set(b)), names=sum(a[p] != b[p] for p in set(a) & set(b)),
                    groups=len(C.groups({p: a[p] for p in b if p in a}) ^ C.groups({p: b[p] for p in a if p in b})))
    return dict(pins=len(copper), nets=len(set(copper.values())), against_copper=differ(linked, copper), against_eagle=differ({p: n for p, n in sch.items() if p in eagle}, eagle),
                open_pads_joined=sum(p in sch and not sch[p].startswith('unconnected-') for p in open_pads), netted_pads_open=sum(n.startswith('unconnected-') and p not in open_pads for p, n in sch.items()))


def clean(state):
    return not any(state['against_copper'].values()) and not any(state['against_eagle'].values()) and not state['open_pads_joined'] and not state['netted_pads_open']


def mutation(board):
    """Leave out one typed wire on each sheet in turn. The comparison must notice."""
    survivors = []
    pages = (build.project_mainboard if board == 'mainboard' else build.project_ioboard)()[1]
    real_route = X.Sheet.route
    tried = 0
    for file, *_ in pages:
        counts = collections.Counter()

        def count(self, *points):
            counts[self.file] += 1
            return real_route(self, *points)
        X.Sheet.route = count
        with tempfile.TemporaryDirectory() as d:
            build.build(board, d)
        n = counts[file]
        target = n // 2
        seen = collections.Counter()

        def drop(self, *points):
            seen[self.file] += 1
            if self.file == file and seen[self.file] == target:
                return None
            return real_route(self, *points)
        X.Sheet.route = drop
        with tempfile.TemporaryDirectory() as d:
            build.build(board, d)
            (Path(d) / f'{board}.kicad_pro').write_text('{}')
            state = net_state(board, netlist(Path(d) / f'{board}.kicad_sch', Path(d) / 'n.net'))
        tried += 1
        if clean(state):
            survivors.append(file)
        X.Sheet.route = real_route
    return tried, survivors


def old_formats(project, work):
    """Files in an older format than this KiCad writes. The editor warns about these and kicad-cli's other commands do not."""
    old = []
    for path in sorted(project.glob('*.kicad_sch')):
        copy = work / path.name
        copy.write_bytes(path.read_bytes())
        result = run(CLI, 'sch', 'upgrade', copy)
        if 'not updated' not in result.stdout + result.stderr:
            old.append(path.name)
    out = work / 'upgraded.kicad_sym'
    run(CLI, 'sym', 'upgrade', '-o', out, project / f'{X.LIB}.kicad_sym')
    if out.exists():
        old.append(f'{X.LIB}.kicad_sym')
    return old


def instance_problems(board, project):
    """Sheet instance data the editor would throw away and rebuild, which it reports as an error fixed on loading."""
    top = json.load(open(project / f'{board}.kicad_pro'))['schematic']['top_level_sheets'][0]['uuid']
    problems = []
    for path in sorted(project.glob('p[0-9][0-9]_*.kicad_sch')):
        roots = set(re.findall(r'\(path "/([^/"]+)/[^"]*" \(reference', path.read_text()))
        if roots != {top}:
            problems.append(f'{path.name}: symbol instances under {sorted(roots)}, project top-level sheet {top}')
    root_text = (project / f'{board}.kicad_sch').read_text()
    pages = re.findall(r'\(path "/([^/"]+)" \(page "(\d+)"\)', root_text)
    if [r for r, _ in pages] != [top] * len(pages):
        problems.append('sub-sheet instances are not under the project top-level sheet')
    if [int(n) for _, n in pages] != list(range(2, len(pages) + 2)):
        problems.append(f'pages out of order: {[n for _, n in pages]}')
    return problems


def link_problems(board, project, net_file):
    """Footprints whose path is not their own symbol's, which KiCad's parity check can't see because it matches by reference,
    and footprints with no symbol, which Update PCB would delete."""
    text = Path(net_file).read_text()
    want = {}
    for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)(.*?)(?=\(comp\s+\(ref|\Z)', text, re.S):
        sheet = re.search(r'\(sheetpath\s+\(names "[^"]*"\)\s+\(tstamps "([^"]*)"\)\s*\)', m[2])
        ids = re.search(r'\)\s*\(tstamps ((?:"[^"]+"\s*)+)\)', m[2][sheet.end() - 1:])
        want[m[1]] = {sheet[1] + u for u in re.findall(r'"([^"]+)"', ids[1])}
    pcb = (project / f'{board}.kicad_pcb').read_text()
    have = collections.defaultdict(list)
    refs = set()
    for chunk in pcb.split('\n\t(footprint ')[1:]:
        ref = re.search(r'\(property "Reference" "([^"]*)"', chunk)
        path = re.search(r'\n\t\t\(path "([^"]*)"\)', chunk)
        refs.add(ref[1])
        if path:
            have[path[1]].append(ref[1])
    found = {r: p for p, refs in have.items() for r in refs}
    return dict(footprints=sum(map(len, have.values())), symbols=len(want), shared_paths=sum(len(r) > 1 for r in have.values()),
                wrong=sorted(r for r, p in found.items() if r in want and p not in want[r])[:12], without_link=sorted(set(want) - set(found))[:12], without_symbol=sorted(refs - set(want)))


def main():
    record = json.load(open(HERE / 'pcb-relink-record.json'))['boards']
    for board in ('mainboard', 'ioboard'):
        project = WORK / board
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            build.build(board, d)
            names = sorted(p.name for p in d.iterdir())
            same = [n for n in names if (project / n).read_bytes() == (d / n).read_bytes()]
            check(f'{board}: the generator reproduces the installed sheets and symbol library', same == names, files=len(names), differing=sorted(set(names) - set(same)))
            work = d / 'formats'
            work.mkdir()
            old = old_formats(project, work)
            check(f'{board}: the sheets and the symbol library are in the format this KiCad writes', not old, older=old)
            problems = instance_problems(board, project)
            check(f'{board}: sheet instances name the project top-level sheet, with pages in sheet order', not problems, problems=problems)
            state = net_state(board, netlist(project / f'{board}.kicad_sch', d / 'n.net'))
            check(f'{board}: every pin on the same net as the board copper and the Eagle schematic, with the same names', clean(state), **state)
            links = link_problems(board, project, d / 'n.net')
            check(f'{board}: every footprint has a symbol and links to its own', not links['shared_paths'] and not links['wrong'] and not links['without_link'] and not links['without_symbol'], **links)
            run(CLI, 'sch', 'erc', '--severity-all', '-o', d / 'erc.rpt', project / f'{board}.kicad_sch')
            summary = re.search(r'ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)', (d / 'erc.rpt').read_text())
            check(f'{board}: ERC finds nothing under the project rules', summary and summary[1] == '0', messages=summary and int(summary[1]))
            r = run(CLI, 'pcb', 'drc', '--schematic-parity', '--severity-all', '--units', 'mm', '-o', d / 'drc.rpt', project / f'{board}.kicad_pcb')
            found = [int(x) for x in re.findall(r'Found (\d+) ', r.stdout)]
            kinds = collections.Counter(re.findall(r'^\[(\w+)\]', (d / 'drc.rpt').read_text(), re.M))
            b = BEFORE[board]
            check(f'{board}: DRC and schematic parity report what they reported at revision 27, apart from the mounting holes', found == [b['violations'], b['unconnected'], b['parity']] and all(kinds[k] == v for k, v in b['parity_types'].items()),
                  found=found, parity_types={k: kinds[k] for k in b['parity_types']})
        pcb = (project / f'{board}.kicad_pcb').read_bytes()
        stripped = re.sub(rb'^\t\t\((path|sheetname|sheetfile) "[^"]*"\)\n', b'', pcb, flags=re.M)  # Footprint level only: a zone has a sheetname too
        check(f'{board}: the board file differs from revision 27 only in its links to the symbols', hashlib.sha256(stripped).hexdigest() == record[board]['without_link_fields_sha256'] and hashlib.sha256(pcb).hexdigest() == record[board]['after_sha256'])
        if '--mutation' in sys.argv:
            tried, survivors = mutation(board)
            check(f'{board}: leaving one wire out of each sheet makes the net comparison fail', tried and not survivors, sheets_tried=tried, not_noticed=survivors)
    passed = sum(r['passed'] for r in results)
    print(f'{passed} of {len(results)} passed')
    if '--mutation' in sys.argv:
        (ROOT / 'docs' / 'schematic-redraw.json').write_text(json.dumps(dict(
            scope='Both KiCad schematics redrawn on sheets by hand from the original Eagle sheets. Files and nets only: nothing here was built or measured.',
            kicad_working_revision=28, measured_on_hardware=False, board_copper_changed=False, checks=results,
            opened_in_kicad_editor='By hand in KiCad 10.0.7, not by this script; what was seen is in kicad-working/schematic-redraw/README.md.'), indent=1) + '\n')
    raise SystemExit(0 if passed == len(results) else 1)


if __name__ == '__main__':
    main()
