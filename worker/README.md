# The inquiry relay (not in use)

> Retired 2026-09-29: every inquiry now goes straight into HoneyBook through its
> own Event Inquiry Form (see `HB_FORM_URL` in `tools/shell.py`). Nothing on the
> site posts to `/api/inquire`. Kept only for reference.

The sheet on every page posts to `/api/inquire`. This Worker answers it. It
validates the inquiry, limits each address to five an hour, checks Turnstile
when that is switched on, keeps a copy for 90 days, and delivers the lead two
ways:

1. **HoneyBook**, through a Zap: *Webhooks by Zapier — Catch Hook* →
   *HoneyBook — Create Project*. HoneyBook has no public API; its Zapier
   integration is the supported way in.
2. **Email** to the inbox, through Cloudflare Email Routing (no third party).

It answers `200` once either delivery succeeded. Otherwise `502`, and the
sheet turns what the visitor typed into a prefilled email — so the relay
being down costs one extra tap, never a lead. Until it is deployed the site
behaves exactly that way.

Added monthly cost: $0. Workers, KV and Email Routing are on Cloudflare's
free tier; the Zap fits Zapier's free plan (100 tasks a month, two steps).

## Files

- `lib.js` — validation and the payload shapes. Pure; tested.
- `index.js` — the Worker. Imports `lib.js`.
- `test.js` — tests for `lib.js`. No Node here, so they run on macOS's
  JavaScriptCore: `jsc worker/lib.js worker/test.js`
  (`jsc` is `/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc`).
- `dist/worker.js` — `lib.js` + `index.js` in one file, for the dashboard
  editor. Regenerate with `python3 tools/pack_worker.py`.
- `wrangler.toml` — bindings and routes, for anyone who has wrangler.

## Switching it on (once, about twenty minutes)

### A. The Zap

1. zapier.com → Create Zap.
2. Trigger: **Webhooks by Zapier → Catch Hook**. Copy the hook URL; that is
   `ZAPIER_HOOK_URL`.
3. Action: **HoneyBook → Create Project**. Connect the HoneyBook account.
   Map the fields the hook will send:
   `client_name`, `client_email`, `client_phone`, `project_name`,
   `project_type`, `project_date`, `project_end_date`, `guest_count`,
   `details` (the readable summary), `lead_source`.
   To see them in the editor, send one test inquiry first (step C).
4. Turn the Zap on.

### B. The Worker (Cloudflare dashboard, no tools needed)

1. **Workers & Pages → Create → Create Worker.** Name it `overlook-inquire`.
   Open the editor, replace everything with `worker/dist/worker.js`, Deploy.
2. **Storage & Databases → KV → Create namespace** `overlook-inquiries`.
   In the Worker: Settings → Bindings → **KV namespace**, variable name
   `INQUIRIES`, pick that namespace.
3. **Settings → Variables and Secrets:**
   - `MAIL_TO` = `theoverlook@luxurylodgingvip.com` (text)
   - `MAIL_FROM` = `inquiries@theoverlookatflatheadlake.com` (text)
   - `ALLOWED_ORIGINS` = `https://theoverlookatflatheadlake.com,https://www.theoverlookatflatheadlake.com` (text)
   - `ZAPIER_HOOK_URL` = the hook URL from A2 (**secret**)
   - `STATS_TOKEN` = any long random string (**secret**); unlocks
     `/api/stats?token=…`
4. **Email** (optional but worth it): the zone's **Email → Email Routing**
   must be enabled and `theoverlook@luxurylodgingvip.com` verified as a
   destination address. Then in the Worker: Settings → Bindings →
   **Send email**, variable name `MAIL`, destination that address.
5. **Settings → Triggers → Routes → Add route:**
   `theoverlookatflatheadlake.com/api/*` (and the `www.` twin), zone
   theoverlookatflatheadlake.com.

### C. Check it

```bash
curl -s -X POST https://theoverlookatflatheadlake.com/api/inquire \
  -H 'Content-Type: application/json' \
  -d '{"name":"Test Person","email":"you@example.com","type":"wedding","start":"2027-07-16","end":"2027-07-18","guests":"120","note":"relay test","source":"/curl"}'
```

Expect `{"ok":true,"id":"…"}`, a new project in HoneyBook, and an email.
`https://theoverlookatflatheadlake.com/api/health` should say `{"ok":true}`.
Delete the test project in HoneyBook afterwards.

### D. Turnstile (optional bot check on the last step)

Cloudflare → Turnstile → Add widget (managed, invisible is fine) for the
domain. Put the **site key** in `tools/shell.py` as `TURNSTILE_SITE_KEY` and
rebuild; put the **secret key** in the Worker as `TURNSTILE_SECRET`. Without
both, the honeypot field and the rate limit are the spam defence, which is
enough to start.

## Reading the numbers

`GET /api/stats?token=STATS_TOKEN` returns inquiries by month, by page they
came from, and by kind. Against Cloudflare Web Analytics page views, that is
the conversion rate the rebuild is measured by.
