"""Nightfall illustrated character-acting engine — 100% local CPU.

Stylized 2D puppet animation, not an AI video generator and NOT a still slide.
Original character body, ears, face, limbs, tail and speech mouth animate on
every frame; deterministic forest, fire, feather and parallax effects.
No network, paid APIs, stock media or external image assets.
"""
from functools import lru_cache
import math
import random

from PIL import Image, ImageDraw, ImageFont

W, H = 360, 640
FPS = 12
DARK = (9, 15, 30, 255)


def mix(a, b, f):
    return int(a + (b - a) * max(0, min(1, f)))


def shift(color, add):
    return tuple(max(0, min(255, int(c + add))) for c in color[:3]) + (255,)


def oval(d, bbox, fill, outline=None, width=1):
    d.ellipse(tuple(int(v) for v in bbox), fill=fill, outline=outline, width=width)


def poly(d, xy, fill, outline=None, width=1):
    d.polygon([(int(x), int(y)) for x, y in xy], fill=fill)
    if outline:
        d.line([(int(x), int(y)) for x, y in xy] + [tuple(map(int, xy[0]))],
               fill=outline, width=width, joint="curve")


def star(d, x, y, radius, fill):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = radius if i % 2 == 0 else radius * 0.47
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    poly(d, pts, fill)


@lru_cache(maxsize=1)
def font(size):
    for name in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


@lru_cache(maxsize=20)
def forest(scene):
    """One detailed background per scene, no pan of a static character image."""
    hot = scene <= 11
    sky_top = (9, 13, 32) if hot else (7, 32, 55)
    sky_low = (96, 40, 38) if hot else (38, 91, 95)
    image = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(image)
    for y in range(H):
        f = min(1, y / 560)
        col = tuple(mix(a, b, f) for a, b in zip(sky_top, sky_low))
        d.line([(0, y), (W, y)], fill=col)
    # Sunset glow and drifting smoke behind silhouetted trees.
    oval(d, (170, 60, 450, 340), (136, 68, 58) if hot else (70, 127, 147))
    for k in range(4):
        r = random.Random(1200 + scene * 13 + k)
        y = 295 + k * 46
        points = [(0, H)] + [(x, y + int(26 * math.sin(x * .019 + k)) +
                              r.randrange(-8, 9)) for x in range(0, W + 25, 25)] + [(W, H)]
        poly(d, points, (25 + k * 5, 41 + k * 3, 47 + k * 2))
    r = random.Random(scene * 331)
    for layer in (0, 1):
        for k in range(15):
            x = r.randrange(-35, W + 35)
            y = r.randrange(235 + 30 * layer, 510)
            height = r.randint(105, 230)
            width = r.randint(15, 41)
            tree = (14 + layer * 6, 30 + layer * 4, 34 + layer * 4)
            d.line((x, y, x, y - height), fill=tree, width=6 + layer * 3)
            for j in range(3):
                yy = y - height + j * int(height * .21)
                poly(d, [(x, yy - 20), (x - width + j * 4, yy + 52),
                         (x + width - j * 4, yy + 52)], tree)
    # Mossy forest stage and soft ground islands.
    d.ellipse((-105, 469, 455, 715), fill=(18, 52, 47))
    d.ellipse((-20, 507, 397, 748), fill=(29, 69, 61))
    for i in range(33):
        x = r.randrange(W)
        y = r.randrange(499, H)
        d.line((x, y, x - r.randrange(3, 9), y + 14),
               fill=(55, 111, 77), width=2)
    for i in range(30):
        x, y = r.randrange(W), r.randrange(370, 545)
        rr = r.randrange(1, 4)
        oval(d, (x - rr, y - rr, x + rr, y + rr),
             (220, 137, 72) if hot else (92, 180, 204))
    return image


