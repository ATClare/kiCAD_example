"""Parametric CadQuery 2.8 model. Units: mm. Run from any directory."""
from pathlib import Path
import cadquery as cq
import json

OUT=Path(__file__).resolve().parent/'exports'; OUT.mkdir(exist_ok=True)
W,D,H,T=140.0,100.0,55.0,3.0
LID=3.0
SCREWS=[(x,y) for x in (-61,61) for y in (-41,41)]
BOARD=[(x,y) for x in (-45,45) for y in (-25,25)]
GLANDS=[-38,0,38]
LED_X=[-18,0,18]
def box(w,d,h,z=0):return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((0,0,z))
def cylinder(x,y,z,r,h):return cq.Workplane('XY').center(x,y).circle(r).extrude(h).translate((0,0,z))

base=box(W,D,H).edges('|Z').fillet(4)
cavity=box(W-2*T,D-2*T,H,T).edges('|Z').fillet(2)
base=base.cut(cavity)
for x,y in SCREWS:
    base=base.union(cylinder(x,y,T,5,H-T))
    base=base.cut(cylinder(x,y,H-16,1.25,18))
for x,y in BOARD:
    base=base.union(cylinder(x,y,T,3.5,8))
    base=base.cut(cylinder(x,y,T+1,1.25,9))
for x in GLANDS:
    # XZ normal points toward -Y; cut through the front wall.
    hole=cq.Workplane('XZ').center(x,24).circle(6.1).extrude(10,both=True).translate((0,-D/2,0))
    base=base.cut(hole)

# Lid STL orientation is installed orientation at z=0..3, with rails at z=-3..0.
lid=box(W,D,LID).edges('|Z').fillet(4)
for x,y in SCREWS:
    lid=lid.cut(cylinder(x,y,-1,1.7,5))
    lid=lid.cut(cylinder(x,y,1.5,3.2,3))
# Interrupted locating rails avoid all four screw bosses; 0.3 mm per-side clearance.
for y in (-45.7,45.7): lid=lid.union(box(106,2,3,-3).translate((0,y,0)))
for x in (-65.7,65.7): lid=lid.union(box(2,64,3,-3).translate((x,0,0)))
for x in LED_X: lid=lid.cut(cylinder(x,20,-1,3.25,5))
lid=lid.cut(cylinder(35,-15,-1,11.1,5)) # 22 mm STOP control
lid=lid.cut(cylinder(-35,-15,-1,6.1,5)) # 12 mm power toggle
for word,x in [('READY',-18),('WATER',0),('FAULT',18)]:
    label=cq.Workplane('XY').text(word,3,0.5,combine=True).translate((x,10,2.5))
    lid=lid.cut(label)

carrier=box(100,60,1.6)
for x,y in BOARD:carrier=carrier.cut(cylinder(x,y,-1,1.7,4))

# External bench bracket: HS-311 body aperture, adjustable flange slots, foot slots.
# Mount on a separate rigid plate above the valve. It is not a pressure-bearing part.
bracket=box(76,44,4)
bracket=bracket.cut(box(40.8,20.8,8,-1))
for x in (-24.5,24.5):
    for y in (-5,5):
        slot=cq.Workplane('XY').center(x,y).slot2D(7,3.4,0).extrude(8).translate((0,0,-1))
        bracket=bracket.cut(slot)
for x in (-35,35):
    bracket=bracket.union(box(6,44,40,-40).translate((x,0,0)))
    bracket=bracket.union(box(16,44,4,-40).translate((x+(-5 if x<0 else 5),0,0)))
for x in (-43,43):
    for y in (-13,13):
        slot=cq.Workplane('XY').center(x,y).slot2D(9,4.5,90).extrude(8).translate((0,0,-42))
        bracket=bracket.cut(slot)

# A generic slotted linkage plate screws to a manufacturer-supplied 24T horn.
# No unverified spline is printed. Valve-specific attachment must be measured.
link=cq.Workplane('XY').slot2D(55,12).extrude(4)
link=link.cut(cq.Workplane('XY').center(-18,0).circle(1.6).extrude(5))
link=link.cut(cq.Workplane('XY').center(8,0).slot2D(25,3.4).extrude(5))

parts={'base':base,'lid':lid,'carrier_drill_template':carrier,'servo_bracket':bracket,'linkage_plate':link}
report={}
for name,part in parts.items():
    solids=part.solids().vals();assert len(solids)==1 and part.val().isValid(),name
    cq.exporters.export(part,str(OUT/(name+'.step')))
    # Translate print meshes to bed Z=0. Lid upside down prints without rail supports.
    printable=part.rotate((0,0,0),(1,0,0),180) if name=='lid' else part
    printable=printable.translate((0,0,-printable.val().BoundingBox().zmin))
    cq.exporters.export(printable,str(OUT/(name+'.stl')),tolerance=0.08,angularTolerance=0.15)
    b=part.val().BoundingBox()
    report[name]={'valid_solid':True,'solid_count':len(solids),'volume_mm3':round(part.val().Volume(),2),'bounds_mm':[round(b.xlen,2),round(b.ylen,2),round(b.zlen,2)]}
installed_lid=lid.translate((0,0,H))
overlap=base.intersect(installed_lid)
collision=sum(s.Volume() for s in overlap.solids().vals())
assert collision<1e-5,collision
report['assembly']={'base_lid_interference_mm3':collision,'nominal_lid_rail_clearance_mm':0.3}
assembly=cq.Assembly(name='SoilValve_Enclosure')
assembly.add(base,name='base',color=cq.Color(0.12,0.23,0.19))
assembly.add(installed_lid,name='lid',color=cq.Color(0.72,0.79,0.69))
assembly.add(carrier.translate((0,0,11)),name='carrier_reference',color=cq.Color(0.55,0.33,0.16))
assembly.export(str(OUT/'enclosure_assembly.step'))
(OUT/'geometry_report.json').write_text(json.dumps(report,indent=2)+'\n')
# Isometric vector review drawings, including a separate exploded enclosure.
exploded=cq.Compound.makeCompound([base.val(),lid.translate((0,0,85)).val(),carrier.translate((0,0,11)).val()])
cq.exporters.export(exploded,str(OUT/'enclosure_exploded.svg'),opt={'width':1000,'height':800,'projectionDir':(1,-1,1),'showHidden':False})
cq.exporters.export(bracket,str(OUT/'servo_bracket.svg'),opt={'width':800,'height':600,'projectionDir':(1,-1,1),'showHidden':False})
print(json.dumps(report,indent=2))
