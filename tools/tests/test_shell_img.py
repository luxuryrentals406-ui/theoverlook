#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shell.img() emits <picture> from the derivative manifest.
Run: python3 -m unittest tools/tests/test_shell_img.py  (after tools/images.py)"""
import os, sys, re, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import shell

HERO = "hero-pavilion-lake.jpg"   # 1920x1280, present in every build


class Picture(unittest.TestCase):
    def test_photo_becomes_picture_with_three_formats(self):
        h = shell.img(HERO, "The pavilion at dusk")
        self.assertTrue(h.startswith("<picture"))
        self.assertIn('type="image/avif"', h)
        self.assertIn('type="image/webp"', h)
        self.assertIn("assets/i/hero-pavilion-lake-480.avif 480w", h)
        self.assertIn("assets/i/hero-pavilion-lake-1920.avif 1920w", h)
        self.assertIn("assets/i/hero-pavilion-lake-1200.webp 1200w", h)
        self.assertNotIn("1920.webp", h)                      # WebP stops at 1200
        self.assertIn("assets/i/hero-pavilion-lake-800.jpg 800w", h)
        self.assertNotIn("1200.jpg", h)                       # JPEG stops at 800
        self.assertIn('src="assets/img/hero-pavilion-lake.jpg"', h)  # the original is the JPEG fallback
        self.assertIn('width="1920" height="1280"', h)
        self.assertIn('alt="The pavilion at dusk"', h)
        self.assertIn('sizes="100vw"', h)
        self.assertIn('loading="lazy"', h)
        self.assertIn('decoding="async"', h)
        self.assertIn("background:url('data:image/webp;base64,", h)

    def test_base_prefix_applies_to_every_candidate(self):
        h = shell.img(HERO, "x", base="../../")
        for url in re.findall(r'(?:src|srcset)="([^"]+)"', h):
            for cand in url.split(","):
                self.assertTrue(cand.strip().startswith("../../assets/"), cand)

    def test_sizes_and_class_pass_through(self):
        h = shell.img(HERO, "x", cls="vmap__base", sizes=shell.SZ_HALF)
        self.assertIn('class="vmap__base"', h)
        self.assertIn(f'sizes="{shell.SZ_HALF}"', h)

    def test_eager_hero_frame(self):
        h = shell.img(HERO, "x", eager=True)
        self.assertIn('loading="eager"', h)
        self.assertIn('fetchpriority="high"', h)
        self.assertNotIn('loading="lazy"', h)
        self.assertNotIn("media=", h)                        # the hero is never capped

    def test_phones_are_offered_nothing_wider_than_800(self):
        h = shell.img(HERO, "x")
        m = re.search(r'<source type="image/avif" media="\(max-width:640px\)" srcset="([^"]+)"', h)
        self.assertIsNotNone(m)
        self.assertIn("800.avif 800w", m.group(1))
        self.assertNotIn("1200", m.group(1))
        self.assertNotIn("1920", m.group(1))
        # the general sources that follow still carry the large candidates
        self.assertIn("1920.avif 1920w", h.split("media=")[-1])
        # a thumbnail is already capped, so it gets no extra phone sources
        self.assertNotIn("media=", shell.img(HERO, "x", thumb=True))

    def test_thumb_caps_candidates(self):
        h = shell.img(HERO, "x", thumb=True)
        self.assertIn("480.avif 480w", h)
        self.assertIn("800.avif 800w", h)
        self.assertNotIn("1200", h)
        self.assertNotIn("1920.avif", h)

    def test_png_logo_is_a_plain_img_with_dimensions(self):
        h = shell.img("overlook-logo-main.png", "The Overlook", eager=None)
        self.assertTrue(h.startswith("<img"))
        self.assertNotIn("<picture", h)
        self.assertNotIn("srcset", h)
        self.assertRegex(h, r'width="\d+" height="\d+"')
        self.assertNotIn("loading=", h)

    def test_unknown_photo_fails_the_build(self):
        with self.assertRaises(KeyError):
            shell.img("does-not-exist.jpg", "x")

    def test_hero_preload_matches_the_avif_candidates(self):
        h = shell.hero_preload(HERO, base="../")
        self.assertIn('rel="preload"', h)
        self.assertIn('as="image"', h)
        self.assertIn('type="image/avif"', h)
        self.assertIn('imagesizes="100vw"', h)
        self.assertIn("../assets/i/hero-pavilion-lake-480.avif 480w", h)
        self.assertIn('fetchpriority="high"', h)


if __name__ == "__main__":
    unittest.main()
