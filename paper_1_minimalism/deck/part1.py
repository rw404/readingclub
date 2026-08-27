"""Часть 1 — ID и хеши.  Кадры 1.1–1.5.

Идентификаторов чудовищно много, и они произвольны.  Хеш сжимает их в
маленькое пространство — и два разных ID неизбежно попадают в одну ячейку.
"""

import numpy as np
from manim import (
    VGroup, FadeIn, FadeOut, Create, Write, Transform, ReplacementTransform,
    LaggedStart, GrowFromCenter, AnimationGroup, Succession, rate_functions,
    ORIGIN, LEFT, RIGHT, UP, DOWN, DL, DR, UL, UR,
)

from deckkit.base import DeckScene
from deckkit.tokens import (
    px, pos, BG, INK, MUTED, DIM, ID, DEC, ATTR, ALERT,
    SIZE_DISPLAY, SIZE_TITLE, SIZE_MONO, S_THIN, S_MID, S_THICK,
    BODY_CX, BODY_CY, BODY_TOP, BODY_H, GRID,
)
from deckkit.components import (
    caption, chip, cell, cell_row, node, fan, track, mono, sans, text,
    rect, dot, ray_px, line_px, at, flex_row, flex_col, body_center,
    b_indicate, b_wave, b_flash_along, b_flash_group, b_box, b_spark,
    b_focus, b_ripple,
)

VIDEO_ID = "8371102934"
NEIGHBOUR_COLLIDER = "4519920073"

# 1.2 — 25 x 6 field of 150 dots; our identifier is dot #58 (row 2, col 8).
FIELD_COLS, FIELD_ROWS = 25, 6
FIELD_W = 1170
FIELD_PITCH_X = FIELD_W / FIELD_COLS          # 1fr columns + 27 px gap
FIELD_PITCH_Y = 8 + 27
OUR_DOT = 58

# 1.5 — how many identifiers landed in each of the eight drawn cells.
BIN_COUNTS = [5, 7, 4, 6, 5, 3, 6, 4]


def catalogue_field(highlight=OUR_DOT):
    """The dot field of 1.2.  Returns the group, the list of dim dots in
    left-to-right wave order, and the one orange dot."""
    dots, ours = [], None
    left = BODY_CX - FIELD_W / 2
    top = 0.0
    for i in range(FIELD_COLS * FIELD_ROWS):
        r, c = divmod(i, FIELD_COLS)
        x = left + c * FIELD_PITCH_X + 4
        y = top + r * FIELD_PITCH_Y + 4
        if i == highlight:
            d = dot(16, ID)
            ours = d
        else:
            d = dot(8, DIM)
        d.move_to(pos(x, y))
        d.grid_col = c
        dots.append(d)
    g = VGroup(*dots)
    g.dots = dots
    g.ours = ours
    g.dim_dots = [d for d in dots if d is not ours]
    return g


def collision_bins():
    """The eight cells of 1.5 with their identifier dots, packed to the floor."""
    bins = VGroup()
    all_dots = []
    for n in BIN_COUNTS:
        box = rect(90, 180, DIM, S_THIN)
        inner = VGroup()
        rows = (n + 2) // 3
        for k in range(n):
            r, c = divmod(k, 3)
            d = dot(12, ID)
            # rows are packed to the bottom (align-content:flex-end)
            d.move_to(box.get_corner(DL) +
                      np.array([px(8 + 6 + c * 20),
                                px(8 + 6 + (rows - 1 - r) * 20), 0]))
            inner.add(d)
            all_dots.append(d)
        cellgrp = VGroup(box, inner)
        cellgrp.box, cellgrp.dots = box, inner
        bins.add(cellgrp)
    bins.arrange(RIGHT, buff=px(27))
    bins.all_dots = all_dots
    return bins


