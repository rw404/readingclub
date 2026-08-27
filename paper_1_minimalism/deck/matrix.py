"""The «метод × критерий» matrix and the criterion glyphs it is headed with.

The matrix is the main frame of the deck.  It is built once, here, so that
кадр 4.9 (part 4) and кадр 6.1 (part 6) render the *same* object: part 6 does
not redraw it, it picks up the finished 4.9 state and only changes what the
storyboard says changes — method rows drop to muted, the last row fills in.
"""

import numpy as np
from manim import VGroup, Line, Circle, Dot, RIGHT, LEFT, UP, DOWN, UL, UR, DL, DR

from deckkit.tokens import (
    px, pos, INK, MUTED, DIM, ID, DEC, ATTR, ALERT,
    SIZE_MONO, S_THIN, S_MID, BODY_CX, BODY_CY,
)
from deckkit.components import mono, rect, ray_px, dot

# --------------------------------------------------------- criterion glyphs -
# Each glyph appears full size in its own frame (4.2 / 4.4 / 4.6 / 4.8) and
# again, small and muted, as a column header of the matrix.  Same shape both
# times — that is what makes the matrix readable without reading.


def glyph_unique(size=18, gap=12, color=MUTED):
    """Две точки, которые не сливаются."""
    g = VGroup(dot(size, color), dot(size, color))
    g.arrange(RIGHT, buff=px(gap))
    return g


def glyph_equal(w=48, h=42, color=MUTED, r=None):
    """Равносторонний треугольник — все пары одинаково далеки."""
    a = pos(0, h)
    b = pos(w, h)
    c = pos(w / 2, 0)
    g = VGroup(Line(a, b, color=color, stroke_width=S_THIN),
               Line(a, c, color=color, stroke_width=S_THIN),
               Line(b, c, color=color, stroke_width=S_THIN))
    if r:
        for p in (a, b, c):
            g.add(Dot(radius=px(r) / 2, color=ATTR,
                      fill_opacity=1).move_to(p))
    g.move_to(pos(BODY_CX, BODY_CY))
    return g


def glyph_highdim(n=4, w=48, gap=6, color=MUTED, stroke=2):
    """Стопка осей: их много, и все независимы."""
    g = VGroup(*[rect(w, stroke, color, 0, fill=color, fill_opacity=1)
                 for _ in range(n)])
    g.arrange(DOWN, buff=px(gap))
    return g


def glyph_entropy(n=4, w=9, h=24, gap=3, color=MUTED):
    """Плотная полоса: каждое измерение чем-то занято."""
    g = VGroup(*[rect(w, h, color, 0, fill=color, fill_opacity=1)
                 for _ in range(n)])
    g.arrange(RIGHT, buff=px(gap))
    return g


# ------------------------------------------------------------ method glyphs -

def glyph_onehot():
    g = VGroup(rect(18, 12, DIM, S_THIN),
               rect(18, 12, ID, 0, fill=ID, fill_opacity=1),
               rect(18, 12, DIM, S_THIN))
    g.arrange(DOWN, buff=px(2))
    return g


def glyph_binary():
    g = VGroup(rect(12, 18, ID, 0, fill=ID, fill_opacity=1),
               rect(12, 18, ID, S_THIN),
               rect(12, 18, ID, S_THIN),
               rect(12, 18, ID, 0, fill=ID, fill_opacity=1))
    g.arrange(RIGHT, buff=px(3))
    return g


def glyph_hashing():
    slot_x, slot_y = 0, 0
    g = VGroup(ray_px(slot_x, slot_y, 26, 27, ID, S_THIN),
               ray_px(slot_x, slot_y + 24, 26, -27, ID, S_THIN))
    return g


def glyph_qr():
    g = VGroup(rect(18, 12, ID, 0, fill=ID, fill_opacity=1),
               rect(18, 12, ID, 0, fill=ID, fill_opacity=1))
    g.arrange(DOWN, buff=px(4))
    return g


def glyph_bloom():
    g = VGroup(rect(18, 8, ID, 0, fill=ID, fill_opacity=1),
               rect(18, 8, DIM, S_THIN),
               rect(18, 8, ID, 0, fill=ID, fill_opacity=1),
               rect(18, 8, ID, 0, fill=ID, fill_opacity=1))
    g.arrange(DOWN, buff=px(2))
    return g


# ------------------------------------------------------------- the matrix ---
LABEL_W = 270
COL_W = 180
PAD_V = 27
HEAD_PAD_B = 36
HEAD_GAP = 18
LABEL_GAP = 27

COLUMNS = [("unique", glyph_unique), ("equal", glyph_equal),
           ("high dim", glyph_highdim), ("entropy", glyph_entropy)]

METHODS = [("one-hot", glyph_onehot), ("binary", glyph_binary),
           ("hashing", glyph_hashing), ("QR", glyph_qr),
           ("bloom", glyph_bloom)]

