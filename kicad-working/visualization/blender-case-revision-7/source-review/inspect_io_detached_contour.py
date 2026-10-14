"""Read-only native GLB outline-component classification."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
base=Path(__file__).resolve().parent.parent
bpy.ops.wm.read_factory_settings(use_empty=True)
p=base/'board-meshes/ioboard.glb'
bpy.ops.import_scene.gltf(filepath=str(p))
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or not o.data.name.startswith('ioboard_'):continue
 vertices=[o.matrix_world@v.co for v in o.data.vertices]
 # Native GLB Y=-KiCad Y; the detached Dimension loop is entirely negative Y.
 chosen={i for i,v in enumerate(vertices) if -.0021601<=v.y<=-.0005079 and -.0040641<=v.x<=.2181861}
 polygons=[poly.index for poly in o.data.polygons if all(i in chosen for i in poly.vertices)]
 used={i for poly in o.data.polygons if poly.index in set(polygons) for i in poly.vertices}
 crossing=[poly.index for poly in o.data.polygons if any(i in chosen for i in poly.vertices) and not all(i in chosen for i in poly.vertices)]
 def bounds(vs):return [[min(v[j] for v in vs)*1000 for j in range(3)],[max(v[j] for v in vs)*1000 for j in range(3)]] if vs else None
 rows.append({'object_name':o.name,'parent':o.parent.name if o.parent else None,
              'vertex_count':len(vertices),'polygon_count':len(o.data.polygons),
              'native_bounds_mm':bounds(vertices),
              'detached_vertex_count':len(used),'detached_polygon_count':len(polygons),
              'detached_bounds_mm':bounds([vertices[i] for i in used]),
              'crossing_polygon_count':len(crossing),
              'detached_vertex_indices':sorted(used),
              'detached_polygon_indices':polygons})
report={'source_GLB':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'frame':'GLB metres/native XYZ=(KiCadX,-KiCadY,Z)',
        'criterion':'Entire polygons with native Y in[-2.159,-0.508]mm andX[-4.064,218.186]mm; this is the detached closed originalDimensionloop.',
        'objects':rows}
(base/'next-review/io-detached-contour-native-meshes.json').write_text(json.dumps(report,indent=2)+'\n')
for r in rows:print({k:v for k,v in r.items() if not k.endswith('_indices')})
