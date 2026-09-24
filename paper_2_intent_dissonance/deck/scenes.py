"""The seventeen storyboard scenes, one function per scene, one state per step.

Each function is a line-by-line port of the storyboard's `Component` method of
the same name (`world`, `choice`, `pipes`, …): same coordinates, same colours,
same transition delays.  `build(frame, step)` returns everything on screen for
that click — the scene itself plus the chrome (step counter, narration line,
code listing) — as prims for `stage.Stage`.
"""

import math

from deck.iso import (
    P, shade, poly, text, flow, box, txt, lab, ln, wl, rect, circle_pts, fig,
    arc, wp, cube, tower, student, at, group_op, with_anim, scene, flat,
)
from deck.tokens import (
    K, YELLOW, NARR, DIMTXT, DIM, CODE_HL, CODE_HL_A, CELL_T, RIBBON,
)

# ------------------------------------------------------------- the deck ----
# clicks per frame — the storyboard's MAX
MAX = [0, 3, 0, 3, 5, 3, 3, 0, 3, 5, 5, 3, 0, 4, 4, 2, 6]

# «screen», «label» exactly as data-screen-label / data-label
SCREENS = [f"{i + 1:02d}" for i in range(17)]

NAR = [
    ["Статья KDD’26 (Google, DeepMind): перенос знаний от модели Homepage к модели Shorts."],
    ["Три поверхности: Homepage, Watch Page и Shorts.",
     "Учитель — большая модель, обучена на данных Homepage и Watch Page.",
     "Студенты — маленькие модели, по одной на поверхность. Они ранжируют выдачу.",
     "Учитель передаёт студентам мягкие метки. Shorts к учителю не подключён."],
    ["Акт I. Почему прямой перенос на Shorts не работает."],
    ["Homepage: пользователь выбирает видео из сетки. Клик — явный сигнал.",
     "Пользователь сам выбирает, что смотреть.",
     "Shorts: видео запускаются автоматически в ленте. Просмотр — не выбор.",
     "Длина видео: 15–20 мин на Homepage, около 1 мин в Shorts."],
    ["Попытка: взять ближайшую задачу учителя вместо задачи студента. Размер кубика — среднее значение метки.",
     "Клик 0.044 против позитива 0.435 — разница в 10 раз.",
     "Досмотр: 0.768 против 0.925.",
     "Потребление: 415.8 против 19.5 — разные шкалы.",
     "Доля досмотра: 0.692 против 0.711.",
     "Средние совпадают в двух парах из четырёх."],
    ["Одни и те же видео Shorts: поведение в ленте и в браузинге различается. Досмотр 0.925 против 0.537.",
     "Остальные задачи тоже различаются.",
     "Признаки: каждая клетка — группа входных признаков.",
     "Доля признаков Shorts: 6.2% у учителя, 79% у студента."],
    ["Офлайн AUC позитива: 0.7706 → 0.7708. Без изменений.",
     "Голубая плоскость — уровень контрольной группы A/B-теста (0%). Выше — рост метрики, ниже — падение.",
     "Онлайн: вовлечённость −0.12%, потребление −0.46%.",
     "Вывод: такие метки ухудшают студента."],
    ["Акт II. Решение: дообучить учителя на данных Shorts."],
    ["Данные: в обучение учителя добавлен поток Shorts.",
     "Вход: общие признаки + признаки своей поверхности.",
     "Признаки других поверхностей заполняются нулями.",
     "Старые задачи не меняются: для них новые признаки нулевые."],
    ["Задачи: к учителю добавлены 4 головы Shorts.",
     "Новые головы пока не обучены.",
     "Сэмпл Homepage: маска = 0, головы Shorts не обучаются.",
     "Сэмпл Shorts: маска = 1, головы Shorts обучаются.",
     "Шумные задачи: stop-gradient, градиент не идёт в общий backbone.",
     "Без stop-gradient качество старых задач падает."],
    ["Архитектура: ResNet использует одни веса признаков для всех поверхностей.",
     "Вход Shorts — веса те же.",
     "HiFormer (attention): веса зависят от входа. Для Shorts важнее свайпы.",
     "Для Homepage важнее длинные просмотры.",
     "Attention требует больше памяти.",
     "Lion вместо Adagrad и квантование AQT освобождают память. Время шага то же."],
    ["Раньше: после обучения учителя отдельный инференс размечал данные.",
     "In-band: метки пишутся во время обучения. Задержка −10 ч.",
     "У студента одна голова учится и на ground truth, и на метках учителя.",
     "Решение: отдельная aux-голова для меток учителя."],
    ["Акт III. Результаты."],
    ["Абляция 2×2: архитектура × данные Shorts. Метрика — AUC клика Homepage, база 0.7557.",
     "Только данные: +0.0002.",
     "Только архитектура: +0.0015.",
     "Вместе: +0.0062.",
     "Сумма по отдельности +0.0017 — вместе почти в 4 раза больше."],
    ["Онлайн A/B-тесты на Shorts. Плоскость — уровень контроля (0%).",
     "Без дообучения: −0.12% и −0.46%.",
     "С дообучением: +0.16% и +0.37%.",
     "С дообучением и новой архитектурой: +0.27% и +0.82%.",
     "Homepage: +0.09%. Watch Page: без изменений."],
    ["Учитель подключён ко всем трём поверхностям.",
     "Подход применим к другим форматам: длинные видео, клипы, посты.",
     "Конец."],
    ["Метод в двух функциях. Нажимайте →.",
     "Вход: признаки других поверхностей — нули.",
     "Backbone — HiFormer.",
     "detach() — stop-gradient для шумных задач.",
     "Маска M[t]: головы Shorts учатся только на Shorts. Оптимизатор — Lion + AQT.",
     "writer.put — метки пишутся во время обучения.",
     "Студент: основная голова на ground truth + aux-голова с KL к учителю."],
]

