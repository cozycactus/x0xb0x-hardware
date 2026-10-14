import re

def add_step_face_colors(path,features):
    """Bind standard AP214 surface styles to faces, without changing geometry.

    Uses the same styled-item/surface-style chain as installed KiCad STEP
    assets. FreeCAD headless exports no ViewObject colors, so apply explicit
    face styles to each exported feature's solids.
    """
    text=path.read_text();entities={int(n):v for n,v in re.findall(r'#(\d+)\s*=\s*(.*?);',text,re.S)}
    breps=[int(n) for n in re.findall(r'#(\d+)\s*=\s*MANIFOLD_SOLID_BREP',text)]
    color_groups=[]
    for _,shape,color in features:
        color_groups.extend([color]*len(shape.Solids))
    assert len(breps)==len(color_groups),(path,len(breps),len(color_groups))
    next_id=max(entities)+1;extra=[]
    def entity(value):
        nonlocal next_id
        n=next_id;next_id+=1;extra.append(f'#{n} = {value};');return n
    for brep,color in zip(breps,color_groups):
        shell=int(re.findall(r'#(\d+)',entities[brep])[0]);faces=[int(n) for n in re.findall(r'#(\d+)',entities[shell])]
        context=None
        for value in entities.values():
            if (value.startswith('ADVANCED_BREP_SHAPE_REPRESENTATION') or value.startswith('SHAPE_REPRESENTATION')) and brep in [int(n) for n in re.findall(r'#(\d+)',value)]:
                refs=re.findall(r'#(\d+)',value);context=int(refs[-1]);break
        assert context is not None
        rgb=entity("COLOUR_RGB('',"+','.join(str(v) for v in color)+')')
        fill_color=entity(f"FILL_AREA_STYLE_COLOUR('',#{rgb})")
        fill=entity(f"FILL_AREA_STYLE('',(#{fill_color}))")
        surface_fill=entity(f'SURFACE_STYLE_FILL_AREA(#{fill})')
        side=entity(f"SURFACE_SIDE_STYLE('',(#{surface_fill}))")
        usage=entity(f'SURFACE_STYLE_USAGE(.BOTH.,#{side})')
        assignment=entity(f'PRESENTATION_STYLE_ASSIGNMENT((#{usage}))')
        styled=[entity(f"STYLED_ITEM('body illustration color',(#{assignment}),#{face})") for face in faces]
        entity("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',("+
               ','.join('#'+str(n) for n in styled)+f'),#{context})')
    text=text.replace('ENDSEC;\nEND-ISO-10303-21;', '\n'.join(extra)+'\nENDSEC;\nEND-ISO-10303-21;')
    path.write_text(text)
    return len(color_groups)
