"""The browser, in Manim.

The storyboard animates by changing a scene's state on click and letting CSS
transitions carry every element there: each has its own `delay` and duration
on the storyboard's `cubic-bezier(.65,0,.35,1)`, the camera `<g>` glides for
2.2 s, and the looping bits — data cubes riding `animateMotion`, gradient
dashes crawling down, a flickering head, a jittering one — never stop.

`Stage` is one Manim mobject that does the same.  It holds the state it came
from and the state it is going to (prim lists from `deck.scenes`), and on
every rendered frame rebuilds each element's outline, colour and opacity from
the time since the click.  All looping motion runs on accumulated phases whose
periods are snapped to the hold length, so a hold renders as a seamless loop
slide.

`IsoDeck` is the part scene: frame by frame, click by click, it drives the
stage and cuts slides — one per click, plus a looping slide wherever the
state keeps moving.
"""

import functools
import math
import subprocess

import numpy as np
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from manim import VGroup, VMobject, Text, MathTex, ManimColor, config, ITALIC
from manim.constants import CapStyleType, LineJointType

from deckkit.base import DeckScene
from deck.tokens import (
    BG, FONT_SERIF, FONT_MONO, FONT_K, TEX_K, STAGE_X, STAGE_S, STAGE_Y,
    UNIT_PX,
)
from deck import scenes as SC

config.disable_caching = True      # hashing ~2000 mobjects per wait is slow

# ------------------------------------------------------------ easing -------


def _bezier(x1, y1, x2, y2, n=2001):
    t = np.linspace(0, 1, 20001)
    bx = 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3
    by = 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3
    xs = np.linspace(0, 1, n)
    ys = np.interp(xs, bx, by)
    return lambda u: float(np.interp(u, xs, ys))


EASE = _bezier(.65, 0, .35, 1)          # the storyboard's E
EASE_IO = _bezier(.42, 0, .58, 1)       # CSS ease-in-out


def _prog(tau, delay, dur):
    if dur <= 1e-6:
        return 1.0 if tau >= delay else 0.0
    return EASE(min(max((tau - delay) / dur, 0.0), 1.0))


# ------------------------------------------------------------ colour -------

@functools.lru_cache(maxsize=None)
def rgb(h):
    return np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])


def _mix(a, b, u):
    if a == b or a is None:
        return rgb(b) if b else np.zeros(3)
    if b is None:
        return rgb(a)
    return rgb(a) + (rgb(b) - rgb(a)) * u


# ------------------------------------------------------------ text ---------

@functools.lru_cache(maxsize=None)
def _font(font, italic):
    fam = FONT_SERIF if font == "serif" else FONT_MONO
    pat = fam + (":italic" if italic else "")
    path = subprocess.check_output(["fc-match", "-f", "%{file}", pat]).decode()
    return TTFont(path, fontNumber=0)


@functools.lru_cache(maxsize=None)
def _ink_top_em(s, font, italic):
    f = _font(font, italic)
    upm = f["head"].unitsPerEm
    gs, cm = f.getGlyphSet(), f.getBestCmap()
    top = None
    for ch in s:
        g = cm.get(ord(ch))
        if g is None:
            continue
        bp = BoundsPen(gs)
        gs[g].draw(bp)
        if bp.bounds:
            top = bp.bounds[3] if top is None else max(top, bp.bounds[3])
    return (top if top is not None else 0.7 * upm) / upm


# Pango shapes at font_size/4.8 and hinting then rounds every advance to a
# whole pixel; shape 16× larger and scale back (see deckkit.components.text)
SHAPE_SCALE = 16


