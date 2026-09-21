# The Overlook at Flathead Lake — website

Static site. No build step to host, no dependencies, no database. Fourteen pages,
one stylesheet, one script, 63 gallery photographs. Deployed on Render from
`render.yaml`; also runs on Netlify, Vercel, Cloudflare Pages or plain shared hosting.

This site **replaces a live, indexed React site** on the same domain. All 19 of that
site's URLs are accounted for: twelve redirect via `render.yaml`, six are preserved
as real pages at their exact paths, one is the home page. Do not remove a redirect
or rename a ported directory without checking the old sitemap first.

```
index.html          Home — orient, then split wedding vs corporate
weddings.html       Primary page: the weekend, what's included, comparison table,
                    packages, lodging teaser, reviews, FAQ
retreats.html       Corporate retreats — new, and the gap in the old site
estate.html         Shared lodging + grounds reference, linked from both
gallery.html        63 photos, filterable, with lightbox
story.html          Claudia & Eric
contact.html        Inquiry page — embedded HoneyBook lead form
wellness.html       Wellness retreats

  Ported from the old site, URLs preserved exactly — these must not move:
privacy/index.html  Privacy policy        -> /privacy
terms/index.html    Terms of service      -> /terms
journal/index.html  Journal index         -> /journal
journal/<slug>/index.html   Three planning guides -> /journal/<slug>

assets/css/site.css Hand-written. No framework.
assets/js/site.js   Progressive enhancement only — the site works without it.
assets/img/         Full-size photography (35 MB)
assets/thumb/       Gallery thumbnails (4.8 MB)

tools/build.py      Regenerates every page.  python3 tools/build.py
tools/shell.py      Header, footer, <head>, shared components
tools/lint.py       Copy-rule + SEO linter, walks subdirectories.
tools/lastmod.json  Per-page content hashes — sitemap lastmod state. Commit it.
render.yaml         Render blueprint: build, redirects, headers
sitemap.xml robots.txt llms.txt
```

Edit `tools/*.py`, never the `.html` directly — the HTML is generated and your
changes there will be overwritten on the next build.

---

## Before it goes live — 3 things

### 1. Real contact details — DONE

These are live in the `BIZ` dict in `tools/shell.py`:

```python
"phone":   "(406) 885-6064",
"tel":     "+14068856064",
"email":   "theoverlook@luxurylodgingvip.com",
```

The email is a Microsoft 365 mailbox on `luxurylodgingvip.com`, deliberately not on
this site's own domain. `theoverlookatflatheadlake.com` runs Google Workspace
(`media@`), but no public-facing address is published there. If you ever change the
published address, edit `tools/shell.py` and rebuild — never the `.html`:

```bash
cd ~/theoverlook
python3 tools/build.py && python3 tools/lint.py
```

### 2. Wire the inquiry form — DONE

`INQUIRY_MODE = "honeybook"` in `tools/build.py`, which embeds the live HoneyBook
lead form on `contact.html`, so a submission becomes a real HoneyBook inquiry.
The hand-built `own_form()` below is the unused fallback path.

**Known gap:** 18 CTAs link to `contact.html?type=wedding|corporate|wellness`, and
`site.js` reads that param to preselect `#eventType` — a field that only exists in
`own_form()`. Under HoneyBook the param is silently ignored.

The options below apply only if you switch `INQUIRY_MODE` back to `"own"`.

**Option A — HoneyBook or any CRM webhook (recommended).** Set `data-endpoint` to
your webhook URL. The script POSTs JSON with every field plus `source` and
`submittedAt`, and shows an inline thank-you without leaving the page:

```html
data-endpoint="https://your-webhook-url"
```

**Option B — Formspree, no code.** Replace `YOUR_FORM_ID` in the form `action`
with your Formspree form ID and leave `data-endpoint` empty.

**Option C — Netlify Forms.** Add `netlify` and `name="inquiry"` to the `<form>`
tag and remove the `action`.

Either way `eventType` (Wedding / Corporate Retreat / Other Private Event) is what
you route on internally. The wedding and corporate CTAs already deep-link with
`contact.html?type=wedding` and `?type=corporate`, which preselects the dropdown.

### 3. Point the domain

`SITE` in `tools/shell.py` is already `https://theoverlookatflatheadlake.com` — it
feeds canonical URLs, OpenGraph tags and the sitemap. If you launch on a staging
domain first, change it there and rebuild so social previews are not wrong.

---

## The copy rules, and how they stay enforced

The rebuild existed because the old site repeated itself. `tools/lint.py` fails the
build if that creeps back in:

- "Begin Your Story" and "Your Story Awaits" never appear
- "dream" appears at most once across the whole site (currently zero)
- **sleeping capacity is 28**, never 24. "Roughly 12" appears only on the corporate
  page, in the executive-group context, exactly as briefed
- wedding vocabulary (ceremony, bride, groom, aisle…) cannot appear on
  `retreats.html`; corporate vocabulary (meeting space, breakout, general session)
  cannot appear on `weddings.html`
- no exclamation points outside the verbatim Google reviews
- luxury filler (unparalleled, magical, breathtaking, stunning, nestled…) capped at
  one per page
- every `<img>` has alt text; every page has a title and meta description in range

```bash
python3 tools/build.py && python3 tools/lint.py
```

Run both before every deploy. Lint exits non-zero on a violation, so it can gate CI.

---

## Photography

67 images pulled from the existing site, resized to 2200px max and recompressed
(89 MB → 35 MB), with 700px thumbnails generated for the gallery grid. Gallery
categories live in the `PHOTOS` list in `tools/build.py` — `weddings`, `estate`,
`grounds`. Add a photo by dropping it in `assets/img/`, making a thumbnail, and
adding one line to that list.

`tools/build.py` fails loudly if any page references an image that isn't on disk.

---

## Still open

- **Photographer credit.** Confirm who shot the professional sets before publishing
  them anywhere beyond this site.
- **Sister property name.** The $100,000 Ultimate Flathead Lake Wedding Weekend
  currently says "our sister property" — name it if you want the SEO.
- **Shoulder-season corporate rates** are deliberately unpublished, per the brief.
  The line reads "available on request" so nothing is overpromised.
- **Real reviews only.** The six on the site are the six real Google reviews.
  Do not add invented ones.
