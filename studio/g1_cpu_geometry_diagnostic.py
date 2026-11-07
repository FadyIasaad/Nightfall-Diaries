"""Original G1 fox/tortoise geometry diagnostic on free CPU Blender.

All meshes, materials, rigs, and animation are authored procedurally here. This
does NOT replace locked characters, does NOT pass G1 quality, and is NEVER a
publishable clip. It deliberately tests real moving 3D geometry, not stills.
"""
import bpy, math, random, sys, json, time
from pathlib import Path
from mathutils import Vector
from math import sin, cos, pi

FPS=12
FRAMES=24
WIDTH=360
HEIGHT=640
OUT="output/g1_cpu_geometry_diagnostic.mp4"
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
for i,arg in enumerate(args):
    if arg=="--frames": FRAMES=int(args[i+1])
    if arg=="--size":
        WIDTH,HEIGHT=map(int,args[i+1].split("x"))
    if arg=="--fps": FPS=int(args[i+1])
    if arg=="--output": OUT=args[i+1]
assert 1<=FRAMES<=480 and 1<=FPS<=30
assert 96<=WIDTH<=720 and 96<=HEIGHT<=1280
Path(OUT).parent.mkdir(parents=True,exist_ok=True)
start=time.time()
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
random.seed(73)
S=bpy.context.scene
S.frame_start=1
S.frame_end=FRAMES
S.render.engine="CYCLES"
S.cycles.device="CPU"
S.cycles.samples=7
S.render.resolution_x=WIDTH
S.render.resolution_y=HEIGHT
S.render.resolution_percentage=100
S.render.fps=FPS
S.render.image_settings.file_format="FFMPEG"
S.render.ffmpeg.format="MPEG4"
S.render.ffmpeg.codec="H264"
S.render.ffmpeg.constant_rate_factor="MEDIUM"
S.render.filepath=str(Path(OUT).resolve())
S.render.film_transparent=False
S.view_settings.view_transform="Filmic"
S.world.use_nodes=True
S.world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.012,0.028,0.043,1)
S.world.node_tree.nodes["Background"].inputs["Strength"].default_value=.36
bpy.context.view_layer.cycles.use_denoising=True

def material(name,color,rough=.72,metal=0,emission=None):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    if emission is not None:
        bs.inputs["Emission Color"].default_value=(*color,1) if "Emission Color" in bs.inputs else (*color,1)
        if "Emission Strength" in bs.inputs: bs.inputs["Emission Strength"].default_value=emission
    return m
ORANGE=material("fox rich russet",(.61,.115,.028))
LIGHT=material("cream fur",(.89,.72,.51))
WHITE=material("left ear ivory tip",(.96,.91,.78))
TEAL=material("teal scarf",(.018,.33,.37),.84)
GOLD=material("single embroidered gold star",(.84,.53,.085),.3,.42)
AMBER=material("amber iris",(.60,.24,.045),.25)
BLACK=material("wet black nose and pupils",(.008,.015,.022),.11)
EYES=material("warm sclera",(.97,.87,.69),.28)
MOSS=material("Moss olive skin",(.22,.33,.125))
MOSS_LIGHT=material("Moss lower skin",(.46,.54,.31))
SHELL=material("spiral weathered shell",(.205,.25,.14),.78)
SHELL_RIM=material("shell raised scutes",(.36,.39,.19),.76)
DARK=material("crack line",(.06,.075,.048))
GROUND=material("mossy forest ground",(.04,.09,.065))
WOOD=material("tree bark",(.13,.08,.05))
LEAF=material("teal canopy",(.065,.19,.15))
GLOW=material("warm firefly glow",(.9,.51,.12),.2,emission=2)

def sphere(name,pos,scale,mat,parent=None,segments=32,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=pos)
    o=bpy.context.object
    o.name=name; o.scale=scale; o.data.materials.append(mat)
    for face in o.data.polygons: face.use_smooth=True
    if parent: o.parent=parent
    return o

def cylinder(name,pos,scale,mat,vertices=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,location=pos)
    o=bpy.context.object; o.name=name; o.scale=scale
    o.data.materials.append(mat)
    for face in o.data.polygons: face.use_smooth=True
    return o

