/* The Overlook — the inquiry window. Loaded by core.js when the page is idle
   or on the first tap of an inquiry control, never in the critical path.

   Every inquiry goes straight into HoneyBook (owner, 2026-09-29): the window
   holds HoneyBook's own Event Inquiry Form, framed the first time the window
   opens so no page pays for it unread. A control may pass a note — a package
   name, the weekend builder's picks — which the window shows above the form
   with a Copy button, because HoneyBook's form cannot be prefilled from here.

   The form scrolls inside the window, as it does on HoneyBook's own page.
   Ad and campaign tags pass through to HoneyBook (the list its own embed
   widget forwards), and a package page adds its package as the campaign, so
   HoneyBook's lead record says which package the inquiry came from. */
(function () {
  "use strict";
  var smooth = !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  // The tags HoneyBook's widget forwards (placement-controller.js), so a lead
  // from an ad or a campaign link is attributed in HoneyBook.
  var FORWARD = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                 "gclid", "fbclid", "msclkid", "ttclid", "li_fat_id"];
  // campaign: the package a package page's inquiries are about, recorded by
  // HoneyBook as the lead's campaign unless an ad already named one.
  function tagged(src, campaign) {
    var kept = location.search.replace(/^\?/, "").split("&").filter(function (pair) {
      return FORWARD.indexOf(pair.split("=")[0]) !== -1;
    });
    if (campaign && !kept.some(function (p) { return p.split("=")[0] === "utm_campaign"; })) {
      kept.push("utm_campaign=" + encodeURIComponent(campaign));
    }
    return kept.length ? src + (src.indexOf("?") === -1 ? "?" : "&") + kept.join("&") : src;
  }

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
      var hdr = document.querySelector(".hdr");
      window.scrollTo({
        top: inline.getBoundingClientRect().top + window.pageYOffset - (hdr ? hdr.offsetHeight : 0) - 16,
        behavior: smooth ? "smooth" : "auto"
      });
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
    f.src = tagged(holder.dataset.src, holder.dataset.campaign);
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
