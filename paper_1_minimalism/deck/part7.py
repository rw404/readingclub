"""Часть 7 — Side features.  Кадры 7.1–7.6.

Вектор-идентификатор — не единственное, что можно подать декодеру.  В таблице
так нельзя в принципе.  Кульминация — новое видео: идентификационная половина
входа шум, половина с атрибутами полна смысла.
"""

import numpy as np
from manim import (
    VGroup, Line, DashedLine, FadeIn, FadeOut, Create, Transform,
    ReplacementTransform, LaggedStart, GrowFromEdge, GrowFromCenter,
    rate_functions, ORIGIN, LEFT, RIGHT, UP, DOWN, DL, DR, UL, UR,
)

from deckkit.base import DeckScene
from deck.data import abs_dots
from deckkit.tokens import (
    px, pos, BG, INK, MUTED, DIM, ID, DEC, ATTR, ALERT, FONT_MONO,
    SIZE_DISPLAY, SIZE_TITLE, SIZE_MONO, S_THIN, S_MID,
    BODY_CX, BODY_CY, BODY_TOP, BODY_BOTTOM, BODY_H, BODY_LEFT, BODY_W,
)
from deckkit.components import (
    caption, mono, sans, text, rect, line_px, dot, flex_row, flex_col,
    body_center, para,
    b_indicate, b_wave, b_flash_along, b_flash_group, b_box, b_spark,
)

INPUT_W = 1350          # ширина полосы входа на 7.1 и 7.4
MAP_W = 1170            # карта кластеров 7.3 / 7.5


def input_strip(height, parts, gap=8, width=INPUT_W):
    """CSS `display:flex` с `flex:N` — ширины пропорциональны размерностям."""
    total = sum(n for n, _, _ in parts)
    avail = width - gap * (len(parts) - 1)
    g = VGroup()
    for n, colour, opacity in parts:
        w = avail * n / total
        g.add(rect(w, height, colour, 0, fill=colour, fill_opacity=opacity))
    g.arrange(RIGHT, buff=px(gap))
    return g


def cluster_map(screen, width=MAP_W, height=None, box_color=DIM):
    """The 2-D projection of 7.3 / 7.5 — a bordered plane with its points."""
    height = height or BODY_H
    box = rect(width, height, box_color, S_THIN)
    box.move_to(pos(BODY_CX, BODY_CY))
    pts = VGroup()
    for l, t, colour, opacity, size in abs_dots(screen):
        d = dot(size, colour).set_opacity(opacity)
        d.move_to(box.get_corner(UL) +
                  np.array([px(width * l / 100 + size / 2),
                            -px(height * t / 100 + size / 2), 0]))
        d.spec = (colour, opacity, size)
        pts.add(d)
    g = VGroup(box, pts)
    g.box, g.pts = box, pts
    return g


