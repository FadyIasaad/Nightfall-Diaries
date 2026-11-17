"""Nightfall E01 V4: isolated CPU cinematic-painterly scene compositor.

Real articulated 2.5D source-locked Ember + enhanced V3 Moss layers,
scene-specific textured atmosphere, physically motivated colors and subtle
minimal subtitles. No generative-video claim, paid API, posting or source edits.
"""
from functools import lru_cache
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from studio import e01_v2_art_direction as old
from studio import e01_v4_moss as moss
from studio.painterly_reference_actor_v2 import puppet
from studio.cpu_motion_engine import W, H, font

SETS = old.SETS
RESAMPLE = Image.Resampling.LANCZOS

# Deliberate editorial compositions rather than a single centered pose.
# x,y indicate the top left of each cropped character *on a 360x640 frame*.
STAGING = {
    1: ("fire-wide", 0.72, 0.00, 82),
    2: ("fire-tight", 0.91, -53.0, 43),
    3: ("discovery", 0.73, -23.0, 101),
    4: ("reach", 0.82, -37.0, 68),
    5: ("face-close", 0.92, -48.0, 54),
    6: ("moss-arrival", 0.54, -33.0, 129),
    7: ("dialogue", 0.53, -26.0, 114),
    8: ("ledge-wide", 0.51, -39.0, 143),
    9: ("fall", 0.68, -45.0, 118),
    10: ("roots", 0.67, -57.0, 161),
    11: ("rescue", 0.49, -28.0, 121),
    12: ("corridor", 0.72, -30.0, 92),
    13: ("hope", 0.75, -44.0, 94),
    14: ("mystery-wide", 0.51, -23.0, 132),
}
assert set(STAGING) == set(SETS)


def _ellipse(d, xy, fill):
    d.ellipse(tuple(round(v) for v in xy), fill=fill)


