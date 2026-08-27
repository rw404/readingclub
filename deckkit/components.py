"""The five parameterised primitives of frame S2, plus the shared frame chrome.

Frame S2 «Компоненты» declares exactly five primitives and says that in code
each becomes a function: chip(value), cell(state), node(color), fan(n),
track(len).  Everything drawn anywhere in the deck is built from these, from
the caption block, or from bare Manim shapes (circle, rect, line, arc, text).
"""

import functools
import subprocess

import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from manim import (
    VGroup, VMobject, Rectangle, RoundedRectangle, Circle, Dot, Line,
    DashedLine, Arc, Text, Polygon, ArcBetweenPoints, ORIGIN, UL, UR, DL, DR,
    LEFT, RIGHT, UP, DOWN, config,
)

from deckkit.tokens import (
    px, pos, GRID, MARGIN, CANVAS_W, CANVAS_H,
    BG, INK, MUTED, DIM, ID, DEC, ATTR, ALERT,
    FONT_SANS, FONT_MONO, fs,
    SIZE_DISPLAY, SIZE_TITLE, SIZE_MONO, W_TITLE, W_DISPLAY, W_MONO,
    S_THIN, S_MID, S_THICK, CAP_X, CAP_Y, CAP_GAP,
)

# --------------------------------------------------------------- metrics ----
# Text is placed by baseline so that every caption in the deck shares one
# baseline regardless of which letters it happens to contain.

_WEIGHT_PATTERN = {
    "NORMAL": "", "MEDIUM": ":weight=medium",
    "SEMIBOLD": ":weight=semibold", "BOLD": ":bold",
}


@functools.lru_cache(maxsize=None)
def _font_file(family, weight):
    pat = family + _WEIGHT_PATTERN.get(weight, "")
    return subprocess.check_output(["fc-match", "-f", "%{file}", pat]).decode()


@functools.lru_cache(maxsize=None)
def _font(family, weight):
    return TTFont(_font_file(family, weight), fontNumber=0)


@functools.lru_cache(maxsize=None)
def _metrics(family, weight):
    f = _font(family, weight)
    upm = f["head"].unitsPerEm
    hhea = f["hhea"]
    return upm, hhea.ascender / upm, -hhea.descender / upm


def _ink_top(s, family, weight, css_px):
    """Distance from baseline up to the highest ink of `s`, in px."""
    f = _font(family, weight)
    upm = f["head"].unitsPerEm
    gs, cm = f.getGlyphSet(), f.getBestCmap()
    top = None
    for ch in s:
        gname = cm.get(ord(ch))
        if gname is None:
            continue
        bp = BoundsPen(gs)
        try:
            gs[gname].draw(bp)
        except Exception:
            continue
        if bp.bounds:
            top = bp.bounds[3] if top is None else max(top, bp.bounds[3])
    if top is None:                      # whitespace-only or all-fallback
        top = _metrics(family, weight)[1] * upm
    return top / upm * css_px


# Pango shapes the text at `font_size / 4.8`, so a 28 px caption would be laid
# out at ~3 pt and then magnified twenty times — at that size hinting snaps
# every glyph advance to a whole pixel and the magnified result has visibly
# ragged letter spacing.  Shaping at SHAPE_SCALE times the size and scaling the
# mobject back down puts the rounding error below a thousandth of an em.
SHAPE_SCALE = 16


def text(s, css_px=SIZE_MONO, color=INK, font=FONT_MONO, weight="NORMAL",
         **kw):
    """A Text sized in CSS pixels, carrying its own metrics for placement."""
    if css_px < SIZE_MONO:
        raise ValueError(
            f"{css_px}px text: nothing on a frame may be smaller than "
            f"{SIZE_MONO}px — the frames are watched on a phone")
    # Pango is handed the render resolution as its layout box and wraps at it,
    # so the box has to grow with the shaping scale — otherwise a long caption
    # that fitted on one line starts wrapping.  Both axes scale together to
    # keep the aspect ratio, which Manim derives the frame width from.
    pw, ph = config.pixel_width, config.pixel_height
    config.pixel_width = int(pw * SHAPE_SCALE)
    config.pixel_height = int(ph * SHAPE_SCALE)
    try:
        t = Text(s, font=font, font_size=fs(css_px) * SHAPE_SCALE, color=color,
                 weight=weight, **kw)
    finally:
        config.pixel_width, config.pixel_height = pw, ph
    t.scale(1 / SHAPE_SCALE)
    t.css_px = css_px
    t.css_font = font
    t.css_weight = weight
    t.ink_top = _ink_top(s, font, weight, css_px)
    return t