CODE = [
    ["def teacher_step(batch, surface):", "", 0],
    ["    ", "# 1 · вход: чужие отсеки — нули", 1],
    ["    x = cat([batch.common] +", "", 1],
    ["            [batch.feat[s] * (s == surface)", "", 1],
    ["             for s in SURFACES])", "", 1],
    ["    h = self.hiformer(x)  ", "# 2 · attention", 2],
    ["    ", "# 3 · detach() = stop-gradient", 3],
    ["    y = {t: head(h.detach() if t in SG else h)", "", 3],
    ["         for t, head in self.heads.items()}", "", 3],
    ["    M = task_mask(surface)  ", "# 4 · M[t] ∈ {0,1}", 4],
    ["    loss = sum(M[t] * ce(y[t], batch.label[t])", "", 4],
    ["               for t in y)", "", 4],
    ["    loss.backward()  ", "# Lion + AQT", 4],
    ["    writer.put(batch.id, y)  ", "# 5 · in-band метки", 5],
    ["    return loss", "", 0],
    [" ", "", 0],
    ["def student_step(batch, lam):", "", 6],
    ["    h = self.backbone(batch.x)", "", 6],
    ["    serve = ce(self.serve(h), batch.label)", "", 6],
    ["    aux = kl(soft(batch.teacher), soft(self.aux(h)))", "", 6],
    ["    return serve + lam * aux  ", "# 6 · aux", 6],
]

TITLES = {
    0: ("ПРОЛОГ", "Один учитель. Три способа смотреть.",
        "Jiang, Khani et al. · KDD 2026", 520),
    2: ("АКТ I · МИР И ПОЛОМКА", "А там, где никто ничего не выбирает?",
        None, 560),
    7: ("АКТ II · ПЕРЕСТРОЙКА УЧИТЕЛЯ", "Учителя нужно пустить в чужой мир.",
        None, 560),
    12: ("АКТ III · РЕЗУЛЬТАТЫ", "Вместе — больше суммы.", None, 560),
}


# ------------------------------------------------------------- scenes ------

def world(s, mode):
    """02 Общий план / 16 Эпилог."""
    epi = mode == "epi"
    plat = True
    tw, st, conn = epi or s >= 1, epi or s >= 2, epi or s >= 3
    sh, alt, dark = epi, epi and s >= 1, epi and s >= 2

    def rise(k, x, y, w, d, h, c, z=0.0, delay=0.0):
        return box(k, x, y, w, d, h if plat else .001, c, z=z if plat else 0,
                   op=1 if plat else 0, delay=delay if plat else 0)

    k = []
    k += box("rh", 3, 8.2, 4 if conn else .001, .6, .05, K["home"],
             op=1 if conn else 0, sw=1)
    k += box("rw", 8.2, 3, .6, 4 if conn else .001, .05, K["watch"],
             op=1 if conn else 0, sw=1)
    k += box("rsa", 12.5, 8.8 if sh else 11.999, .6, 3.2 if sh else .001, .05,
             K["shorts"], op=1 if sh else 0, sw=1)
    k += box("rsb", 10 if sh else 13.1, 8.2, 3.1 if sh else .001, .6, .05,
             K["shorts"], op=1 if sh else 0, sw=1, delay=.4)
    k.append(flow("fh", wp([[3.2, 8.5, .05], [7, 8.5, .05]]), 3, 3.6,
                  cube(K["home"], .34), op=1 if conn else 0,
                  delay=1.2 if conn else 0))
    k.append(flow("fw", wp([[8.5, 3.2, .05], [8.5, 7, .05]]), 3, 3.6,
                  cube(K["watch"], .34), op=1 if conn else 0,
                  delay=1.2 if conn else 0))
    k.append(flow("fs", wp([[12.8, 12, .05], [12.8, 8.5, .05], [10, 8.5, .05]]),
                  4, 5, cube(K["shorts"], .34), op=1 if sh else 0))
    k += rise("hp", -2, 7, 5, 5, .3, K["stone"])
    for j, y in enumerate([7.3, 8.5, 9.7, 10.9]):
        for i, x in enumerate([-1.7, .6]):
            k += rise(f"ht{j}{i}", x, y, 2.1, .9, .12, K["home"], z=.3,
                      delay=.3 + (j * 2 + i) * .06)
    k += rise("wp", 7, -2, 5, 5, .3, K["stone"])
    k += rise("ws", 7.3, -1.7, 3.1, 4.4, .15, K["watch"], z=.3, delay=.3)
    for i, y in enumerate([-1.7, -.2, 1.3]):
        k += rise(f"wt{i}", 10.8, y, .9, 1.2, .12, K["watch"], z=.3,
                  delay=.4 + i * .08)
    k += student("sh_", 3.4, 11, st) + student("sw_", 11, 3.4, st, d0=.2)
    k += tower("t", 7, 7, 3, tw)
    HP = [(0, 0, K["home"], 0), (1, 0, K["home"], 0), (0, 1, K["watch"], 0),
          (2, 0, K["watch"], 0), (2, 1, K["shorts"], 1), (0, 2, K["shorts"], 1),
          (1, 2, K["shorts"], 1), (2, 2, K["shorts"], 1)]
    for n, (i, j, c, nw) in enumerate(HP):
        v = tw and (not nw or sh)
        k += box(f"th{n}", 7.25 + i * .95, 7.25 + j * .95, .6, .6,
                 .9 if v else .001, c, z=5.15, op=1 if v else 0,
                 delay=1.4 + n * .08 if v else 0)
    k.append(flow("sgh", arc([8.5, 8.5, 6.2], [3.9, 11.5, 2], 150), 4, 3.4,
                  cube(K["signal"], .28), op=1 if conn else 0,
                  delay=1.6 if conn else 0))
    k.append(flow("sgw", arc([8.5, 8.5, 6.2], [11.5, 3.9, 2], 150), 4, 3.4,
                  cube(K["signal"], .28), op=1 if conn else 0,
                  delay=1.6 if conn else 0))
    k.append(flow("sgs", arc([8.5, 8.5, 6.2], [17.1, 13.5, 2], 180), 4, 3.8,
                  cube(K["signal"], .28), op=1 if sh else 0))
    k += rise("sp", 12, 12, 4, 4, .3, K["stone"])
    k += rise("sc", 13.4, 12.1, 1.2, 3.8, .06, K["graphite"], z=.3, delay=.3)
    for i, y in enumerate([12.5, 13.3, 14.1, 14.9, 15.6]):
        k += rise(f"spl{i}", 13.5, y, 1, .08, .9,
                  K["shorts"] if sh else K["stone"], z=.36, delay=.4 + i * .08)
    k += student("ss_", 16.6, 13, st, d0=.4, hc=K["shorts"] if sh else K["stone"])
    L1 = dict(italic=True, size=36)
    k.append(lab("lh", [-2, 12], -16, 34, "Homepage", anchor="end",
                 op=1 if plat and not alt else 0, **L1))
    k.append(lab("lh2", [-2, 12], -16, 34, "длинные видео", anchor="end",
                 op=1 if alt else 0, delay=.6, **L1))
    k.append(lab("lw", [12, 3], 34, 44, "Watch Page",
                 op=1 if plat and not alt else 0, **L1))
    k.append(lab("lw2", [12, 3], 34, 44, "клипы", op=1 if alt else 0, delay=.6,
                 **L1))
    k.append(lab("ls", [12, 16], -24, 60, "Shorts", anchor="end",
                 op=1 if plat and not alt else 0, **L1))
    k.append(lab("ls2", [12, 16], -24, 60, "посты", anchor="end",
                 op=1 if alt else 0, delay=.6, **L1))
    k.append(lab("lt", [10, 7, 6.2], 24, -30, "учитель", anchor="start",
                 op=1 if tw else 0, delay=1.2 if tw else 0, **L1))
    k.append(lab("lnc", [12, 16], -24, 104, "не подключено", anchor="end",
                 size=28, op=1 if not epi and s >= 3 else 0, delay=1))
    over = []
    if epi:
        over = [rect("nt", -STAGE_PAD, -STAGE_PAD, 1920 + 2 * STAGE_PAD,
                     1080 + 2 * STAGE_PAD, K["night"], stroke=K["night"],
                     sw=0, op=1 if dark else 0, dur=2.4),
                txt("ntt", 160, 640, "Тот же разрыв?", size=64,
                    op=1 if dark else 0, delay=1.6 if dark else 0)]
    return scene((990, 150, .86), k, over)


