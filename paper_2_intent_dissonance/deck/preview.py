"""Stills of settled storyboard states, for checking layout by eye.

    DECK_DIR=paper_2_intent_dissonance PYTHONPATH=.:paper_2_intent_dissonance \\
        .venv/bin/python paper_2_intent_dissonance/deck/preview.py 05:3 10:5 …

Writes build/preview/<frame>_<step>.png at 1920×1080.  `05:3` is frame 05,
click 3 (0-based, as in the storyboard's `st`); `05` alone is every click.
"""

import pathlib
import sys

from manim import Scene, config, tempconfig

from deck import scenes as SC
from deck.stage import Stage, wrap

OUT = pathlib.Path(__file__).resolve().parent.parent / "build" / "preview"


class Still(Scene):
    def __init__(self, i, v, **kw):
        self.i, self.v = i, v
        super().__init__(**kw)

    def construct(self):
        st = Stage()
        st.clear_updaters()
        state = SC.build(self.i, self.v, wrap)
        prims = Stage.flatten(state)
        st.jump(prims, tuple(float(c) for c in state["cam"]))
        st.A = dict(st.B)
        st.camA = st.camB
        st.tau = 60.0
        st.tick(0.0)
        self.add(st)


def main(args):
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = []
    for a in args:
        f, _, s = a.partition(":")
        i = int(f) - 1
        steps = [int(s)] if s else range(SC.MAX[i] + 1)
        jobs += [(i, v) for v in steps]
    for i, v in jobs:
        name = f"{i + 1:02d}_{v}"
        with tempconfig({"pixel_width": 1920, "pixel_height": 1080,
                         "frame_rate": 15, "save_last_frame": True,
                         "write_to_movie": False, "disable_caching": True,
                         "media_dir": str(OUT / "media"),
                         "output_file": name, "verbosity": "ERROR",
                         "background_color": "#000000"}):
            sc = Still(i, v)
            sc.render()
            src = pathlib.Path(sc.renderer.file_writer.image_file_path)
            dst = OUT / f"{name}.png"
            src.replace(dst)
            print(dst, flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