def cone(name,pos,scale,mat,parent=None):
    bpy.ops.mesh.primitive_cone_add(vertices=28, radius1=1, radius2=.04, depth=1, location=pos)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(mat)
    for face in o.data.polygons: face.use_smooth=True
    if parent: o.parent=parent
    return o

def curve(name,points,mat,radius=.013,parent=None):
    cv=bpy.data.curves.new(name,"CURVE"); cv.dimensions="3D"
    cv.bevel_depth=radius; cv.bevel_resolution=2; cv.resolution_u=16
    s=cv.splines.new("POLY"); s.points.add(len(points)-1)
    for p,v in zip(s.points,points): p.co=(*v,1)
    ob=bpy.data.objects.new(name,cv); S.collection.objects.link(ob)
    cv.materials.append(mat)
    if parent: ob.parent=parent
    return ob

def empty(name,loc):
    ob=bpy.data.objects.new(name,None)
    S.collection.objects.link(ob); ob.location=loc
    return ob

# Ground and moonlit fantasy forest around our original sculpted actors.
cylinder("forest clearing",(0,0,-.17),(15,15,.16),GROUND)
for i in range(22):
    angle=(i+.17)*2*pi/22
    rad=random.uniform(5,10)
    x,y=rad*cos(angle),rad*sin(angle)
    z=random.uniform(2.5,4.0)
    cylinder("forest trunk %d"%i,(x,y,z/2),(.17,.17,z/2),WOOD)
    for j in range(3):
        sphere("forest crown %d %d"%(i,j),
               (x+.38*cos(i+j),y+.3*sin(i+j),z+.4+j*.28),
               (1.05,.90,.68),LEAF,segments=16,rings=10)
for i in range(36):
    x=random.uniform(-4.4,4.4)
    y=random.uniform(-3.9,3.6)
    z=random.uniform(.7,2.4)
    sphere("firefly %d"%i,(x,y,z),(.02,.02,.02),GLOW,segments=8,rings=5)

# Ember: quadruped fox cub, rich rust orange, rounded proportions.
fox=empty("EMBER -- original locked identity candidate",(-1.15,0,0))
sphere("ember compact body",(0,.18,.71),(.42,.62,.39),ORANGE,fox)
sphere("ember cream chest",(0,-.31,.77),(.28,.26,.33),LIGHT,fox)
fox_head=sphere("ember expressive head",(0,-.36,1.34),(.41,.37,.38),ORANGE,fox)
for x in (-.25,.25):
    cone("ember peaked ear", (x,-.35,1.79),(.17,.17,.46),ORANGE,fox)
# Correct LEFT ear ONLY has white tip: asymmetric geometry!
cone("Ember LEFT ear white tip",(-.25,-.35,1.995),(.09,.085,.15),WHITE,fox)
for x in (-.20,.20):
    sphere("ember ivory eye surround",(x,-.645,1.38),(.145,.09,.17),LIGHT,fox)
    sphere("ember amber iris",(x,-.711,1.39),(.100,.054,.116),AMBER,fox)
    sphere("ember reflective pupil",(x,-.756,1.4),(.046,.035,.079),BLACK,fox)
    sphere("ember eye highlight",(x-.025,-.787,1.435),(.018,.018,.023),WHITE,fox)
fox_lid_l=sphere("Ember left animated eyelid",(-.20,-.728,1.53),(.144,.038,.07),ORANGE,fox)
fox_lid_r=sphere("Ember right animated eyelid",(.20,-.728,1.53),(.144,.038,.07),ORANGE,fox)
sphere("ember pale muzzle L",(-.13,-.728,1.17),(.19,.22,.13),LIGHT,fox)
sphere("ember pale muzzle R",(.13,-.728,1.17),(.19,.22,.13),LIGHT,fox)
sphere("ember nose",(0,-.916,1.20),(.084,.063,.05),BLACK,fox)
mouth=sphere("Ember actual mouth opening", (0,-.747,1.064),(.114,.044,.054),BLACK,fox)
jaw=sphere("Ember moveable lower jaw",(0,-.688,1.018),(.192,.1,.064),LIGHT,fox)
for x in (-.29,.29):
    for y in (-.19,.38):
        sphere("ember rounded leg",(x,y,.34),(.12,.15,.33),ORANGE,fox)
        sphere("ember paw",(x,y-.09,.11),(.15,.20,.12),ORANGE,fox)