# the night curtain covers the whole canvas, not only the 0.82 stage
STAGE_PAD = 260


def choice(s):
    """04 Выбор и поток."""
    L = []
    L += box("pl", 0, 0, 5.4, 4.4, .3, K["stone"])
    for j, y in enumerate([.3, 1.65, 3]):
        for i, x in enumerate([.3, 2.95]):
            ch = i == 1 and j == 1
            L += box(f"t{j}{i}", x, y, 2.15, .9, .12, K["home"],
                     z=.9 if ch and s >= 1 else .3, dur=2)
    L += fig("f", [4.02, 2.1, 1.02] if s >= 2 else [2.7, 5.9, 0], dur=2.2)
    L += box("cmpL", 0, 8.5, 4.4, .9, .12, K["home"], op=1 if s >= 3 else 0)
    L.append(lab("cmpLt", [4.4, 9.4], 24, 36, "15–20 мин", size=40,
                 op=1 if s >= 3 else 0, delay=.3))
    R = []
    R += box("cv", 0, -12, 1.4, 22, .15, K["graphite"])
    R.append(flow("pl", [P(.1, -12, .15), P(.1, 10, .15)], 6, 11,
                  lambda: box("p", 0, 0, 1.2, .08, 1.1, K["shorts"], sw=1.2)))
    R += fig("f", [.7, 1.2, .15])
    R += box("cmpR", 4, 7.5, .22, .9, .12, K["shorts"], op=1 if s >= 3 else 0)
    R.append(lab("cmpRt", [4.22, 8.4], 24, 36, "≈1 мин", size=40,
                 op=1 if s >= 3 else 0, delay=.3))
    return scene((0, 0, 1), [
        at("L", 470, 360, L), at("R", 1330, 330, R),
        txt("tl", 120, 250, "Выбор.", size=64),
        txt("tr", 1020, 250, "Поток.", size=64)])


def pipes(s):
    """05 Пары задач."""
    R = [
        dict(a="клик", as_="Homepage", av=.044, ac=K["home"], b="позитив",
             bv=.435, r="×9.9", eq=0),
        dict(a="досмотр", as_="Watch Page", av=.768, ac=K["watch"],
             b="досмотр", bv=.925, r="×1.2", eq=1),
        dict(a="потребление", as_="Homepage", av=415.8, ac=K["home"],
             b="потребление", bv=19.5, r="÷21", eq=0),
        dict(a="доля досмотра", as_="Homepage", av=.692, ac=K["home"],
             b="доля досмотра", bv=.711, r="≈1.0", eq=1),
    ]
    k = [txt("h1", 700, 150, "учитель", anchor="middle", size=34,
             fill=K["stone"]),
         txt("h2", 1220, 150, "студент · Shorts", anchor="middle", size=34,
             fill=K["shorts"])]
    for i, r in enumerate(R):
        on, fin = s >= i + 1, s >= 5
        dim = (not r["eq"]) if fin else (on and s > i + 1)
        op = 0 if not on else (.35 if dim else 1)
        y = 330 + i * 200
        mx = max(r["av"], r["bv"])
        sa, sb = max(.14, 1.5 * r["av"] / mx), max(.14, 1.5 * r["bv"] / mx)

        def cb(key, sz, c, dl, cx):
            z = sz if on else .001
            return at(key, cx, 30, box(key, -sz / 2, -sz / 2, z, z, z, c,
                                       delay=dl, dur=1.4))
        g = [
            txt("an", 520, -44, r["a"], anchor="end", size=34),
            txt("as", 520, -2, r["as_"], anchor="end", size=26,
                fill=K["stone"], italic=True),
            cb("ca", sa, r["ac"], 0, 700),
            txt("av", 700, 112, str(r["av"]), anchor="middle", size=32,
                fill=r["ac"]),
            poly("ar", [(860, -20), (1060, -20)], stroke=K["paper"], sw=3,
                 closed=False, reveal=1 if on else 0, delay=.5, dur=1.0),
            poly("ah", [(1046, -30), (1064, -20), (1046, -10)],
                 fill=K["paper"], stroke=K["paper"], sw=0,
                 op=1 if on else 0, delay=1.4, dur=.3),
            txt("rt", 960, -40, r["r"], anchor="middle", size=34,
                fill=K["signal"] if r["eq"] else K["shorts"],
                op=1 if on else 0, delay=1.6),
            cb("cb", sb, K["shorts"], .9, 1220),
            txt("bv", 1220, 112, str(r["bv"]), anchor="middle", size=32,
                fill=K["shorts"]),
            txt("bn", 1400, -44, r["b"], size=34),
            txt("bs", 1400, -2, "Shorts", size=26, fill=K["stone"],
                italic=True),
            txt("eq", 1700, -20, "≈ совпало" if r["eq"] else "", size=34,
                fill=K["signal"], op=1 if fin else 0, delay=.4),
        ]
        k += group_op(at(f"row{i}", 0, y, g), op, 0, 1.0)
    return scene((0, 0, 1), k)


