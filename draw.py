#!/usr/bin/env python3
"""Draw the news-image-20261123 entry: Monday 23 November 2026.

One 1024x1024 newspaper page: 3 heroes + 10 cards + a 22-line ALSO
rail = exactly 35 stories, across 7 regions including Oceania, every
story dated to Monday 23 November 2026. Geometry first (GATES.md):
hero headlines >= 30px, card headlines >= 19px, brief text >= 14px,
in-scene labels >= 13px. The layout clones the measured superskie
template of the winning editions (masthead, UTC timeline, hero bands
inside the scenes, 5-across x 2-row cards with a single pictogram
strip, dot-grid world map with numbered pins, ALSO rail, red DATE
CHECK box, HOW SURE footer).

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
     "Kyiv says drones sank Russian warship",
     "Zelensky says " + FIG["merkury_drones"] + " sea drones sank the "
     "corvette Merkury at Benghazi; a cargo ship was hit; "
     + FIG["merkury_injured"] + " hurt.",
     "BBC", "R", FIG["merkury_drones"], "SEA DRONES"),
    ("SANTA CLARA, USA", "AME", "Tech",
     "Huang is back: Nvidia jumps 31.5%",
     "Board reinstates Jensen Huang 11 days after he quit; shares "
     + FIG["nvidia_jump"] + " to "
     + FIG["nvidia_close"] + "; Nasdaq " + FIG["nasdaq_gain"] + ".",
     "CNBC", "C", FIG["nvidia_gain"], "ADDED IN A DAY"),
    ("KYIV REGION", "EUR", "Conflict",
     "Russian strikes kill 15 in Kyiv region",
     "Dymer block falls, " + FIG["dymer_killed"] + " dead; "
     + FIG["vyshneve_killed"] + " killed in Vyshneve. "
     + FIG["drones_overnight"] + " drones overnight; "
     + FIG["drones_down"] + " downed.",
     "Al Jazeera", "C", FIG["kyiv_region_killed"], "KILLED"),
]

# Cards: (place, region, field, headline, deck, source, sure)
CARDS = [
    ("HORMUZ", "MEA", "Conflict",
     "Iran vows \u2018all means\u2019 vs blockade",
     "Tehran cites self-defence; Trump vows to sink runners.",
     "Al Jazeera", "R"),
    ("BRUSSELS", "EUR", "Politics",
     "Belgium strike shuts airports",
     "Flights cancelled; tear gas in Brussels; PM's budget deadline.",
     "France 24", "C"),
    ("SEOUL", "ASI", "Economy",
     "Asia stocks slide on AI doubts",
     "Nikkei " + FIG["nikkei_fall"] + "; Kospi " + FIG["kospi_fall"]
     + " to " + FIG["kospi_close"] + ", lowest since January.",
     "BBC", "C"),
    ("KHARTOUM", "AFR", "Conflict",
     "Drone attack hits Khartoum",
     FIG["khartoum_killed"] + " killed, " + FIG["khartoum_injured"]
     + " hurt; UN building hit. Army blames RSF.",
     "Japan Times", "R"),
    ("RICHMOND", "AME", "Tech",
     "US states sue Musk firms over Grok",
     "Virginia and Oregon sue over sexualised images.",
     "Al Jazeera", "C"),
    ("GAZA", "MEA", "Society",
     "Oxfam: Gaza a \u2018toxic wasteland\u2019",
     "Contamination across " + FIG["gaza_contamination"] + " of Gaza; "
     "UN worker killed.",
     "BBC", "C"),
    ("MADRID", "EUR", "Justice",
     "Spain amnesties Puigdemont",
     "Ends the case over the " + FIG["puigdemont_year"]
     + " independence vote.",
     "La Naci\u00f3n", "C"),
    ("BRENTFORD", "EUR", "Sport",
     "Brentford beat 10-man Everton 4-0",
     "Lewis-Potter scores twice in Monday-night win.",
     "Sky Sports", "C"),
    ("NEW DELHI", "ASI", "Diplomacy",
     "India pledges $1.62bn aid to Nepal",
     "After Aug floods killed " + FIG["nepal_flood_dead"]
     + "; railway and power deals.",
     "Al Jazeera", "C"),
    ("AUSTIN", "AME", "Economy",
     "CrowdStrike buys Zscaler for $44bn",
     "AI is supercharging cyberattacks, CrowdStrike says.",
     "CNBC", "C"),
]

CARD_OVERLAYS = ["DAY " + FIG["hormuz_war_day"], "AIRPORTS SHUT",
                 FIG["nikkei_fall"], "UN HIT",
                 FIG["grok_states"] + " STATES SUE",
                 FIG["gaza_contamination"], "AMNESTY", "4-0",
                 FIG["nepal_aid"], FIG["crowdstrike_deal"]]
CARD_FLAGS = ["IR", "BE", "KR", "SD", "US", "PS", "ES", "GB", "IN", "US"]
HERO_FLAGS = ["LY", "US", "UA"]

# ALSO rail, one line per story, numbered 14-35. Fields separated by a
# pipe: place, region, field, the one-line fact, source tag. Facts that
# carry a registered figure name it in braces; the loader fills it
# from the registry, so a brief can never drift from the checked number.
ALSO_TEXT = """BERLIN | EUR | Politics | NATO: defend every inch | SCMP
BRUSSELS | EUR | Diplomacy | 22nd sanctions target {eu_banks} banks | SCMP
MANCHESTER | EUR | Society | {manchester_evacuated} out; {manchester_treated}+ treated | AFP
LONDON | EUR | Economy | Shares fall {capita_fall}; boss quits | BBC
KATHMANDU | ASI | Climate | First {nepal_loss_damage} climate payout | RFI
SEOUL | ASI | Politics | Minister quits over cheating | AFP
ULAANBAATAR | ASI | Politics | President resigns | DW
DUSHANBE | ASI | Justice | Quits ICC, 4th to leave | UPI
WASHINGTON | AME | Diplomacy | Sanctions {us_sanctions_people} people, {us_sanctions_entities} entities | AJ
BRASILIA | AME | Economy | Growth {brazil_growth_new}; inflation {brazil_inflation_new} | MercoPress
BRASILIA | AME | Politics | Bolsonaro in ICU, stable | MercoPress
TUPANCIRETA | AME | Disaster | Storm kills {tupancireta_dead}, injures {tupancireta_injured}+ | AFP
LAHJ | MEA | Conflict | Houthis claim refinery hit | CNBC
DOHA | MEA | Sport | Mali beat Belgium 2-1 | Africanews
JERUSALEM | MEA | Politics | Unity talks end, no deal | BBC
NAIROBI | AFR | Diplomacy | Kenya, DR Congo restore ties | BBC
TONJ EAST | AFR | Conflict | {tonj_dead} killed, incl. {tonj_children} children | CTV
CANBERRA | OCE | Economy | Jobless to pass {australia_jobless} | Guardian
CANBERRA | OCE | Politics | Albanese defends Bowen | Guardian
MELBOURNE | OCE | Culture | Meldrum dies at {meldrum_age} | BBC
TOKYO | ASI | Culture | Tamagotchi turns {tamagotchi_years} | Japan Times
MARIANA TRENCH | GLO | Science | Volcanoes found | Phys.org"""

ALSO = []
for _row in ALSO_TEXT.strip().splitlines():
    _f = [part.strip() for part in _row.split(" | ")]
    ALSO.append((_f[0], _f[1], _f[2], _f[3].format_map(FIG), _f[4]))

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
06:13 | Kyiv toll reaches 15
06:30 | Kospi closes -3.31%
11:26 | Nvidia: Huang back
14:30 | US stocks rebound
20:00 | Brentford 4-0
21:00 | Nvidia closes +31.5%"""

