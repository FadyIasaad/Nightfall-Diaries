"""E01 V2: original story-matched painted sets and more detailed articulated Moss.

Independent motion remains 2.5D, not generative 3D. CPU-only; no network.
Scene settings faithfully follow the original canonical E01 scene directions.
"""
from functools import lru_cache
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from studio import painterly_reference_actor_v2 as ember
from studio.cpu_motion_engine import W, H

SETS = {
    1: ("burning_grove", "Ember escapes burning trees and collapsing branches"),
    2: ("wall_of_fire", "Ember calls out through the heat"),
    3: ("charred_clearing", "Ember discovers the glowing blue feather"),
    4: ("charred_clearing", "Ember reaches for the feather"),
    5: ("feather_closeup", "The feather reflects in Ember's fur"),
    6: ("smoke_firebreak", "Moss emerges from the smoke"),
    7: ("smoke_firebreak", "Ember sees Moss and the fire"),
    8: ("cliff_ledge", "Moss points out a narrow safe ledge"),
    9: ("collapsing_cliff", "Ground crumbles beneath the fox"),
    10: ("dangling_roots", "Ember clings to roots above the ravine"),
    11: ("rescue_ledge", "Moss braces and reaches for Ember"),
    12: ("blue_smoke_corridor", "Feather lights a path through smoke"),
    13: ("afterfire_path", "Ember chooses to follow the light"),
    14: ("mystery_silhouette", "An unknown form waits beyond the smoke"),
}
assert len(SETS)==14

def _ellipse(d,box,fill,width=0,outline=None):
    d.ellipse(tuple(round(v) for v in box),fill=fill,outline=outline,width=width)

