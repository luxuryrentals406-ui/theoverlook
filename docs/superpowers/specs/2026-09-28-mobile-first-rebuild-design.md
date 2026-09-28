# The Overlook — mobile-first rebuild

Date: 2026-09-28. Status: approved direction (Approach A, phased). Eric has
delegated the design decisions; this file is the fixed target for the build.

## Goal and the one metric

Most visitors are on phones. Success is **an inquiry sent**. Everything below is
judged by whether it makes a phone visitor more likely to send one, and whether
we can tell afterwards.

Measured as: inquiries per 100 phone visits, read from the inquiry relay's own
count against Cloudflare Web Analytics page views. Both free.

## What does not change

- The generator (`tools/build.py`, `tools/shell.py`) and the build command.
- All copy and every audited fact. `tools/lint.py` copy rules stay in force.
- All 16 URLs, the 10 redirects, `render.yaml`, Render static hosting.
- The brand: Cormorant Garamond + Jost, bone / forest / gold, the photography.

## Added monthly cost: $0

Cloudflare Workers (free tier), Workers KV (free), Turnstile (free), Cloudflare
Web Analytics (free), Render static (free). No paid analytics, no CDN plan.

## Phase 1 — fast, and a real inquiry path

### Images
`tools/images.py`, called by `build.py`. Originals stay in `assets/img/`.
Derivatives in `assets/i/`: 480 / 800 / 1200 / 1920 wide, WebP + JPEG, plus a
~20px WebP placeholder inlined as a data URI. Content-hashed; only changed
photos regenerate; derivatives are committed so Render still just copies files.
Every `<img>` gets `srcset`, `sizes`, `width`, `height`, `decoding="async"`;
below-the-fold images `loading="lazy"`; the hero is preloaded at phone width via
`imagesrcset`. Target: home page ≤ 500 KB of images at 375px (was 7.9 MB).

### Fonts
Self-hosted latin-subset woff2 in `assets/fonts/` (`tools/fonts.py` fetches and
subsets once; committed). Two files preloaded. `font-display: swap`.

### CSS
`assets/css/site.css` rewritten mobile-first from the same tokens: phone rules
are the default, `min-width` queries add desktop. Layers: tokens → base →
components → pages → desktop. Budget ≤ 14 KB gzipped, which is what a
phone actually downloads (the old file was 13.9 KB gzipped / 57 KB raw).
Tap targets ≥ 44px. Sticky CTA sits in the thumb zone and never covers
content that matters.

### JS
- `assets/js/core.js` — everyone. Menu, reveal, accordions, gallery filter,
  lightbox (swipe on touch). ≤ 10 KB.
- `assets/js/inquire.js` — loaded on first CTA tap or on idle. The bottom sheet.
- `assets/js/cinema.js` — loaded only when `(hover:hover) and (min-width:861px)`.
  Parallax, Ken Burns, drift, cursor marks, page hand-offs. Phones never fetch it.
- Remove the forced scroll-to-top on load; let the browser restore position.

### Inquiry flow
A bottom sheet, opened from any "Check your date" / "Inquire" control, three
steps sized for one thumb:
1. **When** — month grid date-range picker (native `<input type=date>` fallback),
   "dates are flexible" toggle. No availability shown.
2. **The gathering** — Wedding / Corporate retreat / Wellness retreat / Other;
   guest count.
3. **You** — name, email, phone, optional note. Honeypot field + Turnstile.

Submit → `POST /api/inquire` on a Cloudflare Worker (`worker/`), routed on the
live domain. The Worker: validates, rate-limits per IP (KV), verifies Turnstile
when enabled, stores a copy in KV (90-day TTL; this is the inquiry count and
the backup), then delivers the lead two ways — a Zapier catch hook whose next
step is HoneyBook **Create Project** (HoneyBook has no public API; its Zapier
integration is the supported way in, and the free Zapier plan covers the
volume), and an email to the inbox through Cloudflare Email Routing. 200 once
either delivery succeeded; otherwise 502, and the sheet shows a prefilled
"email us" link and the phone number. Nothing is ever lost silently.

*Correction, 2026-09-28:* the design first assumed a direct HoneyBook API.
The "SDK" seen in this session is HoneyBook's connector for Claude, not a
public API, so the relay uses Zapier's official integration instead. Same
outcome for Eric — the lead lands in his HoneyBook pipeline — at $0.

Secrets (Cloudflare, never in the repo): `ZAPIER_HOOK_URL`, `STATS_TOKEN`,
optionally `TURNSTILE_SECRET`. The site works without the Worker: the fallback
is the prefilled email, and with JS off the HoneyBook public form.

### Analytics and privacy
Cloudflare Web Analytics beacon (cookieless, no consent banner). Conversion is
the Worker's count over page views. `privacy/` gets one honest paragraph:
what the form collects, that HoneyBook stores it, that the relay keeps a copy
for 90 days, and that page views are counted without cookies.

### Guard rails
`tools/lint.py` gains a performance budget: fails if any page exceeds 600 KB of
images at phone width, any `<img>` lacks `srcset`/`width`/`height`, or any page
requests an external font or script other than the analytics beacon.

## Phase 2 — the funnel pages re-paced for a phone

Same content, phone pacing. Weddings goes from ~21 screens to ~10.
- **Home:** hero with one primary CTA; the wedding / retreat split as two
  tappable cards; four facts; three proof points (reviews); one closing CTA.
- **Weddings:** hero → the weekend in three cards (Fri / Sat / Sun) → what's
  included as collapsible groups → packages as a swipe rail → lodging teaser →
  reviews → FAQ (accordion) → CTA. Sticky section nav on phones.
- **Retreats:** same skeleton with retreat vocabulary (lint keeps them apart).
- **Estate:** lodging picker (tap a house → rooms, sleeps) above the grounds.
- **Gallery:** 2-column masonry on phones, category chips, swipe lightbox.
- **Contact:** the sheet's three steps inline, plus direct contact and
  getting-here. The HoneyBook iframe goes.
- Journal, legal, ported pages: new shell, no restructuring.

## Phase 3 — the layer that makes it feel like being there

Only pieces that move someone toward an inquiry:
- **Walk the property** — the existing map becomes a tap-through tour with the
  real photographs; swipe on phones.
- **Your weekend** — on Weddings, pick what happens Fri / Sat / Sun from what the
  estate offers; ends in the sheet with the note prefilled.
- **Reviews** as swipe cards with the reviewer's context.
- Native View Transitions between pages where supported; blur-up on every
  photograph; motion respects `prefers-reduced-motion`.

## Testing

- `python3 tools/build.py && python3 tools/lint.py` must pass before every commit.
- Each phase is checked in the built-in browser at 375px and desktop on every
  funnel page: no console errors, no horizontal scroll, all CTAs reach the sheet,
  the sheet submits and the fallback works with the Worker unreachable.
- Worker: unit tests for validation, rate limit, HoneyBook payload shape, and
  the failure path. Run locally with `wrangler dev`.

## Rollout

Branch `mobile-first-rebuild` off `main`. One PR per phase; Render deploys on
merge. Phase 1 needs nothing from Eric to build. To switch the relay on he
(or Claude, with his Cloudflare and Zapier access) follows `worker/README.md`:
one Zap (Catch Hook → HoneyBook Create Project) and one Worker pasted into the
Cloudflare dashboard with its KV, route and secrets. Until then the sheet
falls back to a prefilled email, so shipping Phase 1 early is safe.