def fox(target, cx, cy, t, mouth, scale=1.0, action="run"):
    """Distinct head, eye, ear, scarf, tail and four moving limbs."""
    s = scale
    d = ImageDraw.Draw(target, "RGBA")
    sprint = action in ("run", "jump", "struggle", "reach")
    phase = t * (8.7 if sprint else 2.6)
    wave = math.sin(phase)
    bob = (8 if sprint else 3) * math.sin(phase * 2)
    jump = max(0, math.sin(phase)) * 17 if action == "jump" else 0
    cy += bob - jump
    def p(x, y):
        return (cx + x * s, cy + y * s)
    def bb(x1, y1, x2, y2):
        a, b = p(x1, y1); c, e = p(x2, y2)
        return a, b, c, e
    # Moving cast shadow.
    oval(d, (cx - 78 * s, cy + 90 * s, cx + 93 * s, cy + 113 * s),
         (0, 0, 0, 74))
    # Tail: a distinct swinging silhouette rather than camera motion.
    sway = 31 * math.sin(phase * .72)
    poly(d, [p(54, 27), p(109 + sway, -31), p(171 + sway, -23),
             p(149 + sway, 13), p(99 + sway, 49), p(52, 65)],
         (179, 68, 39, 255), (119, 49, 41, 255), 2)
    poly(d, [p(141 + sway, -21), p(171 + sway, -23),
             p(149 + sway, 13), p(128 + sway, 21)],
         (255, 237, 206, 255))
    # Four independently articulated legs.
    for i, xx in enumerate((-47, -18, 28, 52)):
        phase_j = wave if i in (0, 3) else -wave
        offset = phase_j * (22 if sprint else 8)
        poly(d, [p(xx - 14, 27), p(xx + 10, 28),
                 p(xx + 7 + offset, 99), p(xx - 15 + offset, 99)],
             (142, 55, 34, 255), (90, 44, 37, 255), 2)
        oval(d, bb(xx - 17 + offset, 83, xx + 9 + offset, 107),
             (81, 43, 43, 255))
    # Chest/body painted as multiple nested shades.
    oval(d, bb(-84, -41, 83, 78), (135, 53, 38, 255))
    oval(d, bb(-80, -52, 83, 65), (203, 83, 39, 255))
    oval(d, bb(-33, -18, 47, 69), (255, 228, 191, 255))
    oval(d, bb(-11, 15, 57, 61), (249, 207, 164, 255))
    # Head lifts/tilts relative to body.
    tilt = 4 * math.sin(t * 2.7)
    hx, hy = 0, -77 + tilt
    poly(d, [p(-51, hy - 55), p(-48, hy - 139), p(-4, hy - 92)],
         (198, 73, 36, 255), (98, 46, 35, 255), 2)
    poly(d, [p(46, hy - 57), p(61, hy - 136), p(82, hy - 76)],
         (200, 77, 39, 255), (98, 45, 36, 255), 2)
    # LEFT ear has one ivory-white tip, permanently.
    poly(d, [p(-48, hy - 119), p(-48, hy - 139), p(-35, hy - 113)],
         (251, 238, 215, 255))
    poly(d, [p(-41, hy - 61), p(-40, hy - 110), p(-12, hy - 80)],
         (115, 50, 55, 255))
    poly(d, [p(51, hy - 67), p(60, hy - 118), p(70, hy - 77)],
         (120, 52, 56, 255))
    oval(d, bb(-73, hy - 98, 82, hy + 43), (151, 57, 35, 255))
    oval(d, bb(-68, hy - 104, 79, hy + 32), (221, 94, 42, 255))
    # Animated eyebrows, eye glints and individual glances.
    blink = abs((t * .45) % 4.0 - 2.0) < .075
    for ex in (-29, 30):
        ey = hy - 31
        height = 5 if blink else 37
        oval(d, bb(ex - 20, ey - height / 2, ex + 20, ey + height / 2),
             (255, 239, 218, 255), (112, 51, 40, 255), 2)
        if not blink:
            px = math.sin(t * .6) * 5
            oval(d, bb(ex - 9 + px, ey - 10, ex + 12 + px, ey + 13),
                 (192, 128, 43, 255))
            oval(d, bb(ex - 3 + px, ey - 6, ex + 8 + px, ey + 10),
                 (39, 29, 29, 255))
            oval(d, bb(ex + px, ey - 8, ex + 5 + px, ey - 3),
                 (255, 255, 255, 255))
        d.arc(bb(ex - 21, ey - 34, ex + 24, ey - 15), 195, 343,
              fill=(97, 42, 34, 255), width=3)
    # Distinct cream cheeks and muzzle.
    oval(d, bb(-67, hy - 3, -4, hy + 45), (253, 230, 198, 255))
    oval(d, bb(0, hy - 3, 65, hy + 45), (253, 230, 198, 255))
    oval(d, bb(-30, hy + 11, 32, hy + 58), (255, 235, 205, 255))
    poly(d, [p(-11, hy + 15), p(11, hy + 15), p(0, hy + 24)],
         (57, 34, 35, 255))
    # Amplitude-driven mouth movement (not a phonetic / true-lipsync model).
    opening = 3 + min(22, mouth * 22)
    oval(d, bb(-15, hy + 34, 16, hy + 37 + opening),
         (56, 30, 35, 255))
    if opening > 8:
        oval(d, bb(-9, hy + 37 + opening * .5, 9, hy + 37 + opening),
             (201, 94, 97, 255))
    # Turquoise scarf wraps the neck, exactly ONE gold star.
    poly(d, [p(-65, -33), p(66, -37), p(51, -3), p(-57, -1)],
         (32, 146, 158, 255), (14, 93, 108, 255), 2)
    poly(d, [p(45, -12), p(64, 0), p(74, 34), p(45, 23)],
         (23, 131, 150, 255))
    sx, sy = p(-12, -20)
    star(d, sx, sy, 11 * s, (255, 211, 76, 255))
    # Fur tip lines and ear/head motion.
    for i in range(9):
        fx = -58 + i * 13
        d.line((*p(fx, hy - 93), *p(fx + 4, hy - 105)),
               fill=(245, 150, 75, 110), width=2)


