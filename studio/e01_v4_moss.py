"""Premium generated Moss reference candidate, source hashed and CPU 2.5D-rigged.

This visual candidate retains elderly tortoise/spiral shell/crack silhouette but
adds spectacles and white facial fur, so new design identity approval is pending.
No paid inference, network calls or public posting.
"""
import base64
import hashlib
import io
import math
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter
from studio.restore import ROOT

SOURCE = ROOT / "assets/v4/moss_generated_candidate.webp.b64"
SOURCE_SHA256 = "72732a382a968e4b68dd36398715de9eebe6e5ce1843db75ede47134fc39db52"
SIZE = (288, 201)
RESAMPLE = Image.Resampling.LANCZOS


def shape(points, blur=2):
    mask=Image.new("L",SIZE)
    ImageDraw.Draw(mask).polygon(points,fill=255)
    return mask.filter(ImageFilter.GaussianBlur(blur))


@lru_cache(maxsize=1)
def parts():
    encoded=SOURCE.read_text(encoding="utf-8").strip()
    raw=base64.b64decode(encoded,validate=True)
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:
        raise RuntimeError("MOSS_V4_REFERENCE_HASH_CHANGED_OR_CORRUPT")
    source=Image.open(io.BytesIO(raw)).convert("RGBA")
    if source.size!=SIZE:
        raise RuntimeError("MOSS_V4_REFERENCE_DIMENSIONS_CHANGED")
    alpha=source.getchannel("A")
    head=ImageChops.multiply(alpha,shape([
        (188,2),(220,0),(287,0),(287,118),(266,126),
        (240,121),(209,117),(179,106)
    ],4))
    hind=ImageChops.multiply(alpha,shape([
        (0,116),(55,115),(76,148),(71,201),(0,201)
    ],5))
    fore=ImageChops.multiply(alpha,shape([
        (185,121),(254,123),(287,154),(287,201),(190,201)
    ],5))
    front=ImageChops.multiply(alpha,shape([
        (79,119),(157,120),(164,201),(76,201)
    ],5))
    # Foreground segments subtract from the back layer. No fake image duplications.
    body=alpha
    for mask in (head,hind,fore,front):
        body=ImageChops.subtract(body,mask)
    def layer(m):
        obj=source.copy()
        obj.putalpha(m)
        return obj
    return {
        "body":layer(body),
        "hind":layer(hind),
        "front":layer(front),
        "fore":layer(fore),
        "head":layer(head),
        "original":source,
    }


def sprite(t,mouth):
    p=parts()
    image=Image.new("RGBA",SIZE)
    phase=math.sin(t*2.15)
    # Small coherent movements: shell weight, foot gait and separate head.
    image.alpha_composite(p["hind"].rotate(3*phase,
        center=(40,132),resample=Image.Resampling.BICUBIC))
    image.alpha_composite(p["body"])
    image.alpha_composite(p["front"].rotate(-2.5*phase,
        center=(108,128),resample=Image.Resampling.BICUBIC))
    image.alpha_composite(p["fore"].rotate(2.7*phase,
        center=(220,129),resample=Image.Resampling.BICUBIC))
    head=p["head"].rotate(1.5*math.sin(t*1.35),
        center=(205,114),resample=Image.Resampling.BICUBIC)
    image.alpha_composite(head)
    # Tiny texture-based jaw movement only while speaking. Not phoneme sync.
    if mouth>.22:
        x1,y1,x2,y2=245,57,288,101
        patch=p["head"].crop((x1,y1,x2,y2))
        h=44 + round(3*min(1.0,mouth))
        patch=patch.resize((43,h),RESAMPLE)
        image.alpha_composite(patch,(x1,y1))
    return image


def draw_moss(canvas,x,y,t,mouth,scale=1):
    from studio.cpu_motion_engine import W,H
    if canvas.size!=(W,H):
        raise ValueError("Unexpected output size")
    actual = .64 if scale<.8 else 1.09
    art=sprite(t,mouth)
    art=ImageEnhance.Contrast(art).enhance(1.05)
    art=art.resize((round(SIZE[0]*actual),round(SIZE[1]*actual)),RESAMPLE)
    px=round(x-art.width*.5)
    py=round(y-art.height+math.sin(t*2)*1.6)
    shadow=Image.new("RGBA",(W,H))
    d=ImageDraw.Draw(shadow,"RGBA")
    d.ellipse((x-art.width*.42,y-8,x+art.width*.43,y+13),
              fill=(2,8,17,138))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10)))
    canvas.alpha_composite(art,(px,py))
