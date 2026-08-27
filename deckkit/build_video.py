#!/usr/bin/env python3
"""Render a deck's film: one file per part plus one continuous cut.

Every part is a single Manim scene cut into frames with `next_section`, so the
same render produces both the continuous video and the per-frame clips that
`build_pptx.py` turns into slides.

    python -m deckkit.build_video paper_1_minimalism
    python -m deckkit.build_video paper_1_minimalism --parts 4 5
    python -m deckkit.build_video paper_1_minimalism --quality l   # proof
"""

import argparse
import pathlib
import shutil
import subprocess
import sys

from deckkit.deck import Deck

QUALITY_DIR = {"l": "480p15", "m": "720p30", "h": "1080p60", "k": "2160p60"}
MANIM = pathlib.Path(sys.executable).with_name("manim")


def render(deck, part, quality):
    scene = deck.scene(part)
    stem = f"part{part}"
    cmd = [str(MANIM), f"-q{quality}", "--save_sections",
           "--media_dir", str(deck.media), "-o", stem,
           str(deck.module(part)), scene]
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
    a = ap.parse_args()

    deck = Deck(a.deck)
    wanted = a.parts or deck.parts
    deck.out.mkdir(parents=True, exist_ok=True)
    (deck.out / "parts").mkdir(exist_ok=True)

    rendered = []
    for p in wanted:
        mp4 = render(deck, p, a.quality)
        dest = deck.out / "parts" / f"{deck.name}-part{p}.mp4"
        shutil.copy2(mp4, dest)
        rendered.append(dest)
        print(f"  {dest.name}  {probe(dest):6.1f} s", flush=True)

    if list(wanted) == deck.parts:
        full = deck.out / f"{deck.name}-full.mp4"
        concat(rendered, full)
        t = probe(full)
        print(f"\n{full}  {t:.1f} s = {int(t // 60)}:{int(t % 60):02d}")


if __name__ == "__main__":
    main()