class Part1(DeckScene):
    """ID и хеши."""

    def construct(self):
        self.f_1_1()
        self.f_1_2()
        self.f_1_3()
        self.f_1_4()
        self.f_1_5()
        self.outro()

    # ------------------------------------------------------------ 1.1 -----
    def f_1_1(self):
        """Пустое поле, в центре появляется chip с числом.  Больше ничего."""
        self.frame("1.1")
        cap = caption("Один идентификатор",
                      "сквозной пример на всю презентацию · "
                      "каталог 10⁸ значений, эмбеддинг 32 числа")
        self.play(FadeIn(cap), run_time=0.8)

        c = chip(VIDEO_ID, ID, SIZE_DISPLAY, pad=(45, 90), stroke=S_MID,
                 weight="MEDIUM")
        body_center(c)
        self.cap = cap
        self.the_chip = c

        # layer 1: chip appears;  layer 2: the number resolves inside it
        self.play(Create(c.box), run_time=1.2)
        self.play(Write(c.label), run_time=1.4)
        self.settle(b_box(c.box, ID), b_indicate(c.label, ID))

    # ------------------------------------------------------------ 1.2 -----
    def f_1_2(self):
        """Поле точек заполняется волной; одна точка загорается оранжевым."""
        self.frame("1.2")
        cap = caption("Столько идентификаторов в каталоге",
                      "точки условны, число — настоящее: 100 000 000 видео")

        field = catalogue_field()
        count = text("100 000 000", SIZE_DISPLAY, MUTED, weight="MEDIUM")
        block = flex_col(field, count, gap=90)
        body_center(block)

        # morph: chip → одна точка в поле каталога
        self.play(
            Transform(self.cap, cap),
            ReplacementTransform(self.the_chip, field.ours),
            run_time=1.2,
        )
        # layer 1: the field fills in as a wave, left to right
        by_col = sorted(field.dim_dots, key=lambda d: d.grid_col)
        self.play(
            LaggedStart(*[FadeIn(d, scale=0.4) for d in by_col],
                        lag_ratio=0.012),
            run_time=3.0,
        )
        # layer 2: our dot flares
        self.play(field.ours.animate.scale(1.6), run_time=0.4)
        self.play(field.ours.animate.scale(1 / 1.6), run_time=0.4)
        # layer 3: the number, last
        self.play(FadeIn(count, shift=UP * px(20)), run_time=0.9)

        self.field = field
        self.count_1_2 = count
        self.settle(b_spark(field.ours, ID),
                    b_wave(by_col[::7], MUTED, 1.4, 0.04, 1.4),
                    b_indicate(count, MUTED))

    # ------------------------------------------------------------ 1.3 -----
    def f_1_3(self):
        """Слева контур большого пространства, справа — маленького."""
        self.frame("1.3")
        cap = caption("Хеш сжимает пространство",
                      "h: 1…10⁸ → 1…10⁶ · пространство сжато в 100 раз")

        big = rect(270, 450, DIM, S_THIN)
        big_lab = mono("10⁸", SIZE_MONO, MUTED)
        left_col = flex_col(big, big_lab, gap=45)

        funnel_slot = rect(360, 450, BG, 0)          # spacer, never drawn
        funnel_slot.set_opacity(0)

        small = rect(90, 90, ID, S_MID)
        small_lab = mono("10⁶", SIZE_MONO, ID)
        right_col = flex_col(small, small_lab, gap=45)

        row = flex_row(left_col, funnel_slot, right_col, gap=90)
        body_center(row)

        # the two funnel lines live in the 360x450 slot, 392 px long at ±23°
        ox = (funnel_slot.get_left()[0] * 135) + 960
        oy_top = 540 - funnel_slot.get_top()[1] * 135
        oy_bot = 540 - funnel_slot.get_bottom()[1] * 135
        f_top = ray_px(ox, oy_top, 392, 23, DIM, S_THIN)
        f_bot = ray_px(ox, oy_bot, 392, -23, DIM, S_THIN)
        funnel = VGroup(f_top, f_bot)

        # morph: поле точек → вход воронки
        self.play(
            Transform(self.cap, cap),
            ReplacementTransform(self.field, big),
            FadeOut(self.count_1_2, shift=DOWN * px(20)),
            run_time=1.3,
        )
        self.play(FadeIn(big_lab), run_time=0.5)
        # layer 2: the small space
        self.play(Create(small), run_time=0.9)
        # layer 3: the funnel
        self.play(Create(f_top), Create(f_bot), run_time=1.1)
        # layer 4: the numbers, last — nothing is coloured but the exit
        self.play(FadeIn(small_lab), run_time=0.6)

        self.big, self.small, self.funnel = big, small, funnel
        self.labels_1_3 = VGroup(big_lab, small_lab)
        self.settle(b_flash_group(funnel, ID, 6, 0.1, 1.4),
                    b_box(small, ID))

    # ------------------------------------------------------------ 1.4 -----
    def f_1_4(self):
        """Два идентификатора идут по стрелкам в одну ячейку."""
        self.frame("1.4")
        cap = caption("Два идентификатора — одна ячейка",
                      "h(8371102934) = h(4519920073) → одна строка → "
                      "один эмбеддинг на двоих")

        chip_a = chip(VIDEO_ID, ID, SIZE_MONO, pad=(18, 27), stroke=S_THIN)
        chip_b = chip(NEIGHBOUR_COLLIDER, ID, SIZE_MONO, pad=(18, 27),
                      stroke=S_THIN)
        chips = flex_col(chip_a, chip_b, gap=135)

        arrow_slot = rect(270, 270, BG, 0)
        arrow_slot.set_opacity(0)

        bucket = rect(90, 90, ALERT, S_MID)
        stem = rect(90, 2, ALERT, 0, fill=ALERT, fill_opacity=1)

        vec_w, vec_gap, vec_n = 360, 4, 8
        cw = (vec_w - vec_gap * (vec_n - 1)) / vec_n
        vector = VGroup(*[rect(cw, 45, ALERT, 0, fill=ALERT, fill_opacity=1)
                          for _ in range(vec_n)])
        vector.arrange(RIGHT, buff=px(vec_gap))

        row = flex_row(chips, arrow_slot, bucket, stem, vector, gap=90)
        body_center(row)

        ox = (arrow_slot.get_left()[0] * 135) + 960
        oy_top = 540 - arrow_slot.get_top()[1] * 135
        oy_bot = 540 - arrow_slot.get_bottom()[1] * 135
        a_top = ray_px(ox, oy_top, 292, 27, ID, S_THIN)
        a_bot = ray_px(ox, oy_bot, 292, -27, ID, S_THIN)

        # layer 1: two chips — the left one is the identifier we already know
        self.play(
            Transform(self.cap, cap),
            ReplacementTransform(self.big, chip_a),
            FadeOut(self.labels_1_3),
            run_time=1.1,
        )
        self.play(FadeIn(chip_b), run_time=0.6)
        # layer 2: воронка → две сходящиеся стрелки коллизии
        self.play(
            ReplacementTransform(self.funnel[0], a_top),
            ReplacementTransform(self.funnel[1], a_bot),
            run_time=1.2,
        )
        # layer 3: обе стрелки приходят в одну ячейку
        self.play(ReplacementTransform(self.small, bucket), run_time=1.0)
        # layer 4: и выходят одним красным вектором
        self.play(Create(stem), run_time=0.5)
        self.play(
            LaggedStart(*[GrowFromCenter(c) for c in vector], lag_ratio=0.08),
            run_time=1.2,
        )

        self.vector_1_4 = vector
        self.bucket = bucket
        self.dead = VGroup(chip_a, chip_b, a_top, a_bot, stem)
        self.settle(b_flash_group(VGroup(a_top, a_bot), ID, 6, 0.0, 1.2),
                    b_box(bucket, ALERT),
                    b_wave(vector, ALERT, 1.15, 0.05, 1.2))

    # ------------------------------------------------------------ 1.5 -----
    def f_1_5(self):
        """Точки сыплются в ряд ячеек, пока в каждой не окажется по нескольку."""
        self.frame("1.5")
        cap = caption("Коллизия неизбежна",
                      "10⁸ / 10⁶ = 100 идентификаторов на ячейку · "
                      "доля ячеек с одним ID ≈ 4 × 10⁻⁴²")

        bins = collision_bins()
        avg = text("100", SIZE_DISPLAY, ALERT, weight="MEDIUM")
        pure = text("≈ 0", SIZE_DISPLAY, MUTED, weight="MEDIUM")
        numbers = flex_row(avg, pure, gap=135)
        block = flex_col(bins, numbers, gap=90)
        body_center(block)

        boxes = VGroup(*[b.box for b in bins])

        # layer 1: ряд ячеек — the single bucket of 1.4 becomes the whole row
        self.play(
            Transform(self.cap, cap),
            ReplacementTransform(self.bucket, boxes[0]),
            FadeOut(self.vector_1_4), FadeOut(self.dead),
            run_time=1.2,
        )
        self.play(
            LaggedStart(*[Create(b) for b in boxes[1:]], lag_ratio=0.1),
            run_time=1.2,
        )
        # layer 2: точки падают в ячейки
        falling = []
        for b in bins:
            for d in b.dots:
                start = d.copy().shift(UP * px(360)).set_opacity(0)
                d.save_state()
                d.move_to(start.get_center())
                d.set_opacity(0)
                falling.append(d)
        self.play(
            LaggedStart(*[d.animate.restore() for d in falling],
                        lag_ratio=0.02),
            run_time=2.6, rate_func=rate_functions.ease_out_quad,
        )
        # layers 3 and 4: счётчик и доля чистых ячеек
        self.play(FadeIn(avg, shift=UP * px(20)), run_time=0.7)
        self.play(FadeIn(pure, shift=UP * px(20)), run_time=0.7)
        self.settle(b_wave(bins.all_dots, ID, 1.35, 0.02, 1.8),
                    b_indicate(avg, ALERT),
                    b_indicate(pure, MUTED))
