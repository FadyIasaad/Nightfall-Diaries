"""Zero-cost, browser-runner-friendly illustrated fantasy frames.

This renderer draws *original* stylised atmospheric fantasy graphics locally.
It deliberately does not claim to be photorealistic AI image generation.
Creators can replace any frame with their own/licensed illustration in
assets/scene_overrides/<episode_id>/<shot_id>.png, without changing scripts.
"""
import hashlib
import math
import random
import re
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from .util import ROOT

W,H=720,1280

def seed_for(*items):
    return int(hashlib.sha256('|'.join(map(str,items)).encode()).hexdigest()[:12],16)

def ft(size=30,bold=False):
    paths=[
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf',
    ] if bold else [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf',
    ]
    for p in paths:
        try:return ImageFont.truetype(p,size)
        except OSError:pass
    return ImageFont.load_default()

def _glow(im,x,y,r,color,opacity=180):
    layer=Image.new('RGBA', (W,H));d=ImageDraw.Draw(layer)
    for i in range(8,0,-1):
        rr=int(r*i/8)
        d.ellipse((x-rr,y-rr,x+rr,y+rr),fill=(*color,int(opacity*(1-(i/9))**2/7)))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(23)))

def _gradient(theme,variant,seed):
    # Painted sky, subtle noise, atmospheric ground gradient, purple/orange lights.
    rng=np.random.default_rng(seed)
    if theme=='fox':
        top=(6,17,38);bottom=(40,38,53) if variant!='fire' else (102,47,30)
    else:
        top=(10,15,35);bottom=(43,25,67)
    y=np.linspace(0,1,H,dtype=np.float32)[:,None,None]
    ys=np.clip(y**.72,0,1)
    color=np.array(top,dtype=np.float32)[None,None,:]*(1-ys)+np.array(bottom,dtype=np.float32)[None,None,:]*ys
    noise=rng.normal(0,5,(H,W,1)).astype(np.float32)
    horiz=np.sin(np.arange(W,dtype=np.float32)[None,:,None]/170)*3
    raw=np.clip(color+noise+horiz,0,255).astype('uint8')
    return Image.fromarray(raw,'RGB').convert('RGBA')

