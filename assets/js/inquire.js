/* The Overlook — the inquiry sheet. Loaded by core.js when the page is idle
   or on the first tap of an inquiry control, never in the critical path.
   Three steps, one thumb: when → what → you. Posts JSON to the relay; if the
   relay is unreachable the typed inquiry becomes a prefilled email, so the
   worst case is one more tap, never a lost lead. */
(function () {
  "use strict";
  var STEPS = ["when", "what", "you"];
  var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var LABELS = { wedding: "Wedding", corporate: "Corporate retreat", wellness: "Wellness retreat", other: "Gathering" };
  var TIMEOUT = 8000;

  function setup(form, inSheet) {
    var steps = STEPS.map(function (k) { return form.querySelector('[data-step="' + k + '"]'); });
    var prog = [].slice.call(form.querySelectorAll(".sheet__prog i"));
    var back = form.querySelector("[data-back]");
    var next = form.querySelector("[data-next]");
    var send = form.querySelector("[data-send]");
    var nav = form.querySelector(".sheet__nav");
    var done = form.querySelector(".sheet__done");
    var fallback = form.querySelector(".sheet__fallback");
    var at = 0, sent = false;

    /* chips mirror their input so browsers without :has() still show the state */
    form.querySelectorAll(".chip input").forEach(function (inp) {
      var sync = function () {
        form.querySelectorAll('.chip input[name="' + inp.name + '"]').forEach(function (o) {
          o.closest(".chip").classList.toggle("is-on", o.checked);
        });
      };
      inp.addEventListener("change", sync);
      sync();
    });

    function show(i) {
      at = Math.max(0, Math.min(steps.length - 1, i));
      steps.forEach(function (s, n) { s.classList.toggle("is-on", n === at); });
      prog.forEach(function (p, n) { p.classList.toggle("is-on", n <= at); });
      back.hidden = at === 0;
      next.hidden = at === steps.length - 1;
      send.hidden = at !== steps.length - 1;
      var body = form.closest(".sheet__body");
      if (body) body.scrollTop = 0;
      if (inSheet) {
        var first = steps[at].querySelector("input:not([type=hidden]):not([type=radio]):not([type=checkbox]),textarea");
        if (first && at > 0) setTimeout(function () { first.focus({ preventScroll: true }); }, 80);
      }
    }
    function flag(el, on) {
      var field = el.closest(".field");
      if (field) field.classList.toggle("is-bad", on);
      if (on && !flag.first) flag.first = el;
    }
    function stepErr(key, on) {
      var p = form.querySelector('[data-err="' + key + '"]');
      if (p) p.classList.toggle("is-on", on);
    }
    function valid(i) {
      flag.first = null;
      var ok = true;
      if (i === 0) {
        var s = form.elements.start.value, e = form.elements.end.value;
        var bad = !!(s && e && e < s);
        stepErr("when", bad);
        ok = !bad;
      }
      if (i === 1) {
        var picked = !!form.querySelector('input[name="type"]:checked');
        stepErr("type", !picked);
        ok = picked;
      }
      if (i === 2) {
        var name = form.elements.name, email = form.elements.email;
        var n = name.value.trim().length >= 2, m = EMAIL.test(email.value.trim());
        flag(name, !n); flag(email, !m);
        ok = n && m;
      }
      if (!ok && flag.first) flag.first.focus({ preventScroll: true });
      return ok;
    }

    function payload() {
      var d = {};
      new FormData(form).forEach(function (v, k) { d[k] = typeof v === "string" ? v.trim() : v; });
      d.source = location.pathname;
      d.page = document.title;
      d.submittedAt = new Date().toISOString();
      return d;
    }
    function mailto(d) {
      var kind = LABELS[d.type] || "Inquiry";
      var lines = [
        "Dates: " + (d.start || "—") + (d.end ? " to " + d.end : "") + (d.flexible ? " (flexible)" : ""),
        "Gathering: " + kind + (d.guests ? ", about " + d.guests + " guests" : ""),
        "Name: " + d.name, "Email: " + d.email, "Phone: " + (d.phone || "—"),
        "", d.note || ""
      ];
      var to = (document.querySelector('a[href^="mailto:"]') || {}).href || "mailto:";
      return to.split("?")[0] + "?subject=" + encodeURIComponent(kind + " inquiry — The Overlook") +
             "&body=" + encodeURIComponent(lines.join("\n"));
    }
    function succeed() {
      sent = true;
      steps.forEach(function (s) { s.classList.remove("is-on"); });
      prog.forEach(function (p) { p.classList.add("is-on"); });
      nav.hidden = true;
      fallback.classList.remove("is-on");
      done.hidden = false;
      try { sessionStorage.setItem("sbar-off", "1"); } catch (e) {}
      var sbar = document.querySelector(".sbar");
      if (sbar) sbar.classList.remove("is-up");
      if (window.__inquirySent) window.__inquirySent();
    }
    function fail(d) {
      send.disabled = false;
      send.textContent = "Try again";
      var tel = (document.querySelector('a[href^="tel:"]') || {}).href;
      fallback.innerHTML =
        "<b>That didn&rsquo;t go through</b> &mdash; nothing you typed is lost. " +
        '<a href="' + mailto(d) + '">Send it as an email instead</a>' +
        (tel ? ', or <a href="' + tel + '">call us</a>.' : ".");
      fallback.classList.add("is-on");
      fallback.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
    /* Before the relay is switched on (shell.RELAY_LIVE) the form carries no
       endpoint, and Send is email-first: the visitor's mail app opens with the
       inquiry written out, and the sheet says plainly that pressing Send there
       is what delivers it — with the address and the HoneyBook form beside it
       for anyone whose device opens nothing. */
    function emailFirst(d) {
      var link = mailto(d);
      var addr = link.replace(/^mailto:/, "").split("?")[0];
      sent = true;
      steps.forEach(function (s) { s.classList.remove("is-on"); });
      prog.forEach(function (p) { p.classList.add("is-on"); });
      nav.hidden = true;
      fallback.classList.remove("is-on");
      done.innerHTML =
        '<span class="eyebrow">One more tap</span>' +
        "<h3>Your email is ready to send</h3>" +
        "<p>It opened in your mail app with everything filled in &mdash; press Send " +
        "there and it reaches us. Nothing opened? " +
        '<a href="' + link + '">Try again</a>, email <a href="mailto:' + addr + '">' + addr +
        '</a>, or use <a href="' + form.getAttribute("action") + '" rel="noopener">our inquiry form</a>.</p>';
      done.hidden = false;
      if (window.__inquirySent) window.__inquirySent("email");
      window.location.href = link;
    }
    function submit() {
      if (sent) return;
      var d = payload();
      var endpoint = form.dataset.endpoint;
      if (!endpoint) { emailFirst(d); return; }
      send.disabled = true;
      send.textContent = "Sending…";
      fallback.classList.remove("is-on");
      var ctl = "AbortController" in window ? new AbortController() : null;
      var timer = setTimeout(function () { if (ctl) ctl.abort(); }, TIMEOUT);
      fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(d),
        signal: ctl ? ctl.signal : undefined
      }).then(function (r) {
        clearTimeout(timer);
        if (!r.ok) throw new Error(String(r.status));
        succeed();
      }).catch(function () {
        clearTimeout(timer);
        fail(d);
      });
    }

    next.addEventListener("click", function () { if (valid(at)) show(at + 1); });
    back.addEventListener("click", function () { show(at - 1); });
    form.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && e.target.tagName !== "TEXTAREA" && at < steps.length - 1) {
        e.preventDefault();
        next.click();
      }
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (valid(0) && valid(1) && valid(2)) submit();
    });
    show(0);

    return {
      show: show,
      prefill: function (type) {
        var r = type && form.querySelector('input[name="type"][value="' + type + '"]');
        if (r && !r.checked) { r.checked = true; r.dispatchEvent(new Event("change")); }
      }
    };
  }

  /* ---- the sheet, or the inline form on the contact page ------------------ */
  var sheet = document.getElementById("inquire");
  var form = document.getElementById("inquiry");
  if (!form) return;
  var ctl = setup(form, !!sheet);

  if (!sheet) {
    var want = new URLSearchParams(location.search).get("type");
    if (want) ctl.prefill(want.toLowerCase());
    return;
  }

  var trigger = null, closing = null;
  function open(type, from, note) {
    trigger = from || null;
    clearTimeout(closing);
    sheet.hidden = false;
    document.body.style.overflow = "hidden";
    /* a button with no type of its own takes the page's: wedding on the
       wedding page, corporate on the retreats page */
    ctl.prefill(type || sheet.dataset.default || "");
    /* the weekend builder hands over its picks as the note */
    if (typeof note === "string" && note) form.elements.note.value = note;
    sheet.classList.add("is-open");
    setTimeout(function () { sheet.classList.add("is-in"); }, 20);
    var first = form.querySelector("input:not([type=hidden])");
    setTimeout(function () { if (first) first.focus({ preventScroll: true }); }, 450);
  }
  function close() {
    sheet.classList.remove("is-in");
    document.body.style.overflow = "";
    closing = setTimeout(function () {
      sheet.classList.remove("is-open");
      sheet.hidden = true;
      if (trigger && trigger.focus) trigger.focus({ preventScroll: true });
    }, 420);
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-sheet]");
    if (!a) return;
    e.preventDefault();
    open(a.dataset.sheet, a, a.dataset.note);
  });
  sheet.querySelector(".sheet__x").addEventListener("click", close);
  sheet.querySelector(".sheet__back").addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !sheet.hidden) close();
  });
  window.__openInquiry = open;
})();
