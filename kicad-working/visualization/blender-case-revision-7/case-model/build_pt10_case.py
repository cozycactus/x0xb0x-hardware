"""Visualization reconstruction of PacTec PT-10, from drawing 82232 rev C.

Dimensions are in mm. Unsized mold geometry is generalized; this is not the
original manufacturer's CAD or a fabrication/fit certification.
Run with FreeCAD's Python and its Resources/lib on PYTHONPATH.
"""
import json
import math
import hashlib
from pathlib import Path
import FreeCAD as App
import Part
import MeshPart

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'source' / 'pactec-pt10-manufacturer-drawing.pdf'
D = json.loads((HERE / 'pt10-datums.json').read_text())
W, DEPTH, HEIGHT, T = 279.4, 203.1492, 77.0382, 2.54
A = math.radians(15)
N = App.Vector(0, -math.sin(A), math.cos(A))
V = App.Vector(0, math.cos(A), math.sin(A))
U = App.Vector(1, 0, 0)
MP = D['main_panel']
ORIGIN = App.Vector(*MP['underside_origin_left_front_mm'])

def polygon(points):
    return Part.Face(Part.makePolygon(points + [points[0]]))

def yz_prism(points, x0=-W / 2, width=W):
    return polygon([App.Vector(x0, y, z) for y, z in points]).extrude(
        App.Vector(width, 0, 0))

def rounded_footprint(width, depth, radius, inset=0):
    x0, x1 = -width/2, width/2
    y0, y1 = inset, inset + depth
    corners = [(x1-radius, y1-radius, 0),
               (x0+radius, y1-radius, 90),
               (x0+radius, y0+radius, 180),
               (x1-radius, y0+radius, 270)]
    pts = []
    for cx, cy, start in corners:
        for k in range(13):
            a = math.radians(start + k * 90 / 12)
            pts.append(App.Vector(cx+radius*math.cos(a),
                                  cy+radius*math.sin(a), 0))
    return polygon(pts)

# Section C-C outer silhouette: the front curve is traced from the vector
# drawing, calibrated at 1.7 PDF points/mm. The rear curve and XY corner radius
# are generalized because their mold radii are not dimensioned.
profile = [(6.919, 0), (193.62, 0), (197.5, 1.0), (200.5, 3.5),
           (202, 8), (202.8, 20.435), (DEPTH, 38.01),
           (202.62, 49.5), (201.07, 59), (198.4, 68),
           (194, 74.5), (188, HEIGHT), (182.576, 76.622),
           (20.154, 33.141), (15.705, 31.728), (11.858, 30.246),
           (8.506, 28.621), (5.576, 26.787), (3.281, 24.917),
           (1.516, 22.799), (.422, 20.646), (0, 18.563),
           (.1, 8), (1.4, 3.5), (3.8, 1)]
outer = yz_prism(profile).common(
    rounded_footprint(W, DEPTH, 7.0).extrude(App.Vector(0, 0, 100)))
# Approximate the nominal 0.100-inch shell with a hollow cavity. The upper
# cavity follows the panel slope; this leaves a nominal 2.54-mm top flange.
# Follow the outer shoulder curves as well as the central 15-degree roof.
# Extending only the central roof plane would break through the lower front
# shoulder, leaving an artificial open slit across the assembled case.
upper_profile = profile[6:22]  # rear to front, monotonically decreasing Y
ascending = list(reversed(upper_profile))
def outer_roof_z(y):
    for (y0,z0),(y1,z1) in zip(ascending,ascending[1:]):
        if y0 <= y <= y1:
            return z0+(z1-z0)*(y-y0)/(y1-y0)
    raise ValueError('Roof coordinate outside profile')
roof_offset = T / math.cos(A)
cavity_top = [(DEPTH-T,outer_roof_z(DEPTH-T)-roof_offset)]
cavity_top += [(y,z-roof_offset) for y,z in upper_profile if T<y<DEPTH-T]
cavity_top += [(T,outer_roof_z(T)-roof_offset)]
cavity = yz_prism([(T,T),(DEPTH-T,T)] + cavity_top, -W/2+T,W-2*T)
inner_foot = rounded_footprint(W-2*T, DEPTH-2*T, 4.46, T).extrude(
    App.Vector(0,0,100))
body = outer.cut(cavity.common(inner_foot))
# Approximate rear-panel groove surround. The plate dimensions and the lower
# groove offset are printed dimensions; its depth setback is traced.
rp = D['rear_panel']; rx, ry, rz = rp['outer_face_origin_outside_view_left_bottom_mm']
rw, rh = rp['size_mm']; pt = rp['thickness_mm']
rear_surround = Part.makeBox(rw+2*T, DEPTH-T-(ry-pt), rh+2*T,
                            App.Vector(-rw/2-T,ry-pt,rz-T))
