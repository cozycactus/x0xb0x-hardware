"""Check that every terminal solid of all 12 current terminal models joins its body.

Reads the active STEP for each model (revision 15 where rebuilt, otherwise revision
14 or 13), separates the original body solids from the appended terminal solids,
and measures each terminal's distance to the body. Joined means touching or
overlapping (distance below 1e-6 mm).

Run with FreeCAD's Python from the repository root:
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
      kicad-working/validation/models-review-15/terminal-quality/audit_terminal_joins.py
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, '/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App  # noqa: E402,F401
import Part  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731
audits = [json.loads((WORK / f'validation/models-review-{r}/terminal-quality/terminal-model-audit.json').read_text())
          for r in (13, 14, 15)]
models = {}
for audit in audits:
    models.update(audit['models'])
assert len(models) == 12
checks, rows = [], {}
for key, m in sorted(models.items()):
    path = WORK / m['output']
    assert sha(path) == m['output_sha256'], key
    shape = Part.Shape()
    shape.read(str(path))
    solids = shape.Solids
    body = Part.makeCompound(solids[:m['original_solids']])
    terminals = solids[m['original_solids']:]
    assert len(terminals) == m['terminal_solids'] == len(m['terminals'])
    gaps = {t['name']: round(s.distToShape(body)[0], 6) for t, s in zip(m['terminals'], terminals)}
    rows[key] = dict(step=m['output'], step_sha256=m['output_sha256'], terminal_gaps_mm=gaps)
    checks.append(dict(check=f'{key}: every terminal joins its body', passed=all(g < 1e-6 for g in gaps.values()),
                       detached={n: g for n, g in gaps.items() if g >= 1e-6}))
report = dict(schema=1, revision=15, generator='audit_terminal_joins.py', passed=all(c['passed'] for c in checks),
              check_count=len(checks), terminals=sum(len(r['terminal_gaps_mm']) for r in rows.values()),
              checks=checks, models=rows,
              method='FreeCAD distance from each appended terminal solid to the union of the original body solids.')
(HERE / 'terminal-join-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('passed', 'check_count', 'terminals')}))
for c in checks:
    if not c['passed']:
        print('FAIL', c)
assert report['passed']
