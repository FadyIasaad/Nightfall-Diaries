"""Professional SHA-verified original Ember puppet with GrabCut fur-edge matte.

The original 512x640 approved illustration is NEVER redrawn or overwritten.
Use CPU OpenCV GrabCut with manually identified hero anatomy as trimap hints;
then animate true separately cut head, tail, torso, paws and scarf over a
cinematic defocused background. Still 2.5D cutout, not an AI 3D video.
"""
from functools import lru_cache
import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

from pilot import e01_full_run
from studio.continuity import sha256
from studio.cpu_motion_engine import W, H
from studio.painterly_reference_actor import _caption, _feather, _moss

SOURCE = e01_full_run.CINEMATIC_IMAGE
SHA = e01_full_run.SOURCE_SHA
SCHEMA = "nightfall-approved-ember-clean-matte-25d-v2"
SOURCE_SIZE = (512, 640)
RESAMPLE = Image.Resampling.LANCZOS


def _shape(points, blur=1.5):
    im = Image.new("L", SOURCE_SIZE)
    ImageDraw.Draw(im).polygon(points, fill=255)
    return im.filter(ImageFilter.GaussianBlur(blur))


@lru_cache(maxsize=1)
def approved_cutout():
    import cv2
    if not SOURCE.is_file() or sha256(SOURCE) != SHA:
        raise RuntimeError("ORIGINAL_EMBER_ART_SHA256_NOT_LOCKED")
    original = Image.open(SOURCE).convert("RGB")
    if original.size != SOURCE_SIZE:
        raise RuntimeError("ORIGINAL_EMBER_ART_512X640_DIMENSION_CHANGED")
    pixels = np.array(original)
    w, h = SOURCE_SIZE
    # Exact 512x640 original heroine, not hand-traced emoji or static slide.
    # Background is definite non-character; relaxed polygon is probable hero.
    outer = [
        (28,224),(49,197),(96,201),(165,219),(160,177),(169,130),
        (177,80),(203,70),(230,119),(278,110),(301,51),(324,45),
        (344,87),(351,135),(380,165),(393,190),(390,222),(360,251),
        (352,308),(377,347),(394,382),(393,412),(372,443),
        (317,452),(291,430),(277,471),(255,483),(219,467),
        (203,473),(188,516),(172,536),(110,541),(80,535),
        (61,511),(67,454),(43,460),(20,426),(21,364),
        (53,323),(96,320),(138,322),(125,300),(69,280),(23,271)
    ]
    grab = np.zeros((h,w), np.uint8)
    cv2.fillPoly(grab, [np.asarray(outer,np.int32)], cv2.GC_PR_FGD)
    foreground = np.zeros((h,w), np.uint8)
    seeds = [
        (261,182,77,72,0),
        (215,365,111,71,0),
        (112,390,57,55,0),
        (326,359,28,35,0),
        (94,487,25,41,-14),
        (191,464,15,40,15),
        (211,495,12,17,0),
        (337,396,28,32,-12),
        (239,419,36,24,0),
        (303,98,16,33,0),
        (200,122,16,39,0),
        (245,253,84,21,0),
    ]
    for cx,cy,rx,ry,angle in seeds:
        cv2.ellipse(foreground,(cx,cy),(rx,ry),angle,0,360,255,-1)
    grab[foreground>0]=cv2.GC_FGD
    bgmodel=np.zeros((1,65),np.float64)
    fgmodel=np.zeros((1,65),np.float64)
    cv2.grabCut(pixels[:,:,::-1].copy(),grab,None,bgmodel,fgmodel,
                7,cv2.GC_INIT_WITH_MASK)
    mask=np.where((grab==cv2.GC_FGD)|(grab==cv2.GC_PR_FGD),
                  255,0).astype("uint8")
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,
                          np.ones((5,5),np.uint8))
    full=Image.fromarray(mask).filter(ImageFilter.GaussianBlur(1.2))
    if not 80000 < int(np.count_nonzero(mask)) < 150000:
        raise RuntimeError("EMBER_MATTE_OUT_OF_SAFE_HERO_AREA")
    # The details of the fur, white left ear tip, teal scarf and one star
    # come from original approved pixels, not from procedural vector painting.
    head=ImageChops.multiply(full,_shape([
        (178,71),(207,66),(233,113),(267,117),(287,61),
        (328,45),(346,125),(380,164),(392,202),
        (379,236),(347,262),(310,281),(257,287),
        (216,278),(189,250),(167,216),(167,143)
    ],7))
    tail=ImageChops.multiply(full,_shape([
        (22,365),(37,331),(76,315),(132,309),(175,327),
        (193,360),(195,412),(167,448),(89,476),
        (45,451),(18,407)
    ],8))
    forepaw=ImageChops.multiply(full,_shape([
        (287,336),(340,338),(373,360),(393,401),
        (390,445),(319,449),(287,420)
    ],8))
    hindpaw=ImageChops.multiply(full,_shape([
        (64,423),(121,412),(151,433),(143,505),
        (111,539),(62,533),(57,494)
    ],8))
    scarf=ImageChops.multiply(full,_shape([
        (31,217),(82,196),(158,204),(218,226),
        (299,215),(359,252),(351,292),
        (294,316),(202,298),(139,298),(71,283),(24,263)
    ],7))
    # Left-behind body is free of head and tail duplicates. Feather mask
    # overlap around chin and shoulder is intentionally soft.
    body=ImageChops.subtract(ImageChops.subtract(full,head),tail)
    def part(a):
        obj=original.convert("RGBA")
        obj.putalpha(a)
        return obj
    return original, {k:part(m) for k,m in {
        "body":body, "head":head, "tail":tail,
        "forepaw":forepaw, "hindpaw":hindpaw, "scarf":scarf,
    }.items()}