def mono(s, css_px=SIZE_MONO, color=INK, **kw):
    return text(s, css_px, color, font=FONT_MONO, weight=W_NAME(W_MONO), **kw)


def sans(s, css_px=SIZE_TITLE, color=INK, weight="MEDIUM", **kw):
    return text(s, css_px, color, font=FONT_SANS, weight=weight, **kw)


def W_NAME(numeric):
    return {400: "NORMAL", 500: "MEDIUM", 600: "SEMIBOLD"}[numeric]


# -------------------------------------------------------------- placement ---

def at(mob, x_px, y_px, anchor=UL):
    """Place `mob` so that `anchor` of its bounding box sits at (x_px, y_px)."""
    mob.move_to(pos(x_px, y_px), aligned_edge=anchor)
    return mob


def at_baseline(t, x_px, baseline_px, align="left"):
    """Place a text mobject by its left/centre/right edge and text baseline."""
    top = baseline_px - t.ink_top
    edge = {"left": UL, "center": UP, "right": UR}[align]
    if align == "center":
        t.move_to(pos(x_px, top), aligned_edge=UP)
    else:
        t.move_to(pos(x_px, top), aligned_edge=edge)
    return t


def line_box(t, x_px, box_top_px, line_height=1.0, align="left"):
    """Place text as CSS would place it in a line box of the given height."""
    upm, asc, desc = _metrics(t.css_font, t.css_weight)
    L = t.css_px * line_height
    half_leading = (L - (asc + desc) * t.css_px) / 2
    baseline = box_top_px + half_leading + asc * t.css_px
    return at_baseline(t, x_px, baseline, align)


# -------------------------------------------------------------- primitives --

def chip(value, color=ID, css_px=SIZE_MONO, pad=(27, 36), stroke=S_THIN,
         text_color=None, weight="NORMAL"):
    """Rectangle with a number inside, outlined in `color`.  Frame S2.

    `pad` is CSS (vertical, horizontal); the box is sized exactly as the CSS
    padding box, so a chip drawn here has the same footprint as in the layout.
    """
    label = text(str(value), css_px, text_color or color, font=FONT_MONO,
                 weight=weight)
    content_h = css_px                      # line-height 1 in the storyboard
    w = label.width * 135 + 2 * pad[1] + 2 * stroke
    h = content_h + 2 * pad[0] + 2 * stroke
    box = Rectangle(width=px(w), height=px(h), color=color,
                    stroke_width=stroke, fill_opacity=0)
    label.move_to(box.get_center())
    g = VGroup(box, label)
    g.box, g.label = box, label
    return g


def cell(state="empty", color=ID, size=GRID, stroke=S_THIN):
    """One table cell: empty outline in `dim`, or a flat fill.  Frame S2."""
    if state == "empty":
        return Rectangle(width=px(size), height=px(size), color=DIM,
                         stroke_width=stroke, fill_opacity=0)
    return Rectangle(width=px(size), height=px(size), color=color,
                     stroke_width=0, fill_color=color, fill_opacity=1)


def cell_row(states, color=ID, size=GRID, gap=4):
    """A run of cells, `gap` px apart — the S2 cell strip."""
    g = VGroup(*[cell(s, color, size) for s in states])
    g.arrange(RIGHT, buff=px(gap))
    return g


def node(color=DEC, size=GRID):
    """A filled circle.  Frame S2 draws it 45 px across."""
    return Dot(radius=px(size) / 2, color=color, fill_opacity=1)