tail=sphere("Ember fluffy waving tail",(0,.82,.78),(.19,.68,.23),ORANGE,fox)
sphere("Ember single ivory tail tip",(0,1.38,.91),(.17,.24,.18),WHITE,fox)
sphere("Ember scarf wrapped around neck",(0,-.10,1.04),(.44,.36,.085),TEAL,fox)
# One and only one gold 5-tip star on the teal scarf.
verts=[]
for i in range(10):
    a=-pi/2+i*pi/5
    r=.095 if i%2==0 else .041
    verts.append((r*cos(a),-.454,r*sin(a)+1.045))
mesh=bpy.data.meshes.new("one gold star mesh")
mesh.from_pydata([(0,-.445,1.045)]+verts,[],[(0,i+1,(i+1)%10+1) for i in range(10)])
star=bpy.data.objects.new("ONE stitched gold star",mesh)
S.collection.objects.link(star); mesh.materials.append(GOLD); star.parent=fox
# Purposefully add whiskers and cheek tufts.
for side in (-1,1):
    for k in range(3):
        curve("Ember whisker %d %d"%(side,k),
              [(side*.13,-.885,1.18+k*.027),(side*(.28+k*.04),-.90,1.16+k*.025)],
              LIGHT,.008,fox)
    for k in range(5):
        sphere("fox fur cheek tuft", (side*(.26+k*.027),-.56,1.18+k*.055),
               (.063,.05,.025),ORANGE,fox,12,8)

# Moss: original elderly quadruped tortoise, slow, substantial mass.
turtle=empty("MOSS -- original locked identity candidate",(1.14,.15,0))
sphere("Moss olive body",(0,.18,.46),(.66,.69,.40),MOSS,turtle)
sphere("Moss large curved shell",(0,.28,.87),(.79,.76,.58),SHELL,turtle)
sphere("Moss lower shell rim",(0,.22,.62),(.84,.80,.18),SHELL_RIM,turtle)
# A visible shell spiral follows the curved surface, not a texture label.
pts=[]
for k in range(130):
    theta=k/129*4.3*pi
    r=.07+.47*k/129
    x=r*cos(theta); y=.29+r*sin(theta)
    z=.87+.59*math.sqrt(max(.01,1-(r/.83)**2))
    pts.append((x,y,z+.013))
curve("Moss locked spiral shell growth",pts,SHELL_RIM,.022,turtle)
# One front-right shell-edge crack on the animal's right.
curve("Moss small FRONT RIGHT shell crack",
      [(.47,-.36,.74),(.51,-.34,.80),(.54,-.31,.78),
       (.57,-.29,.85),(.60,-.27,.84)],DARK,.02,turtle)
for x in (-.46,.46):
    for y in (-.34,.62):
        sphere("Moss grounded leg",(x,y,.30),(.20,.24,.31),MOSS,turtle)
        sphere("Moss broad toes",(x,y-.14,.095),(.23,.28,.105),MOSS_LIGHT,turtle)
turtle_head=sphere("Moss weathered olive head",(0,-.57,.87),(.37,.39,.34),MOSS,turtle)
sphere("Moss pale lower muzzle",(0,-.84,.75),(.29,.18,.16),MOSS_LIGHT,turtle)
for x in (-.19,.19):
    sphere("Moss gentle sclera",(x,-.866,1.02),(.14,.065,.16),EYES,turtle)
    sphere("Moss mellow pupil",(x,-.925,1.00),(.060,.033,.092),BLACK,turtle)
    sphere("Moss expressive half lid",(x,-.907,1.105),(.147,.06,.092),MOSS,turtle)
turtle_jaw=sphere("Moss moveable pale jaw",(0,-.90,.689),(.24,.1,.067),MOSS_LIGHT,turtle)
turtle_mouth=sphere("Moss mouth opening",(0,-.920,.731),(.20,.051,.036),DARK,turtle)
for side in (-1,1):
    for i in range(3):
        sphere("Moss faint old-age skin crease",
               (side*(.23+i*.031),-.81,.77+i*.045),(.032,.05,.009),
               MOSS_LIGHT,turtle,12,8)

