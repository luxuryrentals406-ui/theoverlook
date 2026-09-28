# Phase 1 — Fast, and a real inquiry path — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every page fast on a phone and replace the HoneyBook iframe with a native three-step inquiry sheet that creates the lead in HoneyBook.

**Architecture:** The Python generator stays; a new `tools/images.py` produces responsive derivatives that `shell.img()` emits as `<picture>`; `site.css` is rewritten mobile-first; `site.js` is split into `core.js` (everyone), `inquire.js` (on CTA), `cinema.js` (desktop only). A Cloudflare Worker in `worker/` receives the form and creates the HoneyBook contact + project.

**Tech Stack:** Python 3.9 + Pillow 11 (AVIF/WebP/JPEG), stdlib `unittest`; plain ES2017 JS (no Node on this machine — Worker unit tests run under macOS `jsc`); Cloudflare Workers + KV + Turnstile; Cloudflare Web Analytics.

**Spec:** `docs/superpowers/specs/2026-09-28-mobile-first-rebuild-design.md`

## Global Constraints

- Python 3.9 syntax only (no `match`, no `X | Y` types). Pillow 11.3 present; no new pip packages.
- No Node. Worker is plain JS; tests run with `/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc`.
- `python3 tools/build.py && python3 tools/lint.py` passes before every commit.
- Copy and facts unchanged. All 16 URLs, 10 redirects, `render.yaml` unchanged except where a task says otherwise.
- Budgets: home ≤ 500 KB images at 375px; any page ≤ 600 KB; `site.css` ≤ 14 KB gzipped; `core.js` ≤ 10 KB.
- Tap targets ≥ 44px. `prefers-reduced-motion` respected. No external requests except the analytics beacon.
- Secrets never in the repo.

## Review Focus

1. A `<picture>` inside the hero must still paint before JS: first frame `loading="eager"`, preload matches the phone `srcset` candidate — test in Task 2.
2. A photo missing from `assets/img/` referenced by a page must fail the build loudly, not emit a broken `<img>` — test in Task 2.
3. Sheet submission with the Worker unreachable must show the email/phone fallback within 8 s and keep the typed data — test in Task 7.
4. Worker must reject a body with a filled honeypot, an invalid email, or a date in the past with 400 and never call HoneyBook — test in Task 8.
5. `cinema.js` must never be fetched at 375px or when `prefers-reduced-motion` — test in Task 5.

---

### Task 1: Responsive image derivatives

**Files:**
- Create: `tools/images.py`
- Create: `tools/tests/test_images.py`
- Create: `assets/i/` (generated, committed), `assets/i/manifest.json`

**Interfaces:**
- Produces: `images.build(root: str, names: list[str] | None = None) -> dict` — returns and writes the manifest.
  Manifest entry per photo name (e.g. `"tent-front.jpg"`):
  `{"w": 1920, "h": 1280, "hash": "8hex", "lqip": "data:image/webp;base64,...", "widths": [480, 800, 1200, 1920]}`.
  Derivative file naming: `assets/i/<stem>-<width>.<avif|webp|jpg>`. The 1920 JPEG is the original in `assets/img/` (not duplicated).
- Produces: `images.load_manifest(root) -> dict`.

- [ ] **Step 1: Write the failing test**

```python
# tools/tests/test_images.py
import os, sys, json, tempfile, shutil, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from PIL import Image
import images

class Derivatives(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "assets/img"))
        Image.new("RGB", (1920, 1280), (120, 90, 60)).save(
            os.path.join(self.root, "assets/img/tent.jpg"), quality=85)
    def tearDown(self): shutil.rmtree(self.root)

    def test_builds_every_width_and_format(self):
        m = images.build(self.root, ["tent.jpg"])
        e = m["tent.jpg"]
        self.assertEqual((e["w"], e["h"]), (1920, 1280))
        self.assertEqual(e["widths"], [480, 800, 1200, 1920])
        for w in (480, 800, 1200, 1920):
            for ext in ("avif", "webp"):
                self.assertTrue(os.path.exists(os.path.join(self.root, f"assets/i/tent-{w}.{ext}")), f"{w}.{ext}")
        for w in (480, 800, 1200):
            self.assertTrue(os.path.exists(os.path.join(self.root, f"assets/i/tent-{w}.jpg")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "assets/i/tent-1920.jpg")))
        self.assertTrue(e["lqip"].startswith("data:image/webp;base64,"))
        self.assertLess(len(e["lqip"]), 900)

    def test_small_original_caps_widths(self):
        Image.new("RGB", (900, 600)).save(os.path.join(self.root, "assets/img/s.jpg"))
        e = images.build(self.root, ["s.jpg"])["s.jpg"]
        self.assertEqual(e["widths"], [480, 800, 900])

    def test_idempotent_by_hash(self):
        images.build(self.root, ["tent.jpg"])
        p = os.path.join(self.root, "assets/i/tent-480.webp")
        t0 = os.path.getmtime(p)
        images.build(self.root, ["tent.jpg"])
        self.assertEqual(os.path.getmtime(p), t0)

    def test_png_passthrough(self):
        Image.new("RGBA", (400, 300)).save(os.path.join(self.root, "assets/img/logo.png"))
        e = images.build(self.root, ["logo.png"])["logo.png"]
        self.assertEqual(e["widths"], [])  # logos are not photographs

if __name__ == "__main__": unittest.main()
```