@lru_cache(maxsize=16)
def backdrop(scene):
    source,_=approved_cutout()
    # Heavily defocused reference removes any second recognizable fox.
    image=source.filter(ImageFilter.GaussianBlur(42))
    image=image.crop((30,0,482,640)).resize((W,H),RESAMPLE)
    image=ImageEnhance.Color(image).enhance(.92)
    layer=Image.new("RGBA",(W,H),
                    (13,22,42,76) if scene>=12 else (37,19,25,69))
    result=Image.alpha_composite(image.convert("RGBA"),layer)
    d=ImageDraw.Draw(result,"RGBA")
    r=random.Random(3000+scene)
    for i in range(10):
        x=r.randrange(-20,W+20)
        y=r.randrange(340,600)
        height=r.randrange(85,265)
        color=(11,25,34,110) if i%2 else (4,21,28,130)
        d.line((x,y,x-7,y-height),fill=color,width=4)
        for k in range(3):
            yy=y-height+(k+1)*height/4
            d.line((x-7,yy,x-30 if k%2 else x+30,yy-16),
                   fill=color,width=3)
    return result


def _rotated(part,degrees,joint):
    return part.rotate(degrees,center=joint,
                       resample=Image.Resampling.BICUBIC)


def puppet(t,mouth,action):
    original,parts=approved_cutout()
    image=Image.new("RGBA",SOURCE_SIZE)
    speed=7.3 if action in ("run","jump","struggle") else 2.4
    phase=math.sin(t*speed)
    # Real articulation, with authored root motion around anatomy joints.
    image.alpha_composite(_rotated(parts["tail"],
                                 8*math.sin(t*2.7),(172,366)))
    image.alpha_composite(_rotated(parts["hindpaw"],5*phase,(112,435)))
    image.alpha_composite(parts["body"])
    image.alpha_composite(_rotated(parts["forepaw"],-5*phase,(320,350)))
    image.alpha_composite(_rotated(parts["head"],1.6*math.sin(t*1.7),
                                  (252,260)))
    image.alpha_composite(_rotated(parts["scarf"],1.4*math.sin(t*2.8),
                                  (267,254)))
    # Mouth is dynamic but only amplitude-timed, not phoneme-level lip sync.
    if mouth>.12:
        # This is a small jaw color/shadow inside the existing muzzle.
        d=ImageDraw.Draw(image,"RGBA")
        val=2+round(min(8,mouth*7))
        d.ellipse((337,212,350,218+val),fill=(58,34,39,115))
    return image


def render_frame(scene,t,mouth,voice_seconds,text,speaker,visible,direction):
    canvas=backdrop(scene).copy()
    d=ImageDraw.Draw(canvas,"RGBA")
    if "s01_ember" in visible:
        a=direction.lower()
        act=("run" if any(w in a for w in ("run","leapt","jumps","springs"))
             else "struggle" if any(w in a for w in ("slid","climb","grips"))
             else "walk")
        art=puppet(t,mouth if speaker=="s01_ember" else .1,act)
        dual="s01_moss" in visible
        scale=.57 if dual else .79
        art=art.resize((round(512*scale),round(640*scale)),RESAMPLE)
        x=(-17 if dual else 5)+int(math.sin(t*.7)*5)
        y=(104 if dual else 48)+int(math.sin(t*(4.7 if act=="run" else 1.5))*
                                    (5 if act=="run" else 2))
        # Ground-contact shade follows the actual character location, not
        # the background. It is painted UNDER the puppet's paws.
        contact = Image.new("RGBA",(W,H))
        shadow = ImageDraw.Draw(contact,"RGBA")
        floor_y = min(H-120, y + int(640*scale*0.83))
        foot_cx = x + int(242*scale)
        spread = 79 if not dual else 55
        shadow.ellipse((foot_cx-spread, floor_y-12, foot_cx+spread,
                        floor_y+17), fill=(1,10,17,105))
        contact = contact.filter(ImageFilter.GaussianBlur(11))
        canvas.alpha_composite(contact)
        canvas.alpha_composite(art,(x,y))
    if "s01_moss" in visible:
        _moss(canvas,260 if "s01_ember" in visible else 166,
              420,t,mouth if speaker=="s01_moss" else .15,
              .56 if "s01_ember" in visible else 1.0)
    d=ImageDraw.Draw(canvas,"RGBA")
    for i in range(40):
        x=(i*61+t*(9+i%5))%(W+20)-10
        y=(i*71-t*(12+i%9))%(H+25)-15
        rad=(i%3)+1
        d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=(
            (255,170,84,110) if scene<=11 else (113,205,239,90)))
    _feather(d,scene,t)
    _caption(canvas,speaker,text,t,voice_seconds)
    return canvas.convert("RGB")
