# -*- coding: utf-8 -*-
"""Shared chrome for The Overlook site: <head>, header, footer, components.

Everything that must stay identical across pages lives here so no page can
drift. Page bodies live in build.py.
"""

import hashlib
import os
import re
import struct

SITE = "https://theoverlookatflatheadlake.com"

BIZ = {
    "name":    "The Overlook at Flathead Lake",
    "city":    "Lakeside",
    "state":   "MT",
    "region":  "Montana",
    "phone":   "(406) 885-6064",
    "tel":     "+14068856064",
    "email":   "theoverlook@luxurylodgingvip.com",
    "ig":      "https://www.instagram.com/theoverlookatflatheadlake",
    # The sister brand's handle carries a dot. Verified against the account and
    # against the old site's own sameAs block — the dotless spelling 404s.
    "ig_sis":  "https://www.instagram.com/flatheadlake.luxurylodging",
    "fb":      "https://www.facebook.com/61584158843820",
    "handle":  "@theoverlookatflatheadlake",
}

NAV = [
    ("weddings.html", "Weddings"),
    ("retreats.html", "Corporate Retreats"),
    ("wellness.html", "Wellness"),
    ("estate.html",   "The Estate"),
    ("gallery.html",  "Gallery"),
    ("story.html",    "Our Story"),
]

# Inline so the page can never be stranded behind the transition veil: the
# veil is only allowed to exist once this has run and can also remove it.
# The browser keeps its own scroll restoration: the back button lands where the
# reader left, which on a phone is the whole point of the back button.
BOOT = ('<script>(function(d,w){var h=d.documentElement;h.className+=" js";'
        'var go=function(){h.classList.add("is-ready");};'
        'd.addEventListener("DOMContentLoaded",go);'
        'setTimeout(go,2500);})'
        '(document,window);</script>')


IMG  = "assets/img/"
THMB = "assets/thumb/"

# Drive times. Every statement of one on this site interpolates from here —
# prose, spec lists, the FAQ, llms.txt and the travel guide — so changing a
# figure changes it everywhere, which is the only version of "stated once" that
# is worth anything.
#
# Verified 2026-09-20: Glacier. West Glacier is the park's west entrance and the
# nearest way in, 49 miles out, which is not a 45-minute drive at any legal
# speed on US-93 through Kalispell and Columbia Falls; an independent routing
# check puts it at 1 h 02. The old site's "45 minutes to Glacier National Park"
# was wrong and is gone.
#
# NOT verified: FCA and Whitefish. Both are carried from FACTS.md as published.
# The Whitefish figure looks short — Lakeside to Whitefish town is roughly 30
# miles, and Big Mountain Road adds another 5 to 6 up to the resort — so "about
# 45 minutes" may describe the town rather than the ski hill. Eric's to confirm;
# it is one edit here when he does.
DRIVE = {
    "fca": {
        "name":  "Glacier Park International Airport (FCA)",
        "short_name": "Glacier Park International Airport",
        "time":  "35 minutes",          # "… is 35 minutes from the estate"
        "brief": "35 min",              # spec lists
        "drive": "a 35-minute drive",
    },
    "whitefish": {
        "name":  "Whitefish Mountain Resort",
        "time":  "about 45 minutes",
        "brief": "45 min",
    },
    "glacier": {
        "name":     "Glacier National Park",
        "entrance": "West Glacier",
        "time":     "about an hour",
        "brief":    "1 hr",
        "drive":    "roughly a one-hour drive",
        "miles":    "49 miles",
    },
}

FCA, WHITEFISH, GLACIER = DRIVE["fca"], DRIVE["whitefish"], DRIVE["glacier"]


def cap(s):
    """First letter up, for a table cell. 'about an hour' -> 'About an hour'."""
    return s[:1].upper() + s[1:]


def rel(path):
    """Prefix that turns a root-relative path into a link from a page at `path`.

    "weddings.html"                 -> ""
    "privacy/index.html"            -> "../"
    "journal/<slug>/index.html"     -> "../../"

    Every link and every asset on a page is written as prefix + path-from-root,
    never as a traversal from where the reader happens to be. That is what makes
    the extensionless URLs safe: a host may serve /journal/<slug> or
    /journal/<slug>/, and the two resolve relative links differently, but
    "../../assets/x" lands on /assets/x under both because the browser clamps at
    the root. A shortcut like "../other-slug" would not.
    """
    return "../" * path.count("/")


