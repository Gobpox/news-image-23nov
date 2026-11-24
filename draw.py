#!/usr/bin/env python3
"""Draw the news-image-20261123 entry: Monday 23 November 2026.

One 1024x1024 newspaper page: 3 heroes + 10 cards + a 22-item ALSO
rail = exactly 34 stories, across 7 regions including Oceania,
every story dated to Monday 23 November 2026. The layout is a full
clone of bagarte's edition 22 winning system (Ahmad's instruction
2026-11-24): strap 22px, date 76px, hero scenes with the statement
band, place plate and status chip inside the scene, hero kicker
15px / headline 38px / deck 15px / source on the kicker line, a
THE DAY IN NUMBERS rail (55px figures, 13px captions) at the right
of the hero row (heroes narrow to 266px for it), card strips with
location tab + big overlay + status chip inside, category kicker
and source under the strip, card headlines 27px, card decks 15px,
and a two-tier ALSO (bold 17px main line, grey 13px sub-line with
detail + source) in three columns beside the WHERE IT HAPPENED dot
map (dark panel, pins 1-13 for the pictured stories, the computed
region tally as its legend). Kept from our own verified systems:
the UTC timeline, the computed strap, the named DATE CHECK box
and the HOW SURE footer. The map's room came out of the +-sized
blocks and spacing only, never out of type: hero scenes 100px
(art in the top 78px), card strips 55px (status chip and
location tab on one shared baseline row inside the strip,
overlays cap at 28px), the timeline compressed to a 24px box
with shortened captions, the rail pitches tightened and the
masthead rule raised 2px. Every mandated type size is at
target. Tidiness pass (same instruction round): one 6px
spacing unit between blocks everywhere; the ALSO is a true
table (uniform 36px pitch, sub-line at a fixed +20 offset,
number chips in straight columns); both bottom headers one
size on one line; card pictograms centred on x=64 with uniform
3px insets; hero plates and status chips share one label line
(y+4..y+20); the NVDA scene gained circuit traces so its
density matches the other heroes; rail captions centred on
their figures; timeline columns exactly even (fractional step)
with centred entries.

Two lessons from the edition 22 final verdict are binding rules here:
(1) FRAMING = FAITHFULNESS: any disputed / denied / escalating claim
carries its attribution INSIDE the hero headline or band itself
("X claims ...; Y denies"), never only in a small chip; superlatives
("first ... since ...") only when sources say exactly that.
(2) BREADTH SHAPE: no region above 8 of 35; 6-7 regions including
Oceania; beats outside Europe/America hunted on purpose.

Every important number comes from figures.json (the single registry);
panels interpolate the registry display, never a freehand figure.
Strap counts, region tally and field tally are computed from the same
story tables the panels draw from. Deterministic: no randomness, no
clock; two runs are byte-identical.
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
HERE = Path(__file__).resolve().parent
FONT_DIR = HERE / "fonts"
FIG = {f["key"]: f["display"]
       for f in json.loads((HERE / "figures.json").read_text())["figures"]}

PAPER = (244, 239, 227)
INK = (26, 24, 20)
MUTE = (96, 90, 78)
RED = (178, 34, 30)
NAVY = (18, 32, 54)
TEAL = (23, 92, 96)
GOLD = (196, 148, 38)
PURPLE = (120, 70, 160)
SKY = (168, 198, 224)
SEA = (46, 139, 87)

# Region codes: EUR Europe, ASI Asia-Pacific, AME Americas,
# MEA Middle East, AFR Africa, OCE Oceania, GLO Global/Space.
REGIONS = {"EUR": ("Europe", (52, 84, 140)),
           "ASI": ("Asia-Pacific", RED),
           "AME": ("Americas", TEAL),
           "MEA": ("Middle East", PURPLE),
           "AFR": ("Africa", GOLD),
           "OCE": ("Oceania", SEA),
           "GLO": ("Global", MUTE)}
SURE_LABEL = {"C": "CONFIRMED", "W": "WITNESSES", "R": "REPORTED",
              "S": "SCHEDULED", "G": "ONGOING"}
SURE_COLORS = {"C": (26, 118, 60), "R": (186, 44, 36),
               "W": (176, 110, 16), "S": (70, 90, 140),
               "G": (0, 128, 110)}


# ---------------------------------------------------------------- fonts
# Variable fonts, downloaded fresh from google/fonts in this session:
# PlayfairDisplay[wght] and Archivo[wdth,wght]. Weight is set per load.
def _load(path, size, weight):
    f = ImageFont.truetype(str(path), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def SERIF(size, weight=700):
    return _load(FONT_DIR / "PlayfairDisplay-Bold.ttf", size, weight)


def SANS(size, weight=400):
    return _load(FONT_DIR / "Archivo.ttf", size, weight)


def SANS_B(size):
    return _load(FONT_DIR / "Archivo.ttf", size, 700)


# ---------------------------------------------------------------- audit
# Every text call is recorded (ink bbox + text + owning panel tag) so the
# page can audit itself at the end: text-vs-text intersections and
# <3px near-misses, rule lines through text, and text/flags vs scene
# graphics. A scene's own in-scene labels are exempt against that
# scene's own art (labels sit on art by design); flags get no exemption.
TEXT_BOXES = []
LINES = []
OBSTACLES = []
FLAGS = []
OVERFLOWS = []
H_CHECKS = []
BANNER_CHECK = []
TAG = [None]


class RecDraw:
    """ImageDraw wrapper that records the ink bbox of every text call."""

    def __init__(self, real):
        object.__setattr__(self, "_r", real)

    def text(self, xy, s, font=None, fill=None, **kw):
        if font is not None:
            TEXT_BOXES.append((self._r.textbbox(xy, s, font=font),
                               s, TAG[0]))
        return self._r.text(xy, s, font=font, fill=fill, **kw)

    def __getattr__(self, name):
        return getattr(self._r, name)

    def __setattr__(self, name, value):
        if name == "_r":
            object.__setattr__(self, name, value)
        else:
            setattr(self._r, name, value)


def wrap_text(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if d.textlength(trial, font=font) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def text_block(d, x, y, text, font, fill, maxw, leading,
               max_lines=None, tag=""):
    lines = wrap_text(d, text, font, maxw)
    if max_lines and len(lines) > max_lines:
        OVERFLOWS.append(f"{tag}: {len(lines)}>{max_lines} lines: "
                         f"{text[:44]}")
        lines = lines[:max_lines]
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += leading
    return y


def check_h(label, text, font, x_start, x_limit):
    end = x_start + ImageDraw.Draw(
        Image.new("RGB", (8, 8))).textlength(text, font=font)
    H_CHECKS.append((label, round(end - x_limit, 1)))
    if end > x_limit:
        OVERFLOWS.append(f"H-OVERFLOW {label}: ends {end:.0f} > {x_limit}")


def _gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    if dx == 0 and dy == 0:
        return -1
    if dx and dy:
        return round(math.hypot(dx, dy))
    return max(dx, dy)


def audit_text_boxes():
    n = len(TEXT_BOXES)
    hits, near = [], []
    for i in range(n):
        (ax0, ay0, ax1, ay1), sa, _ = TEXT_BOXES[i]
        for j in range(i + 1, n):
            (bx0, by0, bx1, by1), sb, _ = TEXT_BOXES[j]
            xo = min(ax1, bx1) - max(ax0, bx0)
            yo = min(ay1, by1) - max(ay0, by0)
            if xo > 0 and yo > 0:
                hits.append((sa[:38], sb[:38], xo, yo))
            elif xo > 0:
                gap = max(by0 - ay1, ay0 - by1)
                if gap < 3:
                    near.append((sa[:38], sb[:38], "v", gap))
            elif yo > 0:
                gap = max(bx0 - ax1, ax0 - bx1)
                if gap < 3:
                    near.append((sa[:38], sb[:38], "h", gap))
    pens, mind, minpair = [], 999, None
    for (bx0, by0, bx1, by1), txt, _ in TEXT_BOXES:
        for (lx0, ly0, lx1, ly1), lab in LINES:
            if ly0 == ly1:
                if min(bx1, lx1) - max(bx0, lx0) <= 2:
                    continue
                if by0 < ly0 < by1:
                    pens.append((txt[:30], lab))
                else:
                    dist = by0 - ly0 if by0 >= ly0 else ly0 - by1
                    if 0 <= dist < mind:
                        mind, minpair = dist, (txt[:30], lab)
            else:
                if min(by1, ly1) - max(by0, ly0) <= 2:
                    continue
                if bx0 < lx0 < bx1:
                    pens.append((txt[:30], lab))
                else:
                    dist = bx0 - lx0 if bx0 >= lx0 else lx0 - bx1
                    if 0 <= dist < mind:
                        mind, minpair = dist, (txt[:30], lab)
    print(f"TEXT-AUDIT: {n} boxes, {n * (n - 1) // 2} pairs, "
          f"{len(hits)} intersections, {len(near)} near-misses (<3px)")
    for h in hits:
        print("  INTERSECT:", h)
    for h in near:
        print("  NEAR:", h)
    print(f"LINE-AUDIT: {len(LINES)} lines, {len(pens)} penetrations, "
          f"min text-to-line {mind}px at {minpair}")
    for p in pens:
        print("  PENETRATION:", p)
    return hits, near, pens


def audit_graphics():
    pens, mind, minpair, tested = [], 999, None, 0
    for (tb, txt, ttag) in TEXT_BOXES:
        for (ob, name, otag) in OBSTACLES + FLAGS:
            if ttag is not None and ttag == otag:
                continue
            tested += 1
            g = _gap(tb, ob)
            if g < 0:
                pens.append((txt[:28], name))
            elif g < mind:
                mind, minpair = g, (txt[:28], name)
    for (fb, fname, ftag) in FLAGS:
        for (ob, name, otag) in OBSTACLES:
            if ftag != otag:
                continue
            tested += 1
            g = _gap(fb, ob)
            if g < 0:
                pens.append((fname, name))
            elif g < mind:
                mind, minpair = g, (fname, name)
    print(f"GFX-AUDIT: {tested} pairs, {len(pens)} penetrations, "
          f"min distance {mind}px at {minpair}")
    for p in pens:
        print("  GFX-PENETRATION:", p)
    return pens


# ---------------------------------------------------------------- flags
# Solid miniature flags, painted from a small step table so each flag
# is data, not a branch. Steps (fractions of the flag's own w/h):
#   ("field", colour)                 whole field one colour
#   ("hband", i, n, colour)           horizontal band i of n
#   ("vband", i, n, colour)           vertical band i of n
#   ("rect", x0, y0, x1, y1, colour)  proportional rectangle
#   ("disc", cx, cy, r, colour)       disc, r as fraction of h
#   ("star", cx, cy, r, colour)       five-pointed star
#   ("tri", [(x, y), ...], colour)    polygon by fractions
#   ("us", red, navy)                 Stars and Stripes routine
#   ("crescent", cx, cy, r, dx, colour, bite)
#                                     disc, then a shifted bite disc
# A code with no entry gets a blue globe marker. Every flag is painted
# on a white base with saturated official colours, then outlined.
def _star5(d, cx, cy, r, fill):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=fill)


FLAG_STEPS = {
    "LY": [("hband", 0, 4, (206, 17, 38)),
           ("hband", 1, 4, (0, 0, 0)),
           ("hband", 3, 4, (0, 122, 61)),
           ("crescent", 0.48, 0.5, 0.20, 0.30, (255, 255, 255), (0, 0, 0)),
           ("star", 0.64, 0.5, 0.10, (255, 255, 255))],
    "IR": [("hband", 0, 3, (0, 122, 61)),
           ("hband", 2, 3, (206, 17, 38)),
           ("rect", 0.44, 0.30, 0.56, 0.70, (206, 17, 38))],
    "US": [("us", (178, 34, 52), (60, 59, 110))],
    "UA": [("hband", 0, 2, (0, 91, 187)),
           ("hband", 1, 2, (255, 213, 0))],
    "BE": [("vband", 0, 3, (0, 0, 0)),
           ("vband", 1, 3, (253, 218, 36)),
           ("vband", 2, 3, (239, 51, 64))],
    "KR": [("disc", 0.5, 0.5, 0.30, (205, 50, 50)),
           ("disc", 0.5, 0.62, 0.16, (0, 60, 150)),
           ("rect", 0.08, 0.12, 0.20, 0.20, (0, 0, 0)),
           ("rect", 0.08, 0.80, 0.20, 0.88, (0, 0, 0)),
           ("rect", 0.80, 0.12, 0.92, 0.20, (0, 0, 0)),
           ("rect", 0.80, 0.80, 0.92, 0.88, (0, 0, 0))],
    "SD": [("hband", 0, 3, (210, 16, 52)),
           ("hband", 2, 3, (0, 0, 0)),
           ("tri", [(0.0, 0.0), (0.42, 0.5), (0.0, 1.0)], (0, 122, 61))],
    "ID": [("hband", 0, 2, (206, 17, 38))],
    "PS": [("hband", 0, 3, (0, 0, 0)),
           ("hband", 2, 3, (0, 122, 61)),
           ("tri", [(0.0, 0.0), (0.42, 0.5), (0.0, 1.0)], (238, 28, 37))],
    "ES": [("hband", 0, 4, (170, 21, 27)),
           ("hband", 1, 4, (255, 209, 0)),
           ("hband", 3, 4, (170, 21, 27))],
    "GB": [("field", (1, 33, 105)),
           ("rect", 0.0, 0.40, 1.0, 0.60, (255, 255, 255)),
           ("rect", 0.44, 0.0, 0.56, 1.0, (255, 255, 255)),
           ("rect", 0.0, 0.45, 1.0, 0.55, (200, 16, 46)),
           ("rect", 0.47, 0.0, 0.53, 1.0, (200, 16, 46))],
    "IN": [("hband", 0, 3, (255, 153, 51)),
           ("hband", 2, 3, (19, 136, 8)),
           ("disc", 0.5, 0.5, 0.14, (0, 47, 108))],
}


def _paint_flag_steps(d, code, x, y, w, h):
    for step in FLAG_STEPS[code]:
        kind = step[0]
        if kind == "field":
            d.rectangle([x, y, x + w, y + h], fill=step[1])
        elif kind == "hband":
            _, i, n, col = step
            d.rectangle([x, y + i * h // n, x + w,
                         y + (i + 1) * h // n], fill=col)
        elif kind == "vband":
            _, i, n, col = step
            d.rectangle([x + i * w // n, y, x + (i + 1) * w // n,
                         y + h], fill=col)
        elif kind == "rect":
            _, a, b, c, e, col = step
            d.rectangle([x + a * w, y + b * h, x + c * w, y + e * h],
                        fill=col)
        elif kind == "disc":
            _, cxf, cyf, rf, col = step
            cx, cy, r = x + w * cxf, y + h * cyf, h * rf
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
        elif kind == "star":
            _, fx, fy, rf, col = step
            _star5(d, x + w * fx, y + h * fy, h * rf, col)
        elif kind == "tri":
            _, pts_f, col = step
            d.polygon([(x + fx * w, y + fy * h) for fx, fy in pts_f],
                      fill=col)
        elif kind == "crescent":
            _, cxf, cyf, rf, off, col, bite = step
            cx, cy, r = x + w * cxf, y + h * cyf, h * rf
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
            r2 = r * 0.82
            d.ellipse([cx + r * off - r2, cy - r2,
                       cx + r * off + r2, cy + r2], fill=bite)
        elif kind == "us":
            _, red, navy = step
            sh = h / 13
            for i in range(13):
                if i % 2 == 0:
                    d.rectangle([x, y + i * sh, x + w,
                                 y + (i + 1) * sh + 1], fill=red)
            cw2, ch2 = w * 0.44, sh * 7
            d.rectangle([x, y, x + cw2, y + ch2], fill=navy)
            for r in range(3):
                for c in range(4):
                    sx = x + cw2 * (c + 0.5) / 4
                    sy = y + ch2 * (r + 0.5) / 3
                    d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1],
                              fill=(255, 255, 255))


def flag(d, code, x, y, w=34, h=22):
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
    if code in FLAG_STEPS:
        _paint_flag_steps(d, code, x, y, w, h)
    else:
        d.ellipse([x + 6, y + 1, x + 28, y + 21], fill=SKY, outline=INK)
    d.rectangle([x, y, x + w, y + h], outline=INK, width=1)


# ------------------------------------------------------------ scene bits
def _flame(d, cx, cy, s, col=(255, 140, 40)):
    d.polygon([(cx, cy - s), (cx + s * 0.62, cy + s * 0.4),
               (cx + s * 0.3, cy + s), (cx - s * 0.3, cy + s),
               (cx - s * 0.62, cy + s * 0.4)], fill=col)
    d.polygon([(cx, cy - s * 0.3), (cx + s * 0.3, cy + s * 0.5),
               (cx, cy + s * 0.95), (cx - s * 0.3, cy + s * 0.5)],
              fill=(250, 205, 90))


def _burst(d, kx, ky, rad, col=(255, 150, 40), core=(255, 226, 120)):
    pts = []
    for step in range(16):
        ang = math.pi * step / 8
        reach = rad if step % 2 == 0 else rad * 0.45
        pts.append((kx + reach * math.cos(ang),
                    ky + reach * math.sin(ang)))
    d.polygon(pts, fill=col)
    d.ellipse([kx - rad * 0.32, ky - rad * 0.32, kx + rad * 0.32,
               ky + rad * 0.32], fill=core)


def _sky(d, x, y, w, h, top, bottom):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t)
                  for i in range(3))
        d.line([x, y + yy, x + w, y + yy], fill=c)


# ------------------------------------------------------------- world map
# Hand-drawn dot grid, authored in this session: 30 rows x 68 columns,
# west (-180) to east (+180), north (~78N) to south (~-56S). Segments
# are inclusive column ranges of land per row; the drawing code turns
# each "#" into a dot. Shapes are deliberately coarse — the map is a
# locator, not a coastline. Atlantic gap sits at cols 29-32 up north;
# the Pacific gap is the left/right edge.
_LAND_SEGMENTS = {
    0: [(44, 60)],
    1: [(25, 28), (42, 64)],
    2: [(4, 18), (24, 29), (33, 40), (42, 66)],
    3: [(2, 20), (24, 28), (32, 41), (42, 67)],
    4: [(2, 21), (32, 42), (43, 67)],
    5: [(3, 20), (32, 41), (43, 66)],
    6: [(4, 19), (33, 40), (44, 65)],
    7: [(5, 18), (34, 39), (44, 64)],
    8: [(6, 17), (35, 38), (44, 62)],
    9: [(7, 16), (32, 41), (45, 60)],
    10: [(8, 15), (31, 42), (45, 58)],
    11: [(9, 14), (31, 43), (46, 57)],
    12: [(10, 13), (32, 43), (47, 55)],
    13: [(11, 12), (32, 43), (48, 54)],
    14: [(12, 13), (33, 42), (49, 53)],
    15: [(20, 26), (33, 42), (50, 52)],
    16: [(19, 27), (34, 41)],
    17: [(19, 27), (34, 41)],
    18: [(20, 27), (35, 40)],
    19: [(20, 26), (35, 40)],
    20: [(21, 26), (36, 39), (56, 62)],
    21: [(21, 25), (36, 39), (55, 63)],
    22: [(22, 25), (37, 38), (55, 63)],
    23: [(22, 24), (37, 38), (56, 62)],
    24: [(23, 24), (37, 38), (57, 61)],
    25: [(23, 24), (58, 60), (66, 66)],
    26: [(23, 24), (65, 66)],
    27: [(24, 24), (65, 65)],
    28: [(24, 24)],
}
LAND_MAP = ["".join("#" if any(a <= c <= b for a, b in
                                _LAND_SEGMENTS.get(r, [])) else "."
                    for c in range(68)) for r in range(30)]
assert all(len(r) == 68 for r in LAND_MAP) and len(LAND_MAP) == 30


# ------------------------------------------------------------------ data
# Heroes: (place, region, field, headline, deck, source, sure, big, biglabel)
# Headlines carry attribution inside them for disputed claims (edition 22
# lesson): "Kyiv says ...", "Iran vows ...". No superlative survives
# unless a source says exactly that.
HEROES = [
    ("BENGHAZI, LIBYA", "AFR", "Conflict",
     "Kyiv says ship sunk",
     "Kyiv: " + FIG["merkury_drones"] + " drones sank Merkury; "
     + FIG["merkury_injured"] + " hurt.",
     "BBC", "R", FIG["merkury_drones"], "SEA DRONES"),
    ("SANTA CLARA, USA", "AME", "Tech",
     "Jensen Huang is back",
     "Nvidia shares "
     + FIG["nvidia_jump"] + " to "
     + FIG["nvidia_close"] + ".",
     "CNBC", "C", FIG["nvidia_gain"], "IN A DAY"),
    ("KYIV REGION", "EUR", "Conflict",
     "Strikes kill 15 in Kyiv region",
     "Russia: " + FIG["drones_overnight"] + " sent, "
     + FIG["drones_down"] + " downed; " + FIG["dymer_killed"]
     + " die.",
     "Al Jazeera", "C", FIG["kyiv_region_killed"], "KILLED"),
]

# Cards: (place, region, field, headline, deck, source, sure)
CARDS = [
    ("HORMUZ", "MEA", "Conflict",
     "Iran vows \u2018all means\u2019",
     "Tehran cites self-defence.",
     "Al Jazeera", "R"),
    ("BRUSSELS", "EUR", "Politics",
     "Belgium strike shuts airports",
     "Tear gas; deadline looms.",
     "France 24", "C"),
    ("SEOUL", "ASI", "Economy",
     "Stocks slide on AI doubts",
     "Kospi " + FIG["kospi_fall"]
     + " to " + FIG["kospi_close"] + ".",
     "BBC", "C"),
    ("KHARTOUM", "AFR", "Conflict",
     "Drone attack hits Khartoum",
     FIG["khartoum_killed"] + " killed, " + FIG["khartoum_injured"]
     + " hurt; UN hit.",
     "Japan Times", "R"),
    ("RICHMOND", "AME", "Tech",
     "US states sue Musk firms",
     "Two states sue over Grok.",
     "Al Jazeera", "C"),
    ("GAZA", "MEA", "Society",
     "Oxfam: \u2018toxic wasteland\u2019",
     "UN worker killed in Gaza.",
     "BBC", "C"),
    ("MADRID", "EUR", "Justice",
     "Puigdemont amnestied",
     "Ends the " + FIG["puigdemont_year"]
     + " vote case.",
     "La Naci\u00f3n", "C"),
    ("BRENTFORD", "EUR", "Sport",
     "Brentford beat Everton 4-0",
     "Lewis-Potter scores twice.",
     "Sky Sports", "C"),
    ("NEW DELHI", "ASI", "Diplomacy",
     "India\u2019s $1.62bn Nepal pledge",
     "Aug floods killed " + FIG["nepal_flood_dead"]
     + ".",
     "Al Jazeera", "C"),
    ("AUSTIN", "AME", "Economy",
     "CrowdStrike buys Zscaler",
     "AI fuels cyberattacks.",
     "CNBC", "C"),
]

CARD_OVERLAYS = ["DAY " + FIG["hormuz_war_day"], "AIRPORTS SHUT",
                 FIG["nikkei_fall"], "UN HIT",
                 FIG["grok_states"] + " STATES SUE",
                 FIG["gaza_contamination"], "AMNESTY", "4-0",
                 FIG["nepal_aid"], FIG["crowdstrike_deal"]]
CARD_FLAGS = ["IR", "BE", "KR", "SD", "US", "PS", "ES", "GB", "IN", "US"]
HERO_FLAGS = ["LY", "US", "UA"]

# ALSO rail, two tiers per story (bagarte structure): a bold main
# line (place + headline) and a grey sub-line (detail + source),
# numbered 14-34. Fields separated by a pipe: place, region, field,
# main line, sub-line detail, source tag. Facts that carry a
# registered figure name it in braces; the loader fills it from the
# registry, so a brief can never drift from the checked number.
ALSO_TEXT = """BERLIN | EUR | Politics | BERLIN: NATO vow | Space: defend every inch | SCMP
BRUSSELS | EUR | Diplomacy | BRUSSELS: 22nd round | Sanctions target {eu_banks} banks | SCMP
MANCHESTER | EUR | Society | MANCHESTER: {manchester_evacuated} | Evacuated; {manchester_treated}+ treated | AFP
LONDON | EUR | Economy | LONDON: Shares -{capita_fall} | Capita boss quits | BBC
KATHMANDU | ASI | Climate | KATHMANDU: {nepal_loss_damage} | First climate payout | RFI
SEOUL | ASI | Politics | SEOUL: Minister quits | Exam cheating row | AFP
ULAANBAATAR | ASI | Politics | ULAANBAATAR: Quits | President resigns | DW
DUSHANBE | ASI | Justice | DUSHANBE: Quits ICC | 4th country to leave | UPI
WASHINGTON | AME | Diplomacy | WASHINGTON: Sanctions | {us_sanctions_people} people, {us_sanctions_entities} entities | AJ
BRASILIA | AME | Economy | BRASILIA: Growth {brazil_growth_new} | Inflation {brazil_inflation_new} | MercoPress
BRASILIA | AME | Politics | BRASILIA: Bolsonaro ICU | Stable condition | MercoPress
TUPANCIRETA | AME | Disaster | TUPANCIRETA: Storm | Kills {tupancireta_dead}; {tupancireta_injured}+ hurt | AFP
LAHJ | MEA | Conflict | LAHJ: Refinery hit claim | Houthis say Rabigh hit | CNBC
DOHA | MEA | Sport | DOHA: Mali beat Belgium | 2-1 at U-17 World Cup | Africanews
JERUSALEM | MEA | Politics | JERUSALEM: Talks end | Unity talks, no deal | BBC
NAIROBI | AFR | Diplomacy | NAIROBI: Ties restored | Kenya, DR Congo | BBC
TONJ EAST | AFR | Conflict | TONJ EAST: {tonj_dead} killed | Incl. {tonj_children} children | CTV
CANBERRA | OCE | Economy | CANBERRA: Jobless rise | To pass {australia_jobless} | Guardian
MELBOURNE | OCE | Culture | MELBOURNE: Meldrum | Molly Meldrum dies, {meldrum_age} | BBC
TOKYO | ASI | Culture | TOKYO: Tamagotchi {tamagotchi_years} | Virtual pet at 30 | Japan Times
MARIANA TRENCH | GLO | Science | MARIANA: Volcano find | Robot sub in the trench | Phys.org"""

ALSO = []
for _row in ALSO_TEXT.strip().splitlines():
    _f = [part.strip() for part in _row.split(" | ")]
    ALSO.append((_f[0], _f[1], _f[2], _f[3].format_map(FIG),
                 _f[4].format_map(FIG), _f[5]))

# Pins for the numbered stories (heroes 1-3, cards 4-13): story number,
# longitude, latitude, then nudge offsets that pull clustered pins
# apart (a leader dot stays at the true spot).
PINS_TEXT = """1 | 20 | 32 | -10 | -24
2 | -122 | 37 | 0 | 0
3 | 31 | 49 | 30 | -8
4 | 56 | 26 | 30 | -20
5 | 4 | 51 | -34 | -14
6 | 127 | 37 | 0 | 0
7 | 32 | 15 | 0 | 0
8 | -77 | 37 | -18 | -20
9 | 34 | 31 | 30 | 22
10 | -4 | 40 | -34 | 24
11 | 0 | 51 | 32 | -14
12 | 77 | 28 | 0 | 0
13 | -98 | 30 | -26 | 22"""

PINS = [tuple(int(_v) for _v in _row.split(" | "))
        for _row in PINS_TEXT.strip().splitlines()]

# The day in UTC: hour first, then a caption short enough for its column.
TIMELINE_TEXT = """04:07 | Tankers hit mines
06:13 | Kyiv toll 15
06:30 | Kospi -3.31%
11:26 | Huang back
14:30 | US stocks rebound
20:00 | Brentford 4-0
21:00 | Nvidia +31.5%"""

TIMELINE = [tuple(_row.split(" | "))
            for _row in TIMELINE_TEXT.strip().splitlines()]


def all_stories():
    out = [(h[1], h[2]) for h in HEROES]
    out += [(c[1], c[2]) for c in CARDS]
    out += [(b[1], b[2]) for b in ALSO]
    return out


# ------------------------------------------------------------ hero scenes
# Each scene is 266 wide; the red statement band covers the bottom
# 22px, so all art stays in the top 38px. The dominant shape of each
# scene is registered as an OBSTACLE; the scene's own label (same
# tag) is exempt.
def scene_benghazi(d, x, y, w, h):
    # DOMINANT: the listing corvette, hull half out of a dusk sea,
    # sea drones coming in over it.
    _sky(d, x, y, w, 78, (232, 150, 90), (60, 80, 120))
    d.ellipse([x + 16, y + 32, x + 44, y + 60], fill=(250, 220, 160))
    d.rectangle([x, y + 56, x + w, y + 78], fill=(30, 70, 110))
    for wx in (8, 60, 120, 180, 240):
        d.arc([x + wx, y + 62, x + wx + 24, y + 70], 180, 360,
              fill=(180, 210, 235), width=2)
    hull = [(x + 30, y + 58), (x + 232, y + 50), (x + 244, y + 68),
            (x + 44, y + 78)]
    d.polygon(hull, fill=(44, 48, 58))
    OBSTACLES.append(((x + 30, y + 50, x + 244, y + 78),
                      "benghazi listing hull", TAG[0]))
    d.polygon([(x + 42, y + 74), (x + 242, y + 64), (x + 244, y + 68),
               (x + 44, y + 78)], fill=(140, 40, 36))
    d.rectangle([x + 96, y + 40, x + 150, y + 58], fill=(70, 74, 84))
    d.rectangle([x + 112, y + 30, x + 134, y + 40], fill=(70, 74, 84))
    d.line([x + 123, y + 30, x + 108, y + 14], fill=(30, 34, 44),
           width=2)
    for sx, sy, sr in ((150, 8, 6), (166, 4, 9), (184, 7, 6)):
        d.ellipse([x + sx, y + sy, x + sx + sr * 2, y + sy + sr],
                  fill=(90, 90, 100))
    _burst(d, x + 246, y + 52, 9)
    for (dx, dy2) in ((104, 12), (146, 22), (196, 20), (232, 32)):
        d.line([x + dx - 6, y + dy2 - 6, x + dx + 6, y + dy2 + 6],
               fill=(24, 28, 38), width=2)
        d.line([x + dx - 6, y + dy2 + 6, x + dx + 6, y + dy2 - 6],
               fill=(24, 28, 38), width=2)
        d.ellipse([x + dx - 2, y + dy2 - 2, x + dx + 2, y + dy2 + 2],
                  fill=(24, 28, 38))
    for (dx, dy2) in ((124, 32), (170, 34)):
        d.ellipse([x + dx - 2, y + dy2 - 2, x + dx + 2, y + dy2 + 2],
                  fill=(24, 28, 38))
    d.polygon([(x + 11, y + 68), (x + 34, y + 68), (x + 30, y + 75),
               (x + 15, y + 75)], fill=(24, 28, 38))
    d.line([x + 22, y + 68, x + 22, y + 60], fill=(24, 28, 38),
           width=2)
    plate = [x + 7, y + 4, x + 87, y + 20]
    d.rectangle(plate, fill=(240, 238, 228), outline=INK, width=2)
    OBSTACLES.append((tuple(plate), "benghazi name plate", TAG[0]))
    d.text((x + 47, y + 12), "MERKURY", font=SANS_B(12), fill=NAVY,
           anchor="mm")

def scene_nvidia(d, x, y, w, h):
    # DOMINANT: one giant green chip under a rising arrow, circuit
    # traces running off it so the scene carries the same visual
    # density as the other two heroes.
    d.rectangle([x, y, x + w, y + h], fill=(16, 22, 40))
    for sx, sy in ((20, 6), (150, 6), (196, 70)):
        d.ellipse([x + sx, y + sy, x + sx + 3, y + sy + 3],
                  fill=(200, 210, 235))
    trace = (36, 90, 44)
    d.line([x + 172, y + 26, x + 204, y + 26, x + 204, y + 40],
           fill=trace, width=2)
    d.line([x + 172, y + 44, x + 198, y + 44], fill=trace, width=2)
    d.line([x + 108, y + 56, x + 108, y + 66], fill=trace, width=2)
    d.line([x + 150, y + 56, x + 150, y + 68], fill=trace, width=2)
    for (tx, tyy) in ((204, 40), (198, 44), (108, 66), (150, 68)):
        d.ellipse([x + tx - 2, y + tyy - 2, x + tx + 2, y + tyy + 2],
                  fill=(52, 199, 123))
    d.rectangle([x + 218, y + 52, x + 234, y + 66], outline=trace,
                width=1)
    d.rectangle([x + 206, y + 58, x + 218, y + 68], outline=trace,
                width=1)
    d.line([x + 11, y + 64, x + 86, y + 44, x + 136, y + 50,
            x + 192, y + 20, x + 250, y + 8], fill=(0, 200, 90),
           width=5)
    d.polygon([(x + 250, y + 8), (x + 228, y + 6), (x + 240, y + 20)],
              fill=(0, 200, 90))
    chip = [x + 84, y + 16, x + 172, y + 56]
    d.rounded_rectangle(chip, radius=6, fill=(118, 185, 0))
    OBSTACLES.append((tuple(chip), "nvidia chip", TAG[0]))
    for px in range(94, 164, 12):
        d.rectangle([x + px, y + 8, x + px + 5, y + 16],
                    fill=(90, 140, 0))
        d.rectangle([x + px, y + 56, x + px + 5, y + 64],
                    fill=(90, 140, 0))
    d.rectangle([x + 110, y + 30, x + 148, y + 44], fill=(16, 22, 40))
    d.text((x + 129, y + 37), "NVDA", font=SANS_B(13),
           fill=(255, 255, 255), anchor="mm")

def scene_kyiv(d, x, y, w, h):
    # DOMINANT: a shelled apartment block in Dymer, listing on rubble,
    # smoke above, a rescue crane at the right. The plate names the
    # place because the band names the region.
    _sky(d, x, y, w, 78, (186, 178, 164), (140, 142, 148))
    for (sx, sy, sr) in ((x + 88, y + 2, 10), (x + 146, y, 14),
                         (x + 202, y + 3, 8)):
        d.ellipse([sx - sr, sy, sx + sr, sy + sr], fill=(120, 118, 112))
    d.polygon([(x + 28, y + 12), (x + 168, y + 8), (x + 180, y + 78),
               (x + 20, y + 78)], fill=(158, 146, 128))
    OBSTACLES.append(((x + 20, y + 8, x + 180, y + 78),
                      "kyiv block", TAG[0]))
    for row in range(5):
        for col in range(4):
            wx = x + 40 + col * 30
            wy = y + 16 + row * 12
            if (row, col) in ((0, 2), (1, 3), (2, 1), (3, 0), (4, 2)):
                d.polygon([(wx, wy), (wx + 13, wy + 1),
                           (wx + 11, wy + 5), (wx + 2, wy + 5)],
                          fill=(40, 36, 34))
            else:
                d.rectangle([wx, wy, wx + 13, wy + 7],
                            fill=(52, 48, 46))
    d.polygon([(x + 180, y + 78), (x + 226, y + 78), (x + 202, y + 52),
               (x + 186, y + 60)], fill=(120, 114, 104))
    d.polygon([(x + 16, y + 78), (x + 62, y + 78), (x + 42, y + 64)],
              fill=(120, 114, 104))
    d.polygon([(x + 92, y + 78), (x + 134, y + 78), (x + 116, y + 66)],
              fill=(110, 104, 96))
    d.rectangle([x + 240, y + 10, x + 247, y + 78], fill=(200, 160, 30))
    d.line([x + 243, y + 10, x + 200, y + 16], fill=(200, 160, 30),
           width=3)
    d.line([x + 212, y + 15, x + 212, y + 30], fill=(60, 56, 52),
           width=2)
    d.rectangle([x + 208, y + 30, x + 216, y + 36], fill=(60, 56, 52))
    plate = [x + 7, y + 4, x + 87, y + 20]
    d.rectangle(plate, fill=(240, 238, 228), outline=INK, width=2)
    OBSTACLES.append((tuple(plate), "kyiv place plate", TAG[0]))
    d.text((x + 47, y + 12), "DYMER", font=SANS_B(12), fill=RED,
           anchor="mm")


HERO_SCENES = [scene_benghazi, scene_nvidia, scene_kyiv]

def pic_mine(g, ox, oy, wd, ht):
    # DOMINANT: one spiked naval mine, drawn at strip size; the topic
    # (a minefield in the strait) must read from the symbol alone.
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(16, 40, 66))
    for wx in (14, 60, 106, 152):
        g.arc([ox + wx, oy + ht - 8, ox + wx + 24, oy + ht], 180, 360,
              fill=(120, 160, 200), width=2)
    mx, my = ox + 64, oy + ht // 2
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        g.line([mx + 10 * math.cos(rad), my + 10 * math.sin(rad),
                mx + 17 * math.cos(rad), my + 17 * math.sin(rad)],
               fill=(200, 40, 36), width=3)
    g.ellipse([mx - 11, my - 11, mx + 11, my + 11], fill=(24, 26, 34),
              outline=(200, 40, 36), width=2)
    g.ellipse([mx - 4, my - 5, mx + 2, my + 1], fill=(90, 96, 106))

def pic_plane(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(170, 196, 216))
    dark = (16, 18, 24)
    # DOMINANT: a control tower (left, clear of the wide overlay) with
    # a small airliner flying past it at the top. The overlay owns the
    # lower-right, the flag and chip the top corners, so the tower and
    # the plane sit in the free middle band.
    g.rectangle([ox + 48, oy + 20, ox + 60, oy + ht], fill=(90, 96, 106))
    g.rectangle([ox + 42, oy + 4, ox + 66, oy + 16], fill=dark)
    g.rectangle([ox + 45, oy + 8, ox + 52, oy + 13],
                fill=(250, 214, 120))
    g.rectangle([ox + 55, oy + 8, ox + 63, oy + 13],
                fill=(250, 214, 120))
    g.line([ox + 54, oy + 4, ox + 54, oy], fill=dark, width=2)
    g.ellipse([ox + 51, oy, ox + 57, oy + 4], fill=(200, 40, 36))
    g.rectangle([ox + 38, oy + ht - 4, ox + 70, oy + ht], fill=dark)
    g.polygon([(ox + 76, oy + 13), (ox + 96, oy + 10),
               (ox + 112, oy + 10), (ox + 118, oy + 13),
               (ox + 112, oy + 16), (ox + 96, oy + 16),
               (ox + 78, oy + 16)], fill=dark)
    g.polygon([(ox + 104, oy + 10), (ox + 108, oy + 2),
               (ox + 113, oy + 2), (ox + 113, oy + 10)], fill=dark)
    g.polygon([(ox + 88, oy + 16), (ox + 96, oy + 16),
               (ox + 100, oy + 21), (ox + 92, oy + 21)],
              fill=(200, 40, 36))
    g.line([ox + 50, oy + ht - 4, ox + wd, oy + ht - 4],
           fill=(120, 130, 140), width=2)

def pic_chart_down(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(210, 218, 208))
    for idx, bar_h in enumerate((50, 38, 26, 16)):
        bx = ox + 9 + idx * 30
        g.rectangle([bx, oy + ht - bar_h, bx + 20, oy + ht],
                    fill=(52, 84, 140))
    g.line([ox + 4, oy + 10, ox + 45, oy + 24, ox + 81, oy + 18,
            ox + 121, oy + 42], fill=(200, 40, 36), width=5)
    g.polygon([(ox + 121, oy + 42), (ox + 107, oy + 41),
               (ox + 115, oy + 27)], fill=(200, 40, 36))

def pic_blast(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(188, 178, 168))
    g.rectangle([ox + 3, oy + ht - 8, ox + 125, oy + ht],
                fill=(44, 42, 46))
    for wx in (16, 40, 64, 88):
        g.rectangle([ox + wx, oy + ht - 5, ox + wx + 7, oy + ht - 2],
                    fill=(250, 214, 120))
    _burst(g, ox + 64, oy + 27, 17)

def pic_gavel(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(216, 206, 178))
    g.polygon([(ox + 31, oy + 6), (ox + 97, oy + 6), (ox + 97, oy + 18),
               (ox + 31, oy + 18)], fill=(96, 62, 34))
    g.polygon([(ox + 57, oy + 18), (ox + 71, oy + 18),
               (ox + 81, oy + 46), (ox + 67, oy + 46)],
              fill=(60, 40, 22))
    g.rectangle([ox + 53, oy + ht - 6, ox + 97, oy + ht],
                fill=(96, 62, 34))
    g.ellipse([ox + 118, oy + 12, ox + 142, oy + 36],
              fill=(200, 40, 36), outline=(120, 20, 20), width=2)

def pic_warning(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(240, 222, 130))
    g.polygon([(ox + 66, oy + 4), (ox + 130, oy + ht - 4),
               (ox + 2, oy + ht - 4)], fill=(220, 160, 20),
              outline=(24, 28, 38))
    g.rectangle([ox + 60, oy + 15, ox + 68, oy + 32],
                fill=(24, 28, 38))
    g.ellipse([ox + 60, oy + 37, ox + 68, oy + 46], fill=(24, 28, 38))

def pic_scales(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(196, 208, 220))
    g.rectangle([ox + 63, oy + 4, ox + 67, oy + ht - 4],
                fill=(24, 28, 38))
    g.rectangle([ox + 47, oy + ht - 4, ox + 83, oy + ht],
                fill=(24, 28, 38))
    g.line([ox + 19, oy + 9, ox + 111, oy + 9], fill=(24, 28, 38),
           width=4)
    for px in (19, 111):
        g.line([ox + px, oy + 9, ox + px - 12, oy + ht - 14],
               fill=(24, 28, 38), width=2)
        g.line([ox + px, oy + 9, ox + px + 12, oy + ht - 14],
               fill=(24, 28, 38), width=2)
        g.arc([ox + px - 12, oy + ht - 20, ox + px + 12, oy + ht - 4],
              0, 180, fill=(200, 40, 36), width=3)

def pic_ball(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(96, 160, 96))
    g.ellipse([ox + 43, oy + 4, ox + 85, oy + 52],
              fill=(255, 255, 255), outline=(24, 28, 38), width=2)
    g.polygon([(ox + 64, oy + 16), (ox + 74, oy + 24),
               (ox + 69, oy + 36), (ox + 59, oy + 36),
               (ox + 54, oy + 24)], fill=(24, 28, 38))
    for (lx, ly) in ((48, 8), (80, 8), (48, 46), (80, 46)):
        g.line([ox + 64, oy + 27, ox + lx, oy + ly],
               fill=(24, 28, 38), width=2)

def pic_moneybag(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(210, 226, 196))
    g.polygon([(ox + 49, oy + 4), (ox + 79, oy + 4), (ox + 73, oy + 12),
               (ox + 55, oy + 12)], fill=(96, 62, 34))
    g.ellipse([ox + 39, oy + 12, ox + 89, oy + 55],
              fill=(222, 184, 120), outline=(96, 62, 34), width=2)
    g.ellipse([ox + 97, oy + 34, ox + 115, oy + 55],
              fill=(250, 214, 120), outline=(150, 110, 40), width=1)
    g.ellipse([ox + 103, oy + 18, ox + 119, oy + 34],
              fill=(250, 214, 120), outline=(150, 110, 40), width=1)

def pic_shield(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(196, 208, 220))
    g.polygon([(ox + 44, oy + 4), (ox + 84, oy + 4), (ox + 84, oy + 30),
               (ox + 64, oy + 50), (ox + 44, oy + 30)],
              fill=(52, 84, 140), outline=(24, 28, 38))
    g.line([ox + 52, oy + 29, ox + 60, oy + 38, ox + 78, oy + 16],
           fill=(255, 255, 255), width=4)


STRIP_PICS = [pic_mine, pic_plane, pic_chart_down, pic_blast,
              pic_gavel, pic_warning, pic_scales, pic_ball,
              pic_moneybag, pic_shield]

def main():
    stories = HEROES + CARDS + ALSO
    total = len(stories)
    reg_counts, field_counts = {}, {}
    for (region, field) in all_stories():
        reg_counts[region] = reg_counts.get(region, 0) + 1
        field_counts[field] = field_counts.get(field, 0) + 1

    img = Image.new("RGB", (W, H), PAPER)
    d = RecDraw(ImageDraw.Draw(img))
    MX, RX = 12, W - 12

    # -------------------------------- masthead
    land = sum(1 for c in reg_counts if c != "GLO")
    eye_r = (f"{total} STORIES \u00b7 {land} REGIONS + SPACE \u00b7 "
             f"{len(field_counts)} FIELDS")
    d.text((MX, 7), "ONE DAY OF WORLD NEWS, ONE PICTURE",
           font=SANS_B(15), fill=RED)
    rw = d.textlength(eye_r, font=SANS_B(22))
    d.text((RX - rw, 3), eye_r, font=SANS_B(22), fill=INK)
    check_h("eyebrow left", "ONE DAY OF WORLD NEWS, ONE PICTURE",
            SANS_B(15), MX, RX - rw - 8)
    d.rectangle([MX, 30, RX, 33], fill=RED)
    date = "Monday 23 November 2026"
    dw = d.textlength(date, font=SERIF(76))
    d.text(((W - dw) / 2, 9), date, font=SERIF(76), fill=INK)
    d.line([MX, 110, RX, 110], fill=INK, width=2)
    LINES.append(((MX, 110, RX, 110), "date rule"))

    # -------------------------------- timeline: THE DAY IN UTC
    ty = 112
    d.rectangle([MX, ty, MX + 56, ty + 24], fill=RED)
    for j, s in enumerate(("THE DAY", "IN UTC")):
        tw = d.textlength(s, font=SANS_B(9))
        d.text((MX + 28 - tw / 2, ty + 2 + j * 10), s, font=SANS_B(9),
               fill=(255, 255, 255))
    col_x = MX + 64
    step = (RX - col_x) / 7
    for i, (tm, cap) in enumerate(TIMELINE):
        cx = col_x + i * step
        tw = d.textlength(tm, font=SANS_B(13))
        d.text((cx + step / 2 - tw / 2, ty), tm, font=SANS_B(13),
               fill=RED)
        lw = d.textlength(cap, font=SANS(10))
        d.text((cx + step / 2 - lw / 2, ty + 15), cap, font=SANS(10),
               fill=(52, 48, 42))
        check_h(f"tl cap {i}", cap, SANS(10), cx + step / 2 - lw / 2,
                cx + step - 4)
        if i:
            LINES.append(((cx - 5, ty + 3, cx - 5, ty + 21),
                          f"tl sep {i}"))
    d.line([MX, ty + 27, RX, ty + 27], fill=(150, 142, 126), width=1)
    LINES.append(((MX, ty + 27, RX, ty + 27), "timeline rule"))

    # -------------------------------- heroes + THE DAY IN NUMBERS rail
    hy = 145
    hw = 266
    for i, hero in enumerate(HEROES):
        place, region, field, head, deck, src, sure, big, biglab = hero
        x = MX + i * (hw + 14)
        TAG[0] = ("hero", i)
        HERO_SCENES[i](d, x, hy, hw, 100)
        TAG[0] = None
        band = f"{place.split(',')[0]} \u2014 {big} {biglab}"
        d.rectangle([x, hy + 78, x + hw, hy + 100], fill=(176, 32, 28))
        bw = d.textlength(band, font=SANS_B(13))
        d.text((x + (hw - bw) / 2, hy + 82), band, font=SANS_B(13),
               fill=(255, 255, 255))
        check_h(f"hero{i+1} band", band, SANS_B(13),
                x + (hw - bw) / 2, x + hw - 4)
        scol = SURE_COLORS[sure]
        ct = SURE_LABEL[sure]
        chw = d.textlength(ct, font=SANS_B(9)) + 10
        d.rounded_rectangle([x + hw - chw - 6, hy + 4, x + hw - 6,
                             hy + 20], radius=3, fill=(255, 253, 246),
                            outline=scol, width=1)
        d.text((x + hw - chw + 1, hy + 8), ct, font=SANS_B(9),
               fill=scol)
        ky = hy + 102
        col = REGIONS[region][1]
        d.ellipse([x, ky, x + 18, ky + 18], fill=col)
        num = str(i + 1)
        nw = d.textlength(num, font=SANS_B(12))
        d.text((x + 9 - nw / 2, ky + 2), num, font=SANS_B(12),
               fill=(255, 255, 255))
        kick = place.replace(", ", " \u00b7 ")
        d.text((x + 24, ky + 1), kick, font=SANS_B(15), fill=col)
        sw = d.textlength(src, font=SANS(12))
        d.text((x + hw - sw, ky + 3), src, font=SANS(12),
               fill=(110, 100, 88))
        check_h(f"hero{i+1} kicker", kick, SANS_B(15), x + 24,
                x + hw - sw - 6)
        text_block(d, x, ky + 14, head, SERIF(38), INK, hw - 2,
                   41, max_lines=2, tag=f"hero{i}")
        text_block(d, x, ky + 105, deck, SANS(15), (52, 48, 42), hw - 2,
                   17, max_lines=1, tag=f"herodeck{i}")
    # The rail: the day's biggest numbers at SERIF 55, captions 13px.
    rx0 = 852
    d.text((rx0, hy + 1), "THE DAY IN NUMBERS", font=SANS_B(13),
           fill=RED)
    d.line([rx0, hy + 19, RX, hy + 19], fill=(150, 142, 126), width=1)
    LINES.append(((rx0, hy + 19, RX, hy + 19), "rail rule"))
    rail = [(FIG["kyiv_region_killed"], "KILLED IN KYIV REGION", INK,
             hy + 21, "side"),
            (FIG["drones_overnight"], "DRONES IN ONE NIGHT", INK,
             hy + 64, "side"),
            (FIG["nvidia_jump"], "NVIDIA JUMP IN A DAY", RED,
             hy + 108, "below"),
            ("4-0", "EVERTON BEATEN", INK, hy + 182, "side")]
    for j, (rnum, rcap, rcol, top, mode) in enumerate(rail):
        bb = d.textbbox((0, 0), rnum, font=SERIF(55))
        d.text((rx0, top - bb[1]), rnum, font=SERIF(55), fill=rcol)
        num_w = bb[2] - bb[0]
        if mode == "side":
            text_block(d, rx0 + num_w + 8, top + 5, rcap, SANS(13),
                       (104, 96, 84), RX - rx0 - num_w - 8, 15,
                       max_lines=3, tag=f"rail{j}")
        else:
            d.text((rx0, top + 56), rcap, font=SANS(13),
                   fill=(104, 96, 84))
            check_h(f"rail{j} cap", rcap, SANS(13), rx0, RX)

    # -------------------------------- cards: 5 across x 2 rows
    cy = 373
    cw = (RX - MX - 40) // 5
    chh = 149
    for i, card in enumerate(CARDS):
        place, region, field, head, deck0, src, sure = card
        x = MX + (i % 5) * (cw + 10)
        yy0 = cy + (i // 5) * (chh + 6)
        tmp = Image.new("RGB", (190, 55), PAPER)
        td = ImageDraw.Draw(tmp)
        STRIP_PICS[i](td, 0, 0, 190, 55)
        img.paste(tmp, (x + 1, yy0 + 1))
        d.rounded_rectangle([x, yy0, x + cw, yy0 + 56], radius=4,
                            outline=(120, 112, 96), width=1)
        flag(d, CARD_FLAGS[i], x + 3, yy0 + 3, w=24, h=16)
        FLAGS.append(((x + 3, yy0 + 3, x + 27, yy0 + 19),
                      f"card{i+4} flag", ("card", i)))
        scol = SURE_COLORS[sure]
        ct = SURE_LABEL[sure]
        cwid = d.textlength(ct, font=SANS_B(9)) + 10
        d.rounded_rectangle([x + cw - cwid - 3, yy0 + 39, x + cw - 3,
                             yy0 + 52], radius=3, fill=(255, 253, 246),
                            outline=scol, width=1)
        d.text((x + cw - cwid + 2, yy0 + 42), ct, font=SANS_B(9),
               fill=scol)
        ov = CARD_OVERLAYS[i]
        if len(ov) <= 5:
            ov_font = SANS_B(28)
        elif len(ov) <= 9:
            ov_font = SANS_B(24)
        elif len(ov) <= 12:
            ov_font = SANS_B(20)
        else:
            ov_font = SANS_B(17)
        ow = d.textlength(ov, font=ov_font)
        d.text((x + cw - ow - 6, yy0 + 2), ov, font=ov_font,
               fill=(16, 20, 34), stroke_width=2,
               stroke_fill=(255, 253, 246))
        col = REGIONS[region][1]
        tab_t = f"{i + 4} \u00b7 {place}"
        tw = d.textlength(tab_t, font=SANS_B(9)) + 12
        d.rounded_rectangle([x + 3, yy0 + 39, x + 3 + tw, yy0 + 52],
                            radius=3, fill=col)
        d.text((x + 9, yy0 + 42), tab_t, font=SANS_B(9),
               fill=(255, 255, 255))
        check_h(f"card{i+4} tab", tab_t, SANS_B(9), x + 9, x + 184)
        d.text((x, yy0 + 59), field.upper(), font=SANS_B(11), fill=col)
        sw2 = d.textlength(src, font=SANS(12))
        d.text((x + cw - sw2, yy0 + 58), src, font=SANS(12),
               fill=(110, 100, 88))
        check_h(f"card{i+4} kicker", field.upper(), SANS_B(11), x,
                x + cw - sw2 - 6)
        text_block(d, x, yy0 + 67, head, SERIF(27), INK, cw - 4, 31,
                   max_lines=2, tag=f"card{i}")
        text_block(d, x, yy0 + 134, deck0, SANS(15), (52, 48, 42),
                   cw - 4, 17, max_lines=1, tag=f"carddeck{i}")

    # -------------------------------- bottom: map + ALSO two tiers
    by0 = 683
    d.line([MX, by0, RX, by0], fill=INK, width=2)
    LINES.append(((MX, by0, RX, by0), "bottom rule"))
    d.text((MX, by0 + 1), "WHERE IT HAPPENED", font=SANS_B(14),
           fill=RED)
    d.text((288, by0 + 1), "ALSO ON MONDAY 23 NOVEMBER",
           font=SANS_B(14), fill=RED)
    # The dot map (68x30 land grid, dark panel) with pins 1-13 for
    # the pictured stories: a gold dot at the true spot, a leader
    # line to the numbered circle where the cluster needs room.
    map_x, map_y, map_w, map_h = MX, by0 + 15, 240, 150
    d.rectangle([map_x, map_y, map_x + map_w, map_y + map_h],
                fill=(16, 26, 44))
    LINES.append(((map_x, map_y, map_x + map_w, map_y), "map top"))
    LINES.append(((map_x, map_y + map_h, map_x + map_w,
                   map_y + map_h), "map bottom"))
    cw2, chh2 = map_w / 68, map_h / 30
    for r, row in enumerate(LAND_MAP):
        for c, cell in enumerate(row):
            if cell != "#":
                continue
            cx = map_x + (c + 0.5) * cw2
            cy2 = map_y + (r + 0.5) * chh2
            d.ellipse([cx - 1.6, cy2 - 1.6, cx + 1.6, cy2 + 1.6],
                      fill=(120, 150, 190))
    for (num, lon, lat, dx, dy) in PINS:
        tx = map_x + (lon + 168) / 360 * map_w
        tyy = map_y + (78 - lat) / 134 * map_h
        if dx or dy:
            d.ellipse([tx - 2, tyy - 2, tx + 2, tyy + 2],
                      fill=(255, 214, 90))
            d.line([tx, tyy, tx + dx, tyy + dy], fill=(255, 214, 90),
                   width=1)
        px2, py2 = tx + dx, tyy + dy
        col = REGIONS[stories[num - 1][1]][1]
        d.ellipse([px2 - 9, py2 - 9, px2 + 9, py2 + 9], fill=col,
                  outline=(255, 255, 255), width=1)
        ns = str(num)
        nw = d.textlength(ns, font=SANS_B(10))
        TAG[0] = ("pin", num)
        d.text((px2 - nw / 2, py2 - 6), ns, font=SANS_B(10),
               fill=(255, 255, 255))
        TAG[0] = None
    # Region tally as the map legend (computed from the story table).
    leg_names = {"EUR": "Europe", "ASI": "Asia-Pacific",
                 "AME": "Americas", "MEA": "Middle East",
                 "AFR": "Africa", "OCE": "Oceania", "GLO": "Space"}
    for j, code in enumerate(("EUR", "ASI", "AME", "MEA", "AFR",
                              "OCE", "GLO")):
        lx = MX + (j % 2) * 122
        ly = map_y + map_h + 8 + (j // 2) * 18
        d.ellipse([lx, ly + 2, lx + 9, ly + 11],
                  fill=REGIONS[code][1])
        d.text((lx + 14, ly), f"{leg_names[code]} {reg_counts[code]}",
               font=SANS(11), fill=INK)
    # ALSO: two tiers, three columns in the space beside the map.
    cols_x = [288, 526, 776]
    cols_w = [226, 238, 236]
    groups = [(0, 7), (7, 14), (14, 21)]
    for ci, (a2, b2) in enumerate(groups):
        cx = cols_x[ci]
        yy = by0 + 15
        for idx in range(a2, b2):
            place, region, field, main_t, sub_t, src = ALSO[idx]
            colr = REGIONS[region][1]
            d.ellipse([cx, yy + 1, cx + 17, yy + 18], fill=colr)
            num = str(idx + 14)
            nw = d.textlength(num, font=SANS_B(11))
            d.text((cx + 8.5 - nw / 2, yy + 3), num, font=SANS_B(11),
                   fill=(255, 255, 255))
            d.text((cx + 22, yy), main_t, font=SANS_B(17), fill=INK)
            check_h(f"also{idx+14} main", main_t, SANS_B(17), cx + 22,
                    cx + cols_w[ci] - 4)
            sub_full = f"{sub_t} \u00b7 {src}"
            d.text((cx + 22, yy + 20), sub_full, font=SANS(13),
                   fill=(104, 96, 84))
            check_h(f"also{idx+14} sub", sub_full, SANS(13), cx + 22,
                    cx + cols_w[ci] - 4)
            yy += 36

    # -------------------------------- DATE CHECK box
    dy = 952
    d.rectangle([MX, dy, RX, dy + 45], fill=(253, 240, 238),
                outline=RED, width=2)
    LINES.append(((MX, dy, RX, dy), "datecheck top"))
    LINES.append(((MX, dy + 45, RX, dy + 45), "datecheck bottom"))
    d.rectangle([MX + 6, dy + 12, MX + 112, dy + 28], fill=RED)
    tw = d.textlength("DATE CHECK", font=SANS_B(11))
    d.text((MX + 59 - tw / 2, dy + 15), "DATE CHECK", font=SANS_B(11),
           fill=(255, 255, 255))
    dc = ("Left out, first reported before Monday: COP31 no-deal "
          "collapse (Sun 22), first failure since Copenhagen "
          + FIG["cop31_last_nodeal"] + ", " + FIG["cop31_gap_years"]
          + " years on; Iran's Bahrain strike \u2014 IRGC claims "
          + FIG["bahrain_radars_claim"]
          + " radars hit, Bahrain says " + FIG["bahrain_injured"]
          + " hurt, " + FIG["bahrain_critical"]
          + " critical (Sat 21); Shenzhen summit; \u2018El Chapo "
          "Isidro\u2019 seized (Fri 20); Banten toll "
          + FIG["banten_dead"]
          + " (Sat 21); Alcaraz, M\u00e1rquez, Liverpool 4-0 (Sun 22); "
          "BepiColombo in orbit (Sat 21). Not yet: the Kharg convoy; a COP32 "
          "date; the final Dymer toll; US strikes after the New Year.")
    text_block(d, MX + 122, dy + 4, dc, SANS(11), (52, 48, 42),
               RX - MX - 130, 14, max_lines=3, tag="datecheck")

    # -------------------------------- footer
    fy = 998
    left = ("Every story happened or was first reported on Mon 23 Nov "
            "2026; claims attributed.")
    d.text((MX, fy), left, font=SANS(11), fill=(52, 48, 42))
    srcs = []
    for s in [h[5] for h in HEROES] + [c[5] for c in CARDS] \
            + [b[5] for b in ALSO]:
        if s not in srcs:
            srcs.append(s)
    src_line = ("Sources: " + ", ".join(srcs[:5]) + f" + {len(srcs) - 5} "
                "more \u00b7 Original drawings")
    sw = d.textlength(src_line, font=SANS(11))
    d.text((RX - sw, fy), src_line, font=SANS(11), fill=(52, 48, 42))
    check_h("footer left", left, SANS(11), MX, RX - sw - 8)
    seg = [("HOW SURE:  ", SANS_B(11), INK),
           ("CONFIRMED", SANS_B(11), SURE_COLORS["C"]),
           (" 2+ outlets \u00b7 ", SANS(11), INK),
           ("REPORTED", SANS_B(11), SURE_COLORS["R"]),
           (" one outlet or claim", SANS(11), INK)]
    xx = MX
    for txt_s, fnt, fl in seg:
        d.text((xx, fy + 13), txt_s, font=fnt, fill=fl)
        bb = d.textbbox((0, 0), txt_s, font=fnt)
        xx += (bb[2] - bb[0]) + 5

    print(f"H-CHECKS: {len(H_CHECKS)} measured, "
          f"{sum(1 for _, v in H_CHECKS if v > 0)} over limit")
    for lab, v in H_CHECKS:
        if v > -30:
            print(f"  h-check {lab}: slack {-v:+.1f}px")
    for tb, plate, margins in BANNER_CHECK:
        print(f"BANNER bbox text={tb} plate={plate} "
              f"margins L/T/R/B={margins}")
    # Registry self-check: every figure display must appear verbatim in
    # the text actually drawn (check_numbers.py cannot see FIG
    # interpolations, so the page verifies its own registry here).
    drawn_text = " | ".join(s for _, s, _ in TEXT_BOXES)
    for _key, _disp in FIG.items():
        if _disp not in drawn_text:
            OVERFLOWS.append(f"REGISTRY-MISSING {_key}: '{_disp}' "
                             "not in drawn text")
    if OVERFLOWS:
        print("OVERFLOWS:", *OVERFLOWS, sep="\n  ")
    out = HERE / "entry.png"
    hits, near, pens = audit_text_boxes()
    gpens = audit_graphics()
    img.save(out, optimize=True)
    print("wrote", out, out.stat().st_size, "bytes; stories:", total,
          "; regions:", reg_counts, "; fields:", field_counts)
    if OVERFLOWS or hits or near or pens or gpens:
        raise SystemExit("AUDIT FAILED — see lines above")

if __name__ == "__main__":
    main()
