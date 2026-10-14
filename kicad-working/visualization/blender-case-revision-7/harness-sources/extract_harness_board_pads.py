from pathlib import Path
import pcbnew,json,hashlib
ROOT=Path('/Users/ruslanmigirov/Downloads/hardware/kicad-working');HERE=Path(__file__).resolve().parent
records={}
for board in ['mainboard','ioboard']:
 path=ROOT/board/(board+'.kicad_pcb');before=hashlib.sha256(path.read_bytes()).hexdigest();b=pcbnew.LoadBoard(str(path));refs={f.GetReference():f for f in b.GetFootprints()};out={}
 for ref in ['J3','J4','J5','J6','J7']:
  f=refs[ref];pads=[]
  for p in sorted(f.Pads(),key=lambda p:int(p.GetNumber())):
   v=p.GetPosition();l=p.GetFPRelativePosition();pads.append({'pin':int(p.GetNumber()),'pcb_xy_mm':[pcbnew.ToMM(v.x),pcbnew.ToMM(v.y)],'native_xy_mm':[pcbnew.ToMM(v.x),-pcbnew.ToMM(v.y)],'original_footprint_local_xy_mm':[pcbnew.ToMM(l.x),pcbnew.ToMM(l.y)],'canonical_local_xy_mm':[pcbnew.ToMM(l.x),-pcbnew.ToMM(l.y)],'net':p.GetNetname(),'drill_mm':[pcbnew.ToMM(p.GetDrillSize().x),pcbnew.ToMM(p.GetDrillSize().y)]})
  out[ref]={'footprint':str(f.GetFPID()),'pcb_origin_xy_mm':[pcbnew.ToMM(f.GetPosition().x),pcbnew.ToMM(f.GetPosition().y)],'rotation_deg':f.GetOrientationDegrees(),'side':b.GetLayerName(f.GetLayer()),'pin_markers':[{'text':g.GetText(),'pcb_xy_mm':[pcbnew.ToMM(g.GetPosition().x),pcbnew.ToMM(g.GetPosition().y)],'layer':b.GetLayerName(g.GetLayer())} for g in f.GraphicalItems() if isinstance(g,pcbnew.PCB_TEXT) and g.GetText() in ['1','12']], 'pads':pads}
 records[board]={'path':str(path),'sha256':before,'footprints':out,'unchanged_after_read':hashlib.sha256(path.read_bytes()).hexdigest()==before}
(HERE/'actual-board-endpoints.json').write_text(json.dumps(records,indent=2)+'\n')
print('48 actual harness endpoint pads extracted without board writes')
