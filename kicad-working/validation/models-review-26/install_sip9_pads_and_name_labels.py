"""Restore the Eagle SIP9 pad size and the smashed name labels (KiCad revision 26).

1. SIP9 pads (mainboard IC14, IC15A, IC15B and the project library footprint). The library
   pads are "long" with a 1.016 mm diameter on a 0.9 mm drill. Eagle 4.13 restrings the
   diameter to 1.408 mm (0.9 + 2 x rlMinPadTop 0.254) and then elongates it 100 %, so CAM
   plots 1.408 x 2.816 mm. The importer elongated the library diameter instead (1.40 x
   2.032 mm). Only the size node of the 27 + 9 pads changes; drill, position and mask
   margin stay.
2. Reference labels. Eagle's smashed name records give each label's position, rotation,
   size and layer; the importer used the library >NAME position instead. A temporary copy
   of each board is set from the records with KiCad's own API (apply_name_records.py) and
   saved; only the Reference property nodes, plus one new footprint text for each of the 11
   references KiCad ends with "0", are copied from it into the working files.

Run from the repository root:
  python3 -I kicad-working/validation/models-review-26/install_sip9_pads_and_name_labels.py
Needs KiCad 10.0.7 and the conversion's staging XML (X0X_EAGLE_XML, as for the comparison).
"""
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parents[1]
REPO = W.parent
PY = os.environ.get('KICAD_PYTHON',
                    '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3')
