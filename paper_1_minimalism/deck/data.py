"""Numbers read straight out of the storyboard.

Every value in the deck is transcribed from `DHE Storyboard v2.dc.html`, not
recomputed.  For frames that carry long numeric series — bar heights, point
clouds — reading them from the source is safer than retyping them, so this
module parses them out of the inline styles at import time.
"""

import json
import pathlib
import re
from html.parser import HTMLParser

FRAMES = json.loads(
    (pathlib.Path(__file__).resolve().parent.parent / "build" / "frames.json")
    .read_text(encoding="utf-8"))
BY_SCREEN = {f["screen"]: f for f in FRAMES}


def _body(screen):
    return BY_SCREEN[screen]["body"]


def pct_series(screen, prop="height"):
    """Every `prop: N%` in the frame, in document order."""
    return [float(m) for m in
            re.findall(rf'{prop}:\s*([\d.]+)%', _body(screen))]


def px_series(screen, prop="width"):
    return [float(m) for m in
            re.findall(rf'{prop}:\s*([\d.]+)px', _body(screen))]


class _Spans(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "style" in a:
            self.out.append(a["style"])


def point_cloud(screen, colour):
    """Absolute-positioned dots of one colour: list of (left%, top%)."""
    p = _Spans()
    p.feed(_body(screen))
    pts = []
    for st in p.out:
        if colour.lower() not in st.lower() or "position:absolute" not in st.replace(" ", ""):
            continue
        l = re.search(r'left:\s*([\d.]+)%', st)
        t = re.search(r'top:\s*([\d.]+)%', st)
        if l and t:
            pts.append((float(l.group(1)), float(t.group(1))))
    return pts


_BAR = re.compile(
    r'flex:\s*1[^"]*?height:\s*([\d.]+)%[^"]*?background:\s*(#[0-9A-Fa-f]{6})'
    r'(?:[^"]*?opacity:\s*(\.?[\d.]+))?')


def flex_bars(screen):
    """`flex:1` bars of a chart: list of (height %, colour, opacity)."""
    out = []
    for m in _BAR.finditer(_body(screen)):
        out.append((float(m.group(1)), m.group(2).upper(),
                    float(m.group(3)) if m.group(3) else 1.0))
    return out


def abs_dots(screen):
    """Absolutely positioned round dots: (left%, top%, colour, opacity, size)."""
    p = _Spans()
    p.feed(_body(screen))
    out = []
    for st in p.out:
        flat = st.replace(" ", "")
        if "position:absolute" not in flat or "border-radius:50%" not in flat:
            continue
        l = re.search(r'left:\s*([\d.]+)%', st)
        t = re.search(r'top:\s*([\d.]+)%', st)
        c = re.search(r'background:\s*(#[0-9A-Fa-f]{6})', st)
        o = re.search(r'opacity:\s*(\.?[\d.]+)', st)
        w = re.search(r'width:\s*([\d.]+)px', st)
        if l and t and c:
            out.append((float(l.group(1)), float(t.group(1)),
                        c.group(1).upper(),
                        float(o.group(1)) if o else 1.0,
                        float(w.group(1)) if w else 18.0))
    return out


def polylines(screen):
    """SVG polylines of a plot: list of (colour, stroke, [(x%, y%), ...])."""
    out = []
    for m in re.finditer(
            r'<polyline\s+points="([^"]+)"[^>]*?stroke="(#[0-9A-Fa-f]{6})"'
            r'[^>]*?stroke-width="(\d+)"', _body(screen)):
        pts = [tuple(float(v) for v in p.split(","))
               for p in m.group(1).split()]
        out.append((m.group(2).upper(), int(m.group(3)), pts))
    return out
