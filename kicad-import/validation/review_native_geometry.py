#!/usr/bin/env python3
"""Read-only source XML versus saved native PCB geometry and flag checks."""

from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from verify_native_projects import children, one, parse_sexpr, property_value

VAL = Path(__file__).resolve().parent
BASE = VAL.parent
reports = {}


def numeric(node, name, default=0):
    field = one(node, name)
    return float(field[1]) if field else default


def rotate(x, y, degrees):
    angle = math.radians(degrees)
    return (x * math.cos(angle) - y * math.sin(angle),
            x * math.sin(angle) + y * math.cos(angle))


for stem in ("mainboard", "ioboard"):
    path = BASE / stem / (stem + ".kicad_pcb")
    data = path.read_bytes()
    native = parse_sexpr(data.decode("utf-8"))
    source = ET.parse(VAL / "repaired-eagle-xml" / (stem + ".brd")).getroot()
    packages = {(lib.get("name"), pack.get("name")): pack
                for lib in source.findall(".//libraries/library")
                for pack in lib.findall(".//packages/package")}
    footprints = {property_value(fp, "Reference", "reference"): fp
                  for fp in children(native, "footprint")}
    parameters = {p.get("name"): p.get("value")
                  for p in source.findall(".//designrules/param")}
    ring_ratio = float(parameters["rvPadTop"])
    min_ring = float(parameters["rlMinPadTop"].removesuffix("mm"))
    max_ring = float(parameters["rlMaxPadTop"].removesuffix("mm"))
    elongation = float(parameters["psElongationLong"])
    errors, aliases, counts, placement_formats = [], {}, Counter(), Counter()
    maximum_numeric_residuals = {}

    def equal(ref, pad, field, expected, actual):
        if (isinstance(expected, (int, float)) and not isinstance(expected, bool)
                and isinstance(actual, (int, float)) and not isinstance(actual, bool)):
            maximum_numeric_residuals[field] = max(
                maximum_numeric_residuals.get(field, 0), abs(expected - actual))
        good = (abs(expected - actual) <= 0.00001
                if isinstance(expected, (int, float)) and isinstance(actual, (int, float))
                else expected == actual)
        if not good:
            errors.append(dict(reference=ref, pad=pad, field=field,
                               expected=expected, actual=actual))

    for element in source.findall(".//elements/element"):
        ref = element.get("name")
        native_ref = ref if ref in footprints else ref + "0"
        fp = footprints[native_ref]
        if native_ref != ref:
            aliases[ref] = native_ref
        counts["footprints"] += 1
        transform = one(fp, "transform")
        if transform is not None:
            translate = one(transform, "translate")
            orientation = numeric(transform, "rotate")
            scale = one(transform, "scale")
            equal(ref, None, "transform_scale", ["1", "1"], scale[1:])
            placement_formats["transform"] += 1
        else:
            # KiCad 10 serializes the same footprint placement as an at tuple.
            # Pad positions remain local and pad angles remain absolute.
            translate = one(fp, "at")
            assert translate is not None, ref
            orientation = float(translate[3]) if len(translate) > 3 else 0
            placement_formats["legacy_at"] += 1
        equal(ref, None, "footprint_x_mm", float(element.get("x")), float(translate[1]))
        equal(ref, None, "footprint_y_mm", -float(element.get("y")), float(translate[2]))
        mirrored = element.get("mirrored") == "yes"
        counts["mirrored_footprints"] += mirrored
        source_rotation = float(element.get("rot").split("R")[-1])
        package = packages[(element.get("library"), element.get("package"))]
        pads = defaultdict(list)
        for pad in children(fp, "pad"):
            if pad[2] == "np_thru_hole" and pad[1] == "":
                counts["mechanical_holes"] += 1
                continue
            pads[pad[1]].append(pad)
        for source_pad in [p for p in package if p.tag in ("pad", "smd")]:
            number = source_pad.get("name")
            pad = pads[number].pop(0)
            counts["electrical_pads"] += 1
            counts[source_pad.tag] += 1
            at = one(pad, "at")
            native_x, native_y = rotate(float(at[1]), float(at[2]), -orientation)
            native_x += float(translate[1])
            native_y += float(translate[2])
            source_x, source_y = rotate(float(source_pad.get("x")),
                                        float(source_pad.get("y")), source_rotation)
            if mirrored:
                source_x = -source_x
            source_x += float(element.get("x"))
            source_y += float(element.get("y"))
            equal(ref, number, "absolute_x_mm", source_x, native_x)
            equal(ref, number, "absolute_y_mm", -source_y, native_y)
            size = one(pad, "size")
            if source_pad.tag == "pad":
                drill = float(source_pad.get("drill"))
                equal(ref, number, "drill_mm", drill, numeric(pad, "drill"))
                diameter = float(source_pad.get("diameter"))
                if not diameter:
                    diameter = drill + 2 * max(min_ring, min(drill * ring_ratio, max_ring))
                shape = source_pad.get("shape")
                if shape == "round":
                    diameter = max(diameter, drill + 2 * min_ring)
                sx = diameter * (100 + elongation) / 100 if shape == "long" else diameter
                sy = diameter
                expected_shape = {"long": "oval", "round": "circle"}[shape]
                equal(ref, number, "shape", expected_shape, pad[3])
            else:
                sx, sy = float(source_pad.get("dx")), float(source_pad.get("dy"))
                equal(ref, number, "shape", "rect", pad[3])
            equal(ref, number, "size_x_mm", sx, float(size[1]))
            equal(ref, number, "size_y_mm", sy, float(size[2]))
            source_angle = float(source_pad.get("rot", "R0").split("R")[-1])
            native_angle = float(at[3]) if len(at) > 3 else 0
            expected_angle = orientation + (-source_angle if mirrored else source_angle)
            delta = (native_angle - expected_angle + 180) % 360 - 180
            equal(ref, number, "pad_orientation_delta_degrees", 0, delta)
            layers = one(pad, "layers")[1:]
            equal(ref, number, "mask_enabled", source_pad.get("stop", "yes") == "yes",
                  any(layer in ("*.Mask", "F.Mask", "B.Mask") for layer in layers))
            equal(ref, number, "mask_margin_mm", 0.1016, numeric(pad, "solder_mask_margin"))
            zone_connection = one(pad, "zone_connect")
            equal(ref, number, "thermal_connection_inherits_zone", True, zone_connection is None)
            if source_pad.tag == "smd":
                equal(ref, number, "paste_enabled", source_pad.get("cream", "yes") == "yes",
                      any(layer in ("F.Paste", "B.Paste") for layer in layers))
                equal(ref, number, "paste_margin_mm", 0, numeric(pad, "solder_paste_margin"))
        equal(ref, None, "unmatched_native_pad_count", 0, sum(len(p) for p in pads.values()))
    vias = []
    for via in children(native, "via"):
        diameter, drill = numeric(via, "size"), numeric(via, "drill")
        equal(None, None, "via_diameter_mm", 1.0064, diameter)
        equal(None, None, "via_drill_mm", 0.6, drill)
        vias.append(dict(at_mm=[float(v) for v in one(via, "at")[1:3]],
                         diameter_mm=diameter, drill_mm=drill))
    source_via_positions = sorted([float(via.get("x")), -float(via.get("y"))]
                                  for via in source.findall(".//signals/signal/via"))
    native_via_positions = sorted(via["at_mm"] for via in vias)
    equal(None, None, "via_absolute_positions_mm", source_via_positions, native_via_positions)
    reports[stem] = dict(status="pass" if not errors else "fail", counts=dict(counts),
        native_file_version=one(native, "version")[1],
        footprint_placement_formats=dict(placement_formats),
        comparison_tolerance=0.00001,
        maximum_numeric_residuals=maximum_numeric_residuals,
        via_absolute_positions_match_source=source_via_positions == native_via_positions,
        source_reference_to_native_aliases=aliases, vias=vias, errors=errors,
        native_file=str(path), native_sha256=hashlib.sha256(data).hexdigest(),
        scope="All electrical pad absolute positions, sizes, drill dimensions, shape, orientation, mask layers/margins, SMD paste layers/margins, absence of forced-solid pad zone overrides, and all via positions/diameters/drills. Source rotate-then-mirror transform compared with native KiCad 11 transform or KiCad 10 at placement.",
        limitations=["Does not verify routed trace or graphic geometry, zone fill results, manufacturing readiness, or schematic electrical connectivity.",
                     "Source pad thermals=yes maps to inherited zone connection; this check confirms the importer did not force solid connections.",
                     "Importer reference aliases are recorded explicitly; metadata/net-name-only changes may change file hashes without changing geometry."])
(VAL / "native-geometry-review.json").write_text(json.dumps(reports, indent=2) + "\n")
for stem, report in reports.items():
    print(stem, report["status"], report["counts"], "errors", len(report["errors"]))
    for error in report["errors"][:10]:
        print(error)
