#!/usr/bin/env python3
"""Render a deck: one video per part, one continuous cut, and the slide index.

Each part is a single `manim_slides.Slide` scene cut into frames with
`self.frame(...)`.  Rendering through `manim-slides render` writes the normal
Manim video *and* the per-slide clips plus `slides/<Scene>.json`, so the film
and the PPTX come out of one render — `build_pptx.py` only has to convert.

    python -m deckkit.build_video paper_1_minimalism
    python -m deckkit.build_video paper_1_minimalism --parts 4 5
    python -m deckkit.build_video paper_1_minimalism --quality l   # proof
    python -m deckkit.build_video paper_2_intent_dissonance --quality k --jobs 4
"""

import argparse
import pathlib
import shutil
import subprocess
import sys

from deckkit.deck import Deck

QUALITY_DIR = {"l": "480p15", "m": "720p30", "h": "1080p60", "k": "2160p60"}
BIN = pathlib.Path(sys.executable).parent


def render(deck, part, quality):
    scene = deck.scene(part)
    stem = f"part{part}"
    # long form: manim-slides' own parser reads the "h" of "-qh" as -h/--help
    cmd = [str(BIN / "manim-slides"), "render", "--quality", quality,
           "--media_dir", str(deck.media), "-o", stem,
           str(deck.module(part).relative_to(deck.root)), scene]
    print(f"→ {scene} ({QUALITY_DIR[quality]})", flush=True)
    r = subprocess.run(cmd, cwd=deck.root, env=deck.env(),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True)
    if r.returncode != 0:
        print(r.stdout[-4000:])
        raise SystemExit(f"{scene} failed")
    return deck.media / "videos" / stem / QUALITY_DIR[quality] / f"{stem}.mp4"


def concat(files, dest):
    """Join the parts with the concat demuxer — same encoder settings, so the
    streams copy through without a re-encode."""
    listing = dest.with_suffix(".txt")
    listing.write_text("".join(f"file '{f}'\n" for f in files),
                       encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", str(listing), "-c", "copy", str(dest)], check=True)
    listing.unlink()


def probe(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)]).decode().strip()
    return float(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("--parts", nargs="*", type=int)
    ap.add_argument("--quality", default="h", choices=list(QUALITY_DIR))
    ap.add_argument("--jobs", type=int, default=1,
                    help="parts rendered at once (each is its own process)")
    a = ap.parse_args()

    deck = Deck(a.deck)
    wanted = a.parts or deck.parts
    deck.out.mkdir(parents=True, exist_ok=True)
    (deck.out / "parts").mkdir(exist_ok=True)

    def one(p):
        mp4 = render(deck, p, a.quality)
        dest = deck.out / "parts" / f"{deck.name}-part{p}.mp4"
        shutil.copy2(mp4, dest)
        print(f"  {dest.name}  {probe(dest):6.1f} s", flush=True)
        return dest

    if a.jobs > 1:
        # parallel Manim processes race to create the shared caches
        for d in ("texts", "Tex", "images", "videos"):
            (deck.media / d).mkdir(parents=True, exist_ok=True)
        # parallel Manim processes race to create the shared caches
        for d in ("texts", "Tex", "images", "videos"):
            (deck.media / d).mkdir(parents=True, exist_ok=True)
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(a.jobs) as pool:
            rendered = list(pool.map(one, wanted))
    else:
        rendered = [one(p) for p in wanted]

    if list(wanted) == deck.parts:
        full = deck.out / f"{deck.name}-full.mp4"
        concat(rendered, full)
        t = probe(full)
        print(f"\n{full}  {t:.1f} s = {int(t // 60)}:{int(t % 60):02d}")


if __name__ == "__main__":
    main()
