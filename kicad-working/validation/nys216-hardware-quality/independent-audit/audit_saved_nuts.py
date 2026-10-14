"""Measure the three refined nuts from freshly loaded saved Blender geometry.

No generation manifest values are used as measurements. Cross-sections,
extents, radii, connectedness and volume come directly from saved mesh data.
The bore axis comes from evaluated native-connector and nut instance matrices.
"""
import bpy
import bmesh
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REFS = ('HEADPHONE0', 'MIXIN0', 'MIXOUT0')
checks = []


def check(name, passed, **details):
    checks.append(dict(check=name, passed=bool(passed), **details))


def hull(points):
    points = sorted(set((round(x, 9), round(y, 9)) for x, y in points))
    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower, upper = [], []
    for p in points:
        # Saved vertex coordinates are float32 metres. Drop collinear edge
        # subdivisions within 1e-4 mm^2 rather than counting float noise as
        # additional wrench flats.
        while len(lower) > 1 and cross(lower[-2], lower[-1], p) <= 1e-4:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) > 1 and cross(upper[-2], upper[-1], p) <= 1e-4:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def cross_section(mesh, z_mm):
    points = []
    z = z_mm / 1000
    for triangle in mesh.loop_triangles:
        vertices = [mesh.vertices[i].co for i in triangle.vertices]
        for a, b in zip(vertices, vertices[1:] + vertices[:1]):
            da, db = a.z-z, b.z-z
            if abs(da) < 1e-10:
                points.append((a.x*1000, a.y*1000))
            if da * db < 0:
                f = da / (da-db)
                points.append(((a.x+(b.x-a.x)*f)*1000,
                               (a.y+(b.y-a.y)*f)*1000))
    return hull(points)


def widths(polygon):
    result = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        dx, dy = b[0]-a[0], b[1]-a[1]
        length = math.hypot(dx, dy)
        projection = [(-dy*x+dx*y)/length for x, y in polygon]
        result.append(max(projection)-min(projection))
    return result


path = Path(bpy.data.filepath)
digest = hashlib.sha256(path.read_bytes()).hexdigest()
scene = bpy.context.scene
original_frame = scene.frame_current
scene.frame_set(1)
bpy.context.view_layer.update()
displayed = {}
for instance in bpy.context.evaluated_depsgraph_get().object_instances:
    name = instance.object.original.name
    if name in [f'IOBOARD/{r}/mesh' for r in REFS] + [f'{r} / black PA6 nut proxy' for r in REFS]:
        displayed.setdefault(name, []).append(instance.matrix_world.copy())