# ------------------------------------------------------------------ helpers
def _ver(relpath):
    """Content hash appended to css/js URLs so a deploy is never served stale."""
    full = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relpath)
    try:
        with open(full, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except OSError:
        return "1"


_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def imgsize(relpath):
    """(width, height) of a JPEG or PNG, or None. No dependencies.

    Used for og:image:width/height: without them Facebook and LinkedIn render a
    small card on the first scrape of a URL they have never seen — which is every
    URL on this site, the week it launches.
    """
    full = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relpath)
    try:
        with open(full, "rb") as f:
            d = f.read(2 << 20)
    except OSError:
        return None
    if d[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", d[16:24])
    if d[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(d):
        if d[i] != 0xFF:
            i += 1
            continue
        m = d[i + 1]
        if m in _SOF:
            h, w = struct.unpack(">HH", d[i + 5:i + 9])
            return w, h
        if m == 0xD8 or m == 0xD9 or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    return None


DERIV = "assets/i/"

# `sizes` presets — how wide the photograph renders, so the browser can pick
# the smallest candidate that is still sharp. Phones are the default case.
SZ_FULL    = "100vw"
SZ_HALF    = "(min-width:861px) 50vw, 100vw"
SZ_THIRD   = "(min-width:861px) 33vw, 100vw"
SZ_GALLERY = "(min-width:861px) 33vw, 50vw"
SZ_THUMB   = "(min-width:861px) 8vw, 20vw"
PHONE_MAX  = 800      # widest derivative a phone is offered for anything but the hero

_MANIFEST = None


def manifest():
    """assets/i/manifest.json, read once. tools/images.py writes it; build.py
    runs that first, so a photograph missing here is a real mistake."""
    global _MANIFEST
    if _MANIFEST is None:
        import images
        _MANIFEST = images.load_manifest(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return _MANIFEST


def _entry(name):
    try:
        return manifest()[name]
    except KeyError:
        raise KeyError(f"{name}: not in {DERIV}manifest.json — run python3 tools/images.py")


def _candidates(name, widths, ext, base, orig_w):
    stem = os.path.splitext(name)[0]
    out = []
    for w in widths:
        if ext == "jpg" and w == orig_w:
            out.append(f"{base}{IMG}{name} {w}w")      # the original is the JPEG at its own width
        else:
            out.append(f"{base}{DERIV}{stem}-{w}.{ext} {w}w")
    return ", ".join(out)


def _srcsets(name, e, base, thumb):
    import images
    widths = [w for w in e["widths"] if w <= 800] if thumb else e["widths"]
    avif = _candidates(name, widths, "avif", base, e["w"])
    webp = _candidates(name, [w for w in widths if w <= images.WEBP_MAX], "webp", base, e["w"])
    jpg_w = [w for w in widths if w <= images.JPEG_MAX]
    if not thumb and e["w"] not in jpg_w:
        jpg_w = jpg_w + [e["w"]]                        # the original tops the JPEG list
    jpg = _candidates(name, jpg_w, "jpg", base, e["w"])
    return avif, webp, jpg


def img(name, alt, cls="", eager=False, sizes=None, base="", thumb=False):
    """A photograph as <picture> — AVIF, WebP, JPEG — with srcset, real
    width/height and an inline blurred placeholder; a PNG as a plain <img>.

    eager: True  -> loading="eager" fetchpriority="high"  (the hero frame)
           None  -> no loading hints                      (logos in the chrome)
           False -> loading="lazy" decoding="async"       (everything else)
    thumb: cap candidates at 800px for grids of small tiles.
    """
    e = _entry(name)
    c = f' class="{cls}"' if cls else ""
    if eager is True:
        load = ' loading="eager" fetchpriority="high"'
    elif eager is None:
        load = ""
    else:
        load = ' loading="lazy" decoding="async"'
    dims = f' width="{e["w"]}" height="{e["h"]}"'
    if not e["widths"]:
        return f'<img src="{base}{IMG}{name}" alt="{alt}"{c}{dims}{load}>'
    sz = sizes or SZ_FULL
    avif, webp, jpg = _srcsets(name, e, base, thumb)
    ph = f" style=\"background:url('{e['lqip']}') center/cover\"" if e["lqip"] else ""
    # A phone caps at the 800px file even on a 3x screen: the difference is
    # invisible in a card, and it is the difference between a page that loads
    # on cellular and one that does not. The hero (eager) is exempt.
    phone = ""
    if eager is not True and not thumb and any(w > PHONE_MAX for w in e["widths"]):
        p_avif, p_webp, _ = _srcsets(name, e, base, True)
        phone = (f'<source type="image/avif" media="(max-width:640px)" srcset="{p_avif}" sizes="{sz}">'
                 f'<source type="image/webp" media="(max-width:640px)" srcset="{p_webp}" sizes="{sz}">')
    return (f'<picture>{phone}'
            f'<source type="image/avif" srcset="{avif}" sizes="{sz}">'
            f'<source type="image/webp" srcset="{webp}" sizes="{sz}">'
            f'<img src="{base}{IMG}{name}" srcset="{jpg}" sizes="{sz}" alt="{alt}"{c}{dims}{load}{ph}>'
            f'</picture>')


def hero_preload(name, base="", sizes=SZ_FULL):
    """Preload the hero at the width this device will actually use. Browsers
    that cannot decode AVIF ignore a preload of that type and simply fetch
    the <picture> fallback in the normal flow."""
    e = _entry(name)
    avif, _, _ = _srcsets(name, e, base, False)
    return (f'<link rel="preload" as="image" type="image/avif" imagesrcset="{avif}" '
            f'imagesizes="{sizes}" fetchpriority="high">')


def eyebrow(t):
    return f'<span class="eyebrow">{t}</span>'


def btn(href, label, cls="btn"):
    """A button-styled link. One that points at the contact page also carries
    data-sheet, so with JS the inquiry sheet opens in place (prefilled from
    ?type=) and without JS the link still goes where it says."""
    sheet = ""
    m = re.match(r"(?:\.\./)*contact\.html(?:\?type=(\w+))?$", href)
    if m:
        sheet = f' data-sheet="{m.group(1) or ""}"'
    return f'<a class="{cls}" href="{href}"{sheet}>{label}</a>'


def tlink(href, label):
    return f'<a class="tlink" href="{href}">{label} <span>&rarr;</span></a>'


def plist(items):
    li = "".join(f"<li>{i}</li>" for i in items)
    return f'<ul class="plist">{li}</ul>'


def ilist(items):
    li = "".join(f"<li>{i}</li>" for i in items)
    return f'<ul class="ilist">{li}</ul>'


def quote(text, who, role):
    return f"""<div class="quote rv">
        <blockquote>&ldquo;{text}&rdquo;</blockquote>
        <cite><b>{who}</b>{role}</cite>
      </div>"""


def faq(items):
    """items: list of (question, answer_html)"""
    out = ['<div class="acc">']
    for i, (q, a) in enumerate(items):
        out.append(f"""<div class="acc__item">
          <h3><button class="acc__q" aria-expanded="false" id="q{i}">{q}</button></h3>
          <div class="acc__a" role="region" aria-labelledby="q{i}"><div>{a}</div></div>
        </div>""")
    out.append("</div>")
    return "".join(out)


def lines(text):
    """Split a headline on <br> so each line can rise in on its own beat."""
    parts = [p.strip() for p in re.split(r"<br\s*/?>", text) if p.strip()]
    return "".join(
        f'<span class="ln" style="--ln:{i}">{p}</span>' for i, p in enumerate(parts))


def hero(image, alt, eyeb, h1, sub, ctas="", extra="", short=False, slides=None):
    """slides: extra (image, alt) pairs that cross-fade behind the headline.

    With JS off the first frame simply stays put, so the hero still reads.
    """
    cls = "hero hero--short" if short else "hero"
    frames = [(image, alt)] + list(slides or [])
    stack = "".join(
        f'<div class="hero__frame{" is-on" if i == 0 else ""}">'
        f'{img(src, a, eager=(i == 0))}</div>'
        for i, (src, a) in enumerate(frames))
    dots = ""
    if len(frames) > 1:
        dots = ('<div class="hero__dots" role="tablist" aria-label="Hero views">' +
                "".join(f'<button class="hero__dot{" is-on" if i == 0 else ""}" '
                        f'data-i="{i}" role="tab" aria-selected="{"true" if i == 0 else "false"}" '
                        f'aria-label="View {i + 1}"></button>'
                        for i in range(len(frames))) + "</div>")
    cue = "" if short else """<div class="cue" aria-hidden="true"><span>Scroll</span><i></i></div>"""
    return f"""<section class="{cls}" data-parallax>
    <div class="hero__bg{' hero__bg--multi' if len(frames) > 1 else ''}">{stack}</div>
    <div class="wrap hero__in">
      {eyebrow(eyeb)}
      <h1>{lines(h1)}</h1>
      <p class="hero__sub">{sub}</p>
      {f'<div class="hero__cta">{ctas}</div>' if ctas else ''}
      {extra}
    </div>
    {dots}
    {cue}
  </section>"""


def band(image, alt, h2, lede, ctas, base=""):
    return f"""<section class="sect band">
    <div class="band__bg" data-drift>{img(image, alt, base=base)}</div>
    <div class="wrap wrap--narrow rv">
      <h2>{h2}</h2>
      <p class="lede" style="margin-top:1.4rem">{lede}</p>
      <div class="hero__cta" style="justify-content:center">{ctas}</div>
    </div>
  </section>"""


def split(media_html, body_html, flip=False, wide=False):
    cls = "split"
    if flip:
        cls += " split--flip"
    if wide:
        cls += " split--wide-img"
    return f"""<div class="{cls}">
      <div class="split__media rv rv--wipe">{media_html}</div>
      <div class="split__body rv">{body_html}</div>
    </div>"""


# ------------------------------------------------------------------ interactive
def vmap(base, alt, eyeb, title, lede, spots):
    """Interactive plan-view map. spots: (x%, y%, label, title, body, photo, photo_alt).

    Works without JS: every panel is rendered in the DOM and simply stacks.
    """
    pins, panels = "", ""
    for i, (x, y, label, t, body, photo, palt) in enumerate(spots):
        sel = ' aria-selected="true"' if i == 0 else ' aria-selected="false"'
        pins += (f'<button class="vmap__pin" role="tab"{sel} id="pin{i}" '
                 f'aria-controls="panel{i}" style="left:{x}%;top:{y}%" '
                 f'data-i="{i}"><span class="vmap__dot"></span>'
                 f'<span class="vmap__tag">{label}</span></button>')
        hide = "" if i == 0 else " hidden"
        panels += (f'<div class="vmap__panel" role="tabpanel" id="panel{i}" '
                   f'aria-labelledby="pin{i}"{hide}>'
                   f'<div class="vmap__shot">{img(photo, palt, sizes=SZ_THIRD)}</div>'
                   f'<div class="vmap__copy"><span class="vmap__step">{label}</span>'
                   f'<h3>{t}</h3><p>{body}</p></div></div>')
    return f"""<div class="vmap">
      <div class="vmap__head rv">
        {eyebrow(eyeb)}<h2>{title}</h2>
        <p class="lede" style="margin-top:1.3rem;max-width:56ch">{lede}</p>
      </div>
      <div class="vmap__grid">
        <div class="vmap__stage rv">
          {img(base, alt, "vmap__base", sizes=SZ_HALF)}
          <div class="vmap__pins" role="tablist" aria-label="Points on the property">{pins}</div>
        </div>
        <div class="vmap__panels rv">{panels}</div>
      </div>
      <p class="vmap__hint">Select a marker to move through the evening.</p>
    </div>"""


def marquee(items):
    """A slow single line of place names. Duplicated once so the loop is seamless."""
    run = "".join(f'<span>{i}</span><i aria-hidden="true">&bull;</i>' for i in items)
    return f"""<div class="mq" aria-label="{', '.join(items)}">
      <div class="mq__track">
        <div class="mq__run">{run}</div>
        <div class="mq__run" aria-hidden="true">{run}</div>
      </div>
    </div>"""


def getting_here():
    """Where the estate sits, relative to Lakeside and the airport.

    The map is centred on Lakeside rather than the estate itself — this is a
    private property and the exact pin is not published.
    """
    legs = [(FCA["name"], cap(FCA["time"])),
            (WHITEFISH["name"], cap(WHITEFISH["time"])),
            (f"{GLACIER['name']} ({GLACIER['entrance']})", cap(GLACIER["time"]))]
    li = "".join(f'<li><span>{a}</span><b>{b}</b></li>' for a, b in legs)
    return f"""<section class="sect sect--paper2" id="getting-here">
    <div class="wrap">
      <div class="split split--wide-img">
        <div class="split__media rv rv--wipe">
          <div class="map">
            <iframe
              src="https://www.google.com/maps?q=Lakeside,+Montana&amp;z=10&amp;output=embed"
              title="Map of Lakeside, Montana on the west shore of Flathead Lake"
              loading="lazy" referrerpolicy="no-referrer-when-downgrade"
              allowfullscreen></iframe>
          </div>
          <p class="map__note">Lakeside sits on the west shore of Flathead Lake. We send
            the gate code and exact directions once a date is held.</p>
        </div>
        <div class="split__body rv">
          {eyebrow("Getting here")}
          <h2>On the west shore,<br>above Lakeside</h2>
          <p class="lede" style="margin-top:1.3rem">Fifteen acres on the hillside above
            Lakeside, Montana &mdash; close enough that guests can be on the property
            within an hour of landing, far enough that the road noise never reaches you.</p>
          <ul class="legs">{li}</ul>
          {tlink("contact.html", "Ask about a site visit")}
        </div>
      </div>
    </div>
  </section>"""


def switcher(eyeb, title, lede, groups):
    """A place picker: choose a building, its photographs load into the stage.

    groups: (name, sub, body, [(image, alt), ...])
    Without JS every panel renders in sequence, so the page still tells the
    whole story — it just stops being a picker.
    """
    tabs, panels = "", ""
    for i, (name, sub, body, shots) in enumerate(groups):
        on = i == 0
        tabs += (f'<button class="sw__tab{" is-on" if on else ""}" role="tab" '
                 f'aria-selected="{"true" if on else "false"}" aria-controls="sw{i}" '
                 f'id="swtab{i}" data-i="{i}"><b>{name}</b><span>{sub}</span></button>')
        # every shot sits in the stage, one shown at a time; a thumbnail only
        # toggles which, so no image URL is ever swapped by hand
        big = "".join(
            f'<div class="sw__shot{" is-on" if j == 0 else ""}" data-j="{j}"{"" if j == 0 else " hidden"}>'
            f'{img(f, a, "sw__big", sizes=SZ_HALF)}</div>'
            for j, (f, a) in enumerate(shots))
        thumbs = ""
        if len(shots) > 1:
            thumbs = '<div class="sw__thumbs">' + "".join(
                f'<button class="sw__thumb{" is-on" if j == 0 else ""}" data-j="{j}" '
                f'aria-label="{a}">{img(f, "", thumb=True, sizes=SZ_THUMB)}</button>'
                for j, (f, a) in enumerate(shots)) + "</div>"
        panels += (f'<div class="sw__panel" role="tabpanel" id="sw{i}" '
                   f'aria-labelledby="swtab{i}"{"" if on else " hidden"}>'
                   f'<div class="sw__stage">{big}</div>'
                   f'<div class="sw__meta"><h3>{name}</h3><p>{body}</p></div>'
                   f'{thumbs}</div>')
    return f"""<div class="sw">
      <div class="sw__head rv">
        {eyebrow(eyeb)}<h2>{title}</h2>
        <p class="lede" style="margin-top:1.3rem;max-width:58ch">{lede}</p>
      </div>
      <div class="sw__grid">
        <div class="sw__tabs rv" role="tablist" aria-label="Places to stay">{tabs}</div>
        <div class="sw__panels rv">{panels}</div>
      </div>
    </div>"""


def rail(eyeb, title, lede, items):
    """A photo rail you drag. items: (image, alt, caption)

    It is a plain scroll container, so a trackpad, a touch screen, the arrow
    buttons and the keyboard all move it without any of them being special-cased.
    """
    cards = "".join(
        f'<figure class="rail__item"><div class="rail__shot">{img(f, a)}</div>'
        f'<figcaption>{c}</figcaption></figure>' for f, a, c in items)
    return f"""<section class="sect rail">
    <div class="wrap rail__head rv">
      <div>{eyebrow(eyeb)}<h2>{title}</h2></div>
      <div class="rail__side">
        <p class="lede" style="max-width:44ch">{lede}</p>
        <div class="rail__nav">
          <button class="rail__btn" data-dir="-1" aria-label="Previous photographs">&lsaquo;</button>
          <button class="rail__btn" data-dir="1" aria-label="Next photographs">&rsaquo;</button>
        </div>
      </div>
    </div>
    <div class="rail__track" tabindex="0" role="group" aria-label="{title} — drag or use the arrow keys">
      <div class="rail__pad" aria-hidden="true"></div>
      {cards}
      <div class="rail__pad" aria-hidden="true"></div>
    </div>
    <div class="wrap"><div class="rail__bar" aria-hidden="true"><i></i></div></div>
  </section>"""


def mosaic(items):
    """Panels that open as you move across them. items: (image, alt, label)"""
    cells = "".join(
        f'<button class="mos__cell{" is-on" if i == 0 else ""}" data-i="{i}">'
        f'{img(f, a)}<span class="mos__label">{l}</span></button>'
        for i, (f, a, l) in enumerate(items))
    return f'<div class="mos rv">{cells}</div>'


# The live HoneyBook lead form. Submissions land as real inquiries — project
# created, pipeline stage set, auto-reply and workflows fired — which a contact
# pushed in through a third-party bridge does not do.
HB_SUBDOMAIN = "theoverlookatflatheadlake"
HB_FORM_ID   = "691cc90430213200341cb152"          # "Event Inquiry Form", live
HB_FORM_URL  = f"https://{HB_SUBDOMAIN}.hbportal.co/public/{HB_FORM_ID}"


INQUIRE_ENDPOINT = "/api/inquire"     # the Cloudflare Worker relay (worker/)
TURNSTILE_SITE_KEY = ""              # set to enable Cloudflare Turnstile on the last step
# Cloudflare Web Analytics: cookieless page counting, no consent banner. The
# token is not a secret (it is in the page); blank means no beacon at all.
# Conversion = inquiries from the relay's /api/stats over these page views.
CF_ANALYTICS_TOKEN = ""


def analytics():
    if not CF_ANALYTICS_TOKEN:
        return ""
    return ('<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
            f'data-cf-beacon=\'{{"token": "{CF_ANALYTICS_TOKEN}"}}\'></script>\n')

INQ_TYPES = [("wedding", "Wedding"), ("corporate", "Corporate retreat"),
             ("wellness", "Wellness retreat"), ("other", "Something else")]


def inquiry_form(base="", inline=False):
    """The three-step inquiry: when → what → you. One form, three sections;
    inquire.js walks them one at a time and posts JSON to the relay. With JS
    off every section shows and the submit opens HoneyBook's public form, so
    nothing is ever a dead end.

    inline=True is the contact page, where it sits in the layout instead of
    the bottom sheet.
    """
    types = "".join(
        f'<label class="chip"><input type="radio" name="type" value="{v}" required> {l}</label>'
        for v, l in INQ_TYPES)
    turnstile = (f'<div class="cf-turnstile" data-sitekey="{TURNSTILE_SITE_KEY}" data-theme="light"></div>'
                 if TURNSTILE_SITE_KEY else "")
    cls = "inq inq--inline" if inline else "inq"
    return f"""<form class="{cls}" id="inquiry" method="get" action="{HB_FORM_URL}"
      data-endpoint="{INQUIRE_ENDPOINT}" novalidate>
  <div class="sheet__prog" aria-hidden="true"><i class="is-on"></i><i></i><i></i></div>

  <section class="sheet__step is-on" data-step="when" aria-label="Step 1 of 3">
    <h3>When are you thinking?</h3>
    <p class="lede">The dates you have in mind &mdash; a guess is fine.</p>
    <div class="inq__dates">
      <div class="field"><label for="inq-start">Arrive</label>
        <input id="inq-start" name="start" type="date"></div>
      <div class="field"><label for="inq-end">Leave</label>
        <input id="inq-end" name="end" type="date"></div>
    </div>
    <p class="field__err" data-err="when">Leaving before you arrive &mdash; check the dates.</p>
    <div class="chips" style="margin-top:1rem">
      <label class="chip"><input type="checkbox" name="flexible" value="yes"> Dates are flexible</label>
    </div>
  </section>

  <section class="sheet__step" data-step="what" aria-label="Step 2 of 3">
    <h3>What are you planning?</h3>
    <div class="chips" role="radiogroup" aria-label="Kind of gathering">{types}</div>
    <p class="field__err" data-err="type">Pick the closest one.</p>
    <div class="field" style="margin-top:1.2rem"><label for="inq-guests">About how many guests?</label>
      <input id="inq-guests" name="guests" type="number" inputmode="numeric" min="1" max="200" placeholder="e.g. 120"></div>
  </section>

  <section class="sheet__step" data-step="you" aria-label="Step 3 of 3">
    <h3>Where should we reply?</h3>
    <div class="field"><label for="inq-name">Name <span class="req">*</span></label>
      <input id="inq-name" name="name" type="text" autocomplete="name" required>
      <p class="field__err">Your name, so we know who to write to.</p></div>
    <div class="field"><label for="inq-email">Email <span class="req">*</span></label>
      <input id="inq-email" name="email" type="email" autocomplete="email" inputmode="email" required>
      <p class="field__err">That email does not look right.</p></div>
    <div class="field"><label for="inq-phone">Phone</label>
      <input id="inq-phone" name="phone" type="tel" autocomplete="tel" inputmode="tel"></div>
    <div class="field"><label for="inq-note">Anything else?</label>
      <textarea id="inq-note" name="note" rows="3" maxlength="2000"
        placeholder="What you are picturing, and what would make the weekend work."></textarea></div>
    <div class="inq__hp" aria-hidden="true"><label>Leave this empty
      <input name="website" type="text" tabindex="-1" autocomplete="off"></label></div>
    <input type="hidden" name="source" value="">
    {turnstile}
    <p class="form__note">We use this to answer you and nothing else. No list, no drip sequence.</p>
  </section>

  <div class="sheet__done" hidden>
    <span class="eyebrow">Sent</span>
    <h3>Thank you &mdash; it&rsquo;s with us.</h3>
    <p>You&rsquo;ll hear back, usually within one business day.</p>
  </div>
  <div class="sheet__fallback" role="alert"></div>

  <div class="sheet__nav">
    <button type="button" class="btn btn--ghost" data-back hidden>Back</button>
    <button type="button" class="btn" data-next>Continue</button>
    <button type="submit" class="btn" data-send>Send inquiry</button>
  </div>
</form>"""


def inquiry_sheet(base="", kind=""):
    """The bottom sheet every page carries (the contact page has the form
    inline instead). Opened by any control with data-sheet; `kind` is the
    page's own gathering type, used when the control names none."""
    return f"""
<div class="sheet" id="inquire" data-default="{kind}" hidden>
  <button class="sheet__back" type="button" aria-label="Close"></button>
  <div class="sheet__panel" role="dialog" aria-modal="true" aria-labelledby="inq-title">
    <div class="sheet__grip" aria-hidden="true"></div>
    <div class="sheet__head">
      <div>{eyebrow("Inquiry")}<h2 id="inq-title">Check your date</h2></div>
      <button class="sheet__x" type="button" aria-label="Close">&times;</button>
    </div>
    <div class="sheet__body">{inquiry_form(base)}</div>
  </div>
</div>"""


def spec(groups):
    """A grouped spec sheet. groups: (heading, [item_html, ...])

    Numbers are wrapped in <b> in the item text; the stylesheet sets those in the
    serif so the figures can be scanned without reading the sentences.
    """
    out = []
    for head, items in groups:
        li = "".join(f"<li>{i}</li>" for i in items)
        out.append(f'<div class="spec__g"><h3>{head}</h3><ul>{li}</ul></div>')
    return f'<div class="spec rv rv--stagger">{"".join(out)}</div>'


def experiences(eyeb, title, lede, items):
    """Food and what fills the days. items: (image, alt, title, body)"""
    cards = "".join(
        f'<div class="exp__card"><div class="exp__img">{img(f, a)}</div>'
        f'<h3>{t}</h3><p>{d}</p></div>' for f, a, t, d in items)
    return f"""<section class="sect">
    <div class="wrap">
      <div class="rv" style="margin-bottom:clamp(2.5rem,5vw,3.5rem);max-width:54ch">
        {eyebrow(eyeb)}<h2>{title}</h2>
        <p class="lede" style="margin-top:1.4rem">{lede}</p>
      </div>
      <div class="exp rv rv--stagger">{cards}</div>
    </div>
  </section>"""


DW_CATS = [("all", "Everything"), ("water", "Outside &amp; the water"),
           ("living", "Living &amp; dining"), ("rooms", "Bedrooms &amp; baths"),
           ("deck", "Decks &amp; the hot tub")]


def slideshow(shots, label):
    """A slide-through gallery. shots: (slug, caption, category)

    Every frame is a real <picture>; hidden slides do not fetch until shown,
    and the inline placeholder covers the moment they do. With JS off the
    first frame and every thumbnail still render.
    """
    tabs = "".join(
        '<button class="shw__cat%s" data-cat="%s" aria-pressed="%s">%s</button>'
        % (" is-on" if k == "all" else "", k, "true" if k == "all" else "false", lab)
        for k, lab in DW_CATS)
    frames, thumbs = "", ""
    for n, (slug, cap, cat) in enumerate(shots):
        f = f"driftwood-{slug}.jpg"
        frames += (f'<figure class="shw__slide{" is-on" if n == 0 else ""}" data-cat="{cat}">'
                   f'{img(f, f"{cap} at The Driftwood", eager=(None if n == 0 else False), sizes=SZ_HALF)}'
                   f'</figure>')
        thumbs += (f'<button class="shw__thumb{" is-on" if n == 0 else ""}" data-cat="{cat}" '
                   f'aria-label="{cap}">{img(f, "", thumb=True, sizes=SZ_THUMB)}</button>')
    caps = "|".join(cap for _, cap, _ in shots)
    return f"""<div class="shw rv" data-caps="{caps}" tabindex="0" role="group" aria-label="{label}">
      <div class="shw__cats">{tabs}</div>
      <div class="shw__stage">{frames}
        <div class="shw__nav">
          <button class="shw__arrow" data-dir="-1" aria-label="Previous photograph">&lsaquo;</button>
          <button class="shw__arrow" data-dir="1" aria-label="Next photograph">&rsaquo;</button>
        </div>
      </div>
      <div class="shw__bar">
        <p class="shw__cap" role="status" aria-live="polite"></p>
        <p class="shw__count"></p>
      </div>
      <div class="shw__thumbs">{thumbs}</div>
    </div>"""


def driftwood(shots, kind="wedding"):
    """The add-on estate. kind picks the wording, not the facts."""
    ask = ("contact.html?type=corporate" if kind == "retreat"
           else "contact.html?type=wedding")
    if kind == "retreat":
        title = "The Driftwood,<br>for a larger team"
        lede = ("The Overlook houses 28. For a bigger group, The Driftwood can be "
                "added alongside it &mdash; a 14,000 sq ft lakefront home at Woods Bay, "
                "with private lake access, a cove and boat slips.")
        body = ("About twenty minutes around the lake, or a few minutes by air &mdash; we "
                "can move the group between the two by helicopter with WestSlope. Both "
                "estates sit under one booking, so the team stays on the same footing "
                "instead of splitting across a hotel block in town.")
    else:
        title = "The Driftwood,<br>down on the water"
        lede = ("The Overlook sleeps 28 up on the hill. When the guest list runs past "
                "that, The Driftwood can be added to your booking &mdash; a 14,000 sq ft "
                "lakefront home at Woods Bay that sleeps 26, with its own cove and "
                "private boat slips.")
        body = ("It is about twenty minutes around the lake from the venue, or a few "
                "minutes by air &mdash; we can move your group between the two by "
                "helicopter with WestSlope. Either way both estates sit under one "
                "booking, so your family and your closest people stay together instead "
                "of scattering across hotels in Whitefish and Kalispell.")
    specs = [("14,000", "sq ft"), ("7", "bedrooms"), ("9", "baths"),
             ("20 min", "from the venue"), ("", "Private boat slips")]
    if kind != "retreat":
        specs.insert(2, ("26", "sleep here"))
    li = "".join(f'<li>{f"<b>{n}</b> " if n else ""}{l}</li>' for n, l in specs)
    return f"""<section class="sect sect--paper2">
    <div class="wrap">
      <div class="dw__head rv">
        <div>
          {eyebrow("Add to your booking")}
          <h2>{title}</h2>
        </div>
        <div class="dw__copy">
          <p class="lede">{lede}</p>
          <p style="color:var(--ink-soft)">{body}</p>
          <ul class="add__specs">{li}</ul>
          <p class="dw__foot">
            {tlink(ask, "Ask about adding The Driftwood")}
            <span class="dw__note">Availability is separate from the venue, so ask
              early if you want both estates on the same dates.</span>
          </p>
        </div>
      </div>
      {slideshow(shots, "Photographs of The Driftwood")}
    </div>
  </section>"""


def stickybar(page="", base=""):
    """Slim inquiry bar that slides in once someone is invested in the page.

    The corporate buyer is not checking a Saturday in June, so that page gets
    its own wording and its own pre-filled inquiry link.
    """
    if page == "retreats.html":
        lead, tail = "Planning a retreat?", "Send dates, headcount and what it needs to do."
        cta, href = "Request a Proposal", "contact.html?type=corporate"
    elif page == "wellness.html":
        lead, tail = "Planning a retreat?", "Tell us the dates and what the week is for."
        cta, href = "Check Availability", "contact.html?type=wellness"
    else:
        lead, tail = "Limited weekends each season.", "Tell us the one you have in mind."
        cta, href = "Check Your Date", "contact.html?type=wedding"
    return f"""
<div class="sbar" hidden>
  <div class="wrap sbar__in">
    <p class="sbar__txt"><b>{lead}</b> <span>{tail}</span></p>
    <a class="btn sbar__cta" href="{base}{href}" data-sheet="{href.split('=')[-1]}">{cta}</a>
    <button class="sbar__x" aria-label="Dismiss">&times;</button>
  </div>
</div>"""


# ------------------------------------------------------------------ chrome
def head(title, desc, url, og_image="hero-pavilion-lake.jpg", extra="", base=""):
    """url is the absolute canonical URL; base is the depth prefix from rel()."""
    alt = f"{BIZ['name']}, Lakeside, Montana"
    # a 1200x630 card is generated per share image by tools/build.py; use it
    # when it exists so scrapers are not left to crop the 3:2 original.
    _card = f"{IMG}og/{og_image}"
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    og_src = _card if os.path.isfile(os.path.join(_root, _card)) else f"{IMG}{og_image}"
    dims = imgsize(og_src)
    wh = ""
    if dims:
        wh = (f'<meta property="og:image:width" content="{dims[0]}">\n'
              f'<meta property="og:image:height" content="{dims[1]}">\n')
    mime = "image/png" if og_image.lower().endswith(".png") else "image/jpeg"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="theme-color" content="#1B1E1B">
<meta name="geo.region" content="US-MT">
<meta name="geo.placename" content="Lakeside, Montana">
<meta name="geo.position" content="48.0172;-114.2244">
<meta name="ICBM" content="48.0172, -114.2244">

<meta property="og:type" content="website">
<meta property="og:locale" content="en_US">
<meta property="og:site_name" content="{BIZ['name']}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/{og_src}">
<meta property="og:image:secure_url" content="{SITE}/{og_src}">
{wh}<meta property="og:image:type" content="{mime}">
<meta property="og:image:alt" content="{alt}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{SITE}/{og_src}">
<meta name="twitter:image:alt" content="{alt}">

<link rel="icon" href="{base}{IMG}overlook-logo.png">
<link rel="apple-touch-icon" href="{base}{IMG}overlook-logo-main.png">
<link rel="preload" as="font" type="font/woff2" crossorigin href="{base}assets/fonts/cormorant.woff2">
<link rel="preload" as="font" type="font/woff2" crossorigin href="{base}assets/fonts/jost.woff2">
<link rel="stylesheet" href="{base}assets/fonts/fonts.css?v={_ver("assets/fonts/fonts.css")}">
<link rel="stylesheet" href="{base}assets/css/site.css?v={_ver("assets/css/site.css")}">
{extra}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{BOOT}
<div class="veil" aria-hidden="true"></div>
<div class="prog" aria-hidden="true"><i></i></div>"""


def header(current, over_hero=True, base=""):
    """over_hero: page opens on a full-bleed image, so the header sits on top of it."""
    cls = "hdr hdr--over" if over_hero else "hdr"
    links = ""
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        links += f'<a href="{base}{href}"{cur}>{label}</a>'
    mob = "".join(f'<a href="{base}{h}">{l}</a>' for h, l in NAV)
    return f"""
<header class="{cls}">
  <div class="wrap hdr__in">
    <a class="brand" href="{base}index.html" aria-label="{BIZ['name']} — home">
      {img("overlook-logo-main.png", BIZ['name'], eager=None, base=base)}
    </a>
    <nav class="nav" aria-label="Primary">
      {links}
      <a class="btn" href="{base}contact.html" data-sheet="">Start Your Inquiry</a>
    </nav>
    <button class="burger" aria-label="Menu" aria-expanded="false" aria-controls="mobnav">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>
<nav class="mobnav" id="mobnav" aria-label="Mobile">
  <a href="{base}index.html">Home</a>
  {mob}
  <a class="btn" href="{base}contact.html" data-sheet="">Start Your Inquiry</a>
</nav>
<main id="main">"""


def footer(base="", sheet=True, kind=""):
    """sheet=False on the contact page, which carries the form inline.
    kind is the page's default gathering type for the sheet."""
    nav_li = "".join(f'<li><a href="{base}{h}">{l}</a></li>' for h, l in NAV)
    return f"""</main>
{inquiry_sheet(base, kind) if sheet else ""}
<div class="lbox" role="dialog" aria-modal="true" aria-label="Photograph">
  <button class="lbox__x" aria-label="Close">&times;</button>
  <button class="lbox__p" aria-label="Previous">&lsaquo;</button>
  <picture><source type="image/avif" sizes="100vw"><source type="image/webp" sizes="100vw"><img alt=""></picture>
  <button class="lbox__n" aria-label="Next">&rsaquo;</button>
  <p class="lbox__meta"></p>
</div>
{{STICKYBAR}}
<footer class="ftr">
  <div class="wrap">
    <div class="ftr__top">
      <div class="ftr__brandcol">
        {img("overlook-logo-main.png", BIZ['name'], "ftr__logo", eager=None, base=base)}
        <p style="max-width:38ch">A private 15-acre estate above Flathead Lake in
          {BIZ['city']}, {BIZ['state']} — booked one group at a time.</p>
      </div>
      <div>
        <h4>Explore</h4>
        <ul>{nav_li}<li><a href="{base}journal">Journal</a></li>
            <li><a href="{base}contact.html">Contact</a></li></ul>
      </div>
      <div>
        <h4>Get in touch</h4>
        <ul>
          <li><a href="mailto:{BIZ['email']}">{BIZ['email']}</a></li>
          <li><a href="tel:{BIZ['tel']}">{BIZ['phone']}</a></li>
          <li>{BIZ['city']}, {BIZ['state']}</li>
          <li style="margin-top:1.2rem"><a href="{BIZ['ig']}" rel="noopener">Instagram {BIZ['handle']}</a></li>
          <li><a href="{BIZ['fb']}" rel="noopener">Facebook</a></li>
          <li><a href="{BIZ['ig_sis']}" rel="noopener">Flathead Lake Luxury Lodging</a></li>
        </ul>
      </div>
    </div>
    <div class="ftr__bot">
      <span>&copy; {{year}} {BIZ['name']}. All rights reserved.</span>
      <span class="ftr__legal"><a href="{base}privacy">Privacy Policy</a>
        <a href="{base}terms">Terms of Service</a></span>
      <span>Lakeside, Montana</span>
    </div>
  </div>
</footer>
<script src="{base}assets/js/core.js?v={_ver("assets/js/core.js")}" defer data-base="{base}" data-inquire="{_ver("assets/js/inquire.js")}" data-cinema="{_ver("assets/js/cinema.js")}"></script>
{analytics()}</body>
</html>"""
