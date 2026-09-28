#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/budget.py — the performance budget helpers lint.py uses.
Run: python3 -m unittest tools/tests/test_budget.py"""
import os, sys, tempfile, shutil, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import budget

PIC = ('<picture>'
       '<source type="image/avif" media="(max-width:640px)" srcset="assets/i/a-480.avif 480w, assets/i/a-800.avif 800w" sizes="100vw">'
       '<source type="image/webp" media="(max-width:640px)" srcset="assets/i/a-480.webp 480w, assets/i/a-800.webp 800w" sizes="100vw">'
       '<source type="image/avif" srcset="assets/i/a-480.avif 480w, assets/i/a-800.avif 800w, assets/i/a-1200.avif 1200w, assets/i/a-1920.avif 1920w" sizes="100vw">'
       '<source type="image/webp" srcset="assets/i/a-480.webp 480w, assets/i/a-800.webp 800w, assets/i/a-1200.webp 1200w" sizes="100vw">'
       '<img src="assets/img/a.jpg" srcset="assets/i/a-480.jpg 480w, assets/i/a-800.jpg 800w, assets/img/a.jpg 1920w" sizes="100vw" alt="a" width="1920" height="1280" loading="lazy" decoding="async">'
       '</picture>')

HERO = ('<picture>'
        '<source type="image/avif" srcset="assets/i/h-480.avif 480w, assets/i/h-800.avif 800w, assets/i/h-1200.avif 1200w, assets/i/h-1920.avif 1920w" sizes="100vw">'
        '<source type="image/webp" srcset="assets/i/h-480.webp 480w, assets/i/h-800.webp 800w" sizes="100vw">'
        '<img src="assets/img/h.jpg" srcset="assets/i/h-480.jpg 480w, assets/img/h.jpg 1920w" sizes="100vw" alt="h" width="1920" height="1280" loading="eager" fetchpriority="high">'
        '</picture>')


class Bytes(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "assets/i"))
        os.makedirs(os.path.join(self.root, "assets/img"))
        self.sizes = {"assets/i/a-480.avif": 100, "assets/i/a-800.avif": 200, "assets/i/a-1200.avif": 400,
                      "assets/i/a-1920.avif": 800, "assets/i/h-800.avif": 300, "assets/i/h-1200.avif": 500,
                      "assets/img/logo.png": 50}
        for rel, n in self.sizes.items():
            with open(os.path.join(self.root, rel), "wb") as f:
                f.write(b"x" * n)

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_phone_takes_the_800_from_the_capped_source(self):
        # 375px at 2x needs 750 device pixels: the 800 candidate, not 1200
        self.assertEqual(budget.phone_image_bytes(PIC, self.root), 200)

    def test_hero_without_a_cap_takes_the_smallest_that_covers_750(self):
        self.assertEqual(budget.phone_image_bytes(HERO, self.root), 300)

    def test_plain_img_counts_its_file_and_sums(self):
        html = PIC + HERO + '<img src="assets/img/logo.png" alt="" width="10" height="10">'
        self.assertEqual(budget.phone_image_bytes(html, self.root), 200 + 300 + 50)

    def test_subdirectory_prefix_resolves(self):
        html = PIC.replace("assets/", "../../assets/")
        self.assertEqual(budget.phone_image_bytes(html, self.root), 200)

    def test_data_uri_and_empty_img_are_free(self):
        html = '<img alt=""><img src="data:image/webp;base64,AAAA" alt="">'
        self.assertEqual(budget.phone_image_bytes(html, self.root), 0)

    def test_sizes_shrink_what_a_tile_needs(self):
        # a half-width tile on a 375px phone needs 375 device px: the 480 file
        tile = PIC.replace('sizes="100vw"', 'sizes="(min-width:861px) 33vw, 50vw"')
        self.assertEqual(budget.phone_image_bytes(tile, self.root), 100)

    def test_initial_counts_eager_plus_near_fold_lazy_only(self):
        # hero (eager, 300) + eight lazy tiles (200 each): only four of the lazy
        # ones are within the lazy-load margin when the page opens
        html = HERO + PIC * 8
        self.assertEqual(budget.initial_image_bytes(html, self.root), 300 + 4 * 200)
        self.assertEqual(budget.phone_image_bytes(html, self.root), 300 + 8 * 200)

    def test_extra_hero_frames_are_not_fetched_on_a_phone(self):
        # the stylesheet keeps every frame but the first display:none below 861px
        html = ('<div class="hero__frame is-on">' + HERO + '</div>'
                '<div class="hero__frame">' + PIC + '</div>'
                '<div class="hero__frame">' + PIC + '</div>')
        self.assertEqual(budget.initial_image_bytes(html, self.root), 300)
        self.assertEqual(budget.phone_image_bytes(html, self.root), 300)

    def test_images_lists_document_order_with_lazy_flag(self):
        seq = budget.images(HERO + PIC)
        self.assertEqual(seq, [("assets/i/h-800.avif", False), ("assets/i/a-800.avif", True)])


class External(unittest.TestCase):
    def test_finds_fetched_third_parties_only(self):
        html = ('<link rel="canonical" href="https://theoverlookatflatheadlake.com/">'
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?x">'
                '<link rel="preload" as="font" href="assets/fonts/jost.woff2">'
                '<script src="https://static.cloudflareinsights.com/beacon.min.js" defer></script>'
                '<iframe src="https://www.google.com/maps/embed?x"></iframe>'
                '<a href="https://instagram.com/x">ig</a>')
        self.assertEqual(budget.external_requests(html),
                         ["fonts.googleapis.com", "static.cloudflareinsights.com", "www.google.com"])

    def test_clean_page_has_none(self):
        self.assertEqual(budget.external_requests('<script src="assets/js/core.js"></script>'), [])


class Dims(unittest.TestCase):
    def test_flags_missing_dimensions_and_bare_photographs(self):
        html = ('<img src="assets/img/logo.png" alt="" width="10" height="10">'
                '<img src="assets/img/x.jpg" alt="x" width="1" height="1">'
                '<img src="assets/img/y.png" alt="y">'
                '<img alt="">')
        bad = budget.imgs_missing_dims(html)
        self.assertEqual(len(bad), 2)
        self.assertIn("x.jpg", bad[0])        # a photograph with no srcset
        self.assertIn("y.png", bad[1])        # no width/height

    def test_picture_img_with_everything_passes(self):
        self.assertEqual(budget.imgs_missing_dims(PIC), [])


if __name__ == "__main__":
    unittest.main()
