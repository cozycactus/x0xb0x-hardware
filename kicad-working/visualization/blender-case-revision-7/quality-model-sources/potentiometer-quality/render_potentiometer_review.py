"""Standalone source candidate previews; no delivered scene is opened/saved."""
from pathlib import Path
import bpy, json
from mathutils import Vector
H = Path(__file__).resolve().parent
manifest = json.loads((H/'potentiometer-quality-manifest.json').read_text())
def linear(v): return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4
def material(name, rgb, metal=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*[linear(v) for v in rgb],1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = .30 if metal else .38
    return m
for part in manifest['parts']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = 24
    s.cycles.use_denoising = True
    s.render.resolution_x = s.render.resolution_y = 720
    s.world = bpy.data.worlds.new('Studio')
    s.world.use_nodes = True
    s.world.node_tree.nodes['Background'].inputs[0].default_value = (.66,.66,.66,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value = .55
    s.view_settings.view_transform = 'AgX'
    s.view_settings.exposure = 0
    for seg in part['segments']:
        bpy.ops.wm.stl_import(filepath=seg['stl'],global_scale=.001)
        o = bpy.context.object
        o.name = seg['name']
        metal = .7 if any(x in seg['name'] for x in ('Stamped','Folded','Plate','Rivet')) else 0
        if part['id'].startswith('Alpha') and 'Sleeve' in seg['name']: metal = .7
        o.data.materials.append(material(seg['name'],seg['color_srgb'],metal))
    bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.0002))
    bpy.context.object.data.materials.append(material('Neutral stage',(.56,.58,.61)))
    for position,energy in [((-.045,-.06,.08),.18),((.055,.02,.055),.13)]:
        bpy.ops.object.light_add(type='AREA',location=position)
        o = bpy.context.object
        o.data.energy, o.data.size = energy,.055
        o.rotation_euler = (Vector((0,0,.012))-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    camera.data.clip_start = .001
    camera.data.clip_end = 10
    s.camera = camera
    for view,focus,offset,scale in [('full',.015,(.055,-.09,.063),.043),
                                    ('body',.0045,(-.055,.075,.052),.026)]:
        target = Vector((0,0,focus))
        camera.location = target+Vector(offset)
        camera.rotation_euler = (target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.ortho_scale = scale
        s.render.filepath = str(H/(part['id']+'_'+view+'_review.png'))
        bpy.ops.render.render(write_still=True)
        print(part['id'],view,'rendered',flush=True)
