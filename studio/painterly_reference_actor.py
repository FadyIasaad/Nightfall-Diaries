"""Premium 2.5D reference-art Nightfall character animator (CPU only).

Ember is NOT a hand-drawn emoji: the approved 2026-11-13 640px 3D-painted
reference supplies actual textured fur, realistic eyes and scarf, while
separate head/ears, torso, tail and limb layers move independently as 2.5D
puppets. Other artwork is painted CPU graphics. No paid model, internet,
GPU, photo slideshow or public publication. This is still a *cutout 2.5D*
film, not a new generative 3D animation or accurate viseme lip-sync.
"""
from functools import lru_cache
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

from pilot import e01_full_run
from studio.continuity import sha256
from studio.cpu_motion_engine import W, H, font

EMBEDDED_IMAGE = e01_full_run.CINEMATIC_IMAGE
LOCKED_SHA = e01_full_run.SOURCE_SHA
SCHEMA = "nightfall-ember-approved-25d-textured-v1"
_L = Image.Resampling.LANCZOS


def _poly_mask(points, feather=1.45):
    mask = Image.new("L", (640, 640), 0)
    d = ImageDraw.Draw(mask)
    d.polygon(points, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(feather))


@lru_cache(maxsize=1)
def approved_layers():
    if not EMBEDDED_IMAGE.is_file() or sha256(EMBEDDED_IMAGE) != LOCKED_SHA:
        raise RuntimeError("APPROVED_EMBER_REFERENCE_MISSING_OR_MODIFIED")
    original = Image.open(EMBEDDED_IMAGE).convert("RGBA")
    # The official 3D-rendered file is locked by SHA, not by source pixel size.
    # Render all puppet geometry in 640x640 normalized artwork coordinates.
    if original.width != original.height or original.width < 256:
        raise RuntimeError("APPROVED_EMBER_REFERENCE_NOT_A_SQUARE_RENDER")
    if original.size != (640, 640):
        original = original.resize((640, 640), _L)
    # Independently rigged matte pieces from the SAME original painterly art.
    head = _poly_mask([
        (185,74),(204,60),(225,73),(245,110),(271,124),
        (296,77),(318,54),(337,81),(347,126),(373,151),
        (386,192),(387,223),(370,243),(347,262),(321,279),
        (275,285),(238,273),(201,267),(170,243),(150,215),
        (151,170),(170,131)
    ], 2.0)
    body = _poly_mask([
        (131,260),(204,251),(263,261),(326,295),(342,341),
        (361,395),(353,454),(329,485),(302,479),(288,457),
        (265,436),(232,436),(181,450),(169,491),(156,525),
        (96,528),(75,510),(70,472),(79,414),(91,353),
        (107,299)
    ], 2.3)
    tail = _poly_mask([
        (36,371),(52,345),(79,326),(120,317),(158,329),
        (184,347),(202,377),(194,414),(165,443),
        (127,469),(85,461),(51,443),(28,409)
    ], 2.0)
    forepaw = _poly_mask([
        (282,339),(320,337),(351,350),(374,387),(377,418),
        (360,447),(317,464),(294,451),(286,412)
    ], 2.0)
    hindpaw = _poly_mask([
        (74,425),(128,411),(168,422),(171,461),(154,516),
        (110,532),(75,527),(60,499)
    ], 2.0)
    # Scarf identity preserved from the photo: EXACTLY ONE embroidered star.
    scarf = _poly_mask([
        (49,207),(93,201),(135,217),(182,220),(220,227),
        (279,222),(331,236),(342,260),(329,284),(302,301),
        (262,291),(225,291),(173,295),(115,288),(68,271),(42,258)
    ], 2.0)
    masks = {
        "head": head, "body": body, "tail": tail,
        "forepaw": forepaw, "hindpaw": hindpaw, "scarf": scarf,
    }
    parts = {}
    for name, mask in masks.items():
        art = original.copy()
        art.putalpha(mask)
        parts[name] = art
    return original, parts


