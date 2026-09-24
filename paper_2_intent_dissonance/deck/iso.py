"""The storyboard's drawing kit, ported one to one.

The 3b1b storyboard draws every scene with a dozen helpers (`box`, `lab`,
`flow`, `tower`, …) that turn a scene state into SVG, and then lets CSS
transitions carry each element from one click to the next.  This module is the
same kit, but instead of SVG it returns *prims* — flat dicts that describe one
element in one state: its outline in storyboard pixels, colours, opacity and
the transition timing (`delay`, `dur`) the storyboard gives it.

A scene function returns one list of prims per step; `stage.Stage` interpolates
between two such lists frame by frame, the way the browser would.  Keys are
stable across steps, so an element that grows, recolours or moves is the same
key in both states.

Nothing here imports Manim.
"""

import math

import numpy as np

from deck.tokens import K, FIG_BODY, FIG_TOP, FIG_HEAD

# ---------------------------------------------------------- isometry -------
S = 45.0
CX = S * 0.8660254
CY = S * 0.5


def P(x, y, z=0.0):
    """World cell -> storyboard px.  x runs down-right, y down-left, z up."""
    return ((x - y) * CX, (x + y) * CY - z * S)


def shade(hex_, f):
    n = int(hex_[1:], 16)
    c = [max(0, min(255, round(((n >> s) & 255) * f))) for s in (16, 8, 0)]
    return "#%02X%02X%02X" % tuple(c)


def _pts(seq):
    return np.array([[p[0], p[1]] for p in seq], dtype=float)


# ---------------------------------------------------------- primitives -----

def poly(k, pts, fill=None, fo=1.0, stroke=K["paper"], sw=2.2, dash=None,
         op=1.0, delay=0.0, dur=1.6, closed=True, anim=None, base=None,
         grp=None, reveal=1.0, cap="round"):
    return {"t": "poly", "k": k, "pts": _pts(pts), "fill": fill,
            "fo": fo if fill else 0.0, "stroke": stroke, "sw": sw,
            "dash": dash, "op": op, "delay": delay, "dur": dur,
            "closed": closed, "anim": anim, "grp": grp or k,
            "base": None if base is None else _pts(base), "reveal": reveal,
            "gop": 1.0, "gdl": 0.0, "gdu": 1.0, "tag": None}


def text(k, x, y, s, size=30, fill=K["paper"], anchor="start", op=1.0,
         italic=False, font="serif", delay=0.0, dur=1.2, spacing=0.0):
    """`size` is the final CSS px of the element in its own space."""
    return {"t": "text", "k": k, "x": float(x), "y": float(y), "s": s,
            "size": float(size), "fill": fill, "anchor": anchor, "op": op,
            "italic": italic, "font": font, "delay": delay, "dur": dur,
            "spacing": spacing, "gop": 1.0, "gdl": 0.0, "gdu": 1.0,
            "anim": None, "tag": None}


def flow(k, pts, n, dur, draw, op=1.0, delay=0.0):
    """`n` copies of `draw()` running along `pts` — SVG animateMotion.

    Item `i` starts `i·dur/n` early, fades in over the first 12 % of the path
    and out over the last 12 %, at constant speed along the path.
    """
    items = draw()
    return {"t": "flow", "k": k, "path": _pts(pts), "n": n, "period": dur,
            "items": items, "op": op, "delay": delay, "dur": 1.2,
            "gop": 1.0, "gdl": 0.0, "gdu": 1.0, "anim": None, "tag": None}


# ---------------------------------------------------------- storyboard kit --

def box(k, x, y, w, d, h, c, z=0.0, op=1.0, delay=0.0, dur=1.6, sw=2.2,
        stroke=None, empty=False, fo=1.0, anim=None):
    """An isometric block: left, right and top faces, darker shades of `c`
    filled, outlined in `c` itself — the 3b1b look of the storyboard."""
    hh = max(h, 0.001)

    def faces(hz):
        t = [P(x, y, z + hz), P(x + w, y, z + hz), P(x + w, y + d, z + hz),
             P(x, y + d, z + hz)]
        l = [P(x, y + d, z + hz), P(x + w, y + d, z + hz), P(x + w, y + d, z),
             P(x, y + d, z)]
        r = [P(x + w, y, z + hz), P(x + w, y + d, z + hz), P(x + w, y + d, z),
             P(x + w, y, z)]
        return l, r, t

    real, flat = faces(hh), faces(0.001)
    st = stroke or c
    out = []
    for name, f, pts, b in zip("lrt", (0.34, 0.22, 0.5), real, flat):
        out.append(poly(f"{k}.{name}", pts, fill=shade(c, f),
                        fo=0.0 if empty else fo, stroke=st, sw=sw,
                        dash=(6, 5) if empty else None, op=op, delay=delay,
                        dur=dur, anim=anim, base=b, grp=k))
    return out


def txt(k, x, y, s, size=30, fill=K["paper"], anchor="start", op=1.0,
        italic=False, delay=0.0, font="serif", dur=1.2):
    """SVG text of the storyboard: size × 1.08, and nothing at y ≥ 990 — the
    storyboard hides in-scene captions that the narration line replaced."""
    if y >= 990 or s == "":
        return None
    return text(k, x, y, s, size * 1.08, fill, anchor, op, italic, font,
                delay, dur)


def lab(k, w, dx, dy, s, **o):
    p = P(w[0], w[1], w[2] if len(w) > 2 else 0.0)
    return txt(k, p[0] + dx, p[1] + dy, s, **o)


