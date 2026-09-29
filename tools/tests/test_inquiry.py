#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every inquiry goes straight into HoneyBook (owner, 2026-09-29).
Checks the built pages: run after tools/build.py.
Run: python3 -m unittest tools/tests/test_inquiry.py"""
import os, re, sys, glob, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import shell

PAGES = sorted(glob.glob(os.path.join(ROOT, "*.html")) +
               glob.glob(os.path.join(ROOT, "*", "index.html")) +
               glob.glob(os.path.join(ROOT, "*", "*", "index.html")))


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


class StraightIntoHoneyBook(unittest.TestCase):
    def test_every_window_holds_the_honeybook_form(self):
        n = 0
        for p in PAGES:
            h = read(p)
            if 'id="inquire"' not in h:
                continue
            n += 1
            self.assertIn(f'data-src="{shell.HB_FORM_URL}"', h, os.path.relpath(p, ROOT))
        self.assertGreater(n, 10)

    def test_contact_page_shows_the_form_inline(self):
        h = read(os.path.join(ROOT, "contact.html"))
        self.assertTrue(f'src="{shell.HB_FORM_URL}"' in h or shell.HB_EMBED, "contact.html")
        self.assertNotIn('id="inquire"', h)

    def test_no_other_inquiry_route_survives(self):
        for p in PAGES:
            h = read(p)
            name = os.path.relpath(p, ROOT)
            self.assertNotIn("data-endpoint", h, name)
            self.assertNotIn('id="inquiry"', h, name)
            self.assertNotIn("/api/inquire", h, name)
            self.assertNotIn("formspree", h.lower(), name)

    def test_every_inquiry_button_opens_the_window_or_the_contact_page(self):
        for p in PAGES:
            h = read(p)
            if 'id="inquire"' not in h:
                continue
            for m in re.finditer(r"<a [^>]*data-sheet[^>]*>", h):
                self.assertRegex(m.group(0), r'href="(\.\./)*contact\.html', os.path.relpath(p, ROOT))

    def test_no_inquiry_link_skips_the_window(self):
        # A plain link to the contact page reloads it and loses the visitor's
        # place; every one in the page body opens the window instead.
        for p in PAGES:
            h = read(p)
            if 'id="inquire"' not in h:
                continue
            body = re.sub(r"<header.*?</header>|<footer.*?</footer>|<nav.*?</nav>", " ", h, flags=re.S)
            for m in re.finditer(r'<a [^>]*href="(\.\./)*contact\.html[^"]*"[^>]*>', body):
                self.assertIn("data-sheet", m.group(0), os.path.relpath(p, ROOT))

    def test_contact_page_links_reach_the_inline_form(self):
        h = read(os.path.join(ROOT, "contact.html"))
        self.assertIn('id="inquiry-form"', h)
        self.assertNotRegex(h, r'<a class="tlink" href="contact\.html')


if __name__ == "__main__":
    unittest.main()
