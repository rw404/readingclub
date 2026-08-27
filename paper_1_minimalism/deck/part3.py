"""Часть 3 — Способы кодирования.  Кадры 3.1–3.6.

Один и тот же макет, в который по очереди подставляются четыре метода.
Повторение рамки — это и есть дизайн; меняется только начинка E и D.
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
    BODY_CX, BODY_CY, BODY_H,
)
from deckkit.components import (
    caption, chip, mono, sans, text, rect, ray_px, line_px, at,
    flex_row, flex_col, body_center,
    b_indicate, b_wave, b_flash_along, b_flash_group, b_box, b_spark,
)


# --------------------------------------------------------------- helpers ----

def connector(w=45):
    """The 45x2 muted link between two slots of the frame."""
    return rect(w, 2, MUTED, 0, fill=MUTED, fill_opacity=1)


def code_column(marks, w=45, h=36, gap=4, color=ID):
    """The E slot: a column of cells, `marks` says which are filled."""
    g = VGroup()
    for m in marks:
        if m:
            g.add(rect(w, h, color, 0, fill=color, fill_opacity=1))
        else:
            g.add(rect(w, h, DIM, S_THIN))
    g.arrange(DOWN, buff=px(gap))
    g.marks = marks
    return g


def d_matrix(w, h, bands=(), band_h=36, stroke=S_MID, color=DEC):
    """The D slot: an outlined table with rows lit up inside it.

    `bands` are CSS `top` offsets of the highlighted rows, measured from the
    inside of the border, exactly as the storyboard positions them.
    """
    box = rect(w, h, color, stroke)
    g = VGroup(box)
    rows = VGroup()
    for top in bands:
        r = rect(w, band_h, color, 0, fill=color, fill_opacity=1)
        r.move_to(box.get_corner(UL) + np.array([0, -px(top), 0]),
                  aligned_edge=UL)
        rows.add(r)
    g.add(rows)
    g.box, g.rows = box, rows
    return g


def out_vector(width=360, n=8, h=36, color=DEC):
    """The z slot: the d = 32 embedding, drawn as eight cells."""
    cw = (width - 4 * (n - 1)) / n
    g = VGroup(*[rect(cw, h, color, 0, fill=color, fill_opacity=1)
                 for _ in range(n)])
    g.arrange(RIGHT, buff=px(4))
    return g


def labelled(mob, txt, color, gap=27):
    return flex_col(mob, mono(txt, SIZE_MONO, color), gap=gap)


def mini_schema(e_slot, d_slot, name):
    """One panel of the 2x2 grid on 3.6 — the same frame, a different filling."""
    row = VGroup(e_slot, connector(27), d_slot, connector(27),
                 rect(90, 18, DEC, 0, fill=DEC, fill_opacity=1),
                 mono(name, SIZE_MONO, MUTED))
    row.arrange(RIGHT, buff=px(27))
    row.e_slot, row.d_slot = e_slot, d_slot
    return row


class Part3(DeckScene):
    """Способы кодирования."""

    def construct(self):
        self.f_3_1()
        self.f_3_2()
        self.f_3_3()
        self.f_3_4()
        self.f_3_5()
        self.f_3_6()
        self.outro()

    # ------------------------------------------------------------ 3.1 -----
    def f_3_1(self):
        """Рамка, в которую дальше подставляются четыре метода."""
        self.frame("3.1")
        cap = caption("Общая схема",
                      "emb(e) = D(E(e)) · E без параметров задаёт вектор, "
                      "D с параметрами даёт эмбеддинг")
        self.play(FadeIn(cap), run_time=0.8)
        self.cap = cap

        e_box, v_box, z_box = (rect(90, 90, MUTED, S_THIN) for _ in range(3))
        E_box = rect(135, 135, ID, S_MID)
        D_box = rect(135, 135, DEC, S_MID)

        e_col = flex_col(e_box, mono("e", SIZE_MONO, MUTED), gap=27)
        E_col = flex_col(E_box, mono("E", SIZE_MONO, ID), gap=27)
        v_col = flex_col(v_box, mono("v", SIZE_MONO, MUTED), gap=27)
        D_col = flex_col(D_box, mono("D", SIZE_MONO, DEC), gap=27)
        z_col = flex_col(z_box, mono("z", SIZE_MONO, MUTED), gap=27)

        links = [connector() for _ in range(4)]
        row = flex_row(e_col, links[0], E_col, links[1], v_col,
                       links[2], D_col, links[3], z_col, gap=45)
        body_center(row)

        # layer 1: пять узлов слева направо
        self.play(
            LaggedStart(Create(e_box), Create(E_box), Create(v_box),
                        Create(D_box), Create(z_box), lag_ratio=0.35),
            run_time=2.4,
        )
        # layer 2: стрелки
        self.play(
            LaggedStart(*[Create(l) for l in links], lag_ratio=0.25),
            run_time=1.2,
        )
        # layer 3: подписи размерностей
        self.play(
            LaggedStart(*[FadeIn(c[1]) for c in
                          (e_col, E_col, v_col, D_col, z_col)],
                        lag_ratio=0.15),
            run_time=1.2,
        )
        self.E_box, self.D_box, self.z_box = E_box, D_box, z_box
        self.frame_rest = VGroup(e_col, v_col, *links,
                                 E_col[1], D_col[1], z_col[1])
        self.settle(b_flash_group(VGroup(*links), INK, 6, 0.18, 1.5),
                    b_wave(VGroup(e_box, E_box, v_box, D_box, z_box),
                           None, 1.06, 0.14, 1.6))

    # ------------------------------------------------------------ 3.2 -----
    def f_3_2(self):
        """Закрашенная ячейка скользит вдоль матрицы и вытягивает строку."""
        self.frame("3.2")
        cap = caption("one-hot и линейный слой",
                      "E: e ↦ one-hot ∈ {0,1}¹⁰⁸ · D: v ↦ Wᵀv, "
                      "W ∈ ℝ¹⁰⁸ˣ³² — 3.2 × 10⁹ параметров")

        col = code_column([0, 0, 1, 0, 0, 0])
        e_col = labelled(col, "10⁸", ID)
        mat = d_matrix(450, 248, bands=[80], band_h=36)
        d_col = labelled(mat, "10⁸ × 32", DEC)
        out = out_vector(360)
        z_col = labelled(out, "32", MUTED)
        row = flex_row(e_col, connector(), d_col, connector(), z_col, gap=90)
        body_center(row)

        # morph: пустые узлы E и D → начинка one-hot
        self.play(
            Transform(self.cap, cap),
            FadeOut(self.frame_rest),
            ReplacementTransform(self.E_box, col),
            ReplacementTransform(self.D_box, mat.box),
            ReplacementTransform(self.z_box, out),
            run_time=1.5,
        )
        self.play(FadeIn(e_col[1]), FadeIn(d_col[1]), FadeIn(z_col[1]),
                  run_time=0.6)
        # layer 3: строка выезжает вправо — умножение на one-hot и чтение
        # строки это одно и то же движение
        band = mat.rows[0]
        band.save_state()
        band.stretch_to_fit_width(0.001)
        band.move_to(mat.box.get_left() + RIGHT * 0.001, aligned_edge=LEFT)
        self.add(band)
        self.play(band.animate.restore(), run_time=1.4,
                  rate_func=rate_functions.ease_out_cubic)
        self.play(out.animate.set_color(DEC), run_time=0.5)

        self.col, self.mat, self.out = col, mat, out
        self.labels_3 = VGroup(e_col[1], d_col[1], z_col[1])
        self.links_3 = VGroup(row[1], row[3])
        self.settle(b_indicate(col[2], ID), b_flash_along(band, INK, 8, 1.1),
                    b_wave(out, DEC, 1.12, 0.05, 1.1))

    # ------------------------------------------------------------ 3.3 -----
    def f_3_3(self):
        """Обе размерности перекручиваются из 10⁸ в 10⁶; D не меняется."""
        self.frame("3.3")
        cap = caption("hashing trick",
                      "E: e ↦ one-hot(h(e)) ∈ {0,1}¹⁰⁶ · "
                      "D тот же по устройству, но в 100 раз короче — 128 МБ")

        funnel_slot = rect(135, 135, BG, 0)
        funnel_slot.set_opacity(0)
        col = code_column([0, 1, 0, 0])
        e_col = labelled(col, "10⁶", ID)
        mat = d_matrix(450, 168, bands=[40], band_h=36)
        d_col = labelled(mat, "10⁶ × 32", DEC)
        out = out_vector(270)
        z_col = labelled(out, "32", MUTED)
        row = flex_row(funnel_slot, e_col, connector(), d_col, connector(),
                       z_col, gap=63)
        body_center(row)

        ox = funnel_slot.get_left()[0] * 135 + 960
        oy_t = 540 - funnel_slot.get_top()[1] * 135
        oy_b = 540 - funnel_slot.get_bottom()[1] * 135
        funnel = VGroup(ray_px(ox, oy_t, 146, 27, ID, S_THIN),
                        ray_px(ox, oy_b, 146, -27, ID, S_THIN))

        self.play(Transform(self.cap, cap), run_time=0.8)
        # layer 1: воронка перед столбцом
        self.play(Create(funnel[0]), Create(funnel[1]), run_time=1.0)
        # layers 2 and 3: столбец и матрица укорачиваются — одна деформация
        self.play(
            ReplacementTransform(self.col, col),
            ReplacementTransform(self.mat, mat),
            ReplacementTransform(self.out, out),
            Transform(self.labels_3,
                      VGroup(e_col[1], d_col[1], z_col[1]).copy()),
            Transform(self.links_3, VGroup(row[2], row[4]).copy()),
            run_time=1.8,
        )
        self.remove(self.labels_3, self.links_3)
        self.add(e_col[1], d_col[1], z_col[1], row[2], row[4])

        self.col, self.mat, self.out = col, mat, out
        self.labels_3 = VGroup(e_col[1], d_col[1], z_col[1])
        self.links_3 = VGroup(row[2], row[4])
        self.funnel_3 = funnel
        self.settle(b_flash_group(funnel, ID, 6, 0.0, 1.1),
                    b_indicate(col[1], ID),
                    b_flash_along(mat.rows[0], INK, 8, 1.1))

    # ------------------------------------------------------------ 3.4 -----
    def f_3_4(self):
        """Идентификатор расщепляется на частное и остаток."""
        self.frame("3.4")
        cap = caption("quotient-remainder",
                      "e = 8371102934 → q = ⌊e/10³⌋ = 8371102, "
                      "r = e mod 10³ = 934 · 12.93 МБ вместо 12.8 ГБ")

        q_col = code_column([0, 1, 0], w=36, h=27)
        r_col = code_column([1, 0, 0], w=36, h=27)
        q_row = VGroup(mono("8371102", SIZE_MONO, ID), q_col)
        q_row.arrange(RIGHT, buff=px(27))
        r_row = VGroup(mono("934", SIZE_MONO, ID), r_col)
        r_row.arrange(RIGHT, buff=px(27))
        e_side = VGroup(q_row, r_row)
        e_side.arrange(DOWN, buff=px(63))

        m_q = rect(270, 135, DEC, S_MID)
        plus = mono("⊕", SIZE_MONO, DEC)
        m_r = rect(270, 63, DEC, S_MID)
        d_side = flex_col(m_q, plus, m_r, gap=27)

        out = out_vector(270)
        z_col = labelled(out, "32", MUTED)
        row = flex_row(e_side, connector(), d_side, connector(), z_col, gap=63)
        body_center(row)

        self.play(Transform(self.cap, cap), FadeOut(self.funnel_3),
                  run_time=0.8)
        # layers 1 and 2: chip расщепляется надвое, ветви расходятся
        self.play(
            ReplacementTransform(self.col, VGroup(q_col, r_col)),
            FadeOut(self.labels_3),
            Transform(self.links_3, VGroup(row[1], row[3]).copy()),
            run_time=1.4,
        )
        self.remove(self.links_3)
        self.add(row[1], row[3])
        self.play(FadeIn(q_row[0], shift=RIGHT * px(20)),
                  FadeIn(r_row[0], shift=RIGHT * px(20)), run_time=0.8)
        # layer 3: две матрицы вместо одной большой
        self.play(
            ReplacementTransform(self.mat, VGroup(m_q, m_r)),
            ReplacementTransform(self.out, out),
            run_time=1.4,
        )
        # layer 4: сложение
        self.play(FadeIn(plus), FadeIn(z_col[1]), run_time=0.7)

        self.qr_matrices = VGroup(m_q, m_r)
        self.col = VGroup(q_col, r_col)
        self.out = out
        self.labels_3 = VGroup(z_col[1])
        self.links_3 = VGroup(row[1], row[3])
        self.dead_3_4 = VGroup(q_row[0], r_row[0], plus)
        self.settle(b_indicate(q_row[0], ID), b_indicate(r_row[0], ID),
                    b_box(m_q, DEC), b_box(m_r, DEC),
                    b_spark(plus, DEC))

    # ------------------------------------------------------------ 3.5 -----
    def f_3_5(self):
        """В столбце отмечена не одна ячейка, а четыре; k строк складываются."""
        self.frame("3.5")
        cap = caption("bloom",
                      "E: k хешей отмечают k позиций · "
                      "D: сумма k строк одной таблицы 10⁶ × 32")

        col = code_column([0, 1, 0, 1, 0, 1, 0, 1], w=45, h=27)
        e_col = labelled(col, "k из 10⁶", ID)
        mat = d_matrix(450, 248, bands=[31, 93, 155, 186], band_h=27)
        d_col = labelled(mat, "Σ", DEC)
        out = out_vector(270)
        z_col = labelled(out, "32", MUTED)
        row = flex_row(e_col, connector(), d_col, connector(), z_col, gap=90)
        body_center(row)

        self.play(Transform(self.cap, cap), FadeOut(self.dead_3_4),
                  FadeOut(self.labels_3), run_time=0.8)
        # layer 1: столбец с k отметками
        self.play(
            ReplacementTransform(self.col, col),
            Transform(self.links_3, VGroup(row[1], row[3]).copy()),
            run_time=1.2,
        )
        self.remove(self.links_3)
        self.add(row[1], row[3])
        # morph: две матрицы → одна матрица с k отметками
        self.play(
            ReplacementTransform(self.qr_matrices, mat.box),
            ReplacementTransform(self.out, out),
            run_time=1.3,
        )
        self.play(FadeIn(e_col[1]), FadeIn(z_col[1]), run_time=0.5)
        # layer 2: k строк подсвечиваются;  layer 3: сумма
        self.play(
            LaggedStart(*[GrowFromEdge(r, LEFT) for r in mat.rows],
                        lag_ratio=0.2),
            run_time=1.6,
        )
        self.play(FadeIn(d_col[1]), run_time=0.5)

        self.bloom = VGroup(col, mat, out, e_col[1], d_col[1], z_col[1],
                            row[1], row[3])
        self.settle(b_wave(VGroup(col[1], col[3], col[5], col[7]), ID,
                           1.15, 0.1, 1.2),
                    b_flash_group(mat.rows, INK, 8, 0.1, 1.4),
                    b_indicate(d_col[1], DEC))

    # ------------------------------------------------------------ 3.6 -----
    def f_3_6(self):
        """Четыре кадра уменьшаются и встают в сетку два на два."""
        self.frame("3.6")
        cap = caption("Одна схема, четыре начинки",
                      "рамка e → E → v → D → z не меняется · "
                      "меняются только содержимое E и содержимое D")

        # one-hot
        p1 = mini_schema(code_column([0, 1, 0], w=27, h=18, gap=2),
                         rect(180, 135, DEC, S_THIN), "one-hot")
        # hashing — the funnel is drawn into the panel below
        hash_slot = rect(45, 45, BG, 0)
        hash_slot.set_opacity(0)
        p2_e = VGroup(hash_slot, code_column([1, 0], w=27, h=18, gap=2))
        p2_e.arrange(RIGHT, buff=px(27))
        p2 = mini_schema(p2_e, rect(180, 90, DEC, S_THIN), "hashing")
        # QR
        p3_e = code_column([1, 1], w=27, h=18, gap=8)
        p3_d = VGroup(rect(180, 54, DEC, S_THIN), rect(180, 27, DEC, S_THIN))
        p3_d.arrange(DOWN, buff=px(8))
        p3 = mini_schema(p3_e, p3_d, "QR")
        # bloom
        p4 = mini_schema(code_column([1, 0, 1, 0, 1], w=27, h=12, gap=2),
                         rect(180, 135, DEC, S_THIN), "bloom")

        # CSS grid `1fr 1fr` with gap 45/135: two equal columns across the
        # working area, panels left-aligned in their column (justify-items
        # defaults to stretch), rows centred.
        grid = VGroup(p1, p2, p3, p4)
        col_w = (1650 - 135) / 2
        row_h = max(p.height for p in grid) * 135
        # the common outline drawn in layer 3 sits 27 px outside each panel, so
        # the panels start one step in — the outline is what touches the margin
        for k, p in enumerate(grid):
            r, c = divmod(k, 2)
            p.move_to(pos(135 + 27 + c * (col_w + 135),
                          BODY_CY + (r - 0.5) * (row_h + 45)),
                      aligned_edge=LEFT)

        ox = hash_slot.get_left()[0] * 135 + 960
        oy_t = 540 - hash_slot.get_top()[1] * 135
        oy_b = 540 - hash_slot.get_bottom()[1] * 135
        mini_funnel = VGroup(ray_px(ox, oy_t, 49, 27, ID, S_THIN),
                             ray_px(ox, oy_b, 49, -27, ID, S_THIN))

        # layer 1: bloom уменьшается и встаёт на своё место в сетке
        self.play(
            Transform(self.cap, cap),
            ReplacementTransform(self.bloom, p4),
            run_time=1.5,
        )
        # layer 2: остальные три встают в сетку, сохраняя взаимное положение
        self.play(
            LaggedStart(FadeIn(p1, scale=0.85), FadeIn(p2, scale=0.85),
                        FadeIn(p3, scale=0.85), lag_ratio=0.25),
            run_time=1.8,
        )
        self.play(Create(mini_funnel[0]), Create(mini_funnel[1]), run_time=0.6)
        # layer 3: общая рамка обводится — различаются только начинки
        # one and the same outline on all four — the frame does not change
        ow = max(p.width for p in grid) * 135 + 54
        oh = max(p.height for p in grid) * 135 + 54
        outlines = VGroup(*[rect(ow, oh, DIM, S_THIN).move_to(
            p.get_left() + LEFT * px(27), aligned_edge=LEFT) for p in grid])
        self.play(
            LaggedStart(*[Create(o) for o in outlines], lag_ratio=0.12),
            run_time=1.4,
        )
        self.settle(b_flash_group(outlines, MUTED, 5, 0.14, 1.6),
                    b_wave(VGroup(*[p.d_slot for p in grid]), DEC,
                           1.06, 0.12, 1.4),
                    b_wave(VGroup(*[p.e_slot for p in grid]), ID,
                           1.1, 0.12, 1.4))