def ring(color=DEC, size=GRID, stroke=S_THIN):
    return Circle(radius=px(size) / 2, color=color, stroke_width=stroke,
                  fill_opacity=0)


def fan(n, color=ID, length=180, spread=36, stroke=S_THIN, origin=ORIGIN):
    """`n` rays from one point, evenly spread over `spread` degrees.

    Frame S2 draws fan(4) as rays at -18/-6/+6/+18 degrees, 180 px long.
    """
    rays = VGroup()
    if n == 1:
        angles = [0.0]
    else:
        angles = np.linspace(-spread / 2, spread / 2, n)
    for a in angles:
        th = np.deg2rad(a)
        end = origin + np.array([px(length) * np.cos(th),
                                 -px(length) * np.sin(th), 0.0])
        rays.add(Line(origin, end, color=color, stroke_width=stroke))
    return rays


def track(total=270, fill=180, height=S_THICK, color=DEC, bed=DIM):
    """Progress bar: `total` px wide bed with a `fill` px bar.  Frame S2."""
    g = VGroup()
    b = Rectangle(width=px(total), height=px(height), color=bed,
                  stroke_width=0, fill_color=bed, fill_opacity=1)
    g.add(b)
    if fill > 0:
        f = Rectangle(width=px(fill), height=px(height), color=color,
                      stroke_width=0, fill_color=color, fill_opacity=1)
        f.move_to(b.get_left(), aligned_edge=LEFT)
        g.add(f)
    g.bed, g.fill = b, (g[1] if fill > 0 else None)
    return g


# ------------------------------------------------------- derived helpers ----

def bar_row(values, width=45, gap=27, max_h=270, color=ID, baseline="bottom",
            vmax=None):
    """Column chart from a list of values, bars growing from a shared baseline."""
    vmax = vmax or (max(abs(v) for v in values) or 1)
    g = VGroup()
    for v in values:
        h = abs(v) / vmax * max_h
        c = color(v) if callable(color) else color
        bar = Rectangle(width=px(width), height=px(max(h, 1)), color=c,
                        stroke_width=0, fill_color=c, fill_opacity=1)
        g.add(bar)
    g.arrange(RIGHT, buff=px(gap), aligned_edge=DOWN if baseline == "bottom" else UP)
    return g


def rect(w, h, color=DIM, stroke=S_THIN, fill=None, fill_opacity=0.0):
    return Rectangle(width=px(w), height=px(h), color=color,
                     stroke_width=stroke,
                     fill_color=fill or color,
                     fill_opacity=fill_opacity)


def hline(length, color=MUTED, stroke=S_THIN):
    return Line(ORIGIN, RIGHT * px(length), color=color, stroke_width=stroke)


def vline(length, color=MUTED, stroke=S_THIN):
    return Line(ORIGIN, DOWN * px(length), color=color, stroke_width=stroke)


def dashed(length, color=DIM, stroke=S_THIN, dash=12, direction=RIGHT):
    return DashedLine(ORIGIN, direction * px(length), color=color,
                      stroke_width=stroke, dash_length=px(dash))


def ray_px(x, y, length, angle_deg, color=DIM, stroke=S_THIN):
    """A line of `length` px from (x, y), rotated as CSS rotates: positive
    degrees turn clockwise on screen."""
    th = np.deg2rad(angle_deg)
    return Line(pos(x, y),
                pos(x + length * np.cos(th), y + length * np.sin(th)),
                color=color, stroke_width=stroke)


def line_px(x1, y1, x2, y2, color=DIM, stroke=S_THIN):
    return Line(pos(x1, y1), pos(x2, y2), color=color, stroke_width=stroke)


def dot(size=8, color=DIM):
    return Dot(radius=px(size) / 2, color=color, fill_opacity=1)


def dot_field(cols, rows, gap=27, size=8, color=DIM):
    """Grid of small dots — the catalogue field of frame 1.2."""
    g = VGroup()
    for r in range(rows):
        for c in range(cols):
            d = dot(size, color)
            d.move_to(pos(c * gap, r * gap))
            g.add(d)
    g.cols, g.rows = cols, rows
    g.move_to(ORIGIN)
    return g