def moss(target, cx, cy, t, mouth, scale=1.0, action="walk"):
    """Articulated tortoise with a spiral shell, shell crack and speaking mouth."""
    d = ImageDraw.Draw(target, "RGBA")
    s = scale
    walk = math.sin(t * 2.2) * 7
    cy += 2 * math.sin(t * 2.2)
    def p(x, y): return cx + x * s, cy + y * s
    def bb(a, b, c, e): return (*p(a, b), *p(c, e))
    oval(d, bb(-101, 72, 121, 96), (0, 0, 0, 75))
    for j, x in enumerate((-70, -28, 48, 76)):
        v = walk if j % 2 else -walk
        oval(d, bb(x - 23 + v, 39, x + 20 + v, 91),
             (90, 129, 86, 255), (51, 79, 57, 255), 3)
    oval(d, bb(-103, -71, 95, 64), (35, 73, 57, 255))
    oval(d, bb(-100, -93, 85, 55), (96, 103, 57, 255), (43, 66, 43, 255), 4)
    oval(d, bb(-91, -83, 71, 44), (122, 122, 66, 255))
    for scale2 in (.82, .6, .38):
        v = 67 * scale2
        d.arc(bb(-v - 9, -34 - v, v + 5, -30 + v),
              23, 337, fill=(64, 86, 54, 240), width=4)
    # Signature small right front shell crack.
    d.line([p(74, 20), p(81, 13), p(76, 30), p(84, 36)],
           fill=(221, 194, 123, 255), width=3)
    oval(d, bb(37, -65, 152, 33), (121, 159, 108, 255),
         (61, 90, 62, 255), 3)
    for x in (78, 121):
        blink = abs((t * .33) % 4 - 2) < .07
        oval(d, bb(x - 12, -38, x + 10, -30 if blink else -8),
             (239, 239, 196, 255))
        if not blink:
            oval(d, bb(x - 3, -29, x + 7, -14), (45, 60, 41, 255))
    opening = 2 + 13 * min(1, mouth)
    oval(d, bb(100, 1, 123, 2 + opening), (43, 53, 40, 255))


