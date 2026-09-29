#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copy-rule linter. Run after tools/build.py.

Checks the rules the rebuild was commissioned to enforce. Exits non-zero on a
violation so it can gate a deploy.
"""
import os, re, sys, glob, html as ihtml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS, WARNS = [], []

WEDDING_WORDS = ["ceremony", "bride", "groom", " ring ", "aisle", "bridal", "altar",
                 "wedding party", "honeymoon", "elopement"]
FILLER = ["unparalleled", "once-in-a-lifetime", "once in a lifetime", "magical",
          "breathtaking", "stunning", "nestled", "world-class"]

# Verbatim Google reviews — exempt from the exclamation-point and filler rules.
QUOTE_RE = re.compile(r"<blockquote.*?</blockquote>", re.S | re.I)

# Performance budget — see rule 7. INITIAL is what a 375px 2x phone fetches
# when the page opens: every eager image plus the lazy ones inside the
# browser's lazy-load margin (the old home page fetched 7,900 KB). TOTAL is
# what a reader who scrolls to the bottom eventually downloads; it only warns,
# because a 63-photograph gallery is allowed to be long.
import budget
INITIAL_BUDGET_KB = 600
TOTAL_WARN_KB = 3000
# Third parties a page may contact on load. Every host here must be named in
# the privacy policy. The beacon is Cloudflare Web Analytics (cookieless).
ALLOWED_HOSTS = {
    "*": {"static.cloudflareinsights.com"},
    "contact.html": {"static.cloudflareinsights.com", "www.google.com"},
}


def visible(path, strip_chrome=True):
    """Return page text with tags removed. strip_chrome drops nav + footer so the
    word 'Weddings' in the navigation doesn't trip the retreats check."""
    src = open(path, encoding="utf-8").read()
    if strip_chrome:
        src = re.sub(r"<header.*?</header>", " ", src, flags=re.S | re.I)
        src = re.sub(r"<nav.*?</nav>", " ", src, flags=re.S | re.I)
        src = re.sub(r"<footer.*?</footer>", " ", src, flags=re.S | re.I)
        src = re.sub(r"<head>.*?</head>", " ", src, flags=re.S | re.I)
        src = re.sub(r"<script.*?</script>", " ", src, flags=re.S | re.I)
    return src


def text_of(src):
    t = re.sub(r"<[^>]+>", " ", src)
    return re.sub(r"\s+", " ", ihtml.unescape(t))


def all_pages():
    """Every built page, including the directory-index pages two levels deep.

    The ported /journal and legal URLs are site copy like any other page, so
    they answer to the same rules; globbing the root only would have let six
    pages through unlinted.
    """
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in ("dist", "assets", "tools", ".git", ".claude")]
        for f in filenames:
            if f.endswith(".html"):
                out.append(os.path.join(dirpath, f))
    return sorted(out)


pages = all_pages()
if not pages:
    sys.exit("no pages built — run tools/build.py first")