body = body.fuse(rear_surround.common(outer))
# Rear orthographic opening: 8.474 x 1.960 inches. Use the explicit detail-D
# lower datum (floor + .250), and retain the printed .102-inch lower groove.
rear_visible = Part.makeBox(215.2396, 20, 49.784,
                           App.Vector(-215.2396/2,ry,8.89))
rear_pocket = Part.makeBox(rw, pt+0.05, rh,
                          App.Vector(-rw/2,ry-pt-.025,rz))
body = body.cut(rear_visible).cut(rear_pocket)

# Seam height is dimensioned 1.535 inch at the rear. The approximate front
# seam is traced from C-C; molded tongue/clip details are omitted.
seam_front, seam_rear = 17.5, 38.989
seam = lambda y: seam_front + y*(seam_rear-seam_front)/DEPTH
lower_half = yz_prism([(-5,-5),(DEPTH+5,-5),
                       (DEPTH+5,seam(DEPTH+5)),(-5,seam(-5))],-W,W*2)
upper_half = yz_prism([(-5,seam(-5)+.18),
                       (DEPTH+5,seam(DEPTH+5)+.18),
                       (DEPTH+5,100),(-5,100)],-W,W*2)
bottom = body.common(lower_half)
upper = body.common(upper_half)

def panel_prism(x0, y0, w, h, start, distance):
    p = ORIGIN + U*x0 + V*y0 + N*start
    pts = [p, p+U*w, p+U*w+V*h, p+V*h]
    return polygon(pts).extrude(N*distance)

# Recess for the original .062-inch removable plate and an open center. The
# narrow remaining ledge is a visualization approximation to molded supports.
upper = upper.cut(panel_prism(-.25,-.25,232.91,163.7712,-.02,100))
upper = upper.cut(panel_prism(.9,.9,230.61,161.4712,-100,200))
# Four bottom-cover PCB bosses follow the dimensioned 9.2 x 7.217-in board
# and its 8.976/.224 x 6.841/.821-in hole datums. Board centering is inferred.
boss_y = [(DEPTH-183.3118)/2+20.8534,
          (DEPTH-183.3118)/2+173.7614]
for x in [-111.1504,111.1504]:
    for y in boss_y:
        boss = Part.makeCylinder(3.5,6.35,App.Vector(x,y,T))
        bore = Part.makeCylinder(1.13,6.4,App.Vector(x,y,T))
        bottom = bottom.fuse(boss.cut(bore))

bottom, upper = bottom.removeSplitter(), upper.removeSplitter()
doc = App.newDocument('PacTec_PT10_Reconstructed')
parts = []
for name, role, shape in [('PT10_Bottom_Cover','bottom',bottom),
                           ('PT10_Upper_Cover','upper',upper)]:
    if not shape.isValid():
        raise RuntimeError(name + ' shape invalid')
    obj = doc.addObject('PartDesign::Feature', name)
    obj.Label = name.replace('_',' ') + ' - visualization reconstruction'
    obj.Shape = shape
    obj.addProperty('App::PropertyString','Evidence','Provenance')
    obj.Evidence = 'PacTec drawing 82232 rev C; generalized unsized mold detail'
    mesh = MeshPart.meshFromShape(Shape=shape,LinearDeflection=.12,
                                  AngularDeflection=.12,Relative=False)
    filename = name.lower()+'.stl'
    mesh.write(str(HERE/filename))
    parts.append({'name':name,'role':role,'filename':filename,'format':'stl',
                  'units':'mm','solid_count':len(shape.Solids),
                  'is_valid':shape.isValid(),'volume_mm3':shape.Volume,
                  'triangles':mesh.CountFacets,
                  'bbox_mm':{'min':[shape.BoundBox.XMin,shape.BoundBox.YMin,
                                    shape.BoundBox.ZMin],
                             'max':[shape.BoundBox.XMax,shape.BoundBox.YMax,
                                    shape.BoundBox.ZMax]}})
doc.recompute()
doc.saveAs(str(HERE/'pactec-pt10-reconstruction.FCStd'))
Part.export(doc.Objects,str(HERE/'pactec-pt10-reconstruction.step'))
manifest = {'parts':parts,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'generator':'build_pt10_case.py','manufacturing_ready':False,
            'omitted_details':['exact molded draft/radii','clip and screw geometry',
                               'internal ribs','rubber feet'],
            'assumed_details':{'xy_corner_radius_mm':7,'side_wall_mm':T,
                               'front_seam_z_mm':seam_front,
                               'seam_visual_gap_mm':.18,
                               'bottom_boss_outer_radius_mm':3.5,
                               'bottom_boss_bore_radius_mm':1.13}}
(HERE/'case-parts.json').write_text(json.dumps(manifest,indent=2)+'\n')
D['case_mesh_manifest']='case-parts.json'
D['source']['sha256']=manifest['source_sha256']
(HERE/'pt10-datums.json').write_text(json.dumps(D,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
