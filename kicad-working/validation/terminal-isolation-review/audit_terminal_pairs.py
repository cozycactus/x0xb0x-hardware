"""Read-only BRep screen of separate solder-terminal solids in current models.

This checks illustration geometry only, not the internal circuit or actual
component isolation. Intentional switch/jack contacts require source review.
"""
import hashlib,itertools,json,sys
from pathlib import Path
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
H=Path(__file__).resolve().parent;W=H.parents[1];R=W.parent
sys.path.insert(0,str(W/'validation/models-review-16/terminal-quality'))
from terminal_spec import MODELS
plan=json.loads((W/'validation/models-review-19/combined-model-plan.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
guard_files=[W/b/(b+'.kicad_pcb') for b in ['mainboard','ioboard']]+[W/'visualization/blender-case-revision-22/x0xb0x-populated-with-case.blend']
guards={str(p.relative_to(R)):sha(p) for p in guard_files};rows=[]
for key,spec in MODELS.items():
 output=spec['output'] if key!='USB' else 'Kobiconn1542442E_DrawingDerived_Terminals.step'
 assignments=[a for a in plan['assignments'] if Path(a['local_model']).name==output];assert assignments,(key,output)
 a=assignments[0];path=W/a['board']/'3dmodels'/a['local_model'];shape=Part.Shape();shape.read(str(path));assert shape.isValid()
 n=len(spec['terminals']);terms=shape.Solids[2:8] if key=='USB' else shape.Solids[-n:];assert len(terms)==n
 assert all(t.BoundBox.ZMin<0 for t in terms),(key,'Expected solder-terminal solids')
 pairs=[]
 for (i,left),(j,right) in itertools.combinations(enumerate(terms),2):
  volume=left.common(right).Volume;distance=left.distToShape(right)[0]
  pairs.append({'first':spec['terminals'][i]['name'],'second':spec['terminals'][j]['name'],'intersection_mm3':volume,'minimum_distance_mm':distance,'overlap':volume>1e-8,'touches':distance<1e-7})
 row={'id':key,'file':str(path.relative_to(R)),'sha256':sha(path),'references':sorted(r for a in assignments for r in a['references']),'terminals':n,'pair_count':len(pairs),'minimum_distance_mm':min(p['minimum_distance_mm'] for p in pairs),'overlaps':[p for p in pairs if p['overlap']],'touches':[p for p in pairs if p['touches']],'pairs':pairs};rows.append(row)
 print(key,'pairs',len(pairs),'overlaps',len(row['overlaps']),'minimum gap',row['minimum_distance_mm'],flush=True)
assert guards=={str(p.relative_to(R)):sha(p) for p in guard_files}
report={'passed':not any(r['overlaps'] for r in rows),'method':'Fresh exact BRep pairwise common-volume and nearest-distance checks on separately specified terminal solids. End-to-body intentional embedding is excluded. No inference about internal electrical switching or isolation.','model_count':len(rows),'reference_count':sum(len(r['references']) for r in rows),'pair_count':sum(r['pair_count'] for r in rows),'models':rows,'active_inputs_unchanged':guards,'read_only':True,'physical_fit_qualified':False}
(H/'terminal-pair-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['models','active_inputs_unchanged']},indent=2))