def area(name,location,power,color,size):
    bpy.ops.object.light_add(type="AREA",location=location)
    ob=bpy.context.object; ob.name=name; ob.data.energy=power
    ob.data.color=color; ob.data.shape="DISK"; ob.data.size=size
    direction=Vector((0,0,1))-ob.location
    ob.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
area("warm cinematic key",(-3,-4,6),970,(1,.72,.43),4)
area("teal volumetric rim",(3,3,4),1350,(.26,.80,1),3)
area("gentle eye catchlights",(0,-3.5,4),400,(.9,.9,1),3)
bpy.ops.object.camera_add(location=(0,-6.4,2.6))
cam=bpy.context.object; S.camera=cam
direction=Vector((0,0,1.06))-cam.location
cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
cam.data.type="PERSP"; cam.data.lens=42
# Camera acts rather than a static slide.
for f in (1,max(2,FRAMES//2),FRAMES):
    t=(f-1)/FPS
    cam.location=(.0+.13*sin(t*.3),-6.4+.07*t,2.6-.015*t)
    direction=Vector((.08,0,1.06))-cam.location
    cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    cam.keyframe_insert(data_path="location",frame=f)
    cam.keyframe_insert(data_path="rotation_euler",frame=f)
# Every actor has gesture, body, eyes and mouth animations, not image zooms.
for f in range(1,FRAMES+1,max(1,FPS//3)):
    t=(f-1)/FPS
    fox.location=(-1.15+.035*sin(2.2*t),.05*sin(.7*t),.02*sin(2.7*t))
    fox.rotation_euler.z=.028*sin(1.5*t)
    fox.keyframe_insert(data_path="location",frame=f)
    fox.keyframe_insert(data_path="rotation_euler",frame=f)
    fox_head.rotation_euler.z=.045*sin(1.25*t)
    fox_head.keyframe_insert(data_path="rotation_euler",frame=f)
    tail.rotation_euler.x=.18*sin(1.7*t)
    tail.keyframe_insert(data_path="rotation_euler",frame=f)
    # Real moving mouth while Ember speaks, jaw opens/closes in depth.
    openness=1+.7*abs(sin(6.8*t))
    mouth.scale.z=.054*openness
    jaw.location.z=1.018-.035*abs(sin(6.8*t))
    mouth.keyframe_insert(data_path="scale",frame=f)
    jaw.keyframe_insert(data_path="location",frame=f)
    blink=.19 if 1.30<(t%4.3)<1.58 else 1
    for lid in (fox_lid_l,fox_lid_r):
        lid.scale.z=.07*blink
        lid.keyframe_insert(data_path="scale",frame=f)
    turtle.location=(1.14+.016*sin(.7*t),.15,.011*sin(.9*t))
    turtle.rotation_euler.z=.024*sin(.6*t)
    turtle.keyframe_insert(data_path="location",frame=f)
    turtle.keyframe_insert(data_path="rotation_euler",frame=f)
    turtle_head.rotation_euler.z=.035*sin(.8*t+.6)
    turtle_head.keyframe_insert(data_path="rotation_euler",frame=f)
    turtle_jaw.location.z=.689-.018*abs(sin(3.4*t))
    turtle_jaw.keyframe_insert(data_path="location",frame=f)

# This diagnostic is *not* a full G1 and does not include locked voice samples.
bpy.ops.render.render(animation=True)
seconds=time.time()-start
report={"status":"UNAPPROVED_CPU_3D_GEOMETRY_DIAGNOSTIC",
        "rendered_video":Path(OUT).exists(),
        "publicly_published":False,"owner_approved":False,
        "frames":FRAMES,"fps":FPS,"resolution":[WIDTH,HEIGHT],
        "actual_render_wall_seconds":round(seconds,2),
        "duration_seconds":round(FRAMES/FPS,2),
        "voice": "NOT INCLUDED; diagnostic only",
        "quality_gate":"FAIL_UNTIL_OWNER_VISUAL_APPROVAL_AND_15_TO_20_SECOND_PROOF",
        "asset_origin":"Original procedural Blender meshes, no external 3D assets used"}
Path("output/g1_geometry_report.json").write_text(json.dumps(report,indent=2)+"\n")
print("NIGHTFALL_GEOMETRY_DIAGNOSTIC_DONE",json.dumps(report))
