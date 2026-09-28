#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Responsive image derivatives for the site.

    python3 tools/images.py            # every photograph in assets/img
    python3 tools/images.py a.jpg b.jpg

Originals live in assets/img/ and are the source of truth. This writes
assets/i/<stem>-<width>.<avif|webp|jpg> at 480 / 800 / 1200 / 1920 wide and a
manifest (assets/i/manifest.json) that shell.img() reads to emit <picture>
with srcset, width/height and an inline blurred placeholder.

Rules:
  - AVIF at every width is the format almost every visitor gets
  - WebP only up to 1200 and JPEG only up to 800: they exist for the few
    browsers without AVIF, and a phone is the case that matters there
  - the JPEG at the original's own width is the original itself, never copied
  - a photograph narrower than 1920 gets its own width as the largest step
  - PNGs (logos) are measured but not derived
  - content-hashed: an unchanged original is skipped, so this is cheap to
    run on every build and the output is committed
"""
import os, sys, io, json, glob, base64, hashlib
from PIL import Image, ImageOps

WIDTHS = [480, 800, 1200, 1920]
WEBP_MAX = 1200
JPEG_MAX = 800
IMG_DIR = "assets/img"
OUT_DIR = "assets/i"
MANIFEST = os.path.join(OUT_DIR, "manifest.json")
LQIP_W = 20

AVIF = dict(quality=55, speed=7)
WEBP = dict(quality=78, method=4)
JPEG = dict(quality=80, progressive=True, optimize=True)

# A photograph full of foliage can come out twice the size of its neighbours
# at the same quality. Past these byte caps the AVIF is re-encoded a notch
# lower; on a phone a lighter file matters more than the last bit of grain.
AVIF_CAP = {480: 45_000, 800: 100_000, 1200: 200_000, 1920: 350_000}
AVIF_STEPS = (55, 45, 38)
POLICY = 2      # bump when the encoding rules change so every entry regenerates


def load_manifest(root):
    try:
        with open(os.path.join(root, MANIFEST), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_manifest(root, m):
    os.makedirs(os.path.join(root, OUT_DIR), exist_ok=True)
    with open(os.path.join(root, MANIFEST), "w", encoding="utf-8") as f:
        json.dump(m, f, indent=1, sort_keys=True)
        f.write("\n")


def _stem(name):
    return os.path.splitext(name)[0]


def _widths_for(orig_w):
    ws = [w for w in WIDTHS if w < orig_w]
    if orig_w <= WIDTHS[-1] and orig_w not in ws:
        ws.append(orig_w)
    return ws


def _files_for(name, widths, orig_w):
    """Every derivative path (relative to root) an entry should have on disk."""
    out = []
    for w in widths:
        out.append(f"{OUT_DIR}/{_stem(name)}-{w}.avif")
        if w <= WEBP_MAX:
            out.append(f"{OUT_DIR}/{_stem(name)}-{w}.webp")
        if w <= JPEG_MAX and w != orig_w:
            out.append(f"{OUT_DIR}/{_stem(name)}-{w}.jpg")
    return out


def _hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:8]


def _lqip(im):
    h = max(1, round(im.height * LQIP_W / im.width))
    tiny = im.resize((LQIP_W, h), Image.LANCZOS)
    b = io.BytesIO()
    tiny.save(b, "WEBP", quality=40, method=6)
    return "data:image/webp;base64," + base64.b64encode(b.getvalue()).decode("ascii")


def _encode_avif(frame, path, cap, icc=None):
    """Save AVIF at the default quality; step down while it is over `cap`
    bytes. Returns the quality that was kept."""
    kept = AVIF_STEPS[0]
    for q in AVIF_STEPS:
        kept = q
        frame.save(path, "AVIF", icc_profile=icc, quality=q, speed=AVIF["speed"])
        if cap is None or os.path.getsize(path) <= cap:
            break
    return kept


def _derive(root, name, im, widths):
    icc = im.info.get("icc_profile")
    for w in widths:
        h = round(im.height * w / im.width)
        frame = im if w == im.width else im.resize((w, h), Image.LANCZOS)
        base = os.path.join(root, OUT_DIR, f"{_stem(name)}-{w}")
        _encode_avif(frame, base + ".avif", AVIF_CAP.get(w), icc)
        if w <= WEBP_MAX:
            frame.save(base + ".webp", "WEBP", icc_profile=icc, **WEBP)
        if w <= JPEG_MAX and w != im.width:
            frame.save(base + ".jpg", "JPEG", icc_profile=icc, **JPEG)


def build(root, names=None, log=None):
    """Generate derivatives for `names` (default: every photograph) and return
    the full manifest. Raises FileNotFoundError for a name with no original."""
    root = os.path.abspath(root)
    img_dir = os.path.join(root, IMG_DIR)
    os.makedirs(os.path.join(root, OUT_DIR), exist_ok=True)
    manifest = load_manifest(root)

    prune = names is None
    if names is None:
        names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(img_dir, "*"))
                       if p.lower().endswith((".jpg", ".jpeg", ".png")))

    for name in names:
        src = os.path.join(img_dir, name)
        if not os.path.isfile(src):
            raise FileNotFoundError(f"{IMG_DIR}/{name} does not exist")
        digest = _hash(src)
        old = manifest.get(name)
        with Image.open(src) as raw:
            im = ImageOps.exif_transpose(raw)
            if name.lower().endswith(".png"):
                entry = {"w": im.width, "h": im.height, "hash": digest, "lqip": "", "widths": [],
                         "v": POLICY}
            else:
                im = im.convert("RGB")
                widths = _widths_for(im.width)
                entry = {"w": im.width, "h": im.height, "hash": digest,
                         "lqip": "", "widths": widths, "v": POLICY}
                need = _files_for(name, widths, im.width)
                fresh = (old is not None and old.get("hash") == digest and old.get("lqip")
                         and old.get("v") == POLICY
                         and all(os.path.exists(os.path.join(root, p)) for p in need))
                if fresh:
                    entry["lqip"] = old["lqip"]
                else:
                    if log:
                        log(f"  deriving {name}")
                    _derive(root, name, im, widths)
                    entry["lqip"] = _lqip(im)
        manifest[name] = entry

    if prune:
        for name in list(manifest):
            if not os.path.isfile(os.path.join(img_dir, name)):
                for p in glob.glob(os.path.join(root, OUT_DIR, _stem(name) + "-*.*")):
                    os.remove(p)
                del manifest[name]

    _save_manifest(root, manifest)
    return manifest


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    names = argv or None
    m = build(root, names, log=print)
    n = sum(1 for e in m.values() if e["widths"])
    total = sum(os.path.getsize(p) for p in glob.glob(os.path.join(root, OUT_DIR, "*"))
                if not p.endswith(".json"))
    print(f"  {n} photographs, {len(m) - n} other images; {OUT_DIR}/ is {total / 1048576:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1:])
