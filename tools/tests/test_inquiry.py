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
        self.assertIn(f'<iframe class="hbw__frame" src="{shell.HB_FORM_URL}"', h)
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

    def test_package_pages_name_their_package_in_honeybook(self):
        # Owner, 2026-09-29: "if they inquire for the ultimate weekend we need
        # to know that". The package page's form carries the package as its
        # campaign, which HoneyBook records with the lead.
        for page, slug in shell.PACKAGE_CAMPAIGN.items():
            h = read(os.path.join(ROOT, page))
            self.assertIn(f'data-campaign="{slug}"', h, page)
        h = read(os.path.join(ROOT, "weddings.html"))
        self.assertNotIn("data-campaign=", h)
        js = read(os.path.join(ROOT, "assets", "js", "inquire.js"))
        self.assertIn("dataset.campaign", js)

    def test_the_public_form_is_framed_not_the_embed(self):
        # Below 768px wide HoneyBook's /embed/ version shows Submit as a bare
        # arrow (owner, 2026-09-29); the public version has a real button.
        for p in PAGES:
            self.assertNotIn(".hbportal.co/embed/", read(p), os.path.relpath(p, ROOT))
        css = read(os.path.join(ROOT, "assets", "css", "site.css"))
        self.assertRegex(css, r"\.hbw__frame\{[^}]*height:calc\(100% \+ 68px\)")
        # the frame must stay narrower than HoneyBook's 768px desktop layout,
        # whose top bar is 82px tall and would show under a 68px trim
        self.assertRegex(css, r"\.hbw\{[^}]*max-width:720px")

    def test_honeybooks_arrow_bar_is_trimmed_off(self):
        # On a phone HoneyBook's form opens with a 68px bar whose only
        # content is an arrow-shaped copy of Submit (measured 334-700px wide,
        # 2026-09-29); the frame is pulled up so the bar sits outside the box.
        css = read(os.path.join(ROOT, "assets", "css", "site.css"))
        self.assertRegex(css, r"\.hbw\{[^}]*overflow:hidden")
        self.assertRegex(css, r"\.hbw__frame\{[^}]*margin-top:-68px")


if __name__ == "__main__":
    unittest.main()