def bars(s):
    """06 Метки и признаки."""
    A = []
    D = [("досмотр", .925, .537, 1), ("негатив", .297, .148, 1),
         ("позитив", .435, .511, 0), ("доля досмотра", .711, .754, 0)]
    for i, (n, f, b, main) in enumerate(D):
        x, y0 = i * 2.7, -i * 2.7
        w = 1 if main else .7
        v = True if main else s >= 1
        dl = i * .25 if main else (i - 2) * .25
        A += box(f"f{i}", x, y0, w, w, f * 7 if v else .001, K["shorts"],
                 delay=dl, dur=1.8)
        A += box(f"b{i}", x + w + .15, y0, w, w, b * 7 if v else .001,
                 K["watch"], delay=dl + .15, dur=1.8)
        if main:
            A.append(lab(f"fv{i}", [x + w / 2, y0 + w / 2, f * 7], 0, -18,
                         str(f), anchor="middle", size=32, op=1 if v else 0,
                         delay=1.2))
            A.append(lab(f"bv{i}", [x + w * 1.5 + .15, y0 + w / 2, b * 7], 0,
                         -18, str(b), anchor="middle", size=32,
                         op=1 if v else 0, delay=1.35))
        A.append(lab(f"n{i}", [x + w + .07, y0 + w, 0], -10, 50, n,
                     anchor="middle", size=28, op=1 if v else 0))
    B = []
    cellsT = {7, 23, 48, 61, 84, 96}

    def plate(key, ox, oy, base, cell, lit):
        B.extend(box(key + "p", ox - .2, oy - .2, 5.8, 5.8, .2, base,
                     op=1 if s >= 2 else 0))
        for j in range(10):
            for i in range(10):
                n = j * 10 + i
                on = s >= 3 and lit(n)
                B.extend(box(f"{key}{n}", ox + i * .56, oy + j * .56, .5, .5,
                             .3 if on else .12, K["shorts"] if on else cell,
                             z=.2, op=1 if s >= 2 else 0,
                             delay=n * .012 if on else 0, dur=1.2, sw=1))
    plate("T", 0, 0, K["graphite"], CELL_T, lambda n: n in cellsT)
    plate("U", 7.5, -7.5, shade(K["stone"], .85), K["stone"],
          lambda n: (n * 37) % 100 >= 21)
    B.append(lab("tl", [2.8, 5.6], -40, 80, "признаки учителя",
                 anchor="middle", size=30, op=1 if s >= 2 else 0))
    B.append(lab("ul", [10.3, -1.9], -40, 80, "признаки студента",
                 anchor="middle", size=30, op=1 if s >= 2 else 0))
    B.append(lab("tv", [2.8, 5.6], -40, 150, "6.2%", anchor="middle", size=64,
                 fill=K["shorts"], op=1 if s >= 3 else 0, delay=1))
    B.append(lab("uv", [10.3, -1.9], -40, 150, "79.0%", anchor="middle",
                 size=64, fill=K["shorts"], op=1 if s >= 3 else 0, delay=1))
    return scene((-1920 if s >= 2 else 0, 0, 1), [
        at("A", 520, 760, A), at("B", 1920 + 470, 330, B),
        rect("lg1", 120, 190, 28, 28, K["shorts"]),
        txt("lg1t", 164, 214, "лента", size=30),
        rect("lg2", 320, 190, 28, 28, K["watch"]),
        txt("lg2t", 364, 214, "браузинг", size=30)])


