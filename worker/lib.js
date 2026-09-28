/* The Overlook inquiry relay — pure logic, no platform APIs.
   Runs unchanged in the Cloudflare Worker (index.js imports it) and under
   macOS `jsc` for the tests (test.js), so it declares itself on globalThis
   instead of using ES module exports. */
(function (root) {
  "use strict";

  var TYPES = { wedding: "Wedding", corporate: "Corporate retreat",
                wellness: "Wellness retreat", other: "Private gathering" };
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;

  function str(v, max) {
    if (v === undefined || v === null) return "";
    v = String(v).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "").trim();
    return max ? v.slice(0, max) : v;
  }

  /* today's date as YYYY-MM-DD in UTC; `now` is injectable for tests */
  function today(now) {
    return new Date(now || Date.now()).toISOString().slice(0, 10);
  }

  /**
   * validate(body, now) -> { ok: true, data } | { ok: false, errors: [...] }
   * body is the parsed JSON the sheet posts. Rules:
   *   website (honeypot) must be empty
   *   name 2–80, email well-formed, type one of TYPES
   *   start/end are YYYY-MM-DD or blank; end >= start; start >= today unless flexible
   *   guests blank or 1–200; note <= 2000; phone <= 40
   */
  function validate(body, now) {
    var b = body && typeof body === "object" ? body : {};
    var errors = [];
    var d = {
      name: str(b.name, 80),
      email: str(b.email, 120).toLowerCase(),
      phone: str(b.phone, 40),
      type: str(b.type, 20).toLowerCase(),
      start: str(b.start, 10),
      end: str(b.end, 10),
      flexible: b.flexible === "yes" || b.flexible === true,
      guests: str(b.guests, 4),
      note: str(b.note, 2000),
      source: str(b.source, 200),
      page: str(b.page, 200),
      submittedAt: str(b.submittedAt, 40)
    };
    if (str(b.website)) errors.push("honeypot");
    if (d.name.length < 2) errors.push("name");
    if (!EMAIL.test(d.email)) errors.push("email");
    if (!TYPES.hasOwnProperty(d.type)) errors.push("type");
    if (d.start && !ISO_DAY.test(d.start)) errors.push("start");
    if (d.end && !ISO_DAY.test(d.end)) errors.push("end");
    if (d.start && d.end && ISO_DAY.test(d.start) && ISO_DAY.test(d.end) && d.end < d.start) errors.push("range");
    if (d.start && ISO_DAY.test(d.start) && !d.flexible && d.start < today(now)) errors.push("past");
    if (d.guests) {
      var g = parseInt(d.guests, 10);
      if (!(g >= 1 && g <= 200)) errors.push("guests");
      else d.guests = String(g);
    }
    return errors.length ? { ok: false, errors: errors } : { ok: true, data: d };
  }

  /** A readable block for the HoneyBook project details and the email body. */
  function details(d) {
    var when = d.start ? d.start + (d.end ? " to " + d.end : "") : "not set";
    if (d.flexible) when += " (flexible)";
    return [
      "Gathering: " + TYPES[d.type] + (d.guests ? ", about " + d.guests + " guests" : ""),
      "Dates: " + when,
      "Name: " + d.name,
      "Email: " + d.email,
      "Phone: " + (d.phone || "not given"),
      "",
      d.note ? d.note : "(no note)",
      "",
      "From: theoverlookatflatheadlake.com" + (d.source || "") + (d.submittedAt ? " at " + d.submittedAt : "")
    ].join("\n");
  }

  /**
   * leadPayload(data) -> the flat object handed to the Zapier hook, whose
   * next step is HoneyBook "Create Project". Field names are what a Zap
   * editor shows, so mapping is a matter of picking them from a list.
   */
  function leadPayload(d) {
    return {
      project_name: TYPES[d.type] + " — " + d.name + (d.start ? " — " + d.start : ""),
      project_type: TYPES[d.type],
      project_date: d.start || "",
      project_end_date: d.end || d.start || "",
      dates_flexible: d.flexible ? "yes" : "no",
      guest_count: d.guests || "",
      client_name: d.name,
      client_email: d.email,
      client_phone: d.phone || "",
      note: d.note || "",
      details: details(d),
      source_page: d.source || "",
      submitted_at: d.submittedAt || "",
      lead_source: "Website inquiry"
    };
  }

  function subject(d) {
    return "Inquiry — " + TYPES[d.type] + (d.start ? " — " + d.start : "") + " — " + d.name;
  }

  root.InquireLib = { TYPES: TYPES, validate: validate, details: details,
                      leadPayload: leadPayload, subject: subject, today: today };
})(typeof globalThis !== "undefined" ? globalThis : this);