def _wrap(s, width_px, css_px, font, weight):
    """Greedy line breaking measured with the real font."""
    words, lines, cur = s.split(), [], ""
    cache = {}

    def w_of(t):
        if t not in cache:
            cache[t] = text(t, css_px, MUTED, font=font,
                            weight=weight).width * 135
        return cache[t]

    for word in words:
        trial = (cur + " " + word).strip()
        if cur and w_of(trial) > width_px:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def para(s, width_px, css_px=SIZE_MONO, color=MUTED, font=FONT_MONO,
         weight="NORMAL", line_height=1.4, align="left"):
    """A CSS `<p>` of a fixed column width: text wrapped at `width_px`.

    Wrapping is measured with the real font, so a paragraph never crosses the
    135 px frame margin the way a single long line would.
    """
    words = s.split()
    lines, cur = [], ""
    probe_cache = {}

    def w_of(t):
        if t not in probe_cache:
            probe_cache[t] = text(t, css_px, color, font=font,
                                  weight=weight).width * 135
        return probe_cache[t]

    for word in words:
        trial = (cur + " " + word).strip()
        if cur and w_of(trial) > width_px:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)

    g = VGroup(*[text(l, css_px, color, font=font, weight=weight)
                 for l in lines])
    edge = {"left": LEFT, "center": ORIGIN, "right": RIGHT}[align]
    g.arrange(DOWN, buff=px(css_px * (line_height - 1)), aligned_edge=edge)
    g.lines = lines
    return g


def fixed_width(mob, w, align="left"):
    """Wrap `mob` in a transparent box `w` px wide — CSS `width:Npx` on an
    inline element, so neighbours line up in a column."""
    box = Rectangle(width=px(w), height=max(mob.height, 0.01),
                    stroke_width=0, fill_opacity=0)
    box.move_to(mob.get_center())
    if align == "left":
        mob.move_to(box.get_left(), aligned_edge=LEFT)
    elif align == "right":
        mob.move_to(box.get_right(), aligned_edge=RIGHT)
    g = VGroup(box, mob)
    g.inner = mob
    return g


def body_center(mob, cx=None, cy=None):
    """Centre a diagram in the working area — the S3 rule: the diagram is
    centred in whatever the caption leaves."""
    from deckkit.tokens import BODY_CX, BODY_CY
    mob.move_to(pos(BODY_CX if cx is None else cx,
                    BODY_CY if cy is None else cy))
    return mob


def flex_row(*items, gap=90):
    """CSS `display:flex; align-items:center; gap:N` — children centred on one
    baseline row, N px apart."""
    g = VGroup(*items)
    g.arrange(RIGHT, buff=px(gap))
    return g


def flex_col(*items, gap=45, align="center"):
    """CSS `display:flex; flex-direction:column; gap:N`."""
    g = VGroup(*items)
    edge = {"center": ORIGIN, "left": LEFT, "right": RIGHT}[align]
    g.arrange(DOWN, buff=px(gap), aligned_edge=edge)
    return g


GLYPH_OK = "✓"
GLYPH_NO = "✗"
GLYPH_PART = "~"


