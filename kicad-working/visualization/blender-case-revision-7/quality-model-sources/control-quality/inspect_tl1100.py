from pathlib import Path
import FreeCAD as App,Part,json,collections
H=Path(__file__).resolve().parent
out={}
for filename in ['TL1100Fxxxx-manufacturer.stp','source-body-experimental.step','fixed-body-experimental.step']:
 p=H/'sources'/filename;s=Part.Shape();s.read(str(p));b=s.BoundBox
 row=dict(valid=s.isValid(),closed=s.isClosed(),solid_count=len(s.Solids),faces=len(s.Faces),bounds=[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],volume=s.Volume,face_types=collections.Counter(str(f.Surface)for f in s.Faces))
 row['z_planes']=sorted(set(round(v.Point.z,8)for v in s.Vertexes));row['faces']=[dict(index=i,area=f.Area,center=list(f.CenterOfMass),bound=[f.BoundBox.XMin,f.BoundBox.YMin,f.BoundBox.ZMin,f.BoundBox.XMax,f.BoundBox.YMax,f.BoundBox.ZMax],valid=f.isValid(),type=str(f.Surface))for i,f in enumerate(s.Faces)]
 out[filename]=row
(H/'sources/tl1100-detailed-inspection.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:{kk:vv for kk,vv in v.items()if kk!='faces'}for k,v in out.items()},indent=2))
