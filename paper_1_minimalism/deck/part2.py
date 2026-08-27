"""Часть 2 — OOV и память.  Кадры 2.1–2.4.

Два разных провала таблицы: приходит ID, которого не было при обучении —
место есть, содержимого нет; и 10⁸ × 32 × 4 Б = 12.8 ГБ, которые ещё и растут.
"""

import numpy as np
from manim import (
    VGroup, FadeIn, FadeOut, Create, Write, Transform, ReplacementTransform,
    LaggedStart, GrowFromEdge, GrowFromCenter, rate_functions,
    ORIGIN, LEFT, RIGHT, UP, DOWN, DL, DR, UL, UR,
)

from deckkit.base import DeckScene
from deckkit.tokens import (
    px, pos, BG, INK, MUTED, DIM, ID, DEC, ATTR, ALERT,
    SIZE_DISPLAY, SIZE_TITLE, SIZE_MONO, S_THIN, S_MID, S_THICK,
    BODY_CX, BODY_CY, BODY_TOP, BODY_BOTTOM, BODY_H,
)
from deckkit.components import (
    caption, chip, mono, sans, text, rect, ray_px, line_px, at,
    flex_row, flex_col, body_center,
    b_indicate, b_wave, b_flash_along, b_flash_group, b_box, b_spark,
)

VIDEO_ID = "8371102934"

# 2.1 — five table rows; the fourth is the one that does not exist.
ROW_W, ROW_H, ROW_GAP = 540, 45, 8
MISSING_ROW = 3

# 2.2 — five unknown identifiers converge on one <unk> row.
UNK_LINES = [(18, 284, 31), (99, 274, 17), (180, 270, 0),
             (261, 274, -17), (342, 284, -31)]

# 2.4 — twelve months, +128 МБ each; heights are % of the working area.
GROWTH_PCT = [41, 44, 47, 50, 53, 56, 59, 62, 65, 68, 71, 74]