@lru_cache(maxsize=14)
def story_set(scene):
    if scene not in SETS:raise ValueError("Story scene not in canonical E01")
    kind=SETS[scene][0]
    early=scene<=8
    cliff=scene in (8,9,10,11)
    blue=scene>=12 or scene in (3,4,5)
    sky=(10,17,34) if blue else (25,15,26)
    horizon=(30,72,94) if blue else (135,51,35)
    im=Image.new("RGB",(W,H))
    d=ImageDraw.Draw(im)
    for y in range(H):
        t=min(1,max(0,y/570))
        c=tuple(round(s*(1-t)+e*t) for s,e in zip(sky,horizon))
        d.line((0,y,W,y),fill=c)
    # Atmospheric soft-color glows behind branches; strongly distinct settings.
    haze=Image.new("RGBA",(W,H))
    hd=ImageDraw.Draw(haze,"RGBA")
    if blue:
        for rad,alpha in ((168,20),(126,30),(85,35),(46,60)):
            _ellipse(hd,(230-rad,287-rad,230+rad,287+rad),(40,192,235,alpha))
    else:
        for rad,alpha in ((180,20),(120,32),(80,46),(47,65)):
            _ellipse(hd,(95-rad,320-rad,95+rad,320+rad),(255,111,38,alpha))
    im=Image.alpha_composite(im.convert("RGBA"),haze.filter(ImageFilter.GaussianBlur(30)))
    d=ImageDraw.Draw(im,"RGBA")
    rng=random.Random(1400+scene*31)
    for layer in (0,1,2):
        for n in range(7):
            x=rng.randint(-35,W+25)
            y=rng.randint(280,560)
            ht=rng.randint(120,280)
            col=(9+4*layer,20+5*layer,25+6*layer,230) if blue else (17+5*layer,22+3*layer,27+2*layer,230)
            wd=3+layer*2
            d.line((x,y,x+17,y-ht),fill=col,width=wd)
            for branch in range(4):
                by=y-ht*(branch+.2)/4
                sign=(-1 if branch%2 else 1)
                d.line((x+15,by,x+15+sign*(25+layer*8),by-17),fill=col,width=max(2,wd-2))
    # Semantic foreground objects, not a repeating generic background.
    if kind in ("burning_grove","wall_of_fire"):
        for k in range(8):
            x=10+k*51+rng.randint(-18,12)
            y=445+rng.randint(-20,35)
            h=rng.randint(90,180)
            d.polygon([(x-20,y),(x-7,y-h*.72),(x+4,y-h),(x+13,y-h*.55),(x+24,y)],
                      fill=(239,73+rng.randint(0,80),30,150))
            d.polygon([(x-9,y),(x-3,y-h*.5),(x+6,y-h*.68),(x+12,y)],
                      fill=(255,199,76,188))
        if scene==1:
            d.line((10,165,340,265),fill=(39,28,27,255),width=16)
            d.line((10,162,340,262),fill=(142,79,42,115),width=4)
    elif kind in ("charred_clearing","feather_closeup"):
        d.ellipse((-160,418,490,790),fill=(26,50,54,245))
        for i in range(24):
            x=rng.randint(0,W);y=rng.randint(430,610)
            d.line((x,y,x+10,y-9),fill=(44,83,73,160),width=2)
        # feather feature glow in midground, animated separately in foreground
        _ellipse(d,(215,242,285,312),(69,213,245,26))
    elif kind in ("smoke_firebreak",):
        d.polygon([(0,480),(155,449),(360,482),(360,640),(0,640)],fill=(37,49,42,240))
        for x in range(0,W,42):
            d.line((x,465,x+24,480),fill=(128,88,61,92),width=3)
    elif cliff:
        # Broken cliff edge and deep ravine; roots and ledge actually visible.
        d.polygon([(0,435),(128,407),(172,429),(181,492),(122,520),(0,530)],
                  fill=(73,64,55,255))
        d.polygon([(174,465),(200,432),(360,453),(360,520),(240,502)],
                  fill=(79,69,58,255))
        d.polygon([(122,520),(180,493),(240,502),(360,520),(360,640),(0,640)],
                  fill=(10,22,36,230))
        for j in range(6):
            xx=172+j*10
            d.arc((xx-17,395,xx+55,547),0,120,fill=(95,67,44,220),width=3)
        if kind in ("collapsing_cliff","dangling_roots"):
            for j in range(16):
                x=rng.randint(90,250);y=rng.randint(465,560)
                d.ellipse((x,y,x+3,y+3),fill=(155,120,87,175))
    elif kind in ("blue_smoke_corridor","afterfire_path"):
        d.polygon([(0,640),(90,490),(176,408),(223,414),(274,490),(360,640)],
                  fill=(19,55,67,205))
        d.line((186,545,198,401),fill=(67,191,209,105),width=3)
        for j in range(10):
            x=rng.randint(0,W);y=rng.randint(300,480)
            _ellipse(d,(x-3,y-3,x+3,y+3),(111,237,245,140))
    elif kind=="mystery_silhouette":
        d.polygon([(0,640),(130,445),(195,409),(264,456),(360,640)],fill=(16,44,58,245))
        # Only a vague unknown silhouette, canon requires NO reveal.
        _ellipse(d,(180,230,270,360),(10,30,43,90))
    # Lighting gradients/foreground cinematic floor.
    floor=Image.new("RGBA",(W,H))
    fd=ImageDraw.Draw(floor,"RGBA")
    for k in range(6):
        y=505+k*25
        fd.line((0,y,W,y),fill=(4,13,20,10+k*6),width=18)
    im=Image.alpha_composite(im,floor.filter(ImageFilter.GaussianBlur(7)))
    return im