site_text = ""
for p in pages:
    # the name a rule matches on is the path from the site root, so
    # "retreats.html" still means the corporate page and nothing else
    name = os.path.relpath(p, ROOT)
    src = visible(p)
    body = text_of(src)
    body_noquote = text_of(QUOTE_RE.sub(" ", src))
    low = body.lower()
    low_nq = body_noquote.lower()
    site_text += " " + low

    # 1 — retired phrases
    for phrase in ["begin your story", "your story awaits"]:
        if phrase in low:
            FAILS.append(f"{name}: retired phrase '{phrase}'")

    # 2 — sleeping capacity: the estate sleeps 28, and the corporate page does
    #     not discuss beds at all (owner's call, 2026-09-19 — the $100k two-estate
    #     package sleeping 56 is the same 28 counted twice)
    for m in re.finditer(r"(sleep\w*|accommodat\w*|capacity|overnight)\D{0,24}\b(24|12)\b", low):
        FAILS.append(f"{name}: stale sleeping capacity — '{m.group(0).strip()}'")
    if name == "retreats.html":
        for m in re.finditer(r"(sleeps?|sleeping|overnight|double occupancy|beds?)\b", low):
            FAILS.append(f"{name}: sleeping capacity on the corporate page — '{m.group(0)}'")

    # 2b — no published pricing anywhere (owner's call, 2026-09-19). Every
    #      booking is quoted directly, so a figure on the page is a regression.
    # The Overlook weekend and the two-estate weekend (owner set both 2026-09-28).
    ALLOWED_PRICES = {"$20,000", "$135,000"}
    # end the match on a digit: "[\d,]+" swallows the comma in "$20,000, and"
    for m in re.finditer(r"\$\s?[\d,]*\d", body):
        if m.group(0).strip() not in ALLOWED_PRICES:
            FAILS.append(f"{name}: published price — '{m.group(0).strip()}'")

    # 2c — no phone number anywhere (owner's call, 2026-09-28): email and the
    #      inquiry form are the only published contact routes.
    for m in re.finditer(r'tel:|"telephone"|\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b',
                         open(p, encoding="utf-8").read()):
        FAILS.append(f"{name}: published phone number — '{m.group(0)}'")

    # 3 — vocabulary separation
    if name == "retreats.html":
        for w in WEDDING_WORDS:
            if w in low:
                FAILS.append(f"{name}: wedding vocabulary '{w.strip()}' on the corporate page")
    if name == "weddings.html":
        for w in ["meeting space", "general session", "breakout", "offsite"]:
            if w in low:
                FAILS.append(f"{name}: corporate vocabulary '{w}' on the wedding page")

    # 4 — filler, max one per page (quotes exempt)
    for w in FILLER:
        n = low_nq.count(w)
        if n > 1:
            FAILS.append(f"{name}: filler '{w}' x{n} (max 1)")
        elif n == 1:
            WARNS.append(f"{name}: filler '{w}' used once")

    # 5 — exclamation points outside real reviews
    n_excl = body_noquote.count("!")
    if n_excl:
        FAILS.append(f"{name}: {n_excl} exclamation point(s) outside quoted reviews")

    # 6 — SEO basics
    raw = open(p, encoding="utf-8").read()
    title = re.search(r"<title>(.*?)</title>", raw, re.S)
    desc = re.search(r'name="description" content="(.*?)"', raw, re.S)
    if not title:
        FAILS.append(f"{name}: no <title>")
    elif not (15 <= len(title.group(1)) <= 70):
        WARNS.append(f"{name}: title is {len(title.group(1))} chars (aim 15–70)")
    if not desc:
        FAILS.append(f"{name}: no meta description")
    elif not (70 <= len(desc.group(1)) <= 170):
        WARNS.append(f"{name}: meta description is {len(desc.group(1))} chars (aim 70–170)")
    for m in re.finditer(r'"price[A-Za-z]*"\s*:\s*"?([\d,]+)', raw):
        if m.group(1) not in ("20000", "135000"):
            FAILS.append(f"{name}: price in structured data — '{m.group(0)[:40]}'")
    if raw.count("<h1") > 1:
        WARNS.append(f"{name}: {raw.count('<h1')} <h1> tags")
    for m in re.finditer(r"<img (?![^>]*\balt=)[^>]*>", raw):
        FAILS.append(f"{name}: <img> without alt — {m.group(0)[:60]}")

    # 7 — performance budget (mobile-first rebuild, 2026-09-28). Most visitors
    #     are on phones: a page must not regress to full-size photographs, an
    #     <img> without dimensions (layout shift) or a third-party request the
    #     privacy policy does not mention. The byte figure is what a 375px 2x
    #     phone fetches for every image on the page; it tightens in Phase 2.
    kb = budget.initial_image_bytes(raw, ROOT) / 1024
    if kb > INITIAL_BUDGET_KB:
        FAILS.append(f"{name}: {kb:.0f} KB of images on open at phone width (budget {INITIAL_BUDGET_KB})")
    total_kb = budget.phone_image_bytes(raw, ROOT) / 1024
    if total_kb > TOTAL_WARN_KB:
        WARNS.append(f"{name}: {total_kb:.0f} KB of images if scrolled to the end")
    for host in budget.external_requests(raw):
        if host not in ALLOWED_HOSTS.get(name, ALLOWED_HOSTS["*"]):
            FAILS.append(f"{name}: third-party request to {host}")
    for tag in budget.imgs_missing_dims(raw):
        FAILS.append(f"{name}: image without width/height or srcset — {tag}")

# 2c, llms.txt — the assistant brief is contact copy too
_llms = os.path.join(ROOT, "llms.txt")
if os.path.exists(_llms) and re.search(r'\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b',
                                       open(_llms, encoding="utf-8").read()):
    FAILS.append("llms.txt: published phone number")

# 6b — the deploy config must not contradict the sitemap. A redirect whose
#      source is a real, indexed page makes that page unreachable, and a page
#      directory that render.yaml never copies is simply missing after deploy.
rl = os.path.join(ROOT, "render.yaml")
if os.path.exists(rl):
    cfg = open(rl, encoding="utf-8").read()
    sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    indexed = {u.replace("https://theoverlookatflatheadlake.com", "").rstrip("/") or "/"
               for u in re.findall(r"<loc>(.*?)</loc>", sm)}
    for src in re.findall(r"source: (\S+)", cfg):
        if src.rstrip("/") in indexed:
            FAILS.append(f"render.yaml: redirects {src}, but it is an indexed page")
    m = re.search(r"cp -R ([^\n]*?) dist/", cfg)
    copied = set(m.group(1).split()) if m else set()
    for u in indexed:
        top = u.strip("/").split("/")[0]
        if not top or top.endswith(".html"):
            continue
        if top not in copied:
            FAILS.append(f"render.yaml: /{top} is indexed but never copied into dist/")

# 7 — site-wide 'dream' budget
n_dream = len(re.findall(r"\bdream", site_text))
if n_dream > 1:
    FAILS.append(f"site-wide: 'dream' appears {n_dream}x (max 1)")

# ---------------------------------------------------------------- report
# 8 — the site does not repeat itself (owner's brief, 2026-09-28). Each thing
#     the estate offers has one home per page; tools/repetition.py holds the
#     list and the budget. Guest reviews and aria-hidden text are exempt.
import repetition
_texts = {}
for _p in repetition.FUNNEL:
    _full = os.path.join(ROOT, _p)
    if not os.path.exists(_full):
        continue
    _texts[_p] = repetition.page_text(_full)
    for _k, _n, _cap in repetition.over_budget(_texts[_p]):
        FAILS.append(f"{_p}: says '{_k}' {_n} times (max {_cap}) — give it one home on the page")
for _s, _ps in repetition.shared_sentences(_texts).items():
    FAILS.append(f"same sentence on {', '.join(_ps)}: '{_s[:70]}…'")

print(f"\n  linted {len(pages)} pages\n")
for w in WARNS:
    print(f"  warn  {w}")
if WARNS:
    print()
if FAILS:
    for f in FAILS:
        print(f"  FAIL  {f}")
    print(f"\n  {len(FAILS)} violation(s)\n")
    sys.exit(1)
print("  all copy rules pass\n")