def water(s, mode):
    """07 Под воду / 15 Над водой — одна композиция, рифма."""
    Bm = mode == "B"
    SL = [(-.12, -.46, "без дообучения"), (.16, .37, "выровненный"),
          (.27, .82, "выровн. + масшт.")]
    X = [0, 6, 12]
    shown = (lambda i: s >= i + 1) if Bm else (lambda i: i == 0 and s >= 2)
    num_on = (lambda i: i == min(s, 3) - 1) if Bm else shown
    water_on = Bm or s >= 1
    neg, pos, labs = [], [], []
    for i, (e, c, name) in enumerate(SL):
        for t, v, col, dx in (("e", e, K["shorts"], 0), ("c", c, K["graphite"], 1.4)):
            hh, on, x = abs(v) * 5, shown(i), X[i] + dx
            b = box(f"{t}{i}", x, 2.4, 1, 1, hh if on else .001, col,
                    z=-hh if on and v < 0 else 0, op=1 if on else 0, dur=2.2,
                    delay=.25 if t == "c" else 0)
            (neg if v < 0 else pos).extend(b)
            lbl = ("+" if v > 0 else "−") + f"{abs(v):.2f}%"
            if t == "e":
                anchor, ddx, ww = "end", -14, (x, 3.4)
            else:
                anchor, ddx, ww = "start", 14, (x + 1, 2.4)
            labs.append(lab(f"v{t}{i}", [ww[0], ww[1], 0 if v < 0 else hh],
                            ddx, 40 if v < 0 else 8, lbl, anchor=anchor,
                            size=34, op=1 if on and num_on(i) else 0,
                            delay=1.4))
        labs.append(lab(f"n{i}", [X[i] + 1.15, 9], 0, 56, name,
                        anchor="middle", size=28, op=1 if shown(i) else 0))
    wq = [P(-1.5, -.5), P(15.5, -.5), P(15.5, 9), P(-1.5, 9)]
    k = [*neg,
         poly("wat", wq, fill=K["watch"], fo=.22, stroke=K["watch"], sw=2.2,
              op=1 if water_on else 0, dur=1.6),
         # the storyboard puts it at (+24, +10), under the student's feet;
         # dropped below the corner so both read
         lab("zero", [15.5, -.5], 10, 56, "0% · контроль", size=30,
             fill=K["watch"], op=1 if water_on else 0, delay=.8),
         *pos, *student("st", 17, -3.4, True),
         flow("sg", arc([9, -15, 9], [17.5, -2.9, 2], 60), 4, 3.6,
              cube(K["signal"], .28)),
         *labs,
         lab("off", [18, -3.4, 2], 30, -10, "AUC 0.7706 → 0.7708", size=34,
             op=1 if not Bm and s == 0 else 0)]
    over = [rect("lg1", 120, 190, 28, 28, K["shorts"]),
            txt("lg1t", 164, 214, "вовлечённость", size=30),
            rect("lg2", 470, 190, 28, 28, K["graphite"]),
            txt("lg2t", 514, 214, "потребление", size=30),
            txt("side", 120, 280, "Главная +0.09% · Watch Page 0.00%",
                size=30, op=1 if Bm and s >= 4 else 0)]
    return scene((700, 380, .86), k, over)


def beam(s):
    """09 Вход с отсеками."""
    C = [(0, 5, K["graphite"]), (5.15, 2.4, K["home"]), (7.7, 2.4, K["watch"]),
         (10.25, 2.4, K["shorts"])]
    k = []
    for i in (1, 2, 3):
        cx = C[i][0] + 1.2
        k += box(f"r{i}", cx - .5, 1.8, 1, 20, .04, C[i][2], sw=1)
    for i in (1, 2, 3):
        cx = C[i][0] + 1.2
        k.append(flow(f"f{i}", [P(cx, 20, .04), P(cx, 2.2, .04)], 4, 6,
                      cube(C[i][2], .4)))
    for i, (x, w, c) in enumerate(C):
        lit = None if s == 0 else (i == 0 or i == s)
        k += box(f"c{i}", x, 0, w, 1.8, 1.1,
                 K["stone"] if s == 0 else (c if lit else K["stone"]),
                 empty=s > 0 and not lit, dur=1.2)
    k += box("tw", 0, 0, 12.65, 1.8, 4.6, K["graphite"], z=1.3)
    for i in (1, 2, 3):
        cx = C[i][0] + 1.2
        k += box(f"s{i}", cx - .45, 2.3 if s >= i else 7.5, .9, .9, .9,
                 C[i][2], z=.04, op=1 if s == i else 0, dur=1.8)
    F = [(r"x = [\,v_{\mathrm{common}}", None, K["paper"], True),
         (r"\Vert\; v_{\mathrm{Home}}", r"\Vert\; 0", K["home"], s in (0, 1)),
         (r"\Vert\; v_{\mathrm{Watch}}", r"\Vert\; 0", K["watch"], s in (0, 2)),
         (r"\Vert\; v_{\mathrm{Shorts}}\,]", r"\Vert\; 0\,]", K["shorts"],
          s in (0, 3))]
    over = []
    for i, (t, zero, c, on) in enumerate(F):
        # the storyboard indents the continuation lines by two spaces
        over.append(text(f"fm{i}", 1400 + (0 if i == 0 else 27), 480 + i * 60,
                         t if (on or zero is None) else zero, size=40,
                         fill=c if on else DIMTXT, font="tex", dur=1.0))
    over.append(txt("cap", 1400, 820,
                    "Три ленты. Равные доли." if s == 0 else "Чужие отсеки — нули.",
                    size=48))
    return scene((800, 420, 1.1), k, over)


