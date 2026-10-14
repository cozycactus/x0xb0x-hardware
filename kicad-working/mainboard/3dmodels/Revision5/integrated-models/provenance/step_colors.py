# Original STEP presentation helper. SPDX-License-Identifier: CC0-1.0
import re
import Part

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