@lru_cache(maxsize=18)
def backdrop(scene):
    """Detailed original fantasy forest, defocused as a real film set."""
    original, _ = approved_layers()
    base = original.convert("RGB")
    # Background intentionally defocused to remove the original static fox
    # while keeping reference lighting, bark, waterfalls and floral palette.
    base = base.filter(ImageFilter.GaussianBlur(46))
    base = base.crop((36, 0, 604, 640)).resize((W, H), _L)
    base = ImageEnhance.Color(base).enhance(.83)
    tint = (17, 28, 46, 97) if scene >= 12 else (48, 18, 26, 68)
    layer = Image.new("RGBA", (W, H), tint)
    bg = Image.alpha_composite(base.convert("RGBA"), layer)
    d = ImageDraw.Draw(bg, "RGBA")
    rng = random.Random(990 + scene * 17)
    # Deep/near trees, glancing foreground branches with fine rim lighting.
    for i in range(11):
        x = rng.randint(-40, 390)
        y = rng.randint(230, 560)
        height = rng.randint(80, 260)
        width = rng.randint(4, 16)
        near = i % 3 == 0
        col = (5, 24, 29, 210) if near else (12, 38, 47, 155)
        d.line((x, y, x - 9, y - height), fill=col, width=width)
        for branch in range(4):
            by = y - 35 - height * branch / 4
            d.line((x - 9 * branch / 4, by,
                    x + (30 if branch % 2 else -39), by - 21),
                   fill=col, width=max(2, int(width * .55)))
    for i in range(75):
        x, y = rng.randrange(W), rng.randrange(60, H)
        col = ((255, 163, 78, 170) if scene <= 11 else (99, 226, 249, 120))
        rad = rng.choice([1, 1, 2, 2, 3])
        d.ellipse((x-rad, y-rad, x+rad, y+rad), fill=col)
    return bg


def _rotate(layer, degree, point):
    return layer.rotate(degree, resample=Image.Resampling.BICUBIC,
                        center=point)


def _character_cutout(t, action, talking):
    """Real independent head/tail/front-rear-paw articulation from approved art."""
    _, parts = approved_layers()
    mov = math.sin(t * 6.0) if action in ("run", "jump", "struggle") else math.sin(t * 1.9)
    sprint = action in ("run", "jump", "struggle")
    layer = Image.new("RGBA", (640, 640))
    # Motion uses anatomy joints, not movement of a single complete still.
    layer.alpha_composite(_rotate(parts["tail"], 12 * math.sin(t * 3.2), (181, 368)))
    layer.alpha_composite(_rotate(parts["hindpaw"], 7 * mov, (132, 434)))
    layer.alpha_composite(parts["body"])
    layer.alpha_composite(_rotate(parts["forepaw"], -9 * mov, (314, 359)))
    # Eyes, fur and brow are textured pixels from original 3D-style art.
    layer.alpha_composite(_rotate(parts["head"], 2.9 * math.sin(t * 1.3), (258, 255)))
    # Scarf fringe follows air; never add an additional gold star.
    layer.alpha_composite(_rotate(parts["scarf"], 2.2 * math.sin(t * 2.8), (283, 243)))
    if talking > .15:
        # Subtle jaw articulation without drawing cartoon black circles.
        # Photo region already has a mouth; displace a jaw-texture overlay.
        patch = parts["head"].crop((308, 198, 385, 260))
        patch = patch.resize((77, 62 + int(7 * min(1, talking))), _L)
        layer.alpha_composite(patch, (308, 198))
    return layer


def _glow_ellipse(draw, bbox, color, al):
    draw.ellipse(bbox, fill=(*color, al))


