/* The Overlook — the inquiry window. Loaded by core.js when the page is idle
   or on the first tap of an inquiry control, never in the critical path.

   Every inquiry goes straight into HoneyBook (owner, 2026-09-29): the window
   holds HoneyBook's own Event Inquiry Form, framed the first time the window
   opens so no page pays for it unread. A control may pass a note — a package
   name, the weekend builder's picks — which the window shows above the form
   with a Copy button, because HoneyBook's form cannot be prefilled from here.

   The form is framed at its /embed/ address and this file does what
   HoneyBook's embed widget does, without loading the widget: it passes ad
   and campaign tags through to HoneyBook, sizes the frame to the height the
   form reports, and scrolls to where the form asks (the top of the next page,
   the thank-you after Submit). */
(function () {
  "use strict";
  var smooth = !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  /* ---- HoneyBook's side of the frame ------------------------------------ */
  // The tags HoneyBook's widget forwards (placement-controller.js), so a lead
  // from an ad or a campaign link is attributed in HoneyBook.
  var FORWARD = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                 "gclid", "fbclid", "msclkid", "ttclid", "li_fat_id"];
  function tagged(src) {
    var kept = location.search.replace(/^\?/, "").split("&").filter(function (pair) {
      return FORWARD.indexOf(pair.split("=")[0]) !== -1;
    });
    return kept.length ? src + (src.indexOf("?") === -1 ? "?" : "&") + kept.join("&") : src;
  }

  function frameFor(win) {
    var frames = document.querySelectorAll(".hbw__frame");
    for (var i = 0; i < frames.length; i++) {
      if (frames[i].contentWindow === win) return frames[i];
    }
    return null;
  }

  // Bring a point inside the form into view: y is measured from the top of
  // the form, h is the height of what should be centred (0 = align to top).
  function bring(f, y, h) {
    var box = f.closest(".sheet__body");
    var top, view, pad;
    if (box) {
      top = box.scrollTop + f.getBoundingClientRect().top - box.getBoundingClientRect().top + y;
      view = box.clientHeight;
      pad = 12;
    } else {
      var hdr = document.querySelector(".hdr");
      top = window.pageYOffset + f.getBoundingClientRect().top + y;
      view = window.innerHeight;
      pad = (hdr ? hdr.offsetHeight : 0) + 16;
    }
    var to = h ? top - view / 2 + h / 2 : top - pad;
    (box || window).scrollTo({ top: Math.max(0, to), behavior: smooth ? "smooth" : "auto" });
  }

  window.addEventListener("message", function (e) {
    var ev = e.data && e.data.hbEvent;
    if (!ev) return;
    var f = frameFor(e.source);
    if (!f || e.origin !== new URL(f.src).origin) return;
    if (ev.type === "hb_resize") {
      // The form reports ~20px while it is still loading; keep the measured
      // height from site.css until it reports a real one.
      if (ev.height >= 320) f.style.height = Math.ceil(ev.height) + "px";
    } else if (ev.type === "hb_scroll_to_top") {
      bring(f, 0, 0);
    } else if (ev.type === "hb_scroll_to_element" && ev.elementBoundingClientRect) {
      bring(f, ev.elementBoundingClientRect.y, ev.elementBoundingClientRect.height || 1);
    }
  });

  var sheet = document.getElementById("inquire");
  if (!sheet) {
    // The contact page carries the form inline and no window: its inquiry
    // buttons take the visitor down to the form instead of reloading.
    var inline = document.getElementById("inquiry-form");
    if (!inline) return;
    var own = inline.querySelector(".hbw__frame");
    if (own && tagged(own.src) !== own.src) own.src = tagged(own.src);
    document.addEventListener("click", function (e) {
      if (!(e.target.closest && e.target.closest("[data-sheet]"))) return;
      e.preventDefault();
      bring(own || inline, 0, 0);
    });
    return;
  }

  /* ---- the window --------------------------------------------------------- */
  var body = sheet.querySelector(".sheet__body");
  var holder = sheet.querySelector(".hbw");
  var noteBox = sheet.querySelector(".sheet__note");
  var noteText = sheet.querySelector("[data-note-text]");
  var copyBtn = sheet.querySelector("[data-copy]");
  var trigger = null, closing = null;

  function loadForm() {
    if (!holder || holder.querySelector("iframe")) return;
    var f = document.createElement("iframe");
    f.className = "hbw__frame";
    f.name = holder.dataset.id || "";
    f.src = tagged(holder.dataset.src);
    f.title = holder.dataset.title || "Inquiry form";
    f.setAttribute("allow", "clipboard-write");
    f.addEventListener("load", function () { holder.classList.add("is-loaded"); });
    holder.insertBefore(f, holder.firstChild);
  }

  function showNote(note) {
    if (!noteBox) return;
    if (typeof note === "string" && note) {
      noteText.textContent = note;
      noteBox.hidden = false;
      if (copyBtn) copyBtn.textContent = "Copy";
    } else {
      noteBox.hidden = true;
    }
  }

  function open(type, from, note) {
    trigger = from || null;
    clearTimeout(closing);
    sheet.hidden = false;
    document.body.style.overflow = "hidden";
    showNote(note);
    loadForm();
    if (body) body.scrollTop = 0;
    sheet.classList.add("is-open");
    setTimeout(function () { sheet.classList.add("is-in"); }, 20);
    setTimeout(function () {
      var x = sheet.querySelector(".sheet__x");
      if (x) x.focus({ preventScroll: true });
    }, 450);
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

  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      var t = noteText.textContent;
      var done = function () { copyBtn.textContent = "Copied"; };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(t).then(done, function () { copyBtn.textContent = "Select and copy above"; });
      } else {
        copyBtn.textContent = "Select and copy above";
      }
    });
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
