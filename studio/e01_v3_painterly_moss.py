"""Nightfall Moss v3: original high-detail stylized tortoise rig on free CPU.

Replaces the flat vector elder with texture-lit dome, natural scute plates,
subtle shell growth spiral, the required right-front shell crack, aged sage
skin, kind half-lidded amber eyes, four articulated heavy feet and real shadows.
This is original 2.5D painterly illustration, NOT generated 3D CGI.
"""
from functools import lru_cache
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from studio.cpu_motion_engine import W,H


def _ellipse(d,box,fill,outline=None,width=1):
    d.ellipse(tuple(int(x) for x in box),fill=fill,outline=outline,width=width)


def _painted_ellipse(canvas,cx,cy,rx,ry,rgb,seed=41,alpha=255):
    """Real smooth modeled normals and layered low/high-frequency texture."""
    rng=np.random.default_rng(seed)
    h,w=340,420
    yy,xx=np.ogrid[:h,:w]
    u=(xx-cx)/rx
    v=(yy-cy)/ry
    q=u*u+v*v
    inside=q<=1
    n=np.sqrt(np.maximum(0,1-q))
    sun=np.clip(.55*n-.38*u-.63*v,-1,1)
    field=rng.normal(0,1,(20,27))
    small=Image.fromarray(np.uint8(np.clip(field*34+127,0,255))).resize((w,h),Image.Resampling.BICUBIC)
    turbulence=(np.array(small).astype(float)-127)*.19
    grain=rng.normal(0,4,(h,w))
    res=np.empty((h,w,4),np.uint8)
    for k,base in enumerate(rgb):
        val=base+sun*(49 if k==1 else 37)+turbulence+grain
        # Warm etched edge/rim and subtle subsurface shading.
        res[:,:,k]=np.uint8(np.clip(val,4,244))
    edge=np.clip((1-q)*13,0,1)
    res[:,:,3]=np.uint8(np.where(inside,edge*alpha,0))
    layer=Image.fromarray(res,"RGBA")
    canvas.alpha_composite(layer)


