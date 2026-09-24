#!/usr/bin/env python3
"""Convert a rendered deck into a PPTX with `manim-slides`.

The slides are not pictures of the frames — each slide carries the frame's own
Manim clip, the very one the film is cut from, and plays it by itself when the
slide comes up.  So the deck animates exactly like the video, because it *is*
the video, cut at the frame boundaries.

Nothing is re-rendered here: `build_video.py` already wrote the per-slide clips
and `slides/<Scene>.json`.  This only drops the closing fade of each part (a
slide of its own in the render, but not a frame of the talk) and hands the rest
to `manim-slides convert`.

    python -m deckkit.build_pptx paper_1_minimalism
    python -m deckkit.build_pptx paper_1_minimalism --quality l
"""

import argparse
import json
import pathlib
import shutil
import subprocess
import sys

from deckkit.deck import Deck

BIN = pathlib.Path(sys.executable).parent
OUTRO = "_outro"

# The converter defaults to 1280x720; the deck is authored at 1920x1080.
SLIDE_W, SLIDE_H = 1920, 1080


def screen_of(slide):
    """The storyboard frame a slide belongs to, read back from its notes."""
    notes = (slide.get("notes") or "").strip()
    if not notes or notes == OUTRO:
        return None
    return notes.split(None, 1)[0]


def prune(deck, dest_dir):
    """Copy the slide manifests, dropping each part's closing fade.

    Returns the ordered list of (scene, screen) actually kept.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    kept = []
    for p in deck.parts:
        scene = deck.scene(p)
        src = deck.root / "slides" / f"{scene}.json"
        if not src.exists():
            raise SystemExit(f"no slide index for {scene} — run build_video "
                             f"first ({src})")
        cfg = json.loads(src.read_text(encoding="utf-8"))
        slides = []
        for sl in cfg["slides"]:
            screen = screen_of(sl)
            if screen is None:            # the outro fade
                continue
            if screen in deck.skip:
                continue
            # absolute: the converter resolves clip paths against the folder
            # holding the manifest, and this one is not the render's own
            for key in ("file", "rev_file"):
                if sl.get(key):
                    sl[key] = str((deck.root / sl[key]).resolve())
            slides.append(sl)
            kept.append((scene, screen, sl))
        cfg["slides"] = slides
        (dest_dir / f"{scene}.json").write_text(
            json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return kept


def clip_seconds(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)]).decode().strip()
    return float(out)


def auto_advance(dest, kept):
    """Carry `auto_next` over to PowerPoint.

    manim-slides honours `next_slide(auto_next=True)` only in its own player
    and in HTML.  A deck that follows each click with a looping slide needs it
    in PPTX too, or every click would have to be pressed twice: such slides
    get a timed transition that fires when their clip ends.
    """
    if not any(sl.get("auto_next") for _, _, sl in kept):
        return 0
    from lxml import etree
    from pptx import Presentation
    ns = "http://schemas.openxmlformats.org/presentationml/2006/main"
    prs = Presentation(str(dest))
    n = 0
    for slide, (_, _, sl) in zip(prs.slides, kept):
        if not sl.get("auto_next"):
            continue
        el = slide._element
        tr = etree.SubElement(el, f"{{{ns}}}transition")
        tr.set("advTm", str(int(round(clip_seconds(sl["file"]) * 1000))))
        timing = el.find(f"{{{ns}}}timing")
        if timing is not None:          # schema order: transition, timing
            timing.addprevious(tr)
        n += 1
    prs.save(str(dest))
    return n


def stills(deck, kept):
    """One PNG per slide, its settled last frame — what `verify` inspects.

    A looping slide shares its screen with the click before it; the still of
    the click (its settled end) is kept, not a moment from inside the loop.
    """
    if deck.stills.exists():
        shutil.rmtree(deck.stills)
    deck.stills.mkdir(parents=True, exist_ok=True)
    for _, screen, sl in kept:
        clip = pathlib.Path(sl["file"])
        dest = deck.stills / f"{screen.replace('.', '_')}.png"
        if dest.exists():
            continue
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-sseof", "-1", "-i", str(clip),
             "-update", "1", "-q:v", "1", str(dest)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep-stills", action="store_true", default=True)
    a = ap.parse_args()

    deck = Deck(a.deck)
    deck.out.mkdir(parents=True, exist_ok=True)
    work = deck.root / "build" / "slides-pptx"
    if work.exists():
        shutil.rmtree(work)

    kept = prune(deck, work)
    dest = (pathlib.Path(a.out).resolve() if a.out
            else deck.out / f"{deck.name}-slides.pptx")

    cmd = [str(BIN / "manim-slides"), "convert",
           *[deck.scene(p) for p in deck.parts], str(dest),
           "--to", "pptx", "--folder", str(work.relative_to(deck.root)),
           f"-cwidth={SLIDE_W}", f"-cheight={SLIDE_H}"]
    r = subprocess.run(cmd, cwd=deck.root, env=deck.env(),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True)
    if r.returncode != 0:
        print(r.stdout[-4000:])
        raise SystemExit("manim-slides convert failed")

    timed = auto_advance(dest, kept)

    if a.keep_stills:
        stills(deck, kept)

    size = dest.stat().st_size / 1048576
    print(f"{dest}  —  {len(kept)} slides, {SLIDE_W}x{SLIDE_H}, {size:.1f} MB")
    if timed:
        print(f"  {timed} slides advance by themselves into their loop")
    print("  кадры:", ", ".join(s for _, s, _ in kept[:6]), "…",
          ", ".join(s for _, s, _ in kept[-3:]))


if __name__ == "__main__":
    main()