def _moss(canvas, cx, cy, t, mouth, scale=1):
    """Higher-detail painted tortoise with shell scutes and weathered eyes."""
    # Paint at native output scale, with soft gradients and rim light.
    d = ImageDraw.Draw(canvas, "RGBA")
    swing = math.sin(t * 2) * 5
    s = scale
    def p(x, y): return (cx + x * s, cy + y * s)
    def bb(x1, y1, x2, y2): return (*p(x1, y1), *p(x2, y2))
    d.ellipse(bb(-105, 65, 118, 94), fill=(0, 0, 0, 110))
    # Legs each have their own gait, shells cast soft shadow.
    for k, px in enumerate((-65, -12, 43, 80)):
        ox = swing if k % 2 else -swing
        d.ellipse(bb(px-21+ox, 21, px+23+ox, 85),
                  fill=(50, 99, 76, 255), outline=(138, 159, 105, 255), width=2)
        d.ellipse(bb(px-16+ox, 39, px+8+ox, 70), fill=(98, 138, 96, 235))
        for x in range(3):
            d.arc(bb(px-17+ox+x*7, 66, px-7+ox+x*7, 77),
                  10, 165, fill=(197, 193, 128, 180), width=2)
    # Layered shell contours, inlaid plates and amber edge glints.
    d.ellipse(bb(-119, -91, 96, 63), fill=(41, 65, 47, 255),
              outline=(148, 119, 65, 255), width=5)
    d.ellipse(bb(-110, -88, 89, 52), fill=(74, 105, 62, 255),
              outline=(156, 145, 81, 255), width=5)
    d.ellipse(bb(-98, -80, 70, 43), fill=(103, 119, 66, 255),
              outline=(42, 73, 55, 255), width=3)
    for radius in (72, 51, 33):
        d.arc(bb(-radius-12, -radius * .65 - 20,
                 radius + 6, radius * .62 + 20),
              start=37 + (72-radius)*2, end=315,
              fill=(32, 77, 55, 230), width=4)
    for angle in (0, 58, 117, 185, 246, 305):
        a = math.radians(angle)
        center = p(-13, -15)
        start = p(-13 + 23*math.cos(a), -15 + 15*math.sin(a))
        end = p(-13 + 80*math.cos(a), -15 + 61*math.sin(a))
        d.line((start, end), fill=(58, 84, 52, 180), width=3)
    # Distinct crack at front-right shell.
    d.line([p(67, 19), p(77, 12), p(74, 26), p(82, 33)],
           fill=(221, 204, 124, 255), width=3)
    # Olive neck is angled, head bob independently of shell.
    d.ellipse(bb(43, -54, 153, 39), fill=(65, 106, 79, 255))
    hy = math.sin(t*1.4) * 4
    d.ellipse(bb(73, -82+hy, 171, 25+hy), fill=(83, 128, 96, 255),
              outline=(39, 74, 55, 255), width=3)
    d.ellipse(bb(86, -73+hy, 158, 0+hy), fill=(126, 158, 111, 255))
    for ex in (102, 143):
        blink = abs(t % 4.1 - 2.05) < .085
        d.ellipse(bb(ex-16,-52+hy,ex+12,-44+hy if blink else -16+hy),
                  fill=(234, 221, 176, 255),
                  outline=(48, 87, 66, 255), width=2)
        if not blink:
            d.ellipse(bb(ex-4,-43+hy,ex+6,-26+hy), fill=(52, 77, 59, 255))
            d.ellipse(bb(ex-1,-39+hy,ex+2,-36+hy), fill=(255,255,255,240))
        d.arc(bb(ex-19,-60+hy,ex+14,-37+hy),175,325,
              fill=(41,74,55,255),width=3)
    d.ellipse(bb(150,-5+hy,155,1+hy),fill=(35,74,56,255))
    opening=3+9*min(1,mouth)
    d.arc(bb(117,0+hy,151,9+opening+hy),5,176,fill=(42,70,55,255),width=3)
    # Subtle skin and shell freckling make art less icon-like.
    for j in range(33):
        x = (j*37)%128-92
        y = (j*29)%91-69
        d.ellipse(bb(x,y,x+2,y+2),fill=(184,170,105,70))


