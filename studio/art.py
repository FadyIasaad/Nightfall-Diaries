"""Deterministic, 2D, CPU-friendly visual fallback. Saved portraits never regenerate.
You may replace portraits with rights-cleared approved art and lock hashes.
"""
from pathlib import Path
import hashlib, math, textwrap
from PIL import Image, ImageDraw, ImageFont
from .util import ROOT, sha, read, save

COLORS={'s01_ember':('#CA6B3F','#36A9A6'),'s01_moss':('#687E59','#D7BC6B'),'s01_luma':('#747B9F','#E3D6BA'),'s01_ash':('#4F657A','#B9BDC4'),
        's01_narrator':('#8A77A0','#E1A77B'),'s02_noah':('#4D7BCC','#DEE6F4'),'s02_mira':('#B45F8F','#F3E0BC'),
        's02_dr_vale':('#5B8C94','#D6DDDE'),'s02_clockkeeper':('#756E91','#DEC899'),'s02_narrator':('#725A96','#E0D3E9')}

def font(n,bold=False):
    names=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for name in (names if bold else names[::-1]):
        try:return ImageFont.truetype(name,n)
        except OSError:pass
    return ImageFont.load_default()

def char_colors(c):
    if c['id'] in COLORS: return COLORS[c['id']]
    digest=hashlib.sha256(c['id'].encode()).hexdigest()
    vals=[int(digest[i:i+2],16) for i in (0,2,4)]
    return ('#%02x%02x%02x'%tuple(75+x//2 for x in vals),'#EDCB9F')

def _portrait(c,path):
    """Clear graphic cartoon marker, not misleading simulated Pixar/3D output."""
    w,h=600,700; main,accent=char_colors(c)
    im=Image.new('RGB',(w,h),'#1A213B'); d=ImageDraw.Draw(im)
    for y in range(h):
        z=y/h; d.line([(0,y),(w,y)],fill=(int(29+25*z),int(32+15*z),int(55+20*z)))
    # identity-preserving geometric motif
    seed=int(hashlib.sha256(c['id'].encode()).hexdigest()[:5],16)
    for i in range(10):
        x=(seed//(i+1)*31)%600; y=(seed//(i+2)*19)%620
        d.ellipse((x,y,x+5,y+5),fill='#8894B9')
    d.ellipse((125,150,475,500), fill=main,outline='#FAE0BA',width=7)
    if c.get('type')=='animal':
        d.polygon([(180,245),(215,83),(285,210)],fill=main)
        d.polygon([(323,210),(400,83),(430,248)],fill=main)
        d.ellipse((194,295,246,345),fill='#F9E6C7');d.ellipse((354,295,406,345),fill='#F9E6C7')
        d.ellipse((216,306,235,327),fill='#101722');d.ellipse((371,306,390,327),fill='#101722')
        d.ellipse((278,348,324,377),fill='#222735')
        d.polygon([(162,466),(436,466),(400,570),(200,570)],fill=accent)
    else:
        d.arc((198,180,403,445),180,350,fill='#F8E7C8',width=10)
        d.ellipse((215,300,238,325),fill='#131A2A');d.ellipse((356,300,379,325),fill='#131A2A')
        d.arc((262,345,345,390),0,180,fill='#EFE2CA',width=4)
        d.polygon([(147,480),(450,480),(525,700),(75,700)],fill=main)
    d.rounded_rectangle((30,584,570,673),radius=21,fill='#10192C')
    nm=c['name']
    d.text((300,627),nm,font=font(43,True),fill='white',anchor='mm')
    path.parent.mkdir(parents=True,exist_ok=True);im.save(path)

def ensure_portrait(series_id,c):
    path=ROOT/'seasons'/series_id/'characters'/c['id']/'cloud_reference.png'
    if not path.exists():_portrait(c,path)
    lockfile=f'seasons/{series_id}/characters/cloud_reference_locks.json'
    locks=read(lockfile,{})
    current=sha(path)
    if c['id'] in locks and locks[c['id']]!=current:raise RuntimeError(f'Locked art changed: {c["id"]}; approve/reset hash manually')
    if c['id'] not in locks:
        locks[c['id']]=current;save(lockfile,locks)
    return path

def split_lines(text,size=23):
    # Avoid cutting very long words; wrap preserving spaces.
    result=textwrap.wrap(text,width=size,break_long_words=False)
    return result[:9]

def build_slide(series_id,manifest,ep,c,text,path,part_index,total):
    W,H=720,1280; im=Image.new('RGB',(W,H)); d=ImageDraw.Draw(im)
    for y in range(H):
        k=y/H; d.line([(0,y),(W,y)],fill=(int(16+k*14),int(24+k*18),int(44+k*29)))
    d.ellipse((-280,-190,790,630),fill='#28375E')
    d.text((48,60),manifest['title'].upper(),font=font(25,True),fill='#D6DDED')
    d.text((48,109),f"EPISODE {ep['episode']:02d}   •   {ep['title'][:27]}",font=font(21),fill='#F1C675')
    portrait=Image.open(ensure_portrait(series_id,c)).convert('RGB')
    portrait.thumbnail((570,720))
    px=(W-portrait.width)//2;im.paste(portrait,(px,175))
    d=ImageDraw.Draw(im,'RGBA')
    d.rounded_rectangle((22,905,698,1230),radius=24,fill=(6,10,27,237),outline=(235,199,117,220),width=2)
    d.text((48,932),c['name'].upper(),font=font(24,True),fill='#FFD47C')
    lines=split_lines(text,34)
    if len(lines)>6:lines=split_lines(text,40)
    for i,line in enumerate(lines[:6]):d.text((48,977+i*37),line,font=font(22),fill='white')
    d.text((48,1243),f'{part_index}/{total}  •  AI DRAMA UNIVERSE',font=font(15),fill='#BBC5DF')
    path.parent.mkdir(parents=True,exist_ok=True);im.convert('RGB').save(path)
