#!/usr/bin/env python3
"""Original CC0 package illustrations for reviewed source/BOM families.

Use FreeCAD's bundled Python. This reads the revision-4 input snapshot and writes
only review assets here. Body dimensions come from primary package drawings;
formed leads, mounting standoff, fillets and colors are explicit illustration
choices. No PCB geometry is changed and no stock geometry is thinned/scaled.
SPDX-License-Identifier: CC0-1.0
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

sys.path.insert(0, "/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD as App
import Part

ROOT = Path(__file__).resolve().parent
HARDWARE = ROOT.parents[3]
SNAPSHOT = ROOT.parent / "input-snapshot"
sys.path.insert(0, str(HARDWARE / "kicad-import/validation"))
from verify_native_projects import children, one, parse_sexpr, property_value

V = App.Vector
BOM = "https://www.ladyada.net/make/x0xb0x/fab/parts.html"
EXPANDED_BOM = "https://ladyada.net/wiki/x0x/billofmaterials"
PM = "https://www.mouser.com/datasheet/2/70/pm-190464.pdf"
PF = "https://www.mouser.com/ds/2/70/XC-600181-187468.pdf"
XRL = "https://www.mouser.com/datasheet/2/231/XC-600178-1174881.pdf"
AVX = "https://datasheets.kyocera-avx.com/SR-Series.pdf"
T350 = "https://search.kemet.com/component-documentation/download/specsheet/T350A105K035AT"
TO92 = "https://www.jscj-elec.com/gallery/file/2SC536%20TO-92%20V2.pdf"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spec(name, kind, refs, body, factory_pitch, lead_diameter, source, **extra):
    return dict(name=name, kind=kind, refs=refs, body_mm=body,
                factory_pitch_mm=factory_pitch, lead_diameter_mm=lead_diameter,
                source_urls=[BOM, EXPANDED_BOM, source], **extra)


# Body vector = width X, depth Y, height Z. Values are manufacturer dimensions,
# not dimensions inferred from the old silk. A name with P records actual hole
# pitch, while factory_pitch_mm records the manufacturer's unformed lead pitch.
SPECS = [
    spec("C_AVX_SR205_P2.54_Illustration", "rounded", ["C103", "C104", "C106", "C107", "C108", "C109", "C110", "C111", "C112", "C113", "io:C1", "io:C2", "io:C4", "io:C6", "io:C202", "io:C204"],
         [5.08, 3.175, 5.08], 2.54, 0.508, AVX, part="AVX SR205E104MAR", standoff_mm=0.5, source_outline_mm=[4.572, 2.54], polarity=False),
    spec("C_Xicon_PM102_P3.556_Illustration", "rounded", ["C34", "C100", "C101"],
         [5.5, 3.0, 7.5], 3.5, 0.5, PM, part="Xicon PM2A102K", standoff_mm=1.5, source_outline_mm=[5.08, 2.54], polarity=False),
    spec("C_Xicon_PM103_P4.064_Illustration", "rounded", ["C10", "C20", "C21", "C33", "C46"],
         [6.0, 3.5, 7.5], 3.5, 0.5, PM, part="Xicon PM2A103K", standoff_mm=1.5, source_outline_mm=[6.096, 3.302], polarity=False),
    spec("C_Xicon_PM333_P4.064_Illustration", "rounded", ["C19", "C24", "C36", "io:C201"],
         [6.5, 4.0, 9.0], 3.5, 0.5, PM, part="Xicon PM2A333K", standoff_mm=1.5, source_outline_mm=[6.35, 3.556], polarity=False),
    spec("C_Xicon_PM333_P5.08_Illustration", "rounded", ["C26"],
         [6.5, 4.0, 9.0], 3.5, 0.5, PM, part="Xicon PM2A333K", standoff_mm=2.0, source_outline_mm=[6.604, 3.556], polarity=False),
    spec("C_Xicon_PF183_P4.064_Illustration", "rounded", ["C18"],
         [7.0, 4.0, 12.0], 4.0, 0.5, PF, part="Xicon PF2A183K", standoff_mm=1.5, source_outline_mm=[6.35, 3.556], polarity=False),
    spec("C_Xicon_PM104_P5.08_Illustration", "rounded", ["C25", "C27", "C41"],
         [8.5, 6.0, 11.5], 5.0, 0.5, PM, part="Xicon PM2A104K", standoff_mm=1.5, source_outline_mm=[8.128, 5.08], polarity=False),
    spec("C_Xicon_PM224_P7.62_Illustration", "rounded", ["C35"],
         [11.5, 7.0, 13.0], 7.5, 0.5, PM, part="Xicon PM2A224K", standoff_mm=1.5, source_outline_mm=[11.43, 6.35], polarity=False),
    spec("C_Xicon_PF683_P7.62_Illustration", "rounded", ["C45"],
         [9.5, 5.0, 13.0], 7.5, 0.5, PF, part="Xicon PF2A683K", standoff_mm=1.5, source_outline_mm=[8.89, 5.08], polarity=False),
    spec("C_Xicon_PM473_P5.08_Illustration", "rounded", ["C54"],
         [7.5, 4.0, 9.5], 5.0, 0.5, PM, part="Xicon PM2A473K", standoff_mm=1.5, source_outline_mm=[7.366, 4.318], polarity=False),
    spec("C_Xicon_PF682_P3.81_Illustration", "rounded", ["C47"],
         [6.0, 3.5, 10.5], 3.5, 0.5, PF, part="Xicon PF2A682K", standoff_mm=1.5, source_outline_mm=[5.461, 3.048], source_outline_center_x_mm=-0.0635, polarity=False),
    spec("CP_Kemet_T350A105_P2.54_Illustration", "tantalum", ["C42", "C62"],
         [4.5, 4.5, 7.1], 2.54, 0.55, T350, part="Kemet T350A105K035AT", standoff_mm=0.35, source_outline_mm=[4.0956, 4.0956], polarity=True,
         dimensional_notes="Use manufacturer maximum lead diameter 0.50+0.05=0.55 mm. 4.5 mm diameter and 7.1 mm seated height. Ellipsoid, positive marking and 0.35 mm mounting gap are explicit illustration choices."),
    spec("CP_Xicon_XRL1u50_P3.556_Illustration", "can", ["C17"],
         [5.0, 5.0, 11.0], 2.0, 0.5, XRL, part="Xicon XRL50V1.0", standoff_mm=2.0, source_outline_mm=[5.9458, 5.9458], polarity=True,
         dimensional_notes="Nominal 5x11 mm can, nominal 2.0 mm factory pitch, 0.5 mm lead diameter. Manufacturer lists can diameter +/-1 mm, length +/-1.5 mm and lead pitch +/-0.5 mm. Custom lead forming to 3.556 mm is illustrated, not an assembly instruction."),
    spec("CP_Xicon_XRL2200u16_P5.08_Illustration", "can", ["io:C3", "io:C5"],
         [13.0, 13.0, 20.0], 5.0, 0.6, XRL, part="Xicon XRL16V2200", standoff_mm=0.8, source_outline_mm=[12.7, 12.7], polarity=True,
         dimensional_notes="Nominal 13x20 mm can, nominal 5.0 mm factory pitch and documented 0.6 mm lead diameter. Manufacturer lists can diameter +/-1 mm, length +/-1.5 mm and pitch +/-0.5 mm. This is a newly generated family illustration; no rejected stock 0.9 mm leads were thinned."),
    spec("TO92_Asymmetric_x0x_Illustration", "to92", ["Q17", "Q19", "Q23"],
         [4.7, 3.7, 4.7], 1.27, None, TO92, part="2SC536F family / generic TO92", standoff_mm=3.2, source_outline_mm=[5.332, 4.317], polarity=False,
         lead_rectangle_mm=[0.55, 0.51], dimensional_notes="Generic TO92 envelope uses JSCJ 2SC536 maximum D/E=4.7 mm and A=3.7 mm, maximum b/c leads .55/.51 mm. Not identification of the historical F-bin manufacturer. Flat side preserved at positive PCB Y; asymmetrical lead forming is explicitly illustrated."),
]


def read_inputs():
    result = {}
    for board in ("mainboard", "ioboard"):
        path = SNAPSHOT / board / (board + ".kicad_pcb")
        tree = parse_sexpr(path.read_text())
        result[board] = dict(path=path, sha256=sha(path),
                             fps={property_value(f, "Reference", "reference"): f
                                  for f in children(tree, "footprint")})
    return result


def input_refs(spec, inputs):
    refs = []
    for token in spec["refs"]:
        board, reference = ("ioboard", token[3:]) if token.startswith("io:") else ("mainboard", token)
        fp = inputs[board]["fps"][reference]
        pads = {p[1]: p for p in children(fp, "pad")}
        expected = ("1", "2", "3") if spec["kind"] == "to92" else (("+", "-") if spec["polarity"] else ("1", "2"))
        assert set(pads) == set(expected), (token, set(pads), expected)
        geometry = []
        for name in expected:
            p = pads[name]
            geometry.append(dict(pad=name, center_mm=[float(x) for x in one(p, "at")[1:3]],
                                 drill_mm=float(one(p, "drill")[1]),
                                 size_mm=[float(x) for x in one(p, "size")[1:3]],
                                 net=one(p, "net")))
        for p in geometry:
            assert abs(p["center_mm"][1]) < 1e-9
        if spec["polarity"]:
            assert geometry[0]["pad"] == "+" and geometry[0]["center_mm"][0] < 0
            assert geometry[1]["pad"] == "-" and geometry[1]["center_mm"][0] > 0
        local = fp[1].split(":")[-1]
        library = SNAPSHOT / board / (board + "-import-fps.pretty") / (local + ".kicad_mod")
        refs.append(dict(board=board, reference=reference, footprint=local,
                         value=property_value(fp, "Value", "value"),
                         input_board_sha256=inputs[board]["sha256"],
                         input_footprint_library_sha256=sha(library), pads=geometry,
                         pad_geometry_sha256=hashlib.sha256(json.dumps(geometry, sort_keys=True).encode()).hexdigest()))
    return refs


def lead_shape(xstart, xhole, start_z, radius=None, rectangle=None):
    finish_z = 0.45
    if abs(xstart - xhole) < 1e-10:
        path = Part.Wire(Part.makeLine(V(xhole, 0, start_z), V(xhole, 0, -2.5)))
    else:
        curve = Part.BezierCurve()
        h = start_z - finish_z
        curve.setPoles([V(xstart, 0, start_z), V(xstart, 0, start_z - h / 3),
                        V(xhole, 0, finish_z + h / 3), V(xhole, 0, finish_z)])
        path = Part.Wire([curve.toShape(), Part.makeLine(V(xhole, 0, finish_z), V(xhole, 0, -2.5))])
    if rectangle:
        dx, dy = (v / 2 for v in rectangle)
        pts = [V(xstart-dx, -dy, start_z), V(xstart+dx, -dy, start_z),
               V(xstart+dx, dy, start_z), V(xstart-dx, dy, start_z)]
        profile = Part.Wire(Part.makePolygon(pts + [pts[0]]).Edges)
        area = rectangle[0] * rectangle[1]
    else:
        profile = Part.Wire(Part.makeCircle(radius, V(xstart, 0, start_z), V(0, 0, 1)))
        area = math.pi * radius ** 2
    solid = path.makePipeShell([profile], True, False)
    assert solid.isValid() and len(solid.Solids) == 1
    assert abs(solid.Volume - path.Length * area) < 1e-5
    return solid


def sphere_ellipsoid(width, depth, height, zbase):
    assert abs(width - depth) < 1e-9
    center = V(0, 0, zbase + height / 2)
    ellipse = Part.Ellipse(center + V(0, 0, height / 2),
                           center + V(width / 2, 0, 0), center)
    arc = Part.ArcOfEllipse(ellipse, 0, math.pi).toShape()
    ends = [v.Point for v in arc.Vertexes]
    profile = Part.Face(Part.Wire([arc, Part.makeLine(ends[1], ends[0])]))
    return profile.revolve(V(0, 0, 0), V(0, 0, 1), 360)


def parts_for(spec, ref):
    w, d, h = spec["body_mm"]
    z = spec["standoff_mm"]
    kind = spec["kind"]
    parts = []
    if kind == "rounded":
        raw = Part.makeBox(w, d, h, V(-w / 2, -d / 2, z))
        body = raw.makeFillet(min(0.4, d / 8), raw.Edges)
        parts.append(("Body", body, [0.75, 0.26, 0.07] if "AVX" in spec["name"] else [0.53, 0.17, 0.08]))
    elif kind == "can":
        r = w / 2
        sleeve = Part.makeCylinder(r, h - 0.2, V(0, 0, z), V(0, 0, 1), 320)
        sleeve.rotate(V(0, 0, 0), V(0, 0, 1), 20)
        stripe = Part.makeCylinder(r, h - 0.2, V(0, 0, z), V(0, 0, 1), 40)
        stripe.rotate(V(0, 0, 0), V(0, 0, 1), -20)
        top = Part.makeCylinder(r - 0.1, 0.2, V(0, 0, z + h - 0.2))
        parts.extend([("Sleeve", sleeve, [0.06, 0.20, 0.55]),
                      ("NegativeStripe", stripe, [0.80, 0.82, 0.85]),
                      ("TopMetal", top, [0.70, 0.72, 0.74])])
        assert stripe.CenterOfMass.x > 0
    elif kind == "tantalum":
        body = sphere_ellipsoid(w, d, h, z)
        outer_ink = sphere_ellipsoid(w + 0.02, d + 0.02, h + 0.02, z - 0.01)
        shell = outer_ink.cut(body)
        # Curved positive '+' annotation projects onto the negative-X/front
        # surface. Its typography/position are explicit illustration choices.
        cross = Part.makeBox(0.8, d, 0.16, V(-1.3, -d, z + h / 2 - 0.08)).fuse(
            Part.makeBox(0.16, d, 0.8, V(-0.98, -d, z + h / 2 - 0.4)))
        positive = shell.common(cross)
        assert positive.isValid() and len(positive.Solids) == 1
        assert positive.Solids[0].CenterOfMass.x < 0
        parts.extend([("Body", body, [0.88, 0.55, 0.09]),
                      ("PositiveMark", positive, [0.025, 0.025, 0.025])])
    else:
        raw = Part.makeCylinder(w / 2, h, V(0, 0, z))
        # Chopped-cylinder silhouette is generic. The flat is at model -Y,
        # corresponding to +Y in PCB footprint coordinates.
        flat = -(d - w / 2)
        body = raw.cut(Part.makeBox(20, 20, h + 2, V(-10, flat - 20, z - 1)))
        parts.append(("Body", body, [0.08, 0.08, 0.09]))
        assert abs(body.BoundBox.YMin - flat) < 1e-8
    lead_checks = []
    for i, pad in enumerate(ref["pads"]):
        xhole = pad["center_mm"][0]
        if kind == "to92":
            xstart = {"1": 1.27, "2": 0, "3": -1.27}[pad["pad"]]
            start_z = z + 0.05
        elif kind == "tantalum":
            xstart = xhole
            start_z = z + 1.5
        else:
            xstart = (-1 if i == 0 else 1) * spec["factory_pitch_mm"] / 2
            start_z = z + 0.05
        rectangle = spec.get("lead_rectangle_mm")
        radius = spec["lead_diameter_mm"] / 2 if not rectangle else None
        lead = lead_shape(xstart, xhole, start_z, radius, rectangle)
        parts.append(("Lead_" + {"+": "Positive", "-": "Negative"}.get(pad["pad"], pad["pad"]), lead, [0.68, 0.70, 0.73]))
        circumscribed = math.hypot(*rectangle) / 2 if rectangle else radius
        assert pad["drill_mm"] / 2 - circumscribed > 0
        lead_checks.append(dict(pad=pad["pad"], hole_center_mm=[xhole, 0],
                                factory_body_exit_x_mm=xstart,
                                lead_circumscribed_radius_mm=circumscribed,
                                drill_mm=pad["drill_mm"],
                                nominal_radial_margin_mm=pad["drill_mm"] / 2 - circumscribed))
    for name, shape, color in parts:
        assert shape.isValid() and len(shape.Solids) == 1, name
    return [(name, shape.Solids[0], color) for name, shape, color in parts], lead_checks


def color_step(path, parts):
    text = path.read_text()
    entities = {int(m[1]): m[2] for m in re.finditer(r"#(\d+)\s*=\s*(.*?)\s*;", text, re.S)}
    breps = [n for n, e in entities.items() if e.startswith("MANIFOLD_SOLID_BREP(")]
    shapes = Part.read(str(path)).Solids
    assert len(breps) == len(parts) == len(shapes)
    for shape, (_, original, _) in zip(shapes, parts):
        assert abs(shape.Volume - original.Volume) < 1e-6
        assert (shape.CenterOfMass - original.CenterOfMass).Length < 1e-6
    next_id = max(entities) + 1
    added = []

    def add(expression):
        nonlocal next_id
        n = next_id
        next_id += 1
        added.append("#{} = {};".format(n, expression))
        return n

    styled = []
    for number, (name, shape, rgb) in zip(breps, parts):
        text = re.sub(r"(#{}\s*=\s*MANIFOLD_SOLID_BREP\()''".format(number), lambda m: m[1] + "'" + name + "'", text)
        col = add("COLOUR_RGB('',{},{},{})".format(*rgb))
        area_col = add("FILL_AREA_STYLE_COLOUR('',#{})".format(col))
        area = add("FILL_AREA_STYLE('',(#{}))".format(area_col))
        fill = add("SURFACE_STYLE_FILL_AREA(#{})".format(area))
        side = add("SURFACE_SIDE_STYLE('',(#{}))".format(fill))
        usage = add("SURFACE_STYLE_USAGE(.BOTH.,#{})".format(side))
        assignment = add("PRESENTATION_STYLE_ASSIGNMENT((#{}))".format(usage))
        styled.append(add("STYLED_ITEM('original CC0 illustration',(#{}),#{})".format(assignment, number)))
    context = next(n for n, e in entities.items() if "GEOMETRIC_REPRESENTATION_CONTEXT(3)" in e)
    add("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',({}),#{})".format(
        ",".join("#{}".format(n) for n in styled), context))
    marker = "ENDSEC;\nEND-ISO-10303-21;"
    assert marker in text
    path.write_text(text.replace(marker, "\n".join(added) + "\n" + marker))


def section_checks(shape, expected, spec):
    result = []
    zs = sorted(set([-0.05, -0.8, -1.5] + [-i * 1.6 / 16 for i in range(17)]))
    for z in zs:
        section = shape.section(Part.makePlane(40, 40, V(-20, -20, z)))
        # Lead sections are separate closed wires; each belongs to one drilled
        # pad and must be wholly within its original drill radius.
        remaining = list(section.Edges)
        wires = []
        while remaining:
            connected = Part.__sortEdges__(remaining)
            assert connected
            wires.append(connected)
            previous_count = len(remaining)
            remaining = [e for e in remaining if not any(e.isSame(c) for c in connected)]
            assert len(remaining) < previous_count
        assert len(wires) == len(expected), (spec["name"], z, len(wires))
        sections = []
        for wire_edges in wires:
            wire = Part.Wire(wire_edges)
            bbox = wire.BoundBox
            center = [(bbox.XMin + bbox.XMax) / 2, (bbox.YMin + bbox.YMax) / 2]
            pad = min(expected, key=lambda p: math.hypot(center[0] - p["hole_center_mm"][0], center[1]))
            residual = math.hypot(center[0] - pad["hole_center_mm"][0], center[1])
            assert residual < 1e-7
            if spec.get("lead_rectangle_mm"):
                radius = math.hypot(bbox.XLength, bbox.YLength) / 2
            else:
                circle = wire.Edges[0].Curve
                assert hasattr(circle, "Radius")
                radius = circle.Radius
                assert abs(radius - pad["lead_circumscribed_radius_mm"]) < 1e-7
            assert radius + residual < pad["drill_mm"] / 2
            sections.append(dict(pad=pad["pad"], center_mm=center,
                                 lead_radius_mm=radius,
                                 center_residual_mm=residual,
                                 nominal_radial_margin_mm=pad["drill_mm"] / 2 - radius - residual))
        result.append(dict(z_mm=z, sections=sections))
    return result


def main():
    inputs = read_inputs()
    all_records, assignments = [], []
    for definition in SPECS:
        refs = input_refs(definition, inputs)
        # All instances in a generated asset must share actual pad geometry.
        geometry = [{k: v for k, v in p.items() if k != "net"} for p in refs[0]["pads"]]
        for ref in refs:
            assert [{k: v for k, v in p.items() if k != "net"} for p in ref["pads"]] == geometry
        parts, lead_checks = parts_for(definition, refs[0])
        doc = App.newDocument(definition["name"])
        objs = []
        for name, shape, color in parts:
            assert shape.isValid() and len(shape.Solids) == 1, name
            obj = doc.addObject("Part::Feature", name)
            obj.Shape = shape
            objs.append(obj)
        doc.recompute()
        combined = Part.makeCompound([s for _, s, _ in parts])
        fused = parts[0][1]
        for _, shape, _ in parts[1:]:
            fused = fused.fuse(shape)
        assert fused.isValid() and len(fused.Solids) == 1, definition["name"]
        step = ROOT / (definition["name"] + ".step")
        Part.export(objs, str(step))
        color_step(step, parts)
        reimported = Part.read(str(step))
        assert reimported.isValid() and len(reimported.Solids) == len(parts)
        assert abs(reimported.Volume - combined.Volume) < 1e-6
        validation = section_checks(reimported, lead_checks, definition)
        App.closeDocument(doc.Name)
        differences = [definition["body_mm"][i] - definition["source_outline_mm"][i] for i in (0, 1)]
        limits = ["Original package illustration, not manufacturer CAD or identification of the actual fitted component.",
                  "Mounting gap, lead forming, colors, fillet radii and printed/stripe annotations are explicit illustration choices.",
                  "Manufacturer body dimensions are retained without shrinking to historical silk; no physical assembly, enclosure, tolerance or clearance approval.",
                  "Body width/depth minus historical silk envelope: {:.6f}/{:.6f} mm; height is from the linked primary drawing and source height is unknown.".format(*differences)]
        if definition["kind"] == "to92":
            limits.append("Modern JSCJ 2SC536 drawing supports a generic TO92 envelope only; historical 2SC536F manufacturer and lead dress remain unverified.")
        if definition["kind"] == "tantalum":
            limits.append("Original footprint name E2,5-7 is misleading; original BOM specifies a polarized Kemet T350 tantalum drop. Positive model annotation and lead map to source '+', not geometric numbering inferred from the package name.")
        record = dict(specification=definition, references=refs,
                      model_sha256=sha(step), source_model=str(step),
                      original_CC0_geometry=True, lead_checks=lead_checks,
                      all_parts_form_one_valid_connected_solid=True,
                      export_reimport_valid=True,
                      export_reimport_volume_mm3=reimported.Volume,
                      export_reimport_volume_delta_mm3=reimported.Volume - combined.Volume,
                      all_board_depth_sections=validation,
                      documented_minus_silk_width_depth_mm=differences,
                      limitations=limits)
        all_records.append(record)
        for board in ("mainboard", "ioboard"):
            board_refs = [r for r in refs if r["board"] == board]
            for local in sorted(set(r["footprint"] for r in board_refs)):
                selected = [r for r in board_refs if r["footprint"] == local]
                assignments.append(dict(board=board, footprint=local,
                    references=[r["reference"] for r in selected],
                    source_model=str(step), source_sha256=sha(step),
                    offset_mm=[0, 0, 0], rotation_deg=[0, 0, 0], scale=[1, 1, 1],
                    classification="qualified original package illustration",
                    limitations=limits, source_kind="original CC0 package illustration",
                    source_urls=definition["source_urls"],
                    source_refs=selected, dimensions=definition,
                    board_depth_validation=validation,
                    polarity_mapping={"positive_mark_and_lead": "+", "negative_stripe_and_lead": "-"} if definition["polarity"] else None))
        (ROOT / "passive-dimensional-records.json").write_text(json.dumps(
            dict(generator_sha256=sha(Path(__file__)), FreeCAD_version=App.Version(), models=all_records), indent=2) + "\n")
        (ROOT / "passive-assignments.json").write_text(json.dumps(dict(
            assignments=assignments, selected_instances=sum(len(a["references"]) for a in assignments),
            unique_assets=len(all_records), generation_complete=False), indent=2) + "\n")
        print("Validated", definition["name"], len(refs), flush=True)
    (ROOT / "passive-dimensional-records.json").write_text(json.dumps(
        dict(generator_sha256=sha(Path(__file__)), FreeCAD_version=App.Version(), models=all_records), indent=2) + "\n")
    (ROOT / "passive-assignments.json").write_text(json.dumps(dict(
        assignments=assignments, selected_instances=sum(len(a["references"]) for a in assignments),
        unique_assets=len(all_records), generation_complete=True), indent=2) + "\n")
    print(json.dumps({"validated_instances": sum(len(a["references"]) for a in assignments), "unique_assets": len(all_records)}))


if __name__ == "__main__":
    main()