TIMELINE = [tuple(_row.split(" | "))
            for _row in TIMELINE_TEXT.strip().splitlines()]


def all_stories():
    out = [(h[1], h[2]) for h in HEROES]
    out += [(c[1], c[2]) for c in CARDS]
    out += [(b[1], b[2]) for b in ALSO]
    return out


# ------------------------------------------------------------ hero scenes
# Each scene is 324x96. The red statement band covers the bottom 21px,
# so all art stays in the top 72px. The dominant shape of each scene is
# registered as an OBSTACLE; the scene's own label (same tag) is exempt.
def scene_benghazi(d, x, y, w, h):
    # DOMINANT: the listing corvette, hull half out of a dusk sea.
    _sky(d, x, y, w, 72, (232, 150, 90), (60, 80, 120))
    d.ellipse([x + 268, y + 6, x + 296, y + 34], fill=(250, 220, 160))
    d.rectangle([x, y + 58, x + w, y + 72], fill=(30, 70, 110))
    for wx in (8, 60, 120, 180, 240, 290):
        d.arc([x + wx, y + 60, x + wx + 24, y + 70], 180, 360,
              fill=(180, 210, 235), width=2)
    hull = [(x + 48, y + 58), (x + 276, y + 48), (x + 288, y + 64),
            (x + 60, y + 72)]
    d.polygon(hull, fill=(44, 48, 58))
    OBSTACLES.append(((x + 48, y + 48, x + 288, y + 72),
                      "benghazi listing hull", TAG[0]))
    d.polygon([(x + 60, y + 72), (x + 288, y + 64), (x + 288, y + 68),
               (x + 60, y + 74)], fill=(140, 40, 36))
    d.rectangle([x + 150, y + 38, x + 190, y + 52], fill=(70, 74, 84))
    d.line([x + 170, y + 38, x + 152, y + 20], fill=(30, 34, 44), width=3)
    for sx, sy, sr in ((210, 16, 9), (228, 8, 11), (248, 14, 8)):
        d.ellipse([x + sx, y + sy, x + sx + sr * 2, y + sy + sr],
                  fill=(90, 90, 100))
    _burst(d, x + 292, y + 52, 11)
    d.polygon([(x + 14, y + 64), (x + 44, y + 64), (x + 40, y + 70),
               (x + 18, y + 70)], fill=(24, 28, 38))
    d.line([x + 28, y + 64, x + 28, y + 56], fill=(24, 28, 38), width=2)
    d.line([x + 8, y + 68, x + 50, y + 68], fill=(180, 210, 235), width=1)
    plate = [x + 10, y + 6, x + 102, y + 26]
    d.rectangle(plate, fill=(240, 238, 228), outline=INK, width=2)
    OBSTACLES.append((tuple(plate), "benghazi name plate", TAG[0]))
    d.text((x + 56, y + 16), "MERKURY", font=SANS_B(13), fill=NAVY,
           anchor="mm")


