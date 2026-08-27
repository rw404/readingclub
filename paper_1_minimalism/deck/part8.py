"""Часть 8 — Прод и реализация.  Кадры 8.1–8.9.

Что дало, где выигрыша нет, и как считать быстро: наивный маршрут через HBM
против одного ядра, в котором промежуточные значения не покидают регистры.
"""

import numpy as np
from manim import (
    VGroup, Line, DashedLine, VMobject, FadeIn, FadeOut, Create, Transform,
    ReplacementTransform, LaggedStart, GrowFromEdge, GrowFromCenter,
    rate_functions, ORIGIN, LEFT, RIGHT, UP, DOWN, DL, DR, UL, UR,
)

from deckkit.base import DeckScene
from deck.data import polylines
from deckkit.tokens import (
    px, pos, BG, INK, MUTED, DIM, ID, DEC, ATTR, ALERT, FONT_MONO,
    SIZE_DISPLAY, SIZE_TITLE, SIZE_MONO, S_THIN, S_MID, S_THICK,
    BODY_CX, BODY_CY, BODY_TOP, BODY_BOTTOM, BODY_H, BODY_LEFT, BODY_W,
)
from deckkit.components import (
    caption, mono, sans, text, rect, line_px, ray_px, dot, flex_row, flex_col,
    body_center, fixed_width, para, code_block,
    b_indicate, b_wave, b_flash_along, b_flash_group, b_box, b_spark,
)

# 8.2 — таблица растёт со словарём, декодер стоит на месте
DECADES = [("10³", 14, MUTED), ("10⁴", 37, MUTED),
           ("66 700", 73, INK), ("10⁵", 100, MUTED)]
DECODER_PCT = 73

# 8.4 — AUC, MovieLens-20M, шкала обрезана 97.0 … 97.8
QUALITY = [("Full Emb · таблица", 608, "97.64", MUTED, 0.55, INK),
           ("DHE", 637, "97.67", ID, 1.0, ID),
           ("Hash Emb", 323, "97.34", MUTED, 0.55, INK),
           ("Hybrid Hashing", 209, "97.22", MUTED, 0.55, INK)]
QUALITY_SIDE = [("DHE · только ID", "97.67", ID),
                ("DHE · ID + жанры", "97.71", ID),
                ("только жанры, без ID", "79.17", ALERT)]

K_TICKS = ["2", "4", "8", "32", "128", "1024", "2048"]

# 8.6 — абляции
ABL_LEFT = [("ReLU, без BN", 70, "97.47", MUTED, 0.5, MUTED),
            ("Mish, без BN", 100, "97.50", MUTED, 0.5, MUTED),
            ("ReLU + BN", 190, "97.59", MUTED, 0.5, MUTED),
            ("Mish + BN", 270, "97.67", ATTR, 1.0, ATTR)]
ABL_RIGHT = [("identity, 1 измерение", 17, "95.01", ALERT, 0.5, ALERT),
             ("binary, 27 измерений", 205, "97.36", MUTED, 0.5, MUTED),
             ("Fourier features", 15, "94.99", ALERT, 0.5, ALERT),
             ("dense hash, гаусс", 229, "97.66", MUTED, 0.5, MUTED),
             ("dense hash, равномерн.", 230, "97.68", ID, 1.0, ID)]

# 8.7 — секунды на 1 млн запросов, батч 100, V100
SPEED = [("Full Emb · таблица", MUTED,
          [(31, "3.4 c · CPU", 0.45, MUTED), (31, "3.4 c · GPU", 1.0, MUTED)]),
         ("Hash Emb", MUTED,
          [(77, "8.4 c · CPU", 0.45, MUTED), (56, "6.1 c · GPU", 1.0, MUTED)]),
         ("DHE", ID,
          [(700, "76.1 c · CPU", 0.45, MUTED),
           (250, "27.2 c · GPU", 1.0, ID)])]

# 8.8 / 8.9 — стадии маршрута данных, одна геометрия на оба кадра
STAGES = [(20, "hᵢ", ID), (146, "vᵢ", ID), (272, "W₁v", ID), (398, "y", DEC)]