- [ ] **Step 2: Run to verify it fails** — `python3 -m unittest tools/tests/test_images.py` → ImportError.
- [ ] **Step 3: Implement `tools/images.py`** — Pillow resize with `Image.LANCZOS`, EXIF transpose, AVIF q=55, WebP q=78, JPEG q=80 progressive; LQIP = 20px-wide WebP q=40 base64; hash = md5 of original bytes[:8], stored in manifest; skip when hash matches and all files exist; PNG → manifest with intrinsic size, no derivatives.
- [ ] **Step 4: Run tests → PASS.**
- [ ] **Step 5: Generate the real set** — `python3 tools/images.py` over `assets/img/*.jpg`; commit `assets/i/` and `manifest.json`.
- [ ] **Step 6: Commit** — `git add tools/images.py tools/tests assets/i && git commit -m "Build-time responsive image derivatives"`

### Task 2: `shell.img()` emits `<picture>` with srcset, dimensions and placeholder

**Files:**
- Modify: `tools/shell.py:65-70` (`img`), `:274-284` (vmap thumbs), `:399-420` (slideshow), `:570,604` (logos)
- Modify: `tools/build.py:1012-1013` (gallery figures), `:1596` (hero preload)
- Create: `tools/tests/test_shell_img.py`

**Interfaces:**
- Produces: `img(name, alt, cls="", eager=False, sizes="100vw", thumb=False) -> str` — `<picture>` with AVIF, WebP and JPEG `<source>`/`<img>`, `width`/`height` from the manifest, `style="background:..."` LQIP, `loading`, `decoding`. `thumb=True` caps candidates at 480/800. Missing manifest entry → `KeyError` with the name (build fails loudly).
- Produces: `hero_preload(name) -> str` — `<link rel="preload" as="image" imagesrcset="..." imagesizes="100vw">`.
- Sizes presets used by build.py: hero `100vw`; card in a grid `(min-width:861px) 33vw, 100vw`; split media `(min-width:861px) 50vw, 100vw`; gallery `(min-width:861px) 33vw, 50vw`.

- [ ] **Step 1: Failing test** — assert `img("tent-front.jpg","x")` contains `<picture>`, `type="image/avif"`, `width="1920" height="1280"`, `srcset="assets/i/tent-front-480.webp 480w`, and `img("nope.jpg","x")` raises `KeyError`.
- [ ] **Step 2–4:** implement, run, pass. Update every call site listed above. `python3 tools/build.py && python3 tools/lint.py` passes.
- [ ] **Step 5: Verify in browser at 375px** — home loads; `read_network_requests` shows only `-480`/`-800` candidates; no `assets/img/*.jpg` except the OG/logo PNGs.
- [ ] **Step 6: Commit.**

### Task 3: Self-hosted fonts

**Files:** Create `tools/fonts.py`, `assets/fonts/*.woff2`; Modify `tools/shell.py:head()`; Modify `assets/css/site.css` (`@font-face` block only, rest is Task 4).

- [ ] Fetch Google's CSS with a Chrome UA, keep only `unicode-range` blocks that begin `U+0000-00FF` (latin), download those woff2 files, name them `cormorant-300.woff2`, `cormorant-300i.woff2`, `cormorant-400.woff2`, `cormorant-400i.woff2`, `jost-200.woff2`, `jost-300.woff2`, `jost-400.woff2`; write `assets/fonts/fonts.css` with `@font-face` + `font-display:swap`.
- [ ] `head()`: remove the three Google `<link>`s; add `<link rel="preload" as="font" type="font/woff2" crossorigin href="assets/fonts/cormorant-300.woff2">` and the same for `jost-300`; `<link rel="stylesheet" href="assets/fonts/fonts.css?v=...">`.
- [ ] Verify: `grep -r "fonts.googleapis" *.html` → none; browser shows the serif headline.
- [ ] Commit.