def valve(s):
    """10 Вентиль — stop-gradient и маски."""
    kk = 1.15
    roof, hH = 5.15 * kk, 1.1
    HD = [(0, 0, K["home"], 0, 0), (1, 0, K["home"], 0, 0),
          (0, 1, K["watch"], 0, 0), (2, 0, K["watch"], 0, 0),
          (1, 1, None, 0, 0), (2, 1, K["shorts"], 1, 1),
          (0, 2, K["shorts"], 1, 1), (1, 2, K["shorts"], 1, 0),
          (2, 2, K["shorts"], 1, 0)]
    T = tower("t", 0, 0, 4, True, kk=kk)
    gr = []
    for n, (i, j, c, nw, noisy) in enumerate(HD):
        if not c:
            continue
        x, y = .25 + i * 1.3, .25 + j * 1.3
        v, lit = (not nw) or s >= 1, (not nw) or s >= 3
        T += box(f"h{n}", x, y, .8, .8, hH if v else .001,
                 c if lit else shade(K["graphite"], .8), z=roof,
                 op=1 if v else 0, delay=n * .08 if nw else 0,
                 anim="flick" if noisy and s == 4 else None)
        cx, cy = x + .4, y + .4
        g, full = s >= 4, (not noisy) or s >= 5
        gr.append(wl(f"g{n}", [cx, cy, roof + hH],
                     [cx, cy, .05 if full else roof], c=K["paper"], w=3,
                     dash=(10, 8), anim="gdash", op=1 if g else 0, dur=1.2))
        if noisy:
            ring = [P(cx + .62 * math.cos(t), cy + .62 * math.sin(t), roof + .02)
                    for t in [q / 28 * 2 * math.pi for q in range(29)]]
            vo = 1 if s == 4 else 0
            gr += [ln(f"vr{n}", ring, w=4, op=vo, dur=1),
                   wl(f"vs{n}", [cx + .62, cy, roof], [cx + .62, cy, roof + .7],
                      w=4, op=vo, dur=1),
                   wl(f"vh{n}", [cx + .32, cy - .3, roof + .7],
                      [cx + .92, cy + .3, roof + .7], w=5, op=vo, dur=1)]
    T += gr
    T += box("hc", 1.6, 4.4, .8, .8, .8, K["home"], z=7.4 if s >= 2 else 0,
             op=1 if s == 2 else 0, dur=2.4)
    T += box("sc", 1.6, 4.4, .8, .8, .8, K["shorts"], z=7.4 if s >= 3 else 0,
             op=1 if s == 3 else 0, dur=2.4)
    grp = with_anim(T, "tilt" if s == 5 else None, tag="tg")
    over = [
        txt("a", 1260, 330, "4 головы Shorts", size=34, op=1 if s >= 1 else 0),
        txt("a2", 1260, 380, "негатив · позитив · досмотр · доля", size=28,
            op=1 if s >= 1 else 0),
        txt("b", 1260, 500,
            "Кубик Shorts — зажигает." if s >= 3 else "Кубик Главной — темно.",
            size=44, op=1 if s in (2, 3) else 0),
        text("f1", 1260, 520, r"\hat{y} = \varphi(\mathrm{sg}(h(x)))",
             size=44 * 1.08, font="tex", op=1 if s >= 4 else 0),
        txt("f1n", 1260, 568, "для шумных задач", size=28,
            op=1 if s >= 4 else 0),
        text("f2", 1260, 680, r"\mathcal{L} = \sum_i \sum_t M_{it}\cdot \ell_t",
             size=44 * 1.08, font="tex", op=1 if s >= 4 else 0, delay=.3),
        txt("f2n", 1260, 728, "M = 0 вне Shorts", size=28,
            op=1 if s >= 4 else 0, delay=.3),
    ]
    return scene((820, 760, 1.25), [grp], over)


def attn(s):
    """11 Проводка — ResNet против attention, память ускорителя."""
    A = []
    ctx = "home" if s == 0 else ("shorts" if s <= 2 else "home")
    att = s >= 2
    W = ([4] * 6 if not att else
         [12, 12, 5, 5, 1.5, 1.5] if ctx == "shorts" else
         [1.5, 1.5, 5, 5, 12, 12])
    for i in range(6):
        A += box(f"f{i}", i * 2.1, 0, 1.2, 1.2, 1.2, K["stone"])
    for i in range(6):
        A.append(wl(f"l{i}", [3.4 + i * 1.15, .6, 6], [i * 2.1 + .6, .6, 1.2],
                    w=W[i], dur=1.8))
    A += box("hub", 3, -.2, 6.5, 1.6, .6, K["graphite"], z=6)
    A += box("in", 5.8, .2, .8, .8, .8,
             K["shorts"] if ctx == "shorts" else K["home"], z=6.6, dur=1.2)
    A.append(lab("inl", [6.6, .2, 7.4], 28, -8,
                 "вход: Shorts" if ctx == "shorts" else "вход: Главная",
                 size=30))
    A.append(lab("hl", [9.5, -.2, 6.3], 30, 10,
                 "Attention · слушает вход" if att else "ResNet · жёсткая проводка",
                 size=30))
    for i, (t, x) in enumerate([("свайпы", 1.65), ("общие", 5.85),
                                ("длинные", 10.05)]):
        A.append(lab(f"g{i}", [x, 1.2], -10, 56, t, anchor="middle", size=30))
    B = []
    opt, mat = (1.1, .8) if s >= 5 else (2.2, 1.6)
    B += box("o", .1, .1, 5.8, 5.8, opt, K["stone"], dur=2)
    B += box("m", .1, .1, 5.8, 5.8, mat, K["graphite"], z=opt, dur=2)
    bc = [K["home"], K["watch"], K["shorts"]]
    for j in range(2):
        for i in range(3):
            n = j * 3 + i
            B += box(f"b{n}", .5 + i * 1.8, .6 + j * 2.6, 1.1, 1.1, 1.1,
                     bc[(i + j) % 3], z=opt + mat if s >= 5 else 5.6,
                     op=1 if s >= 5 else 0,
                     delay=1 + n * .12 if s >= 5 else 0, dur=1.6)
    B += box("ct", 0, 0, 6, 6, 5.2, K["stone"], empty=True)
    B.append(lab("lo", [6, 0, opt / 2], 30, 10, "состояние оптимизатора",
                 size=28))
    B.append(lab("lm", [6, 0, opt + mat / 2], 30, 10,
                 "Lion + AQT" if s >= 5 else "матрицы", size=28))
    B.append(lab("lb", [6, 0, opt + mat + 1.6], 30, 10, "батч ↑", size=28,
                 op=1 if s >= 5 else 0, delay=1.4))
    cxk, cyk = 900, -60
    B.append(poly("ck", circle_pts(cxk, cyk, 80, 96), stroke=K["paper"], sw=3))
    for q in range(12):
        a = q / 12 * 2 * math.pi
        B.append(poly(f"tk{q}", [(cxk + 68 * math.sin(a), cyk - 68 * math.cos(a)),
                                 (cxk + 78 * math.sin(a), cyk - 78 * math.cos(a))],
                      stroke=K["paper"], sw=2, closed=False, cap="butt"))
    B.append(poly("hd", [(cxk, cyk), (cxk + 52, cyk - 30)], stroke=K["paper"],
                  sw=4, closed=False))
    B.append(txt("ckl", cxk, cyk + 130, "время шага", anchor="middle",
                 size=28))
    return scene((-1920 if s >= 4 else 0, 0, 1), [
        at("A", 560, 620, A), at("B", 1920 + 560, 640, B)])