NAIVE_CODE = [
    (0, [("# три отдельных ядра, три промежуточных тензора", MUTED)]),
    (0, [("h = (A * e[:,", INK), ("None", DEC), ("] + B) % P % M", INK),
         ("   ", INK), ("# [8192,1024] i64", MUTED)]),
    (0, [("v = 2.0 * h.float() / (M - 1) - 1.0", INK),
         ("   ", INK), ("# [8192,1024] f32", MUTED)]),
    (0, [("y = v @ W1 + c1", INK),
         ("                    ", INK), ("# [8192,1024] f32", MUTED)]),
    (0, []),
    (0, [("# каждая строка пишет тензор в HBM,", MUTED)]),
    (0, [("# следующая читает его обратно", MUTED)]),
]

KERNEL_CODE = [
    (0, [("@triton.jit", ID)]),
    (0, [("def", DEC), (" dhe_l1(E, A, B, W1, Y, K: tl.constexpr,", INK)]),
    (184.8, [("N: tl.constexpr, BK: tl.constexpr,", INK)]),
    (184.8, [("BN: tl.constexpr):", INK)]),
    (67.2, [("row = tl.program_id(0); e = tl.load(E + row)", INK)]),
    (67.2, [("acc = tl.zeros((BN,), dtype=tl.float32)", INK)]),
    (67.2, [("for", DEC), (" k0 ", INK), ("in", DEC),
            (" range(0, K, BK):", INK)]),
    (134.4, [("kk = k0 + tl.arange(0, BK)", INK)]),
    (134.4, [("a = tl.load(A + kk); b = tl.load(B + kk)", INK)]),
    (134.4, [("h = (a * e + b) % P % M", INK), ("   ", INK),
             ("# регистры", ATTR)]),
    (134.4, [("v = 2.0 * h.to(tl.float32) / (M-1) - 1.0", INK)]),
    (134.4, [("w = tl.load(W1 + kk[:,", INK), ("None", DEC),
             ("]*N + tl.arange(0,BN))", INK)]),
    (134.4, [("acc += tl.sum(v[:,", INK), ("None", DEC),
             ("] * w, axis=0)", INK)]),
    (67.2, [("tl.store(Y + row*N + tl.arange(0,BN), acc)", INK)]),
]

# Подписи держим короткими: легенда идёт в два столбца слева от схемы
# маршрута, а та начинается на 1185 px.
DIMS_LEGEND = [("K", ID, "1024 · длина вектора"),
               ("BK", ID, "блок по K за итерацию"),
               ("N", DEC, "1024 · ширина слоя W1"),
               ("BN", DEC, "блок по N на программу")]



def metric_row(label, bar_w, value, bar_col, opacity, val_col, label_w=340,
               bar_h=36):
    r = VGroup(fixed_width(mono(label, SIZE_MONO,
                                bar_col if opacity == 1.0 else MUTED), label_w),
               rect(bar_w, bar_h, bar_col, 0, fill=bar_col,
                    fill_opacity=opacity),
               mono(value, SIZE_MONO, val_col))
    r.arrange(RIGHT, buff=px(27))
    return r


def route_diagram(kernel=False):
    """The data route of 8.8 / 8.9 — one geometry, two stories.

    600x520 px: four stages on the left, the HBM column on the right, and
    either three red round trips through it or one green kernel box.
    """
    g = VGroup()
    W, H = 600, 520
    ox = BODY_LEFT + BODY_W - W
    oy = BODY_CY - H / 2

    def P(x, y):
        return pos(ox + x, oy + y)

    hbm = rect(80, 448, DIM, 0, fill=DIM, fill_opacity=1)
    hbm.move_to(P(480, 20), aligned_edge=UL)
    hbm_lab = mono("HBM", SIZE_MONO, MUTED)
    hbm_lab.move_to(P(480, 478 + 14), aligned_edge=LEFT)
    g.add(hbm, hbm_lab)

    traffic = VGroup()
    if not kernel:
        # three round trips: each stage writes its tensor and reads it back
        for top in (90, 216, 342):
            traffic.add(Line(P(99, top), P(99, top + 28),
                             color=ALERT, stroke_width=S_THIN))
            traffic.add(Line(P(99, top + 28), P(480, top + 28),
                             color=ALERT, stroke_width=S_THIN))
    else:
        # one write, at the very end
        traffic.add(Line(P(99, 468), P(480, 468), color=DEC,
                         stroke_width=S_THIN))
    g.add(traffic)

    boxes = VGroup()
    labels = VGroup()
    for top, name, colour in STAGES:
        b = rect(200, 70, colour, S_THIN)
        b.move_to(P(0, top), aligned_edge=UL)
        lab = mono(name, SIZE_MONO, MUTED)
        lab.move_to(P(220, top + 21 + 14), aligned_edge=LEFT)
        boxes.add(b)
        labels.add(lab)
    g.add(boxes, labels)

    frame = None
    frame_lab = None
    if kernel:
        frame = rect(236, 358, ATTR, S_MID)
        frame.move_to(P(-18, 2), aligned_edge=UL)
        frame_lab = mono("одно ядро", SIZE_MONO, ATTR)
        frame_lab.move_to(P(220, 370 + 14), aligned_edge=LEFT)
        g.add(frame, frame_lab)

    g.hbm, g.hbm_lab = hbm, hbm_lab
    g.traffic, g.boxes, g.labels = traffic, boxes, labels
    g.frame, g.frame_lab = frame, frame_lab
    return g