@lru_cache(maxsize=1)
def moss_parts():
    """Detailed shaded elder tortoise: scutes, raised shell, crack, aged skin."""
    sz=(420,340)
    def blank():return Image.new("RGBA",sz)
    legs=[]
    for j,x in enumerate((105,167,255,326)):
        L=blank();d=ImageDraw.Draw(L,"RGBA")
        _ellipse(d,(x-31,236,x+34,314),(39,83,65,255))
        for k in range(15):
            rr=max(1,29-k*2)
            _ellipse(d,(x-rr,239+k,x+rr,311-k*.12),(72+k*2,121+k,85+k,50))
        for k in range(3):
            _ellipse(d,(x-26+k*16,302,x-12+k*16,320),(198,174,114,230))
        legs.append(L)
    shell=blank();d=ImageDraw.Draw(shell,"RGBA")
    _ellipse(d,(36,79,350,266),(20,53,45,245))
    for i in range(29):
        margin=i*2.8
        c=(46+int(i*.55),73+int(i*1.15),54+int(i*.6),255)
        _ellipse(d,(45+margin,78+margin*.41,344-margin,263-margin*.26),c)
    # 3D shell highlight and scute pattern with varied textured strokes.
    for k in range(7):
        u=(k+1)/8
        x=55+274*u
        y=96+45*(1-(1-2*u)**2)
        d.arc((x-44,y-20,x+45,y+70),180,350,fill=(142,163,104,155),width=3)
    for i in range(7):
        a=(i/7)*6.28
        x=195+115*math.cos(a)
        y=171+67*math.sin(a)
        d.line((190,167,x,y),fill=(25,74,55,135),width=3)
    for a in range(90,860,2):
        t=a/92
        rr=5+t*5
        x=195+rr*math.cos(t);y=170+rr*.57*math.sin(t)
        d.point((x,y),fill=(167,151,89,215))
    rng=random.Random(91)
    for k in range(420):
        x=rng.randint(48,343);y=rng.randint(90,249)
        if ((x-196)/154)**2+((y-171)/94)**2<1:
            tone=rng.randint(80,155)
            d.point((x,y),fill=(tone,tone+8,tone-25,rng.randint(55,130)))
    # Tiny canonical crack on front-right shell edge.
    d.line([(322,205),(330,198),(326,214),(338,224),(333,238)],
           fill=(205,194,127,245),width=3,joint="curve")
    d.arc((49,70,343,271),185,353,fill=(184,166,99,225),width=4)
    neck=blank();d=ImageDraw.Draw(neck,"RGBA")
    _ellipse(d,(279,179,381,253),(62,116,86,255))
    for k in range(7):
        _ellipse(d,(289+k*2,184+k*.9,383-k,245-k*.4),
                 (91+2*k,135+2*k,100+k,72))
    head=blank();d=ImageDraw.Draw(head,"RGBA")
    _ellipse(d,(300,118,414,250),(38,90,68,255))
    for k in range(15):
        _ellipse(d,(303+k*.4,119+k*.7,411-k*.6,242-k*.8),
                 (84+2*k,119+2*k,92+k,30))
    # Half-lidded wise eyes, warm amber iris, catchlights.
    for x in (329,378):
        _ellipse(d,(x-15,145,x+16,184),(229,216,171,255))
        _ellipse(d,(x-6,154,x+10,175),(107,91,51,255))
        _ellipse(d,(x-1,155,x+7,174),(27,39,36,255))
        _ellipse(d,(x+1,155,x+5,159),(255,247,216,240))
        d.arc((x-19,139,x+18,167),182,354,fill=(45,80,60,245),width=5)
    _ellipse(d,(399,203,406,210),(46,64,51,255))
    d.arc((357,209,403,241),14,156,fill=(44,73,57,245),width=3)
    for k in range(70):
        x=303+(k*37)%96;y=161+(k*13)%83
        _ellipse(d,(x,y,x+2,y+2),(168,178,125,92))
    return shell,neck,head,legs

