# The Overlook at Flathead Lake — website

Static site. No framework, no database, no build step to host. Sixteen pages,
one stylesheet, three small scripts, 63 gallery photographs. Deployed on Render
from `render.yaml`; also runs on Netlify, Vercel, Cloudflare Pages or plain
shared hosting. The only server-side code is the inquiry relay in `worker/`,
a Cloudflare Worker.

This site **replaces a live, indexed React site** on the same domain. All 19 of
that site's URLs are accounted for: twelve redirect via `render.yaml`, six are
preserved as real pages at their exact paths, one is the home page. Do not
remove a redirect or rename a ported directory without checking the old sitemap
first.

```
index.html          Home — orient, then split wedding vs corporate
weddings.html       Primary page: the weekend, what's included, comparison table,
                    packages, lodging teaser, reviews, FAQ
retreats.html       Corporate retreats
estate.html         Shared lodging + grounds reference, linked from both
gallery.html        63 photos, filterable, with lightbox
story.html          Claudia & Eric
contact.html        The inquiry form, inline (every other page has it as a sheet)
wellness.html       Wellness retreats

  Ported from the old site, URLs preserved exactly — these must not move:
privacy/index.html  Privacy policy        -> /privacy
terms/index.html    Terms of service      -> /terms
journal/index.html  Journal index         -> /journal
journal/<slug>/index.html   Three planning guides -> /journal/<slug>
things-to-do/ wedding-venues-montana/     Two more ported pages

assets/css/site.css   Hand-written, mobile-first. Phone rules are the default;
                      min-width queries add tablet (641), desktop (861), wide nav (1041).
assets/js/core.js     The controls every device gets: menu, reveal, lightbox, pickers.
assets/js/inquire.js  The inquiry sheet. Loaded on idle or the first inquiry tap.
assets/js/cinema.js   Desktop-with-a-mouse only: parallax, Ken Burns, cursor mark,
                      page hand-offs. A phone never downloads it.
assets/img/           Original photography — the source of truth (43 MB)
assets/i/             Generated derivatives: AVIF/WebP/JPEG at 480/800/1200/1920 and
                      manifest.json (dimensions + placeholders). Committed. (62 MB)
assets/fonts/         Cormorant Garamond and Jost, self-hosted latin subsets

tools/build.py        Regenerates every page.  python3 tools/build.py
tools/shell.py        Header, footer, <head>, shared components, the inquiry form
tools/images.py       Derivatives + manifest. build.py runs it; content-hashed, so
                      only changed photographs are re-encoded.
tools/fonts.py        Fetches the font subsets once. Output is committed.
tools/lint.py         Copy rules + SEO + the phone performance budget. Walks subdirectories.
tools/budget.py       What a phone fetches per page; used by lint.py
tools/pack_worker.py  worker/lib.js + index.js -> worker/dist/worker.js (one file to paste)
tools/tests/          unittest suite for images, picture markup and the budget
tools/lastmod.json    Per-page content hashes — sitemap lastmod state. Commit it.
worker/               The inquiry relay (Cloudflare Worker). README.md there is
                      the switch-on guide.
render.yaml           Render blueprint: build, redirects, headers
sitemap.xml robots.txt llms.txt
docs/superpowers/     The rebuild's spec and plans
```

Edit `tools/*.py`, `assets/css`, `assets/js`, never the `.html` directly — the
HTML is generated and your changes there will be overwritten on the next build.

## Building and checking

```bash
cd ~/theoverlook
python3 tools/build.py && python3 tools/lint.py
python3 -m unittest discover -s tools/tests -t .
/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc worker/lib.js worker/test.js
```

Run the first line before every deploy; lint exits non-zero on a violation, so
it can gate CI. The other two are the unit tests (Python has no dependencies
beyond Pillow, which is installed; the Worker tests run on macOS's own
JavaScriptCore because there is no Node here).

To add a photograph: drop it in `assets/img/`, add it where a page uses it
(gallery photos are the `PHOTOS` list in `tools/build.py`), and build —
`images.py` makes the derivatives. Photos are used through `shell.img()`,
which emits a `<picture>` with the right `sizes`; the build fails loudly on a
name that is not in the manifest.

## The inquiry path

Every "Check Your Date" / "Start Your Inquiry" control opens a three-step sheet
(when → what → you). It posts JSON to `/api/inquire`, the Worker in `worker/`,
which keeps a copy and delivers the lead to HoneyBook (through Zapier's
official HoneyBook integration — HoneyBook has no public API) and to the
inbox by email. If the relay is unreachable the sheet turns what was typed
into a prefilled email, so nothing is lost. With JS off, every step shows and
the submit opens HoneyBook's public form.

`worker/README.md` has the switch-on steps: one Zap and one Worker pasted into
the Cloudflare dashboard. Until that is done the sheet is in fallback mode.

## The copy rules, and how they stay enforced

`tools/lint.py` fails the build if any of these creep back in:

- "Begin Your Story" and "Your Story Awaits" never appear
- "dream" appears at most once across the whole site (currently zero)
- **sleeping capacity is 28**, never 24; the corporate page does not discuss beds
- no published prices except the two the owner set
- wedding vocabulary cannot appear on `retreats.html`; corporate vocabulary
  cannot appear on `weddings.html`
- no exclamation points outside the verbatim Google reviews
- luxury filler (unparalleled, magical, breathtaking, stunning, nestled…) capped at
  one per page
- every `<img>` has alt text, width/height and (for photographs) a srcset; every
  page has a title and meta description in range
- **performance budget:** no page may fetch more than 600 KB of images when it
  opens on a 375px phone; no third party may be contacted on load except the
  analytics beacon and, on the contact page, Google Maps
- no phone number anywhere, including `llms.txt`

## Measurement

`shell.CF_ANALYTICS_TOKEN` switches on Cloudflare Web Analytics (cookieless,
no consent banner). The relay's `/api/stats` counts inquiries by month, page
and kind. Inquiries over page views is the number the rebuild is judged by.

## Still open

- **Photographer credit.** Confirm who shot the professional sets before publishing
  them anywhere beyond this site.
- **Sister property name.** The Ultimate Flathead Lake Wedding Weekend (starting at $135,000)
  currently says "our sister property" — name it if you want the SEO.
- **Shoulder-season corporate rates** are deliberately unpublished, per the brief.
  The line reads "available on request" so nothing is overpromised.
- **Real reviews only.** The six on the site are the six real Google reviews.
  Do not add invented ones.
- **Phase 2 and 3** of the rebuild (phone-paced funnel pages, the interactive
  layer) are specified in `docs/superpowers/specs/`.
