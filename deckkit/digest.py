"""Turn each frame's inline-styled HTML into a compact element blueprint.

Reading a storyboard frame as raw HTML is unusable; this prints it as a short
tree of shapes with only the properties that matter for drawing it.

    python -m deckkit.digest paper_1_minimalism 5.6
"""
import json, re, sys, pathlib
from html.parser import HTMLParser

def parse_style(s):
    d = {}
    for part in s.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            d[k.strip()] = v.strip()
    return d

KEEP = ("width","height","background","border","color","font","gap","padding","margin",
        "position","left","top","right","bottom","inset","transform","transform-origin",
        "display","flex","flex-direction","align-items","justify-content","grid-template-columns",
        "border-radius","border-top","border-left","border-bottom","border-right","opacity",
        "align-content","flex-wrap","writing-mode","white-space","line-height","text-align")

class D(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.depth = 0
        self.stack = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        st = parse_style(a.get("style",""))
        st = {k:v for k,v in st.items() if k in KEEP}
        extra = {k:v for k,v in a.items() if k.startswith("data-")}
        self.out.append(("  "*self.depth) + f"<{tag}" +
                        (" " + json.dumps(st, ensure_ascii=False) if st else "") +
                        (" " + json.dumps(extra, ensure_ascii=False) if extra else "") + ">")
        self.depth += 1
        self.stack.append(tag)
    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop(); self.depth = max(0, self.depth-1)
    def handle_data(self, d):
        t = d.strip()
        if t: self.out.append(("  "*self.depth) + "«" + t + "»")

def digest(body, collapse=True):
    p = D(); p.feed(body)
    lines = p.out
    if collapse:
        # collapse runs of identical consecutive lines
        res, i = [], 0
        while i < len(lines):
            j = i
            while j+1 < len(lines) and lines[j+1] == lines[i]:
                j += 1
            n = j - i + 1
            res.append(lines[i] + (f"   ×{n}" if n > 1 else ""))
            i = j + 1
        lines = res
    return "\n".join(lines)

if __name__ == "__main__":
    # deckkit.digest <deck-dir> [screen ...]
    import pathlib as _pl
    sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent))
    from deckkit.deck import Deck
    deck = Deck(sys.argv[1])
    frames = deck.frames()
    want = sys.argv[2:] or None
    for f in frames:
        if want and f["screen"] not in want: continue
        print("="*100)
        print(f'[{f["screen"]}] {f["label"]}   {f["duration"]}s')
        print("LAYERS: " + " | ".join(f["layers"]))
        print("MORPH→ " + f["morph"])
        print("NOTES: " + f["notes"])
        print("SECTION-STYLE: " + json.dumps(parse_style(f["style"]), ensure_ascii=False))
        print("-"*100)
        print(digest(f["body"]))