def infra(s):
    """12 Дистилляция — in-band метки и aux-голова."""
    A = []
    nw = s >= 1
    crX = 5.2 if nw else 13
    A += box("tr", 0, 1, crX + .8 if nw else 13.8, .6, .04, RIBBON, dur=2)
    A.append(flow("old", wp([[2.6, 1.3, .1], [13, 1.3, .1]]), 5, 6,
                  cube(K["stone"], .34), op=0 if nw else 1))
    A += tower("t", 0, 0, 2.4, True, kk=.7)
    A += box("lb", 6.4, 0, 2.4, 2.4, .001 if nw else 2.6, K["stone"],
             op=0 if nw else 1, dur=2)
    A += box("cr", crX, .4, 1.6, 1.6, 1.2, K["stone"], dur=2.2)
    A.append(flow("new", arc([1.2, 1.2, 3.8], [crX + .8, 1.2, 1.3], 110), 5, 3,
                  cube(K["signal"], .3), op=1 if nw else 0,
                  delay=2 if nw else 0))
    A.append(lab("l1", [0, 0, 3.8], -10, -30, "обучение", size=30))
    A.append(lab("l2", [6.4, 0, 2.6], 0, -30, "разметка", size=30,
                 op=0 if nw else 1))
    A.append(lab("l3", [crX, .4, 1.2], 20, -30, "метки", size=30, dur=2))
    A.append(lab("l4", [crX + 1.6, 1.6], 30, 80, "−10 ч", size=72,
                 fill=K["signal"], op=1 if nw else 0, delay=2.2))
    B = []
    split, roof = s >= 3, 5.15 * .8
    B += tower("st", 0, 0, 3, True, kk=.8, c=K["stone"])
    B += box("gt", .5, 7, 1, 1, 1.4, K["paper"])
    B += box("te", 7, .5, 1.2, 1.2, 5, K["graphite"])
    B.append(lab("gtl", [.5, 8], -20, 56, "ground truth", anchor="end",
                 size=30))
    B.append(lab("tel", [8.2, 1.7], 20, 56, "учитель", size=30))
    B.append(wl("ad", [2.2, 1.4, roof], [2.2, 1.4, .1], c=K["paper"], w=3,
                dash=(10, 8), anim="gdash", op=1 if split else 0))
    heads = (box("h1", .4 if split else 1, 1.1 if split else 1,
                 .9 if split else 1, .9 if split else 1, 1, K["stone"], z=roof,
                 dur=1.8)
             + box("h2", 1.8 if split else 1, 1.1 if split else 1,
                   .9 if split else 1, .9 if split else 1, 1,
                   K["signal"] if split else K["stone"], z=roof,
                   op=1 if split else 0, dur=1.8))
    B += with_anim(heads, "jit" if s == 2 else None)
    B.append(wl("r1", [1, 7.5, 1.4],
                [.85, 1.55, roof + 1] if split else [1.5, 1.5, roof + 1], w=3,
                dur=1.8))
    B.append(wl("r2", [7.6, 1.1, 5],
                [2.25, 1.55, roof + 1] if split else [1.5, 1.5, roof + 1],
                c=K["signal"], w=3, dur=1.8))
    B.append(lab("hl1", [.4, 2, roof + 1], -20, -20,
                 "рабочая" if split else "одна голова", anchor="end", size=28))
    B.append(lab("hl2", [2.7, 1.1, roof + 1], 20, -30, "aux", size=28,
                 op=1 if split else 0))
    # storyboard y = 820 lays it over «ground truth»; one line lower instead
    fm = text("fm", 1920 + 120, 905,
              r"\mathcal{L} = \sum \mathrm{CE}\big(y,\, \sigma(z^{s})\big)"
              r" + \lambda \sum \mathrm{KL}\big(\sigma(z^{T}) \,\Vert\,"
              r" \sigma(z^{s}_{\mathrm{aux}})\big)",
              size=34 * 1.08, font="tex", op=1 if split else 0, delay=1)
    return scene((-1920 if s >= 2 else 0, 0, 1), [
        at("A", 420, 560, A), at("B", 1920 + 860, 560, B), fm])


def grid2(s):
    """14 Два на два — абляция."""
    U = .00124
    C = [(1, 1, .0062, 3), (1, 0, .0015, 2), (0, 1, .0002, 1), (0, 0, 0, 0)]
    GX = lambda i: (1 - i) * 3.4
    k = []
    for i, j, _, _ in C:
        k += box(f"p{i}{j}", GX(i), GX(j), 2.8, 2.8, .15, K["stone"])
    for i, j, v, st in C:
        on = s >= st
        x, y = GX(i) + .35, GX(j) + .75
        hh = max(v / U, .06)
        k += box(f"c{i}{j}", x, y, 1.3, 1.3, hh if on else .001, K["home"],
                 z=.15, op=1 if on or st == 0 else 0, dur=2.2)
        if st:
            k.append(lab(f"v{i}{j}", [x + .65, y + .65, .15 + hh], 0, -22,
                         f"+{v:.4f}", anchor="middle", size=34,
                         op=1 if on else 0, delay=1.6))
        if i == 1 and j == 1:
            k += box("gh", x + 1.45, y, .85, 1.3,
                     .0017 / U if s >= 4 else .001, K["stone"], z=.15,
                     empty=True, op=1 if s >= 4 else 0, dur=2)
    k += [lab("ax1", [4.8, 6.5], -24, 40, "старая архитектура", anchor="end",
              size=28),
          lab("ax2", [1.4, 6.5], -24, 40, "новая архитектура", anchor="end",
              size=28),
          lab("ay1", [6.5, 4.8], 24, 40, "без данных Shorts", size=28),
          lab("ay2", [6.5, 1.4], 24, 40, "+ данные Shorts", size=28)]
    return scene((960, 560, 1.1), k, [
        txt("ghl", 1300, 360, "пунктир = сумма по отдельности, +0.0017",
            size=30, op=1 if s >= 4 else 0, delay=1.4)])


