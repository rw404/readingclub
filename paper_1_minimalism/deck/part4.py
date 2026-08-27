"""Часть 4 — Критерии кодирования.  Кадры 4.1–4.11.

Каждое требование вводится провалом, а не определением: сначала метод,
который его нарушает, потом глиф самого критерия.  Финал раздела — матрица
«метод × критерий», главный кадр всей презентации.
"""

import numpy as np
from manim import (
    VGroup, Line, FadeIn, FadeOut, Create, Write, Transform,
    ReplacementTransform, LaggedStart, GrowFromEdge, GrowFromCenter,
    rate_functions, ORIGIN, LEFT, RIGHT, UP, DOWN, DL, DR, UL, UR,
)

from deckkit.base import DeckScene
from deckkit.tokens import (
    px, pos, BG, INK, MUTED, DIM, ID, DEC, ATTR, ALERT,
    SIZE_DISPLAY, SIZE_TITLE, SIZE_MONO, S_THIN, S_MID, S_THICK,
    BODY_CX, BODY_CY, BODY_TOP, BODY_BOTTOM, BODY_H, BODY_LEFT, BODY_W,
    FONT_MONO,
)
from deckkit.components import (
    caption, chip, mono, sans, text, rect, ray_px, line_px, dot, at,
    flex_row, flex_col, body_center, fixed_width, para,
    b_indicate, b_wave, b_flash_along, b_flash_group, b_box, b_spark, b_focus,
)
from deck.matrix import (
    criteria_matrix, glyph_unique, glyph_equal, glyph_highdim, glyph_entropy,
)

# 4.3 — 7 = 0111, 8 = 1000, 9 = 1001.  Filled cell = bit that differs.
BITS = {"7": [0, 1, 1, 1], "8": [1, 0, 0, 0], "9": [1, 0, 0, 1]}
# positions of 7, 8, 9 on the number line of 4.3 (CSS `left`, px)
LINE_POS = [(90, MUTED), (855, ALERT), (915, ALERT)]

# 4.5 — the same six points, crowded on a line and spread on a plane
LINE_PTS = [100, 124, 148, 196, 214, 262]
PLANE_PTS = [(54, 63), (225, 36), (117, 171), (288, 144), (63, 288), (252, 297)]

# 4.8 — the dense strip, opacities transcribed from the storyboard
DENSE = [.8, .4, .9, .6, .3, .75, .5, .85, .45, .7, .35, .9, .55, .8, .4,
         .65, .95, .3, .7, .5, .85, .6, .4, .75, .55, .45, .85, .6, .3, .8,
         .5, .9, .4, .7, .55, .95, .35, .65, .8, .45, .75, .3, .9, .5, .7,
         .4, .85, .6, .35, .8]

# 4.11 — H(vᵢ), bits per dimension, on a log scale (% of the plot height)
ENTROPY_BARS = [("one-hot", 12.6, "2.8·10⁻⁷", ALERT, 0.55),
                ("hashing", 33.3, "2.1·10⁻⁵", ALERT, 0.55),
                ("bloom", 39.4, "7.8·10⁻⁵", MUTED, 1.0),
                ("QR · r", 63.3, "0.011", MUTED, 1.0),
                ("binary", 84.6, "1", MUTED, 1.0),
                ("DHE", 98.9, "19.93", ID, 1.0)]

STRIP_COLS, STRIP_W, STRIP_GAP = 25, 1170, 8
STRIP_CW = (STRIP_W - STRIP_GAP * (STRIP_COLS - 1)) / STRIP_COLS


def strip(fills):
    """The 25-wide strip of 4.7 / 4.8; `fills` is (colour, opacity) or None."""
    g = VGroup()
    for i, f in enumerate(fills):
        r, c = divmod(i, STRIP_COLS)
        if f is None:
            cell = rect(STRIP_CW, 45, DIM, S_THIN)
        else:
            col, op = f
            cell = rect(STRIP_CW, 45, col, 0, fill=col, fill_opacity=op)
        cell.move_to(pos(BODY_CX - STRIP_W / 2 + c * (STRIP_CW + STRIP_GAP),
                         r * (45 + STRIP_GAP)), aligned_edge=UL)
        g.add(cell)
    g.move_to(pos(BODY_CX, BODY_CY))
    return g


