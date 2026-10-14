#!/usr/bin/env python3
"""Independent read-only sections of exported STEP at seven PCB depths.
SPDX-License-Identifier: CC0-1.0
"""
import sys,json,math,hashlib
from pathlib import Path
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App,Part
HERE=Path(__file__).resolve().parent;WORK=HERE.parents[2]
sys.path.insert(0,str(WORK.parent/'kicad-import/validation'))
from verify_native_projects import parse_sexpr,children,one,property_value
manifest=json.loads((HERE/'integrated-model-manifest.json').read_text())
depths=[.001,.1,.4,.8,1.2,1.5,1.599]
result=[];failures=[]
for row in manifest['assignments']:
    path=Path(row['source_model']);shape=Part.read(str(path))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    boardpath=WORK/row['board']/(row['board']+'.kicad_pcb');br=parse_sexpr(boardpath.read_text())
    angle=math.radians(-row['rotation_deg'][2]);assert row['scale']==[1,1,1] and row['offset_mm']==[0,0,0]
    checked=[]
    for depth in depths:
        section=shape.section(Part.makePlane(100,100,App.Vector(-50,-50,-depth)))
        loops=[]
        for edges in Part.sortEdges(section.Edges):
            wire=Part.Wire(edges);bbox=wire.BoundBox
            center=[(bbox.XMin+bbox.XMax)/2,(bbox.YMin+bbox.YMax)/2]
            points=wire.discretize(Number=512)+[v.Point for v in wire.Vertexes]
            rotated_center=[math.cos(angle)*center[0]-math.sin(angle)*center[1],math.sin(angle)*center[0]+math.cos(angle)*center[1]]
            rotated_points=[[math.cos(angle)*p.x-math.sin(angle)*p.y,math.sin(angle)*p.x+math.cos(angle)*p.y] for p in points]
            loops.append(dict(center=rotated_center,points=rotated_points))
        for ref in row['refs']:
            fp=next(f for f in children(br,'footprint') if property_value(f,'Reference','reference')==ref)
            pads=children(fp,'pad');assert len(pads)==len(loops)
            used=set()
            for pad in pads:
                center=[float(one(pad,'at')[1]),-float(one(pad,'at')[2])]
                idx=min(range(len(loops)),key=lambda i:math.dist(center,loops[i]['center']))
                assert idx not in used;used.add(idx)
                loop=loops[idx];error=math.dist(center,loop['center']);radius=max(math.dist(center,p) for p in loop['points'])
                drill=float(one(pad,'drill')[1]);margin=drill/2-radius
                good=error<1e-7 and margin>.01
                record=dict(reference=ref,pin=pad[1],depth_below_board_mm=depth,actual_board_drill_mm=drill,center_error_mm=error,lead_section_radius_mm=radius,radial_margin_mm=margin,passed=good)
                checked.append(record)
                if not good:failures.append(record)
    result.append(dict(board=row['board'],refs=row['refs'],model=path.name,shape_valid=shape.isValid(),actual_board_sha256=hashlib.sha256(boardpath.read_bytes()).hexdigest(),checks=checked,
                       minimum_radial_margin_mm=min(c['radial_margin_mm'] for c in checked),passed=all(c['passed'] for c in checked)))
report=dict(audit='Independent exported STEP full nominal PCB thickness sampling against actual placed drills',passed=not failures,check_count=sum(len(r['checks']) for r in result),failure_count=len(failures),failures=failures,
            depths_below_board_mm=depths,results=result,limits='Seven sampled planes across nominal1.6mm board; all generated below-board lead sections are straight. Actual part tolerances, plating and fitted geometry remain unverified.')
(HERE/'integrated-full-thickness-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k in ['passed','check_count','failure_count','failures']},indent=2))
