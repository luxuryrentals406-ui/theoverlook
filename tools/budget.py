#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance budget checks for tools/lint.py.

Pure functions over a page's HTML so they can be tested without building the
site. The question each one answers:

  phone_image_bytes   how many bytes of images does a phone (375px, 2x) fetch
                      for this page, counting every <picture> and <img>
  external_requests   which third-party hosts does the page contact on load
  imgs_missing_dims   which <img> tags lack width/height (layout shift) or,
                      for photographs, a srcset (full-size file on a phone)
"""
import os, re

PHONE_CSS_PX = 375
PHONE_DPR = 2
PHONE_NEED = PHONE_CSS_PX * PHONE_DPR          # 750 device pixels across

PICTURE_RE = re.compile(r"<picture>(.*?)</picture>", re.S)
SOURCE_RE = re.compile(r"<source\b[^>]*>")
IMG_RE = re.compile(r"<img\b[^>]*>")
ATTR_RE = re.compile(r'\b([a-zA-Z-]+)="([^"]*)"')


def attrs(tag):
    return dict(ATTR_RE.findall(tag))


def _local(root, ref):
    """assets/i/x.avif or ../../assets/i/x.avif -> absolute path under root."""
    ref = ref.split("?")[0].split("#")[0]
    while ref.startswith("../"):
        ref = ref[3:]
    return os.path.join(root, ref)


def _size(root, ref):
    try:
        return os.path.getsize(_local(root, ref))
    except OSError:
        return 0


def _need(sizes):
    """Device pixels a 375px 2x phone needs for an image with this `sizes`.
    Only min-width conditions occur in this site; none match at 375px, so the
    last, unconditional entry applies: '50vw' -> 187.5 CSS px -> 375 device px."""
    entry = sizes.split(",")[-1].strip() if sizes else "100vw"
    val = entry.split()[-1]
    if val.endswith("vw"):
        css = PHONE_CSS_PX * float(val[:-2]) / 100
    elif val.endswith("px"):
        css = float(val[:-2])
    else:
        css = PHONE_CSS_PX
    return css * PHONE_DPR


def _pick(srcset, need=PHONE_NEED):
    """The candidate the phone takes: the smallest width that covers `need`
    device pixels, or the widest on offer if none does."""
    cands = []
    for part in srcset.split(","):
        bits = part.strip().split()
        if len(bits) == 2 and bits[1].endswith("w"):
            cands.append((int(bits[1][:-1]), bits[0]))
    if not cands:
        return None
    cands.sort()
    for w, url in cands:
        if w >= need:
            return url
    return cands[-1][1]


# A phone shows one hero frame; the stylesheet keeps the others display:none,
# and a display:none <picture> is never fetched. Only the first frame carries
# is-on in the markup, so the plain ones are the ones to drop.
EXTRA_FRAME_RE = re.compile(r'<div class="hero__frame">.*?</div>', re.S)


def images(html):
    """Every image on the page in document order, as (url_the_phone_fetches,
    lazy). A <picture> resolves to its phone AVIF candidate; a plain <img> to
    its src. Data URIs, empty slots and remote images are skipped."""
    out = []
    html = EXTRA_FRAME_RE.sub(" ", html)
    for m in re.finditer(r"<picture>.*?</picture>|<img\b[^>]*>", html, re.S):
        tag = m.group(0)
        if tag.startswith("<picture"):
            sources = [attrs(s) for s in SOURCE_RE.findall(tag)]
            avif = [s for s in sources if s.get("type") == "image/avif"]
            phone = [s for s in avif if "max-width" in s.get("media", "")]
            chosen = (phone or avif or sources)[:1]
            im = IMG_RE.search(tag)
            a = attrs(im.group(0)) if im else {}
            url = _pick(chosen[0].get("srcset", ""), _need(chosen[0].get("sizes", ""))) if chosen else None
            url = url or a.get("src")
        else:
            a = attrs(tag)
            url = a.get("src", "")
            if a.get("srcset"):
                url = _pick(a["srcset"], _need(a.get("sizes", ""))) or url
        if not url or url.startswith("data:") or url.startswith("http"):
            continue
        out.append((url, a.get("loading") == "lazy"))
    return out


def phone_image_bytes(html, root):
    """Bytes of every image on the page, at the sizes a phone takes — what a
    reader who scrolls to the bottom eventually downloads."""
    return sum(_size(root, url) for url, _ in images(html))


NEAR_FOLD = 4   # lazy images inside ~two phone screens of the top


def initial_image_bytes(html, root, near=NEAR_FOLD):
    """Bytes a phone fetches when the page opens: every eager image plus the
    first `near` lazy ones, which sit within the browser's lazy-load margin
    and are fetched before anyone scrolls."""
    total, lazy_seen = 0, 0
    for url, lazy in images(html):
        if lazy:
            lazy_seen += 1
            if lazy_seen > near:
                continue
        total += _size(root, url)
    return total


LOAD_TAGS = re.compile(r"<(link|script|img|iframe|source)\b[^>]*>", re.I)


def external_requests(html):
    """Hosts a page contacts on load, from link/script/img/iframe/source tags.
    Only stylesheets and preloads count among <link>s; canonical and og
    links are not fetched."""
    hosts = []
    for m in LOAD_TAGS.finditer(html):
        tag, a = m.group(1).lower(), attrs(m.group(0))
        if tag == "link":
            rel = a.get("rel", "").lower()
            if not any(r in rel for r in ("stylesheet", "preload", "preconnect", "modulepreload")):
                continue
        url = a.get("src") or a.get("href") or ""
        mm = re.match(r"https?://([^/]+)", url)
        if mm:
            hosts.append(mm.group(1).lower())
    return sorted(set(hosts))


def imgs_missing_dims(html):
    """<img> tags with a real src that lack width/height, plus photographs
    (jpg/avif/webp) that lack a srcset. Returns short tag excerpts."""
    bad = []
    for tag in IMG_RE.findall(html):
        a = attrs(tag)
        src = a.get("src", "")
        if not src or src.startswith("data:"):
            continue                       # the empty lightbox slot
        if not (a.get("width") and a.get("height")):
            bad.append(tag[:70])
            continue
        if re.search(r"\.(jpe?g|avif|webp)$", src.split("?")[0], re.I) and not a.get("srcset"):
            bad.append(tag[:70])
    return bad