# ни один известный метод не проходит все четыре
VERDICTS = {
    "one-hot": ["✓", "✓", "✓", "✗"],
    "binary":  ["✓", "✗", "✗", "✓"],
    "hashing": ["✗", "✓", "✓", "✗"],
    "QR":      ["✓", "~", "✓", "~"],
    "bloom":   ["~", "✓", "✓", "~"],
}

MARK_COLOR = {"✓": ATTR, "✗": ALERT, "~": MUTED}


def criteria_matrix(last_row=None):
    """Build the matrix.  `last_row` fills the sixth row (used by 6.1);
    left as None it stays empty, as кадр 4.9 requires."""
    grid_w = LABEL_W + len(COLUMNS) * COL_W
    left = BODY_CX - grid_w / 2

    col_cx = [left + LABEL_W + j * COL_W + COL_W / 2
              for j in range(len(COLUMNS))]

    # --- measure rows -----------------------------------------------------
    heads = [(name, factory()) for name, factory in COLUMNS]
    head_h = max(g.height * 135 for _, g in heads) + HEAD_GAP + SIZE_MONO
    row_specs = []
    for name, factory in METHODS:
        gl = factory()
        row_specs.append((name, gl, max(gl.height * 135, SIZE_MONO) + 2 * PAD_V))
    empty_h = SIZE_MONO + 2 * PAD_V
    total_h = head_h + HEAD_PAD_B + sum(h for _, _, h in row_specs) + empty_h
    top = BODY_CY - total_h / 2

    g = VGroup()
    g.cells, g.row_labels, g.col_headers, g.rules = {}, {}, {}, VGroup()

    # --- column headers ---------------------------------------------------
    for j, (name, gl) in enumerate(heads):
        lab = mono(name, SIZE_MONO, MUTED)
        block = VGroup(gl, lab)
        block.arrange(DOWN, buff=px(HEAD_GAP))
        block.move_to(pos(col_cx[j], top + head_h / 2))
        g.add(block)
        g.col_headers[name] = block
        block.glyph, block.label = gl, lab

    y = top + head_h + HEAD_PAD_B

    # --- method rows ------------------------------------------------------
    for i, (name, gl, h) in enumerate(row_specs):
        rule = Line(pos(left, y), pos(left + grid_w, y),
                    color=DIM, stroke_width=S_THIN)
        g.add(rule)
        g.rules.add(rule)

        lab = mono(name, SIZE_MONO, MUTED)
        block = VGroup(gl, lab)
        block.arrange(RIGHT, buff=px(LABEL_GAP))
        block.move_to(pos(left, y + h / 2), aligned_edge=LEFT)
        g.add(block)
        g.row_labels[name] = block
        block.glyph, block.label = gl, lab

        for j, mark in enumerate(VERDICTS[name]):
            m = mono(mark, SIZE_MONO, MARK_COLOR[mark])
            m.move_to(pos(col_cx[j], y + h / 2))
            g.add(m)
            g.cells[(name, COLUMNS[j][0])] = m
        y += h

    # --- the empty last row ----------------------------------------------
    top_rule = Line(pos(left, y), pos(left + grid_w, y),
                    color=DIM, stroke_width=S_THIN)
    bot_rule = Line(pos(left, y + empty_h), pos(left + grid_w, y + empty_h),
                    color=DIM, stroke_width=S_THIN)
    g.add(top_rule, bot_rule)
    g.rules.add(top_rule, bot_rule)

    g.last_row_y = y + empty_h / 2
    g.last_row_left = left
    g.col_cx = col_cx
    g.grid_w = grid_w

    if last_row:
        name, marks, colour = last_row
        lab = mono(name, SIZE_MONO, colour)
        lab.move_to(pos(left, g.last_row_y), aligned_edge=LEFT)
        g.add(lab)
        g.dhe_label = lab
        g.dhe_cells = {}
        for j, mark in enumerate(marks):
            m = mono(mark, SIZE_MONO, ATTR)
            m.move_to(pos(g.col_cx[j], g.last_row_y))
            g.add(m)
            g.dhe_cells[COLUMNS[j][0]] = m
    return g


def glyph_dhe():
    """Веер — глиф DHE в последней строке матрицы (кадр 6.1)."""
    g = VGroup(*[ray_px(0, 11, 36, a, ID, S_THIN)
                 for a in (-20, -7, 7, 20)])
    return g


def dim_methods(m, colour=MUTED):
    """6.1: остальные пять строк приглушены, но остаются для сравнения."""
    anims = []
    for name in m.row_labels:
        anims.append(m.row_labels[name].animate.set_color(colour)
                     .set_stroke(colour))
    for key in m.cells:
        anims.append(m.cells[key].animate.set_color(colour))
    return anims
