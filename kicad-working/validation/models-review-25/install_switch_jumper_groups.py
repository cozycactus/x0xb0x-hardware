"""Declare the internal terminal strips of the Omron B3F-40XX tact switches (KiCad revision 25).

The original Eagle switch symbol draws pins 1-2 and 3-4 as two joined strips, and the
B3F-40XX package places pads 1 and 2 (3 and 4) 12.5 mm apart on one strip. The original
mainboard routes +5V through S19 and S22 pads 1 and 2, so its one stored +5V airwire is
closed inside those switches. KiCad's footprint jumper pad groups express exactly that:
("1" "2") and ("3" "4"). The node is inserted where KiCad's own writer places it, after
(duplicate_pad_numbers_are_jumpers no); no pad, track, zone, net or placement changes.

Run from the repository root:
  python3 -I kicad-working/validation/models-review-25/install_switch_jumper_groups.py
"""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
FLAG = '(duplicate_pad_numbers_are_jumpers no)\n'


def groups(indent):
    return f'{indent}(jumper_pad_groups\n{indent}\t("1" "2")\n{indent}\t("3" "4")\n{indent})\n'


def insert(text, start_key, indent):
    """Insert the groups after the jumper flag of every footprint block that starts with start_key."""
    out, i, count = [], 0, 0
    while True:
        j = text.find(start_key, i)
        if j < 0:
            out.append(text[i:])
            break
        k = text.find(indent + FLAG, j)
        nxt = text.find('\n' + indent[:-1] + '(footprint ', j + 1) if indent != '\t' else -1
        assert k > 0 and (nxt < 0 or k < nxt), 'jumper flag not found inside the footprint'
        k += len(indent + FLAG)
        assert not text.startswith(indent + '(jumper_pad_groups', k), 'already installed'
        out += [text[i:k], groups(indent)]
        i, count = k, count + 1
    return ''.join(out), count


targets = [('mainboard/mainboard.kicad_pcb', '\t(footprint "mainboard-import-fps:B3F-40XX"', '\t\t', 23),
           ('mainboard/mainboard-import-fps.pretty/B3F-40XX.kicad_mod', '(footprint "B3F-40XX"', '\t', 1)]
files = []
for rel, key, indent, expected in targets:
    path = W / rel
    old = path.read_text()
    new, n = insert(old, key, indent)
    assert n == expected, (rel, n)
    # every byte outside the inserted nodes is unchanged
    assert new.replace(groups(indent), '') == old
    path.write_text(new)
    files.append(dict(file=rel, before_sha256=hashlib.sha256(old.encode()).hexdigest(), after_sha256=sha(path),
                      inserted_jumper_pad_groups=n, inserted_text=groups(indent),
                      bytes_outside_inserted_nodes_identical=True))

board = (W / 'mainboard/mainboard.kicad_pcb').read_text()
refs = []
for block in board.split('\n\t(footprint ')[1:]:
    if block.startswith('"mainboard-import-fps:B3F-40XX"'):
        ref = block.split('(property "Reference" "', 1)[1].split('"', 1)[0]
        refs.append(ref)
        assert '(jumper_pad_groups' in block
assert len(refs) == 23
summary = json.loads((W / 'validation/working-validation-summary-revision-24.json').read_text())
changed = sorted(f['file'] for f in files)
assert all(f in summary['outputs'] for f in changed)
audit = dict(passed=True, files=files, references=sorted(refs, key=lambda r: int(r[1:])),
             previous_core_file_count=len(summary['outputs']), changed_previous_core_files=changed,
             new_core_files=[],
             scope='Footprint metadata only: jumper pad groups ("1" "2") and ("3" "4") on the 23 B3F-40XX '
                   'placements and the project library footprint. Copper, pads, drills, nets, placement, '
                   'zones and models are unchanged; checked by byte equality after removing the inserted nodes.')
(H / 'installation-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps({k: audit[k] for k in ('passed', 'references', 'changed_previous_core_files')}, indent=2))
