"""Standalone candidate previews. No delivered scene opened or saved."""
from pathlib import Path
import bpy,json
from mathutils import Vector
H=Path(__file__).resolve().parent
manifest_path=H/'rear-connector-quality-corrected-manifest.json'
if not manifest_path.exists():manifest_path=H/'rear-connector-quality-manifest.json'
M=json.loads(manifest_path.read_text())
def lin(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def mat(name,rgb,metal=False):
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value=(*[lin(c)for c in rgb],1)
    p.inputs['Metallic'].default_value=.75 if metal else 0
    p.inputs['Roughness'].default_value=.27 if metal else .36
    return m
for part in M['parts']:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32
    s.cycles.use_denoising=True;s.render.resolution_x=900;s.render.resolution_y=820
    s.world=bpy.data.worlds.new('Studio');s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(.7,.7,.7,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=.6
    s.view_settings.view_transform='AgX'
    for f in part['features']:
        bpy.ops.wm.stl_import(filepath=f['stl'],global_scale=.001)
        o=bpy.context.object;o.name=f['name']
        o.data.materials.append(mat(f['name'],f['color_rgb'],f['role']in['contact','bushing']))
        bpy.ops.object.shade_smooth_by_angle(angle=.523598776)
    bpy.ops.mesh.primitive_plane_add(size=2,location=(0,0,-.00015))
    bpy.context.object.data.materials.append(mat('Neutralstage',(.61,.63,.66)))
    cy=(part['exact_bounds_mm'][1]+part['exact_bounds_mm'][4])*.0005
    target=Vector((0,cy,.0049))
    for pos,energy in [((-.045,-.055,.065),.16),((.055,.035,.055),.14),((.0,.05,.07),.1)]:
        bpy.ops.object.light_add(type='AREA',location=pos)
        o=bpy.context.object;o.data.energy=energy;o.data.size=.05
        o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();c=bpy.context.object;c.data.type='ORTHO'
    c.data.clip_start=.001;c.data.clip_end=10;c.data.ortho_scale=.0275;s.camera=c
    front=-1 if part['id'].startswith('MJ')else 1
    for name,offset in [('front',( .034,front*.050,.033)),('rear',(-.034,-front*.050,.033))]:
        c.location=target+Vector(offset)
        c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler()
        s.render.filepath=str(H/(part['id']+'-'+name+'-review.png'))
        bpy.ops.render.render(write_still=True)
        print(part['id'],name,'rendered',flush=True)
