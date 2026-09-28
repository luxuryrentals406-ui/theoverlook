#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-host the two typefaces.

    python3 tools/fonts.py            # fetch what is missing
    python3 tools/fonts.py --force    # refetch everything

Asks Google Fonts for the woff2 CSS the way a modern browser would, keeps only
the latin subset of each face, downloads those files into assets/fonts/ and
writes assets/fonts/fonts.css with @font-face rules that point at them.
The output is committed; the site never contacts fonts.googleapis.com.
"""
import os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "fonts")
CSS_URL = ("https://fonts.googleapis.com/css2?"
           "family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400"
           "&family=Jost:wght@200;300;400&display=swap")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
SLUG = {"Cormorant Garamond": "cormorant", "Jost": "jost"}

FACE_RE = re.compile(r"@font-face\s*{(.*?)}", re.S)


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def parse_faces(css):
    """Yield dicts for every latin @font-face block in Google's CSS."""
    for block in FACE_RE.findall(css):
        def prop(name):
            m = re.search(name + r"\s*:\s*([^;]+);", block)
            return m.group(1).strip() if m else ""
        rng = prop("unicode-range")
        if not rng.startswith("U+0000-00FF"):
            continue  # latin-ext, cyrillic, vietnamese — the site is English
        url = re.search(r"url\(([^)]+)\)", prop("src")).group(1)
        yield {"family": prop("font-family").strip('"\''), "style": prop("font-style"),
               "weight": prop("font-weight"), "url": url, "range": rng}


def merge_variable(faces):
    """Google serves one variable-weight file per family and style, listed
    once per requested weight. Collapse those into one face with a weight
    range so the file is fetched and declared once."""
    by_url = {}
    for f in faces:
        g = by_url.setdefault(f["url"], dict(f, weights=[]))
        g["weights"].append(int(f["weight"]))
    out = []
    for g in by_url.values():
        lo, hi = min(g["weights"]), max(g["weights"])
        g["weight"] = str(lo) if lo == hi else "%d %d" % (lo, hi)
        out.append(g)
    return sorted(out, key=lambda g: (g["family"], g["style"]))


def filename(face):
    return "%s%s.woff2" % (SLUG[face["family"]], "-i" if face["style"] == "italic" else "")


def face_css(face):
    return ("@font-face{font-family:\"%s\";font-style:%s;font-weight:%s;font-display:swap;"
            "src:url(%s) format(\"woff2\");unicode-range:%s}"
            % (face["family"], face["style"], face["weight"], filename(face), face["range"]))


def main(force=False):
    os.makedirs(OUT, exist_ok=True)
    faces = merge_variable(parse_faces(_get(CSS_URL).decode("utf-8")))
    if not faces:
        sys.exit("no latin @font-face blocks found — did Google change the CSS?")
    keep = {filename(f) for f in faces} | {"fonts.css"}
    for stale in os.listdir(OUT):
        if stale not in keep:
            os.remove(os.path.join(OUT, stale))
    for f in faces:
        dest = os.path.join(OUT, filename(f))
        if force or not os.path.exists(dest):
            with open(dest, "wb") as fh:
                fh.write(_get(f["url"]))
            print("  fetched", filename(f))
    with open(os.path.join(OUT, "fonts.css"), "w", encoding="utf-8") as fh:
        fh.write("/* Self-hosted latin subsets. Regenerate with tools/fonts.py */\n")
        fh.write("\n".join(face_css(f) for f in faces) + "\n")
    total = sum(os.path.getsize(os.path.join(OUT, p)) for p in os.listdir(OUT))
    print("  %d faces, assets/fonts/ is %d KB" % (len(faces), total // 1024))


if __name__ == "__main__":
    main(force="--force" in sys.argv)
