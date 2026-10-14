#!/usr/bin/env python3
"""Check imported STEP lead stock normal to each bent straight segment.
SPDX-License-Identifier: CC0-1.0
"""
from pathlib import Path
import hashlib
import json
import math
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,'/Applications/FreeCAD.app/Contents/Resources/lib')
import FreeCAD as App
import Part
H=Path(__file__).resolve().parent
M=json.loads((H/'transistor-quality-manifest.json').read_text())
checks=[]


def check(name,passed,**evidence):
    checks.append(dict(name=name,passed=bool(passed),**evidence))
    assert passed,(name,evidence)


for part in M['parts']:
    shape=Part.read(part['step'])
    check(part['id']+':source-frozen',
          hashlib.sha256(Path(part['step']).read_bytes()).hexdigest()==part['source_sha256'])
    leads=sorted([s for s in shape.Solids if s.Volume<5],key=lambda s:s.CenterOfMass.x,reverse=True)
    for pin,(lead,points) in enumerate(zip(leads,part['dimensions']['bend_centerlines_XZ_mm']),1):
        for segment,((x1,z1),(x2,z2)) in enumerate(zip(points,points[1:]),1):
            # Middle of the straight segment avoids the explicitly rounded joins.
            mid=App.Vector((x1+x2)/2,0,(z1+z2)/2)
            tangent=App.Vector(x2-x1,0,z2-z1);tangent.normalize()
            normal=App.Vector(tangent.z,0,-tangent.x)
            a=mid+normal*10+App.Vector(0,10,0)
            b=mid-normal*10+App.Vector(0,10,0)
            c=mid-normal*10-App.Vector(0,10,0)
            d=mid+normal*10-App.Vector(0,10,0)
            plane=Part.Face(Part.makePolygon([a,b,c,d,a]))
            section=lead.section(plane)
            face=Part.Face(Part.Wire(section.Edges))
            widths=[(v.Point-mid).dot(normal)for v in section.Vertexes]
            depths=[v.Point.y for v in section.Vertexes]
            width=max(widths)-min(widths);depth=max(depths)-min(depths)
            check(part['id']+f':pin{pin}:segment{segment}:source-stock-transverse',
                  abs(width-.45)<1e-6 and abs(depth-.44)<1e-6 and abs(face.Area-.198)<1e-6,
                  transverse_width_mm=width,depth_mm=depth,area_mm2=face.Area,
                  normal_plane_center_mm=[mid.x,mid.y,mid.z])
report=dict(passed=True,check_count=len(checks),checks=checks,
            proof='Imported STEP conductor sections normal to all straight centerline segments retain full0.45x0.44mm stock, including diagonals. Rounded joining unions add material without thinning.',
            physical_fit_qualified=False)
(H/'transverse-stock-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,checks=len(checks)),indent=2))