class Part2(DeckScene):
    """OOV и память."""

    def construct(self):
        self.f_2_1()
        self.f_2_2()
        self.f_2_3()
        self.f_2_4()
        self.outro()

    # ------------------------------------------------------------ 2.1 -----
    def f_2_1(self):
        """Стрелка проходит строки одну за другой и останавливается на пустом
        контуре.  Пустота — это и есть поломка."""
        self.frame("2.1")
        cap = caption("Новый идентификатор: строки нет",
                      "словарь фиксируется при обучении · "
                      "для значения вне словаря строки не существует")

        c = chip(VIDEO_ID, ID, SIZE_MONO, pad=(18, 27), stroke=S_THIN)
        pointer = rect(90, 2, MUTED, 0, fill=MUTED, fill_opacity=1)

        rows = VGroup()
        for i in range(5):
            if i == MISSING_ROW:
                r = rect(ROW_W, ROW_H, ALERT, S_THIN)   # место есть, строки нет
            else:
                r = rect(ROW_W, ROW_H, DIM, 0, fill=DIM, fill_opacity=1)
            rows.add(r)
        rows.arrange(DOWN, buff=px(ROW_GAP))

        row = flex_row(c, pointer, rows, gap=90)
        body_center(row)

        self.play(FadeIn(cap), run_time=0.8)
        self.cap = cap

        # layer 1: стопка строк
        blanks = VGroup(*[r for i, r in enumerate(rows) if i != MISSING_ROW])
        empty = rows[MISSING_ROW]
        empty_ghost = rect(ROW_W, ROW_H, DIM, S_THIN).move_to(empty.get_center())
        self.play(
            LaggedStart(*[GrowFromEdge(r, LEFT) for r in blanks],
                        lag_ratio=0.12),
            run_time=1.4,
        )
        self.play(Create(empty_ghost), run_time=0.5)

        # layer 2: chip приходит сверху
        c.save_state()
        c.shift(UP * px(300)).set_opacity(0)
        self.play(c.animate.restore(), run_time=1.0,
                  rate_func=rate_functions.ease_out_cubic)

        # layer 3: стрелка ищет — строки проверяются одна за другой
        self.play(FadeIn(pointer), run_time=0.4)
        for i, r in enumerate(rows):
            probe = r.copy().set_stroke(MUTED, S_THIN).set_fill(opacity=
                                                                0 if i == MISSING_ROW else 1)
            self.play(r.animate.set_stroke(MUTED, S_THIN), run_time=0.22)
            if i != MISSING_ROW:
                self.play(r.animate.set_stroke(DIM, 0), run_time=0.18)

        # layer 4: пустой контур краснеет
        self.play(
            empty_ghost.animate.set_stroke(ALERT, S_THIN),
            rows[MISSING_ROW].animate.set_stroke(ALERT, S_THIN),
            run_time=0.8,
        )
        self.remove(empty_ghost)
        self.add(empty)

        self.unk_row = empty
        self.dead_2_1 = VGroup(c, pointer, blanks)
        self.settle(b_wave(rows, MUTED, 1.03, 0.12, 1.5),
                    b_box(empty, ALERT),
                    b_flash_along(pointer, MUTED, 6, 0.9))

    # ------------------------------------------------------------ 2.2 -----
    def f_2_2(self):
        """Пять незнакомых идентификаторов упираются в одну и ту же строку."""
        self.frame("2.2")
        cap = caption("Все незнакомые делят одну строку",
                      "один вектор <unk> на весь хвост словаря — "
                      "сколько бы значений в него ни попало")

        chips = VGroup(*[rect(270, 36, ID, S_THIN) for _ in range(5)])
        chips.arrange(DOWN, buff=px(27))

        rays_slot = rect(270, 360, BG, 0)
        rays_slot.set_opacity(0)

        unk = rect(360, 45, ALERT, 0, fill=ALERT, fill_opacity=1)

        row = flex_row(chips, rays_slot, unk, gap=135)
        body_center(row)

        ox = rays_slot.get_left()[0] * 135 + 960
        oy = 540 - rays_slot.get_top()[1] * 135
        rays = VGroup(*[ray_px(ox, oy + top, w, a, MUTED, S_THIN)
                        for top, w, a in UNK_LINES])

        # morph: пустой контур → строка <unk>
        self.play(
            Transform(self.cap, cap),
            ReplacementTransform(self.unk_row, unk),
            FadeOut(self.dead_2_1),
            run_time=1.2,
        )
        # layer 2: пять chip прилетают
        self.play(
            LaggedStart(*[FadeIn(c, shift=RIGHT * px(60)) for c in chips],
                        lag_ratio=0.15),
            run_time=1.8,
        )
        # layer 3: стрелки сходятся в неё — строка не меняется от того,
        # сколько их пришло
        self.play(
            LaggedStart(*[Create(r) for r in rays], lag_ratio=0.12),
            run_time=1.8,
        )
        self.unk_bar = unk
        self.dead_2_2 = VGroup(chips, rays)
        self.settle(b_flash_group(rays, MUTED, 6, 0.1, 1.6),
                    b_indicate(unk, ALERT))

    # ------------------------------------------------------------ 2.3 -----
    def f_2_3(self):
        """Из одной строки разворачивается площадь всей таблицы."""
        self.frame("2.3")
        cap = caption("Размер одной таблицы",
                      "10⁸ строк × 32 числа × 4 байта = 12.8 ГБ · "
                      "одна строка = 128 байт")

        one = rect(45, 45, ID, 0, fill=ID, fill_opacity=1)
        one_lab = mono("128 Б", SIZE_MONO, ID)
        left_col = flex_col(one, one_lab, gap=45)

        table = rect(540, 540, DIM, 0, fill=DIM, fill_opacity=1)
        table_lab = text("12.8 ГБ", SIZE_DISPLAY, INK, weight="MEDIUM")
        mid_col = flex_col(table, table_lab, gap=45)

        factors = VGroup(mono("10⁸", SIZE_MONO, MUTED),
                         mono("× 32", SIZE_MONO, MUTED),
                         mono("× 4 Б", SIZE_MONO, MUTED))
        factors.arrange(DOWN, buff=px(SIZE_MONO * 0.6), aligned_edge=LEFT)

        row = flex_row(left_col, mid_col, factors, gap=135)
        body_center(row)

        # the original row stays visible inside the big square, at its corner
        seed = rect(8, 8, ID, 0, fill=ID, fill_opacity=1)
        seed.move_to(table.get_corner(UL), aligned_edge=UL)

        # morph: строка <unk> → одна ячейка большой таблицы
        self.play(
            Transform(self.cap, cap),
            ReplacementTransform(self.unk_bar, one),
            FadeOut(self.dead_2_2),
            run_time=1.2,
        )
        self.play(FadeIn(one_lab), run_time=0.5)
        # layer 2: большой квадрат разворачивается из малого
        table.save_state()
        table.stretch_to_fit_width(px(45)).stretch_to_fit_height(px(45))
        table.move_to(one.get_center())
        self.add(table)
        self.play(table.animate.restore(), run_time=1.6,
                  rate_func=rate_functions.ease_out_cubic)
        self.play(FadeIn(seed), run_time=0.4)
        # layer 3: числа появляются последними
        self.play(
            LaggedStart(*[FadeIn(f, shift=UP * px(12)) for f in factors],
                        lag_ratio=0.2),
            run_time=1.0,
        )
        self.play(FadeIn(table_lab, shift=UP * px(20)), run_time=0.8)

        self.table = table
        self.dead_2_3 = VGroup(one, one_lab, factors, table_lab, seed)
        self.settle(b_spark(seed, ID), b_box(table, MUTED),
                    b_indicate(table_lab, INK))

    # ------------------------------------------------------------ 2.4 -----
    def f_2_4(self):
        """Двенадцать столбиков встают по одному; прирост постоянный."""
        self.frame("2.4")
        cap = caption("Каталог растёт — таблица тоже",
                      "+1 млн видео в месяц → +128 МБ в месяц · "
                      "12.80 ГБ → 14.34 ГБ за год")

        bars = VGroup()
        for i, p in enumerate(GROWTH_PCT):
            col = ID if i == len(GROWTH_PCT) - 1 else DIM
            bars.add(rect(63, BODY_H * p / 100, col, 0, fill=col,
                          fill_opacity=1))
        rate = mono("+128 МБ / мес", SIZE_MONO, ID)

        row = VGroup(bars, rate)
        bars.arrange(RIGHT, buff=px(27), aligned_edge=DOWN)
        row.arrange(RIGHT, buff=px(27), aligned_edge=DOWN)
        row.move_to(pos(BODY_CX, BODY_BOTTOM), aligned_edge=DOWN)

        # layer 1: ось
        axis = line_px(0, 0, 1, 0, MUTED, S_THIN)
        axis.put_start_and_end_on(
            bars.get_corner(DL) + LEFT * px(27),
            bars.get_corner(DR) + RIGHT * px(27),
        )

        # morph: большой квадрат → первый столбик роста
        self.play(
            Transform(self.cap, cap),
            ReplacementTransform(self.table, bars[0]),
            FadeOut(self.dead_2_3),
            run_time=1.2,
        )
        self.play(Create(axis), run_time=0.6)
        # layer 2: столбики по одному, 0.15 с на месяц
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars[1:]],
                        lag_ratio=1.0),
            run_time=0.15 * (len(bars) - 1),
        )
        # layer 3: линия тренда — прирост постоянный, и остановиться не может
        trend = line_px(0, 0, 1, 0, MUTED, S_THIN)
        trend.put_start_and_end_on(bars[0].get_top(), bars[-1].get_top())
        self.play(Create(trend), run_time=1.0)
        # layer 4: счётчик
        self.play(FadeIn(rate, shift=UP * px(12)), run_time=0.7)
        self.settle(b_wave(bars, ID, 1.04, 0.07, 1.6),
                    b_flash_along(trend, INK, 5, 1.2),
                    b_indicate(rate, ID))