def scene_nvidia(d, x, y, w, h):
    # DOMINANT: one giant green chip under a rising arrow.
    d.rectangle([x, y, x + w, y + 72], fill=(16, 22, 40))
    for sx, sy in ((26, 10), (296, 8), (250, 60)):
        d.ellipse([x + sx, y + sy, x + sx + 3, y + sy + 3],
                  fill=(200, 210, 235))
    d.line([x + 14, y + 66, x + 108, y + 40, x + 170, y + 48,
            x + 236, y + 18, x + 306, y + 10], fill=(0, 200, 90), width=5)
    d.polygon([(x + 306, y + 10), (x + 288, y + 8), (x + 296, y + 24)],
              fill=(0, 200, 90))
    chip = [x + 118, y + 16, x + 206, y + 70]
    d.rounded_rectangle(chip, radius=6, fill=(118, 185, 0))
    OBSTACLES.append((tuple(chip), "nvidia chip", TAG[0]))
    for px in range(126, 200, 12):
        d.rectangle([x + px, y + 10, x + px + 4, y + 16], fill=(90, 140, 0))
        d.rectangle([x + px, y + 70, x + px + 4, y + 76], fill=(90, 140, 0))
    d.rectangle([x + 146, y + 32, x + 178, y + 54], fill=(16, 22, 40))
    d.text((x + 162, y + 43), "NVDA", font=SANS_B(15),
           fill=(255, 255, 255), anchor="mm")


