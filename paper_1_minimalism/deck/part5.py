"""Часть 5 — Как устроен DHE.  Кадры 5.1–5.12.

Таблицы нет вообще: 8371102934 → 1024 независимых хеша → 1024 вещественных
числа в [−1, 1] → многослойный перцептрон → 32 числа.  Сюда же входят
Box–Muller, BatchNorm и Mish — и разбор того, почему сосед улетает.
"""

import numpy as np
from manim import (
    VGroup, Line, DashedLine, Circle, Arc, FadeIn, FadeOut, Create, Write,
    Transform, ReplacementTransform, LaggedStart, GrowFromEdge, GrowFromCenter,
    VMobject, rate_functions, ORIGIN, LEFT, RIGHT, UP, DOWN, DL, DR, UL, UR,
)

from deckkit.base import DeckScene
from deck.data import flex_bars, point_cloud
from deckkit.tokens import (
    px, pos, BG, INK, MUTED, DIM, ID, DEC, ATTR, ALERT, FONT_MONO,
    SIZE_DISPLAY, SIZE_TITLE, SIZE_MONO, S_THIN, S_MID, S_THICK,
    BODY_CX, BODY_CY, BODY_TOP, BODY_BOTTOM, BODY_H, BODY_LEFT, BODY_W,
)
from deckkit.components import (
    caption, chip, mono, sans, text, rect, ray_px, line_px, dot, at,
    flex_row, flex_col, body_center, fixed_width, para,
    b_indicate, b_wave, b_flash_along, b_flash_group, b_box, b_spark, b_focus,
)

VIDEO_ID = "8371102934"
NEIGHBOUR = "8371102935"

# 5.2 — twenty of the 1024 rays are drawn; angles and opacities from the mock
FAN_ANGLES = list(range(-23, 23, 3))
FAN_OPACITY = [.8, .6, .8, .5, .7, .55, .8, .6, .9, .6, .8, .5, .7, .55, .8, .6]

# 5.3 — the real arithmetic for our identifier and the first coefficient pair
HASH_STEPS = [("a · e", "8 224 203 914 941 449 902", MUTED),
              ("+ b", "8 224 203 914 999 335 063", MUTED),
              ("mod p", "1 306 674 887 358 253 210", MUTED)]

# 5.10 — +1 on the input shifts every hᵢ by its own aᵢ mod m
SHIFT_ROWS = [
    ("h₁", "253 210", "+ 451 653", "", "704 863", INK),
    ("h₂", "638 622", "+ 7", "", "638 629", ATTR),
    ("h₃", "430 532", "+ 483 647", "", "914 179", INK),
    ("h₄", "660 749", "+ 104 729", "", "765 478", INK),
    ("h₅", "686 621", "+ 485 867", "− 10⁶", "172 488", INK),
    ("h₆", "129 779", "+ 979 687", "− 10⁶", "109 466", INK),
]

# 5.11 — the same six hashes for both neighbours
PAIRS_934 = ["253210", "638622", "430532", "660749", "686621", "129779"]
PAIRS_935 = ["704863", "638629", "914179", "765478", "172488", "109466"]


def mish(x):
    return x * np.tanh(np.log1p(np.exp(x)))


def curve(fn, x0, x1, to_point, n=240, color=ATTR, stroke=S_MID, dashed=False):
    pts = [to_point(x, fn(x)) for x in np.linspace(x0, x1, n)]
    if dashed:
        g = VGroup()
        for i in range(0, n - 1, 8):
            j = min(i + 4, n - 1)
            g.add(Line(pts[i], pts[j], color=color, stroke_width=stroke))
        return g
    m = VMobject(color=color, stroke_width=stroke)
    m.set_points_smoothly(pts)
    return m


def bar_chart(bars, width, height, gap=3, colour_map=None):
    """`flex:1` bars filling `width`, growing from a shared floor."""
    n = len(bars)
    bw = (width - gap * (n - 1)) / n
    g = VGroup()
    for i, (pct, col, op) in enumerate(bars):
        c = colour_map(i, col) if colour_map else col
        b = rect(bw, max(height * pct / 100, 1), c, 0, fill=c, fill_opacity=op)
        g.add(b)
    g.arrange(RIGHT, buff=px(gap), aligned_edge=DOWN)
    return g


