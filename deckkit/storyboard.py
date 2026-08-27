"""Parse a Claude Design storyboard (.dc.html) into a frame index.

Each `<section>` is one frame; its data-* attributes carry the label, the
layer order, the morph into the next frame and the speaker notes with the
frame duration.  Everything downstream reads `build/frames.json`, never the
HTML.

    python -m deckkit.storyboard paper_1_minimalism
"""

import argparse
import json
import pathlib
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from deckkit.deck import Deck  # noqa: E402


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.frames = []
        self.depth = 0
        self.cur = None
        self.buf = []
    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        if tag == "section":
            if self.depth == 0:
                self.cur = dict(attrs)
                self.buf = []
                self.depth = 1
                return
            self.depth += 1
        if self.depth:
            self.buf.append(raw)
    def handle_startendtag(self, tag, attrs):
        if self.depth: self.buf.append(self.get_starttag_text())
    def handle_endtag(self, tag):
        if tag == "section" and self.depth:
            self.depth -= 1
            if self.depth == 0:
                self.frames.append((self.cur, "".join(self.buf)))
                self.cur = None
                return
        if self.depth: self.buf.append(f"</{tag}>")
    def handle_data(self, d):
        if self.depth: self.buf.append(d)
    def handle_entityref(self, n):
        if self.depth: self.buf.append(f"&{n};")
    def handle_charref(self, n):
        if self.depth: self.buf.append(f"&#{n};")

def parse(html_text):
    p = P()
    p.feed(html_text)
    frames = []
    for a, body in p.frames:
        notes = a.get("data-speaker-notes", "") or ""
        dm = re.match(r"\s*([\d.,]+)\s*с\b", notes)
        frames.append({
            "idx": len(frames),
            "label": a.get("data-label", ""),
            "screen": a.get("data-screen-label", ""),
            "layers": [x.strip() for x in
                       (a.get("data-layers") or "").split(";") if x.strip()],
            "morph": a.get("data-morph", "") or "",
            "notes": notes,
            "duration": float(dm.group(1).replace(",", ".")) if dm else None,
            "style": a.get("style", ""),
            "body": body,
        })
    return frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    a = ap.parse_args()
    deck = Deck(a.deck)
    frames = parse(deck.storyboard.read_text(encoding="utf-8"))
    deck.frames_json.parent.mkdir(parents=True, exist_ok=True)
    deck.frames_json.write_text(
        json.dumps(frames, ensure_ascii=False, indent=1), encoding="utf-8")

    content = [f for f in frames if f["screen"] not in deck.skip]
    total = sum(f["duration"] or 0 for f in content)
    print(f"{deck.storyboard.name}")
    print(f"  frames  {len(frames)}   content {len(content)}   "
          f"skipped {sorted(deck.skip)}")
    print(f"  runtime {total:.0f}s = {int(total // 60)}:{int(total % 60):02d}")
    missing = [f["screen"] for f in content if f["duration"] is None]
    if missing:
        print("  no duration in notes:", ", ".join(missing))
    print(f"  → {deck.frames_json}")


if __name__ == "__main__":
    main()
