/* The Overlook — the inquiry window. Loaded by core.js when the page is idle
   or on the first tap of an inquiry control, never in the critical path.

   Every inquiry goes straight into HoneyBook (owner, 2026-09-29): the window
   holds HoneyBook's own Event Inquiry Form, framed the first time the window
   opens so no page pays for it unread. A control may pass a note — a package
   name, the weekend builder's picks — which the window shows above the form
   with a Copy button, because HoneyBook's form cannot be prefilled from here. */
(function () {
  "use strict";
  var sheet = document.getElementById("inquire");
  if (!sheet) {
    // The contact page carries the form inline and no window: its inquiry
    // buttons take the visitor down to the form instead of reloading.
    var inline = document.getElementById("inquiry-form");
    if (inline) document.addEventListener("click", function (e) {
      if (!(e.target.closest && e.target.closest("[data-sheet]"))) return;
      e.preventDefault();
      var hdr = document.querySelector(".hdr");
      window.scrollTo({
        top: inline.getBoundingClientRect().top + window.pageYOffset - (hdr ? hdr.offsetHeight : 0) - 16,
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"
      });
    });
    return;
  }
  var body = sheet.querySelector(".sheet__body");
  var holder = sheet.querySelector(".hbw");
  var noteBox = sheet.querySelector(".sheet__note");
  var noteText = sheet.querySelector("[data-note-text]");
  var copyBtn = sheet.querySelector("[data-copy]");
  var trigger = null, closing = null;

  function loadForm() {
    if (!holder || holder.querySelector("iframe") || holder.querySelector("script")) return;
    var f = document.createElement("iframe");
    f.className = "hbw__frame";
    f.src = holder.dataset.src;
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