@functools.lru_cache(maxsize=None)
def _template(s, px, font, italic, spacing):
    """A text mobject laid out at the origin, with its placement metrics:
    `ul` — its upper-left corner, `w` — ink width in px, `top` — ink height
    above the baseline in px."""
    if font == "tex":
        m = MathTex("H", r"\textstyle " + s, font_size=px * TEX_K)
        h, body = m[0], m[1]
        base_y = h.get_bottom()[1]
        body = body.copy()
        top_px = (body.get_top()[1] - base_y) * UNIT_PX
    else:
        pw, ph = config.pixel_width, config.pixel_height
        config.pixel_width, config.pixel_height = pw * SHAPE_SCALE, ph * SHAPE_SCALE
        try:
            body = Text(s, font=FONT_SERIF if font == "serif" else FONT_MONO,
                        font_size=px * FONT_K * SHAPE_SCALE,
                        slant=ITALIC if italic else "NORMAL")
        finally:
            config.pixel_width, config.pixel_height = pw, ph
        body.scale(1 / SHAPE_SCALE)
        if spacing:
            glyphs = body.submobjects
            chars = [i for i, ch in enumerate(s) if not ch.isspace()]
            if len(glyphs) == len(chars):
                for g, ci in zip(glyphs, chars):
                    g.shift(np.array([ci * spacing / UNIT_PX, 0, 0]))
        top_px = _ink_top_em(s, font, italic) * px
    body.set_stroke(width=0)
    ul = body.get_corner(np.array([-1, 1, 0]))
    return body, ul, body.width * UNIT_PX, top_px


def text_width_px(s, px, font="serif", italic=False):
    return _template(s, px, font, italic, 0.0)[2]


def wrap(s, px, width):
    """Greedy line breaking at the flex item width."""
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if cur and text_width_px(cand, px) > width:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------ geometry -----

def _poly_points(chains):
    """Polylines (lists of Nx2 unit arrays) -> VMobject bezier points."""
    segs = []
    for c in chains:
        if len(c) < 2:
            continue
        a, b = c[:-1], c[1:]
        d = b - a
        seg = np.stack([a, a + d / 3, a + 2 * d / 3, b], axis=1)
        segs.append(seg.reshape(-1, 2))
    if not segs:
        return np.zeros((0, 3))
    p = np.concatenate(segs)
    return np.column_stack([p, np.zeros(len(p))])


def _cum(pts):
    d = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    return np.concatenate([[0], np.cumsum(d)])


def _cut(pts, cum, a, b):
    """The piece of a polyline between arc lengths a and b."""
    a, b = max(a, 0.0), min(b, cum[-1])
    if b <= a:
        return None
    xs = np.interp([a, b], cum, pts[:, 0])
    ys = np.interp([a, b], cum, pts[:, 1])
    inner = pts[(cum > a) & (cum < b)]
    return np.vstack([[xs[0], ys[0]], inner, [xs[1], ys[1]]])


def _dashes(pts, pattern, offset):
    cum = _cum(pts)
    on, off = pattern
    per = on + off
    total = cum[-1]
    out = []
    start = (offset % per) - per
    while start < total:
        piece = _cut(pts, cum, start, start + on)
        if piece is not None:
            out.append(piece)
        start += per
    return out


def _along(pts, cum, u):
    s = u * cum[-1]
    return np.array([np.interp(s, cum, pts[:, 0]), np.interp(s, cum, pts[:, 1])])


def _keyframes(u, frames, ease=None):
    for (t0, v0), (t1, v1) in zip(frames, frames[1:]):
        if u <= t1:
            f = 0 if t1 == t0 else (u - t0) / (t1 - t0)
            f = ease(f) if ease else f
            return v0 + (v1 - v0) * f
    return frames[-1][1]


def _snap(period, hold):
    """A period that divides the hold, so the hold loops seamlessly."""
    return hold / max(1, round(hold / period))


# ------------------------------------------------------------ stage --------

