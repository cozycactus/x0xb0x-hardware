"""Read-only sampling probe against the current reconstructed case STL meshes."""
from pathlib import Path
import json, struct, collections, hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
base=Path(__file__).resolve().parent
samples=json.loads((base/'scene-clearance-samples.json').read_text())
manifest=json.loads((base/'case-parts.json').read_text())
shapes=[]
for part in manifest['parts']:
    p=base/part['filename'];data=p.read_bytes()
    count=struct.unpack_from('<I',data,80)[0]
    vertices=[];triangles=[]
    for i in range(count):
        vals=struct.unpack_from('<12fH',data,84+i*50)
        idx=len(vertices)
        vertices.extend([vals[3:6],vals[6:9],vals[9:12]])
        triangles.append((idx,idx+1,idx+2))
    bvh=BVHTree.FromPolygons(vertices,triangles,all_triangles=True,epsilon=1e-6)
    shapes.append((part['name'],part['bbox_mm'],bvh,hashlib.sha256(data).hexdigest()))
directions=[Vector((.314,.5,.812)).normalized(),Vector((.613,-.729,.304)).normalized()]
rows=[]
for r in samples['rows']:
    hits=collections.Counter();examples={};points={}
    for coords in r['samples']:
        for name,bb,bvh,digest in shapes:
            if any(coords[j]<bb['min'][j] or coords[j]>bb['max'][j] for j in range(3)):continue
            inside=True
            for direction in directions:
                location,normal,index,distance=bvh.ray_cast(Vector(coords),direction)
                if location is None or distance<.002 or normal.dot(direction)<.0001:
                    inside=False;break
            if inside:
                hits[name]+=1
                if name not in examples:examples[name]=coords
                points.setdefault(name,[]).append(coords)
    if hits:
        rows.append({'board':r['board'],'reference':r['reference'],
                     'object':r['object'],'hits':dict(hits),
                     'sample_count':len(r['samples']),
                     'first_hit_mm':examples,'bounds':r['bounds'],
                     'inside_sample_points_mm':points})
report={'blend':samples['blend'],'blend_sha256':samples['sha256'],
        'case_stl_sha256':{n:h for n,b,v,h in shapes},
        'sampled_vertices':sum(len(r['samples']) for r in samples['rows']),
        'hit_objects':rows,
        'scope':'Coarse actual-model vertex samples from assembled frame1, tested inside corrected case solids with two ray exit-normal tests. Positive hits are candidate visualization intersections requiring exact confirmation; absence of a sampled hit does not establish clearance. No source or scene edited.'}
(base/'case-clearance-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'sampled_vertices':report['sampled_vertices'],
                  'hit_objects':[{k:v for k,v in r.items() if k!='inside_sample_points_mm'} for r in rows]},indent=2))