def matrix(rows, cols, values, cell_w=225, cell_h=90, row_label_w=270,
           col_label_h=135, ok_color=ATTR, no_color=ALERT, part_color=MUTED,
           label_color=MUTED, grid_color=DIM):
    """The «метод × критерий» grid.

    Built once and returned as a group whose parts are addressable, because the
    same object comes back in later frames: rows dim to muted and the last row
    fills in — it is never redrawn.
    """
    g = VGroup()
    g.cells = {}
    g.row_labels = {}
    g.col_labels = {}
    n_r, n_c = len(rows), len(cols)

    body_w = n_c * cell_w
    body_h = n_r * cell_h

    for j, c in enumerate(cols):
        lab = mono(c, SIZE_MONO, label_color)
        lab.move_to(pos(row_label_w + j * cell_w + cell_w / 2,
                        col_label_h - 40))
        g.add(lab)
        g.col_labels[c] = lab

    for i, r in enumerate(rows):
        lab = mono(r, SIZE_MONO, label_color)
        lab.move_to(pos(row_label_w - 27, col_label_h + i * cell_h + cell_h / 2),
                    aligned_edge=RIGHT)
        g.add(lab)
        g.row_labels[r] = lab

    for i in range(n_r + 1):
        y = col_label_h + i * cell_h
        g.add(Line(pos(row_label_w, y), pos(row_label_w + body_w, y),
                   color=grid_color, stroke_width=S_THIN))
    for j in range(n_c + 1):
        x = row_label_w + j * cell_w
        g.add(Line(pos(x, col_label_h), pos(x, col_label_h + body_h),
                   color=grid_color, stroke_width=S_THIN))

    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            v = values.get((r, c))
            if v is None:
                continue
            col = {GLYPH_OK: ok_color, GLYPH_NO: no_color,
                   GLYPH_PART: part_color}.get(v, label_color)
            m = mono(v, SIZE_MONO, col)
            m.move_to(pos(row_label_w + j * cell_w + cell_w / 2,
                          col_label_h + i * cell_h + cell_h / 2))
            g.add(m)
            g.cells[(r, c)] = m

    g.move_to(ORIGIN)
    return g


# ------------------------------------------------------------- frame chrome -

def caption(title, sub=None):
    """Frame title and mono subline, always at the same point: top-left of the
    working area.  Never move it."""
    g = VGroup()
    t = sans(title, SIZE_TITLE, INK, weight=W_NAME(W_TITLE))
    line_box(t, CAP_X, CAP_Y, line_height=1.2)
    g.add(t)
    g.title = t
    g.sub = None
    if sub:
        # Four of the sublines are longer than the working area; they wrap
        # rather than cross the 135 px margin.  Everything else stays the
        # single line the storyboard draws.
        top = CAP_Y + SIZE_TITLE * 1.2 + CAP_GAP
        avail = CANVAS_W - 2 * MARGIN
        probe = mono(sub, SIZE_MONO, MUTED)
        if probe.width * 135 <= avail:
            line_box(probe, CAP_X, top, line_height=1.3)
            g.add(probe)
            g.sub = probe
        else:
            block = VGroup()
            for i, line in enumerate(_wrap(sub, avail, SIZE_MONO, FONT_MONO,
                                           "NORMAL")):
                t = mono(line, SIZE_MONO, MUTED)
                line_box(t, CAP_X, top + i * SIZE_MONO * 1.3, line_height=1.3)
                block.add(t)
            g.add(block)
            g.sub = block
    return g


def grid_overlay(step=GRID, color=DIM, opacity=0.5):
    """The 45 px layout grid of frame S3 — diagnostics only, never in the film."""
    g = VGroup()
    for x in range(0, CANVAS_W + 1, step):
        g.add(Line(pos(x, 0), pos(x, CANVAS_H), color=color, stroke_width=1))
    for y in range(0, CANVAS_H + 1, step):
        g.add(Line(pos(0, y), pos(CANVAS_W, y), color=color, stroke_width=1))
    g.set_stroke(opacity=opacity)
    return g


def margin_box(color=ID, opacity=0.4, stroke=S_THIN):
    r = Rectangle(width=px(CANVAS_W - 2 * MARGIN), height=px(CANVAS_H - 2 * MARGIN),
                  color=color, stroke_width=stroke, fill_opacity=0)
    r.set_stroke(opacity=opacity)
    return r


# ------------------------------------------------------------------ code ----

@functools.lru_cache(maxsize=None)
def mono_advance(css_px=SIZE_MONO):
    """Advance width of one JetBrains Mono cell, in CSS px."""
    f = _font(FONT_MONO, "NORMAL")
    upm = f["head"].unitsPerEm
    gname = f.getBestCmap()[ord("0")]
    return f["hmtx"][gname][0] / upm * css_px