class Stage(VGroup):
    """Every element of the current scene, re-posed each frame."""

    def __init__(self):
        super().__init__()
        self.A, self.B, self.order = {}, {}, []
        self.camA = self.camB = (0.0, 0.0, 1.0)
        self.tau = 0.0
        self.hold = 4.0
        self.mobs = {}
        self.settled = set()
        self.ph = {"flick": 0.0, "jit": 0.0, "dash": 0.0}
        self.flow_ph = {}
        self.tilt_pivot = None
        self.add_updater(lambda m, dt: m.tick(dt))

    # -- state changes -----------------------------------------------------
    @staticmethod
    def flatten(state):
        out = []
        for sp in ("world", "over", "screen"):
            for q in state[sp]:
                q = dict(q)
                q["sp"] = sp[0].upper()
                q["k"] = q["sp"] + ":" + q["k"]
                out.append(q)
        return out

    def go(self, prims, cam, hold):
        """Start a transition from the current target to `prims`."""
        prev = self.B
        self.A = prev
        self.B = {q["k"]: q for q in prims}
        new_order = [q["k"] for q in prims]
        gone = [k for k in self.order if k not in self.B]
        order = list(new_order)
        for k in gone:                     # keep leavers where they were
            i = self.order.index(k)
            prev_keys = [x for x in self.order[:i] if x in self.B]
            pos = order.index(prev_keys[-1]) + 1 if prev_keys else 0
            order.insert(pos, k)
        for k in gone:
            q = dict(self.A[k])
            q["op"], q["delay"], q["dur"] = 0.0, 0.0, 0.5
            self.B[k] = q
        self.order = order
        self.camA, self.camB = self.camB, cam
        self.tau = 0.0
        self.hold = hold
        self.settled = set()
        tg = [q for q in prims if q.get("tag") == "tg" and q["t"] == "poly"]
        if tg:
            allp = np.vstack([q["pts"] for q in tg])
            self.tilt_pivot = ((allp[:, 0].min() + allp[:, 0].max()) / 2,
                               allp[:, 1].max())
        self._sync_mobs()
        return self.duration()

    def duration(self):
        """Seconds until every transition of this click has finished."""
        T = 0.0
        if self.camA != self.camB:
            T = 2.2
        for k, b in self.B.items():
            a = self.A.get(k)
            if a is None:
                T = max(T, b["delay"] + b["dur"], b["gdl"] + b["gdu"])
                continue
            if b.get("anim") == "tilt":
                T = max(T, 5.9)
            if self._differs(a, b):
                T = max(T, b["delay"] + (0.6 if b["t"] == "text" and
                                         a.get("s") != b.get("s") else b["dur"]))
            if a["gop"] != b["gop"]:
                T = max(T, b["gdl"] + b["gdu"])
        return max(T, 0.8)

    @staticmethod
    def _differs(a, b):
        if a["t"] != b["t"] or a["op"] != b["op"]:
            return True
        if a["t"] == "poly":
            return (a["pts"].shape != b["pts"].shape
                    or not np.allclose(a["pts"], b["pts"])
                    or a["fill"] != b["fill"] or a["fo"] != b["fo"]
                    or a["stroke"] != b["stroke"] or a["sw"] != b["sw"]
                    or a["reveal"] != b["reveal"] or a["dash"] != b["dash"])
        if a["t"] == "text":
            return (a["s"] != b["s"] or a["fill"] != b["fill"]
                    or a["x"] != b["x"] or a["y"] != b["y"])
        return False

    def moving(self):
        """Does the target state keep moving after its transitions end?"""
        for q in self.B.values():
            if q["op"] * q["gop"] <= 0:
                continue
            if q["t"] == "flow" or q.get("anim") in ("flick", "jit", "gdash"):
                return True
        return False

    # -- mobjects ------------------------------------------------------------
    def _sync_mobs(self):
        subs = []
        for k in self.order:
            q = self.B[k]
            m = self.mobs.get(k)
            if m is None or m.kind != q["t"]:
                m = self._new_mob(q)
                m.kind = q["t"]
                self.mobs[k] = m
            subs.append(m)
        for k in list(self.mobs):
            if k not in self.B:
                del self.mobs[k]
        self.submobjects = subs

    def _new_mob(self, q):
        if q["t"] == "poly":
            m = VGroup(self._vm(), self._vm())      # fill+stroke, dashes
        elif q["t"] == "text":
            m = VGroup()
            m.cur = {}
        else:
            m = VGroup(*[VGroup(*[self._vm() for _ in q["items"]])
                         for _ in range(q["n"])])
        return m

    @staticmethod
    def _vm():
        v = VMobject()
        v.joint_type = LineJointType.ROUND
        v.cap_style = CapStyleType.ROUND
        v.fill_rgbas = np.zeros((1, 4))
        v.stroke_rgbas = np.zeros((1, 4))
        v.stroke_width = 0.0
        v.background_stroke_width = 0.0
        return v

    # -- the frame ---------------------------------------------------------
    def tick(self, dt):
        self.tau += dt
        H = self.hold
        self.ph["flick"] += dt / _snap(1.4, H)
        self.ph["jit"] += dt / _snap(0.32, H)
        self.ph["dash"] += dt * 18.0 / _snap(0.55, H)
        uc = _prog(self.tau, 0.0, 2.2)
        cam = tuple(a + (b - a) * uc for a, b in zip(self.camA, self.camB))
        cam_moving = self.camA != self.camB and self.tau < 2.3
        for k in self.order:
            q = self.B[k]
            if q["t"] == "flow":
                self.flow_ph[k] = self.flow_ph.get(k, 0.0) + dt / (
                    _snap(q["period"] / q["n"], H) * q["n"])
            if k in self.settled and not (cam_moving and q["sp"] == "W"):
                continue
            a = self.A.get(k)
            done = self._draw(k, a, q, cam)
            if done:
                self.settled.add(k)

    # space transform -------------------------------------------------------
    @staticmethod
    def _xf(sp, cam):
        """(scale, ox, oy) from space px to canvas px."""
        if sp == "S":
            return 1.0, 0.0, 0.0
        if sp == "O":
            return STAGE_S, STAGE_X, STAGE_Y
        tx, ty, sc = cam
        return STAGE_S * sc, STAGE_X + STAGE_S * tx, STAGE_Y + STAGE_S * ty

    @staticmethod
    def _units(p, s, ox, oy):
        x = (ox + s * p[:, 0] - 960.0) / UNIT_PX
        y = (540.0 - (oy + s * p[:, 1])) / UNIT_PX
        return np.column_stack([x, y])

    def _local(self, q, pts):
        """Looping per-element motion in the element's own coordinates."""
        an = q.get("anim")
        if an == "jit":
            u = self.ph["jit"] % 1.0
            dx = _keyframes(u, [(0, 0), (.25, -4), (.75, 4), (1, 0)])
            dy = _keyframes(u, [(0, 0), (.25, 1), (.75, -1), (1, 0)])
            pts = pts + (dx, dy)
        elif an == "tilt" and self.tilt_pivot is not None:
            u = min(max((self.tau - 0.4) / 5.5, 0.0), 1.0)
            deg = _keyframes(u, [(0, 0.0), (.38, -8.0), (.56, -8.0), (1, 0.0)],
                             EASE)
            th = math.radians(deg)
            c, s_ = math.cos(th), math.sin(th)
            px_, py_ = self.tilt_pivot
            d = pts - (px_, py_)
            pts = np.column_stack([d[:, 0] * c - d[:, 1] * s_,
                                   d[:, 0] * s_ + d[:, 1] * c]) + (px_, py_)
        return pts

    def _anim_live(self, q):
        return q.get("anim") in ("jit", "tilt", "flick", "gdash") and \
            q["op"] * q["gop"] > 0

    # drawing ---------------------------------------------------------------
    def _draw(self, k, a, b, cam):
        tau = self.tau
        u = _prog(tau, b["delay"], b["dur"])
        ug = _prog(tau, b["gdl"], b["gdu"])
        if a is None:
            a = dict(b)
            a["op"] = 0.0
        op = a["op"] + (b["op"] - a["op"]) * u
        gop = a["gop"] + (b["gop"] - a["gop"]) * ug
        alpha = op * gop
        live = self._anim_live(b)
        finished = (u >= 1.0 and ug >= 1.0 and not live
                    and tau >= b["delay"] + b["dur"] + 0.6)
        m = self.mobs[k]
        s, ox, oy = self._xf(b["sp"], cam)
        if b["t"] == "poly":
            self._draw_poly(m, a, b, u, alpha, s, ox, oy)
        elif b["t"] == "text":
            self._draw_text(m, a, b, u, alpha, s, ox, oy)
        else:
            self._draw_flow(k, m, b, alpha, s, ox, oy)
            finished = finished and alpha <= 0
        return finished

    def _draw_poly(self, m, a, b, u, alpha, s, ox, oy):
        fillm, dashm = m.submobjects
        if alpha <= 1e-4:
            fillm.points = np.zeros((0, 3))
            dashm.points = np.zeros((0, 3))
            return
        pa, pb = a["pts"], b["pts"]
        pts = pa + (pb - pa) * u if pa.shape == pb.shape else pb
        pts = self._local(b, pts)
        if b.get("anim") == "flick":
            f = self.ph["flick"] % 1.0
            alpha *= _keyframes(f, [(0, 1.0), (.5, .72), (1, 1.0)], EASE_IO)
        P_ = self._units(pts, s, ox, oy)
        fo = (a["fo"] + (b["fo"] - a["fo"]) * u)
        sw = (a["sw"] + (b["sw"] - a["sw"]) * u) * s / UNIT_PX * 100.0
        fcol = _mix(a["fill"], b["fill"], u) if (a["fill"] or b["fill"]) else np.zeros(3)
        scol = _mix(a["stroke"], b["stroke"], u)
        rev = a["reveal"] + (b["reveal"] - a["reveal"]) * u
        closed = b["closed"]
        chain = np.vstack([P_, P_[:1]]) if closed else P_
        dashed = b["dash"] is not None
        if rev < 1.0:
            cum = _cum(chain)
            piece = _cut(chain, cum, 0.0, rev * cum[-1])
            chain = piece if piece is not None else chain[:1]
        fa = fo * alpha if closed else 0.0
        fillm.points = _poly_points([chain])
        fillm.fill_rgbas = np.array([[*fcol, fa]])
        cap = CapStyleType.BUTT if b.get("cap") == "butt" else CapStyleType.ROUND
        fillm.cap_style = cap
        if dashed and sw > 0:
            fillm.stroke_width = 0.0
            off = self.ph["dash"] if b.get("anim") == "gdash" else 0.0
            # pattern in local px -> units
            k_ = s / UNIT_PX
            pat = (b["dash"][0] * k_, b["dash"][1] * k_)
            dashm.points = _poly_points(_dashes(chain, pat, off * k_))
            dashm.stroke_rgbas = np.array([[*scol, alpha]])
            dashm.stroke_width = sw
            dashm.cap_style = CapStyleType.BUTT if b.get("anim") != "gdash" else cap
        else:
            dashm.points = np.zeros((0, 3))
            fillm.stroke_rgbas = np.array([[*scol, alpha]])
            fillm.stroke_width = sw

    def _text_mob(self, m, q, s):
        key = (q["s"], round(q["size"] * s, 3), q["font"], q["italic"],
               round(q["spacing"] * s, 3))
        if key not in m.cur:
            tpl, ul, w, top = _template(*key)
            mob = tpl.copy()
            mob.ul, mob.w, mob.top = ul.copy(), w, top
            mob.last = None
            m.cur[key] = mob
            m.add(mob)
        return m.cur[key], key

    def _place_text(self, mob, x, y, anchor, colr, alpha):
        left = x - {"start": 0.0, "middle": mob.w / 2, "end": mob.w}[anchor]
        top = y - mob.top
        target = np.array([(left - 960.0) / UNIT_PX, (540.0 - top) / UNIT_PX, 0])
        d = target - mob.ul
        if abs(d[0]) > 1e-6 or abs(d[1]) > 1e-6:
            mob.shift(d)
            mob.ul = target
        state = (tuple(np.round(colr, 4)), round(alpha, 4))
        if state != mob.last:
            mob.set_fill(ManimColor.from_rgb(colr), opacity=alpha)
            mob.last = state

    def _draw_text(self, m, a, b, u, alpha, s, ox, oy):
        mb, kb = self._text_mob(m, b, s)
        colr = _mix(a["fill"], b["fill"], u)
        xa, ya = ox + s * a["x"], oy + s * a["y"]
        xb, yb = ox + s * b["x"], oy + s * b["y"]
        x, y = xa + (xb - xa) * u, ya + (yb - ya) * u
        swap = a["s"] != b["s"] or a["font"] != b["font"] or a["size"] != b["size"]
        if swap:
            ma, ka = self._text_mob(m, a, s)
            f = min(max((self.tau - b["delay"]) / 0.6, 0.0), 1.0)
            f = EASE(f)
            self._place_text(ma, xa, ya, a["anchor"], rgb(a["fill"]),
                             a["op"] * a["gop"] * (1 - f))
            self._place_text(mb, xb, yb, b["anchor"], rgb(b["fill"]),
                             b["op"] * b["gop"] * f)
            keep = {ka, kb}
        else:
            self._place_text(mb, x, y, b["anchor"], colr, alpha)
            keep = {kb}
        for key in list(m.cur):
            if key not in keep:
                gone = m.cur.pop(key)
                m.remove(gone)

    def _draw_flow(self, k, m, q, alpha, s, ox, oy):
        path = self._units(q["path"], s, ox, oy)
        cum = _cum(path)
        n = q["n"]
        ph = self.flow_ph.get(k, 0.0)
        for i, item in enumerate(m.submobjects):
            uu = (ph + i / n + 0.01 / q["period"]) % 1.0
            a_i = alpha * _keyframes(uu, [(0, 0.0), (.12, 1.0), (.88, 1.0),
                                          (1, 0.0)])
            at = _along(path, cum, uu)
            for vm, face in zip(item.submobjects, q["items"]):
                if a_i <= 1e-4:
                    vm.points = np.zeros((0, 3))
                    continue
                loc = self._units(face["pts"], s, 0.0, 0.0)
                loc = loc - (-960.0 / UNIT_PX, 540.0 / UNIT_PX) + at
                chain = np.vstack([loc, loc[:1]])
                vm.points = _poly_points([chain])
                vm.fill_rgbas = np.array([[*rgb(face["fill"]), face["fo"] * a_i]])
                vm.stroke_rgbas = np.array([[*rgb(face["stroke"]), a_i]])
                vm.stroke_width = face["sw"] * s / UNIT_PX * 100.0

    # -- derived states ----------------------------------------------------
    @staticmethod
    def intro(prims, spread=1.1, dur=1.1):
        """How a frame builds itself: blocks rise out of their footprint in
        drawing order, labels and chrome fade in after them."""
        grps = []
        for q in prims:
            if q["t"] == "poly" and q["sp"] != "S" and q["grp"] not in grps:
                grps.append(q["grp"])
        rank = {g: i / max(1, len(grps) - 1) for i, g in enumerate(grps)}
        void, target = [], []
        for q in prims:
            v, t = dict(q), dict(q)
            v["op"] = 0.0
            if q["t"] == "poly" and q["base"] is not None:
                v["pts"] = q["base"]
            if q["t"] == "poly" and q["sp"] != "S":
                t["delay"], t["dur"] = rank[q["grp"]] * spread, dur
            elif q["sp"] == "S" and q["k"].startswith("S:t"):
                pass                               # title cards keep theirs
            else:
                t["delay"], t["dur"] = spread * 0.6 + q["delay"] * 0.3, 0.9
            t["gdl"], t["gdu"] = t["delay"], t["dur"]
            v["gop"] = q["gop"]
            void.append(v)
            target.append(t)
        return void, target

    def outro_state(self):
        out = []
        for k in self.order:
            q = dict(self.B[k])
            q["op"], q["delay"], q["dur"] = 0.0, 0.0, 0.5
            out.append(q)
        return out

    def jump(self, prims, cam):
        """Set a state instantly (used for the invisible start of a frame).

        A new frame starts from fresh mobjects: keys repeat between scenes
        (`A/l1` is a wire in 11 and a label in 12)."""
        self.mobs = {}
        self.flow_ph = {}
        self.B = {q["k"]: q for q in prims}
        self.order = [q["k"] for q in prims]
        self.camB = cam
        self._sync_mobs()


