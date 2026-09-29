#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static guards on the site scripts. Run: python3 -m unittest tools/tests/test_scripts.py

Bug, 2026-09-28: opening the weddings page dropped the reader 76% of the way
down, onto The Driftwood. The slideshow selected its first photograph on load
with thumb.scrollIntoView({block: "nearest"}) — and scrollIntoView scrolls
every scrollable ancestor, the page included, to reach an element below the
fold. A horizontal strip (thumbnails, the section nav, the map rail) must
scroll itself sideways and never the page."""
import os, re, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def src(name):
    with open(os.path.join(ROOT, "assets", "js", name), encoding="utf-8") as f:
        return f.read()


class NoPageJumps(unittest.TestCase):
    def test_core_never_scrolls_the_page_to_reach_an_element(self):
        calls = [m.start() for m in re.finditer(r"\.scrollIntoView\(", src("core.js"))]
        self.assertEqual(calls, [], "core.js calls scrollIntoView; scroll the strip itself "
                                    "(stripTo) so the page never moves")

    def test_core_has_the_sideways_helper(self):
        self.assertIn("function stripTo(", src("core.js"))


if __name__ == "__main__":
    unittest.main()
