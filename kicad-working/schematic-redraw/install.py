#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Write a board's redrawn sheets into its KiCad project and relink the board to them.

Usage: install.py <mainboard|ioboard>

Replaces <board>.kicad_sch, adds the pNN sheets and x0x.kicad_sym, adds the library to sym-lib-table, lists the sheets in
the project file and runs relink_board.py. Close the project in KiCad first: edits made there would be lost.
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
import build  # noqa: E402
import x0x_draw as X  # noqa: E402


def main():
    board = sys.argv[1]
    project = HERE.parent / board
    build.build(board, project)
    table = project / 'sym-lib-table'
    text = table.read_text()
    if '"x0x"' not in text:
        text = text.rstrip()
        assert text.endswith(')')
        text = text[:-1].rstrip() + '\n  (lib (name "x0x") (type "KiCad") (uri "${KIPRJMOD}/x0x.kicad_sym") (options "") (descr "Symbols of the redrawn sheets"))\n)\n'
        table.write_text(text)
    pro = project / f'{board}.kicad_pro'
    text = pro.read_text()
    root = X.uid(board, 'root')
    sheets = re.findall(r'\(uuid "([^"]+)"\) \(paper', ''.join((project / p.name).read_text()[:400] for p in sorted(project.glob('p[0-9][0-9]_*.kicad_sch'))))
    titles = [re.search(r'\(title "([^"]*)"', (project / p.name).read_text()[:800])[1] for p in sorted(project.glob('p[0-9][0-9]_*.kicad_sch'))]
    rows = [f'    [\n      "{root}",\n      "Root"\n    ]'] + [f'    [\n      "{u}",\n      "{t}"\n    ]' for u, t in zip(sheets, titles)]
    text, count = re.subn(r'"sheets": \[.*?\n  \]', '"sheets": [\n' + ',\n'.join(rows) + '\n  ]', text, count=1, flags=re.S)
    assert count == 1
    pro.write_text(text)
    subprocess.run([sys.executable, '-I', str(HERE / 'relink_board.py'), str(project), board], check=True)


if __name__ == '__main__':
    main()