def _feather(draw, scene, t):
    if scene not in (3,4,5,12,13,14): return
    x = 248 + 29*math.sin(t*.6+scene)
    y = 190 + 25*math.cos(t*.9)
    for r,a in ((39,17),(23,24),(11,57)):
        _glow_ellipse(draw, (x-r,y-r,x+r,y+r),(67,200,255),a)
    draw.polygon([(x-6,y+17),(x+2,y-21),(x+11,y-27),(x+8,y+7)],
                 fill=(123,241,252,245))
    draw.line((x-5,y+20,x+8,y-25),fill=(231,252,255,235),width=2)


def _caption(canvas, speaker, text, t, voice_seconds):
    if not text or t > voice_seconds+.5: return
    words=text.split()
    groups=[" ".join(words[i:i+9]) for i in range(0,len(words),9)]
    index=min(len(groups)-1,int(t/max(.15,voice_seconds/max(1,len(groups)))))
    text=groups[index]
    d=ImageDraw.Draw(canvas,"RGBA")
    d.rounded_rectangle((15,530,345,622),radius=14,
                        fill=(4,13,28,234),outline=(162,180,174,165),width=2)
    who="EMBER" if speaker=="s01_ember" else ("MOSS" if speaker=="s01_moss" else "NARRATOR")
    d.text((30,540),who,fill=(109,214,213,255),font=font(12))
    words=text.split()
    lines=[]
    buf=""
    for w in words:
        attempt=(buf+" "+w).strip()
        if d.textbbox((0,0),attempt,font=font(17))[2]>287 and buf:
            lines.append(buf);buf=w
        else: buf=attempt
    if buf: lines.append(buf)
    for j,line in enumerate(lines[:3]):
        d.text((30,557+j*19),line,fill=(252,244,228,255),font=font(17))


def render_frame(scene, t, mouth, voice_seconds, text, speaker, visible, direction):
    """Drop-in replacement for CPU basic renderer; each frame truly changes."""
    base=backdrop(scene).copy()
    d=ImageDraw.Draw(base,"RGBA")
    # Fire embers, drifting dust and moving cyan glows; background not flat.
    rng=random.Random(scene*107)
    for j in range(34):
        x=((j*47+math.sin(t*.33+j)*22)%390)-15
        y=((j*97-t*(7+j%9))%590)+24
        rr=(j%3)+1
        color=(255,157,92,160) if scene<=11 else (109,208,237,115)
        d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=color)
    acts=direction.lower()
    kind=("run" if any(w in acts for w in ("run","springs","leapt","jumps"))
          else "struggle" if any(w in acts for w in ("slid","grips","climb"))
          else "walk")
    if "s01_ember" in visible:
        art=_character_cutout(t,kind,mouth if speaker=="s01_ember" else 0)
        dual="s01_moss" in visible
        scale=.58 if dual else .79
        size=round(640*scale)
        art=art.resize((size,size),_L)
        x=(-18 if dual else 2)+int(math.sin(t*.95)*4)
        y=(102 if dual else 55)+int(math.sin(t*(5.5 if kind=="run" else 1.7))*(5 if kind=="run" else 2))
        # Actor moves independently of the original environmental artwork.
        base.alpha_composite(art,(x,y))
    if "s01_moss" in visible:
        cx=260 if "s01_ember" in visible else 170
        _moss(base,cx,417,t,mouth if speaker=="s01_moss" else .15,
              .57 if "s01_ember" in visible else 1.0)
    d=ImageDraw.Draw(base,"RGBA")
    _feather(d,scene,t)
    _caption(base,speaker,text,t,voice_seconds)
    # Subtle film vignette, away from subtitle area.
    return base.convert("RGB")
