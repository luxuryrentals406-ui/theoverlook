/* The Overlook inquiry relay — a Cloudflare Worker on /api/*.
   The sheet posts JSON here. The Worker validates, rate-limits, (optionally)
   checks Turnstile, stores a copy in KV, then delivers the lead two ways:
   a Zapier catch hook whose next step is HoneyBook "Create Project", and an
   email to the inbox through Cloudflare Email Routing. It answers 200 once
   at least one delivery succeeded; otherwise 502, and the sheet falls back
   to a prefilled email. Nothing is ever lost silently.

   Bindings / settings (see wrangler.toml and README.md):
     INQUIRIES        KV namespace — copies, rate limits, counts
     MAIL             send_email binding (optional)
     MAIL_TO, MAIL_FROM, ALLOWED_ORIGINS   plain vars
     ZAPIER_HOOK_URL, TURNSTILE_SECRET, STATS_TOKEN   secrets */
import "./lib.js";
import { EmailMessage } from "cloudflare:email";

const L = globalThis.InquireLib;
const RATE_PER_HOUR = 5;
const KEEP_SECONDS = 90 * 24 * 3600;
const DEFAULT_ORIGINS = "https://theoverlookatflatheadlake.com,https://www.theoverlookatflatheadlake.com";

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    if (url.pathname === "/api/health") return json({ ok: true }, 200, req, env);
    if (url.pathname === "/api/stats") return stats(req, env);
    if (url.pathname !== "/api/inquire") return json({ ok: false, error: "not found" }, 404, req, env);
    if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(req, env) });
    if (req.method !== "POST") return json({ ok: false, error: "method" }, 405, req, env);
    if (!originOk(req, env)) return json({ ok: false, error: "origin" }, 403, req, env);

    let body;
    try { body = await req.json(); } catch (e) { return json({ ok: false, error: "json" }, 400, req, env); }

    const ip = req.headers.get("cf-connecting-ip") || "0.0.0.0";
    if (await limited(env, ip)) return json({ ok: false, error: "rate" }, 429, req, env);

    const v = L.validate(body);
    if (!v.ok) {
      /* a filled honeypot is a bot: say yes, do nothing */
      if (v.errors.indexOf("honeypot") > -1) return json({ ok: true }, 200, req, env);
      return json({ ok: false, errors: v.errors }, 400, req, env);
    }
    if (env.TURNSTILE_SECRET) {
      const pass = await turnstile(env.TURNSTILE_SECRET, body["cf-turnstile-response"], ip);
      if (!pass) return json({ ok: false, error: "turnstile" }, 403, req, env);
    }

    const d = v.data;
    const id = new Date().toISOString() + "-" + Math.random().toString(36).slice(2, 8);
    const key = "inq:" + id;
    await env.INQUIRIES.put(key, JSON.stringify({ ...d, ip }), { expirationTtl: KEEP_SECONDS });

    const delivery = {};
    if (env.ZAPIER_HOOK_URL) delivery.zapier = await forward(env.ZAPIER_HOOK_URL, L.leadPayload(d));
    if (env.MAIL && env.MAIL_TO) delivery.email = await mail(env, d);
    const tried = Object.keys(delivery);
    const ok = tried.some((k) => delivery[k] === "ok");
    ctx.waitUntil(env.INQUIRIES.put(key, JSON.stringify({ ...d, ip, delivery }), { expirationTtl: KEEP_SECONDS }));
    if (!ok) {
      /* stored, but nobody has been told: let the sheet offer the email route */
      return json({ ok: false, error: tried.length ? "delivery" : "unconfigured", id }, 502, req, env);
    }
    return json({ ok: true, id }, 200, req, env);
  }
};