def code_scene(s):
    """17 Код — мини-башня справа от листинга."""
    hl = lambda g: s == 0 or s in g
    k = []
    k += tower("t", 0, 0, 2.4, True, kk=.9,
               cols=[K["graphite"] if hl([1] if i == 0 else [2]) else DIM
                     for i in range(6)])
    roof = 5.15 * .9
    HD = [(0, 0, K["home"], 0), (1, 0, K["watch"], 0), (0, 1, K["shorts"], 1),
          (1, 1, K["shorts"], 1)]
    for n, (i, j, c, sh) in enumerate(HD):
        lit = sh if s == 4 else hl([3, 5])
        k += box(f"h{n}", .3 + i * 1.1, .3 + j * 1.1, .7, .7, .9,
                 c if lit else DIM, z=roof)
    ring = [P(1.75 + .55 * math.cos(t), 1.75 + .55 * math.sin(t), roof + .02)
            for t in [q / 28 * 2 * math.pi for q in range(29)]]
    k.append(ln("vr", ring, w=4, op=1 if s == 3 else 0))
    k += box("cr", 5.2, -1.4, 1.4, 1.4, 1, K["stone"], op=1 if s >= 5 else 0)
    k.append(flow("sg", arc([1.2, 1.2, 5.6], [5.9, -.7, 1.1], 90), 4, 2.8,
                  cube(K["signal"], .28), op=1 if s == 5 else 0))
    k += student("su", 5.4, 3.2, s >= 6, hc=K["stone"])
    k += box("ax", 6.5, 3.5, .4, .4, .45 if s >= 6 else .001, K["signal"],
             z=1.5, op=1 if s >= 6 else 0, delay=.6)
    k.append(flow("sg2", arc([5.9, -.7, 1.1], [6.7, 3.7, 2], 70), 3, 2.4,
                  cube(K["signal"], .24), op=1 if s >= 6 else 0, delay=1))
    return scene((1500, 560, 1), k)


# ------------------------------------------------------------- chrome ------

# JetBrains Mono advance is exactly 0.6 em
MONO_ADV = 0.6


def code_rows(cs):
    """The listing of frame 17: 26 px JetBrains Mono, 35 px rows from y=150,
    active group on a 14 % BLUE_C band, the rest dimmed to #555."""
    out = []
    for i, (code, comment, g) in enumerate(CODE):
        act = cs > 0 and g == cs
        dim = cs > 0 and not act
        top = 150 + i * 35
        out.append(rect(f"cb{i}", 104, top, 1160, 35, CODE_HL, stroke=CODE_HL,
                        sw=0, fo=CODE_HL_A, op=1 if act else 0, dur=.8))
        base = top + 26.9
        body = code.rstrip()
        lead = len(code) - len(code.lstrip(" "))
        if body.strip():
            out.append(text(f"cc{i}", 120 + lead * 26 * MONO_ADV, base,
                            body.strip(), size=26,
                            fill=DIMTXT if dim else K["paper"], font="mono",
                            dur=.8))
        if comment:
            out.append(text(f"cm{i}", 120 + len(code) * 26 * MONO_ADV, base,
                            comment, size=26,
                            fill=DIMTXT if dim else K["signal"], font="mono",
                            dur=.8))
    return out


def chrome(i, v, wrap):
    """Step counter top right, narration line bottom left — HTML over the SVG.

    `wrap(text, css_px, width_px)` breaks the narration into lines the way the
    1544 px flex item would; the block is bottom-aligned at 36 px.
    """
    m = MAX[i]
    out = []
    # a black band under the narration: the storyboard lets scenes that bleed
    # off the bottom (09's ribbons) run under the text; here they fade out
    for j in range(8):
        out.append(rect(f"scr{j}", 0, 950 + j * 5, 1920, 5, K["ink"],
                        stroke=K["ink"], sw=0, fo=(j + 1) / 9, dur=.5))
    out.append(rect("scr8", 0, 990, 1920, 90, K["ink"], stroke=K["ink"], sw=0,
                    dur=.5))
    if m:
        out.append(text("stp", 1800, 72, f"ШАГ {v + 1} / {m + 1}", size=30,
                        fill=K["graphite"], anchor="end", dur=.5))
    idx = f"{i + 1:02d}" + (f"·{v + 1}" if m else "")
    lines = wrap(NAR[i][v], 28, 1544)
    lh = 28 * 1.35
    first = 1033 - lh * (len(lines) - 1)
    out.append(text("nidx", 120, first, idx, size=24, fill=YELLOW, dur=.5))
    for j, ln_ in enumerate(lines):
        out.append(text(f"nar{j}", 256, first + j * lh, ln_, size=28,
                        fill=NARR, dur=.5))
    return out


def title_card(i):
    kicker, title, sub, top = TITLES[i]
    out = [text("tk", 160, top + 29, kicker, size=30, fill=YELLOW,
                spacing=0.08 * 30, dur=1.4),
           text("tt", 160, top + 133, title, size=72, fill=K["paper"],
                dur=1.4, delay=.15)]
    if sub:
        out.append(text("ts", 160, top + 215, sub, size=30, fill=K["graphite"],
                        italic=True, dur=1.4, delay=.3))
    return out


# ------------------------------------------------------------- dispatch ----

SCENES = {
    1: lambda v: world(v, "pro"), 3: choice, 4: pipes, 5: bars,
    6: lambda v: water(v, "A"), 8: beam, 9: valve, 10: attn, 11: infra,
    13: grid2, 14: lambda v: water(v, "B"), 15: lambda v: world(v, "epi"),
    16: code_scene,
}


def build(i, v, wrap):
    """Everything on screen at frame `i` (0-based), click `v`.

    Returns {"cam", "world", "over", "screen"}: world prims sit under the
    camera, over prims under the fixed 0.82 stage, screen prims are HTML
    chrome in raw canvas px.
    """
    if i in SCENES:
        sc = SCENES[i](v)
    else:
        sc = scene((0, 0, 1), [], [])
    scr = []
    if i in TITLES:
        scr += title_card(i)
    if i == 16:
        scr += code_rows(v)
    scr += chrome(i, v, wrap)
    sc["screen"] = scr
    return sc