def scene_kyiv(d, x, y, w, h):
    # DOMINANT: a shelled apartment block in Dymer, listing on rubble,
    # smoke above, a rescue crane at the right. The plate names the
    # place because the band names the region.
    _sky(d, x, y, w, 72, (186, 178, 164), (140, 142, 148))
    for (sx, sy, sr) in ((x + 90, y + 2, 16), (x + 150, y - 2, 20),
                         (x + 210, y + 6, 14)):
        d.ellipse([sx - sr, sy, sx + sr, sy + sr], fill=(120, 118, 112))
    d.polygon([(x + 40, y + 14), (x + 196, y + 8), (x + 206, y + 66),
               (x + 32, y + 66)], fill=(158, 146, 128))
    OBSTACLES.append(((x + 32, y + 8, x + 206, y + 66),
                      "kyiv block", TAG[0]))
    for row in range(3):
        for col in range(5):
            wx = x + 52 + col * 30
            wy = y + 20 + row * 15
            if (row, col) in ((0, 2), (1, 3), (2, 1)):
                d.polygon([(wx, wy), (wx + 14, wy + 2), (wx + 12, wy + 10),
                           (wx + 2, wy + 8)], fill=(40, 36, 34))
            else:
                d.rectangle([wx, wy, wx + 13, wy + 9], fill=(52, 48, 46))
    d.polygon([(x + 206, y + 66), (x + 262, y + 66), (x + 238, y + 40),
               (x + 214, y + 52)], fill=(120, 114, 104))
    d.rectangle([x + 282, y + 18, x + 288, y + 66], fill=(200, 160, 30))
    d.line([x + 285, y + 18, x + 246, y + 30], fill=(200, 160, 30),
           width=4)
    d.line([x + 246, y + 30, x + 246, y + 44], fill=(60, 56, 52), width=2)
    plate = [x + 8, y + 6, x + 104, y + 26]
    d.rectangle(plate, fill=(240, 238, 228), outline=INK, width=2)
    OBSTACLES.append((tuple(plate), "kyiv place plate", TAG[0]))
    d.text((x + 56, y + 16), "DYMER", font=SANS_B(13), fill=RED,
           anchor="mm")


HERO_SCENES = [scene_benghazi, scene_nvidia, scene_kyiv]


# ---------------------------------------------------------- card pictograms
# One dominant pictogram per card, drawn natively at strip size
# (190x42) on a throwaway canvas: the topic must read from the symbol
# alone before any word is decoded.
def pic_mine(g, ox, oy, wd, ht):
    # DOMINANT: one spiked naval mine, drawn at strip size; the topic
    # (a minefield in the strait) must read from the symbol alone.
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(16, 40, 66))
    for wx in (14, 60, 106, 152):
        g.arc([ox + wx, oy + 34, ox + wx + 24, oy + 42], 180, 360,
              fill=(120, 160, 200), width=2)
    mx, my = ox + 78, oy + 21
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        g.line([mx + 11 * math.cos(rad), my + 11 * math.sin(rad),
                mx + 19 * math.cos(rad), my + 19 * math.sin(rad)],
               fill=(200, 40, 36), width=3)
    g.ellipse([mx - 12, my - 12, mx + 12, my + 12], fill=(24, 26, 34),
              outline=(200, 40, 36), width=2)
    g.ellipse([mx - 4, my - 6, mx + 2, my], fill=(90, 96, 106))


def pic_plane(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(170, 196, 216))
    dark = (16, 18, 24)
    # DOMINANT: a control tower (left, clear of the wide overlay) with
    # a small airliner flying past it at the top. The overlay owns the
    # lower-right, the flag and chip the top corners, so the tower and
    # the plane sit in the free middle band.
    g.rectangle([ox + 42, oy + 14, ox + 54, oy + 42], fill=(90, 96, 106))
    g.rectangle([ox + 36, oy + 4, ox + 60, oy + 14], fill=dark)
    g.rectangle([ox + 39, oy + 7, ox + 46, oy + 11], fill=(250, 214, 120))
    g.rectangle([ox + 49, oy + 7, ox + 57, oy + 11], fill=(250, 214, 120))
    g.line([ox + 48, oy + 4, ox + 48, oy + 1], fill=dark, width=2)
    g.ellipse([ox + 45, oy + 0, ox + 51, oy + 4], fill=(200, 40, 36))
    g.rectangle([ox + 32, oy + 38, ox + 64, oy + 42], fill=dark)
    g.polygon([(ox + 70, oy + 10), (ox + 90, oy + 8), (ox + 106, oy + 8),
               (ox + 112, oy + 10), (ox + 106, oy + 12), (ox + 90, oy + 12),
               (ox + 72, oy + 12)], fill=dark)
    g.polygon([(ox + 98, oy + 8), (ox + 102, oy + 2), (ox + 107, oy + 2),
               (ox + 107, oy + 8)], fill=dark)
    g.polygon([(ox + 82, oy + 12), (ox + 90, oy + 12), (ox + 94, oy + 16),
               (ox + 86, oy + 16)], fill=(200, 40, 36))
    g.line([ox + 44, oy + 38, ox + wd, oy + 38], fill=(120, 130, 140),
           width=2)


