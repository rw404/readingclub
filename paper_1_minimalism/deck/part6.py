"""Часть 6 — DHE против критериев.  Кадры 6.1–6.2.

Возврат к главному кадру.  Матрица не перерисовывается: она собирается той же
функцией, что и в 4.9, ставится в то же место в том же состоянии, и дальше
меняется только то, что говорит сториборд — строки методов гаснут до muted,
последняя строка заполняется.
"""

import numpy as np
from manim import (
    VGroup, Line, FadeIn, FadeOut, Create, Transform, ReplacementTransform,
    LaggedStart, GrowFromCenter, ORIGIN, LEFT, RIGHT, UP, DOWN,
)

from deckkit.base import DeckScene
from deckkit.tokens import (
    px, pos, BG, INK, MUTED, DIM, ID, DEC, ATTR, ALERT, FONT_SANS, FONT_MONO,
    SIZE_DISPLAY, SIZE_TITLE, SIZE_MONO, S_THIN, S_MID,
    BODY_CX, BODY_CY, BODY_TOP, BODY_BOTTOM, BODY_LEFT, BODY_W,
)
from deckkit.components import (
    caption, mono, sans, text, rect, line_px, dot, flex_row, flex_col,
    body_center, para,
    b_indicate, b_wave, b_flash_along, b_flash_group, b_box, b_spark,
)
from deck.matrix import criteria_matrix, glyph_dhe, dim_methods, COLUMNS

# 6.2 — что именно обеспечивает каждую галочку
MECHANISMS = ["1024 хеша", "независимые a, b", "k = 1024", "10⁶ на измерение"]


class Part6(DeckScene):
    """DHE против критериев."""

    def construct(self):
        self.f_6_1()
        self.f_6_2()
        self.outro()

    # ------------------------------------------------------------ 6.1 -----
    def f_6_1(self):
        """Возврат к главному кадру: это тот же кадр, а не новый."""
        self.frame("6.1")
        cap = caption("Строка DHE",
                      "все четыре критерия выполнены · остальные пять строк "
                      "приглушены, но остаются для сравнения")

        # layer 1: матрица из 4.9 возвращается — тот же объект, тот же монтаж,
        # поэтому она просто стоит на месте, её никто не рисует заново
        m = criteria_matrix()
        self.add(m)
        self.matrix = m
        self.play(FadeIn(cap), run_time=0.8)
        self.cap = cap
        self.wait(0.8)

        # остальные строки приглушаются
        self.play(*dim_methods(m), run_time=1.2)

        # layer 2: глиф веера в пятой строке
        fan = glyph_dhe()
        label = mono("DHE", SIZE_MONO, ID)
        block = VGroup(fan, label)
        block.arrange(RIGHT, buff=px(27))
        block.move_to(pos(m.last_row_left, m.last_row_y), aligned_edge=LEFT)

        rule_top = Line(pos(m.last_row_left, m.last_row_y - 41),
                        pos(m.last_row_left + m.grid_w, m.last_row_y - 41),
                        color=ID, stroke_width=S_MID)
        rule_bot = Line(pos(m.last_row_left, m.last_row_y + 41),
                        pos(m.last_row_left + m.grid_w, m.last_row_y + 41),
                        color=ID, stroke_width=S_MID)

        self.play(FadeIn(block, shift=RIGHT * px(18)),
                  Create(rule_top), Create(rule_bot), run_time=1.2)

        # layer 3: четыре галочки по очереди
        ticks = VGroup()
        for j, (name, _) in enumerate(COLUMNS):
            t = mono("✓", SIZE_MONO, ATTR)
            t.move_to(pos(m.col_cx[j], m.last_row_y))
            ticks.add(t)
        self.play(
            LaggedStart(*[FadeIn(t, scale=0.5) for t in ticks], lag_ratio=0.4),
            run_time=2.4,
        )
        self.ticks = ticks
        self.dhe_row = VGroup(block, rule_top, rule_bot)
        self.settle(b_wave(ticks, ATTR, 1.25, 0.14, 1.4),
                    b_flash_group(VGroup(rule_top, rule_bot), ID, 6, 0.1, 1.3),
                    b_indicate(block, ID))

    # ------------------------------------------------------------ 6.2 -----
    def f_6_2(self):
        """Под каждой галочкой встаёт механизм, который её обеспечивает."""
        self.frame("6.2")
        cap = caption("Каждая галочка — из конструкции",
                      "ни одно свойство не получено случайно — "
                      "у каждого свой механизм")

        col_w = (BODY_W - 3 * 90) / 4
        cols = VGroup()
        for k, mech in enumerate(MECHANISMS):
            tick = text("✓", SIZE_TITLE, ATTR, font=FONT_SANS, weight="MEDIUM")
            stem = rect(2, 63, DIM, 0, fill=DIM, fill_opacity=1)
            lab = para(mech, col_w, SIZE_MONO, ID, align="center")
            c = VGroup(tick, stem, lab)
            c.arrange(DOWN, buff=px(36))
            c.move_to(pos(BODY_LEFT + k * (col_w + 90) + col_w / 2, BODY_CY))
            c.tick, c.stem, c.lab = tick, stem, lab
            cols.add(c)

        # morph: четыре галочки матрицы → четыре галочки механизмов
        self.play(
            Transform(self.cap, cap),
            FadeOut(self.matrix), FadeOut(self.dhe_row),
            *[ReplacementTransform(a, b.tick)
              for a, b in zip(self.ticks, cols)],
            run_time=1.6,
        )
        # layer 2: стрелки вниз
        self.play(
            LaggedStart(*[Create(c.stem) for c in cols], lag_ratio=0.15),
            run_time=1.2,
        )
        # layer 3: механизмы под ними
        self.play(
            LaggedStart(*[FadeIn(c.lab, shift=UP * px(16)) for c in cols],
                        lag_ratio=0.2),
            run_time=1.6,
        )
        self.ticks_out = VGroup(*[c.tick for c in cols])
        self.settle(b_wave(VGroup(*[c.tick for c in cols]), ATTR, 1.2, 0.16, 1.4),
                    b_flash_group(VGroup(*[c.stem for c in cols]), INK, 5,
                                  0.16, 1.3),
                    b_wave(VGroup(*[c.lab for c in cols]), ID, 1.06, 0.16, 1.3))
