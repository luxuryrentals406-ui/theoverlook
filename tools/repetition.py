#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
How often each thing the estate offers is said on one page, and which
sentences appear word for word on more than one page.

    python3 tools/repetition.py            # the table, for reading
    (tools/lint.py imports offer_counts() and shared_sentences())

The owner's brief (2026-09-28): the site must not repeat itself, especially
about what the estate offers. Each offering gets one proper home per page;
a second mention has to be doing a different job. BUDGET is how many times a
page may state each one before lint fails it. Verbatim guest reviews are not
copy and are excluded; so is anything aria-hidden (the word strip's duplicate
run exists only to make the loop seamless).
"""
import os, re, html, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# the pages that sell; journal and legal pages are reference text
FUNNEL = ["index.html", "weddings.html", "retreats.html", "wellness.html", "estate.html",
          "overlook-wedding.html", "ultimate-wedding-weekend.html"]

OFFERINGS = {
    "15 acres":            r"\b(15|fifteen)[ -](private )?acres?\b",
    "200 guests":          r"(?<![\d,])\b200\b(?! ?AMP)(?!,000)",   # not 3,200 sq ft
    "sleeps 28":           r"\b(28|twenty-eight)\b",
    "3,200 sq ft pavilion": r"3,200",
    "40x80 tent":          r"40 ?[×x] ?80|forty by eighty",
    "200 AMP power":       r"200 ?AMP",
    "parking for 75":      r"\b75\b",
    "built-in bar":        r"built-in bar",
    "four head tables":    r"\b(four|4) head tables",
    "50 ft load-in":       r"\b50 (ft|feet)\b",
    "Starlink":            r"starlink",
    "heated pool":         r"heated pool",
    "hot tub":             r"hot tub",
    "sauna":               r"\bsauna\b",
    "putting green":       r"putting green",
    "fitness room":        r"fitness room",
    "fire pit":            r"fire pit",
    "one group at a time": r"one group|closed to everyone|no other (guests|events|party)|nobody else on",
    "five accommodations": r"five (accommodations|buildings|houses)",
    "venue coordinator":   r"coordinator",
    "private chef":        r"private chef",
    "airport drive":       r"\b35 min",
    "Glacier drive":       r"west glacier|west entrance",
    "Whitefish drive":     r"whitefish mountain resort",
    "helicopter":          r"helicopter(?!s\b)",   # not the company name, WestSlope Helicopters
}
BUDGET = 2
# the promise the whole site is built on may be made a third time
CORE = {"one group at a time": 3, "15 acres": 3}


def page_text(path):
    """Visible main-content text: no head, header, nav, footer, scripts,
    inquiry sheet, sticky bar, aria-hidden duplicates or guest reviews."""
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<(head|header|nav|footer|script|style)\b.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r'<div class="sheet".*?<!-- /inquire -->', " ", s, flags=re.S)   # the inquiry window
    s = re.sub(r'<div class="sbar".*?</div>\s*</div>', " ", s, flags=re.S)
    s = re.sub(r'<div class="mq__run" aria-hidden="true">.*?</div>', " ", s, flags=re.S)
    s = re.sub(r"<blockquote.*?</blockquote>|<cite.*?</cite>", " ", s, flags=re.S | re.I)
    s = re.sub(r'\salt="[^"]*"', " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def offer_counts(text):
    return {k: len(re.findall(rx, text, re.I)) for k, rx in OFFERINGS.items()}


def over_budget(text):
    out = []
    for k, n in offer_counts(text).items():
        cap = CORE.get(k, BUDGET)
        if n > cap:
            out.append((k, n, cap))
    return out


def shared_sentences(texts, min_len=50):
    """{sentence: [pages]} for any sentence of min_len+ characters that
    appears on more than one page."""
    seen = collections.defaultdict(set)
    for page, t in texts.items():
        for s in re.split(r"(?<=[.!?])\s+", t):
            s = s.strip()
            if len(s) >= min_len:
                seen[s].add(page)
    return {s: sorted(p) for s, p in seen.items() if len(p) > 1}


def main():
    texts = {p: page_text(os.path.join(ROOT, p)) for p in FUNNEL}
    print(f"{'':22s}" + "".join(f"{p.split('.')[0][:8]:>9s}" for p in FUNNEL))
    for k in OFFERINGS:
        row = [offer_counts(texts[p])[k] for p in FUNNEL]
        cap = CORE.get(k, BUDGET)
        flag = "  <-- over" if max(row) > cap else ""
        print(f"{k:22s}" + "".join(f"{n:9d}" for n in row) + flag)
    sh = shared_sentences(texts)
    print(f"\n{len(sh)} sentence(s) on more than one page")
    for s, ps in sh.items():
        print(f"  {ps}  {s[:100]}")


if __name__ == "__main__":
    main()
