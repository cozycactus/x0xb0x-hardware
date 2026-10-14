"""Add a qualified, display-only harness study without saving the open file.

Run in Blender after loading a revision 5 base scene, or call build() from the
revision builder. Geometry stays at the original assembled poses; only the new
frame 160 view displays this unverified routing study. This script never saves.
"""
from pathlib import Path
import hashlib
import json
import math
import struct
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "harness-sources"
MM = 0.001
FRAME = 160
RADIUS_MM = 0.5
STOCK_MM = 152.4
OVERLAP_MM = 0.05
TITLE = "Wiring routing study — length/fit unverified"
BOARD_NAMES = {
    "mainboard": "Mainboard — B.Cu outward in assembled view",
    "ioboard": "I/O board — rear mounting approximation",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_mesh_hash(mesh):
    digest = hashlib.sha256()
    for vertex in mesh.vertices:
        digest.update(struct.pack("<3f", *vertex.co))
    for edge in mesh.edges:
        digest.update(struct.pack("<2I", *edge.vertices))
    for poly in mesh.polygons:
        digest.update(struct.pack("<I", len(poly.vertices)))
        for index in poly.vertices:
            digest.update(struct.pack("<I", index))
    return digest.hexdigest()


def poses(objects):
    scene = bpy.context.scene
    result = {}
    for frame in [1, 80, 120]:
        scene.frame_set(frame)
        result[str(frame)] = {
            obj.name: {"matrix": [list(row) for row in obj.matrix_world],
                       "hide_render": obj.hide_render,
                       "hide_viewport": obj.hide_viewport}
            for obj in objects
        }
    return result


def material(name, color, unlit=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = 0.46
    if unlit:
        nodes = mat.node_tree.nodes
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = (*color, 1)
        emission.inputs["Strength"].default_value = 1.0
        mat.node_tree.links.new(emission.outputs[0], nodes.get("Material Output").inputs["Surface"])
    return mat


def only_study(obj):
    """Constant visibility keys keep study objects out of every earlier view."""
    for frame, hide in [(1, True), (80, True), (120, True), (159, True),
                        (160, False), (161, True)]:
        obj.hide_render = hide
        obj.hide_viewport = hide
        obj.keyframe_insert(data_path="hide_render", frame=frame)
        obj.keyframe_insert(data_path="hide_viewport", frame=frame)
    obj["classification"] = "Display-only routing study; length and fit unverified"


def polyline(name, points_mm, collection, mat, radius_mm, cyclic=False):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 1
    data.bevel_depth = radius_mm * MM
    data.bevel_resolution = 2
    data.use_fill_caps = True
    spline = data.splines.new("POLY")
    spline.points.add(len(points_mm) - 1)
    for control, point in zip(spline.points, points_mm):
        control.co = (*[v * MM for v in point], 1)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    data.materials.append(mat)
    only_study(obj)
    return obj


def bezier_points(p0, p1, p2, p3, steps=400):
    return [(1-t)**3*p0 + 3*(1-t)**2*t*p1 +
            3*(1-t)*t*t*p2 + t**3*p3
            for t in (i/steps for i in range(steps+1))]


def route(a, b, outward_a, outward_b, ref, pin):
    """Two smooth cubic spans; dimensions here are explicit display choices.

    Departure preserves the native termination tangent. The intervening lane
    and individual-wire twist are illustrative, not measured cable routing.
    The 12-way group is split into two inferred six-wire pieces. No assumption
    about an undocumented 1.27 mm ribbon stock pitch is encoded.
    """
    begin = a - outward_a * OVERLAP_MM
    end = b - outward_b * OVERLAP_MM
    lane = (a + b) * 0.5
    lane.z = {"J3": 13.5, "J4": 31.0, "J5": 36.0,
              "J6": 34.0, "J7": 18.0}[ref]
    if ref == "J3":
        # Six-conductor halves remain separate groups. Both retain actual
        # 2.54 mm endpoint pitch; no connecting web is asserted for midspan.
        lane.y += 2.0 if pin <= 6 else -2.0
    direction = (b - a).normalized()
    mid_handle = min((b-a).length * 0.16, 18.0)
    departure = 2.0 if ref == "J3" else 14.0
    arrival = 14.0
    first = bezier_points(begin, a + outward_a*departure,
                          lane - direction*mid_handle, lane)
    second = bezier_points(lane, lane + direction*mid_handle,
                           b + outward_b*arrival, end)
    return first + second[1:]


def grouped_routes(rows):
    """Transport each fanout row perpendicular to its study centerline.

    This avoids collapsing neighboring wire paths when a cable travels along
    its endpoint pad row. Smooth twist joins the two real numbered pad rows.
    The 2.54 mm midspan separation is a display choice; no physical stock web,
    conductor spacing or torsional/bending qualification is claimed.
    """
    paths = {}
    groups = [("J3", list(range(1, 7))), ("J3", list(range(7, 13)))]
    groups.extend((ref, [1, 2, 3]) for ref in ["J4", "J5", "J6", "J7"])
    for ref, pins in groups:
        ma, io = rows["mainboard", ref], rows["ioboard", ref]
        a = {int(t["pin"]): Vector(t["world_tip_mm"]) for t in ma["tips"]}
        b = {int(t["pin"]): Vector(t["world_tip_mm"]) for t in io["tips"]}
        ca = sum((a[pin] for pin in pins), Vector())/len(pins)
        cb = sum((b[pin] for pin in pins), Vector())/len(pins)
        na = Vector(ma["world_outward_tangent"])
        nb = Vector(io["world_outward_tangent"])
        ra = (a[pins[-1]]-a[pins[0]]).normalized()
        rb = (b[pins[-1]]-b[pins[0]]).normalized()
        center = route(ca, cb, na, nb, ref, pins[0])
        tangents = []
        for i in range(len(center)):
            delta = center[min(i+1, len(center)-1)]-center[max(0, i-1)]
            tangents.append(delta.normalized())
        tangents[0], tangents[-1] = na, -nb
        transported = [ra]
        for before, after in zip(tangents[:-1], tangents[1:]):
            current = before.rotation_difference(after) @ transported[-1]
            transported.append((current-after*current.dot(after)).normalized())
        twist = math.atan2(tangents[-1].dot(transported[-1].cross(rb)), transported[-1].dot(rb))
        for pin in pins:
            points = []
            offset_a = (a[pin]-ca).dot(ra)
            offset_b = (b[pin]-cb).dot(rb)
            for i, (c, tangent, row) in enumerate(zip(center, tangents, transported)):
                t = i/(len(center)-1)
                easing = t*t*(3-2*t)
                axis = Quaternion(tangent, twist*easing) @ row
                points.append(c+axis*((1-easing)*offset_a+easing*offset_b))
            points[0] = a[pin]-na*OVERLAP_MM
            points[-1] = b[pin]-nb*OVERLAP_MM
            paths[ref, pin] = points
    return paths


def ref_of(obj):
    while obj:
        if obj.get("source_reference"):
            return obj["source_reference"]
        obj = obj.parent
    return None


def obstacles():
    """World-space surface BVH, using assembled source instances only."""
    allowed = set(BOARD_NAMES.values()) | {"Case / bottom", "Case / upper",
                                          "Rear panel — original DXF",
                                          "Spacers — original length, approximate seats"}
    vertices, triangles, owners, sources = [], [], [], []
    deps = bpy.context.evaluated_depsgraph_get()
    for inst in deps.object_instances:
        obj = inst.object
        if obj.type != "MESH" or not inst.is_instance:
            continue
        parent_name = inst.parent.original.name if inst.parent else ""
        if parent_name not in allowed:
            continue
        # Intentional overlap with the retained native ribbon stubs is checked
        # separately at the tips. Those five groups are excluded as obstacles.
        if ref_of(obj.original) in {"J3", "J4", "J5", "J6", "J7"}:
            continue
        mesh = obj.to_mesh()
        mesh.calc_loop_triangles()
        start = len(vertices)
        vertices.extend(inst.matrix_world @ vertex.co for vertex in mesh.vertices)
        owner = parent_name + " / " + obj.original.name
        for tri in mesh.loop_triangles:
            triangles.append(tuple(start + index for index in tri.vertices))
            owners.append(owner)
        sources.append({"instance": parent_name, "mesh": obj.original.name,
                        "triangles": len(mesh.loop_triangles)})
        obj.to_mesh_clear()
    assert triangles, "No assembled obstacle surfaces collected"
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True), owners, sources


def surface_screen(points, bvh, owners):
    minimum = math.inf
    close = {}
    crossings = {}
    for point in points:
        near = bvh.find_nearest(point*MM)
        if near[0] is None:
            continue
        distance_mm = near[3]/MM
        minimum = min(minimum, distance_mm)
        if distance_mm < RADIUS_MM:
            name = owners[near[2]]
            close[name] = close.get(name, 0)+1
    for a, b in zip(points[:-1], points[1:]):
        delta = b-a
        if delta.length < 1e-9:
            continue
        hit = bvh.ray_cast(a*MM, delta.normalized(), delta.length*MM)
        if hit[0] is not None:
            name = owners[hit[2]]
            crossings[name] = crossings.get(name, 0)+1
    return {"method": "Centerline samples and segment ray crossings against assembled native surfaces; 0.5 mm insulation radius",
            "minimum_sampled_surface_distance_mm": minimum,
            "radius_intrusion_candidate_surfaces": close,
            "centerline_surface_crossing_candidates": crossings,
            "clearance_certified": False,
            "limitations": "Surface screening cannot certify volumetric fit, flexible forming, bends, tolerances or source-body accuracy. Native J3–J7 stubs are excluded because the new curves intentionally overlap their insulation."}


def pair_screen(routes):
    """Bounded surface-risk screen with spacing uncertainty reported."""
    rows = []
    for index, a in enumerate(routes):
        for b in routes[index+1:]:
            tree = KDTree(len(b["_points"]))
            for i, point in enumerate(b["_points"]):
                tree.insert(point, i)
            tree.balance()
            nearest = min(tree.find(point)[2] for point in a["_points"])
            step_a = max((y-x).length for x, y in zip(a["_points"][:-1], a["_points"][1:]))
            step_b = max((y-x).length for x, y in zip(b["_points"][:-1], b["_points"][1:]))
            lower = nearest - (step_a+step_b)*0.5
            rows.append({"a": a["name"], "b": b["name"],
                         "minimum_sampled_centerline_distance_mm": nearest,
                         "centerline_distance_lower_bound_mm": max(0, lower),
                         "insulation_diameter_mm": 1.0,
                         "possible_intersection": lower < 1.0})
    return rows


def text(name, content, position_mm, collection, mat, size_mm=3.0):
    data = bpy.data.curves.new(name, "FONT")
    data.body = content
    data.size = size_mm*MM
    data.align_x = "CENTER"
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = Vector(position_mm)*MM
    data.materials.append(mat)
    only_study(obj)
    return obj


def build():
    scene = bpy.context.scene
    base_file = Path(bpy.data.filepath) if bpy.data.filepath else None
    base_sha_before = sha(base_file) if base_file else None
    assert not bpy.data.collections.get("DISPLAY / Wiring routing study — unverified"), "Study already exists"
    original_objects = list(scene.objects)
    original_meshes = list(bpy.data.meshes)
    mesh_before = {mesh.name: raw_mesh_hash(mesh) for mesh in original_meshes}
    poses_before = poses(original_objects)
    exposure_before = {}
    for frame in [1, 80, 120]:
        scene.frame_set(frame)
        exposure_before[frame] = scene.view_settings.exposure
    scene.frame_set(1)
    assembled = {obj.name: obj.matrix_world.copy() for obj in original_objects}
    tips = json.loads((SOURCE/"existing-ribbon-termination-endpoints.json").read_text())
    mapping = json.loads((SOURCE/"verified-harness-map.json").read_text())
    assert mapping["passed"] and mapping["conductor_count"] == 24
    rows = {(row["board"], row["reference"]): row for row in tips["endpoints"] if row["frame"] == 1}
    # Check the supplied tips against the current native collection transforms.
    # This prevents stale endpoint placement when reusing the script in revision5.
    endpoint_checks = []
    for (board, ref), row in rows.items():
        instance = bpy.data.objects[BOARD_NAMES[board]]
        roots = {o.get("source_reference"): o for o in instance.instance_collection.objects if o.get("source_reference")}
        pose = instance.matrix_world @ roots[ref].matrix_world
        for tip in row["tips"]:
            actual = pose @ (Vector(tip["canonical_insulation_tip_mm"])*MM)
            expected = Vector(tip["world_tip_mm"])*MM
            error = (actual-expected).length/MM
            assert error < 0.0001, (board, ref, tip["pin"], error)
            endpoint_checks.append({"board": board, "reference": ref, "pin": int(tip["pin"]),
                                    "source_to_current_tip_error_mm": error, "passed": True})
    bvh, owners, obstacle_sources = obstacles()
    collection = bpy.data.collections.new("DISPLAY / Wiring routing study — unverified")
    scene.collection.children.link(collection)
    silver = material("Study / grey insulation", (0.065, 0.075, 0.085))
    stripe = material("Study / low-number stripe", (0.002, 0.003, 0.004))
    cyan = material("Study / mainboard ghost reference", (0.025, 0.60, 0.75), unlit=True)
    ink = material("Study / qualification", (0.012, 0.022, 0.030), unlit=True)
    routes = []
    connection_checks = []
    route_paths = grouped_routes(rows)
    for cable in mapping["cables"]:
        ref = cable["reference"]
        ma, io = rows["mainboard", ref], rows["ioboard", ref]
        main_tips = {int(t["pin"]): t for t in ma["tips"]}
        io_tips = {int(t["pin"]): t for t in io["tips"]}
        for connection in cable["pins"]:
            pin, io_pin = connection["main_pin"], connection["io_pin"]
            assert pin == io_pin, "Do not cross swap J3 pins1/2 due to USB net label differences"
            ta, tb = main_tips[pin], io_tips[io_pin]
            a, b = Vector(ta["world_tip_mm"]), Vector(tb["world_tip_mm"])
            normal_a, normal_b = Vector(ma["world_outward_tangent"]), Vector(io["world_outward_tangent"])
            points = route_paths[ref, pin]
            name = f"STUDY / {ref}.{pin:02d} → {ref}.{io_pin:02d} / same-number conductor"
            obj = polyline(name, points, collection, stripe if pin in ([1, 7] if ref == "J3" else [1]) else silver, RADIUS_MM)
            for board, target, normal, point_index, adjacent_index in [
                    ("mainboard", a, normal_a, 0, 1),
                    ("ioboard", b, normal_b, -1, -2)]:
                actual = Vector(obj.data.splines[0].points[point_index].co[:3])/MM
                expected = target-normal*OVERLAP_MM
                error = (actual-expected).length
                tangent = (points[adjacent_index]-points[point_index]).normalized()
                outward_cosine = tangent.dot(normal)
                assert error < 0.0001 and outward_cosine > 0.95, (board, ref, pin, error, outward_cosine)
                connection_checks.append({"board": board, "reference": ref,
                                          "pin": pin, "curve": name,
                                          "curve_endpoint_to_expected_overlap_error_mm": error,
                                          "curve_endpoint_to_native_insulation_tip_distance_mm": (actual-target).length,
                                          "outward_departure_cosine": outward_cosine,
                                          "closed_curve_cap": obj.data.use_fill_caps,
                                          "passed": True})
            length = sum((y-x).length for x, y in zip(points[:-1], points[1:]))
            above_seat = length + 15.0 - 2*OVERLAP_MM
            obj["main_pin"] = pin
            obj["io_pin"] = io_pin
            obj["harness_connector_ref"] = ref
            obj["centerline_length_mm"] = length
            obj["approx_above_seat_total_with_retained_stubs_mm"] = above_seat
            obj["stock_length_mm"] = STOCK_MM
            obj["stock_comparison_status"] = "Study only: current inferred stubs and seats; no cut length or physical fit claim"
            routes.append({"name": name, "reference": ref, "main_pin": pin, "io_pin": io_pin,
                           "main_net": connection["mainboard"]["net"], "io_net": connection["ioboard"]["net"],
                           "documented_function": connection["documented_function"],
                           "piece": "J3 pins1–6" if ref == "J3" and pin <= 6 else ("J3 pins7–12" if ref == "J3" else ref),
                           "centerline_length_mm": length,
                           "approx_above_seat_total_with_retained_stubs_mm": above_seat,
                           "stock_length_mm": STOCK_MM,
                           "stock_minus_approx_above_seat_total_mm": STOCK_MM-above_seat,
                           "main_tip_mm": list(a), "io_tip_mm": list(b),
                           "span_start_mm": list(points[0]), "span_end_mm": list(points[-1]),
                           "overlap_into_each_native_insulation_tip_mm": OVERLAP_MM,
                           "sample_count": len(points),
                           "max_sample_interval_mm": max((y-x).length for x, y in zip(points[:-1], points[1:])),
                           "surface_screen": surface_screen(points, bvh, owners),
                           "_points": points})
    assert len(routes) == 24 and len(endpoint_checks) == 48
    # Exact mainboard outline is a transformed copy of the original Edge.Cuts,
    # not a fabricated replacement substrate or a modified native object.
    work = HERE.parents[1]
    sys.path.insert(0, str(work.parent/"kicad-import/validation"))
    from verify_native_projects import children, one, parse_sexpr
    tree = parse_sexpr((work/"mainboard/mainboard.kicad_pcb").read_text())
    outline = []
    main_matrix = assembled[BOARD_NAMES["mainboard"]]
    for line in children(tree, "gr_line"):
        if one(line, "layer")[1] != "Edge.Cuts":
            continue
        ends = []
        for key in ["start", "end"]:
            item = one(line, key)
            point = main_matrix @ Vector((float(item[1])*MM, -float(item[2])*MM, 0.000755))
            ends.append(list(point/MM))
        polyline("STUDY / exact mainboard outline ghost", ends, collection, cyan, 0.16)
        outline.append(ends)
    assert len(outline) == 4, "Mainboard source outline unexpectedly changed"
    # Mainboard endpoint markers remain at the true native tips while its body
    # instance is hidden for this inspection. Straight ghosts indicate stubs.
    for (board, ref), row in rows.items():
        normal = Vector(row["world_outward_tangent"])
        for tip in row["tips"]:
            point = Vector(tip["world_tip_mm"])
            polyline(f"STUDY / {board} {ref}.{tip['pin']} native endpoint ghost",
                     [point-normal*7.5, point], collection, cyan, 0.13)
        point = Vector(row["tips"][0]["world_tip_mm"])
        text(f"STUDY / {board} {ref} label", f"{ref}.1 / {'MAIN' if board == 'mainboard' else 'I/O'}",
             [point.x, point.y-4.0, point.z+2.5], collection, cyan, 2.2)
    title = text("STUDY / qualification title", "WIRING ROUTING STUDY\nLength and physical fit unverified", [0, 5, 12], collection, ink, 4.0)
    caption = text("STUDY / qualification caption", "24 same-number connections / cyan = original board endpoints\nJ3 split into two 6-wire groups is inferred; original stubs retained", [0, -10, 12], collection, ink, 2.6)
    # New frame uses original assembled poses, without changing any of the
    # existing inspection-frame poses. Source meshes and object data stay intact.
    hidden = {BOARD_NAMES["mainboard"], "Top panel — original DXF",
              "Front controls — presentation proxies", "Case / upper",
              "Spacers — original length, approximate seats"}
    for obj in original_objects:
        if obj.animation_data and obj.animation_data.action:
            scene.frame_set(120)
            for path in ["location", "rotation_euler", "scale"]:
                obj.keyframe_insert(data_path=path, frame=120)
            obj.matrix_world = assembled[obj.name]
            # Hidden objects may retain the last visible dependency-graph
            # matrix. Settle at the assembled pose before the new hide key.
            for target_frame in [159, 160]:
                for path in ["location", "rotation_euler", "scale"]:
                    obj.keyframe_insert(data_path=path, frame=target_frame)
        # Retain every earlier visibility exactly; isolate frame160 only.
        for frame in [1, 80, 120]:
            obj.hide_render = poses_before[str(frame)][obj.name]["hide_render"]
            obj.hide_viewport = poses_before[str(frame)][obj.name]["hide_viewport"]
            obj.keyframe_insert(data_path="hide_render", frame=frame)
            obj.keyframe_insert(data_path="hide_viewport", frame=frame)
        obj.hide_render = obj.name in hidden or (obj.name == "Historical detached Dimension outline — hidden reference")
        obj.hide_viewport = obj.hide_render
        obj.keyframe_insert(data_path="hide_render", frame=160)
        obj.keyframe_insert(data_path="hide_viewport", frame=160)
    camera_data = bpy.data.cameras.new("Camera / wiring routing study")
    camera = bpy.data.objects.new("Camera / wiring routing study", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (0.015, 0.035, 0.58)
    camera.rotation_euler = (Vector((0, 0.10, 0.022))-camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 0.39
    camera_data.clip_start = 0.001
    camera_data.clip_end = 20
    # Unlit camera-facing review labels stay readable and are explicitly
    # annotation objects, rather than additional enclosure geometry.
    for label, y in [(title, -0.121), (caption, -0.136)]:
        label.parent = camera
        label.location = (0, y, -0.5)
        label.rotation_euler = (0, 0, 0)
        label["classification"] = "Camera-facing review annotation; display-only"
    scene.timeline_markers.new(TITLE, frame=FRAME).camera = camera
    scene.frame_end = max(scene.frame_end, FRAME)
    for frame, exposure in list(exposure_before.items())+[(160, -2.5)]:
        scene.view_settings.exposure = exposure
        scene.view_settings.keyframe_insert(data_path="exposure", frame=frame)
    scene["frame_160"] = TITLE + "; source board/body geometry retained; original assembled endpoint poses"
    scene["harness_status"] = "Display-only routing study, hidden in assembled/exploded/control views. Same-number electrical mapping verified; physical routing and stock fit unresolved."
    pair_checks = pair_screen(routes)
    for row in routes:
        del row["_points"]
    mesh_after = {mesh.name: raw_mesh_hash(mesh) for mesh in original_meshes}
    poses_after = poses(original_objects)
    assert mesh_before == mesh_after, "Source mesh geometry changed"
    assert poses_before == poses_after, "Existing inspection poses/visibility changed"
    visibility_checks = []
    for frame in [1, 80, 120, 159, 160, 161]:
        scene.frame_set(frame)
        expected_hidden = frame != 160
        checked = all(obj.hide_render == expected_hidden and
                      obj.hide_viewport == expected_hidden for obj in collection.objects)
        assert checked
        visibility_checks.append({"frame": frame, "study_hidden": expected_hidden,
                                  "object_count": len(collection.objects), "passed": checked})
    scene.frame_set(160)
    study_pose_checks = []
    for board, name in BOARD_NAMES.items():
        actual = bpy.data.objects[name].matrix_world
        error = max(abs(actual[i][j]-assembled[name][i][j]) for i in range(4) for j in range(4))
        assert error < 1e-6, (board, error, [list(r) for r in actual], [list(r) for r in assembled[name]])
        study_pose_checks.append({"board": board, "assembled_matrix_max_error": error, "passed": True})
    scene.frame_set(1)
    scene.camera = bpy.data.objects["Camera / assembled and exploded"]
    assert not base_file or sha(base_file) == base_sha_before, "Saved base scene changed"
    report = {"classification": "Display-only routing study; no physical fit, bend radius, cable cut length or fabrication claim",
              "saved_automatically": False, "base_scene": bpy.data.filepath,
              "base_scene_sha256": base_sha_before, "saved_base_scene_unchanged": True,
              "display_frame": FRAME, "display_title": TITLE,
              "original_source_mesh_count": len(mesh_before), "all_source_mesh_geometry_unchanged": mesh_before == mesh_after,
              "existing_frames_1_80_120_pose_and_visibility_unchanged": poses_before == poses_after,
              "original_mesh_hashes": mesh_before,
              "existing_frame_poses": poses_before,
              "endpoint_check_count": len(endpoint_checks), "endpoint_checks": endpoint_checks,
              "connection_endpoint_check_count": len(connection_checks), "connection_endpoint_checks": connection_checks,
              "study_visibility_checks": visibility_checks, "study_assembled_board_pose_checks": study_pose_checks,
              "study_exposure": -2.5,
              "conductor_count": len(routes), "physical_piece_count": 6,
              "piece_grouping_basis": mapping["assembly_interpretation"],
              "original_mainboard_outline_world_mm": outline,
              "routing_parameters": {"insulation_diameter_mm": 1.0, "overlap_mm": OVERLAP_MM,
                                     "retained_stub_tip_height_mm": 7.5, "stock_mm": STOCK_MM,
                                     "midspan_pitch": "Independent display wires use a transported fanout row to preserve separation and numbered endpoints. Actual 2.54 mm pad pitch is retained at ends; its continuation through the study is a display assumption, not physical ribbon web/pitch evidence.",
                                     "bend_radius": "Unqualified display path; no manufacturer bend radius available"},
              "routes": routes,
              "surface_screen_obstacle_meshes": obstacle_sources,
              "cable_pair_screen": pair_checks,
              "possible_cable_pair_intersections": [row for row in pair_checks if row["possible_intersection"]],
              "limits": ["J3 straight-tip chord plus the two pre-existing assumed 7.5 mm stubs already exceeds the documented 152.4 mm stock. This conflict is retained and reported, not hidden by shrinking stubs.",
                         "Source component and case models include simplifications and uncertain mounting seats; surface checks are candidate collision screens only.",
                         "All full paths remain hidden in the assembled, exploded and control inspection views, and appear only in the explicitly qualified frame160.",
                         "The study preserves all native board meshes, copper, component geometry and pre-existing termination stub geometry.",
                         "Full paths represent insulation. Native metal ends and solder geometry are not changed. The 0.05 mm overlap prevents a visual gap at the flat original insulation tips."],
              "source_inputs": {name: sha(SOURCE/name) for name in ["existing-ribbon-termination-endpoints.json", "verified-harness-map.json"]}}
    (HERE/"harness-routing-study-audit.json").write_text(json.dumps(report, indent=2)+"\n")
    note = bpy.data.texts.new("READ ME — wiring routing study, physical fit unverified")
    note.write("Frame160 only: "+TITLE+"\n\n"+"\n".join(report["limits"])+"\n\nSee harness-routing-study-audit.json for all 24 curve lengths, original stock comparisons, 48 endpoint checks and unresolved collision screens. No automatic save is performed by this script.\n")
    print(json.dumps({"harness_study_added": True, "conductors": 24, "endpoint_checks": 48,
                      "source_meshes_unchanged": True, "existing_views_unchanged": True,
                      "possible_cable_pair_intersections": len(report["possible_cable_pair_intersections"]),
                      "saved_automatically": False}))
    return report


if __name__ == "__main__":
    build()
