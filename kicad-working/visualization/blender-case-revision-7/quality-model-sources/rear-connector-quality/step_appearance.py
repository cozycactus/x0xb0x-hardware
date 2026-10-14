"""Project-local AP214 face appearance helper; original generated reconstruction."""
import re
def face_colors(path,palette):
 raw=path.read_text();ent={int(n):body for n,body in re.findall(r'#(\d+)\s*=\s*(.*?);',raw,re.S)};breps=[int(n)for n in re.findall(r'#(\d+)\s*=\s*MANIFOLD_SOLID_BREP',raw)];assert len(breps)==len(palette)
 extra=[];next_id=max(ent)+1
 def add(body):
  nonlocal next_id
  i=next_id;next_id+=1;extra.append(f'#{i} = {body};');return i
 roles=[]
 for brep,rgb in zip(breps,palette):
  shell=int(re.findall(r'#(\d+)',ent[brep])[0]);faces=list(map(int,re.findall(r'#(\d+)',ent[shell])));assert all(ent[f].lstrip().startswith('ADVANCED_FACE')for f in faces)
  context=None
  for body in ent.values():
   if body.startswith(('SHAPE_REPRESENTATION','ADVANCED_BREP_SHAPE_REPRESENTATION')):
    rr=list(map(int,re.findall(r'#(\d+)',body)))
    if brep in rr:context=rr[-1];break
  if context is None:context=next(i for i,b in ent.items()if 'GEOMETRIC_REPRESENTATION_CONTEXT(3)'in b)
  c=add("COLOUR_RGB('',"+','.join(map(str,rgb))+')');f=add(f"FILL_AREA_STYLE_COLOUR('',#{c})");f=add(f"FILL_AREA_STYLE('',(#{f}))");f=add(f'SURFACE_STYLE_FILL_AREA(#{f})');f=add(f"SURFACE_SIDE_STYLE('',(#{f}))");f=add(f'SURFACE_STYLE_USAGE(.BOTH.,#{f})');f=add(f'PRESENTATION_STYLE_ASSIGNMENT((#{f}))');styles=[add(f"STYLED_ITEM('',(#{f}),#{face})")for face in faces];add("MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',("+','.join('#'+str(i)for i in styles)+f'),#{context})');roles.append(dict(brep=brep,faces=len(faces),color=rgb))
 pos=raw.rfind('ENDSEC;');path.write_text(raw[:pos]+'\n'+'\n'.join(extra)+'\n'+raw[pos:]);return roles