EAGLE = Path(os.environ.get('X0X_EAGLE_XML', REPO.parent / 'kicad-import/validation/repaired-eagle-xml'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
OLD_PAD, NEW_PAD = '(size 2.032 1.40)', '(size 2.816 1.408)'


def node_end(text, start):
    """Index just past the s-expression that opens at text[start] == '('."""
    depth, i, quoted = 0, start, False
    while True:
        c = text[i]
        if quoted:
            if c == '\\':
                i += 1
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1


def footprint_blocks(text):
    """(start, end, reference) of every board footprint."""
    out = []
    for m in re.finditer(r'\n\t\(footprint ', text):
        s = m.start() + 1
        e = node_end(text, s)
        out.append((s, e, re.search(r'\(property "Reference" "([^"]*)"', text[s:e]).group(1)))
    return out


def child(text, start, end, prefix):
    """The one child node of the block [start, end) that starts with prefix at depth 2 (with its indent)."""
    hits = [m.start() + 1 for m in re.finditer('\n' + re.escape('\t\t' + prefix), text[start:end])]
    assert len(hits) == 1, (prefix, len(hits))
    s = start + hits[0]
    return s, node_end(text, s)


def uuid(node):
    return re.search(r'\(uuid "([^"]+)"\)', node).group(1)


# 1. SIP9 pads
pad_files = []
for rel, expected, key in (('mainboard/mainboard.kicad_pcb', 27, '\t(footprint "mainboard-import-fps:SIP9"'),
                           ('mainboard/mainboard-import-fps.pretty/SIP9.kicad_mod', 9, '(footprint "SIP9"')):
    path = W / rel
    old = path.read_text()
    assert old.count(OLD_PAD) == expected, rel
    blocks = [(m.start(), node_end(old, m.start() + (1 if key.startswith('\t') else 0)))
              for m in re.finditer(re.escape(key), old)]
    inside = sum(old[s:e].count(OLD_PAD) for s, e in blocks)
    assert inside == expected, (rel, inside)
    new = old.replace(OLD_PAD, NEW_PAD)
    assert new.replace(NEW_PAD, OLD_PAD) == old
    pad_files.append(dict(file=rel, path=path, old=old, new=new, replaced_pad_sizes=expected))

# 2. Name labels, generated on temporary copies and copied node by node
label_files, rows_by_board = [], {}
tmp = Path(tempfile.mkdtemp(prefix='x0xb0x-rev26-names-'))
env = dict(os.environ, KICAD_CONFIG_HOME=str(tmp / 'config'), XDG_CACHE_HOME=str(tmp / 'cache'))
for board in ('mainboard', 'ioboard'):
    rel = f'{board}/{board}.kicad_pcb'
    pending = next((f for f in pad_files if f['file'] == rel), None)
    old = pending['new'] if pending else (W / rel).read_text()
    (tmp / f'{board}.kicad_pcb').write_text(old)
    r = subprocess.run([PY, '-I', str(H / 'apply_name_records.py'), str(tmp / f'{board}.kicad_pcb'),
                        str(EAGLE / f'{board}.brd'), str(tmp / f'{board}-names.kicad_pcb'),
                        str(tmp / f'{board}-rows.json')], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr[-800:]
    rows = json.loads((tmp / f'{board}-rows.json').read_text())
    saved = (tmp / f'{board}-names.kicad_pcb').read_text()
    saved_blocks = {ref: (s, e) for s, e, ref in footprint_blocks(saved)}
    edits = []
    for s, e, ref in footprint_blocks(old):
        row = next((x for x in rows if x['reference'] == ref), None)
        if row is None:
            continue
        ns, ne = saved_blocks[ref]
        a, b = child(old, s, e, f'(property "Reference" "{ref}"\n')
        c, d = child(saved, ns, ne, f'(property "Reference" "{ref}"\n')
        assert uuid(old[a:b]) == uuid(saved[c:d])
        if old[a:b] != saved[c:d]:
            edits.append((a, b, saved[c:d]))
        if row['printed'] != ref:
            c, d = child(saved, ns, ne, f'(fp_text user "{row["printed"]}"\n')
            # insert after the node KiCad's writer puts before it, found in the working file by uuid
            before = saved.rfind('\n\t\t(', ns, c - 1) + 1
            anchor = uuid(saved[before:node_end(saved, before)])
            at = old.index(f'(uuid "{anchor}")', s, e)
            at = node_end(old, old.rfind('\n\t\t(', s, at) + 1)
            assert old[at] == '\n'
            edits.append((at + 1, at + 1, saved[c:d] + '\n'))
    new, last = [], 0
    for a, b, text in sorted(edits):
        assert a >= last
        new += [old[last:a], text]
        last = b
    new = ''.join(new + [old[last:]])
    rows_by_board[board] = rows
    label_files.append(dict(file=rel, path=W / rel, old=old, new=new,
                            replaced_reference_nodes=sum(1 for a, b, _ in edits if b > a),
                            inserted_user_texts=sum(1 for a, b, _ in edits if b == a)))

# write, then check the written boards with KiCad
for f in pad_files:
    if f['file'] != 'mainboard/mainboard.kicad_pcb':
        f['path'].write_text(f['new'])
for f in label_files:
    f['path'].write_text(f['new'])
r = subprocess.run([PY, '-I', str(H / 'verify_name_labels.py'), str(W), str(EAGLE), str(tmp / 'check.json')],
                   capture_output=True, text=True, env=env)
assert r.returncode == 0, r.stderr[-800:]
check = json.loads((tmp / 'check.json').read_text())
assert check['passed'], check

originals = {f['file']: f['old'] for f in pad_files}
originals.update({f['file']: f['old'] for f in label_files if f['file'] not in originals})
files = []
for rel, before in sorted(originals.items()):
    path = W / rel
    files.append(dict(file=rel, before_sha256=hashlib.sha256(before.encode()).hexdigest(), after_sha256=sha(path),
                      sip9_pad_sizes_replaced=next((f['replaced_pad_sizes'] for f in pad_files if f['file'] == rel), 0),
                      reference_nodes_replaced=next((f['replaced_reference_nodes'] for f in label_files
                                                     if f['file'] == rel), 0),
                      user_texts_inserted=next((f['inserted_user_texts'] for f in label_files if f['file'] == rel), 0)))
summary = json.loads((W / 'validation/working-validation-summary-revision-25.json').read_text())
changed = sorted(f['file'] for f in files)
assert all(f in summary['outputs'] for f in changed)
renamed = {b: sorted(x['reference'] for x in rows if x['printed'] != x['reference']) for b, rows in rows_by_board.items()}
audit = dict(
    passed=True, files=files, label_check=check,
    sip9=dict(references=['IC14', 'IC15A', 'IC15B'], pads=27, library_pads=9, before=OLD_PAD, after=NEW_PAD,
              rule='Eagle 4.13: diameter max(1.016, 0.9 + 2 x 0.254) = 1.408 mm, long pad 2 x 1.408 = 2.816 mm'),
    name_labels={b: dict(records=len(rows), renamed_printed_with_eagle_name=renamed[b],
                         changed_size=[x['reference'] for x in rows
                                       if abs(x['font_mm'] - x['before']['size_mm']) > 1e-6],
                         rows=rows) for b, rows in rows_by_board.items()},
    previous_core_file_count=len(summary['outputs']), changed_previous_core_files=changed, new_core_files=[],
    scope=('SIP9 pad size nodes (27 board pads, 9 library pads) and the Reference property nodes of the parts '
           'with an Eagle smashed name record (381 mainboard, 80 I/O), plus 11 footprint texts printing the Eagle '
           'name of the references KiCad ends with "0". Nets, tracks, zones, drills, footprint poses and models '
           'are unchanged.'))
(H / 'installation-audit.json').write_text(json.dumps(audit, indent=1) + '\n')
print(json.dumps(dict(passed=True, changed_previous_core_files=changed, renamed=renamed,
                      files=[{k: f[k] for k in ('file', 'sip9_pad_sizes_replaced', 'reference_nodes_replaced',
                                                'user_texts_inserted')} for f in files]), indent=1))
