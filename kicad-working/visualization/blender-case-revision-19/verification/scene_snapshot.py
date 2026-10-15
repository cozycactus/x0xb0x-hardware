"""Read-only, repository-relative scene preservation evidence.

Imported by update_rear_openings.py and audit_saved_scene.py. A snapshot
covers stored geometry, shading, hierarchy, collection links, animation data,
curves, editable labels and evaluated transforms in all four existing views.
"""
import gzip
import hashlib
import json
import struct
from pathlib import Path
import bpy

FRAMES = (1, 80, 120, 160)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def value(v):
    if v is None or isinstance(v, (str, bool, int, float)):
        return v
    if isinstance(v, bpy.types.ID):
        return {'id_type': type(v).__name__, 'name': v.name}
    if hasattr(v, 'to_dict'):
        return {str(k): value(x) for k, x in v.to_dict().items()}
    if hasattr(v, 'items'):
        return {str(k): value(x) for k, x in v.items()}
    try:
        return [value(x) for x in v]
    except TypeError:
        return str(v)


def props(obj):
    return {str(k): value(v) for k, v in obj.items()}


def matrix(m):
    return [list(row) for row in m]


def ancestor_reference(obj):
    while obj:
        if obj.get('source_reference'):
            return obj.get('source_board') + '/' + obj['source_reference']
        obj = obj.parent
    return None


def mesh_signature(data):
    digest = hashlib.sha256()
    for v in data.vertices:
        digest.update(struct.pack('<3f', *v.co))
    for e in data.edges:
        digest.update(struct.pack('<2I', *e.vertices))
    for p in data.polygons:
        digest.update(struct.pack('<3I?', len(p.vertices), p.material_index,
                                  p.loop_start, p.use_smooth))
        digest.update(struct.pack('<' + str(len(p.vertices)) + 'I', *p.vertices))
    attributes = {}
    for a in data.attributes:
        if a.name in {'.edge_verts', '.corner_vert', 'position'}:
            continue
        rows = []
        for item in a.data:
            for key in ('value', 'vector', 'color', 'uv'):
                if hasattr(item, key):
                    rows.append(value(getattr(item, key)))
                    break
        attributes[a.name] = dict(data_type=a.data_type, domain=a.domain,
                                  hash=hashlib.sha256(json.dumps(rows,
                                       sort_keys=True).encode()).hexdigest())
    return dict(hash=digest.hexdigest(), vertices=len(data.vertices),
                edges=len(data.edges), polygons=len(data.polygons),
                attributes=attributes, props=props(data),
                materials=[m.name if m else None for m in data.materials])


def material_signature(material):
    data = dict(diffuse_color=list(material.diffuse_color),
                metallic=material.metallic, roughness=material.roughness,
                use_nodes=material.use_nodes, props=props(material), nodes={},
                links=[])
    for key in ('surface_render_method', 'use_transparency_overlap',
                'use_backface_culling', 'use_backface_culling_shadow',
                'alpha_threshold', 'displacement_method'):
        if hasattr(material, key):
            data[key] = value(getattr(material, key))
    if material.node_tree:
        for node in material.node_tree.nodes:
            record = dict(type=node.bl_idname, label=node.label,
                          mute=node.mute, props=props(node), inputs={})
            for key in ('operation', 'blend_type', 'data_type', 'interpolation',
                        'projection', 'distribution', 'subsurface_method',
                        'extension', 'attribute_name', 'uv_map'):
                if hasattr(node, key):
                    record[key] = value(getattr(node, key))
            if hasattr(node, 'image'):
                record['image'] = value(node.image)
            for i, socket in enumerate(node.inputs):
                if hasattr(socket, 'default_value'):
                    record['inputs'][str(i) + ':' + socket.name] = value(socket.default_value)
            data['nodes'][node.name] = record
        data['links'] = sorted((link.from_node.name, link.from_socket.identifier,
                               link.to_node.name, link.to_socket.identifier)
                              for link in material.node_tree.links)
    return data


def curve_signature(data):
    splines = []
    for spline in data.splines:
        splines.append(dict(type=spline.type, use_cyclic_u=spline.use_cyclic_u,
            order_u=spline.order_u, resolution_u=spline.resolution_u,
            points=[dict(co=list(p.co), radius=p.radius, tilt=p.tilt,
                         weight_softbody=p.weight_softbody) for p in spline.points],
            bezier_points=[dict(co=list(p.co), handle_left=list(p.handle_left),
                handle_right=list(p.handle_right), handle_left_type=p.handle_left_type,
                handle_right_type=p.handle_right_type, radius=p.radius, tilt=p.tilt)
                for p in spline.bezier_points]))
    return dict(dimensions=data.dimensions, bevel_depth=data.bevel_depth,
                bevel_resolution=data.bevel_resolution, resolution_u=data.resolution_u,
                use_fill_caps=data.use_fill_caps, splines=splines,
                materials=[m.name if m else None for m in data.materials],
                props=props(data))