@lru_cache(maxsize=14)
def painted_set(scene):
    """Texture, fog, rich lighting and distinct foreground geology over V2 sets."""
    if scene not in SETS:
        raise ValueError("Unknown canonical E01 scene")
    im = old.story_set(scene).convert("RGB")
    rng = np.random.default_rng(4271 + scene)
    # Coherent multi-scale texture replaces the overly smooth flat planes.
    tonal = np.zeros((H, W), dtype=np.float32)
    for nx, ny, strength in ((9, 15, 12), (26, 46, 9), (74, 120, 4)):
        values = rng.normal(0, 1, (ny, nx))
        scaled = Image.fromarray(np.uint8(np.clip(values * 27 + 127, 0, 255)))
        scaled = scaled.resize((W, H), Image.Resampling.BICUBIC)
        tonal += (np.asarray(scaled, dtype=np.float32) - 127) / 27 * strength
    pix = np.array(im, dtype=np.float32)
    y = np.arange(H, dtype=np.float32)[:, None]
    x = np.arange(W, dtype=np.float32)[None, :]
    # Controlled edge darkening and believable key-light direction.
    vignette = ((x - 175) / 220) ** 2 + ((y - 290) / 420) ** 2
    lighting = np.clip(1.12 - 0.16 * vignette, .71, 1.1)
    pix = np.clip(pix * lighting[..., None] + tonal[..., None], 0, 255)
    im = Image.fromarray(pix.astype("uint8"), "RGB").convert("RGBA")
    haze = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(haze, "RGBA")
    r = random.Random(4122 + scene * 19)
    cold = scene in (3, 4, 5, 12, 13, 14)
    for j in range(18):
        xx = r.randint(-75, W + 70)
        yy = r.randint(110, 545)
        radius = r.randint(55, 155)
        tint = (60, 160, 188, r.randrange(7, 25)) if cold else (228, 108, 67, r.randrange(7, 28))
        _ellipse(d, (xx-radius, yy-radius//2, xx+radius, yy+radius//2), tint)
    im = Image.alpha_composite(im, haze.filter(ImageFilter.GaussianBlur(29)))
    # Distinct blurred fore/midground branches give separation from the subject.
    geology = Image.new("RGBA", (W, H))
    g = ImageDraw.Draw(geology, "RGBA")
    if scene in (8, 9, 10, 11):
        for i in range(19):
            xx = r.randint(-80, W+80)
            yy = r.randint(440, 610)
            rad = r.randint(3, 22)
            _ellipse(g, (xx-rad, yy-rad//3, xx+rad, yy+rad//2),
                     (95, 85, 77, r.randint(25, 110)))
    if scene in (1, 2, 6, 7):
        for i in range(9):
            xx = r.randint(-30, W + 30)
            yy = r.randint(135, 460)
            height = r.randint(55, 150)
            col = (19, 22, 25, r.randint(45, 110))
            g.line((xx, yy, xx-5, yy-height), fill=col, width=r.randrange(2, 8))
    im = Image.alpha_composite(im, geology.filter(ImageFilter.GaussianBlur(2)))
    return im


def _place_ember(canvas, scene, t, mouth, speaker, visible):
    if "s01_ember" not in visible:
        return
    _, scale, x, y = STAGING[scene]
    duo = "s01_moss" in visible
    if duo:
        scale = min(scale, .53)
    action = ("run" if scene in (1, 2, 9, 10)
              else "struggle" if scene in (8, 11) else "walk")
    layer = puppet(t, mouth if speaker == "s01_ember" else 0.05, action)
    size = (round(512*scale), round(640*scale))
    layer = layer.resize(size, RESAMPLE)
    # Small grounded motion. Avoid an actor floating up/down off a flat floor.
    xx = round(x + 4 * math.sin(t * (1.1 if action == "walk" else 3.8)))
    yy = round(y + (1.4 if action == "walk" else 3.0) * math.sin(t * 4))
    if scene in (9, 10):
        yy += round(7 * math.sin(t*0.6))
    under = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(under, "RGBA")
    floor = yy + size[1] * .84
    if scene not in (9, 10):
        _ellipse(d, (xx+65*scale, floor-10, xx+440*scale, floor+9),
                 (1, 9, 17, 125))
    canvas.alpha_composite(under.filter(ImageFilter.GaussianBlur(10)))
    # Scene light spills onto the original fox without repainting the locked ref.
    light = Image.new("RGBA", size, (243, 117, 36, 12)
                      if scene in (1, 2, 6, 7, 8, 9, 10, 11)
                      else (70, 177, 205, 10))
    light.putalpha(Image.composite(light.getchannel("A"),
                                   Image.new("L", size, 0), layer.getchannel("A")))
    layer = Image.alpha_composite(layer, light)
    canvas.alpha_composite(layer, (xx, yy))


def _place_moss(canvas, scene, t, mouth, speaker, visible):
    if "s01_moss" not in visible:
        return
    dual = "s01_ember" in visible
    # SHA-locked generated source-textured head, shell and independently moving feet.
    # This is a new REVIEW candidate, not automatic canon/style approval.
    x = 268 if dual else 181
    y = 488 if dual else 508
    if scene == 11:
        y = 468
    moss.draw_moss(canvas,x,y,t,
                   mouth if speaker == "s01_moss" else .04,
                   scale=.62 if dual else 1.0)


def _feather(canvas, scene, t):
    if scene not in (3, 4, 5, 12, 13, 14):
        return
    x = (314 if scene in (3, 4, 5) else 283) + 9*math.sin(t*.7)
    y = (336 if scene in (3, 4, 5) else 295) + 10*math.cos(t*.65)
    glows = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(glows, "RGBA")
    for radius, alpha in ((83, 12), (56, 20), (30, 32)):
        _ellipse(d, (x-radius, y-radius, x+radius, y+radius),
                 (25, 198, 250, alpha))
    canvas.alpha_composite(glows.filter(ImageFilter.GaussianBlur(12)))
    plume = Image.new("RGBA", (W, H))
    p = ImageDraw.Draw(plume, "RGBA")
    # Slim curved magic feather instead of a giant blue on-screen sticker.
    spine = [(x-7+2*math.sin(q*.3+t), y+19-q*2.2) for q in range(23)]
    for side in (-1, 1):
        for i in range(2, 19):
            px, py = spine[i]
            spread = (1.0-(i/22)**1.8)*11
            p.line((px,py, px+side*spread, py-(4+i%3)), fill=(91, 231, 250, 170), width=1)
    p.line(spine, fill=(221, 252, 252, 235), width=2, joint="curve")
    canvas.alpha_composite(plume.filter(ImageFilter.GaussianBlur(.45)))


def _atmosphere(canvas, scene, t):
    d = ImageDraw.Draw(canvas, "RGBA")
    r = random.Random(1373+scene)
    cold = scene in (3, 4, 5, 12, 13, 14)
    for j in range(43):
        xx=(r.randint(0, W) + t * (3+j%7)) % W
        yy=(r.randint(0, H) - t * (6+j%8)) % H
        rad = 1 if j%4 else 2
        _ellipse(d,(xx-rad,yy-rad,xx+rad,yy+rad),
                 (120, 214, 234, 74) if cold else (255, 174, 80, 105))
    # Variable translucent atmospheric ribbons, no opaque rectangular smears.
    mist = Image.new("RGBA", (W, H))
    md=ImageDraw.Draw(mist, "RGBA")
    for j in range(3):
        sx=60+j*145 + 17*math.sin(t*.24+j)
        sy=170+j*134 - 6*math.cos(t*.44+j)
        _ellipse(md, (sx-130,sy-34,sx+130,sy+34),
                 (91, 156, 158, 12) if cold else (142, 114, 103, 10))
    canvas.alpha_composite(mist.filter(ImageFilter.GaussianBlur(23)))


def _subtitle(canvas, speaker, words, t, voice_sec):
    if not words or t > voice_sec + .35:
        return
    chunks = words.split()
    groups = [" ".join(chunks[i:i+8]) for i in range(0,len(chunks),8)]
    if not groups:
        return
    idx = min(len(groups)-1, int(t / max(.2, voice_sec/max(1,len(groups)))))
    label = {"s01_ember":"EMBER","s01_moss":"MOSS"}.get(speaker,"NARRATOR")
    d = ImageDraw.Draw(canvas, "RGBA")
    # Minimal dark gradient in the safe bottom zone. No bulky game-style card.
    overlay = Image.new("RGBA", (W,H))
    a = ImageDraw.Draw(overlay, "RGBA")
    for yy in range(524,640):
        alpha = int(190*(yy-524)/116)
        a.line((0,yy,W,yy),fill=(5,11,23,alpha))
    canvas.alpha_composite(overlay)
    d = ImageDraw.Draw(canvas, "RGBA")
    fsmall=font(12)
    ftext=font(19)
    d.text((23,555),label,fill=(105,220,226,245),font=fsmall,stroke_width=1,stroke_fill=(5,13,20,200))
    msg=groups[idx]
    lines=[]
    line=""
    for word in msg.split():
        option=(line+" "+word).strip()
        if d.textbbox((0,0),option,font=ftext)[2] > 310 and line:
            lines.append(line);line=word
        else:
            line=option
    if line:lines.append(line)
    for i,txt in enumerate(lines[:2]):
        d.text((23,576+i*22),txt,fill=(255,251,240,255),
               font=ftext,stroke_width=2,stroke_fill=(3,9,17,245))


def frame(scene,t,mouth,voice_sec,words,speaker,visible,direction):
    canvas = painted_set(scene).copy()
    _place_ember(canvas,scene,t,mouth,speaker,visible)
    _place_moss(canvas,scene,t,mouth,speaker,visible)
    _feather(canvas,scene,t)
    _atmosphere(canvas,scene,t)
    _subtitle(canvas,speaker,words,t,voice_sec)
    return canvas.convert("RGB")