def ln(k, pts, c=K["paper"], w=3, dash=None, op=1.0, anim=None, delay=0.0,
       dur=1.4, cap="round"):
    return poly(k, pts, fill=None, stroke=c, sw=w, dash=dash, op=op,
                delay=delay, dur=dur, closed=False, anim=anim, cap=cap)


def wl(k, a, b, **o):
    return ln(k, [P(*a), P(*b)], **o)


def rect(k, x, y, w, h, fill, stroke=K["ink"], sw=1.5, op=1.0, fo=1.0,
         delay=0.0, dur=1.6):
    return poly(k, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                fill=fill, fo=fo, stroke=stroke, sw=sw, op=op, delay=delay,
                dur=dur)


def circle_pts(cx, cy, r, n=64):
    return [(cx + r * math.cos(t), cy + r * math.sin(t))
            for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def _ell(cx, cy, rx, ry, a0, a1, n=20):
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a))
            for a in np.linspace(a0, a1, n)]


def fig(k, w, op=1.0, delay=0.0, dur=1.8):
    """The little person: a cylinder body, its top ellipse and a round head."""
    px_, py_ = P(*w)
    rx, ry, bh = 15.0, 8.7, 34.0
    body = ([(-rx, 0), (-rx, -bh)]
            + _ell(0, -bh, rx, ry, math.pi, 2 * math.pi)
            + [(rx, 0)] + _ell(0, 0, rx, ry, 0, math.pi))
    top = _ell(0, -bh, rx, ry, 0, 2 * math.pi, 40)[:-1]
    head = circle_pts(0, -bh - 20, 13, 40)
    sh = lambda pts: [(a + px_, b + py_) for a, b in pts]
    return [poly(k + ".b", sh(body), fill=FIG_BODY, stroke=K["paper"],
                 sw=2.2, op=op, delay=delay, dur=dur, grp=k),
            poly(k + ".e", sh(top), fill=FIG_TOP, stroke=K["paper"], sw=2.2,
                 op=op, delay=delay, dur=dur, grp=k),
            poly(k + ".h", sh(head), fill=FIG_HEAD, stroke=K["paper"],
                 sw=2.2, op=op, delay=delay, dur=dur, grp=k)]


def qpts(a, c, b, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        out.append((u * u * a[0] + 2 * u * t * c[0] + t * t * b[0],
                    u * u * a[1] + 2 * u * t * c[1] + t * t * b[1]))
    return out


def arc(a, b, lift):
    pa, pb = P(*a), P(*b)
    return qpts(pa, ((pa[0] + pb[0]) / 2, min(pa[1], pb[1]) - lift), pb)


def wp(pts):
    return [P(*q) for q in pts]


def cube(c, s=0.3):
    return lambda: box("c", -s / 2, -s / 2, s, s, s, c, sw=1)


def tower(k, x, y, w, vis, kk=1.0, cols=None, c=None, ops=None, d0=0.0):
    TL = [(0, .5), (.65, .6), (1.4, .9), (2.45, .9), (3.5, .9), (4.55, .6)]
    out = []
    for i, (z, hh) in enumerate(TL):
        out += box(f"{k}{i}", x, y, w, w, hh * kk if vis else .001,
                   (cols[i] if cols else None) or c or K["graphite"],
                   z=z * kk if vis else 0, op=(ops[i] if ops else 1) if vis else 0,
                   delay=d0 + i * .2 if vis else 0, dur=1.4)
    return out


def student(k, x, y, vis, d0=0.0, c=None, hc=None):
    c = c or K["stone"]
    return (box(k + "a", x, y, 1, 1, .7 if vis else .001, c, op=1 if vis else 0,
                delay=d0 if vis else 0)
            + box(k + "b", x, y, 1, 1, .7 if vis else .001, c,
                  z=.8 if vis else 0, op=1 if vis else 0,
                  delay=d0 + .2 if vis else 0)
            + box(k + "c", x + .3, y + .3, .4, .4, .45 if vis else .001,
                  hc or c, z=1.5 if vis else 0, op=1 if vis else 0,
                  delay=d0 + .4 if vis else 0))


# ---------------------------------------------------------- grouping -------

def flat(kids):
    out = []
    for q in kids:
        if q is None:
            continue
        if isinstance(q, (list, tuple)):
            out += flat(q)
        else:
            out.append(q)
    return out


def at(k, ox, oy, kids):
    """`<g transform="translate(ox oy)">` — shift and namespace the keys."""
    out = []
    for q in flat(kids):
        q = dict(q)
        q["k"] = f"{k}/{q['k']}"
        if q["t"] == "poly":
            q["pts"] = q["pts"] + (ox, oy)
            if q["base"] is not None:
                q["base"] = q["base"] + (ox, oy)
            q["grp"] = f"{k}/{q['grp']}"
        elif q["t"] == "text":
            q["x"] += ox
            q["y"] += oy
        else:
            q["path"] = q["path"] + (ox, oy)
        out.append(q)
    return out


def group_op(kids, op, delay=0.0, dur=1.0):
    """A `<g>` with its own opacity transition (pipes rows)."""
    out = []
    for q in flat(kids):
        q = dict(q)
        q["gop"], q["gdl"], q["gdu"] = op, delay, dur
        out.append(q)
    return out


def with_anim(kids, anim, tag=None):
    out = []
    for q in flat(kids):
        q = dict(q)
        if anim:
            q["anim"] = anim
        if tag:
            q["tag"] = tag
        out.append(q)
    return out


def scene(cam, kids, over=()):
    """What the storyboard's `scene()` returns: world prims under the camera
    `translate(tx ty) scale(sc)`, and `over` prims above it — both inside the
    storyboard's fixed `translate(173 72) scale(0.82)`."""
    return {"cam": cam, "world": flat(kids), "over": flat(over)}
