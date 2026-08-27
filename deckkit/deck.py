"""A deck is a directory; this reads its manifest.

Every talk in the repo lives in its own folder with a `deck.json` next to a
`deck/` package of scenes.  The framework never knows anything about a
particular talk beyond what this manifest says.

    {
      "name": "dhe",
      "storyboard": "storyboard/DHE Storyboard v2.dc.html",
      "parts": [1, 2, 3, 4, 5, 6, 7, 8],
      "scene": "Part{n}",
      "module": "deck/part{n}.py",
      "skip": ["S1", "S2", "S3", "8.10"]
    }
"""

import json
import os
import pathlib


class Deck:
    def __init__(self, root):
        self.root = pathlib.Path(root).resolve()
        manifest = self.root / "deck.json"
        if not manifest.exists():
            raise SystemExit(f"no deck.json in {self.root}")
        self.cfg = json.loads(manifest.read_text(encoding="utf-8"))

    # -- identity -----------------------------------------------------------
    @property
    def name(self):
        return self.cfg.get("name", self.root.name)

    @property
    def parts(self):
        return list(self.cfg.get("parts", []))

    def scene(self, n):
        return self.cfg.get("scene", "Part{n}").format(n=n)

    def module(self, n):
        return self.root / self.cfg.get("module", "deck/part{n}.py").format(n=n)

    @property
    def skip(self):
        """Frames that exist in the storyboard but are not part of the talk."""
        return set(self.cfg.get("skip", []))

    # -- paths --------------------------------------------------------------
    @property
    def storyboard(self):
        return self.root / self.cfg["storyboard"]

    @property
    def frames_json(self):
        return self.root / "build" / "frames.json"

    @property
    def media(self):
        return self.root / "build" / "media"

    @property
    def out(self):
        return self.root / "out"

    @property
    def stills(self):
        return self.root / "build" / "stills"

    def frames(self):
        return json.loads(self.frames_json.read_text(encoding="utf-8"))

    def content_frames(self):
        return [f for f in self.frames() if f["screen"] not in self.skip]

    # -- child process environment -----------------------------------------
    def env(self):
        """PYTHONPATH for a manim subprocess: the framework and this deck."""
        repo = pathlib.Path(__file__).resolve().parent.parent
        e = dict(os.environ)
        e["PYTHONPATH"] = os.pathsep.join(
            [str(repo), str(self.root), e.get("PYTHONPATH", "")]).rstrip(os.pathsep)
        e["DECK_DIR"] = str(self.root)
        return e