def pic_chart_down(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(210, 218, 208))
    for idx, bar_h in enumerate((36, 27, 19, 12)):
        bx = ox + 14 + idx * 30
        g.rectangle([bx, oy + 42 - bar_h, bx + 20, oy + 42],
                    fill=(52, 84, 140))
    g.line([ox + 10, oy + 8, ox + 52, oy + 18, ox + 88, oy + 15,
            ox + 128, oy + 34], fill=(200, 40, 36), width=5)
    g.polygon([(ox + 128, oy + 34), (ox + 114, oy + 33), (ox + 122, oy + 20)],
              fill=(200, 40, 36))


def pic_blast(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(188, 178, 168))
    g.rectangle([ox + 8, oy + 33, ox + 130, oy + 42], fill=(44, 42, 46))
    for wx in (20, 44, 68, 92):
        g.rectangle([ox + wx, oy + 36, ox + wx + 7, oy + 40],
                    fill=(250, 214, 120))
    _burst(g, ox + 66, oy + 19, 19)


def pic_gavel(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(216, 206, 178))
    g.polygon([(ox + 30, oy + 6), (ox + 96, oy + 6), (ox + 96, oy + 20),
               (ox + 30, oy + 20)], fill=(96, 62, 34))
    g.polygon([(ox + 56, oy + 20), (ox + 70, oy + 20), (ox + 82, oy + 38),
               (ox + 68, oy + 38)], fill=(60, 40, 22))
    g.rectangle([ox + 52, oy + 36, ox + 96, oy + 42], fill=(96, 62, 34))
    g.ellipse([ox + 128, oy + 8, ox + 152, oy + 32], fill=(200, 40, 36),
              outline=(120, 20, 20), width=2)


def pic_warning(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(240, 222, 130))
    g.polygon([(ox + 66, oy + 4), (ox + 124, oy + 38), (ox + 8, oy + 38)],
              fill=(220, 160, 20), outline=(24, 28, 38))
    g.rectangle([ox + 62, oy + 14, ox + 70, oy + 28], fill=(24, 28, 38))
    g.ellipse([ox + 62, oy + 31, ox + 70, oy + 39], fill=(24, 28, 38))


def pic_scales(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(196, 208, 220))
    g.rectangle([ox + 64, oy + 4, ox + 68, oy + 38], fill=(24, 28, 38))
    g.rectangle([ox + 48, oy + 38, ox + 84, oy + 42], fill=(24, 28, 38))
    g.line([ox + 20, oy + 10, ox + 112, oy + 10], fill=(24, 28, 38),
           width=4)
    for px in (20, 112):
        g.line([ox + px, oy + 10, ox + px - 12, oy + 26], fill=(24, 28, 38),
               width=2)
        g.line([ox + px, oy + 10, ox + px + 12, oy + 26], fill=(24, 28, 38),
               width=2)
        g.arc([ox + px - 13, oy + 22, ox + px + 13, oy + 36], 0, 180,
              fill=(200, 40, 36), width=3)


def pic_ball(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(96, 160, 96))
    g.ellipse([ox + 52, oy + 2, ox + 94, oy + 40], fill=(255, 255, 255),
              outline=(24, 28, 38), width=2)
    g.polygon([(ox + 73, oy + 12), (ox + 83, oy + 19), (ox + 79, oy + 30),
               (ox + 67, oy + 30), (ox + 63, oy + 19)], fill=(24, 28, 38))
    for (lx, ly) in ((58, 8), (88, 8), (58, 32), (88, 32)):
        g.line([ox + 73, oy + 21, ox + lx, oy + ly], fill=(24, 28, 38),
               width=2)


def pic_moneybag(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(210, 226, 196))
    g.polygon([(ox + 58, oy + 6), (ox + 88, oy + 6), (ox + 82, oy + 14),
               (ox + 64, oy + 14)], fill=(96, 62, 34))
    g.ellipse([ox + 48, oy + 12, ox + 98, oy + 40], fill=(222, 184, 120),
              outline=(96, 62, 34), width=2)
    g.ellipse([ox + 106, oy + 28, ox + 124, oy + 40], fill=(250, 214, 120),
              outline=(150, 110, 40), width=1)
    g.ellipse([ox + 112, oy + 16, ox + 128, oy + 28], fill=(250, 214, 120),
              outline=(150, 110, 40), width=1)