measurements = []
for reference in REFS:
    name = reference + ' / black PA6 nut proxy'
    native_name = 'IOBOARD/' + reference + '/mesh'
    check(name + ' has exactly one evaluated displayed instance',
          len(displayed.get(name, [])) == len(displayed.get(native_name, [])) == 1)
    obj = bpy.data.objects[name]
    mesh = obj.data
    mesh.calc_loop_triangles()
    vertices = [v.co.copy() for v in mesh.vertices]
    lo = [min(v[i] for v in vertices)*1000 for i in range(3)]
    hi = [max(v[i] for v in vertices)*1000 for i in range(3)]
    center = Vector(((lo[0]+hi[0])/2000, (lo[1]+hi[1])/2000, 0))
    outer = [v for v in vertices if math.hypot(v.x-center.x, v.y-center.y)*1000 > 8.70]
    radii = [math.hypot(v.x-center.x, v.y-center.y)*1000 for v in outer]
    flange_z = [v.z*1000 for v in outer]
    profile = cross_section(mesh, 0.)
    hex_widths = widths(profile)
    check(name + ' has 5 mm total depth and unchanged rear seating plane',
          abs(lo[2]+2.5) < .001 and abs(hi[2]-2.5) < .001,
          z_min_mm=lo[2], z_max_mm=hi[2], total_depth_mm=hi[2]-lo[2])
    check(name + ' has a 17.5 mm circular flange',
          len(radii) >= 64 and max(abs(r-8.75) for r in radii) < .001,
          radial_sample_count=len(radii), diameter_min_mm=2*min(radii),
          diameter_max_mm=2*max(radii), fitted_outer_center_mm=list(center*1000))
    check(name + ' flange is 1.5 mm thick at the rear',
          abs(min(flange_z)+2.5) < .001 and abs(max(flange_z)+1.) < .001,
          flange_z_min_mm=min(flange_z), flange_z_max_mm=max(flange_z),
          flange_thickness_mm=max(flange_z)-min(flange_z))
    check(name + ' central cross-section has six 15 mm wrench flats',
          len(profile) == 6 and all(abs(w-15.) < .002 for w in hex_widths),
          hull_mm=profile, across_flats_mm=hex_widths)
    corner_radii = [math.hypot(x-center.x*1000, y-center.y*1000) for x, y in profile]
    check(name + ' hex corners match the 15 mm AF geometric consequence',
          all(abs(r-15/math.sqrt(3)) < .002 for r in corner_radii),
          corner_diameters_mm=[2*r for r in corner_radii])
    # Near the tangent of the rounded profile, preceding rings are less than
    # .001 mm behind the end face. Select the actual end plane rather than a
    # slab containing those larger preceding rings.
    front = [v for v in vertices if abs(v.z*1000-hi[2]) < .00001]
    front_radii = [math.hypot(v.x-center.x, v.y-center.y)*1000 for v in front]
    check(name + ' illustrated rounded front edge remains within the source envelope',
          abs(max(front_radii)-7.5) < .002,
          front_outer_diameter_mm=2*max(front_radii),
          unsized_illustration=True)
    rounded_measurements = []
    # Boolean trimming creates extra vertices at partial flat/curve boundary
    # levels. Such a level is not a complete radial ring, so its maximum
    # vertex radius is not the cap radius. Measure the declared arc stations,
    # which retain their actual cap vertices at the untrimmed corner sectors.
    for station in range(65):
        declared_z = 1.95+.55*math.sin(station*math.pi/128)
        group = [v for v in vertices if abs(v.z*1000-declared_z) < .00001]
        if not group:
            continue
        z_mm = sum(v.z*1000 for v in group)/len(group)
        radius_mm = max(math.hypot(v.x-center.x, v.y-center.y)*1000 for v in group)
        fraction = max(0., min(1., (z_mm-1.95)/.55))
        expected_radius = 7.5+(15/math.sqrt(3)-7.5)*math.sqrt(1-fraction*fraction)
        rounded_measurements.append(dict(station=station,z_mm=z_mm, max_radius_mm=radius_mm,
                                         quarter_ellipse_radius_mm=expected_radius,
                                         residual_mm=abs(radius_mm-expected_radius)))
    check(name + ' saved rounded transition follows its declared illustrative profile',
          len(rounded_measurements) >= 32
          and max(p['residual_mm'] for p in rounded_measurements) < .004,
          measured_level_count=len(rounded_measurements),
          max_profile_residual_mm=max(p['residual_mm'] for p in rounded_measurements),
          unsized_illustration=True)
    # Check every clipped vertex too. Additional Boolean boundary vertices
    # need not lie on a complete arc ring, but may never protrude outside the
    # analytic cap or the six support planes. Use the implicit ellipse's
    # normal-distance residual; radial error alone is ill-conditioned near
    # its horizontal tangent at the front face.
    outer_planes = []
    for va, vb in zip(profile, profile[1:]+profile[:1]):
        dx, dy = vb[0]-va[0], vb[1]-va[1]
        length = math.hypot(dx,dy)
        nx, ny = dy/length, -dx/length
        outer_planes.append((nx,ny,nx*va[0]+ny*va[1]))
    rounded_vertices = [v for v in vertices if v.z*1000 >= 1.95-.0001]
    cap_outward = []
    hex_outward = []
    delta = 15/math.sqrt(3)-7.5
    for vertex in rounded_vertices:
        x,y,z = vertex.x*1000,vertex.y*1000,vertex.z*1000
        radius = math.hypot(x-center.x*1000,y-center.y*1000)
        u,v = (radius-7.5)/delta,(z-1.95)/.55
        gradient = math.hypot(2*(radius-7.5)/(delta*delta),
                              2*(z-1.95)/(.55*.55))
        ellipse_out = max(0.,u*u+v*v-1)/gradient if radius > 7.5 else 0.
        cap_outward.append(max(ellipse_out,z-2.5,0.))
        hex_outward.append(max(0.,max(nx*x+ny*y-support
                                    for nx,ny,support in outer_planes)))
    check(name + ' all rounded vertices stay inside the analytic cap and hex envelope',
          max(cap_outward) < .00001 and max(hex_outward) < .00001,
          inspected_vertex_count=len(rounded_vertices),
          max_cap_outward_normal_distance_mm=max(cap_outward),
          max_hex_outward_distance_mm=max(hex_outward),
          numeric_envelope_tolerance_mm=.00001,
          partial_clip_vertices_may_lie_inside=True,
          unsized_illustration=True)
    native = displayed[native_name][0]
    inv = displayed[name][0].inverted()
    axis_point = inv @ (native @ Vector((0, -.0085, .008)))
    axis = (inv.to_3x3() @ (native.to_3x3() @ Vector((0, -1, 0)))).normalized()
    axis_center = axis_point-axis*(axis_point.z/axis.z)
    check(name + ' native socket axis is parallel to the plain bore',
          abs(axis.x) < 1e-6 and abs(axis.y) < 1e-6 and abs(axis.z-1) < 1e-6,
          native_axis_local=list(axis), native_axis_at_local_z0_mm=list(axis_center*1000))
    check(name + ' flange, hex and bore share the actual native mating axis',
          (center-axis_center).length*1000 < .001,
          fitted_outer_center_mm=list(center*1000),
          native_axis_at_local_z0_mm=list(axis_center*1000),
          center_error_mm=(center-axis_center).length*1000)
    bore = [v for v in vertices if (v-axis_center).cross(axis).length*1000 < 5.5]
    bore_radii = [(v-axis_center).cross(axis).length*1000 for v in bore]
    check(name + ' actual saved inner wall is the nominal 9.6 mm native-axis bore',
          bore and max(abs(r-4.8) for r in bore_radii) < .002,
          inner_vertex_count=len(bore), bore_diameter_min_mm=2*min(bore_radii),
          bore_diameter_max_mm=2*max(bore_radii))
    check(name + ' plain bore wall spans the entire nut depth',
          abs(min(v.z for v in bore)*1000-lo[2]) < .001
          and abs(max(v.z for v in bore)*1000-hi[2]) < .001)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    unvisited = set(bm.verts)
    components = 0
    while unvisited:
        components += 1
        queue = [unvisited.pop()]
        while queue:
            vertex = queue.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in unvisited:
                    unvisited.remove(other)
                    queue.append(other)
    signed_volume = bm.calc_volume(signed=True)*1e9
    check(name + ' is one closed manifold solid with positive signed volume',
          components == 1 and all(e.is_manifold for e in bm.edges)
          and signed_volume > 0, connected_components=components,
          signed_volume_mm3=signed_volume,
          nonmanifold_edge_count=sum(not e.is_manifold for e in bm.edges))
    bm.free()
    measurements.append(dict(object=name,local_bounds_mm=lo+hi,
                             cross_section_plane_z_mm=0.,cross_section_hull_mm=profile,
                             nominal_bore_mm=9.6, signed_volume_mm3=signed_volume))
scene.frame_set(original_frame)
bpy.context.view_layer.update()
check('Independent measurement leaves the saved scene bytes unchanged',
      hashlib.sha256(path.read_bytes()).hexdigest() == digest)
failures = [c for c in checks if not c['passed']]
result = dict(passed=not failures, check_count=len(checks), scene=path.name,
              scene_sha256=digest, measured_nut_count=len(measurements),
              measurements=measurements, failures=failures, checks=checks,
              read_only=True, physical_fit_qualified=False,
              limitations=['Front rounded transition, its 0.55 mm depth and 15 mm front circle are undimensioned appearance choices.',
                           'Undimensioned rear features are omitted to preserve the nominal rear seat and total depth.',
                           'Bores are plain illustrations; no thread, torque, interchangeability or physical seating certification.'])
(HERE/'saved-nut-geometry-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in {'checks','measurements'}},indent=2))
assert not failures, 'Independent saved nut geometry audit failed'
