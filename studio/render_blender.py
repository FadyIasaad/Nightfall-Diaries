"""Blender-driven procedural animated 3D characters. No image slides."""
import bpy,sys,json,math,random
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];plan=json.load(open(args[0]));n=int(args[1]);target=args[2]
scene=plan['scenes'][n];duration=plan['durations'][n];fps=18;frames=round(duration*fps)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
world=bpy.context.scene.world or bpy.data.worlds.new('Nightfall fantasy environment');bpy.context.scene.world=world;world.use_nodes=True;world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.025,.045,.095,1)
def mat(name,rgb,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=.65;return m
def sphere(name,loc,scale,material,parent=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material)
 if parent:o.parent=parent
 return o
orange=mat('Warm red fox',(.72,.24,.08));cream=mat('Cream',(.95,.77,.52));teal=mat('Teal scarf',(.05,.45,.5));gold=mat('Gold',(.96,.67,.16));ink=mat('Dark eyes',(.008,.015,.025));blue=mat('Glowing blue',(.12,.47,.93));floor=mat('Forest ground',(.03,.12,.12));pale=mat('Skin',(.68,.53,.44));coat=mat('Clothing',(.16,.23,.38))
bpy.ops.mesh.primitive_plane_add(size=100,location=(0,0,-.3));bpy.context.object.data.materials.append(floor)
character=scene['character_id'];fox=character.startswith('s01_');random.seed(5+n)
root=sphere('Animated actor root',(0,0,0),(.01,.01,.01),orange)
if fox:
 sphere('Ember body',(0,0,.73),(.63,.31,.49),orange,root);sphere('Cream chest',(.17,-.23,.75),(.25,.14,.39),cream,root)
 head=sphere('Expressive fox head',(.24,0,1.46),(.43,.35,.4),orange,root)
 for side in (-1,1):
  sphere('Fox ear',(.18,side*.27,1.83),(.13,.13,.32),orange,root)
  sphere('Amber animated eye',(.58,side*.17,1.53),(.09,.065,.12),gold,root)
  sphere('Pupil',(.657,side*.17,1.53),(.03,.04,.06),ink,root)
 sphere('Muzzle',(.6,0,1.3),(.22,.24,.16),cream,root)
 mouth=sphere('Speaking mouth',(.78,0,1.23),(.035,.075,.015),ink,root)
 sphere('Teal scarf',(.24,0,1.03),(.30,.34,.10),teal,root)
 sphere('Scarf star',(.47,-.12,1.04),(.045,.05,.045),gold,root)
 tail=sphere('Moving tail',(-.7,0,.77),(.65,.19,.22),orange,root)
 sphere('White tail tip',(-1.17,0,.81),(.18,.16,.19),cream,root)
else:
 sphere('Body',(0,0,.86),(.35,.25,.72),coat,root);sphere('Head',(0,0,1.79),(.29,.25,.34),pale,root)
 for side in (-1,1):
  sphere('Eye',(side*.13,-.235,1.84),(.045,.037,.05),ink,root)
  arm=sphere('Arm',(side*.45,0,1.09),(.13,.15,.51),coat,root)
 sphere('Hair',(0,0,2.04),(.3,.26,.15),ink,root)
 mouth=sphere('Moving lips',(0,-.252,1.63),(.07,.018,.025),ink,root)
 tail=None
for i in range(16):
 x=random.uniform(-7,7);y=random.uniform(-7,7)
 if abs(x)<1.9 and abs(y)<1.9:continue
 if fox:
  trunk=mat('Wood',(.14,.095,.07))
  bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.13,depth=2.6,location=(x,y,1));bpy.context.object.data.materials.append(trunk)
  sphere('Tree crown',(x,y,2.4),(.68,.68,1.1),teal)
 else:
  bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,.65));o=bpy.context.object;o.scale=(.9,.7,1.5);o.data.materials.append(coat)
bpy.ops.object.light_add(type='AREA',location=(1,-3,5));bpy.context.object.data.energy=750;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=6
bpy.ops.object.light_add(type='POINT',location=(-2,2,2));bpy.context.object.data.energy=260;bpy.context.object.data.color=(.3,.65,1)
bpy.ops.object.camera_add(location=(4,-7,2.9));cam=bpy.context.object;direction=Vector((0,0,1.16))-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.4;bpy.context.scene.camera=cam
for f in range(1,frames+1,6):
 t=f/fps
 root.location.z=.06*math.sin(t*4);root.rotation_euler.z=.14*math.sin(t*1.4+n);root.keyframe_insert(data_path='location',frame=f);root.keyframe_insert(data_path='rotation_euler',frame=f)
 mouth.scale.z=.045+.14*abs(math.sin(t*12));mouth.keyframe_insert(data_path='scale',frame=f)
 if tail:tail.rotation_euler.y=.16*math.sin(t*3);tail.keyframe_insert(data_path='rotation_euler',frame=f)
 cam.location.x=4+0.2*math.sin(t*.21+n);cam.location.z=2.9+.08*math.sin(t*.4);cam.keyframe_insert(data_path='location',frame=f)
s=bpy.context.scene;s.frame_start=1;s.frame_end=frames;s.render.engine='CYCLES';s.cycles.samples=8
# Ubuntu's packaged Blender can lack OpenImageDenoiser; disable denoising on CPU runners.
bpy.context.view_layer.cycles.use_denoising = False
s.render.resolution_x=360;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.fps=fps
s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='MEDIUM';s.render.filepath=target
bpy.ops.render.render(animation=True)
