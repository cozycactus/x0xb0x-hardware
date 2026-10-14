#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Read a supplied COLLADA file and print source geometry metadata as JSON.

No import, conversion, file writing, unit guessing or model modification.
Geometry remains in the declared COLLADA scene axes; measurements use mm.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
IDENTITY=[[int(i==j) for j in range(4)] for i in range(4)]
def multiply(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def point(m,p):return [sum(m[i][k]*p[k] for k in range(3))+m[i][3] for i in range(3)]
def bounds(points):return [min(p[i] for p in points) for i in range(3)]+[max(p[i] for p in points) for i in range(3)]
def size(b):return [b[i+3]-b[i] for i in range(3)]

def inspect(path):
    original_hash=sha(path)
    root=ET.parse(path).getroot()
    ns={'c':root.tag.split('}')[0][1:]}
    ids={e.attrib['id']:e for e in root.iter() if 'id' in e.attrib}
    asset=root.find('c:asset',ns)
    unit=asset.find('c:unit',ns)
    to_mm=float(unit.attrib['meter'])*1000
    materials={e.attrib['id']:e.attrib.get('name') for e in root.findall('c:library_materials/c:material',ns)}
    images=[dict(id=e.attrib['id'],uri=e.find('c:init_from',ns).text)
            for e in root.findall('c:library_images/c:image',ns)]
    all_points=[]
    records=[]
    matrices=[]
    def walk(node,parent=IDENTITY,ancestry=(),visited=()):
        matrix=parent
        name=node.attrib.get('name',node.attrib.get('id','?'))
        path_names=ancestry+(name,)
        for transform in node:
            tag=transform.tag.split('}')[-1]
            if tag=='matrix':
                values=list(map(float,transform.text.split()))
                assert len(values)==16
                local=[values[i:i+4] for i in range(0,16,4)]
                # This SketchUp file serializes affine rows. Checking the last
                # row prevents accidental perspective/translation transpose.
                assert max(abs(local[3][i]-(1 if i==3 else 0)) for i in range(4))<1e-7
                matrix=multiply(matrix,local)
                matrices.append(dict(node='/'.join(path_names),local_affine_rows=local))
            elif tag in ['translate','scale','rotate','lookat','skew']:
                raise ValueError('Unexpected transform kind:'+tag)
        for child in node:
            tag=child.tag.split('}')[-1]
            if tag=='instance_geometry':
                geometry=ids[child.attrib['url'][1:]]
                mesh=geometry.find('c:mesh',ns)
                vertices=mesh.find('c:vertices',ns)
                source=ids[vertices.find('c:input[@semantic="POSITION"]',ns).attrib['source'][1:]]
                numbers=list(map(float,source.find('c:float_array',ns).text.split()))
                accessor=source.find('c:technique_common/c:accessor',ns)
                stride=int(accessor.attrib.get('stride',3));offset=int(accessor.attrib.get('offset',0))
                coords=[numbers[offset+i*stride:offset+i*stride+3] for i in range(int(accessor.attrib['count']))]
                used=set();triangles=lines=0
                for primitive in mesh:
                    kind=primitive.tag.split('}')[-1]
                    if kind not in ['triangles','lines','polylist','polygons']:continue
                    if kind not in ['triangles','lines']:raise ValueError('Unexpected primitive:'+kind)
                    inputs=primitive.findall('c:input',ns)
                    width=max(int(i.attrib.get('offset',0)) for i in inputs)+1
                    position_offset=int(next(i for i in inputs if i.attrib['semantic']=='VERTEX').attrib.get('offset',0))
                    count=0
                    for indices in primitive.findall('c:p',ns):
                        values=list(map(int,indices.text.split()))
                        assert len(values)%width==0
                        used.update(values[position_offset::width]);count+=len(values)//width
                    expected=int(primitive.attrib['count'])
                    assert count==expected*(3 if kind=='triangles' else 2)
                    if kind=='triangles':triangles+=expected
                    else:lines+=expected
                points=[[v*to_mm for v in point(matrix,coords[i])] for i in used]
                b=bounds(points);all_points.extend(points)
                bindings=[dict(symbol=i.attrib['symbol'],material_id=i.attrib['target'][1:],material_name=materials.get(i.attrib['target'][1:]))
                          for i in child.findall('c:bind_material/c:technique_common/c:instance_material',ns)]
                records.append(dict(geometry_id=geometry.attrib['id'],scene_path='/'.join(path_names),
                                    bounds_mm=b,size_mm=size(b),triangles=triangles,line_segments=lines,
                                    used_position_indices=len(used),material_bindings=bindings))
            elif tag=='instance_node':
                target=child.attrib['url'][1:]
                assert target not in visited,'Cyclic instance graph'
                walk(ids[target],matrix,path_names,visited+(target,))
            elif tag=='node':walk(child,matrix,path_names,visited)
    scene=ids[root.find('c:scene/c:instance_visual_scene',ns).attrib['url'][1:]]
    for node in scene.findall('c:node',ns):walk(node)
    b=bounds(all_points)
    groups=[]
    for path_names in sorted({r['scene_path'] for r in records}):
        group=[r for r in records if r['scene_path']==path_names]
        bb=[min(r['bounds_mm'][i] for r in group) for i in range(3)]+[max(r['bounds_mm'][i] for r in group) for i in range(3,6)]
        groups.append(dict(scene_path=path_names,geometry_instances=len(group),bounds_mm=bb,size_mm=size(bb)))
    assert sha(path)==original_hash
    return dict(schema_version=1,passed=True,review_date='2026-10-15',input_filename=path.name,
                input_bytes=path.stat().st_size,input_sha256=original_hash,
                authoring_tool=asset.find('c:contributor/c:authoring_tool',ns).text,
                created=asset.find('c:created',ns).text,modified=asset.find('c:modified',ns).text,
                declared_unit=dict(name=unit.attrib.get('name'),meters_per_unit=float(unit.attrib['meter']),mm_per_unit=to_mm),
                up_axis=asset.find('c:up_axis',ns).text,
                method='Parse original XML position indices, visual_scene/instance_node hierarchy and validated affine matrices; apply declared unit25.4mm once. No asset conversion or axis normalization.',
                matrices=matrices,geometry_definitions=len(root.findall('c:library_geometries/c:geometry',ns)),
                geometry_instances=len(records),triangle_count=sum(r['triangles'] for r in records),
                line_segment_count=sum(r['line_segments'] for r in records),
                material_count=len(materials),materials=materials,images=images,
                world_bounds_mm=b,world_size_mm=size(b),groups=groups,geometry_records=records,
                source_unchanged=True,
                limitations=['Node names and IDs do not identify electrical pin numbers; no invented pin-number mapping.',
                             '725listingpolygons and listing17materials/mmunits are page metadata; this export uses4122triangles/10materials/inchunits. These are not interchangeable counts or a license/identity proof.',
                             'Older exported mesh differs from current drawing; do not scale, trim or assert fit before separate geometry/footprint review.'],
                physical_fit_qualified=False,manufacturer_CAD_provenance_verified=False,model_integrated=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('dae',type=Path)
    print(json.dumps(inspect(parser.parse_args().dae),indent=2))

if __name__=='__main__':main()
