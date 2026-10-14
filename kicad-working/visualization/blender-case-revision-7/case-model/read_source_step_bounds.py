from pathlib import Path
import json,FreeCAD,Part
p=Path(__file__).resolve().parent
rows={}
for name,h in json.loads((p/"source-step-audit-input.json").read_text()).items():
 s=Part.Shape();s.read(name);b=s.BoundBox
 rows[name]={"sha256":h,"valid":s.isValid(),"solid_count":len(s.Solids),"bounds_mm":[[b.XMin,b.YMin,b.ZMin],[b.XMax,b.YMax,b.ZMax]]}
(p/"source-step-bounds.json").write_text(json.dumps(rows,indent=2)+"\n")