/* ---- helpers ---------------------------------------------------------- */
function origins(env) {
  return (env.ALLOWED_ORIGINS || DEFAULT_ORIGINS).split(",").map((s) => s.trim()).filter(Boolean);
}
function originOk(req, env) {
  const o = req.headers.get("origin");
  if (!o) return true;                       /* same-origin form posts and curl */
  return origins(env).indexOf(o) > -1 || /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(o);
}
function cors(req, env) {
  const o = req.headers.get("origin") || "";
  const h = { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" };
  if (originOk(req, env) && o) {
    h["Access-Control-Allow-Origin"] = o;
    h["Access-Control-Allow-Methods"] = "POST, OPTIONS";
    h["Access-Control-Allow-Headers"] = "Content-Type";
    h["Vary"] = "Origin";
  }
  return h;
}
function json(obj, status, req, env) {
  return new Response(JSON.stringify(obj), { status: status || 200, headers: cors(req, env) });
}

async function limited(env, ip) {
  const hour = Math.floor(Date.now() / 3600000);
  const key = "rl:" + ip + ":" + hour;
  const n = parseInt((await env.INQUIRIES.get(key)) || "0", 10);
  if (n >= RATE_PER_HOUR) return true;
  await env.INQUIRIES.put(key, String(n + 1), { expirationTtl: 3700 });
  return false;
}

async function turnstile(secret, token, ip) {
  if (!token) return false;
  try {
    const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ secret, response: token, remoteip: ip })
    });
    const j = await r.json();
    return !!j.success;
  } catch (e) { return false; }
}

async function forward(hook, payload) {
  try {
    const r = await fetch(hook, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(6000)
    });
    return r.ok ? "ok" : "http " + r.status;
  } catch (e) { return "error " + (e && e.name); }
}

function rfc822(from, to, replyTo, subject, text) {
  const id = "<" + Date.now() + "." + Math.random().toString(36).slice(2) + "@theoverlookatflatheadlake.com>";
  const enc = (s) => "=?UTF-8?B?" + btoa(unescape(encodeURIComponent(s))) + "?=";
  return [
    "From: " + from,
    "To: " + to,
    "Reply-To: " + replyTo,
    "Subject: " + enc(subject),
    "Date: " + new Date().toUTCString(),
    "Message-ID: " + id,
    "MIME-Version: 1.0",
    "Content-Type: text/plain; charset=utf-8",
    "Content-Transfer-Encoding: 8bit",
    "",
    text
  ].join("\r\n");
}

async function mail(env, d) {
  try {
    const from = env.MAIL_FROM || "inquiries@theoverlookatflatheadlake.com";
    const raw = rfc822(from, env.MAIL_TO, d.email, L.subject(d), L.details(d));
    await env.MAIL.send(new EmailMessage(from, env.MAIL_TO, raw));
    return "ok";
  } catch (e) { return "error " + (e && e.message); }
}

/* GET /api/stats?token=…  -> inquiries per month, from the KV copies.
   This plus Cloudflare Web Analytics page views is the conversion rate. */
async function stats(req, env) {
  const url = new URL(req.url);
  if (!env.STATS_TOKEN || url.searchParams.get("token") !== env.STATS_TOKEN) {
    return json({ ok: false, error: "auth" }, 403, req, env);
  }
  const byMonth = {}, bySource = {}, byType = {};
  let cursor, total = 0;
  do {
    const page = await env.INQUIRIES.list({ prefix: "inq:", cursor, limit: 1000 });
    for (const k of page.keys) {
      total++;
      const m = k.name.slice(4, 11);
      byMonth[m] = (byMonth[m] || 0) + 1;
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);
  /* the last 200 in detail, for source page and type */
  const recent = await env.INQUIRIES.list({ prefix: "inq:", limit: 200 });
  for (const k of recent.keys) {
    const v = await env.INQUIRIES.get(k.name, "json");
    if (!v) continue;
    bySource[v.source || "?"] = (bySource[v.source || "?"] || 0) + 1;
    byType[v.type || "?"] = (byType[v.type || "?"] || 0) + 1;
  }
  return json({ ok: true, total, byMonth, bySource, byType }, 200, req, env);
}
