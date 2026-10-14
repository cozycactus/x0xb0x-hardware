"""Coarse read-only interference probe; not a certified collision sweep."""
import FreeCAD as App
import json, collections
from pathlib import Path
base=Path(__file__).resolve().parent
samples=json.loads((base/'scene-clearance-samples.json').read_text())
doc=App.openDocument(str(base/'pactec-pt10-reconstruction.FCStd'))
shapes=[(o.Name,o.Shape) for o in doc.Objects]
rows=[]
for r in samples['rows']:
    hits=collections.Counter(); examples={}
    for coords in r['samples']:
        p=App.Vector(*coords)
        for name,shape in shapes:
            if shape.BoundBox.isInside(p) and shape.isInside(p,.001,False):
                hits[name]+=1
                if name not in examples:examples[name]=coords
    if hits:rows.append({'board':r['board'],'reference':r['reference'],
                         'object':r['object'],'hits':dict(hits),
                         'sample_count':len(r['samples']),
                         'first_hit_mm':examples,'bounds':r['bounds']})
report={'blend':samples['blend'],'blend_sha256':samples['sha256'],
        'sampled_vertices':sum(len(r['samples']) for r in samples['rows']),
        'hit_objects':rows,'scope':'Sampled actual board-model vertices inside approximated case solids at frame 1. A hit is a visualization intersection; absence of a hit does not establish clearance. No source or scene edited.'}
(base/'case-clearance-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'hit_objects':len(rows),'hits':rows},indent=2))
