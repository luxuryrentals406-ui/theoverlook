# The Overlook at Flathead Lake — website

Static site. No build step to host, no dependencies, no database. Seven HTML pages,
one stylesheet, one script, 67 photographs. Runs on Netlify, Vercel, Cloudflare Pages,
GitHub Pages, or plain shared hosting over FTP.

```
index.html          Home — orient, then split wedding vs corporate
weddings.html       Primary page: the weekend, what's included, comparison table,
                    packages, lodging teaser, reviews, FAQ
retreats.html       Corporate retreats — new, and the gap in the old site
estate.html         Shared lodging + grounds reference, linked from both
gallery.html        63 photos, filterable, with lightbox
story.html          Claudia & Eric
contact.html        Single inquiry form, event-type routing

assets/css/site.css Hand-written. No framework.
assets/js/site.js   Progressive enhancement only — the site works without it.
assets/img/         Full-size photography (35 MB)
assets/thumb/       Gallery thumbnails (4.8 MB)

tools/build.py      Regenerates every page.  python3 tools/build.py
tools/shell.py      Header, footer, <head>, shared components
tools/lint.py       Copy-rule + SEO linter.  python3 tools/lint.py
sitemap.xml robots.txt
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

### 2. Wire the inquiry form

The form posts nowhere until you pick one of these. It lives in `page_contact()`
in `tools/build.py`.

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
- **Real reviews only.** The three on the site are the three real Google reviews.
  Do not add invented ones.