class Part5(DeckScene):
    """Конструкция DHE."""

    def construct(self):
        self.f_5_1()
        self.f_5_2()
        self.f_5_3()
        self.f_5_4()
        self.f_5_5()
        self.f_5_6()
        self.f_5_7()
        self.f_5_8()
        self.f_5_9()
        self.f_5_10()
        self.f_5_11()
        self.f_5_12()
        self.outro()

    # ------------------------------------------------------------ 5.1 -----
    def f_5_1(self):
        """Таблица возвращается на своё место и растворяется."""
        self.frame("5.1")
        cap = caption("Таблицы нет",
                      "у DHE нет ни одной строки, привязанной к значению — "
                      "только функции")
        self.play(FadeIn(cap), run_time=0.8)
        self.cap = cap

        # layer 1: таблица из части 2 возвращается на своё место
        solid = rect(540, 540, DIM, 0, fill=DIM, fill_opacity=1)
        body_center(solid)
        self.play(FadeIn(solid), run_time=1.0)

        # layer 2: заливка уходит;  layer 3: остаётся пунктирный контур
        outline = VGroup()
        for a, b in ((UL, UR), (UR, DR), (DR, DL), (DL, UL)):
            outline.add(DashedLine(solid.get_corner(a), solid.get_corner(b),
                                   color=DIM, stroke_width=S_THIN,
                                   dash_length=px(12)))
        self.play(solid.animate.set_fill(opacity=0), FadeIn(outline),
                  run_time=1.4)
        self.remove(solid)
        # layer 4: контур гаснет — пустое место остаётся в кадре
        self.play(outline.animate.set_stroke(opacity=0.35), run_time=1.0)
        self.ghost = outline
        self.settle(b_flash_group(outline, DIM, 5, 0.1, 1.4))

    # ------------------------------------------------------------ 5.2 -----
    def f_5_2(self):
        """Из идентификатора расходится веер: по лучу на хеш-функцию."""
        self.frame("5.2")
        cap = caption("Хеши вместо строки",
                      "k = 1024 независимых хеш-функции · "
                      "ни одного обучаемого параметра")

        c = chip(VIDEO_ID, ID, SIZE_MONO, pad=(18, 27), stroke=S_THIN)
        slot = rect(630, 540, BG, 0)
        slot.set_opacity(0)
        count = mono("1024", SIZE_MONO, ID)
        row = flex_row(c, slot, count, gap=45)
        body_center(row)

        ox = slot.get_left()[0] * 135 + 960
        oy = 540 - slot.get_center()[1] * 135
        rays = VGroup()
        for a, op in zip(FAN_ANGLES, FAN_OPACITY):
            r = ray_px(ox, oy, 640, a, ID, S_THIN)
            r.set_stroke(opacity=op)
            rays.add(r)

        # morph: исчезнувшая таблица → веер хешей
        self.play(
            Transform(self.cap, cap),
            ReplacementTransform(self.ghost, rays),
            run_time=1.4,
        )
        # layer 1: chip слева
        self.play(FadeIn(c, shift=RIGHT * px(30)), run_time=0.8)
        # layer 2: лучи расходятся веером
        self.play(
            LaggedStart(*[Create(r) for r in rays], lag_ratio=0.05),
            run_time=2.2,
        )
        # layer 3: столбец значений справа
        self.play(FadeIn(count), run_time=0.6)
        self.fan_rays = rays
        self.dead = VGroup(c, count)
        self.settle(b_flash_group(rays, ID, 5, 0.04, 1.8),
                    b_indicate(c, ID), b_indicate(count, ID))

    # ------------------------------------------------------------ 5.3 -----
    def f_5_3(self):
        """Вычисление разворачивается сверху вниз, каждая строка — число."""
        self.frame("5.3")
        cap = caption("Один хеш",
                      "hᵢ(e) = ((aᵢ · e + bᵢ) mod p) mod m · "
                      "a₁ = 982451653, b₁ = 57885161, p = 2⁶¹ − 1, m = 10⁶")

        rows = VGroup()
        for label, value, col in HASH_STEPS:
            r = VGroup(fixed_width(mono(label, SIZE_MONO, col), 180),
                       mono(value, SIZE_MONO, col))
            r.arrange(RIGHT, buff=px(63))
            rows.add(r)
        final = VGroup(fixed_width(mono("mod m", SIZE_MONO, ID), 180),
                       text("253 210", SIZE_DISPLAY, ID, font=FONT_MONO,
                            weight="MEDIUM"))
        final.arrange(RIGHT, buff=px(63))
        rows.add(final)
        rows.arrange(DOWN, buff=px(36), aligned_edge=LEFT)
        body_center(rows)

        self.play(Transform(self.cap, cap), FadeOut(self.dead),
                  FadeOut(self.fan_rays), run_time=0.9)
        # layers 1-4: умножение, сложение, mod p, mod m
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * px(24)), run_time=0.8)
            self.wait(0.35)
        self.result = final[1]
        self.dead = VGroup(*rows[:-1], final[0])
        self.settle(b_wave(rows, None, 1.03, 0.16, 1.5),
                    b_spark(final[1], ID))

    # ------------------------------------------------------------ 5.4 -----
    def f_5_4(self):
        """Первые 96 из 1024 компонент реального вектора."""
        self.frame("5.4")
        cap = caption("Вектор в диапазоне",
                      "vᵢ = 2 hᵢ / (m − 1) − 1 · "
                      "показаны первые 96 из 1024 компонент реального вектора")

        bars = bar_chart(flex_bars("5.4"), BODY_W, 405)
        axis = VGroup(mono("−1", SIZE_MONO, MUTED),
                      mono("96 из 1024", SIZE_MONO, MUTED),
                      mono("+1", SIZE_MONO, MUTED))
        axis[0].move_to(pos(BODY_LEFT, 0), aligned_edge=LEFT)
        axis[1].move_to(pos(BODY_CX, 0))
        axis[2].move_to(pos(BODY_LEFT + BODY_W, 0), aligned_edge=RIGHT)
        block = VGroup(bars, axis)
        block.arrange(DOWN, buff=px(27))
        body_center(block)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # morph: результат 253210 → первый столбик вектора
        self.play(ReplacementTransform(self.result, bars[0]), run_time=1.0)
        # layer 2: столбики появляются волной, 8 мс на измерение
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars[1:]],
                        lag_ratio=0.6),
            run_time=3.0,
        )
        # layers 1 and 3: ось −1…1
        self.play(FadeIn(axis), run_time=0.7)
        self.vector_bars = bars
        self.dead = VGroup(axis)
        self.settle(b_wave(VGroup(*bars[::3]), ID, 1.1, 0.012, 1.7),
                    b_wave(VGroup(*bars[1::3]), ID, 1.1, 0.012, 1.7))

    # ------------------------------------------------------------ 5.5 -----
    def f_5_5(self):
        """Хеши равномерны, а инициализация рассчитана на единичную дисперсию."""
        self.frame("5.5")
        cap = caption("Равномерный вход не годится декодеру",
                      "Var U(−1,1) = 1/3 · инициализация слоёв "
                      "рассчитана на Var = 1")

        left_w = (BODY_W - 135) / 2
        hist_w = (left_w - 45) / 2
        bars = flex_bars("5.5")
        # столбики плюс подпись σ должны уместиться между подписью кадра и
        # нижним полем: полная высота рабочей области их не вмещает
        plot_h = BODY_H - 90
        uni = bar_chart(bars[:8], hist_w, plot_h * 0.58)
        nor = bar_chart(bars[8:], hist_w, plot_h)
        uni_c = flex_col(uni, mono("σ = 0.577", SIZE_MONO, ID), gap=27)
        nor_c = flex_col(nor, mono("σ = 1", SIZE_MONO, INK), gap=27)
        hists = VGroup(uni_c, nor_c)
        hists.arrange(RIGHT, buff=px(45), aligned_edge=DOWN)
        hists.move_to(pos(BODY_LEFT, BODY_BOTTOM), aligned_edge=DL)

        sx = BODY_LEFT + left_w + 135
        head = para("σ активаций без нормировки входа", BODY_W - left_w - 135,
                    SIZE_MONO, MUTED, line_height=1.3)
        decay = VGroup()
        for name, w, val in (("слой 1", 346, "0.577"), ("слой 2", 200, "0.333"),
                             ("слой 3", 115, "0.192")):
            r = VGroup(fixed_width(mono(name, SIZE_MONO, MUTED), 63 + 63),
                       rect(w, 36, ALERT, 0, fill=ALERT, fill_opacity=0.55),
                       mono(val, SIZE_MONO, ALERT))
            r.arrange(RIGHT, buff=px(27))
            decay.add(r)
        decay.arrange(DOWN, buff=px(27), aligned_edge=LEFT)
        foot = para("каждый слой делит разброс на √3",
                    BODY_W - left_w - 135, SIZE_MONO, MUTED, line_height=1.3)
        side = VGroup(head, decay, foot)
        side.arrange(DOWN, buff=px(36), aligned_edge=LEFT)
        side.move_to(pos(sx, BODY_CY), aligned_edge=LEFT)
        sep = line_px(sx - 67, BODY_TOP, sx - 67, BODY_BOTTOM, DIM, S_THIN)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: две гистограммы — вход и то, чего от него ждут
        self.play(ReplacementTransform(self.vector_bars, uni), run_time=1.4)
        self.play(FadeIn(uni_c[1]), run_time=0.4)
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in nor], lag_ratio=0.08),
            run_time=1.2,
        )
        self.play(FadeIn(nor_c[1]), run_time=0.4)
        # layers 2-3: следствие — разброс падает на каждом слое
        self.play(Create(sep), FadeIn(head), run_time=0.8)
        self.play(
            LaggedStart(*[FadeIn(r, shift=RIGHT * px(20)) for r in decay],
                        lag_ratio=0.25),
            run_time=1.8,
        )
        self.play(FadeIn(foot), run_time=0.6)
        self.narrow_hist = uni
        self.dead = VGroup(uni_c[1], nor_c, sep, head, decay, foot)
        self.settle(b_wave(uni, ID, 1.06, 0.07, 1.2),
                    b_wave(nor, INK, 1.06, 0.07, 1.2),
                    b_wave(VGroup(*[r[1] for r in decay]), ALERT, 1.06,
                           0.16, 1.3))

    # ------------------------------------------------------------ 5.6 -----
    def f_5_6(self):
        """Из первого хеша радиус, из второго угол; пересечение — нормальная пара."""
        self.frame("5.6")
        cap = caption("Box–Muller: два равномерных числа дают два нормальных",
                      "r = √(−2 ln u₁) · θ = 2π u₂ · z₀ = r cos θ · z₁ = r sin θ")

        left = VGroup(
            mono("h₁ / m", SIZE_MONO, MUTED),
            text("u₁ = 0.2532", SIZE_TITLE, ID, font=FONT_MONO, weight="MEDIUM"),
            mono("→ r = 1.657", SIZE_MONO, MUTED),
        )
        left.arrange(DOWN, buff=px(14), aligned_edge=LEFT)
        right_in = VGroup(
            mono("h₂ / m", SIZE_MONO, MUTED),
            text("u₂ = 0.6386", SIZE_TITLE, ID, font=FONT_MONO, weight="MEDIUM"),
            mono("→ θ = 229.9°", SIZE_MONO, MUTED),
        )
        right_in.arrange(DOWN, buff=px(14), aligned_edge=LEFT)
        inputs = VGroup(left, right_in)
        inputs.arrange(DOWN, buff=px(36), aligned_edge=LEFT)
        inputs.move_to(pos(BODY_LEFT, BODY_CY), aligned_edge=LEFT)

        # the 540x540 plane, placed to the right of the input column
        px0 = BODY_LEFT + 360 + 90
        py0 = BODY_CY - 270

        def P(x, y):
            return pos(px0 + x, py0 + y)

        axes = VGroup(Line(P(0, 270), P(540, 270), color=DIM, stroke_width=S_THIN),
                      Line(P(270, 0), P(270, 540), color=DIM, stroke_width=S_THIN))
        circ = Circle(radius=px(149), color=ID, stroke_width=S_THIN)
        circ.move_to(P(270, 270)).set_stroke(opacity=0.55)
        radius = ray_px(px0 + 270, py0 + 270, 149, 130.1, ID, S_THIN)
        theta_ref = ray_px(px0 + 270, py0 + 270, 90, 0, MUTED, S_THIN)
        arc = Arc(radius=px(70), start_angle=0, angle=-np.deg2rad(130.1),
                  arc_center=P(270, 270), color=MUTED, stroke_width=S_THIN)
        zdot = dot(24, INK).move_to(P(174, 384))
        zlab = mono("z", SIZE_MONO, INK).move_to(P(186 + 8, 396 + 14))
        rlab = mono("r", SIZE_MONO, ID).move_to(P(288 + 8, 222 + 14))
        tlab = mono("θ", SIZE_MONO, MUTED).move_to(P(315 + 8, 288 + 14))

        sx = px0 + 540 + 90
        outs = VGroup()
        for name, val in (("z₀", "−1.068"), ("z₁", "−1.268")):
            b = VGroup(mono(name, SIZE_MONO, MUTED),
                       text(val, SIZE_TITLE, INK, font=FONT_MONO,
                            weight="MEDIUM"))
            b.arrange(DOWN, buff=px(14), aligned_edge=LEFT)
            outs.add(b)
        note = para("пара хешей → пара значений · 1024 → 1024 без остатка",
                    BODY_LEFT + BODY_W - sx, SIZE_MONO, MUTED)
        outs.add(note)
        outs.arrange(DOWN, buff=px(36), aligned_edge=LEFT)
        outs.move_to(pos(sx, BODY_CY), aligned_edge=LEFT)
        sep = line_px(sx - 45, BODY_TOP, sx - 45, BODY_BOTTOM, DIM, S_THIN)

        self.play(Transform(self.cap, cap), FadeOut(self.dead),
                  FadeOut(self.narrow_hist), run_time=0.9)
        # layer 1: два хеша слева
        self.play(FadeIn(inputs, shift=RIGHT * px(20)), run_time=1.0)
        self.play(Create(axes), run_time=0.7)
        # layer 2: радиус — окружность стягивается
        self.play(Create(circ), run_time=1.0)
        self.play(Create(radius), FadeIn(rlab), run_time=0.9)
        # layer 3: угол — луч поворачивается
        self.play(Create(theta_ref), Create(arc), FadeIn(tlab), run_time=1.0)
        # layer 4: точка на пересечении
        self.play(GrowFromCenter(zdot), FadeIn(zlab), run_time=0.8)
        # layer 5: второе значение z₁
        self.play(Create(sep), run_time=0.5)
        self.play(
            LaggedStart(*[FadeIn(o, shift=RIGHT * px(16)) for o in outs],
                        lag_ratio=0.25),
            run_time=2.0,
        )
        self.zdot = zdot
        self.dead = VGroup(inputs, axes, circ, radius, theta_ref, arc,
                           zlab, rlab, tlab, sep, outs)
        self.settle(b_flash_along(circ, ID, 6, 1.5),
                    b_flash_along(radius, INK, 6, 1.0),
                    b_flash_along(arc, INK, 6, 1.0),
                    b_spark(zdot, INK))

    # ------------------------------------------------------------ 5.7 -----
    def f_5_7(self):
        """Слева углы квадрата заняты, справа облако вращательно симметрично."""
        self.frame("5.7")
        cap = caption("У входа больше нет выделенных направлений",
                      "60 пар до преобразования и после · те же хеши")

        def panel(pts, colour, opacity, label, lab_col):
            box = VGroup()
            corners = [(UL, UR), (UR, DR), (DR, DL), (DL, UL)]
            frame = rect(495, 495, DIM, 0)
            for a, b in corners:
                box.add(DashedLine(frame.get_corner(a), frame.get_corner(b),
                                   color=DIM, stroke_width=S_THIN,
                                   dash_length=px(12)))
            ds = VGroup()
            for l, t in pts:
                d = dot(12, colour).set_opacity(opacity)
                d.move_to(frame.get_corner(UL) +
                          np.array([px(495 * l / 100 + 6),
                                    -px(495 * t / 100 + 6), 0]))
                ds.add(d)
            lab = mono(label, SIZE_MONO, lab_col)
            lab.move_to(frame.get_corner(DL) +
                        np.array([px(18), px(18), 0]), aligned_edge=DL)
            g = VGroup(box, ds, lab)
            g.frame, g.box, g.dots, g.label = frame, box, ds, lab
            return g

        p_uni = panel(point_cloud("5.7", "#F2994A"), ID, 0.75,
                      "равномерное", ID)
        arrow = flex_col(rect(90, 2, MUTED, 0, fill=MUTED, fill_opacity=1),
                         mono("Box–Muller", SIZE_MONO, MUTED), gap=18)
        p_nor = panel(point_cloud("5.7", "#E8EAF0"), INK, 0.85, "", INK)
        row = flex_row(p_uni, arrow, p_nor, gap=90)
        body_center(row)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: квадратное облако
        self.play(ReplacementTransform(self.zdot, p_uni.dots[0]), run_time=0.9)
        self.play(Create(p_uni.box), run_time=0.8)
        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in p_uni.dots[1:]],
                        lag_ratio=0.03),
            FadeIn(p_uni.label),
            run_time=1.8,
        )
        self.play(FadeIn(arrow), Create(p_nor.box), run_time=0.8)
        # layers 2-4: точки едут по своим траекториям, квадрат остаётся призраком
        self.play(
            *[ReplacementTransform(a.copy(), b)
              for a, b in zip(p_uni.dots, p_nor.dots)],
            run_time=2.4,
        )
        self.cloud = p_nor.dots
        self.dead = VGroup(p_uni, arrow, p_nor.box)
        self.settle(b_wave(p_uni.dots, ID, 1.25, 0.02, 1.5),
                    b_wave(p_nor.dots, INK, 1.25, 0.02, 1.5))

    # ------------------------------------------------------------ 5.8 -----
    def f_5_8(self):
        """Linear → BatchNorm → Mish, трижды."""
        self.frame("5.8")
        cap = caption("Стек декодера: Linear → BatchNorm → Mish, трижды",
                      "1024 → 1024 → 1024 → 32 · всего 2 136 096 параметров · "
                      "8.54 МБ fp32")

        def block(w, h, colour, stroke, label, lab_col, fill=None):
            b = (rect(w, h, colour, stroke) if stroke
                 else rect(w, h, colour, 0, fill=colour,
                           fill_opacity=fill if fill is not None else 1))
            return flex_col(b, mono(label, SIZE_MONO, lab_col), gap=18)

        def link(count):
            return flex_col(mono(count, SIZE_MONO, MUTED),
                            rect(63, 2, MUTED, 0, fill=MUTED, fill_opacity=1),
                            gap=18)

        parts = [
            block(63, 405, ID, 0, "1024", ID),
            link("1 049 600"),
            block(90, 405, DEC, S_MID, "Linear", DEC),
            block(45, 405, DEC, 0, "BN", MUTED, fill=0.45),
            block(36, 405, ATTR, 0, "Mish", MUTED, fill=0.7),
            link("1 049 600"),
            block(90, 405, DEC, S_MID, "Linear", DEC),
            block(45, 405, DEC, 0, "BN", MUTED, fill=0.45),
            block(36, 405, ATTR, 0, "Mish", MUTED, fill=0.7),
            link("32 800"),
            block(90, 13, DEC, S_MID, "32", DEC),
        ]
        stack = flex_row(*parts, gap=27)
        body_center(stack)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # morph: круглое облако → входной слой перцептрона
        self.play(ReplacementTransform(self.cloud, parts[0][0]), run_time=1.2)
        self.play(FadeIn(parts[0][1]), run_time=0.4)
        # layer 1: три блока Linear
        self.play(
            LaggedStart(*[Create(parts[i][0]) for i in (2, 6, 10)],
                        lag_ratio=0.25),
            run_time=1.6,
        )
        # layers 2-3: BatchNorm между ними и Mish
        self.play(
            LaggedStart(*[GrowFromEdge(parts[i][0], DOWN) for i in (3, 7)],
                        lag_ratio=0.25),
            run_time=0.9,
        )
        self.play(
            LaggedStart(*[GrowFromEdge(parts[i][0], DOWN) for i in (4, 8)],
                        lag_ratio=0.25),
            run_time=0.9,
        )
        # layers 4-5: размерности под блоками, параметры над связями
        self.play(
            LaggedStart(*[FadeIn(parts[i][1]) for i in (2, 3, 4, 6, 7, 8, 10)],
                        lag_ratio=0.1),
            run_time=1.2,
        )
        self.play(
            LaggedStart(*[FadeIn(parts[i]) for i in (1, 5, 9)],
                        lag_ratio=0.2),
            run_time=1.2,
        )
        self.out_block = parts[10]          # block and its «32» label together
        self.dead = VGroup(*[p for i, p in enumerate(parts) if i != 10])
        # активации бегут по стеку слева направо — как в прогоне
        self.settle(b_wave(VGroup(*[parts[i][0] for i in
                                    (0, 2, 3, 4, 6, 7, 8, 10)]),
                           None, 1.05, 0.13, 1.7),
                    b_flash_group(VGroup(*[parts[i][0] for i in (2, 6, 10)]),
                                  INK, 6, 0.18, 1.4))

    # ------------------------------------------------------------ 5.9 -----
    def f_5_9(self):
        """Отличие от ReLU — нет излома в нуле и нет мёртвой зоны."""
        self.frame("5.9")
        cap = caption("Mish: гладкая активация без мёртвой зоны",
                      "mish(x) = x · tanh(ln(1 + eˣ)) · "
                      "минимум −0.309 при x = −1.19")

        plot_w, plot_h = 810, BODY_H
        x0 = BODY_LEFT
        y0 = BODY_TOP
        # y = 0 sits at 90.91 % of the plot, the −0.309 dip at 97.91 %
        Y_TOP, Y_BOT = 4.01, -0.401

        def P(x, y):
            return pos(x0 + (x + 4) / 8 * plot_w,
                       y0 + (Y_TOP - y) / (Y_TOP - Y_BOT) * plot_h)

        axis_x = Line(P(-4, 0), P(4, 0), color=DIM, stroke_width=S_THIN)
        axis_y = Line(P(0, Y_BOT), P(0, Y_TOP), color=DIM, stroke_width=S_THIN)
        relu = curve(lambda x: max(x, 0.0), -4, 4, P, color=MUTED,
                     stroke=S_MID, dashed=True)
        m = curve(mish, -4, 4, P, color=ATTR, stroke=S_MID)
        low = dot(18, ATTR).move_to(P(-1.19, -0.309))
        low_lab = mono("−0.309", SIZE_MONO, ATTR)
        low_lab.move_to(low.get_center() + RIGHT * px(27), aligned_edge=LEFT)
        xm = mono("−4", SIZE_MONO, MUTED).move_to(P(-4, 0) + DOWN * px(30),
                                                  aligned_edge=LEFT)
        xp = mono("+4", SIZE_MONO, MUTED).move_to(P(4, 0) + DOWN * px(30),
                                                  aligned_edge=RIGHT)

        sx = x0 + plot_w + 135
        legend = VGroup()
        for w, col, name, dash in ((63, ATTR, "Mish", False),
                                   (63, MUTED, "ReLU", True)):
            key = (DashedLine(ORIGIN, RIGHT * px(w), color=col, stroke_width=4,
                              dash_length=px(10)) if dash
                   else rect(w, 4, col, 0, fill=col, fill_opacity=1))
            r = VGroup(key, mono(name, SIZE_MONO, col))
            r.arrange(RIGHT, buff=px(27))
            legend.add(r)
        facts = VGroup(mono("нет излома в нуле", SIZE_MONO, MUTED),
                       mono("градиент течёт при x < 0", SIZE_MONO, MUTED),
                       mono("нет мёртвых нейронов", SIZE_MONO, MUTED),
                       mono("0 параметров", SIZE_MONO, INK))
        facts.arrange(DOWN, buff=px(27), aligned_edge=LEFT)
        side = VGroup(*legend, facts)
        side.arrange(DOWN, buff=px(45), aligned_edge=LEFT)
        side.move_to(pos(sx, BODY_CY), aligned_edge=LEFT)

        self.play(Transform(self.cap, cap), FadeOut(self.dead),
                  FadeOut(self.out_block), run_time=0.9)
        # layer 1: оси
        self.play(Create(axis_x), Create(axis_y), FadeIn(xm), FadeIn(xp),
                  run_time=1.0)
        # layer 2: кривая ReLU пунктиром
        self.play(Create(relu), run_time=1.2)
        # layer 3: кривая Mish рисуется слева направо
        self.play(Create(m), run_time=2.2)
        # layer 4: провал под нулём
        self.play(GrowFromCenter(low), FadeIn(low_lab), run_time=0.9)
        # layer 5: формула и выводы
        self.play(
            LaggedStart(*[FadeIn(s, shift=RIGHT * px(16)) for s in side],
                        lag_ratio=0.2),
            run_time=1.8,
        )
        self.mish_curve = m
        self.dead = VGroup(axis_x, axis_y, relu, low, low_lab, xm, xp, side)
        self.settle(b_flash_along(m, INK, 7, 1.8, 0.25),
                    b_spark(low, ATTR), b_indicate(low_lab, ATTR))

    # ------------------------------------------------------------ 5.10 ----
    def f_5_10(self):
        """Прибавление единицы сдвигает hᵢ на aᵢ mod m."""
        self.frame("5.10")
        cap = caption("Почему +1 на входе даёт другой вектор",
                      "a·(e+1) = a·e + a · значит hᵢ сдвигается на aᵢ mod m — "
                      "у каждого измерения на свою величину")

        # что именно стоит за e и e + 1 — сквозной идентификатор и его сосед
        legend = VGroup(mono("e =", SIZE_MONO, MUTED),
                        mono(VIDEO_ID, SIZE_MONO, ID),
                        mono("· e + 1 =", SIZE_MONO, MUTED),
                        mono(NEIGHBOUR, SIZE_MONO, ID))
        legend.arrange(RIGHT, buff=px(18))

        widths = [90, 216, 216, 135, 216]
        header = ["", "e", "aᵢ mod m", "перенос", "e + 1"]
        head_cols = [MUTED, ID, MUTED, MUTED, ID]
        grid = VGroup()
        hrow = VGroup(*[fixed_width(mono(h, SIZE_MONO, c), w, align="right")
                        for h, c, w in zip(header, head_cols, widths)])
        hrow.arrange(RIGHT, buff=px(36))
        grid.add(hrow)
        for name, val, shift, carry, res, res_col in SHIFT_ROWS:
            cells = [(name, MUTED), (val, INK), (shift, ID),
                     (carry, MUTED), (res, res_col)]
            r = VGroup(*[fixed_width(mono(t, SIZE_MONO, c), w, align="right")
                         for (t, c), w in zip(cells, widths)])
            r.arrange(RIGHT, buff=px(36))
            grid.add(r)
        grid.arrange(DOWN, buff=px(22), aligned_edge=LEFT)
        block = VGroup(legend, grid)
        block.arrange(DOWN, buff=px(36), aligned_edge=LEFT)
        block.move_to(pos(BODY_LEFT, BODY_CY), aligned_edge=LEFT)

        sx = BODY_LEFT + grid.width * 135 + 90
        side_w = BODY_LEFT + BODY_W - sx
        bars = bar_chart(flex_bars("5.10"), side_w, 225)
        blab = para("|vᵢ − v′ᵢ| по первым 48 измерениям · "
                    "салатовое — то самое h₂", side_w, SIZE_MONO, MUTED,
                    line_height=1.3)
        mean = VGroup(text("0.661", SIZE_TITLE, INK, font=FONT_MONO,
                           weight="MEDIUM"),
                      para("средняя |Δvᵢ| по 1024 измерениям · "
                           "ожидание для независимых — 0.667",
                           side_w - 160, SIZE_MONO, MUTED))
        mean.arrange(RIGHT, buff=px(36), aligned_edge=UP)
        side = VGroup(bars, blab, mean)
        side.arrange(DOWN, buff=px(27), aligned_edge=LEFT)
        side.move_to(pos(sx, BODY_CY), aligned_edge=LEFT)
        sep = line_px(sx - 45, BODY_TOP, sx - 45, BODY_BOTTOM, DIM, S_THIN)

        self.play(Transform(self.cap, cap), FadeOut(self.dead),
                  FadeOut(self.mish_curve), run_time=0.9)
        # layers 1-4: столбец hᵢ, сдвиг въезжает справа, перенос, новый столбец
        self.play(FadeIn(legend, shift=RIGHT * px(20)), run_time=0.7)
        self.play(FadeIn(hrow), run_time=0.6)
        self.play(
            LaggedStart(*[FadeIn(r[:2]) for r in grid[1:]], lag_ratio=0.12),
            run_time=1.4,
        )
        self.play(
            LaggedStart(*[FadeIn(r[2], shift=LEFT * px(40))
                          for r in grid[1:]], lag_ratio=0.12),
            run_time=1.4,
        )
        self.play(
            LaggedStart(*[FadeIn(r[3]) for r in grid[1:]], lag_ratio=0.12),
            run_time=0.9,
        )
        self.play(
            LaggedStart(*[FadeIn(r[4]) for r in grid[1:]], lag_ratio=0.12),
            run_time=1.4,
        )
        # layer 5: полоска |Δv|
        self.play(Create(sep), run_time=0.5)
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars],
                        lag_ratio=0.03),
            run_time=1.8,
        )
        self.play(FadeIn(blab), FadeIn(mean), run_time=0.9)
        self.delta_bars = bars
        self.dead = VGroup(legend, grid, sep, blab, mean)
        self.settle(b_wave(VGroup(*[r[2] for r in grid[1:]]), ID, 1.08,
                           0.12, 1.4),
                    b_indicate(grid[2][4], ATTR),
                    b_wave(VGroup(*bars[::2]), None, 1.12, 0.02, 1.4))

    # ------------------------------------------------------------ 5.11 ----
    def f_5_11(self):
        """Те же 48 измерений, два соседних идентификатора."""
        self.frame("5.11")
        cap = caption("Хеши двух соседних ID — несвязанные числа",
                      "те же 48 измерений · корреляция по всем 1024 "
                      "измерениям = 0.03 · близких значений 2 из 1024")

        map_w = 450
        chart_w = BODY_W - map_w - 90
        allbars = flex_bars("5.11")
        top_bars = bar_chart(allbars[:48], chart_w, 171,
                             colour_map=lambda i, c: ATTR if i == 1 else c)
        bot_bars = bar_chart(allbars[48:], chart_w, 171,
                             colour_map=lambda i, c: ATTR if i == 1 else c)
        top_lab = VGroup(mono(VIDEO_ID, SIZE_MONO, ID),
                         mono("hᵢ ∈ 0 … 10⁶", SIZE_MONO, MUTED))
        top_lab[0].move_to(pos(BODY_LEFT, 0), aligned_edge=LEFT)
        top_lab[1].move_to(pos(BODY_LEFT + chart_w, 0), aligned_edge=RIGHT)
        bot_lab = mono(NEIGHBOUR, SIZE_MONO, DEC)

        pairs = VGroup()
        for tag, vals, tcol in (("…934", PAIRS_934, ID),
                                ("…935", PAIRS_935, DEC)):
            row = VGroup(mono(tag, SIZE_MONO, tcol),
                         *[mono(v, SIZE_MONO,
                                ATTR if k == 1 else INK)
                           for k, v in enumerate(vals)])
            row.arrange(RIGHT, buff=px(27))
            pairs.add(row)
        pairs.arrange(DOWN, buff=px(12), aligned_edge=LEFT)

        chart = VGroup(top_bars, top_lab, bot_bars, bot_lab, pairs)
        chart.arrange(DOWN, buff=px(8), aligned_edge=LEFT)
        chart.move_to(pos(BODY_LEFT, BODY_CY), aligned_edge=LEFT)

        mx = BODY_LEFT + chart_w + 90
        board = rect(map_w, map_w, DIM, S_THIN)
        board.move_to(pos(mx, BODY_CY), aligned_edge=LEFT)
        d934 = dot(36, ID).move_to(board.get_corner(UL) +
                                   np.array([px(81), -px(81), 0]))
        d935 = dot(36, DEC).move_to(board.get_corner(DR) +
                                    np.array([-px(81), px(81), 0]))
        span = Line(d934.get_center(), d935.get_center(),
                    color=MUTED, stroke_width=S_THIN)
        l934 = mono("…934", SIZE_MONO, ID).move_to(
            d934.get_center() + np.array([-px(18), px(45), 0]))
        l935 = mono("…935", SIZE_MONO, DEC).move_to(
            d935.get_center() + np.array([px(18), px(45), 0]))
        mlab = mono("эмбеддинги", SIZE_MONO, MUTED).move_to(
            board.get_corner(DL) + np.array([px(18), px(18), 0]),
            aligned_edge=DL)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: верхний столбец хешей
        self.play(ReplacementTransform(self.delta_bars, top_bars), run_time=1.2)
        self.play(FadeIn(top_lab), run_time=0.5)
        # layer 2: нижний столбец появляется поверх
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bot_bars],
                        lag_ratio=0.03),
            run_time=1.6,
        )
        self.play(FadeIn(bot_lab), run_time=0.4)
        # layer 3: шесть числовых пар
        self.play(
            LaggedStart(*[FadeIn(r) for r in pairs], lag_ratio=0.25),
            run_time=1.2,
        )
        # layers 4-5: корреляция и две точки на карте
        self.play(Create(board), FadeIn(mlab), run_time=0.8)
        self.play(GrowFromCenter(d934), FadeIn(l934), run_time=0.6)
        self.play(GrowFromCenter(d935), FadeIn(l935), Create(span),
                  run_time=0.9)
        self.map_board = VGroup(board, d934, d935, span, l934, l935, mlab)
        self.dead = VGroup(chart)
        self.settle(b_wave(VGroup(*top_bars[::2]), ID, 1.12, 0.02, 1.3),
                    b_wave(VGroup(*bot_bars[::2]), DEC, 1.12, 0.02, 1.3),
                    b_indicate(top_bars[1], ATTR), b_indicate(bot_bars[1], ATTR),
                    b_flash_along(span, INK, 6, 1.1))

    # ------------------------------------------------------------ 5.12 ----
    def f_5_12(self):
        """Десяток идентификаторов упирается в один и тот же блок параметров."""
        self.frame("5.12")
        cap = caption("Ни один параметр не принадлежит идентификатору",
                      "10⁸ значений делят один декодер · "
                      "2 136 096 параметров против 12.8 ГБ таблицы")

        chips = VGroup(*[rect(180, 27, ID, S_THIN) for _ in range(7)])
        chips.arrange(DOWN, buff=px(18))
        slot = rect(270, 315, BG, 0)
        slot.set_opacity(0)
        core = rect(270, 270, DEC, 0, fill=DEC, fill_opacity=1)
        numbers = flex_col(mono("2 136 096", SIZE_MONO, DEC),
                           mono("12.8 ГБ", SIZE_MONO, MUTED), gap=36)
        row = flex_row(chips, slot, core, numbers, gap=90)
        body_center(row)

        ox = slot.get_left()[0] * 135 + 960
        oy = 540 - slot.get_top()[1] * 135
        rays = VGroup()
        for top, w, a in ((14, 290, 29), (59, 280, 20), (104, 273, 10),
                          (149, 270, 0), (194, 273, -10), (239, 280, -20),
                          (284, 290, -29)):
            rays.add(ray_px(ox, oy + top, w, a, MUTED, S_THIN))

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # morph: карта из 5.11 → общий блок параметров
        self.play(ReplacementTransform(self.map_board, core), run_time=1.3)
        # layer 1: много chip слева
        self.play(
            LaggedStart(*[FadeIn(c, shift=RIGHT * px(30)) for c in chips],
                        lag_ratio=0.1),
            run_time=1.6,
        )
        # layer 2: стрелки сходятся к одному блоку
        self.play(
            LaggedStart(*[Create(r) for r in rays], lag_ratio=0.08),
            run_time=1.6,
        )
        # layer 3: два числа
        self.play(FadeIn(numbers, shift=LEFT * px(20)), run_time=0.9)
        self.shared_core = core
        self.settle(b_flash_group(rays, MUTED, 6, 0.07, 1.5),
                    b_box(core, DEC), b_indicate(numbers[0], DEC))
