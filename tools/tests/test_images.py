#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/images.py — responsive derivatives. Run: python3 -m unittest tools/tests/test_images.py"""
import os, sys, json, tempfile, shutil, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from PIL import Image
import images


class Derivatives(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "assets/img"))
        Image.new("RGB", (1920, 1280), (120, 90, 60)).save(
            os.path.join(self.root, "assets/img/tent.jpg"), quality=85)

    def tearDown(self):
        shutil.rmtree(self.root)

    def path(self, rel):
        return os.path.join(self.root, rel)

    def test_builds_every_width_and_format(self):
        m = images.build(self.root, ["tent.jpg"])
        e = m["tent.jpg"]
        self.assertEqual((e["w"], e["h"]), (1920, 1280))
        self.assertEqual(e["widths"], [480, 800, 1200, 1920])
        for w in (480, 800, 1200, 1920):
            self.assertTrue(os.path.exists(self.path(f"assets/i/tent-{w}.avif")), f"{w}.avif")
        for w in (480, 800, 1200):
            self.assertTrue(os.path.exists(self.path(f"assets/i/tent-{w}.webp")), f"{w}.webp")
        for w in (480, 800):
            self.assertTrue(os.path.exists(self.path(f"assets/i/tent-{w}.jpg")), f"{w}.jpg")
        # fallbacks stop where the fallback browsers stop mattering
        self.assertFalse(os.path.exists(self.path("assets/i/tent-1920.webp")))
        self.assertFalse(os.path.exists(self.path("assets/i/tent-1200.jpg")))
        # the 1920 JPEG is the original in assets/img — never duplicated
        self.assertFalse(os.path.exists(self.path("assets/i/tent-1920.jpg")))
        self.assertTrue(e["lqip"].startswith("data:image/webp;base64,"))
        self.assertLess(len(e["lqip"]), 900)
        self.assertEqual(len(e["hash"]), 8)
        # the manifest is written to disk and round-trips
        self.assertEqual(images.load_manifest(self.root)["tent.jpg"], e)

    def test_derivative_dimensions_keep_aspect(self):
        images.build(self.root, ["tent.jpg"])
        with Image.open(self.path("assets/i/tent-480.webp")) as im:
            self.assertEqual(im.size, (480, 320))

    def test_small_original_caps_widths(self):
        Image.new("RGB", (900, 600)).save(self.path("assets/img/s.jpg"))
        e = images.build(self.root, ["s.jpg"])["s.jpg"]
        self.assertEqual(e["widths"], [480, 800, 900])
        self.assertTrue(os.path.exists(self.path("assets/i/s-900.avif")))
        self.assertFalse(os.path.exists(self.path("assets/i/s-900.jpg")))

    def test_idempotent_by_hash(self):
        images.build(self.root, ["tent.jpg"])
        p = self.path("assets/i/tent-480.webp")
        t0 = os.path.getmtime(p)
        images.build(self.root, ["tent.jpg"])
        self.assertEqual(os.path.getmtime(p), t0)

    def test_changed_original_regenerates(self):
        images.build(self.root, ["tent.jpg"])
        h0 = images.load_manifest(self.root)["tent.jpg"]["hash"]
        Image.new("RGB", (1920, 1280), (10, 200, 10)).save(self.path("assets/img/tent.jpg"), quality=85)
        h1 = images.build(self.root, ["tent.jpg"])["tent.jpg"]["hash"]
        self.assertNotEqual(h0, h1)

    def test_png_passthrough(self):
        Image.new("RGBA", (400, 300)).save(self.path("assets/img/logo.png"))
        e = images.build(self.root, ["logo.png"])["logo.png"]
        self.assertEqual((e["w"], e["h"]), (400, 300))
        self.assertEqual(e["widths"], [])  # logos are not photographs
        self.assertEqual(e["lqip"], "")

    def test_missing_original_raises(self):
        with self.assertRaises(FileNotFoundError):
            images.build(self.root, ["nope.jpg"])

    def test_default_set_is_every_jpg_and_png_in_img(self):
        Image.new("RGB", (900, 600)).save(self.path("assets/img/b.jpg"))
        Image.new("RGBA", (40, 40)).save(self.path("assets/img/c.png"))
        with open(self.path("assets/img/notes.txt"), "w") as f:
            f.write("x")
        m = images.build(self.root)
        self.assertEqual(sorted(m), ["b.jpg", "c.png", "tent.jpg"])


if __name__ == "__main__":
    unittest.main()