def action_signature(action):
    channels = []
    if hasattr(action, 'fcurves'):
        channels.extend(action.fcurves)
    if hasattr(action, 'layers'):
        for layer in action.layers:
            for strip in layer.strips:
                if hasattr(strip, 'channelbags'):
                    for bag in strip.channelbags:
                        channels.extend(bag.fcurves)
    return dict(props=props(action), channels=[dict(
        data_path=f.data_path, array_index=f.array_index,
        extrapolation=f.extrapolation, mute=f.mute,
        keyframes=[dict(co=list(p.co), handle_left=list(p.handle_left),
            handle_right=list(p.handle_right), interpolation=p.interpolation,
            handle_left_type=p.handle_left_type,
            handle_right_type=p.handle_right_type) for p in f.keyframe_points])
        for f in channels])


def font_signature(data):
    """Editable text, all writable scalar/font settings and character style."""
    settings = {}
    for prop in data.bl_rna.properties:
        key = prop.identifier
        if prop.is_readonly or key in {'rna_type', 'name', 'name_full'}:
            continue
        current = getattr(data, key, None)
        if prop.type in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}:
            settings[key] = value(current)
        elif prop.type == 'POINTER' and isinstance(current, bpy.types.ID):
            settings[key] = value(current)
    return dict(settings=settings, props=props(data),
                body_format=[{key: value(getattr(char, key)) for key in
                    ('use_bold', 'use_italic', 'use_underline', 'use_small_caps')}
                    for char in data.body_format],
                text_boxes=[dict(x=t.x, y=t.y, width=t.width, height=t.height)
                            for t in data.text_boxes],
                materials=[m.name if m else None for m in data.materials])


def capture():
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    objects = {}
    for o in bpy.data.objects:
        record = dict(type=o.type, reference=ancestor_reference(o),
            parent=o.parent.name if o.parent else None,
            parent_type=o.parent_type, matrix_parent_inverse=matrix(o.matrix_parent_inverse),
            matrix_basis=matrix(o.matrix_basis), matrix_world=matrix(o.matrix_world),
            collections=sorted(c.name for c in o.users_collection), props=props(o),
            instance_type=o.instance_type,
            instance_collection=o.instance_collection.name if o.instance_collection else None,
            hide_render=o.hide_render, hide_viewport=o.hide_viewport,
            animation_action=o.animation_data.action.name if o.animation_data and o.animation_data.action else None,
            modifiers=[dict(name=m.name, type=m.type) for m in o.modifiers],
            constraints=[dict(name=c.name, type=c.type) for c in o.constraints])
        if o.type == 'MESH':
            record['data'] = mesh_signature(o.data)
        elif o.type == 'CURVE':
            record['data'] = curve_signature(o.data)
        elif o.type == 'FONT':
            record['data'] = font_signature(o.data)
        elif o.type == 'CAMERA':
            record['data'] = {key: value(getattr(o.data, key)) for key in
                ('type', 'lens', 'ortho_scale', 'clip_start', 'clip_end',
                 'sensor_width', 'sensor_height', 'shift_x', 'shift_y')}
        elif o.type == 'LIGHT':
            record['data'] = {key: value(getattr(o.data, key)) for key in
                ('type', 'energy', 'color', 'shadow_soft_size')}
        objects[o.name] = record
    frames = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        frames[str(frame)] = dict(objects={o.name: dict(
            matrix_world=matrix(o.matrix_world), hide_render=o.hide_render,
            hide_viewport=o.hide_viewport) for o in bpy.data.objects}, displayed={}, glyph_geometry={})
        for instance in bpy.context.evaluated_depsgraph_get().object_instances:
            key = instance.object.original.name
            if instance.object.type == 'FONT':
                mesh = instance.object.to_mesh()
                frames[str(frame)]['glyph_geometry'][key] = mesh_signature(mesh)
                instance.object.to_mesh_clear()
            frames[str(frame)]['displayed'].setdefault(key, []).append(
                matrix(instance.matrix_world))
        for instances in frames[str(frame)]['displayed'].values():
            instances.sort(key=lambda m: json.dumps(m))
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return dict(objects=objects, frames=frames,
        fonts={f.name: dict(filepath=f.filepath,
            packed_sha256=hashlib.sha256(bytes(f.packed_file.data)).hexdigest()
            if f.packed_file else None) for f in bpy.data.fonts},
        materials={m.name: material_signature(m) for m in bpy.data.materials},
        actions={a.name: action_signature(a) for a in bpy.data.actions},
        collections={c.name: dict(objects=sorted(o.name for o in c.objects),
            children=sorted(x.name for x in c.children), fake_user=c.use_fake_user,
            hide_viewport=c.hide_viewport, hide_render=c.hide_render, props=props(c))
            for c in bpy.data.collections},
        texts={t.name: t.as_string() for t in bpy.data.texts},
        scene_props=props(scene),
        scene_camera=scene.camera.name if scene.camera else None,
        markers=[dict(name=m.name, frame=m.frame,
                      camera=m.camera.name if m.camera else None)
                 for m in scene.timeline_markers],
        render={key: value(getattr(scene.render, key)) for key in
                ('engine', 'resolution_x', 'resolution_y', 'resolution_percentage',
                 'film_transparent', 'fps', 'fps_base')})


def write_snapshot(path, snapshot):
    """Keep full evidence compact without losing floating-point precision."""
    payload = json.dumps(snapshot, separators=(",", ":")).encode()
    Path(path).write_bytes(gzip.compress(payload, mtime=0))
