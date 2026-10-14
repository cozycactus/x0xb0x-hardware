#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Inspect the loaded assembly's eleven rear mating apertures without saving.

Run with Blender 5:
  blender --background <assembly.blend> --python-exit-code 1 \
      --python scripts/verify_rear_openings.py

JSON is printed to stdout alongside Blender's own log. No files are written.
This verifier intentionally accepts an older scene for regression comparison;
the separate portability verifier checks PROJECT.json's declared scene/hash.
Dimensions here describe the checked-in drawing-derived illustrations, not
tolerances, insertion forces or certification of a physical assembly.
"""

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


AUDIO = ("HEADPHONE0", "MIXIN0", "MIXOUT0")
SMALL = ("CV0", "GATE0")
DIN = ("DIN1", "DIN2", "DIN3", "DIN4")
REFERENCES = ("POWER0", *AUDIO, *SMALL, "USB0", *DIN)


def circle_samples(radius_mm, fractions=(.70, .95), angles=range(0, 360, 22)):
    samples = [("center", 0., 0.)]
    for fraction in fractions:
        for angle in angles:
            a = math.radians(angle)
            samples.append((f"r{fraction}-a{angle}",
                            radius_mm * fraction * math.cos(a),
                            radius_mm * fraction * math.sin(a)))
    return samples


def verify():
    scene_path = Path(bpy.data.filepath).resolve()
    if not bpy.data.filepath or not scene_path.is_file():
        raise RuntimeError("Load a saved assembly .blend before verification")
    original_hash = hashlib.sha256(scene_path.read_bytes()).hexdigest()
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = {}
    meshes = []
    native = {}
    hardware = {}
    for instance in depsgraph.object_instances:
        obj = instance.object
        if obj.type != "MESH" or obj.hide_render:
            continue
        if instance.parent and instance.parent.hide_render:
            continue
        key = obj.original.as_pointer()
        if key not in trees:
            mesh = obj.to_mesh()
            trees[key] = BVHTree.FromPolygons(
                [v.co.copy() for v in mesh.vertices],
                [list(p.vertices) for p in mesh.polygons],
                all_triangles=False)
            obj.to_mesh_clear()
        matrix = instance.matrix_world.copy()
        points = [matrix @ Vector(p) for p in obj.bound_box]
        item = {"name": obj.original.name, "matrix": matrix,
                "inverse": matrix.inverted(), "tree": trees[key],
                "bounds": ([min(p[i] for p in points) for i in range(3)]
                           + [max(p[i] for p in points) for i in range(3)])}
        meshes.append(item)
        for reference in REFERENCES:
            if obj.original.name == f"IOBOARD/{reference}/mesh":
                if reference in native:
                    raise RuntimeError("Duplicate displayed rear port: "
                                       + reference)
                native[reference] = item
        for reference in AUDIO:
            for suffix in ("black ABS washer proxy", "black PA6 nut proxy"):
                if obj.original.name == f"{reference} / {suffix}":
                    hardware[obj.original.name] = item
    if set(native) != set(REFERENCES):
        raise RuntimeError("Missing native displayed rear connector geometry: "
                           + str(sorted(set(REFERENCES) - set(native))))
    if len(hardware) != 6:
        raise RuntimeError("Expected all six retained audio nut/washer meshes")

    checks = []
    ray_count = 0
    ports = []

    def check(name, passed, **details):
        checks.append({"check": name, "passed": bool(passed), **details})

    def hits(face, outward, depth_mm, candidates):
        """Return first intersection per mesh from outside to target depth."""
        nonlocal ray_count
        ray_count += 1
        origin = face + outward * .035
        direction = -outward
        maximum = .035 + depth_mm / 1000
        result = []
        for item in candidates:
            # Port axes are rear-facing. Include float uncertainty from the
            # evaluated 180-degree instance transform in the bounds filter.
            bb = item["bounds"]
            end = origin + direction * maximum
            if any(max(origin[i], end[i]) < bb[i] - 1e-7
                   or min(origin[i], end[i]) > bb[i + 3] + 1e-7
                   for i in range(3)):
                continue
            inverse = item["inverse"]
            local_origin = inverse @ origin
            local_direction = (inverse.to_3x3() @ direction).normalized()
            hit, normal, index, distance = item["tree"].ray_cast(
                local_origin, local_direction, maximum + 1e-7)
            if hit is not None:
                world = item["matrix"] @ hit
                depth = (face - world).dot(outward) * 1000
                if depth <= depth_mm + .0001:
                    result.append({"object": item["name"],
                                   "depth_from_native_face_mm": depth,
                                   "world_mm": [c * 1000 for c in world],
                                   "face": index})
        return sorted(result, key=lambda h: h["depth_from_native_face_mm"])

    def opening_rays(reference, samples, depth_mm, front_y_mm, axis_z_mm):
        item = native[reference]
        matrix = item["matrix"]
        outward_local = Vector((0, 1 if reference == "POWER0" else -1, 0))
        outward = (matrix.to_3x3() @ outward_local).normalized()
        check(reference + " mating axis faces the exterior", outward.y > .9999,
              outward_axis=list(outward))
        observations = []
        for label, x_mm, dz_mm in samples:
            face = matrix @ Vector((x_mm / 1000, front_y_mm / 1000,
                                    (axis_z_mm + dz_mm) / 1000))
            intersections = hits(face, outward, depth_mm, meshes)
            observations.append({"sample": label, "passed": not intersections,
                                 "first_hit": (intersections[0]
                                               if intersections else None)})
        check(reference + " mating passage reaches its intended depth",
              all(o["passed"] for o in observations),
              ray_count=len(observations), minimum_clear_depth_mm=depth_mm,
              observations=observations)
        ports.append({"reference": reference, "opening_ray_count": len(samples),
                      "minimum_clear_depth_mm": depth_mm,
                      "native_face_axis_world_mm": [c * 1000 for c in
                          matrix @ Vector((0, front_y_mm / 1000,
                                           axis_z_mm / 1000))]})
        return matrix, outward

    # All geometry participates in these casts, including panel, enclosure,
    # detached illustrations and native connector meshes. Absence of a named
    # recess proxy alone cannot make these passage checks pass.
    for reference in AUDIO:
        matrix, outward = opening_rays(
            reference, circle_samples(3.175), 8.6, -8.5, 8.)
        center = matrix @ Vector((0, -.0085, .008))
        native_hits = hits(center, outward, 33., [native[reference]])
        check(reference + " retains its native through bore", not native_hits,
              native_hits=native_hits)
        # Isolate each hardware piece. The native threaded bushing itself is
        # expected at this larger radius and must not be treated as a cap.
        for suffix in ("black ABS washer proxy", "black PA6 nut proxy"):
            name = f"{reference} / {suffix}"
            observations = []
            for label, x_mm, dz_mm in circle_samples(
                    9.525 / 2, (.25, .70, .999), range(0, 360, 11)):
                face = matrix @ Vector((x_mm / 1000, -.0085,
                                        (.008 + dz_mm / 1000)))
                intersections = hits(face, outward, 8.6, [hardware[name]])
                observations.append({"sample": label,
                                     "passed": not intersections,
                                     "first_hit": (intersections[0]
                                                   if intersections else None)})
            check(name + " clears the nominal threaded bushing",
                  all(o["passed"] for o in observations),
                  native_bushing_diameter_mm=9.525,
                  sampled_max_diameter_mm=9.525 * .999,
                  ray_count=len(observations), observations=observations)

    for reference in SMALL:
        matrix, outward = opening_rays(
            reference, circle_samples(1.8), 8.0, -3., 5.5)
        center = matrix @ Vector((0, -.003, .0055))
        native_hits = hits(center, outward, 18., [native[reference]])
        depth = native_hits[0]["depth_from_native_face_mm"] if native_hits else None
        check(reference + " retains its intended recessed blind back",
              depth is not None and 16.8 < depth < 17.3, first_hit_depth_mm=depth)

    matrix, outward = opening_rays(
        "POWER0", [(f"annulus-{a}", 2 * math.cos(math.radians(a)),
                    2 * math.sin(math.radians(a))) for a in range(0, 360, 45)],
        3.0, 0., 6.5)
    native_hits = hits(matrix @ Vector((0, 0, .0065)), outward, 3.,
                       [native["POWER0"]])
    depth = native_hits[0]["depth_from_native_face_mm"] if native_hits else None
    check("POWER0 retains its recessed center mating pin",
          depth is not None and .8 < depth < 1.2, first_hit_depth_mm=depth)

    usb_samples = [("left", -3.2, 0.), ("right", 3.2, 0.),
                   ("below", 0., -2.31), ("above", 0., 2.19),
                   ("upper-left", -2.9, 1.69),
                   ("upper-right", 2.9, 1.69),
                   ("lower-left", -2.9, -2.31),
                   ("lower-right", 2.9, -2.31)]
    matrix, outward = opening_rays("USB0", usb_samples, 5.0, 0., 5.31)
    native_hits = hits(matrix @ Vector((0, 0, .00531)), outward, 3.,
                       [native["USB0"]])
    depth = native_hits[0]["depth_from_native_face_mm"] if native_hits else None
    check("USB0 retains its recessed insulating tongue",
          depth is not None and 1.15 < depth < 1.45, first_hit_depth_mm=depth)

    for reference in DIN:
        matrix, outward = opening_rays(
            reference, circle_samples(7.1, (.95,)), 5.5, 0., 10.)
        native_hits = hits(matrix @ Vector((0, 0, .010)), outward, 7.,
                           [native[reference]])
        depth = native_hits[0]["depth_from_native_face_mm"] if native_hits else None
        check(reference + " retains its intended recessed socket insert",
              depth is not None and 5.65 < depth < 5.95, first_hit_depth_mm=depth)
        contact_results = []
        for angle in (25, 155, 225, 270, 315):
            a = math.radians(angle)
            cx, cz = 3.5 * math.cos(a), 10 + 3.5 * math.sin(a)
            for label, dx, dz in circle_samples(.30, (1.,), range(0, 360, 90)):
                face = matrix @ Vector(((cx + dx) / 1000, 0,
                                        (cz + dz) / 1000))
                intersections = hits(face, outward, 7.3, meshes)
                contact_results.append({"contact_angle_deg": angle,
                                        "sample": label,
                                        "passed": not intersections,
                                        "first_hit": (intersections[0]
                                                      if intersections else None)})
        check(reference + " has five open contact bores through its insert",
              all(o["passed"] for o in contact_results), contact_count=5,
              minimum_clear_depth_mm=7.3, ray_count=len(contact_results),
              observations=contact_results)

    check("Read-only checks left saved scene bytes unchanged",
          hashlib.sha256(scene_path.read_bytes()).hexdigest() == original_hash)
    failures = [c for c in checks if not c["passed"]]
    return {"passed": not failures, "check_count": len(checks),
            "ray_count": ray_count, "rear_port_count": len(native),
            "audio_hardware_count": len(hardware), "scene": str(scene_path),
            "scene_sha256": original_hash, "blender_version": bpy.app.version_string,
            "method": "Frame 1 evaluated dependency-graph instance matrices and "
                      "native per-mesh BVH raycasts from the exterior.",
            "ports": ports, "failures": failures, "checks": checks,
            "read_only": True, "physical_fit_qualified": False,
            "scope": "Sampled visual mating apertures, nominal bushing passage "
                     "and preservation of intended recessed internals; not "
                     "thread, plug, seating, cable-clearance or physical-fit certification."}


original_frame = bpy.context.scene.frame_current
try:
    result = verify()
except Exception as error:
    result = {"passed": False, "read_only": True,
              "error": f"{type(error).__name__}: {error}"}
finally:
    bpy.context.scene.frame_set(original_frame)
    bpy.context.view_layer.update()
print(json.dumps(result, indent=2, allow_nan=False), flush=True)
if not result["passed"]:
    raise RuntimeError("Rear connector opening verification failed; see JSON output")