def draw_moss(canvas,x,y,t,speech,scale=.75):
    shell,neck,head,legs=moss_parts()
    spr=Image.new("RGBA",(420,340))
    for i,L in enumerate(legs):
        angle=(1 if i%2 else -1)*4.7*math.sin(t*2.1)
        spr.alpha_composite(L.rotate(angle,center=(106+76*i,244),resample=Image.Resampling.BICUBIC))
    spr.alpha_composite(shell)
    spr.alpha_composite(neck)
    spr.alpha_composite(head.rotate(1.7*math.sin(t*1.7),center=(327,209),resample=Image.Resampling.BICUBIC))
    if speech>.12:
        d=ImageDraw.Draw(spr,"RGBA")
        _ellipse(d,(375,223,399,230+min(14,int(speech*14))),(51,58,48,172))
    ww,hh=round(420*scale),round(340*scale)
    spr=spr.resize((ww,hh),Image.Resampling.LANCZOS)
    # x,y in video frame give body center and ground anchor
    left=round(x-210*scale);top=round(y-308*scale)
    ground=Image.new("RGBA",(W,H));g=ImageDraw.Draw(ground,"RGBA")
    _ellipse(g,(x-95*scale,y-11,x+105*scale,y+11),(0,9,20,115))
    canvas.alpha_composite(ground.filter(ImageFilter.GaussianBlur(9)))
    canvas.alpha_composite(spr,(left,top))

def frame(scene,t,mouth,voice_sec,words,speaker,visible,direction):
    from studio.painterly_reference_actor_v2 import puppet
    canvas=story_set(scene).copy()
    d=ImageDraw.Draw(canvas,"RGBA")
    # Real moving smoke/fire/reflections independent of character positions.
    rng=random.Random(scene*201)
    kind=SETS[scene][0]
    for k in range(39):
        x=((k*53)+t*(9+(k%6))+(k%9)*7)%(W+20)-10
        y=((k*67)-t*(19+k%7))%(H+30)-10
        rr=1+(k%3)
        col=(255,160,82,125) if scene<12 else (102,218,240,132)
        _ellipse(d,(x-rr,y-rr,x+rr,y+rr),col)
    action=("run" if scene in (1,2,9,10) else "struggle" if scene in (8,11) else "walk")
    dual="s01_moss" in visible and "s01_ember" in visible
    if "s01_ember" in visible:
        layer=puppet(t,mouth if speaker=="s01_ember" else .1,action)
        scale=(.51 if dual else .76)
        if scene in (3,4,5):scale=.82
        if scene in (9,10):scale=.7
        if scene==14:scale=.56
        art=layer.resize((round(512*scale),round(640*scale)),Image.Resampling.LANCZOS)
        x=(-25 if dual else 8)+int(math.sin(t*1.0)*7)
        if scene in (9,10):x=14+int(math.sin(t*2)*4)
        y=(118 if dual else 64)+int(math.sin(t*(4.8 if action=="run" else 1.6))*4)
        if scene in (9,10):y=125+int(t*3)%6
        sh=Image.new("RGBA",(W,H));sd=ImageDraw.Draw(sh,"RGBA")
        bottom=y+int(640*scale*.81)
        _ellipse(sd,(x+80*scale,bottom-6,x+420*scale,bottom+13),(1,11,18,107))
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
        canvas.alpha_composite(art,(x,y))
    if "s01_moss" in visible:
        cx=272 if dual else 185
        cy=488 if dual else 504
        if scene==11:cy=474
        draw_moss(canvas,cx,cy,t,mouth if speaker=="s01_moss" else .09,scale=(.55 if dual else 1.0))
    d=ImageDraw.Draw(canvas,"RGBA")
    if scene in (3,4,5,12,13,14):
        xx=269+23*math.sin(t*.7+scene)
        yy=235+31*math.sin(t*1.2)
        for rad,a in ((38,14),(25,21),(11,57)):
            _ellipse(d,(xx-rad,yy-rad,xx+rad,yy+rad),(59,205,243,a))
        d.polygon([(xx-9,yy+16),(xx+2,yy-22),(xx+10,yy-28),(xx+9,yy+8)],
                  fill=(158,239,248,225))
        d.line((xx-8,yy+22,xx+8,yy-23),fill=(245,250,252,220),width=2)
    # Quiet ending silhouette remains UNKNOWN; don't reveal mystery culprit.
    if scene==14:
        _ellipse(d,(169,203,253,370),(2,21,31,56))
    ember._caption(canvas,speaker,words,t,voice_sec)
    return canvas.convert("RGB")
