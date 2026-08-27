"""Design tokens for the DHE deck.

Everything here is transcribed from the three specification frames of
``DHE Storyboard v2.dc.html`` (S1 Токены, S2 Компоненты, S3 Анатомия кадра).
No colour, size or stroke width outside this module is allowed.
"""

import numpy as np

# ---------------------------------------------------------------- canvas ----
# Storyboard canvas is 1920x1080. Manim at 16:9 gives frame_width 14.222 and
# frame_height 8, so the scale is exact: 135 px = 1 unit, grid step 45 px = 1/3.
CANVAS_W = 1920
CANVAS_H = 1080
UNIT_PX = 135.0
GRID = 45           # layout grid step, px
MARGIN = 135        # frame margin, px — nothing crosses it but deliberate bleeds


def px(v):
    """Storyboard pixels -> Manim units."""
    return v / UNIT_PX


def pos(x_px, y_px):
    """Storyboard pixel coordinate (origin top-left) -> Manim point."""
    return np.array([(x_px - CANVAS_W / 2) / UNIT_PX,
                     (CANVAS_H / 2 - y_px) / UNIT_PX,
                     0.0])


# ---------------------------------------------------------------- palette ---
# Eight tokens, nothing else. Frame S1.
BG = "#0B0D12"      # фон, почти чёрный
INK = "#E8EAF0"     # основной штрих и текст
MUTED = "#5A6072"   # второстепенное
DIM = "#2A2F3D"     # сетка, неактивное, «призраки»
ID = "#F2994A"      # кодирование, идентификатор, хеши
DEC = "#56CCF2"     # декодер
ATTR = "#6FCF97"    # побочные признаки, положительный результат
ALERT = "#EB5757"   # нарушение, коллизия, провал критерия

PALETTE = {"bg": BG, "ink": INK, "muted": MUTED, "dim": DIM,
           "id": ID, "dec": DEC, "attr": ATTR, "alert": ALERT}


# ------------------------------------------------------------ typography ----
FONT_SANS = "Inter"
FONT_MONO = "JetBrains Mono"

# Manim's Text(font_size=...) is not CSS px. Measured against the real font
# metrics (see build/calibrate.py): the ratio is font-independent.
FONT_K = 0.53318


def fs(css_px):
    """CSS pixel em size -> Manim font_size."""
    return css_px * FONT_K


# Three sizes only, nothing below 28 px — frames are watched on a phone.
SIZE_DISPLAY = 64
SIZE_TITLE = 40
SIZE_MONO = 28

W_TITLE = 500       # Inter medium — frame title
W_DISPLAY = 600     # Inter semibold — display numerals
W_MONO = 400


# ---------------------------------------------------------------- strokes ---
# Only three widths. Flat fills. No shadows, blurs, gradients, textures, glow.
S_THIN = 2
S_MID = 4
S_THICK = 8


# ------------------------------------------------------------ frame layout --
# The caption lives at the same point on every frame: top-left of the working
# area. Title baseline block starts at the margin; the mono subline sits 18 px
# below it (CSS `margin:18px 0 0` with 40px/1.2 and 28px/1.3 line boxes).
CAP_X = MARGIN
CAP_Y = MARGIN
CAP_GAP = 18

# Working area below the caption block, where the diagram is centred.
# Caption line boxes: 40*1.2 + 18 + 28*1.3 = 48 + 18 + 36.4 = 102.4 px.
CAP_BLOCK_H = SIZE_TITLE * 1.2 + CAP_GAP + SIZE_MONO * 1.3

# Most sections are `flex-direction:column; gap:36px`; a few use gap 45.
BODY_GAP = 36
BODY_TOP = MARGIN + CAP_BLOCK_H + BODY_GAP        # 273.4
BODY_BOTTOM = CANVAS_H - MARGIN                   # 945
BODY_LEFT = MARGIN
BODY_RIGHT = CANVAS_W - MARGIN
BODY_CX = CANVAS_W / 2                            # 960
BODY_CY = (BODY_TOP + BODY_BOTTOM) / 2            # 609.2
BODY_W = BODY_RIGHT - BODY_LEFT                   # 1650
BODY_H = BODY_BOTTOM - BODY_TOP                   # 671.6