@lru_cache(maxsize=1)
def parts():
    width,height=420,340
    def layer():return Image.new("RGBA",(width,height))
    feet=[]
    for i,x in enumerate((103,174,263,333)):
        foot=layer()
        # Gradient body skin rather than four flat circles.
        _painted_ellipse(foot,x,270,30,48,(80,123,89),seed=910+i)
        d=ImageDraw.Draw(foot,"RGBA")
        # Folds and wrinkles give an elderly animal, with natural pale claws.
        for k in range(3):
            _ellipse(d,(x-22+k*3,263+k*8,x+22-k*4,270+k*9),
                     None,outline=(32,68,51,118),width=2)
        for k in range(3):
            at=x-17+k*13
            d.polygon([(at-6,307),(at+8,306),(at+4,319),(at-5,319)],
                      fill=(200,187,133,245))
            d.line((at-3,309,at+3,307),fill=(255,243,196,170),width=2)
        feet.append(foot)
    # Lower abdomen and neck: shaped, layered olive skin.
    body=layer()
    _painted_ellipse(body,191,230,134,67,(76,117,79),seed=109)
    _painted_ellipse(body,311,218,79,47,(82,128,91),seed=110)
    d=ImageDraw.Draw(body,"RGBA")
    d.arc((254,182,379,272),start=208,end=338,
          fill=(181,193,130,135),width=4)
    # Shell is rounded and actually textured with coherent light/shade.
    shell=layer()
    _painted_ellipse(shell,185,169,155,96,(77,105,64),seed=255)
    sd=ImageDraw.Draw(shell,"RGBA")
    sd.arc((31,67,337,271),171,351,fill=(206,186,114,215),width=6)
    sd.arc((39,73,334,261),16,158,fill=(24,58,44,230),width=5)
    # Natural pentagonal shell scutes: neither a clock face nor scratch lines.
    scutes=[
       [(108,125),(137,101),(172,111),(186,139),(169,163),(128,159)],
       [(174,109),(207,91),(240,106),(255,137),(234,157),(186,141)],
       [(242,105),(276,115),(298,139),(290,164),(254,168),(235,148)],
       [(76,159),(117,152),(139,177),(127,209),(90,217),(62,192)],
       [(145,165),(187,146),(217,170),(211,208),(178,227),(134,206)],
       [(216,164),(258,158),(286,185),(268,217),(225,222),(209,203)],
       [(287,171),(316,180),(312,205),(282,221),(270,214)]
    ]
    for j,p in enumerate(scutes):
        # Drawing translucent fill directly onto an RGBA shell REPLACES
        # alpha, cutting large transparent holes. Keep original modeled
        # textured shell fully opaque, paint only opaque scute etching.
        sd.line(p+[p[0]],fill=(35,68,47,255),width=3,joint="curve")
        sd.line([(a[0]+2,a[1]-3) for a in p[:3]],
                fill=(175,166,101,255),width=2,joint="curve")
    # Growth spiral remains on the shell but is delicate and confined.
    for n in range(10,200,2):
        a=n*.078
        rad=n*.22
        xx=171+rad*math.cos(a)
        yy=183+rad*.52*math.sin(a)
        if ((xx-185)/155)**2+((yy-169)/96)**2<.8:
            _ellipse(sd,(xx-1,yy-1,xx+1,yy+1),(210,181,104,117))
    # Small front-right crack in canonical identity.
    sd.line([(304,221),(314,217),(310,229),(321,238),(313,248)],
            fill=(210,185,110,235),width=3,joint="curve")
    sd.line([(307,222),(313,220),(312,225)],
            fill=(35,61,40,220),width=2)
    # Moss head is distinct from torso, softly modeled, with beak/snouted jaw.
    head=layer()
    _painted_ellipse(head,346,177,57,63,(93,141,105),seed=771)
    _painted_ellipse(head,378,210,42,30,(101,155,117),seed=772)
    hd=ImageDraw.Draw(head,"RGBA")
    # Eyes: warm and kind, HALF-LIDDED, asymmetric as in a three-quarter view.
    for i,(cx,cy,rad) in enumerate(((332,168,15),(380,173,11))):
        _ellipse(hd,(cx-rad,cy-rad,cx+rad,cy+rad),
                 (224,213,169,255),outline=(53,82,58,230),width=2)
        _ellipse(hd,(cx-5,cy-4,cx+6,cy+7),(123,101,57,255))
        _ellipse(hd,(cx-2,cy-1,cx+4,cy+6),(26,40,34,255))
        _ellipse(hd,(cx-1,cy-4,cx+2,cy-1),(255,255,239,249))
        # Heavy moss-green upper eyelid covers upper third of the eye.
        hd.pieslice((cx-rad-3,cy-rad-6,cx+rad+2,cy+rad-3),180,360,
                    fill=(71,119,84,220))
        hd.arc((cx-rad-4,cy-rad-6,cx+rad+2,cy+rad-3),
               182,360,fill=(39,78,56,230),width=3)
        hd.arc((cx-rad-3,cy-rad-15,cx+rad+2,cy+rad-6),
               192,339,fill=(44,83,58,160),width=2)
    _ellipse(hd,(396,204,403,210),(40,61,49,225))
    hd.arc((354,204,411,247),15,143,fill=(45,76,56,239),width=3)
    hd.arc((317,226,379,259),195,301,fill=(176,186,127,78),width=2)
    # Age lines and tiny skin pores.
    rng=np.random.default_rng(893)
    for k in range(115):
        xx=int(rng.integers(296,408))
        yy=int(rng.integers(138,240))
        if ((xx-346)/57)**2+((yy-177)/63)**2<.83:
            _ellipse(hd,(xx,yy,xx+1,yy+1),(185,186,123,68))
    return feet,body,shell,head


def draw_moss(canvas,x,y,t,mouth,scale=1.0):
    feet,body,shell,head=parts()
    solo=scale>=.8
    # Original previous placement cut the character's face OFF the frame.
    if solo:
        scale=.81;x=min(x,184)
    else:
        scale=.52;x=min(x,247)
    spr=Image.new("RGBA",(420,340))
    for i,foot in enumerate(feet):
        joint_x=(103,174,263,333)[i]
        theta=(4.2 if i%2 else -4.2)*math.sin(t*2.0)
        spr.alpha_composite(foot.rotate(theta,center=(joint_x,258),
                     resample=Image.Resampling.BICUBIC))
    spr.alpha_composite(body)
    spr.alpha_composite(shell)
    spr.alpha_composite(head.rotate(1.45*math.sin(t*1.45),
                        center=(331,225),resample=Image.Resampling.BICUBIC))
    if mouth>.13:
        dd=ImageDraw.Draw(spr,"RGBA")
        k=round(min(11,mouth*11))
        _ellipse(dd,(370,229,392,234+k),(34,56,45,125))
    ww,hh=round(420*scale),round(340*scale)
    spr=spr.resize((ww,hh),Image.Resampling.LANCZOS)
    left=round(x-210*scale)
    top=round(y-307*scale)
    shadow=Image.new("RGBA",(W,H))
    sd=ImageDraw.Draw(shadow,"RGBA")
    _ellipse(sd,(x-102*scale,y-10,x+107*scale,y+12),(0,8,14,145))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(11)))
    canvas.alpha_composite(spr,(left,top))