# ------------------------------------------------------------ the scene ----

def read_time(s):
    """Seconds to read a narration line: ~15 characters a second."""
    return 1.2 + len(s) / 15.0


class IsoDeck(DeckScene):
    """One part of the talk: a run of storyboard frames, click by click."""

    FRAMES = ()          # 0-based storyboard section indices

    def setup(self):
        super().setup()
        self.camera.background_color = ManimColor(BG)

    def construct(self):
        self.stage = Stage()
        self.add(self.stage)
        for i in self.FRAMES:
            self.play_frame(i)
        self.outro()

    # -- timing ------------------------------------------------------------
    def run(self, seconds):
        self.wait(seconds)

    def hold_for(self, i, v, T):
        need = read_time(SC.NAR[i][v]) - 0.5 * T
        if self.stage.moving():
            return "loop", (4.0 if need <= 4.5 else 6.0 if need <= 6.5 else 8.0)
        return "still", max(2.2, need)

    def _step_notes(self, i, v):
        base = DeckScene._notes(SC.SCREENS[i])
        tag = SC.SCREENS[i] + (f"·{v + 1}" if SC.MAX[i] else "")
        head = tag if v else SC.SCREENS[i]
        return f"{head}\n\n{SC.NAR[i][v]}\n\n{base}"

    def play_frame(self, i):
        screen = SC.SCREENS[i]
        self.frame(screen)
        self._base_slide_config.notes = self._step_notes(i, 0)
        states = [SC.build(i, v, wrap) for v in range(SC.MAX[i] + 1)]
        st = self.stage
        # leave the previous frame
        if st.order:
            st.go(st.outro_state(), st.camB, 1.0)
            self.run(0.6)
        for v, state in enumerate(states):
            prims = Stage.flatten(state)
            cam = tuple(float(c) for c in state["cam"])
            if v == 0:
                void, target = Stage.intro(prims)
                st.jump(void, cam)
                st.A = {}
                st.camB = cam
                T = st.go(target, cam, 4.0)
            else:
                T = st.go(prims, cam, 4.0)
            mode, hold = self.hold_for(i, v, T)
            st.hold = hold if mode == "loop" else 4.0
            if v:
                self.next_slide(notes=self._step_notes(i, v),
                                auto_next=mode == "loop")
            else:
                self._base_slide_config.auto_next = mode == "loop"
            if i in SC.TITLES:
                T = max(T, 1.7)
            self.run(T)
            if mode == "loop":
                self.next_slide(loop=True, notes=self._step_notes(i, v))
                self.run(hold)
            else:
                self.run(hold if i not in SC.TITLES else 3.0)

    def outro(self, run_time=0.6):
        self.next_section(name="_outro", skip_animations=False)
        self.next_slide(notes="_outro")
        st = self.stage
        st.go(st.outro_state(), st.camB, 1.0)
        self.run(run_time)
