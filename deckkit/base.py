"""Shared scene machinery.

Every part of a deck is ONE continuous scene, cut into frames with
`self.next_section(...)`.  That gives both the per-frame export used for the
PPTX and a single continuous film, from the same code.
"""

import json
import os
import pathlib

from manim import Scene, config, FadeIn, FadeOut, VGroup

from deckkit.tokens import BG


def _frames_path():
    """Where the storyboard index lives.

    The build scripts point at it with DECK_DIR; run a scene by hand and it
    is found by walking up from the working directory.
    """
    env = os.environ.get("DECK_DIR")
    if env:
        return pathlib.Path(env) / "build" / "frames.json"
    here = pathlib.Path.cwd()
    for d in [here, *here.parents]:
        cand = d / "build" / "frames.json"
        if cand.exists():
            return cand
    raise SystemExit("frames.json not found — set DECK_DIR or run from the "
                     "deck directory")


def load_frames():
    with open(_frames_path(), encoding="utf-8") as fh:
        return {f["screen"]: f for f in json.load(fh)}


FRAMES = load_frames()


def notes_of(screen):
    return FRAMES[screen]["notes"]


def duration_of(screen, default=16.0):
    d = FRAMES[screen]["duration"]
    return default if d is None else d


class DeckScene(Scene):
    """A part of the deck.  Subclasses implement `construct`."""

    def setup(self):
        self.camera.background_color = BG
        self._budget = None
        self._frame_start = 0.0

    # -- frame boundaries ---------------------------------------------------
    def frame(self, screen):
        """Open a new storyboard frame.  Returns its budgeted duration."""
        meta = FRAMES[screen]
        self.next_section(name=screen, skip_animations=False)
        self._budget = duration_of(screen)
        self._frame_start = self.clock()
        return self._budget

    def clock(self):
        """Seconds of finished film, straight from the renderer.

        Adding up requested `run_time`s drifts: several Manim animations
        recompute their own duration after construction, so the tally runs
        ahead of the timeline and frames end early.  The renderer's clock is
        the only number that matches what was written.
        """
        return float(getattr(self.renderer, "time", 0.0))

    def left(self):
        return (self._budget or 0.0) - (self.clock() - self._frame_start)

    def settle(self, *beats, hold=0.9, gap=0.3, tail=0.9):
        """Finish the frame: hold briefly, then keep it alive to the end.

        The storyboard gives each frame 8-20 s, but its layers take only a few
        of them.  Rather than freeze on the finished image for the remainder,
        the frame replays `beats` — small Manim animations over the elements
        that carry its meaning — until the budget is used up.  The last
        `tail` seconds are always still, so the still the PPTX takes from the
        end of the section is the clean finished frame.
        """
        self.wait(min(max(self.left(), 0.0), hold) or 0.0)
        if beats:
            i = 0
            while True:
                room = self.left() - tail
                if room <= gap + 0.5:
                    break
                anim = beats[i % len(beats)]()
                rt = getattr(anim, "run_time", 1.0)
                if rt + gap > room:
                    break
                self.play(anim)
                self.wait(gap)
                i += 1
        rest = self.left()
        self.wait(max(rest, 1.0))

    def outro(self, run_time=0.6):
        """Close the part.

        The fade-out gets a section of its own: without it the fade would fall
        inside the last storyboard frame's section, and the still the PPTX
        takes from the end of that section would be an empty screen.
        """
        self.next_section(name="_outro", skip_animations=False)
        if self.mobjects:
            super().play(FadeOut(*self.mobjects), run_time=run_time)

    # -- convenience --------------------------------------------------------
    def clear_frame(self, keep=(), run_time=0.6):
        """Fade out everything except `keep` — used only where the storyboard
        says an element leaves for good."""
        keep_set = set()
        for k in keep:
            keep_set.add(k)
        going = [m for m in self.mobjects if m not in keep_set]
        if going:
            self.play(*[FadeOut(m) for m in going], run_time=run_time)
