"""Read-only native KiCad actual Q22 pad/drill input for independent audit."""
import pcbnew,json,hashlib,re
from pathlib import Path
root=Path('/Users/ruslanmigirov/Downloads/hardware/kicad-working')
p=root/'mainboard/mainboard.kicad_pcb';c=root/'mainboard/mainboard-import-fps.pretty/SSIP5.kicad_mod'
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
before={str(q):sha(q) for q in [p,c]}
b=pcbnew.LoadBoard(str(p));fp=next(f for f in b.GetFootprints() if f.GetReference()=='Q22')
r={'pcb':str(p),'cache':str(c),'source_sha256_before':before,'footprint':str(fp.GetFPID().GetLibItemName()),'layer':str(b.GetLayerName(fp.GetLayer())),'orientation_deg':fp.GetOrientationDegrees(),'position_mm':[pcbnew.ToMM(fp.GetPosition().x),pcbnew.ToMM(fp.GetPosition().y)],'board_thickness_mm':pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness()),'pads':[],'cache_model_nodes':len(re.findall(r'^\s*\(model\b',c.read_text(),re.M))}
for pad in sorted(fp.Pads(),key=lambda p:int(p.GetNumber())):
 d=pad.GetDrillSize();q=pad.GetFPRelativePosition()
 r['pads'].append({'pin':str(pad.GetNumber()),'original_F_Cu_local_xy_mm':[pcbnew.ToMM(q.x),pcbnew.ToMM(q.y)],'canonical_xy_mm':[pcbnew.ToMM(q.x),-pcbnew.ToMM(q.y)],'drill_xy_mm':[pcbnew.ToMM(d.x),pcbnew.ToMM(d.y)],'drill_shape':int(pad.GetDrillShape())})
r['source_sha256_after']={str(q):sha(q) for q in [p,c]}
assert r['source_sha256_before']==r['source_sha256_after']
out=root/'validation/models-review-9/legacy-quality/independent-2sc2291-actual-pad-input.json';out.write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'footprint':r['footprint'],'pads':len(r['pads']),'input_hashes':r['source_sha256_after']}))