class Part4(DeckScene):
    """Четыре критерия и матрица."""

    def construct(self):
        self.f_4_1()
        self.f_4_2()
        self.f_4_3()
        self.f_4_4()
        self.f_4_5()
        self.f_4_6()
        self.f_4_7()
        self.f_4_8()
        self.f_4_9()
        self.f_4_10()
        self.f_4_11()
        self.outro()

    # ------------------------------------------------------------ 4.1 -----
    def f_4_1(self):
        """Два разных входа, один выход."""
        self.frame("4.1")
        cap = caption("Хеш теряет различимость",
                      "E не инъекция: e ≠ e′, но E(e) = E(e′) — "
                      "модель физически не может их различить")
        self.play(FadeIn(cap), run_time=0.8)
        self.cap = cap

        a, b = dot(45, ID), dot(45, ID)
        ins = flex_col(a, b, gap=180)
        slot = rect(360, 225, BG, 0)
        slot.set_opacity(0)
        out = dot(45, ID)
        row = flex_row(ins, slot, out, gap=90)
        body_center(row)

        ox = slot.get_left()[0] * 135 + 960
        oy_t = 540 - slot.get_top()[1] * 135
        oy_b = 540 - slot.get_bottom()[1] * 135
        arrows = VGroup(ray_px(ox, oy_t, 378, 18, MUTED, S_THIN),
                        ray_px(ox, oy_b, 378, -18, MUTED, S_THIN))

        # layer 1: две точки слева
        self.play(GrowFromCenter(a), GrowFromCenter(b), run_time=0.9)
        # layer 2: стрелки сходятся
        self.play(Create(arrows[0]), Create(arrows[1]), run_time=1.2)
        # layer 3: одна точка справа краснеет
        self.play(GrowFromCenter(out), run_time=0.6)
        self.play(out.animate.set_color(ALERT), run_time=0.8)

        self.merged = out
        self.dead = VGroup(a, b, arrows)
        self.settle(b_flash_group(arrows, MUTED, 6, 0.0, 1.1),
                    b_spark(out, ALERT), b_wave(VGroup(a, b), ID, 1.2, 0.1, 1.0))

    # ------------------------------------------------------------ 4.2 -----
    def f_4_2(self):
        """Глиф критерия: две точки, которые не сливаются."""
        self.frame("4.2")
        cap = caption("uniqueness",
                      "e ≠ e′ ⟹ E(e) ≠ E(e′) · у каждого значения свой вектор")

        left_d, right_d = dot(90, ATTR), dot(90, ATTR)
        bar = rect(135, 2, DIM, 0, fill=DIM, fill_opacity=1)
        g = flex_row(left_d, bar, right_d, gap=90)
        body_center(g)

        # morph: слияние двух точек → глиф uniqueness
        self.play(
            Transform(self.cap, cap),
            FadeOut(self.dead),
            ReplacementTransform(self.merged, left_d),
            run_time=1.2,
        )
        self.play(FadeIn(bar), GrowFromCenter(right_d), run_time=1.0)
        self.uniqueness = VGroup(left_d, bar, right_d)
        self.settle(b_wave(VGroup(left_d, right_d), ATTR, 1.14, 0.2, 1.2),
                    b_flash_along(bar, INK, 6, 1.0))

    # ------------------------------------------------------------ 4.3 -----
    def f_4_3(self):
        """Совпавшие биты гаснут; близость взялась из кодировки."""
        self.frame("4.3")
        cap = caption("Двоичный код придумывает близость",
                      "8 = 1000, 9 = 1001 — различие в одном бите · "
                      "7 = 0111 против 8 = 1000 — во всех четырёх")

        groups = VGroup()
        for name in ("7", "8", "9"):
            cells = VGroup(*[
                rect(36, 36, ALERT if b else DIM, 0,
                     fill=ALERT if b else DIM, fill_opacity=1)
                for b in BITS[name]])
            cells.arrange(RIGHT, buff=px(4))
            col = flex_col(cells, mono(name, SIZE_MONO, MUTED), gap=27)
            col.cells = cells
            groups.add(col)
        groups.arrange(RIGHT, buff=px(90))

        axis = rect(1080, 2, DIM, 0, fill=DIM, fill_opacity=1)
        marks = VGroup()
        for left, col in LINE_POS:
            d = dot(27, col)
            marks.add(d)
        block = flex_col(groups, VGroup(axis), gap=90)
        body_center(block)
        for (left, col), d in zip(LINE_POS, marks):
            d.move_to(axis.get_left() + RIGHT * px(left + 13.5))

        self.play(Transform(self.cap, cap), FadeOut(self.uniqueness),
                  run_time=0.9)
        # layer 1: три битовых кода
        self.play(
            LaggedStart(*[FadeIn(g, shift=UP * px(20)) for g in groups],
                        lag_ratio=0.2),
            run_time=1.6,
        )
        # layer 2: совпавшие биты гаснут
        self.play(
            *[c.animate.set_fill(DIM).set_stroke(DIM, 0)
              for g, name in zip(groups, ("7", "8", "9"))
              for c, b in zip(g.cells, BITS[name]) if not b],
            run_time=1.2,
        )
        # layer 3: те же три значения как точки на прямой
        self.play(Create(axis), run_time=0.9)
        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in marks], lag_ratio=0.2),
            run_time=1.4,
        )
        self.play(marks[1].animate.set_color(ALERT),
                  marks[2].animate.set_color(ALERT), run_time=0.6)
        self.three_pts = marks
        self.dead = VGroup(groups, axis)
        self.settle(b_wave(VGroup(marks[1], marks[2]), ALERT, 1.3, 0.12, 1.0),
                    b_indicate(marks[0], MUTED),
                    b_wave(VGroup(*[c for g, n in zip(groups, ('7', '8', '9'))
                                    for c, bit in zip(g.cells, BITS[n]) if bit]),
                           ALERT, 1.12, 0.06, 1.3))

    # ------------------------------------------------------------ 4.4 -----
    def f_4_4(self):
        """Глиф критерия: три точки на равных расстояниях."""
        self.frame("4.4")
        cap = caption("equal similarity",
                      "‖E(e) − E(e′)‖ одинаково для всех пар · "
                      "кодировка не решает, что на что похоже")

        tri = glyph_equal(360, 312, DIM)
        corners = VGroup(dot(45, ATTR).move_to(tri[0].get_start()),
                         dot(45, ATTR).move_to(tri[0].get_end()),
                         dot(45, ATTR).move_to(tri[1].get_end()))

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # morph: три точки на прямой → три точки треугольника
        self.play(
            *[ReplacementTransform(a, b)
              for a, b in zip(self.three_pts, corners)],
            run_time=1.4,
        )
        # layer 2: три равных отрезка между ними
        self.play(
            LaggedStart(*[Create(l) for l in tri], lag_ratio=0.2),
            run_time=1.6,
        )
        self.equal_glyph = VGroup(tri, corners)
        self.settle(b_flash_group(tri, INK, 6, 0.1, 1.4),
                    b_wave(corners, ATTR, 1.14, 0.14, 1.2))

    # ------------------------------------------------------------ 4.5 -----
    def f_4_5(self):
        """На прямой точки налезают друг на друга, на плоскости расходятся."""
        self.frame("4.5")
        cap = caption("Мало измерений — точки слипаются",
                      "при малом k разным значениям не хватает места, "
                      "чтобы разойтись")

        axis = rect(405, 2, DIM, 0, fill=DIM, fill_opacity=1)
        crowded = VGroup(*[dot(36, ALERT).set_opacity(0.7)
                           for _ in LINE_PTS])
        plane = VGroup(
            line_px(0, 0, 0, 405, DIM, S_THIN),      # border-left
            line_px(0, 405, 405, 405, DIM, S_THIN),  # border-bottom
        )
        spread = VGroup(*[dot(36, ATTR) for _ in PLANE_PTS])

        # place the points on their own panel first: flex_row lays panels out
        # by bounding box, so unplaced dots piled at the origin would drag the
        # two panels off a shared centre line
        for d, left in zip(crowded, LINE_PTS):
            d.move_to(axis.get_left() + RIGHT * px(left + 18))
        origin = plane.get_corner(UL)
        for d, (x, y) in zip(spread, PLANE_PTS):
            d.move_to(origin + np.array([px(x + 18), -px(y + 18), 0]))

        left_panel = VGroup(axis, crowded)
        right_panel = VGroup(plane, spread)
        row = flex_row(left_panel, right_panel, gap=180)
        body_center(row)

        self.play(Transform(self.cap, cap), FadeOut(self.equal_glyph),
                  run_time=0.9)
        # layer 1: прямая с налезающими точками
        self.play(Create(axis), run_time=0.7)
        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in crowded], lag_ratio=0.1),
            run_time=1.6,
        )
        # layer 2: плоскость
        self.play(Create(plane), run_time=1.0)
        # layer 3: те же точки расходятся
        self.play(
            *[ReplacementTransform(a.copy(), b)
              for a, b in zip(crowded, spread)],
            run_time=1.8,
        )
        self.plane_pts = VGroup(plane, spread)
        self.dead = VGroup(axis, crowded)
        self.settle(b_wave(crowded, ALERT, 1.25, 0.05, 1.2),
                    b_wave(spread, ATTR, 1.2, 0.06, 1.4))

    # ------------------------------------------------------------ 4.6 -----
    def f_4_6(self):
        """Глиф критерия: стопка осей."""
        self.frame("4.6")
        cap = caption("high dimensionality",
                      "k достаточно велико, чтобы декодер мог разделять значения")

        axes = glyph_highdim(6, 405, 27, ATTR, stroke=4)
        body_center(axes)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # morph: плоскость с точками → стопка осей
        self.play(ReplacementTransform(self.plane_pts, axes), run_time=1.6)
        self.dim_glyph = axes
        self.settle(b_wave(axes, ATTR, 1.05, 0.09, 1.4),
                    b_flash_group(axes, INK, 6, 0.09, 1.5))

    # ------------------------------------------------------------ 4.7 -----
    def f_4_7(self):
        """Полоса из ста ячеек, заполнена одна."""
        self.frame("4.7")
        cap = caption("Пустое пространство ничего не несёт",
                      "у одного измерения one-hot вероятность единицы 10⁻⁸ · "
                      "H = 2.8 × 10⁻⁷ бит")

        fills = [None] * 50
        fills[7] = (ALERT, 1.0)
        s = strip(fills)

        self.play(Transform(self.cap, cap), FadeOut(self.dim_glyph),
                  run_time=0.9)
        # layer 1: длинная полоса ячеек
        self.play(
            LaggedStart(*[Create(c) for i, c in enumerate(s) if i != 7],
                        lag_ratio=0.012),
            run_time=2.4,
        )
        # layer 2: одна ячейка заполняется;  layer 3: остальные пусты
        self.play(GrowFromCenter(s[7]), run_time=0.8)
        self.sparse_strip = s
        self.settle(b_spark(s[7], ALERT),
                    b_wave(VGroup(*s[::6]), MUTED, 1.1, 0.03, 1.5))

    # ------------------------------------------------------------ 4.8 -----
    def f_4_8(self):
        """Та же полоса, но заполненная — из пустого в плотное."""
        self.frame("4.8")
        cap = caption("high entropy",
                      "у DHE одно измерение принимает 10⁶ значений · "
                      "H = 19.93 бит вместо 2.8 × 10⁻⁷")

        dense = strip([(ATTR, o) for o in DENSE])

        self.play(Transform(self.cap, cap), run_time=0.8)
        # morph: почти пустая полоса → плотная полоса
        self.play(
            *[ReplacementTransform(a, b)
              for a, b in zip(self.sparse_strip, dense)],
            run_time=1.8,
        )
        self.entropy_glyph = dense
        self.settle(b_wave(VGroup(*dense[::2]), ATTR, 1.1, 0.02, 1.5),
                    b_wave(VGroup(*dense[1::2]), ATTR, 1.1, 0.02, 1.5))

    # ------------------------------------------------------------ 4.9 -----
    def f_4_9(self):
        """Главный кадр презентации.  Ячейки заполняются по столбцам."""
        self.frame("4.9")
        cap = caption("Метод × критерий",
                      "ни один известный метод не проходит все четыре · "
                      "последняя строка пока пуста")

        m = criteria_matrix()
        self.play(Transform(self.cap, cap), FadeOut(self.entropy_glyph),
                  run_time=0.9)

        # layer 1: глифы столбцов — те же глифы из 4.2 / 4.4 / 4.6 / 4.8
        self.play(
            LaggedStart(*[FadeIn(m.col_headers[n], shift=DOWN * px(18))
                          for n, _ in [(c[0], None) for c in
                                       [("unique",), ("equal",),
                                        ("high dim",), ("entropy",)]]],
                        lag_ratio=0.18),
            run_time=1.8,
        )
        # layer 2: глифы строк — глифы методов из части 3
        self.play(
            LaggedStart(*[FadeIn(m.row_labels[n], shift=RIGHT * px(18))
                          for n in ("one-hot", "binary", "hashing",
                                    "QR", "bloom")],
                        lag_ratio=0.15),
            Create(m.rules),
            run_time=2.0,
        )
        # layer 3: ячейки по столбцам, по одному критерию за раз —
        # чтобы читалось «ни у кого нет полного набора»
        for col in ("unique", "equal", "high dim", "entropy"):
            self.play(
                LaggedStart(*[FadeIn(m.cells[(r, col)], scale=0.6)
                              for r in ("one-hot", "binary", "hashing",
                                        "QR", "bloom")],
                            lag_ratio=0.15),
                run_time=1.5,
            )
        # layer 4: последняя строка остаётся пустой
        self.matrix = m
        self.settle(*[b_wave(VGroup(*[m.cells[(r, c)] for r in
                                      ('one-hot', 'binary', 'hashing',
                                       'QR', 'bloom')]),
                             None, 1.22, 0.1, 1.3)
                      for c in ('unique', 'equal', 'high dim', 'entropy')],
                    b_flash_along(m.rules[-1], ID, 6, 1.2))

    # ------------------------------------------------------------ 4.10 ----
    def f_4_10(self):
        """Разбор провалов по столбцу equal similarity."""
        self.frame("4.10")
        cap = caption("Почему три метода навязывают похожесть",
                      "общая часть входа → общая часть эмбеддинга · "
                      "чем больше общего, тем сильнее навязанная близость")

        pw = (BODY_W - 2 * 90) / 3          # three flex:1 panels, gap 90

        # --- binary: совпавшие биты
        b_rows = VGroup()
        for name, diff_fill in (("8", False), ("9", True)):
            cells = VGroup(*[rect(45, 45, MUTED, 0, fill=MUTED,
                                  fill_opacity=1) for _ in range(3)])
            last = (rect(45, 45, ALERT, 0, fill=ALERT, fill_opacity=1)
                    if diff_fill else rect(45, 45, ALERT, S_THIN))
            cells.add(last)
            cells.arrange(RIGHT, buff=px(6))
            r = VGroup(mono(name, SIZE_MONO, MUTED), cells)
            r.arrange(RIGHT, buff=px(27))
            b_rows.add(r)
        b_rows.arrange(DOWN, buff=px(12), aligned_edge=LEFT)
        b_bar = VGroup(rect(159, 8, MUTED, 0, fill=MUTED, fill_opacity=1),
                       rect(45, 8, ALERT, 0, fill=ALERT, fill_opacity=1))
        b_bar.arrange(RIGHT, buff=px(18))
        p1 = VGroup(mono("binary · совпавшие биты", SIZE_MONO, ALERT),
                    b_rows, b_bar,
                    mono("общего 3 бита из 4", SIZE_MONO, MUTED),
                    mono("расстояния 1, 2, 3 вместо одного", SIZE_MONO, MUTED))
        p1.arrange(DOWN, buff=px(24), aligned_edge=LEFT)

        # --- QR: общая строка частного
        # the shared quotient stays muted, the remainder is the part that
        # differs — one monospaced run so the digits keep their pitch
        q_nums = VGroup()
        for tail in ("934", "001"):
            q_nums.add(text("8371102" + tail, SIZE_MONO, MUTED,
                            font=FONT_MONO, t2c={"[7:10]": INK}))
        q_nums.arrange(DOWN, buff=px(12), aligned_edge=LEFT)
        q_bars = VGroup()
        for w, col, op, lab, lc in ((204, ALERT, .6, "q", ALERT),
                                    (204, DEC, .5, "r", MUTED)):
            r = VGroup(rect(w, 45, col, 0, fill=col, fill_opacity=op),
                       mono(lab, SIZE_MONO, lc))
            r.arrange(RIGHT, buff=px(18))
            q_bars.add(r)
        q_bars.arrange(DOWN, buff=px(12), aligned_edge=LEFT)
        p2 = VGroup(mono("QR · общая строка частного", SIZE_MONO, ALERT),
                    q_nums, q_bars,
                    mono("одно из двух слагаемых", SIZE_MONO, MUTED),
                    mono("одинаково — половина суммы", SIZE_MONO, MUTED))
        p2.arrange(DOWN, buff=px(24), aligned_edge=LEFT)

        # --- bloom: совпавший хеш
        def bcol(spec):
            g = VGroup()
            for s in spec:
                if s == "o":
                    g.add(rect(45, 27, DIM, S_THIN))
                elif s == "i":
                    g.add(rect(45, 27, ID, 0, fill=ID, fill_opacity=1))
                else:
                    g.add(rect(45, 27, ALERT, 0, fill=ALERT, fill_opacity=1))
            g.arrange(DOWN, buff=px(6))
            return g
        bl = VGroup(bcol("oiaoii"), bcol("ioaiio"))
        bl.arrange(RIGHT, buff=px(27))
        bl_bar = VGroup(rect(51, 8, ALERT, 0, fill=ALERT, fill_opacity=1),
                        rect(153, 8, MUTED, 0, fill=MUTED, fill_opacity=1))
        bl_bar.arrange(RIGHT, buff=px(18))
        p3 = VGroup(mono("bloom · совпавший хеш", SIZE_MONO, ALERT),
                    bl, bl_bar,
                    mono("один хеш из четырёх общий", SIZE_MONO, MUTED),
                    mono("четверть суммы одинакова", SIZE_MONO, MUTED))
        p3.arrange(DOWN, buff=px(24), aligned_edge=LEFT)

        panels = VGroup(p1, p2, p3)
        for k, p in enumerate(panels):
            p.move_to(pos(BODY_LEFT + k * (pw + 90), BODY_CY), aligned_edge=LEFT)
        seps = VGroup(*[
            line_px(BODY_LEFT + k * (pw + 90) - 45, BODY_TOP,
                    BODY_LEFT + k * (pw + 90) - 45, BODY_BOTTOM, DIM, S_THIN)
            for k in (1, 2)])

        # morph: пустая последняя строка матрицы → разбор провалов
        self.play(
            Transform(self.cap, cap),
            self.matrix.animate.set_opacity(0).scale(0.9),
            run_time=1.2,
        )
        self.remove(self.matrix)
        # layer 1: три панели
        self.play(
            LaggedStart(FadeIn(p1), FadeIn(p2), FadeIn(p3), lag_ratio=0.2),
            Create(seps),
            run_time=2.4,
        )
        # layers 2-4: общая часть подсвечивается, доля общего подписана
        self.play(
            b_bar[0].animate.set_fill(MUTED, 1),
            q_bars[0][0].animate.set_fill(ALERT, 0.6),
            bl_bar[0].animate.set_fill(ALERT, 1),
            run_time=1.2,
        )
        self.dead = VGroup(panels, seps)
        self.settle(b_indicate(b_bar[0], MUTED), b_indicate(q_bars[0][0], ALERT),
                    b_indicate(bl_bar[0], ALERT),
                    b_wave(VGroup(p1[0], p2[0], p3[0]), ALERT, 1.06, 0.18, 1.4))

    # ------------------------------------------------------------ 4.11 ----
    def f_4_11(self):
        """Разбор провалов по столбцам high entropy и high dimensionality."""
        self.frame("4.11")
        cap = caption("Почему у разреженных кодировок пустые измерения",
                      "H(vᵢ) — сколько бит несёт одно измерение · "
                      "логарифмическая шкала · для различения 10⁸ значений "
                      "нужно 26.58 бит")

        plot_w = (BODY_W - 90) * 1.6 / 2.6
        side_w = (BODY_W - 90) * 1.0 / 2.6
        plot_h = BODY_H - 126                # room for labels and a wrapped caption
        slot = (plot_w - 5 * 36) / 6

        bars, blabels, bvalues = VGroup(), VGroup(), VGroup()
        for k, (name, pct, val, col, op) in enumerate(ENTROPY_BARS):
            x = BODY_LEFT + k * (slot + 36)
            h = plot_h * pct / 100
            bar = rect(slot, h, col, 0, fill=col, fill_opacity=op)
            bar.move_to(pos(x, BODY_BOTTOM - 45), aligned_edge=DL)
            bars.add(bar)
            lab = mono(name, SIZE_MONO, col if name == "DHE" else MUTED)
            lab.move_to(pos(x + slot / 2, BODY_BOTTOM - 31))
            blabels.add(lab)
            v = mono(val, SIZE_MONO, col if name == "DHE" else MUTED)
            v.move_to(bar.get_top() + UP * px(18))
            bvalues.add(v)

        sx = BODY_LEFT + plot_w + 90
        head = para("сколько измерений нужно, чтобы набрать 26.58 бит",
                    side_w, SIZE_MONO, MUTED)
        need_rows = VGroup()
        for name, w, note, col, op in (("one-hot", 270, "10⁸", ALERT, .55),
                                       ("binary", 48, "27 — мало декодеру",
                                        MUTED, 1.0),
                                       ("DHE", 10, "2 · взято 1024", ID, 1.0)):
            r = VGroup(fixed_width(mono(name, SIZE_MONO,
                                        ID if name == "DHE" else MUTED), 135),
                       rect(w, 36, col, 0, fill=col, fill_opacity=op),
                       mono(note, SIZE_MONO, col))
            r.arrange(RIGHT, buff=px(27))
            need_rows.add(r)
        need_rows.arrange(DOWN, buff=px(27), aligned_edge=LEFT)
        foot = para("разреженность и размерность — "
                    "одно и то же ограничение с двух сторон",
                    side_w, SIZE_MONO, MUTED)
        side = VGroup(head, need_rows, foot)
        side.arrange(DOWN, buff=px(36), aligned_edge=LEFT)
        side.move_to(pos(sx, BODY_CY), aligned_edge=LEFT)
        sep = line_px(sx - 45, BODY_TOP, sx - 45, BODY_BOTTOM, DIM, S_THIN)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: логарифмическая ось
        axis = line_px(BODY_LEFT, BODY_BOTTOM - 45,
                       BODY_LEFT + plot_w, BODY_BOTTOM - 45, DIM, S_THIN)
        self.play(Create(axis), run_time=0.7)
        # layer 2: столбики энтропии по одному
        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.2),
            LaggedStart(*[FadeIn(l) for l in blabels], lag_ratio=0.2),
            run_time=2.6,
        )
        self.play(
            LaggedStart(*[FadeIn(v) for v in bvalues], lag_ratio=0.15),
            run_time=1.6,
        )
        # layers 3-4: риска нужных 26.58 бит и сравнение размерностей
        self.play(Create(sep), FadeIn(head), run_time=0.9)
        self.play(
            LaggedStart(*[FadeIn(r, shift=RIGHT * px(20)) for r in need_rows],
                        lag_ratio=0.2),
            run_time=1.8,
        )
        self.play(FadeIn(foot), run_time=0.7)
        self.settle(b_wave(bars, None, 1.05, 0.09, 1.6),
                    b_indicate(bars[-1], ID), b_indicate(bvalues[-1], ID),
                    b_wave(VGroup(*[r[1] for r in need_rows]), None,
                           1.06, 0.14, 1.2))
