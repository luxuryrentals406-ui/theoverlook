/* Tests for lib.js. No Node on this machine, so they run under macOS
   JavaScriptCore:
     jsc worker/lib.js worker/test.js
   (jsc lives at /System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc) */
(function () {
  "use strict";
  var L = globalThis.InquireLib;
  var passed = 0, failed = 0;
  function eq(actual, expected, label) {
    var a = JSON.stringify(actual), e = JSON.stringify(expected);
    if (a === e) { passed++; }
    else { failed++; print("FAIL " + label + "\n  expected " + e + "\n  got      " + a); }
  }
  var NOW = Date.UTC(2026, 8, 28, 12);          // 2026-09-28
  var good = { name: "Test Person", email: "Test@Example.com", phone: "406 555 0100",
               type: "wedding", start: "2027-07-16", end: "2027-07-18", flexible: "",
               guests: "120", note: "Hello", website: "", source: "/weddings.html",
               submittedAt: "2026-09-28T12:00:00.000Z" };

  var r = L.validate(good, NOW);
  eq(r.ok, true, "a complete inquiry validates");
  eq(r.data.email, "test@example.com", "email is lower-cased");
  eq(r.data.guests, "120", "guests normalised");
  eq(r.data.flexible, false, "flexible defaults to false");

  eq(L.validate(Object.assign({}, good, { website: "http://spam" }), NOW).errors, ["honeypot"], "honeypot rejects");
  eq(L.validate(Object.assign({}, good, { email: "nope" }), NOW).errors, ["email"], "bad email rejects");
  eq(L.validate(Object.assign({}, good, { type: "party" }), NOW).errors, ["type"], "unknown type rejects");
  eq(L.validate(Object.assign({}, good, { name: "A" }), NOW).errors, ["name"], "one-letter name rejects");
  eq(L.validate(Object.assign({}, good, { start: "2026-01-01", end: "" }), NOW).errors, ["past"], "past date rejects");
  eq(L.validate(Object.assign({}, good, { start: "2026-01-01", end: "", flexible: "yes" }), NOW).ok, true, "past date is fine when flexible");
  eq(L.validate(Object.assign({}, good, { end: "2027-07-10" }), NOW).errors, ["range"], "end before start rejects");
  eq(L.validate(Object.assign({}, good, { guests: "900" }), NOW).errors, ["guests"], "900 guests rejects");
  eq(L.validate(Object.assign({}, good, { guests: "" }), NOW).ok, true, "blank guests is fine");
  eq(L.validate(Object.assign({}, good, { start: "", end: "" }), NOW).ok, true, "no dates is fine");
  eq(L.validate(Object.assign({}, good, { start: "July 2027" }), NOW).errors, ["start"], "free-text date rejects");
  eq(L.validate(null, NOW).ok, false, "null body rejects");
  eq(L.validate({ name: "x", email: "y", type: "z", website: "w" }, NOW).errors,
     ["honeypot", "name", "email", "type"], "every failure is reported");

  var long = L.validate(Object.assign({}, good, { note: new Array(3000).join("n") }), NOW);
  eq(long.data.note.length, 2000, "note is capped at 2000");
  var ctl = L.validate(Object.assign({}, good, { name: "Te\u0007st" }), NOW);
  eq(ctl.data.name, "Test", "control characters are stripped");

  var p = L.leadPayload(r.data);
  eq(p.project_type, "Wedding", "payload project type");
  eq(p.project_date, "2027-07-16", "payload project date");
  eq(p.project_end_date, "2027-07-18", "payload end date");
  eq(p.guest_count, "120", "payload guests");
  eq(p.client_email, "test@example.com", "payload email");
  eq(p.project_name, "Wedding — Test Person — 2027-07-16", "payload project name");
  eq(p.details.indexOf("about 120 guests") > -1, true, "details carry the guest count");
  eq(p.details.indexOf("/weddings.html") > -1, true, "details carry the source page");
  eq(p.details.indexOf("2027-07-16 to 2027-07-18") > -1, true, "details carry the dates");
  eq(L.subject(r.data), "Inquiry — Wedding — 2027-07-16 — Test Person", "email subject");

  var nod = L.validate(Object.assign({}, good, { start: "", end: "", guests: "", note: "", phone: "" }), NOW).data;
  eq(L.leadPayload(nod).project_end_date, "", "no dates -> empty end date");
  eq(L.details(nod).indexOf("Dates: not set") > -1, true, "no dates reads as not set");
  eq(L.details(nod).indexOf("(no note)") > -1, true, "no note reads as no note");

  print(passed + " passed, " + failed + " failed");
  if (failed) throw new Error(failed + " test(s) failed");
})();
