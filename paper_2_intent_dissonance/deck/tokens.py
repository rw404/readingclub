"""Design tokens of the 3b1b storyboard.

Colours are the storyboard's `K` table — Manim's own constants, as the chat
settled on: главная GOLD-ish `#F0AC5F`, Watch Page BLUE_C, Shorts RED_C,
знание учителя TEAL (`signal`), нейтральное GREY.  Plus the few literals the
storyboard uses for chrome, the code listing and the little figures.
"""

K = {
    "paper": "#FFFFFF",
    "ink": "#000000",
    "night": "#000000",
    "graphite": "#888888",
    "stone": "#BBBBBB",
    "home": "#F0AC5F",
    "watch": "#58C4DD",
    "shorts": "#FC6255",
    "signal": "#5CD0B3",
}

BG = "#000000"
YELLOW = "#F4D345"       # номер шага, надзаголовок интертитра
NARR = "#DDDDDD"         # строка разбора
DIMTXT = "#555555"       # погашенные строки кода и формулы
DIM = "#333333"          # погашенные блоки мини-башни на слайде кода
CODE_HL = "#58C4DD"      # подсветка строк кода (с прозрачностью 0.14)
CODE_HL_A = 0.14
FIG_BODY, FIG_TOP, FIG_HEAD = "#2A2A2A", "#444444", "#333333"
CELL_T = "#5B5B61"       # клетки признаков учителя
RIBBON = "#666666"       # трасса разметки

FONT_SERIF = "CMU Serif"         # Computer Modern, как в LaTeX
FONT_MONO = "JetBrains Mono"

# CSS px -> Manim font_size, measured on CMU Serif (same constant as deckkit)
FONT_K = 0.53318
# MathTex at the same font_size is 0.747 the size of Text: measured on "H"
TEX_K = FONT_K / 0.7473

# the storyboard wraps every scene in translate(173 72) scale(0.82)
STAGE_X, STAGE_Y, STAGE_S = 173.0, 72.0, 0.82

UNIT_PX = 135.0
CANVAS_W, CANVAS_H = 1920, 1080

PALETTE = {"bg": BG, **K, "yellow": YELLOW, "narr": NARR, "dimtxt": DIMTXT,
           "dim": DIM, "fig_body": FIG_BODY, "fig_top": FIG_TOP,
           "fig_head": FIG_HEAD, "cell_t": CELL_T, "ribbon": RIBBON}