### Task 4: Mobile-first CSS rewrite

**Files:** Rewrite `assets/css/site.css`.

Order: tokens → base → components (buttons, header, mobnav, hero, facts, cards, split, band, quote, faq/acc, gallery grid, lightbox, sbar, sheet, forms, footer) → pages → `@media (min-width:641px)` → `@media (min-width:861px)` → `@media (hover:hover)` → reduced-motion. Phone defaults: `--sect: clamp(3.5rem,10vw,5rem)`; grids single column; hero `min-height: 100svh` with CTA in the lower third; all controls `min-height:44px`; sheet styles for Task 7 (`.sheet`, `.sheet__panel`, `.sheet__step`, `.field`, `.dgrid` month grid).

- [ ] Write it. Keep every class name used by the generator (grep the HTML for `class="` first and diff the set before/after).
- [ ] Verify: `wc -c assets/css/site.css` ≤ 40960; at 375px on all six funnel pages `document.documentElement.scrollWidth === 375`; no console errors; screenshots reviewed at 375 and desktop.
- [ ] Commit.

### Task 5: JS split and the scroll fix

**Files:** Create `assets/js/core.js`, `assets/js/cinema.js`, `assets/js/inquire.js` (stub that opens the sheet; real steps in Task 7); Delete `assets/js/site.js`; Modify `tools/shell.py` (BOOT, script includes).

- [ ] `core.js` = site.js lines 1–195 (sticky header, menu, accordions, reveal, gallery filter, lightbox + swipe from 299–315) plus the building picker (515–565) and drag rail (566–624) since those are content controls. Remove the form handler (goes to inquire.js).
- [ ] `cinema.js` = lines 196–505 and 641–904 (progress, count-up, hero cross-fade/Ken Burns, parallax, drift, header hide, stagger, button lean, page hand-off, zoom marks, photo drift).
- [ ] Include in `footer()`:
  ```html
  <script src="assets/js/core.js?v=…" defer></script>
  <script>if(matchMedia("(hover:hover) and (min-width:861px)").matches&&!matchMedia("(prefers-reduced-motion:reduce)").matches){var s=document.createElement("script");s.src="assets/js/cinema.js?v=…";s.defer=true;document.head.appendChild(s)}</script>
  ```
- [ ] BOOT: delete `scrollRestoration="manual"` and the `top()` calls; keep the `js`/`is-ready` classes.
- [ ] Verify at 375px: network shows `core.js` only; menu, accordions, gallery filter and lightbox work; back button restores position. At desktop: `cinema.js` loads, hero cross-fades.
- [ ] Commit.

### Task 6: Performance budget in lint

**Files:** Modify `tools/lint.py`; Create `tools/tests/test_lint_budget.py`.

**Interfaces:** `phone_image_bytes(html_path, root) -> int` — sums, for each `<picture>`/`<img>`, the smallest `srcset` candidate ≥ 375px (the 480 AVIF) or the raw file for plain `<img>`. `external_requests(html) -> list[str]` — every `http(s)://` in `src`/`href` of `link[rel=stylesheet|preload]`, `script`, `img`, `iframe`.

- [ ] Test: a fixture page with two `<picture>` blocks totals the two 480-AVIF sizes; a page with `<script src="https://x.y/z.js">` fails unless the host is `static.cloudflareinsights.com`; an `<img>` without `width` fails.
- [ ] Implement; wire into the existing FAILS list with messages `home.html: 812 KB of images at phone width (budget 500)`.
- [ ] `python3 tools/lint.py` passes on the built site. Commit.

### Task 7: The inquiry sheet

**Files:** Modify `tools/shell.py` (new `inquiry_sheet()`, `stickybar()` → `data-sheet` trigger, `honeybook_form()` → deleted, `footer()` includes the sheet once); Modify `tools/build.py` (contact page uses `inquiry_sheet(inline=True)`; every "Check Your Date"/"Request a Proposal" CTA gets `data-sheet="wedding|corporate|wellness"`); Rewrite `assets/js/inquire.js`.