class Part8(DeckScene):
    """Прод и реализация."""

    def construct(self):
        self.f_8_1()
        self.f_8_2()
        self.f_8_3()
        self.f_8_4()
        self.f_8_5()
        self.f_8_6()
        self.f_8_7()
        self.f_8_8()
        self.f_8_9()
        self.outro()

    # ------------------------------------------------------------ 8.1 -----
    def f_8_1(self):
        """Верхняя полоса сжимается, нижняя растёт."""
        self.frame("8.1")
        cap = caption("Память меняется на арифметику",
                      "lookup: 128 байт чтения, ~0 FLOP · "
                      "DHE: 8.54 МБ весов и 4.26 MFLOP на вызов")
        self.play(FadeIn(cap), run_time=0.8)
        self.cap = cap

        def bar_row(w, colour, label, lab_col):
            r = VGroup(rect(w, 63, colour, 0, fill=colour, fill_opacity=1),
                       mono(label, SIZE_MONO, lab_col))
            r.arrange(RIGHT, buff=px(45))
            return r

        mem_table = bar_row(1080, DIM, "12.8 ГБ", MUTED)
        mem_dhe = bar_row(8, DEC, "8.54 МБ", DEC)
        flop_table = bar_row(8, DIM, "~0 FLOP", MUTED)
        flop_dhe = bar_row(1080, DEC, "4.26 MFLOP", DEC)
        rows = VGroup(mem_table, mem_dhe, flop_table, flop_dhe)
        for r in rows:
            r.move_to(pos(BODY_LEFT, 0), aligned_edge=LEFT)
        rows.arrange(DOWN, buff=px(90), aligned_edge=LEFT)
        rows.move_to(pos(BODY_LEFT, BODY_CY), aligned_edge=LEFT)
        # border-top of the FLOP half — spans the working area, and only its
        # height follows the rows (move_to would re-centre it off the margin)
        rule = line_px(BODY_LEFT, 0, BODY_LEFT + BODY_W, 0, DIM, S_THIN)
        rule.set_y(float((mem_dhe.get_bottom() + flop_table.get_top())[1]) / 2)

        # layer 1: полоса памяти сжимается
        self.play(GrowFromEdge(mem_table[0], LEFT), FadeIn(mem_table[1]),
                  run_time=1.0)
        shrunk = mem_dhe[0].copy()
        big = rect(1080, 63, DEC, 0, fill=DEC, fill_opacity=1)
        big.move_to(mem_dhe[0].get_left(), aligned_edge=LEFT)
        self.add(big)
        self.play(Transform(big, shrunk), run_time=1.6)
        self.remove(big)
        self.add(mem_dhe[0])
        self.play(FadeIn(mem_dhe[1]), Create(rule), run_time=0.6)
        # layer 2: полоса арифметики растёт
        self.play(FadeIn(flop_table), run_time=0.6)
        self.play(GrowFromEdge(flop_dhe[0], LEFT), run_time=1.6)
        # layer 3: числа
        self.play(FadeIn(flop_dhe[1]), run_time=0.6)
        self.bars_8_1 = VGroup(mem_dhe[0], flop_dhe[0])
        self.dead = VGroup(rows, rule)
        self.settle(b_flash_along(mem_table[0], INK, 8, 1.3),
                    b_indicate(mem_dhe[0], DEC, 1.5),
                    b_flash_along(flop_dhe[0], INK, 8, 1.3),
                    b_indicate(flop_table[0], MUTED, 1.5))

    # ------------------------------------------------------------ 8.2 -----
    def f_8_2(self):
        """Столбики таблицы растут с словарём, декодер стоит на месте."""
        self.frame("8.2")
        cap = caption("На малом словаре выигрыша нет",
                      "декодер не зависит от словаря · "
                      "таблица дешевле до 66 700 значений")

        plot_h = BODY_H - 90
        groups = VGroup()
        for name, pct, lab_col in DECADES:
            table = rect(63, plot_h * pct / 100, ID, 0, fill=ID,
                         fill_opacity=1)
            decoder = rect(63, plot_h * DECODER_PCT / 100, DIM, 0, fill=DIM,
                           fill_opacity=1)
            pair = VGroup(table, decoder)
            pair.arrange(RIGHT, buff=px(8), aligned_edge=DOWN)
            lab = mono(name, SIZE_MONO, lab_col)
            grp = VGroup(pair, lab)
            grp.pair, grp.label, grp.table = pair, lab, table
            groups.add(grp)
        for g in groups:
            g.pair.move_to(pos(0, BODY_BOTTOM - 45), aligned_edge=DOWN)
            g.label.move_to(g.pair.get_bottom() + DOWN * px(31))
        row = VGroup(*[g for g in groups])
        for k, g in enumerate(groups):
            g.move_to(pos(BODY_CX - 1.5 * (134 + 90) + k * (134 + 90),
                          BODY_BOTTOM), aligned_edge=DOWN)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # morph: две полосы размена → пары столбиков безубыточности
        self.play(
            ReplacementTransform(self.bars_8_1[0], groups[0].pair[0]),
            ReplacementTransform(self.bars_8_1[1], groups[0].pair[1]),
            run_time=1.2,
        )
        self.play(FadeIn(groups[0].label), run_time=0.4)
        # layer 1: пары столбиков по декадам
        self.play(
            LaggedStart(*[FadeIn(g, shift=UP * px(20)) for g in groups[1:]],
                        lag_ratio=0.25),
            run_time=2.0,
        )
        # layer 2: точка пересечения подсвечивается
        cross = groups[2]
        self.play(cross.pair.animate.scale(1.05), run_time=0.5)
        self.play(cross.pair.animate.scale(1 / 1.05), run_time=0.5)
        self.cross = cross
        self.dead = VGroup(groups)
        self.settle(b_wave(VGroup(*[g.pair[0] for g in groups]), ID,
                           1.05, 0.16, 1.4),
                    b_box(cross.pair, INK), b_indicate(cross.label, INK))

    # ------------------------------------------------------------ 8.3 -----
    def f_8_3(self):
        """У таблицы хвост словаря схлопнут, у DHE каждое значение своё."""
        self.frame("8.3")
        cap = caption("Выигрыш на редких и новых",
                      "у таблицы хвост словаря схлопнут в <unk> · "
                      "у DHE каждое значение получает свой вектор")

        def dot_row(colours):
            g = VGroup()
            pitch = 1170 / 20
            for i, c in enumerate(colours):
                d = dot(18, c)
                d.move_to(pos(BODY_CX - 1170 / 2 + i * pitch + 9, 0))
                g.add(d)
            return g

        top = dot_row([ALERT] + [DIM] * 19)
        bottom = dot_row([ATTR] * 20)
        block = VGroup(top, bottom)
        block.arrange(DOWN, buff=px(135))
        body_center(block)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: два ряда точек — сначала оба «живые»
        live = dot_row([ATTR] * 20)
        live.move_to(top.get_center())
        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in live], lag_ratio=0.03),
            run_time=1.4,
        )
        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in bottom], lag_ratio=0.03),
            run_time=1.4,
        )
        # layer 2: верхний ряд гаснет — почти все схлопываются в заглушку
        self.play(
            *[Transform(a, b) for a, b in zip(live, top)],
            run_time=1.6,
        )
        # layer 3: нижний остаётся целым
        self.play(bottom.animate.set_opacity(1), run_time=0.5)
        self.rows_8_3 = VGroup(live, bottom)
        self.dead = self.rows_8_3
        self.settle(b_wave(bottom, ATTR, 1.3, 0.02, 1.5),
                    b_spark(live[0], ALERT),
                    b_wave(VGroup(*live[1:]), MUTED, 1.15, 0.02, 1.3))

    # ------------------------------------------------------------ 8.4 -----
    def f_8_4(self):
        """DHE догоняет полную таблицу по AUC."""
        self.frame("8.4")
        cap = caption("Качество: DHE догоняет полную таблицу",
                      "AUC · MovieLens-20M, словарь 165K, backbone MLP · "
                      "DHE при 1/4 размера полной модели · "
                      "шкала обрезана 97.0 … 97.8")

        rows = VGroup(*[metric_row(*q) for q in QUALITY])
        rows.arrange(DOWN, buff=px(36), aligned_edge=LEFT)
        rows.move_to(pos(BODY_LEFT, BODY_CY), aligned_edge=LEFT)

        sx = BODY_LEFT + BODY_W - 405
        side = VGroup()
        for label, value, col in QUALITY_SIDE:
            b = VGroup(para(label, 405, SIZE_MONO, MUTED),
                       mono(value, SIZE_MONO, col))
            b.arrange(DOWN, buff=px(10), aligned_edge=LEFT)
            side.add(b)
        side.arrange(DOWN, buff=px(36), aligned_edge=LEFT)
        side.move_to(pos(sx, BODY_CY), aligned_edge=LEFT)
        sep = line_px(sx - 45, BODY_TOP, sx - 45, BODY_BOTTOM, DIM, S_THIN)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layers 1-2: ось AUC и полоски по одной
        self.play(
            LaggedStart(*[FadeIn(r, shift=RIGHT * px(20)) for r in rows],
                        lag_ratio=0.25),
            run_time=2.4,
        )
        # layer 3: столбец с атрибутами
        self.play(Create(sep), run_time=0.5)
        self.play(
            LaggedStart(*[FadeIn(b) for b in side], lag_ratio=0.25),
            run_time=1.8,
        )
        self.dhe_bar = rows[1][1]
        self.dead = VGroup(rows[0], rows[2], rows[3], rows[1][0], rows[1][2],
                           side, sep)
        self.settle(b_wave(VGroup(*[r[1] for r in rows]), None, 1.05,
                           0.16, 1.5),
                    b_indicate(rows[1][2], ID),
                    b_indicate(side[2][1], ALERT))

    # ------------------------------------------------------------ 8.5 -----
    def f_8_5(self):
        """Кривая, которая оправдывает k = 1024."""
        self.frame("8.5")
        cap = caption("Только DHE выигрывает от роста числа хешей",
                      "AUC · backbone MLP · по горизонтали число хеш-функций k, "
                      "шкала неравномерная · вертикальная шкала 92.5 … 98.0")

        plot_w = BODY_W - 405 - 90
        plot_h = 405
        ox, oy = BODY_LEFT, BODY_CY - plot_h / 2

        def P(xp, yp):
            return pos(ox + plot_w * xp / 100, oy + plot_h * yp / 100)

        axes = VGroup(Line(P(0, 0), P(0, 100), color=DIM, stroke_width=S_THIN),
                      Line(P(0, 100), P(100, 100), color=DIM,
                           stroke_width=S_THIN))
        curves = VGroup()
        for colour, width, pts in polylines("8.5"):
            m = VMobject(color=colour, stroke_width=width)
            m.set_points_as_corners([P(x, y) for x, y in pts])
            curves.add(m)
        ticks = VGroup()
        for i, name in enumerate(K_TICKS):
            col = ID if name == "1024" else MUTED
            t = mono(name, SIZE_MONO, col)
            base = P(i * 100 / 6, 100) + DOWN * px(18 + 14)
            # the end ticks align to the axis ends instead of centring on them,
            # so the first one does not hang past the 135 px margin
            edge = LEFT if i == 0 else RIGHT if i == len(K_TICKS) - 1 else None
            t.move_to(base, aligned_edge=edge) if edge is not None \
                else t.move_to(base)
            ticks.add(t)

        sx = BODY_LEFT + BODY_W - 405
        legend = VGroup()
        for w, h, col, name in ((54, 4, ID, "DHE"), (54, 2, DEC, "Bloom Emb"),
                                (54, 2, MUTED, "Hybrid Emb")):
            r = VGroup(rect(w, h, col, 0, fill=col, fill_opacity=1),
                       mono(name, SIZE_MONO, col))
            r.arrange(RIGHT, buff=px(18))
            legend.add(r)
        notes = VGroup(mono("k = 2", SIZE_MONO, MUTED),
                       mono("92.74", SIZE_MONO, ALERT),
                       mono("k = 1024", SIZE_MONO, MUTED),
                       mono("97.67", SIZE_MONO, ID))
        notes.arrange(DOWN, buff=px(14), aligned_edge=LEFT)
        side = VGroup(*legend, notes)
        side.arrange(DOWN, buff=px(36), aligned_edge=LEFT)
        side.move_to(pos(sx, BODY_CY), aligned_edge=LEFT)
        sep = line_px(sx - 45, BODY_TOP, sx - 45, BODY_BOTTOM, DIM, S_THIN)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: оси
        self.play(ReplacementTransform(self.dhe_bar, axes[1]), run_time=1.0)
        self.play(Create(axes[0]), FadeIn(ticks), run_time=0.8)
        # layer 2: кривые baseline стоят на месте
        self.play(Create(curves[1]), Create(curves[2]), run_time=1.4)
        # layer 3: кривая DHE слева направо
        self.play(Create(curves[0]), run_time=2.4)
        # layer 4: отметка k = 1024
        self.play(Create(sep), run_time=0.4)
        self.play(
            LaggedStart(*[FadeIn(s) for s in side], lag_ratio=0.2),
            run_time=1.8,
        )
        self.k_point = curves[0]
        self.dead = VGroup(axes, ticks, curves, side, sep)
        self.settle(b_flash_along(curves[0], INK, 6, 1.8, 0.3),
                    b_indicate(ticks[5], ID),
                    b_flash_group(VGroup(curves[1], curves[2]), MUTED, 4,
                                  0.15, 1.4))

    # ------------------------------------------------------------ 8.6 -----
    def f_8_6(self):
        """Две абляции, обе подтверждают то, что мы утверждали раньше."""
        self.frame("8.6")
        cap = caption("Абляции: что именно даёт вклад",
                      "AUC · backbone MLP · слева нормировка и активация, "
                      "справа выбор кодировки при том же декодере")

        lw = (BODY_W - 90) / 2.15
        rw = BODY_W - 90 - lw
        left = VGroup(mono("декодер: нормировка и активация", SIZE_MONO, MUTED),
                      *[metric_row(*a, label_w=290, bar_h=30)
                        for a in ABL_LEFT])
        left.arrange(DOWN, buff=px(27), aligned_edge=LEFT)
        left.move_to(pos(BODY_LEFT, BODY_CY), aligned_edge=LEFT)

        sx = BODY_LEFT + lw + 90
        right = VGroup(mono("кодировка на входе декодера", SIZE_MONO, MUTED),
                       *[metric_row(*a, label_w=340, bar_h=30)
                         for a in ABL_RIGHT])
        right.arrange(DOWN, buff=px(27), aligned_edge=LEFT)
        right.move_to(pos(sx, BODY_CY), aligned_edge=LEFT)
        sep = line_px(sx - 45, BODY_TOP, sx - 45, BODY_BOTTOM, DIM, S_THIN)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: левая таблица BN и Mish
        self.play(
            LaggedStart(*[FadeIn(r, shift=RIGHT * px(16)) for r in left],
                        lag_ratio=0.18),
            run_time=2.0,
        )
        # layer 2: правая таблица кодировок
        self.play(Create(sep), run_time=0.4)
        self.play(
            LaggedStart(*[FadeIn(r, shift=RIGHT * px(16)) for r in right],
                        lag_ratio=0.18),
            run_time=2.2,
        )
        # layer 3: подсветка лучших
        self.play(left[-1][1].animate.scale(1.04),
                  right[-1][1].animate.scale(1.04), run_time=0.5)
        self.play(left[-1][1].animate.scale(1 / 1.04),
                  right[-1][1].animate.scale(1 / 1.04), run_time=0.5)
        self.dense_row = right[-1]
        self.dead = VGroup(left, right, sep)
        self.settle(b_wave(VGroup(*[r[1] for r in left[1:]]), None,
                           1.06, 0.16, 1.3),
                    b_wave(VGroup(*[r[1] for r in right[1:]]), None,
                           1.06, 0.14, 1.4),
                    b_indicate(left[-1][2], ATTR),
                    b_indicate(right[-1][2], ID))

    # ------------------------------------------------------------ 8.7 -----
    def f_8_7(self):
        """Цена, замеренная в статье."""
        self.frame("8.7")
        cap = caption("Скорость: за качество платим вычислениями",
                      "секунды на 1 млн запросов, батч 100 · NVIDIA V100 · "
                      "замер на наивной реализации")

        groups = VGroup()
        for name, name_col, bars in SPEED:
            rows = VGroup(mono(name, SIZE_MONO, name_col))
            for w, label, opacity, lab_col in bars:
                r = VGroup(rect(w, 30, name_col if name_col == ID else MUTED,
                                0, fill=name_col if name_col == ID else MUTED,
                                fill_opacity=opacity),
                           mono(label, SIZE_MONO, lab_col))
                r.arrange(RIGHT, buff=px(27))
                rows.add(r)
            rows.arrange(DOWN, buff=px(14), aligned_edge=LEFT)
            groups.add(rows)
        groups.arrange(DOWN, buff=px(45), aligned_edge=LEFT)
        groups.move_to(pos(BODY_LEFT, BODY_CY), aligned_edge=LEFT)

        sx = BODY_LEFT + BODY_W - 450
        side = VGroup(
            VGroup(mono("ускорение от GPU", SIZE_MONO, MUTED),
                   mono("−64 %", SIZE_MONO, ATTR),
                   mono("у таблицы −1 %", SIZE_MONO, MUTED)),
            VGroup(mono("DHE к таблице на GPU", SIZE_MONO, MUTED),
                   mono("× 8", SIZE_MONO, ALERT)),
        )
        for b in side:
            b.arrange(DOWN, buff=px(14), aligned_edge=LEFT)
        side.arrange(DOWN, buff=px(36), aligned_edge=LEFT)
        side.move_to(pos(sx, BODY_CY), aligned_edge=LEFT)
        sep = line_px(sx - 45, BODY_TOP, sx - 45, BODY_BOTTOM, DIM, S_THIN)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: три пары полосок
        self.play(
            LaggedStart(*[FadeIn(g, shift=RIGHT * px(16)) for g in groups],
                        lag_ratio=0.25),
            run_time=2.6,
        )
        # layers 2-3: ускорение от GPU и отношение к таблице
        self.play(Create(sep), run_time=0.4)
        self.play(
            LaggedStart(*[FadeIn(b) for b in side], lag_ratio=0.3),
            run_time=1.8,
        )
        self.gpu_bar = groups[2][2][0]
        self.dead = VGroup(groups, side, sep)
        self.settle(b_flash_along(groups[2][1][0], INK, 8, 1.4),
                    b_indicate(groups[2][2][0], ID),
                    b_indicate(side[1][1], ALERT),
                    b_wave(VGroup(groups[0][1][0], groups[0][2][0]), MUTED,
                           1.2, 0.14, 1.0))

    # ------------------------------------------------------------ 8.8 -----
    def f_8_8(self):
        """Три строки на PyTorch — три отдельных ядра."""
        self.frame("8.8")
        cap = caption("Наивный маршрут: три ядра, три тензора в HBM",
                      "batch = 8192 · k = 1024 · "
                      "каждая строка PyTorch материализует полный тензор")

        code = code_block(NAIVE_CODE, BODY_LEFT, BODY_CY - 240,
                          SIZE_MONO, line_height=1.5)
        totals = VGroup(mono("≈ 134 МБ", SIZE_MONO, ALERT),
                        mono("записано и прочитано обратно", SIZE_MONO, MUTED),
                        mono("3 ядра", SIZE_MONO, ALERT))
        totals.arrange(RIGHT, buff=px(63))
        totals.move_to(pos(BODY_LEFT, BODY_CY + 210), aligned_edge=LEFT)
        rule = line_px(BODY_LEFT, BODY_CY + 168,
                       BODY_LEFT + BODY_W - 663, BODY_CY + 168, DIM, S_THIN)

        route = route_diagram(kernel=False)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: четыре стадии
        self.play(
            ReplacementTransform(self.gpu_bar, route.boxes[0]),
            FadeIn(route.hbm), FadeIn(route.hbm_lab),
            run_time=1.2,
        )
        self.play(
            LaggedStart(*[Create(b) for b in route.boxes[1:]], lag_ratio=0.2),
            FadeIn(route.labels),
            run_time=1.4,
        )
        # layer 2: код построчно
        self.play(
            LaggedStart(*[FadeIn(r) for r in code.rows if len(r)],
                        lag_ratio=0.2),
            run_time=2.0,
        )
        # layer 3: красные заходы в HBM
        self.play(
            LaggedStart(*[Create(t) for t in route.traffic], lag_ratio=0.12),
            run_time=1.8,
        )
        # layer 4: счётчик трафика
        self.play(Create(rule), FadeIn(totals), run_time=0.9)
        self.route = route
        self.dead = VGroup(code, totals, rule)
        self.settle(b_flash_group(route.traffic, ALERT, 6, 0.08, 1.6),
                    b_wave(route.boxes, None, 1.04, 0.14, 1.3),
                    b_indicate(totals[0], ALERT))

    # ------------------------------------------------------------ 8.9 -----
    def f_8_9(self):
        """Тот же расчёт одним ядром Triton."""
        self.frame("8.9")
        cap = caption("Одно ядро: хеши, нормировка и первый слой сразу",
                      "aᵢ, bᵢ и промежуточные значения живут в регистрах · "
                      "в HBM уходит только выход")

        # The left column is stacked from the top of the working area: the
        # kernel is fourteen lines, so legend and totals hang off its bottom
        # rather than off fixed offsets, which would run into the code.
        LH = SIZE_MONO * 1.21
        code_top = BODY_TOP + 6
        code = code_block(KERNEL_CODE, BODY_LEFT, code_top,
                          SIZE_MONO, line_height=1.21)
        code_bottom = code_top + len(KERNEL_CODE) * LH

        legend = VGroup()
        for name, col, desc in DIMS_LEGEND:
            r = VGroup(fixed_width(mono(name, SIZE_MONO, col), 54),
                       mono(desc, SIZE_MONO, MUTED))
            r.arrange(RIGHT, buff=px(27))
            legend.add(r)
        legend.arrange_in_grid(rows=2, cols=2, buff=(px(27), px(10)),
                               col_alignments="ll")
        legend.move_to(pos(BODY_LEFT, code_bottom + 18), aligned_edge=UL)

        rule_y = code_bottom + 18 + legend.height * 135 + 24
        rule = line_px(BODY_LEFT, rule_y,
                       BODY_LEFT + BODY_W - 663, rule_y, DIM, S_THIN)
        totals = VGroup(mono("≈ 34 МБ", SIZE_MONO, ATTR),
                        mono("только выход", SIZE_MONO, MUTED),
                        mono("1 ядро", SIZE_MONO, ATTR))
        totals.arrange(RIGHT, buff=px(63))
        totals.move_to(pos(BODY_LEFT, rule_y + 18), aligned_edge=UL)

        kroute = route_diagram(kernel=True)

        self.play(Transform(self.cap, cap), FadeOut(self.dead), run_time=0.9)
        # layer 1: те же стадии остаются на месте
        # layer 2: код построчно
        self.play(
            LaggedStart(*[FadeIn(r) for r in code.rows if len(r)],
                        lag_ratio=0.12),
            run_time=2.4,
        )
        # layer 3: зигзаг через HBM → рамка одного ядра
        self.play(
            ReplacementTransform(self.route.traffic, kroute.frame),
            run_time=1.4,
        )
        self.play(FadeIn(kroute.frame_lab), run_time=0.5)
        # layer 4: единственная запись выхода
        self.play(Create(kroute.traffic), run_time=0.9)
        self.play(Create(rule), FadeIn(legend), FadeIn(totals), run_time=1.0)
        self.kroute = kroute
        self.dead = VGroup(code, legend, totals, rule)
        self.settle(b_flash_along(kroute.frame, ATTR, 6, 1.5),
                    b_wave(VGroup(*kroute.boxes[:3]), ATTR, 1.05, 0.14, 1.2),
                    b_flash_along(kroute.traffic[0], DEC, 6, 1.2),
                    b_indicate(totals[0], ATTR))