class Part7(DeckScene):
    """Side features."""

    def construct(self):
        self.f_7_1()
        self.f_7_2()
        self.f_7_3()
        self.f_7_4()
        self.f_7_5()
        self.f_7_6()
        self.outro()

    # ------------------------------------------------------------ 7.1 -----
    def f_7_1(self):
        """К вектору-идентификатору справа пристраивается блок атрибутов."""
        self.frame("7.1")
        cap = caption("Атрибуты дописываются ко входу",
                      "1024 хеша + 32 категориальных + 2 числовых = 1058 · "
                      "первый слой растёт на 34 816 параметров, +1.63 %")

        strip = input_strip(135, [(1024, ID, 1.0), (32, ATTR, 1.0),
                                  (2, ATTR, 1.0)])
        sums = VGroup(mono("1024", SIZE_MONO, ID),
                      mono("+ 34", SIZE_MONO, ATTR),
                      mono("= 1058", SIZE_MONO, MUTED))
        sums.arrange(RIGHT, buff=px(63))
        block = flex_col(strip, sums, gap=63)
        body_center(block)

        self.play(FadeIn(cap), run_time=0.8)
        self.cap = cap
        # layer 1: полоса identity
        self.play(GrowFromEdge(strip[0], LEFT), run_time=1.2)
        # layer 2: салатовая полоса пристраивается справа
        self.play(
            LaggedStart(GrowFromEdge(strip[1], LEFT),
                        GrowFromEdge(strip[2], LEFT), lag_ratio=0.4),
            run_time=1.2,
        )
        # layer 3: сумма длин
        self.play(
            LaggedStart(*[FadeIn(s, shift=UP * px(12)) for s in sums],
                        lag_ratio=0.25),
            run_time=1.2,
        )
        self.strip = strip
        self.dead = VGroup(sums)
        self.settle(b_indicate(strip[0], ID),
                    b_wave(VGroup(strip[1], strip[2]), ATTR, 1.3, 0.15, 1.0),
                    b_wave(sums, None, 1.08, 0.16, 1.1))

    # ------------------------------------------------------------ 7.2 -----
    def f_7_2(self):
        """Салатовый блок пытается встать между строками и не находит куда."""
        self.frame("7.2")
        cap = caption("В таблице места нет",
                      "ключ строки — только ID · чтобы добавить атрибут, "
                      "нужна строка на каждую пару (ID, атрибут)")

        rows = VGroup(*[rect(630, 45, DIM, 0, fill=DIM, fill_opacity=1)
                        for _ in range(4)])
        rows.arrange(DOWN, buff=px(45))

        ghost = rect(180, 45, ATTR, 0)
        dash = VGroup()
        for a, b in ((UL, UR), (UR, DR), (DR, DL), (DL, UL)):
            dash.add(DashedLine(ghost.get_corner(a), ghost.get_corner(b),
                                color=ATTR, stroke_width=S_THIN,
                                dash_length=px(10)))
        dash.set_stroke(opacity=0.4)
        refuse = mono("✗", SIZE_MONO, ALERT)
        attempt = flex_col(dash, refuse, gap=27)
        row = flex_row(rows, attempt, gap=90)
        body_center(row)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: строки таблицы — каждая изолирована
        self.play(ReplacementTransform(self.strip, rows[0]), run_time=1.1)
        self.play(
            LaggedStart(*[GrowFromEdge(r, LEFT) for r in rows[1:]],
                        lag_ratio=0.15),
            run_time=1.4,
        )
        # layer 2: попытка положить общее знание между строками
        self.play(Create(dash), run_time=0.9)
        for gap_i in (0, 1, 2):
            self.play(
                dash.animate.move_to(
                    (rows[gap_i].get_center() + rows[gap_i + 1].get_center()) / 2
                    + RIGHT * px(0)),
                run_time=0.35,
            )
        self.play(dash.animate.move_to(attempt[0].get_center()), run_time=0.4)
        # layer 3: отказ — это структурное ограничение
        self.play(FadeIn(refuse, scale=0.6), run_time=0.6)
        self.play(dash.animate.set_stroke(opacity=0.4), run_time=0.4)
        self.rows_7_2 = rows
        self.dead = VGroup(dash, refuse)
        self.settle(b_wave(rows, MUTED, 1.03, 0.12, 1.3),
                    b_flash_group(dash, ATTR, 5, 0.06, 1.1),
                    b_spark(refuse, ALERT))

    # ------------------------------------------------------------ 7.3 -----
    def f_7_3(self):
        """Точки перекрашиваются по значению атрибута."""
        self.frame("7.3")
        cap = caption("Близкие атрибуты — близкие эмбеддинги",
                      "декодер видел миллионы примеров с теми же атрибутами — "
                      "гладкость появляется сама")

        m = cluster_map("7.3")

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # morph: изолированные строки → карта кластеров
        self.play(ReplacementTransform(self.rows_7_2, m.box), run_time=1.2)
        # layer 1: точки появляются серыми
        grey = [d.copy().set_color(DIM).set_opacity(1) for d in m.pts]
        self.play(
            LaggedStart(*[GrowFromCenter(g) for g in grey], lag_ratio=0.02),
            run_time=1.8,
        )
        # layer 2: перекрашиваются по атрибуту
        self.play(
            *[Transform(g, d) for g, d in zip(grey, m.pts)],
            run_time=1.6,
        )
        self.remove(*grey)
        self.add(m.pts)
        # layer 3: у одного видео атрибут плавно меняется — точка едет
        traveller = m.pts[0]
        start = traveller.get_center()
        self.play(traveller.animate.move_to(m.pts[13].get_center() +
                                            np.array([px(60), px(40), 0])),
                  run_time=1.6, rate_func=rate_functions.ease_in_out_sine)
        self.play(traveller.animate.move_to(start), run_time=1.2,
                  rate_func=rate_functions.ease_in_out_sine)
        self.map_7_3 = m
        # атрибут одного видео плавно меняется — точка едет непрерывно
        self.settle(b_wave(VGroup(*m.pts[24:]), ATTR, 1.25, 0.04, 1.3),
                    b_wave(VGroup(*m.pts[12:24]), ATTR, 1.25, 0.04, 1.3),
                    b_wave(VGroup(*m.pts[:12]), ATTR, 1.25, 0.04, 1.3))

    # ------------------------------------------------------------ 7.4 -----
    def f_7_4(self):
        """Контраст двух половин — всё содержание кадра."""
        self.frame("7.4")
        cap = caption("Половина шум, половина смысл",
                      "у нового видео 1024 хеша сети незнакомы, "
                      "а 34 числа атрибутов знакомы полностью")

        strip = input_strip(270, [(1024, DIM, 1.0), (34, ATTR, 1.0)])
        body_center(strip)

        self.play(Transform(self.cap, cap), FadeOut(self.map_7_3),
                  run_time=1.0)
        # layer 1: полоса входа — сначала целиком «своя»
        whole = input_strip(270, [(1024, ID, 1.0), (34, ATTR, 1.0)])
        body_center(whole)
        self.play(GrowFromEdge(whole, LEFT), run_time=1.2)
        # layer 2: левая часть сереет — такой комбинации сеть не видела
        self.play(whole[0].animate.set_fill(DIM, 1).set_color(DIM),
                  run_time=1.6)
        # layer 3: правая остаётся салатовой
        self.play(whole[1].animate.scale(1.06), run_time=0.5)
        self.play(whole[1].animate.scale(1 / 1.06), run_time=0.5)
        self.split_strip = whole
        self.settle(b_indicate(whole[1], ATTR, 1.25),
                    b_flash_along(whole[0], MUTED, 8, 1.4),
                    b_box(whole[1], ATTR))

    # ------------------------------------------------------------ 7.5 -----
    def f_7_5(self):
        """Новая точка приземляется внутрь своей области с первого показа."""
        self.frame("7.5")
        cap = caption("Новое видео попадает в область",
                      "без единого обновления весов · "
                      "таблица на этом входе не имеет строки вовсе")

        m = cluster_map("7.5")
        newcomer = m.pts[-1]            # the 45 px dot is the new video

        self.play(Transform(self.cap, cap), run_time=0.8)
        # layers 1-2: карта возвращается, остальные точки гаснут
        self.play(Create(m.box), run_time=0.8)
        self.play(
            LaggedStart(*[FadeIn(d) for d in m.pts[:-1]], lag_ratio=0.03),
            run_time=1.6,
        )
        # layer 3: новая точка приземляется — вход из 7.4 становится точкой
        newcomer.save_state()
        newcomer.move_to(self.split_strip.get_center())
        self.play(
            ReplacementTransform(self.split_strip, newcomer),
            run_time=1.2,
        )
        self.play(newcomer.animate.restore(), run_time=1.4,
                  rate_func=rate_functions.ease_out_cubic)
        self.play(newcomer.animate.scale(1.25), run_time=0.35)
        self.play(newcomer.animate.scale(1 / 1.25), run_time=0.35)
        self.map_7_5 = m
        self.newcomer = newcomer
        self.settle(b_spark(newcomer, ATTR),
                    b_wave(VGroup(*[d for d in m.pts[:-1]
                                    if d.get_fill_opacity() < 0.9]),
                           ATTR, 1.2, 0.06, 1.2))

    # ------------------------------------------------------------ 7.6 -----
    def f_7_6(self):
        """Одна и та же карта, два способа получить вектор."""
        self.frame("7.6")
        cap = caption("Таблица отдала бы заглушку",
                      "одна и та же проекция · слева <unk> в центре облака, "
                      "справа вектор в своей области")

        pw = (BODY_W - 90) / 2
        ph = BODY_H

        def half(dots):
            box = rect(pw, ph, DIM, S_THIN)
            pts = VGroup()
            for l, t, colour, opacity, size in dots:
                d = dot(size, colour).set_opacity(opacity)
                d.move_to(box.get_corner(UL) +
                          np.array([px(pw * l / 100 + size / 2),
                                    -px(ph * t / 100 + size / 2), 0]))
                pts.add(d)
            g = VGroup(box, pts)
            g.box, g.pts = box, pts
            return g

        # The <unk> stub is positioned with `calc(50% - 22px)` in the mock, so
        # both panels are listed explicitly rather than scraped.
        left = half([(25, 65, DIM, 1.0, 18), (70, 70, DIM, 1.0, 18),
                     (45, 28, DIM, 1.0, 18), (60, 40, DIM, 1.0, 18),
                     (50, 50, ALERT, 1.0, 45)])
        right = half([(25, 65, DIM, 1.0, 18), (70, 70, DIM, 1.0, 18),
                      (45, 28, ATTR, 0.45, 18), (60, 40, ATTR, 0.45, 18),
                      (50, 31, ATTR, 1.0, 45)])
        row = flex_row(left, right, gap=90)
        body_center(row)
        # слева заглушка стоит ровно в центре облака
        left.pts[-1].move_to(left.box.get_center())

        self.play(Transform(self.cap, cap), run_time=0.8)
        # layer 1: две одинаковые рамки
        self.play(
            ReplacementTransform(self.map_7_5.box, left.box),
            FadeOut(self.map_7_5.pts),
            run_time=1.2,
        )
        self.play(Create(right.box), run_time=0.7)
        self.play(FadeIn(left.pts[:-1]), FadeIn(right.pts[:-1]), run_time=0.8)
        # layer 2: слева точка в центре — одна и та же для всех незнакомых
        self.play(ReplacementTransform(self.newcomer, left.pts[-1]),
                  run_time=1.1)
        # layer 3: справа точка в области
        self.play(GrowFromCenter(right.pts[-1]), run_time=0.9)
        self.settle(b_spark(left.pts[-1], ALERT),
                    b_spark(right.pts[-1], ATTR),
                    b_box(left.pts[-1], ALERT), b_box(right.pts[-1], ATTR))