**Interfaces:**
- Markup: `<div class="sheet" id="inquire" hidden>` → `.sheet__panel[role=dialog]` → three `.sheet__step` sections `data-step="when|what|you"` inside one `<form id="inquiry" action="https://theoverlookatflatheadlake.hbportal.co/public/691cc90430213200341cb152" method="get" data-endpoint="/api/inquire">`.
- Fields: `start` (date), `end` (date), `flexible` (checkbox), `type` (radio: wedding|corporate|wellness|other), `guests` (number, 1–200), `name`, `email`, `phone`, `note`, `website` (honeypot, hidden), `cf-turnstile-response` (added by Turnstile when the site key is present), hidden `source` (page path).
- JS: `inquire.js` opens the sheet from any `[data-sheet]` (prefills `type`), advances steps with validation, loads on first tap or `requestIdleCallback`, POSTs JSON to `data-endpoint`, 8 s timeout, on failure renders `.sheet__fallback` with `mailto:` prefilled from the fields and `tel:`. With JS off the form's native `action` opens the HoneyBook page.

- [ ] Build the markup and CSS hooks; build the JS; contact page renders the same form inline instead of the iframe.
- [ ] Verify at 375px: tap sticky CTA → sheet opens with `type` prefilled; step validation blocks empty required fields; submit with the Worker absent → fallback shows in < 8 s with `mailto:` containing the typed name and dates; Escape / backdrop closes; focus returns to the trigger.
- [ ] Commit.

### Task 8: Cloudflare Worker relay

**Files:** Create `worker/lib.js` (pure), `worker/index.js` (fetch handler), `worker/test.js` (jsc), `worker/wrangler.toml`, `worker/README.md`.

**Interfaces (lib.js, ES5-compatible so jsc runs it):**
- `validate(body) -> {ok:true, data} | {ok:false, errors:[...]}` — required: name (2–80), email (RFC-ish), type ∈ set, start ≥ today (UTC) unless `flexible`, guests 1–200 or blank, honeypot `website` must be empty, note ≤ 2000.
- `honeybookPayloads(data, sourcePage) -> {contact:{email, full_name, phone_number, private_notes}, project:{name, project_date, project_end_date, guest_count, project_details, project_location:"The Overlook at Flathead Lake", availability_type:"busy"}}` — `project_details` is a readable block: type, dates, flexible, guests, note, source page, submitted at.
- `index.js`: `POST /api/inquire` only; CORS for the site origin; rate limit 5/hour/IP via KV `RL:<ip>`; Turnstile verify when `TURNSTILE_SECRET` set; HoneyBook `POST https://api.honeybook.com/v1/contacts` then `/v1/projects` with `Authorization: Bearer ${HONEYBOOK_API_KEY}` (confirm exact paths against the SDK docs before deploying; README records the check); store `INQ:<iso>:<rand>` in KV with 90-day TTL regardless of HoneyBook outcome; respond `{ok:true}` or `502 {ok:false}`.

- [ ] Tests in `worker/test.js` (run: `jsc worker/lib.js worker/test.js`): valid body passes; filled honeypot fails; past date fails unless flexible; bad email fails; payload has the right project_date and a details block that contains the guest count and source page.
- [ ] Implement; README explains the two deploy routes (paste into the Cloudflare dashboard, or `curl` to the Workers API with a token) and the three settings: KV namespace binding `INQUIRIES`, secrets `HONEYBOOK_API_KEY`, `TURNSTILE_SECRET`, plus the route `theoverlookatflatheadlake.com/api/*`.
- [ ] Commit. Deployment itself waits for Eric's Cloudflare access and HoneyBook key.

### Task 9: Analytics beacon and the privacy paragraph

**Files:** Modify `tools/shell.py:footer()` (beacon, gated on a `CF_ANALYTICS_TOKEN` constant; emits nothing when blank); Modify `tools/build.py` privacy page content; Modify `tools/lint.py` allowlist (already in Task 6).

- [ ] Add the paragraph under the existing privacy headings: what the inquiry form collects, HoneyBook as the processor, the 90-day relay copy, cookieless page counting.
- [ ] Build + lint pass. Commit.

### Task 10: Phase 1 acceptance and PR

- [ ] `python3 tools/build.py && python3 tools/lint.py && python3 -m unittest discover -s tools/tests && jsc worker/lib.js worker/test.js` all pass.
- [ ] Browser pass at 375px and desktop on home, weddings, retreats, estate, gallery, contact: no console errors, no horizontal scroll, sheet opens from every CTA, image bytes on home ≤ 500 KB (from `read_network_requests`).
- [ ] Push branch, open PR against `main` titled "Phase 1: fast on phones, native inquiry sheet". Body lists the before/after numbers and what Eric must do to switch the relay on.