def _landscape(im,theme,variant,seed):
    rng=random.Random(seed)
    d=ImageDraw.Draw(im,'RGBA')
    # Far moon / magical sky light source
    moonx=505 if seed%2 else 160
    moony=210+seed%90
    _glow(im,moonx,moony,230,(104,183,246) if theme=='fox' else (168,103,250),200)
    d=ImageDraw.Draw(im,'RGBA')
    d.ellipse((moonx-66,moony-66,moonx+66,moony+66),fill=(175,208,226,76),outline=(201,232,243,80),width=3)
    for idx in range(3):
        baseline=570+idx*112
        pts=[(0,H),(0,baseline)]
        for i in range(16):
            x=i*50
            yy=baseline+rng.randint(-115,95)
            pts.append((x,yy))
        pts.extend([(W,H)])
        color=((36,53,74,140),(21,39,56,205),(14,29,43,242))[idx] if theme=='fox' else ((63,52,103,145),(37,39,75,195),(15,24,45,250))[idx]
        d.polygon(pts,fill=color)
    if theme=='fox':
        # Hundreds of tree-branch lines to create parallax-like depth and atmosphere.
        for layer in range(3):
            n=17+layer*4
            for i in range(n):
                x=rng.randint(-90,W+90);w=rng.randint(12,24)+layer*8
                treetop=rng.randint(270,670)+layer*85
                trunk=(9+layer*2,18+layer*4,26+layer*4,125+layer*55)
                d.polygon([(x-w,H),(x-w//2,treetop),(x+w//2,treetop),(x+w,H)],fill=trunk)
                for b in range(3):
                    yy=treetop+50+b*120
                    side=-1 if (i+b)%2 else 1
                    endx=x+side*rng.randint(46,115)
                    d.line([(x,yy+35),(endx,yy-rng.randint(65,125))],fill=trunk,width=max(3,w//5))
        if variant=='fire':
            _glow(im,390,830,360,(237,86,36),230)
        else:
            _glow(im,360,850,300,(13,147,181),80)
    else:
        # Arcane towers for the human fantasy series.
        for i in range(12):
            x=i*72+rng.randint(-30,25)
            height=rng.randint(250,580)
            top=920-height
            d.polygon([(x-36,980),(x-28,top),(x,top-85),(x+28,top),(x+36,980)],fill=(10,15,35,230))
            d.line([(x,top-85),(x,top-118)],fill=(95,125,189,115),width=3)
            for window in range(4):
                yy=top+85+window*70
                if yy<850:d.ellipse((x-4,yy-8,x+4,yy+8),fill=(160,144,242,130))
        _glow(im,385,830,330,(106,68,190),125)
        # Clock circles / magic geometry
        for rad in (145,178,190):
            d.arc((360-rad,420-rad,360+rad,420+rad),15,310,fill=(162,176,234,35),width=3)
    # Ground and drifting mist/particles
    d=ImageDraw.Draw(im,'RGBA')
    d.polygon([(0,945),(W,900),(W,H),(0,H)],fill=(10,19,30,232))
    for i in range(135):
        x=rng.randint(0,W);y=rng.randint(100,1150);r=rng.choice([1,1,2,3])
        if variant=='fire':c=(255,151,56,rng.randint(70,160))
        elif theme=='fox':c=(126,209,230,rng.randint(40,120))
        else:c=(179,165,241,rng.randint(40,140))
        d.ellipse((x-r,y-r,x+r,y+r),fill=c)
    # Fog rendered as blurred translucent horizontal painterly pools
    mist=Image.new('RGBA',(W,H));md=ImageDraw.Draw(mist,'RGBA')
    for i in range(18):
        y=rng.randint(690,1100);x=rng.randint(-120,500)
        md.ellipse((x,y,x+rng.randint(320,690),y+rng.randint(35,100)),fill=(144,169,194,rng.randint(10,30)))
    im.alpha_composite(mist.filter(ImageFilter.GaussianBlur(28)))

def _fox_character(im,character,seed,focus='hero'):
    # Shadow-puppet / illustrated storybook fox with recognisable glowing eyes and teal scarf.
    d=ImageDraw.Draw(im,'RGBA')
    cx=350+(seed%61-30);cy=690
    s=1.08 if focus=='hero' else 0.9
    def pt(x,y):return int(cx+(x-350)*s),int(cy+(y-690)*s)
    def poly(points,fill,outline=None,width=1):
        d.polygon([pt(x,y) for x,y in points],fill=fill)
        if outline:d.line([pt(x,y) for x,y in points+[points[0]]],fill=outline,width=width,joint='curve')
    # Tail behind torso
    poly([(452,810),(555,760),(560,650),(535,700),(495,718),(435,736)],(119,56,45,255),(201,111,75,210),4)
    poly([(540,700),(560,650),(556,737),(525,758)],(219,180,139,235))
    # Body and furry cheeks
    poly([(300,740),(411,744),(480,960),(433,1055),(258,1055),(233,944)],(118,57,44,255),(239,147,102,140),4)
    # ears behind forehead
    poly([(242,560),(249,386),(334,501),(357,558)],(124,60,47,255),(231,171,143,130),5)
    poly([(363,545),(452,395),(464,573)],(113,54,48,255),(246,186,143,130),4)
    poly([(251,416),(260,515),(286,523)],(244,220,197,255))  # white LEFT ear tip
    poly([(443,424),(429,519),(401,527)],(188,113,99,230))
    # head and layered forehead fur
    poly([(240,543),(288,501),(354,497),(423,521),(474,611),(450,698),(387,748),(297,735),(227,671)],(157,76,53,255),(242,176,127,210),5)
    poly([(270,575),(332,555),(350,610),(366,559),(417,577),(394,670),(352,731),(299,681)],(193,102,66,225))
    # cream lower cheek and muzzle
    poly([(246,668),(301,682),(353,716),(398,680),(458,671),(398,748),(305,750)],(232,204,160,230))
    poly([(326,690),(352,681),(383,692),(365,715),(342,714)],(37,37,43,255))
    # glowing amber eyes with darker outlines
    for ex in [294,413]:
        _glow(im,pt(ex,633)[0],pt(ex,633)[1],58,(254,165,49),125)
    d=ImageDraw.Draw(im,'RGBA')
    for ex in [294,413]:
        px,py=pt(ex,633)
        d.ellipse((px-14,py-8,px+15,py+9),fill=(246,185,71,230))
        d.ellipse((px-3,py-8,px+5,py+8),fill=(15,26,31,255))
        d.ellipse((px+5,py-6,px+8,py-3),fill=(255,255,255,245))
    # scarf teal with gold star (signature continuity)
    poly([(270,770),(414,756),(443,804),(379,832),(283,811)],(22,137,153,255),(112,211,216,165),4)
    poly([(402,798),(446,821),(420,961),(387,931)],(15,116,135,255))
    d=ImageDraw.Draw(im,'RGBA');sx,sy=pt(361,799)
    points=[]
    for i in range(10):
        angle=-math.pi/2+i*math.pi/5
        r=11 if i%2==0 else 5
        points.append((sx+math.cos(angle)*r,sy+math.sin(angle)*r))
    d.polygon(points,fill=(254,199,82,240))
    # glints / fur edge highlights
    d.line([pt(247,593),pt(229,668),pt(282,735)],fill=(255,185,120,95),width=3)

def _human_character(im,seed,character=None):
    """Readable, *identity-stable* stylized human designs for the mystery cast."""
    ch=character or {};cid=ch.get('id','')
    d=ImageDraw.Draw(im,'RGBA');cx=350
    noah='noah' in cid or ('cast1' in cid)
    mira='mira' in cid or ('cast2' in cid)
    vale='vale' in cid or ('cast3' in cid)
    keeper='clockkeeper' in cid or ('cast4' in cid)
    if noah: skin=(144,96,66,255);hair=(28,29,32,255);cloth=(43,88,168,255);eyes=(46,37,31,255)
    elif mira:skin=(169,121,95,255);hair=(93,47,37,255);cloth=(212,172,58,255);eyes=(101,84,42,255)
    elif vale:skin=(95,62,48,255);hair=(93,89,91,255);cloth=(32,100,89,255);eyes=(37,31,29,255)
    elif keeper:skin=(197,167,136,255);hair=(45,48,52,255);cloth=(172,143,75,255);eyes=(37,38,44,255)
    else:skin=(157,119,98,255);hair=(38,34,47,255);cloth=(57,64,112,255);eyes=(65,54,54,255)
    # Distinctive outerwear and short/long silhouette; signature detail per cast.
    d.polygon([(cx-135,813),(cx+135,813),(cx+210,1120),(cx-197,1120)],fill=cloth)
    d.polygon([(cx-100,808),(cx-95,640),(cx+95,640),(cx+110,807)],fill=skin)
    d.ellipse((cx-108,492,cx+108,772),fill=skin)
    if mira:
        d.polygon([(cx-115,592),(cx-130,498),(cx-92,447),(cx+90,445),(cx+126,545),(cx+97,635),(cx+84,518),(cx-88,527)],fill=hair)
        d.ellipse((cx+88,504,cx+110,531),fill=(225,132,61,255)) # copper clip right
        d.polygon([(cx-80,804),(cx+80,804),(cx+61,1080),(cx-65,1080)],fill=(119,88,178,255))
    elif vale:
        d.ellipse((cx+57,430,cx+114,493),fill=hair) # low bun
        d.polygon([(cx-117,594),(cx-105,505),(cx-50,461),(cx+76,465),(cx+109,540),(cx+93,564)],fill=hair)
        d.polygon([(cx-70,828),(cx+70,828),(cx+63,1100),(cx-53,1100)],fill=(228,225,203,255))
    elif keeper:
        d.polygon([(cx-110,586),(cx-88,449),(cx+75,453),(cx+117,565)],fill=hair)
        d.line([(cx-77,480),(cx-91,565)],fill=(210,208,200,255),width=13) # silver streak left temple
        d.line([(cx+18,814),(cx+14,1100)],fill=(77,58,42,205),width=9)
    else:
        d.polygon([(cx-112,594),(cx-114,493),(cx-54,438),(cx+35,460),(cx+87,447),(cx+124,520),(cx+100,597),(cx+67,515),(cx+19,509),(cx-22,538),(cx-85,514)],fill=hair)
        if noah:
            for ox,oy in [(-100,480),(-68,460),(-35,452),(0,457),(28,469),(55,454),(81,485)]:
                d.ellipse((cx+ox-19,oy-12,cx+ox+19,oy+23),fill=hair)
            # white lightning seam on LEFT sleeve, always
            d.line([(cx-126,873),(cx-101,916),(cx-124,941),(cx-87,973)],fill=(227,242,254,255),width=7)
    for ex in (cx-41,cx+44):
        d.ellipse((ex-10,621,ex+10,634),fill=eyes)
        d.ellipse((ex+2,622,ex+5,625),fill=(241,239,230,210))
    d.arc((cx-20,688,cx+20,704),0,165,fill=(89,53,51,235),width=2)
    if vale or keeper:
        d.ellipse((cx-77,604,cx-2,662),outline=(219,198,156,255),width=4)
        d.ellipse((cx+4,604,cx+78,662),outline=(219,198,156,255),width=4)
        d.line([(cx-2,624),(cx+4,624)],fill=(219,198,156,255),width=4)
    if keeper:
        _glow(im,cx,906,95,(249,193,77),130)
        d=ImageDraw.Draw(im,'RGBA');d.ellipse((cx-33,878,cx+33,947),fill=(181,141,63,255),outline=(246,212,115,255),width=5)
        for k in range(12):
            a=2*math.pi*k/12
            x=cx+int(23*math.cos(a));y=911+int(23*math.sin(a))
            d.ellipse((x-2,y-2,x+2,y+2),fill=(248,238,188,255))
    elif noah:
        _glow(im,cx,907,95,(119,204,255),140)
        d=ImageDraw.Draw(im,'RGBA');d.ellipse((cx-25,879,cx+25,933),fill=(44,121,206,255),outline=(212,207,143,235),width=4)
    elif mira:
        d=ImageDraw.Draw(im,'RGBA');d.line([(cx-40,845),(cx+42,965)],fill=(36,50,84,255),width=10)
    else:
        d=ImageDraw.Draw(im,'RGBA');d.line([(cx-88,796),(cx+89,796)],fill=(211,222,197,255),width=6)

def _other_animal(im,character,seed):
    # Stylized silhouettes for the tortoise, owl, and wolf; never use generic labeled portraits.
    name=character.get('name','').lower(); d=ImageDraw.Draw(im,'RGBA')
    if 'moss' in name:
        d.ellipse((168,642,570,1020),fill=(74,98,82,255),outline=(171,183,132,180),width=7)
        for r in (0,1,2):d.arc((185+r*33,660+r*35,548-r*33,970-r*35),40,310,fill=(180,167,117,110),width=4)
        d.ellipse((255,534,444,781),fill=(116,144,99,255));d.ellipse((295,631,318,649),fill=(19,34,33,255));d.ellipse((383,630,407,649),fill=(19,34,33,255))
    elif 'luma' in name:
        d.ellipse((179,490,548,976),fill=(199,204,190,235))
        d.polygon([(180,710),(66,1010),(279,947)],fill=(70,102,128,250))
        d.polygon([(542,708),(645,1010),(449,951)],fill=(72,101,129,250))
        for x in (283,425):d.ellipse((x-51,583,x+51,687),fill=(234,232,200,255));d.ellipse((x-18,622,x+18,658),fill=(207,162,55,255))
        d.polygon([(347,684),(375,684),(361,727)],fill=(190,146,60,255))
    else:
        # Ash: gray wolf pup with slanted icy eyes and a notched ear.
        d.polygon([(183,751),(269,408),(344,558),(420,385),(559,760),(465,950),(253,960)],fill=(83,108,121,255),outline=(170,194,205,220),width=5)
        d.polygon([(307,657),(407,657),(357,761)],fill=(178,190,184,255))
        for x in (290,417):d.ellipse((x-22,632,x+22,655),fill=(137,205,249,255))
        d.polygon([(341,707),(372,702),(359,722)],fill=(26,32,40,255))
        d.line([(390,607),(436,580)],fill=(218,218,232,180),width=4)

def _feather(im,variant):
    cx,cy=(565,680) if variant!='cliffhanger' else (530,530)
    _glow(im,cx,cy,145,(81,215,245),215)
    d=ImageDraw.Draw(im,'RGBA')
    d.polygon([(cx-31,cy+63),(cx-18,cy-70),(cx+16,cy-105),(cx+32,cy-56),(cx+25,cy+37),(cx,cy+97)],fill=(62,206,243,210),outline=(170,240,253,220),width=3)
    d.line([(cx-14,cy+89),(cx+10,cy-84)],fill=(232,250,255,210),width=3)

def _overlay(im,manifest,ep,shot,idx,total,variant):
    # Platform-safe typography: don't mimic TikTok buttons or logos.
    d=ImageDraw.Draw(im,'RGBA')
    title=manifest['title'];epi=ep['episode'];maxeps=manifest['episode_count']
    d.rounded_rectangle((24,45,320,96),radius=20,fill=(4,12,23,175),outline=(180,191,210,70),width=2)
    d.text((45,56),'NIGHTFALL DIARIES',font=ft(22,True),fill=(235,228,215,255),stroke_width=0)
    # Thin episode micro-mark at top-right
    d.text((W-35,58),f'EP {epi:02d}/{maxeps:02d}',font=ft(24,True),fill=(239,217,182,255),anchor='ra')
    # Subtitle text centered and stroked, framed over image at safe height.
    words=shot.get('subtitle') or shot['text']
    lines=textwrap.wrap(words,width=23,break_long_words=False,break_on_hyphens=False)
    if len(lines)>3:lines=textwrap.wrap(words,width=31,break_long_words=False)
    if len(lines)>3:lines=lines[:3]
    text='\n'.join(lines)
    fontsize=48 if max(len(x) for x in lines)<27 else 41
    f=ft(fontsize,True)
    y=950-(len(lines)-1)*29
    # center over the subject yet safe above bottom CTA. Slight duplicate glow for readability.
    d.multiline_text((360,y+4),text,font=f,fill=(0,0,0,205),anchor='mm',align='center',spacing=8,stroke_width=8,stroke_fill=(2,5,13,235))
    d.multiline_text((360,y),text,font=f,fill=(250,250,249,255),anchor='mm',align='center',spacing=8,stroke_width=3,stroke_fill=(4,9,18,245))
    # Dark gradient-like title footer
    footer=Image.new('RGBA',(W,H));fd=ImageDraw.Draw(footer,'RGBA')
    for k in range(175):
        y0=H-190+k
        fd.line((0,y0,W,y0),fill=(3,8,16,int(110+145*(k/174))))
    im.alpha_composite(footer)
    d=ImageDraw.Draw(im,'RGBA')
    d.text((40,1130),title,font=ft(29,True),fill=(251,248,238,255))
    d.text((40,1180),f'Episode {epi:02d}  |  {ep["title"][:35]}',font=ft(22),fill=(224,217,201,255))
    d.rounded_rectangle((36,1225,684,1258),radius=14,fill=(175,187,200,49))
    d.text((54,1232),f'Fantasy Drama  •  {idx}/{total} scenes',font=ft(16,True),fill=(231,235,240,255))
    d.rounded_rectangle((36,1270,36+int(648*idx/total),1277),radius=3,fill=(235,145,68,255))

def render_frame(manifest,ep,shot,idx,total,featured_character,outfile):
    episode_id=ep['id'];sid=manifest['series_id']
    shot_id=shot.get('shot_id',f'{idx:02d}')
    # Approved shot art is a drop-in: never infer license from random URLs.
    override=ROOT/'assets'/'scene_overrides'/episode_id/f'{shot_id}.png'
    if override.exists():
        image=Image.open(override).convert('RGB')
        # cover-crop without distortion
        scale=max(W/image.width,H/image.height); nw,nh=int(image.width*scale),int(image.height*scale)
        image=image.resize((nw,nh),Image.Resampling.LANCZOS)
        im=image.crop(((nw-W)//2,(nh-H)//2,(nw+W)//2,(nh+H)//2)).convert('RGBA')
    else:
        seed=seed_for(episode_id,shot_id)
        theme='fox' if sid.startswith('S01') else 'human'
        variant=shot.get('mood','mystery')
        im=_gradient(theme,variant,seed)
        _landscape(im,theme,variant,seed)
        approved=ROOT/'assets'/'approved_characters'/f"{featured_character.get('id', 'unknown')}.png"
        if approved.exists():
            # User-provided *transparent* illustration, reused identically across episodes.
            from .util import read,save,sha
            lockfile='cloud_data/approved_character_art_locks.json'
            locks=read(lockfile,{})
            current=sha(approved)
            key=featured_character['id']
            if key in locks and locks[key]!=current:
                raise RuntimeError(f'Approved character art changed without explicit unlock: {key}')
            if key not in locks:
                locks[key]=current;save(lockfile,locks)
            art=Image.open(approved).convert('RGBA')
            scale=min(600/art.width,790/art.height);tw,th=max(1,int(art.width*scale)),max(1,int(art.height*scale))
            art=art.resize((tw,th),Image.Resampling.LANCZOS)
            im.alpha_composite(art,((W-tw)//2,1050-th))
        elif featured_character.get('type')=='animal':
            if 'ember' in featured_character['id']:_fox_character(im,featured_character,seed)
            else:_other_animal(im,featured_character,seed)
        elif featured_character.get('type')=='human':_human_character(im,seed,featured_character)
        else:
            if theme=='fox':_fox_character(im,featured_character,seed)
            else:_human_character(im,seed,featured_character)
        if shot.get('prop')=='blue_feather' or 'feather' in shot.get('text','').lower():_feather(im,variant)
        # Gentle vignette to focus center
        gx=np.linspace(-1,1,W)[None,:];gy=np.linspace(-1,1,H)[:,None]
        dark=np.clip((gx*gx+gy*gy)*100,0,110).astype('uint8')
        vignette=Image.fromarray(np.stack([np.zeros_like(dark)]*3+[dark],axis=2),'RGBA')
        im.alpha_composite(vignette)
    _overlay(im,manifest,ep,shot,idx,total,shot.get('mood','mystery'))
    outfile=Path(outfile);outfile.parent.mkdir(parents=True,exist_ok=True)
    im.convert('RGB').save(outfile,optimize=True)
    return outfile