def code_block(lines, x_px, y_px, css_px=SIZE_MONO, line_height=1.5):
    """Source code laid out on the monospace grid.

    `lines` is a list of (indent_px, [(text, colour), ...]).  Runs are placed
    by column index rather than by concatenating mobjects, so the indentation
    is real offset — never spaces baked into a string — and syntax colouring
    never shifts the glyph grid.
    """
    adv = mono_advance(css_px)
    lh = css_px * line_height
    g = VGroup()
    g.rows = []
    for i, (indent, runs) in enumerate(lines):
        row = VGroup()
        col = 0
        for txt, colour in runs:
            body = txt.strip()
            if body:
                # Pango drops the leading blank of a run, so the run is drawn
                # stripped and shifted to the column of its first real
                # character — otherwise `def` and `dhe_l1` come out glued.
                lead = len(txt) - len(txt.lstrip())
                t = mono(body, css_px, colour)
                line_box(t, x_px + indent + (col + lead) * adv,
                         y_px + i * lh, line_height=line_height)
                row.add(t)
            col += len(txt)
        g.rows.append(row)
        g.add(row)
    return g


# ------------------------------------------------------------------ beats ---
# A storyboard frame lasts 8-20 s but its layers take only a few of them.  The
# rest used to be a frozen image; these are the animations that keep it alive.
# Each helper returns a *factory* — a zero-argument callable building a fresh
# Animation — because a Manim animation cannot be played twice.

from manim import (  # noqa: E402
    Indicate, Circumscribe, ShowPassingFlash, Flash, Wiggle, ApplyWave,
    FocusOn, AnimationGroup, LaggedStart as _Lag, Rectangle as _Rect,
)


def b_indicate(mob, colour=None, scale=1.08, rt=0.9):
    """Пульс — самый нейтральный способ вернуть внимание на элемент."""
    return lambda: Indicate(mob, color=colour, scale_factor=scale, run_time=rt)


def b_wave(mobs, colour=None, scale=1.12, lag=0.06, rt=1.6):
    """Волна по ряду: столбикам, ячейкам, точкам."""
    def make():
        items = list(mobs)
        return _Lag(*[Indicate(m, color=colour, scale_factor=scale)
                      for m in items], lag_ratio=lag, run_time=rt)
    return make


def b_flash_along(mob, colour=INK, width=8, rt=1.2, time_width=0.4):
    """Свет, бегущий по линии или контуру — движение по самому штриху."""
    def make():
        ghost = mob.copy().set_stroke(colour, width, opacity=1)
        return ShowPassingFlash(ghost, time_width=time_width, run_time=rt)
    return make


def b_flash_group(mobs, colour=INK, width=8, lag=0.12, rt=1.6):
    def make():
        return _Lag(*[ShowPassingFlash(m.copy().set_stroke(colour, width,
                                                           opacity=1),
                                       time_width=0.4)
                      for m in mobs], lag_ratio=lag, run_time=rt)
    return make


def b_box(mob, colour=ID, rt=1.4, buff=0.12):
    """Обводка вокруг элемента, которая гаснет."""
    return lambda: Circumscribe(mob, color=colour, shape=_Rect, buff=buff,
                                fade_out=True, run_time=rt)


def b_spark(mob, colour=ID, rt=0.9, n=12, length=0.25):
    """Вспышка в точке — для одиночного узла или числа."""
    return lambda: Flash(mob, color=colour, num_lines=n, line_length=length,
                         flash_radius=mob.width / 2 + 0.14, run_time=rt)


def b_focus(mob, colour=ID, rt=1.1):
    return lambda: FocusOn(mob, color=colour, run_time=rt)


def b_wiggle(mob, rt=1.0, scale=1.05):
    return lambda: Wiggle(mob, scale_value=scale, run_time=rt)


def b_ripple(mob, rt=1.4, amp=0.12):
    """Рябь по группе — читается как «это одно целое»."""
    return lambda: ApplyWave(mob, amplitude=amp, run_time=rt)
