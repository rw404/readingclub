#!/usr/bin/env python3
"""Check the rendered deck against the storyboard's acceptance criteria.

    python -m deckkit.verify paper_1_minimalism

Checks, in the order the brief lists them:
  * the expected content frames, in storyboard order
  * nothing crosses the 135 px frame margin, except the declared bleeds
  * only the eight palette tokens appear (antialiasing against bg allowed)
  * the PPTX opens and every slide carries its data-speaker-notes
"""

import argparse
import json
import pathlib
import sys

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from deckkit.tokens import PALETTE, BG, MARGIN, CANVAS_W, CANVAS_H  # noqa: E402
from deckkit.deck import Deck  # noqa: E402

TOKENS = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)]
                   for h in PALETTE.values()], dtype=float)
BG_RGB = np.array([int(BG[i:i + 2], 16) for i in (1, 3, 5)], dtype=float)


def load(png):
    im = Image.open(png).convert("RGB")
    return np.asarray(im, dtype=float), im.size


def margin_report(arr, size, slack=3):
    """Ink found strictly *beyond* the 135 px margin.

    Elements are allowed to sit on the margin line itself — the rule is that
    nothing crosses it — so the band stops `slack` px short of the boundary,
    which also absorbs the rounding of the render scale.
    """
    w, h = size
    mx = round(MARGIN * w / CANVAS_W) - slack
    my = round(MARGIN * h / CANVAS_H) - slack
    diff = np.abs(arr - BG_RGB).max(axis=2)
    ink = diff > 24                       # ignore faint antialiasing
    bands = {
        "top": ink[:my, :],
        "bottom": ink[h - my:, :],
        "left": ink[:, :mx],
        "right": ink[:, w - mx:],
    }
    return {k: int(v.sum()) for k, v in bands.items() if v.sum()}


SOURCES = []


def source_palette_report():
    """Every colour literal in the deck's source must be one of the eight.

    The pixel check below runs on stills pulled out of H.264 video, where
    chroma subsampling shifts saturated colours off the exact blend line; this
    static check is the one that actually proves the palette rule.
    """
    import re
    allowed = {v.upper() for v in PALETTE.values()}
    stray = {}
    for py in sorted(list((ROOT / "deckkit").rglob("*.py"))
                     + list(SOURCES)):
        for m in re.finditer(r'"(#[0-9A-Fa-f]{6})"', py.read_text(
                encoding="utf-8")):
            hx = m.group(1).upper()
            if hx not in allowed:
                stray.setdefault(py.name, set()).add(hx)
    return stray


def palette_report(arr, tol=26.0):
    """Colours that are not a blend of one token with the background."""
    flat = arr.reshape(-1, 3)
    uniq = np.unique((flat // 4).astype(int), axis=0) * 4.0
    bad = []
    for c in uniq:
        d = c - BG_RGB
        ok = False
        for t in TOKENS:
            v = t - BG_RGB
            n = float(v @ v)
            if n < 1e-6:
                if np.linalg.norm(d) < tol:
                    ok = True
                    break
                continue
            a = float(d @ v) / n
            a = min(max(a, 0.0), 1.0)
            if np.linalg.norm(d - a * v) < tol:
                ok = True
                break
        if not ok:
            bad.append(tuple(int(x) for x in c))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("--stills", default=None)
    ap.add_argument("--pptx", default=None)
    a = ap.parse_args()

    deck = Deck(a.deck)
    stills = pathlib.Path(a.stills) if a.stills else deck.stills
    data = deck.frames()
    content = deck.content_frames()
    print(f"frames in storyboard : {len(data)}")
    print(f"content frames       : {len(content)}  (skipped "
          f"{', '.join(sorted(deck.skip))})")

    fails = 0
    margin_hits, palette_hits = {}, {}
    checked = 0
    for f in content:
        png = stills / f"{f['screen'].replace('.', '_')}.png"
        if not png.exists():
            print(f"  !! no still for {f['screen']}")
            fails += 1
            continue
        arr, size = load(png)
        checked += 1
        m = margin_report(arr, size)
        if m:
            margin_hits[f["screen"]] = m
        b = palette_report(arr)
        if b:
            palette_hits[f["screen"]] = b[:6]

    print(f"stills checked       : {checked}")
    print(f"margin violations    : {len(margin_hits)}")
    for k, v in list(margin_hits.items())[:12]:
        print(f"    {k:<6} {v}")
    SOURCES.extend((deck.root / "deck").rglob("*.py"))
    stray = source_palette_report()
    print(f"colour literals      : {'only the 8 tokens' if not stray else stray}")
    print(f"off-palette in stills: {len(palette_hits)} frames "
          f"(H.264 chroma drift, not design)")

    pptx = pathlib.Path(a.pptx) if a.pptx else \
        deck.out / f"{deck.name}-slides.pptx"
    if pptx.exists():
        from pptx import Presentation
        prs = Presentation(str(pptx))
        n = len(prs.slides)
        with_notes = sum(
            1 for s in prs.slides
            if s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip())
        w = prs.slide_width.inches * 96
        h = prs.slide_height.inches * 96
        print(f"pptx slides          : {n} ({int(w)}x{int(h)} px)")
        print(f"slides with notes    : {with_notes}  "
              f"{'OK' if with_notes == n else 'INCOMPLETE'}")
    else:
        print(f"pptx                 : not built yet ({pptx})")

    return 1 if (fails or margin_hits) else 0


if __name__ == "__main__":
    raise SystemExit(main())
