#!/usr/bin/env python3
"""Assemble a deck's PPTX from the same render as the film.

One slide per storyboard frame, in storyboard order, each showing the frame's
final state — the last frame of its Manim section — full bleed at 1920x1080.
`data-speaker-notes` goes into the speaker notes verbatim, duration included.

    python -m deckkit.build_pptx paper_1_minimalism
    python -m deckkit.build_pptx paper_1_minimalism --quality l
"""

import argparse
import json
import pathlib
import subprocess

from pptx import Presentation
from pptx.util import Inches

from deckkit.deck import Deck

QUALITY_DIR = {"l": "480p15", "m": "720p30", "h": "1080p60", "k": "2160p60"}

# 1920x1080 px at 96 dpi
SLIDE_W = Inches(20)
SLIDE_H = Inches(11.25)


def last_frame(video, dest):
    """Grab the final rendered frame of a section — the settled state."""
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-sseof", "-1", "-i", str(video),
         "-update", "1", "-q:v", "1", str(dest)], check=True)
    if not dest.exists() or dest.stat().st_size == 0:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(video),
             "-vf", "select='eq(n,0)'", "-vsync", "0", "-q:v", "1",
             str(dest)], check=True)
    return dest


def collect(deck, quality):
    """screen -> still, walking each part's section manifest."""
    stills = {}
    deck.stills.mkdir(parents=True, exist_ok=True)
    for p in deck.parts:
        sec_dir = (deck.media / "videos" / f"part{p}" / QUALITY_DIR[quality]
                   / "sections")
        manifest = sec_dir / f"part{p}.json"
        if not manifest.exists():
            raise SystemExit(f"missing sections for part {p} — run "
                             f"build_video first ({manifest})")
        for sec in json.loads(manifest.read_text(encoding="utf-8")):
            dest = deck.stills / f"{sec['name'].replace('.', '_')}.png"
            stills[sec["name"]] = last_frame(sec_dir / sec["video"], dest)
    return stills


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("--quality", default="h", choices=list(QUALITY_DIR))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    deck = Deck(a.deck)
    deck.out.mkdir(parents=True, exist_ok=True)
    meta = {f["screen"]: f for f in deck.frames()}
    order = [f["screen"] for f in deck.frames()]
    stills = collect(deck, a.quality)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank = prs.slide_layouts[6]

    made, missing = 0, []
    for screen in order:
        if screen in deck.skip:
            continue
        if screen not in stills:
            missing.append(screen)
            continue
        slide = prs.slides.add_slide(blank)
        slide.shapes.add_picture(str(stills[screen]), 0, 0,
                                 width=SLIDE_W, height=SLIDE_H)
        notes = meta[screen]["notes"] or ""
        label = meta[screen]["label"]
        slide.notes_slide.notes_text_frame.text = (
            f"{label}\n\n{notes}" if notes else label)
        made += 1

    dest = pathlib.Path(a.out) if a.out else deck.out / f"{deck.name}-slides.pptx"
    prs.save(str(dest))
    print(f"{dest}  —  {made} slides")
    if missing:
        print("missing sections:", ", ".join(missing))


if __name__ == "__main__":
    main()