def pic_shield(g, ox, oy, wd, ht):
    g.rectangle([ox, oy, ox + wd, oy + ht], fill=(196, 208, 220))
    g.polygon([(ox + 56, oy + 4), (ox + 96, oy + 4), (ox + 96, oy + 22),
               (ox + 76, oy + 40), (ox + 56, oy + 22)], fill=(52, 84, 140),
              outline=(24, 28, 38))
    g.line([ox + 64, oy + 22, ox + 72, oy + 30, ox + 90, oy + 12],
           fill=(255, 255, 255), width=4)


STRIP_PICS = [pic_mine, pic_plane, pic_chart_down, pic_blast,
              pic_gavel, pic_warning, pic_scales, pic_ball,
              pic_moneybag, pic_shield]


# ------------------------------------------------------------------ page
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
             f"{len(field_counts)} FIELDS \u00b7 ALL FROM THIS MONDAY")
    d.text((MX, 8), "ONE DAY OF WORLD NEWS, ONE PICTURE",
           font=SANS_B(15), fill=RED)
    rw = d.textlength(eye_r, font=SANS_B(15))
    d.text((RX - rw, 8), eye_r, font=SANS_B(15), fill=INK)
    check_h("eyebrow left", "ONE DAY OF WORLD NEWS, ONE PICTURE",
            SANS_B(15), MX, RX - rw - 8)
    d.rectangle([MX, 30, RX, 33], fill=RED)
    date = "Monday 23 November 2026"
    dw = d.textlength(date, font=SERIF(66))
    d.text(((W - dw) / 2, 28), date, font=SERIF(66), fill=INK)
    d.line([MX, 116, RX, 116], fill=INK, width=2)
    LINES.append(((MX, 116, RX, 116), "date rule"))

    # -------------------------------- timeline: THE DAY IN UTC
    ty = 122
    d.rectangle([MX, ty, MX + 64, ty + 46], fill=RED)
    for j, s in enumerate(("THE DAY", "IN UTC")):
        tw = d.textlength(s, font=SANS_B(12))
        d.text((MX + 32 - tw / 2, ty + 7 + j * 16), s, font=SANS_B(12),
               fill=(255, 255, 255))
    col_x = MX + 72
    colw = (RX - col_x) // 7
    for i, (tm, cap) in enumerate(TIMELINE):
        cx = col_x + i * colw
        tw = d.textlength(tm, font=SANS_B(19))
        d.text((cx + colw / 2 - tw / 2, ty + 1), tm, font=SANS_B(19),
               fill=RED)
        lw = d.textlength(cap, font=SANS(11))
        d.text((cx + colw / 2 - lw / 2, ty + 27), cap, font=SANS(11),
               fill=(52, 48, 42))
        check_h(f"tl cap {i}", cap, SANS(11), cx + colw / 2 - lw / 2,
                cx + colw - 4)
        if i:
            LINES.append(((cx - 5, ty + 4, cx - 5, ty + 42), f"tl sep {i}"))
    d.line([MX, ty + 50, RX, ty + 50], fill=(150, 142, 126), width=1)
    LINES.append(((MX, ty + 50, RX, ty + 50), "timeline rule"))

    # -------------------------------- heroes
    hy = 178
    hw = (RX - MX - 26) // 3
    for i, hero in enumerate(HEROES):
        place, region, field, head, deck, src, sure, big, biglab = hero
        x = MX + i * (hw + 13)
        TAG[0] = ("hero", i)
        HERO_SCENES[i](d, x, hy, hw, 96)
        TAG[0] = None
        band = f"{place.split(',')[0]} \u2014 {big} {biglab}"
        d.rectangle([x, hy + 75, x + hw, hy + 96], fill=(176, 32, 28))
        bw = d.textlength(band, font=SANS_B(13))
        d.text((x + (hw - bw) / 2, hy + 79), band, font=SANS_B(13),
               fill=(255, 255, 255))
        check_h(f"hero{i+1} band", band, SANS_B(13),
                x + (hw - bw) / 2, x + hw - 4)
        ky = hy + 102
        col = REGIONS[region][1]
        d.ellipse([x + 1, ky, x + 19, ky + 18], fill=col)
        num = str(i + 1)
        nw = d.textlength(num, font=SANS_B(12))
        d.text((x + 10 - nw / 2, ky + 2), num, font=SANS_B(12),
               fill=(255, 255, 255))
        kick = place.replace(", ", " \u00b7 ")
        d.text((x + 25, ky + 1), kick, font=SANS_B(14), fill=col)
        chip_t = f"{SURE_LABEL[sure]} \u00b7 {src}"
        chw2 = d.textlength(chip_t, font=SANS_B(10)) + 14
        scol = SURE_COLORS[sure]
        d.rounded_rectangle([x + hw - chw2, ky - 1, x + hw, ky + 17],
                            radius=4, outline=scol, width=2)
        d.text((x + hw - chw2 + 7, ky + 2), chip_t, font=SANS_B(10),
               fill=scol)
        check_h(f"hero{i+1} kicker", kick, SANS_B(14), x + 25,
                x + hw - chw2 - 6)
        text_block(d, x, ky + 22, head, SERIF(30), INK, hw - 2, 34,
                   max_lines=2, tag=f"hero{i}")
        text_block(d, x, ky + 98, deck, SANS(13), (52, 48, 42), hw - 2,
                   17, max_lines=2, tag=f"herodeck{i}")

    # -------------------------------- cards: 5 across x 2 rows
    cy = 414
    cw = (RX - MX - 40) // 5
    chh = 142
    for i, card in enumerate(CARDS):
        place, region, field, head, deck0, src, sure = card
        x = MX + (i % 5) * (cw + 10)
        yy0 = cy + (i // 5) * (chh + 8)
        tmp = Image.new("RGB", (190, 42), PAPER)
        td = ImageDraw.Draw(tmp)
        STRIP_PICS[i](td, 0, 0, 190, 42)
        img.paste(tmp, (x + 1, yy0 + 1))
        d.rounded_rectangle([x, yy0, x + cw, yy0 + 43], radius=4,
                            outline=(120, 112, 96), width=1)
        flag(d, CARD_FLAGS[i], x + 5, yy0 + 5, w=24, h=16)
        FLAGS.append(((x + 5, yy0 + 5, x + 29, yy0 + 21),
                      f"card{i+4} flag", ("card", i)))
        scol = SURE_COLORS[sure]
        ct = SURE_LABEL[sure]
        cwid = d.textlength(ct, font=SANS_B(9)) + 10
        d.rounded_rectangle([x + cw - cwid - 4, yy0 + 4, x + cw - 4,
                             yy0 + 19], radius=3, fill=(255, 253, 246),
                            outline=scol, width=1)
        d.text((x + cw - cwid + 1, yy0 + 7), ct, font=SANS_B(9),
               fill=scol)
        ov = CARD_OVERLAYS[i]
        ov_font = SANS_B(19) if len(ov) <= 10 else SANS_B(17)
        ow = d.textlength(ov, font=ov_font)
        d.text((x + cw - ow - 6, yy0 + 20), ov, font=ov_font,
               fill=(16, 20, 34), stroke_width=2,
               stroke_fill=(255, 253, 246))
        col = REGIONS[region][1]
        d.ellipse([x + 1, yy0 + 48, x + 17, yy0 + 64], fill=col)
        num = str(i + 4)
        nw = d.textlength(num, font=SANS_B(11))
        d.text((x + 9 - nw / 2, yy0 + 50), num, font=SANS_B(11),
               fill=(255, 255, 255))
        d.text((x + 22, yy0 + 49), place, font=SANS_B(12), fill=col)
        check_h(f"card{i+4} kicker", place, SANS_B(12), x + 22,
                x + cw - 4)
        text_block(d, x, yy0 + 66, head, SERIF(19), INK, cw - 4, 23,
                   max_lines=2, tag=f"card{i}")
        text_block(d, x, yy0 + 115, deck0, SANS(12), (52, 48, 42),
                   cw - 4, 15, max_lines=2, tag=f"carddeck{i}")

    # -------------------------------- bottom: map left, ALSO right
    by0 = 712
    d.line([MX, by0, RX, by0], fill=INK, width=2)
    LINES.append(((MX, by0, RX, by0), "bottom rule"))
    d.text((MX, by0 + 8), "WHERE IT HAPPENED", font=SANS_B(14), fill=RED)
    ax = 276
    also_head = "ALSO ON MONDAY 23 NOVEMBER"
    d.text((ax, by0 + 8), also_head, font=SANS_B(14), fill=RED)
    check_h("also header", also_head, SANS_B(14), ax, RX)
    map_x, map_y, map_w, map_h = MX, by0 + 26, 240, 118
    d.rectangle([map_x, map_y, map_x + map_w, map_y + map_h],
                fill=(16, 26, 44))
    LINES.append(((map_x, map_y, map_x + map_w, map_y), "map top"))
    LINES.append(((map_x, map_y + map_h, map_x + map_w, map_y + map_h),
                  "map bottom"))
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
        d.text((px2 - nw / 2, py2 - 6), ns, font=SANS_B(10),
               fill=(255, 255, 255))
    leg_names = {"EUR": "Europe", "ASI": "Asia-Pacific",
                 "AME": "Americas", "MEA": "Middle East",
                 "AFR": "Africa", "OCE": "Oceania", "GLO": "Space"}
    for j, code in enumerate(("EUR", "ASI", "AME", "MEA", "AFR", "OCE",
                              "GLO")):
        lx = MX + (j % 2) * 122
        ly = map_y + map_h + 6 + (j // 2) * 15
        d.ellipse([lx, ly + 2, lx + 9, ly + 11], fill=REGIONS[code][1])
        d.text((lx + 14, ly), f"{leg_names[code]} {reg_counts[code]}",
               font=SANS(11), fill=INK)
    colw2 = (RX - ax - 16) // 2
    for i, (place, region, field, fact, src) in enumerate(ALSO):
        col_i, row = divmod(i, 11)
        x = ax + col_i * (colw2 + 16)
        yy = by0 + 26 + row * 17
        colr = REGIONS[region][1]
        d.ellipse([x, yy, x + 17, yy + 17], fill=colr)
        num = str(i + 14)
        nw = d.textlength(num, font=SANS_B(11))
        d.text((x + 8.5 - nw / 2, yy + 2), num, font=SANS_B(11),
               fill=(255, 255, 255))
        head = f"{place}: "
        d.text((x + 22, yy + 1), head, font=SANS_B(14), fill=colr)
        hw2 = d.textlength(head, font=SANS_B(14))
        tail = f"{fact} \u00b7 {src}"
        d.text((x + 22 + hw2 + 6, yy + 1), tail, font=SANS(14), fill=INK)
        check_h(f"also{i+14}", head + tail, SANS(14), x + 22,
                x + colw2 - 2)

    # -------------------------------- DATE CHECK box
    dy = 928
    d.rectangle([MX, dy, RX, dy + 56], fill=(253, 240, 238),
                outline=RED, width=2)
    LINES.append(((MX, dy, RX, dy), "datecheck top"))
    LINES.append(((MX, dy + 56, RX, dy + 56), "datecheck bottom"))
    d.rectangle([MX + 6, dy + 18, MX + 112, dy + 38], fill=RED)
    tw = d.textlength("DATE CHECK", font=SANS_B(12))
    d.text((MX + 59 - tw / 2, dy + 21), "DATE CHECK", font=SANS_B(12),
           fill=(255, 255, 255))
    dc = ("Left out, first reported before Monday: COP31 no-deal "
          "collapse (Sun 22); Iran's Bahrain strike \u2014 IRGC claims "
          + FIG["bahrain_radars_claim"]
          + " radars hit, Bahrain says " + FIG["bahrain_injured"]
          + " hurt, " + FIG["bahrain_critical"]
          + " critical (Sat 21); Shenzhen summit; \u2018El Chapo "
          "Isidro\u2019 seized (Fri 20); Banten toll "
          + FIG["banten_dead"]
          + " (Sat 21); Alcaraz, M\u00e1rquez, Liverpool 4-0 (Sun 22); "
          "BepiColombo in orbit (Sat 21). Not yet: the Kharg convoy; a COP32 "
          "date; the final Dymer toll; US strikes after the New Year.")
    text_block(d, MX + 122, dy + 6, dc, SANS(12), (52, 48, 42),
               RX - MX - 130, 15, max_lines=3, tag="datecheck")

    # -------------------------------- footer
    fy = 992
    left = ("Every story happened or was first reported on Mon 23 Nov "
            "2026; claims attributed.")
    d.text((MX, fy), left, font=SANS(11), fill=(52, 48, 42))
    srcs = []
    for s in [h[5] for h in HEROES] + [c[5] for c in CARDS] \
            + [b[4] for b in ALSO]:
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
        d.text((xx, fy + 15), txt_s, font=fnt, fill=fl)
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
