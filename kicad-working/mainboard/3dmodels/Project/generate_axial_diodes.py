#!/usr/bin/env python3
"""Generate source-pitch diode illustrations with continuous formed leads.

Run with /Applications/FreeCAD.app/Contents/Resources/bin/python.
These are original parametric illustrations, not manufacturer-supplied CAD.
Body and lead envelopes use the linked Vishay manufacturer drawings; forming,
standoff, cut length, colors and band width are illustrative choices.
SPDX-License-Identifier: CC0-1.0
"""
import hashlib
import json
import math
from pathlib import Path
import re
import sys

sys.path.insert(0, "/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD as App
import Part

OUTPUT = Path(__file__).resolve().parent
V = App.Vector

SPECS = [
    dict(name="D_DO35_P7.112_Illustration", local_footprint="DO35-10",
         part="1N4148", pitch=7.112, body_length=3.4, body_diameter=1.75,
         lead_diameter=0.55, original_drill=1.0, body_standoff=0.35,
         bend_radius=0.70, cut_end_z=-2.5, band_start=-1.40,
         band_width=0.50, body_color=[0.74, 0.28, 0.08],
         sources=[dict(url="https://www.vishay.com/docs/81857/1n4148.pdf",
                       document="Vishay 81857, Rev. 1.6, 07-Nov-2024, page 3",
                       dimensions="DO35 body length max 3.4 mm, diameter 1.50 to 1.75 mm, lead diameter max 0.55 mm; cathode band identifies cathode.")]),
    dict(name="D_DO41_P11.176_Illustration", local_footprint="DO41-10",
         part="1N4001", pitch=11.176, body_length=5.2, body_diameter=2.7,
         lead_diameter=0.86, original_drill=1.2, body_standoff=0.35,
         bend_radius=1.00, cut_end_z=-2.5, band_start=-2.25,
         band_width=0.65, body_color=[0.10, 0.10, 0.11],
         sources=[dict(url="https://www.vishay.com/docs/88503/1n4001.pdf",
                       document="Vishay 88503, Revision 29-Apr-2020, pages 1 and 4",
                       dimensions="DO41 body length 4.1 to 5.2 mm, body diameter 2.0 to 2.7 mm, standard lead diameter 0.71 to 0.86 mm; color band denotes cathode. The optional E lead suffix has smaller leads and is not assumed.")]),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def left_lead(spec):
    z = spec["body_standoff"] + spec["body_diameter"] / 2
    halfpitch = spec["pitch"] / 2
    radius = spec["bend_radius"]
    # Embed 0.05 mm into the illustrated body to avoid disconnected CAD gaps.
    start = V(-spec["body_length"] / 2 + 0.05, 0, z)
    tangent1 = V(-halfpitch + radius, 0, z)
    mid = V(-halfpitch + radius - radius / math.sqrt(2), 0,
            z - radius + radius / math.sqrt(2))
    tangent2 = V(-halfpitch, 0, z - radius)
    end = V(-halfpitch, 0, spec["cut_end_z"])
    path = Part.Wire([Part.makeLine(start, tangent1),
                      Part.Arc(tangent1, mid, tangent2).toShape(),
                      Part.makeLine(tangent2, end)])
    section = Part.Wire(Part.makeCircle(spec["lead_diameter"] / 2,
                                       start, V(1, 0, 0)))
    solid = path.makePipeShell([section], True, False)
    assert solid.isValid() and len(solid.Solids) == 1
    expected_volume = path.Length * math.pi * (spec["lead_diameter"] / 2) ** 2
    assert abs(solid.Volume - expected_volume) < 1e-7
    return solid, dict(path_length_mm=path.Length,
                       volume_mm3=solid.Volume,
                       circular_sweep_volume_mm3=expected_volume,
                       continuous_solid=True,
                       start_xyz_mm=list(start),
                       hole_axis_xyz_mm=[-halfpitch, 0, 0],
                       lower_end_xyz_mm=list(end))


def set_step_colors(path, color_by_name, original_parts):
    """Add original AP214 presentation data to a geometry-only STEP export."""
    text = path.read_text()
    entities = {int(m[1]): m[2] for m in
                re.finditer(r"#(\d+)\s*=\s*(.*?)\s*;", text, re.S)}
    next_number = max(entities) + 1
    definitions = []

    def add(expression):
        nonlocal next_number
        number = next_number
        next_number += 1
        definitions.append("#{} = {};".format(number, expression))
        return number

    # Part.export emits one compound with anonymous solids in input order.
    # Verify that order through actual STEP reimport centroid, volume and bbox
    # comparisons before attaching labels and per-solid presentation colors.
    reimported = Part.read(str(path)).Solids
    assert len(reimported) == len(original_parts) == len(color_by_name)
    for imported, original in zip(reimported, original_parts):
        assert (imported.CenterOfMass - original.Shape.CenterOfMass).Length < 1e-8
        assert abs(imported.Volume - original.Shape.Volume) < 1e-8
        assert abs(imported.BoundBox.XMin - original.Shape.BoundBox.XMin) < 1e-8
        assert abs(imported.BoundBox.XMax - original.Shape.BoundBox.XMax) < 1e-8
    styles = []
    found = set()
    labels = iter(color_by_name)
    for number, value in entities.items():
        match = re.fullmatch(r"MANIFOLD_SOLID_BREP\('([^']*)',#\d+\)", value)
        if not match:
            continue
        label = next(labels)
        assert label in color_by_name, (label, color_by_name)
        text = re.sub(r"(#{}\s*=\s*MANIFOLD_SOLID_BREP\()''".format(number),
                      lambda m: m[1] + "'" + label + "'", text)
        found.add(label)
        rgb = color_by_name[label]
        color = add("COLOUR_RGB('',{},{},{})".format(*rgb))
        area_color = add("FILL_AREA_STYLE_COLOUR('',#{})".format(color))
        area = add("FILL_AREA_STYLE('',(#{}))".format(area_color))
        fill = add("SURFACE_STYLE_FILL_AREA(#{})".format(area))
        side = add("SURFACE_SIDE_STYLE('',(#{}))".format(fill))
        usage = add("SURFACE_STYLE_USAGE(.BOTH.,#{})".format(side))
        assignment = add("PRESENTATION_STYLE_ASSIGNMENT((#{}))".format(usage))
        styles.append(add("STYLED_ITEM('original parametric color',(#{}),#{})".format(assignment, number)))
    assert found == set(color_by_name), (found, set(color_by_name))
    contexts = [n for n, e in entities.items()
                if "GEOMETRIC_REPRESENTATION_CONTEXT(3)" in e]
    assert contexts
    add("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',({}),#{})".format(
        ",".join("#{}".format(s) for s in styles), contexts[0]))
    marker = "ENDSEC;\nEND-ISO-10303-21;"
    assert marker in text
    path.write_text(text.replace(marker, "\n".join(definitions) + "\n" + marker))
    return dict(styled_solids=sorted(found), color_by_solid=color_by_name)


def validate_export(path, spec, export_volume):
    shape = Part.read(str(path))
    assert shape.isValid() and len(shape.Solids) == 5
    assert abs(shape.Volume - export_volume) < 1e-6
    # Cross-sections through each through-board lead at Z=-1 prove their centers
    # and circular diameters survived actual STEP export/reimport.
    plane = Part.makePlane(50, 50, V(-25, -25, -1), V(0, 0, 1))
    section = shape.section(plane)
    circles = []
    for edge in section.Edges:
        curve = edge.Curve
        if hasattr(curve, "Radius") and hasattr(curve, "Center"):
            center = curve.Center
            if abs(center.z + 1) < 1e-8:
                circles.append(dict(center_xyz_mm=list(center), radius_mm=curve.Radius))
    assert len(circles) == 2, circles
    circles.sort(key=lambda c: c["center_xyz_mm"][0])
    for circle, x in zip(circles, [-spec["pitch"] / 2, spec["pitch"] / 2]):
        assert abs(circle["center_xyz_mm"][0] - x) < 1e-8
        assert abs(circle["center_xyz_mm"][1]) < 1e-8
        assert abs(circle["radius_mm"] - spec["lead_diameter"] / 2) < 1e-8
    return dict(step_reimport_valid=True, step_reimport_solid_count=len(shape.Solids),
                step_reimport_volume_mm3=shape.Volume,
                lead_sections_at_z_minus_1_mm=circles,
                nominal_original_drill_radial_margin_mm=(spec["original_drill"] - spec["lead_diameter"]) / 2)


def generate(spec):
    doc = App.newDocument(spec["name"])
    z = spec["body_standoff"] + spec["body_diameter"] / 2
    lo, hi = -spec["body_length"] / 2, spec["body_length"] / 2
    band_lo = spec["band_start"]
    band_hi = band_lo + spec["band_width"]
    assert lo < band_lo < band_hi < 0 < hi
    body_segments = [("CathodeBodyEnd", lo, band_lo, spec["body_color"]),
                     ("CathodeBand", band_lo, band_hi,
                      [0.025, 0.025, 0.025] if spec["part"] == "1N4148" else [0.72, 0.72, 0.72]),
                     ("AnodeBody", band_hi, hi, spec["body_color"])]
    parts, colors = [], {}
    for name, xlo, xhi, color in body_segments:
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = Part.makeCylinder(spec["body_diameter"] / 2,
                                      xhi - xlo, V(xlo, 0, z), V(1, 0, 0))
        assert obj.Shape.isValid()
        parts.append(obj)
        colors[name] = color
    lead_c, lead_record = left_lead(spec)
    lead_a = lead_c.copy()
    lead_a.rotate(V(0, 0, 0), V(0, 0, 1), 180)
    for name, shape in (("CathodeLead", lead_c), ("AnodeLead", lead_a)):
        obj = doc.addObject("Part::Feature", name)
        obj.Shape = shape
        parts.append(obj)
        colors[name] = [0.68, 0.70, 0.73]
    doc.recompute()
    compound = Part.makeCompound([obj.Shape for obj in parts])
    assert compound.isValid()
    joined = parts[0].Shape
    for obj in parts[1:]:
        joined = joined.fuse(obj.Shape)
    assert joined.isValid() and len(joined.Solids) == 1
    path = OUTPUT / (spec["name"] + ".step")
    Part.export(parts, str(path))
    colors_record = set_step_colors(path, colors, parts)
    validation = validate_export(path, spec, compound.Volume)
    App.closeDocument(doc.Name)
    return dict(specification=spec, classification="generic_parametric_package_illustration_exact_pitch",
                manufacturer_exact_cad=False, original_parametric_geometry=True,
                step_path=str(path), step_sha256=sha(path), offset_mm=[0, 0, 0],
                rotate_degrees=[0, 0, 0], scale=[1, 1, 1],
                terminal_mapping={"negative_x": "C", "positive_x": "A"},
                cathode_band_negative_x=True, fully_joined_geometry=True,
                lead_c_record=lead_record, presentation=colors_record,
                validation=validation,
                illustration_choices=["0.35 mm body underside standoff", "formed lead bend radius", "2.5 mm lead tail below PCB top", "body color and cathode band width", "no printed text or exact internal construction"],
                limitations="Body and lead maxima reflect one primary manufacturer's package drawing, not identification of historically fitted parts. Forming/standoff/tail/colors are explicit illustration choices. No fabrication, tolerance or assembly approval.")


def main():
    OUTPUT.mkdir(exist_ok=True)
    records = [generate(spec) for spec in SPECS]
    result = dict(generator=str(Path(__file__).name), generator_sha256=sha(Path(__file__)),
                  freecad_version=App.Version(), models=records)
    (OUTPUT / "axial-diode-dimensional-record.json").write_text(json.dumps(result, indent=2) + "\n")
    hardware = OUTPUT.parents[3]
    sys.path.insert(0, str(hardware / "kicad-import/validation"))
    from verify_native_projects import children, one, parse_sexpr, property_value
    recommendations = []
    for project in ("mainboard", "ioboard"):
        project_dir = hardware / "kicad-working" / project
        board = parse_sexpr((project_dir / (project + ".kicad_pcb")).read_text())
        for record in records:
            spec = record["specification"]
            selected = [f for f in children(board, "footprint")
                        if f[1].split(":")[-1] == spec["local_footprint"]]
            if not selected:
                continue
            original_library = project_dir / (project + "-import-fps.pretty") / (spec["local_footprint"] + ".kicad_mod")
            checked = []
            for f in selected:
                assert property_value(f, "Value", "value") == spec["part"]
                pad_by_name = {p[1]: p for p in children(f, "pad")}
                for number, x in (("C", -spec["pitch"] / 2), ("A", spec["pitch"] / 2)):
                    pad = pad_by_name[number]
                    position = [float(v) for v in one(pad, "at")[1:3]]
                    assert abs(position[0] - x) < 1e-9 and abs(position[1]) < 1e-9
                    assert abs(float(one(pad, "drill")[1]) - spec["original_drill"]) < 1e-9
                checked.append(property_value(f, "Reference", "reference"))
            recommendations.append(dict(project=project,
                local_footprint=spec["local_footprint"], references=sorted(checked),
                count=len(checked), classification=record["classification"],
                manufacturer_exact=False, selected=True,
                original_parametric_geometry=True,
                model_source_path=record["step_path"],
                model_relative_path="generated/" + Path(record["step_path"]).name,
                model_sha256=record["step_sha256"],
                original_local_library_sha256=sha(original_library),
                offset_mm=[0, 0, 0], scale=[1, 1, 1], rotate_degrees=[0, 0, 0],
                terminal_mapping={"C": [-spec["pitch"] / 2, 0], "A": [spec["pitch"] / 2, 0]},
                lead_center_residual_mm=0,
                original_drill_mm=spec["original_drill"],
                lead_radius_mm=spec["lead_diameter"] / 2,
                nominal_radial_margin_mm=record["validation"]["nominal_original_drill_radial_margin_mm"],
                sources=spec["sources"], limitations=record["limitations"]))
    (OUTPUT / "axial-diode-recommendations.json").write_text(json.dumps(
        dict(selected_instance_count=sum(m["count"] for m in recommendations), models=recommendations),
        indent=2) + "\n")
    print(json.dumps({"models": [r["specification"]["name"] for r in records],
                      "selected_instances": sum(m["count"] for m in recommendations),
                      "validated": True}))


if __name__ == "__main__":
    main()