def moving_feather(d, scene, t):
    if scene not in (3, 4, 5, 12, 13, 14):
        return
    x = 177 + 63 * math.sin(t * .48 + scene)
    y = 230 + 36 * math.sin(t * .9 + scene)
    for radius, alpha in ((40, 15), (25, 31), (13, 85)):
        oval(d, (x-radius, y-radius, x+radius, y+radius),
             (53, 180, 238, alpha))
    poly(d, [(x - 10, y + 14), (x - 2, y - 18),
             (x + 7, y - 27), (x + 8, y + 5)],
         (118, 231, 249, 245))
    d.line((x - 9, y + 20, x + 9, y - 21),
           fill=(237, 253, 255, 245), width=2)


def caption(draw, text, speaker, t, voice_seconds):
    if not text or t > voice_seconds + .6:
        return
    words = text.split()
    group = 7
    chunks = [" ".join(words[i:i+group]) for i in range(0, len(words), group)]
    if not chunks:
        return
    idx = min(len(chunks) - 1,
              int(t / max(.25, voice_seconds / len(chunks))))
    txt = chunks[idx]
    name = ("EMBER" if speaker.endswith("_ember") else
            "MOSS" if speaker.endswith("_moss") else "NARRATOR")
    x1, y1, x2, y2 = 19, 523, 341, 621
    draw.rounded_rectangle((x1, y1, x2, y2), radius=15,
                           fill=(8, 17, 28, 225), outline=(66, 122, 133, 190),
                           width=2)
    draw.text((33, 533), name, fill=(96, 211, 220), font=font(11))
    # Wrap with pixel-based width; avoid accidental cropped text.
    lines = []
    current = ""
    for word in txt.split():
        trial = (current + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=font(17))[2] > 280 and current:
            lines.append(current)
            current = word
        else:
            current = trial
    if current: lines.append(current)
    for i, line in enumerate(lines[:3]):
        draw.text((33, 554 + i * 20), line, fill=(250, 246, 224),
                  font=font(17), stroke_width=0)


def render_frame(scene, t, mouth, voice_seconds, text, speaker, visible, direction):
    image = forest(scene).convert("RGBA")
    d = ImageDraw.Draw(image, "RGBA")
    # Smoke / embers move independently of character rigs.
    hot = scene < 12
    for i in range(24):
        x = (i * 79 + t * (11 + i % 5) * (1 if i % 2 else -1)) % (W + 30) - 15
        y = (i * 97 - t * (21 + i % 7)) % (H + 35)
        radius = 1.5 + (i % 3) * .8
        fill = (246, 136 + (i % 3) * 20, 63, 150) if hot else (86, 192, 228, 100)
        oval(d, (x-radius, y-radius, x+radius, y+radius), fill)
    act = ("jump" if any(word in direction.lower()
                        for word in ("leap", "jump", "springs", "stumbled")) else
           "struggle" if any(word in direction.lower()
                             for word in ("slid", "grips", "climb", "struggles")) else
           "run" if any(word in direction.lower()
                        for word in ("running", "run", "through smoke")) else "walk")
    chars = set(visible)
    if "s01_ember" in chars and "s01_moss" in chars:
        fox(image, 124 + math.sin(t * .6) * 12, 413, t,
            mouth if speaker == "s01_ember" else .1, scale=.72, action=act)
        moss(image, 269 + math.sin(t * .3) * 4, 416, t,
             mouth if speaker == "s01_moss" else .1, scale=.78)
    elif "s01_moss" in chars:
        moss(image, 160 + math.sin(t * .3) * 10, 420, t,
             mouth if speaker == "s01_moss" else .1, scale=1.1)
    else:
        fox(image, 161 + math.sin(t * .7) * 13, 410, t,
            mouth if speaker == "s01_ember" else .12, scale=1.02, action=act)
    d = ImageDraw.Draw(image, "RGBA")
    moving_feather(d, scene, t)
    caption(d, text, speaker, t, voice_seconds)
    return image.convert("RGB")
