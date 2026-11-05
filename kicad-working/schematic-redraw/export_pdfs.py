#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Export the schematic PDFs, with their sheet references as links that any viewer follows.

Usage: export_pdfs.py [mainboard|ioboard ...]   (both by default)

KiCad writes a sheet reference as a link running JavaScript, ShM([["Show Page 9", "#8"]]), and only Acrobat runs that. This turns each
one into a plain GoTo link. A reference to several sheets gets one link per sheet, side by side along its text. The file is rewritten
object by object with a new cross-reference table. Drawing, sheet boxes and symbol property menus stay as KiCad wrote them.
"""
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLI = os.environ.get('KICAD_CLI', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')
OBJECT = re.compile(rb'(?m)^(\d+) 0 obj\s*(.*?)\s*endobj', re.S)
TRAILER = re.compile(rb'trailer\s*<<(.*?)>>\s*startxref', re.S)
MENU = re.compile(rb'/A\s*<<\s*/Type /Action /S /JavaScript /JS \((ShM.*?)\)\s*>>', re.S)
RECT = re.compile(rb'/Rect\s*\[([^\]]*)\]')
GOTO = re.compile(rb'/S /GoTo /D \[(\d+) 0 R')


def page_ids(objects, trailer):
    """Page objects in document order, from the page tree."""
    root = int(re.search(rb'/Root (\d+) 0 R', trailer)[1])

    def walk(i):
        kids = re.search(rb'/Kids\s*\[(.*?)\]', objects[i], re.S)
        if not kids:
            return [i]
        return [p for k in re.findall(rb'(\d+) 0 R', kids[1]) for p in walk(int(k))]
    return walk(int(re.search(rb'/Pages (\d+) 0 R', objects[root])[1]))


def annotations(objects, page):
    """A page's annotation array and the objects in it. KiCad always writes the array as an object of its own."""
    array = re.search(rb'/Annots\s+(\d+) 0 R', objects[page])
    assert array or b'/Annots' not in objects[page], page
    return (int(array[1]), [int(i) for i in re.findall(rb'(\d+) 0 R', objects[int(array[1])])]) if array else (None, [])


def split(rect, n):
    """n rectangles side by side along the longer side of rect: the text reads left to right, or bottom to top on a vertical label."""
    x0, y0, x1, y1 = rect
    if x1 - x0 >= y1 - y0:
        step = (x1 - x0) / n
        return [(x0 + i * step, y0, x0 + (i + 1) * step, y1) for i in range(n)]
    step = (y1 - y0) / n
    return [(x0, y0 + i * step, x1, y0 + (i + 1) * step) for i in range(n)]


def plain_links(data):
    """The PDF with every 'Show Page' menu turned into GoTo links, and how many references it held."""
    objects = {int(m[1]): m[2] for m in OBJECT.finditer(data)}
    trailer = TRAILER.search(data)[1]
    pages = page_ids(objects, trailer)
    next_id = max(objects) + 1
    references = 0
    for page in pages:
        array, ids = annotations(objects, page)
        kept = []
        for i in ids:
            menu = MENU.search(objects[i])
            targets = [int(t) for t in re.findall(rb'"Show Page \d+",\s*"#(\d+)"', menu[1])] if menu else []
            if not targets:
                kept.append(i)
                continue
            references += 1
            rect = [float(v) for v in RECT.search(objects[i])[1].split()]
            body = objects[i]
            for n, (target, part) in enumerate(zip(targets, split(rect, len(targets)))):
                action = b'/A << /Type /Action /S /GoTo /D [%d 0 R /Fit] >>' % pages[target]
                link = MENU.sub(lambda _: action, body, count=1)
                link = RECT.sub(lambda _: ('/Rect [%.3f %.3f %.3f %.3f]' % part).encode(), link, count=1)
                number = i if n == 0 else next_id
                next_id += n > 0
                objects[number] = link
                kept.append(number)
        if array:
            objects[array] = b'[ ' + b' '.join(b'%d 0 R' % i for i in kept) + b' ]'
    out = bytearray(data[:data.index(b'\n') + 1] + b'%\xe2\xe3\xcf\xd3\n')
    offsets = {}
    for i in sorted(objects):
        offsets[i] = len(out)
        out += b'%d 0 obj\n' % i + objects[i] + b'\nendobj\n'
    table = len(out)
    size = max(objects) + 1
    out += b'xref\n0 %d\n0000000000 65535 f \n' % size
    for i in range(1, size):
        out += b'%010d 00000 n \n' % offsets[i] if i in offsets else b'0000000000 65535 f \n'
    out += b'trailer\n<<' + re.sub(rb'/Size \d+', b'/Size %d' % size, trailer) + b'>>\nstartxref\n%d\n%%%%EOF\n' % table
    return bytes(out), references


def reference_links(data):
    """(page, target page) of each plain reference link in a PDF, with page numbers from 1. Sheet boxes use /Dest, so they aren't counted."""
    objects = {int(m[1]): m[2] for m in OBJECT.finditer(data)}
    pages = page_ids(objects, TRAILER.search(data)[1])
    links = Counter()
    for number, page in enumerate(pages, 1):
        for i in annotations(objects, page)[1]:
            goto = GOTO.search(objects[i])
            if goto:
                links[number, pages.index(int(goto[1])) + 1] += 1
    return links


def export(board, out):
    """Plot a board's installed sheets and write the PDF with plain links. Returns how many references it holds."""
    with tempfile.TemporaryDirectory() as d:
        raw = Path(d) / 'raw.pdf'
        subprocess.run([CLI, 'sch', 'export', 'pdf', '-o', str(raw), str(HERE.parent / board / f'{board}.kicad_sch')], check=True, capture_output=True)
        data, references = plain_links(raw.read_bytes())
    Path(out).write_bytes(data)
    return references


def main():
    for board in sys.argv[1:] or ['mainboard', 'ioboard']:
        print(f'{board}: {export(board, HERE / f"{board}-schematic.pdf")} sheet references as plain links')


if __name__ == '__main__':
    main()
