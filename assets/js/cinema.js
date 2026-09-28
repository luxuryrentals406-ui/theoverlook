/* The Overlook — cinema. Loaded by core.js only where a mouse and a wide
   screen make it worth it: (hover:hover) and (min-width:861px), and never
   under prefers-reduced-motion. A phone never downloads this file.
   Cross-fading hero, scroll parallax, magnetic buttons, page hand-offs,
   the zoom cursor and the photographs that drift as they pass. */
(function () {
  "use strict";

  /* ---- rAF-batched scroll bus -------------------------------------------- */
  var subs = [], queued = false;
  function onFrame(fn) { subs.push(fn); }
  function pump() {
    queued = false;
    var y = window.pageYOffset;
    for (var i = 0; i < subs.length; i++) subs[i](y);
  }
  window.addEventListener("scroll", function () {
    if (queued) return;
    queued = true;
    requestAnimationFrame(pump);
  }, { passive: true });

  /* ---- scroll progress ------------------------------------------------------ */
  var bar = document.querySelector(".prog i");
  if (bar) {
    var tick = function () {
      var d = document.documentElement;
      var max = d.scrollHeight - d.clientHeight;
      bar.style.width = (max > 0 ? (d.scrollTop / max) * 100 : 0) + "%";
    };
    tick();
    onFrame(tick);
    window.addEventListener("resize", tick);
  }

  /* ---- hero: cross-fade the frames, Ken Burns each one ----------------------- */
  var stack = document.querySelector(".hero__bg--multi");
  if (stack) {
    var frames = [].slice.call(stack.querySelectorAll(".hero__frame"));
    var dots = [].slice.call(document.querySelectorAll(".hero__dot"));
    var cur = 0, timer = null;
    /* a hidden frame's <picture> only fetches once it is shown; asking for
       the next one a beat early keeps the cross-fade from landing on a blur */
    var warm = function (n) {
      var f = frames[(n + frames.length) % frames.length];
      var im = f && f.querySelector("img");
      if (im && im.loading === "lazy") im.loading = "eager";
    };
    var goTo = function (n) {
      cur = (n + frames.length) % frames.length;
      warm(cur + 1);
      frames.forEach(function (f, i) {
        f.classList.toggle("is-on", i === cur);
        if (i === cur) {
          var im = f.querySelector("img");
          im.style.animation = "none";
          void im.offsetWidth;
          im.style.animation = "";
        }
      });
      dots.forEach(function (d, i) {
        d.classList.toggle("is-on", i === cur);
        d.setAttribute("aria-selected", i === cur ? "true" : "false");
      });
    };
    var play = function () { timer = setInterval(function () { goTo(cur + 1); }, 6800); };
    var pause = function () { clearInterval(timer); timer = null; };
    window.addEventListener("load", function () { warm(1); });
    dots.forEach(function (d, i) {
      d.addEventListener("click", function () { pause(); goTo(i); play(); });
    });
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) pause(); else if (!timer) play();
    });
    play();
  }

  /* ---- hero parallax: background lags, copy lifts and dissolves ---------------- */
  document.querySelectorAll(".hero[data-parallax]").forEach(function (h) {
    var bg = h.querySelector(".hero__bg");
    var copy = h.querySelector(".hero__in");
    var was = null;
    onFrame(function (y) {
      var height = h.offsetHeight;
      var t = y < height ? y : height;          /* clamp, or scrolling past freezes it */
      if (t === was) return;
      was = t;
      /* 0.16 keeps the shift inside the 20% of headroom the box was given */
      if (bg) bg.style.transform = "translate3d(0," + (t * 0.16).toFixed(1) + "px,0)";
      if (copy) {
        copy.style.transform = "translate3d(0," + (t * -0.22).toFixed(1) + "px,0)";
        copy.style.opacity = Math.max(0, 1 - t / (height * 0.7)).toFixed(3);
      }
      h.classList.toggle("is-scrolled", t > 80);
    });
  });

  /* ---- slow drift on full-bleed band backgrounds ------------------------------ */
  document.querySelectorAll("[data-drift]").forEach(function (el) {
    var im = el.querySelector("img");
    if (!im) return;
    im.style.willChange = "transform";
    im.style.height = "116%";
    im.style.top = "-8%";
    im.style.position = "absolute";
    onFrame(function () {
      var r = el.getBoundingClientRect();
      if (r.bottom < 0 || r.top > window.innerHeight) return;
      var p = (r.top + r.height / 2 - window.innerHeight / 2) / window.innerHeight;
      im.style.transform = "translate3d(0," + (p * 7).toFixed(2) + "%,0)";
    });
  });

  /* ---- buttons lean toward the cursor ------------------------------------------- */
  document.querySelectorAll(".btn").forEach(function (b) {
    var pull = 5;
    b.addEventListener("pointermove", function (e) {
      var r = b.getBoundingClientRect();
      var dx = (e.clientX - (r.left + r.width / 2)) / (r.width / 2);
      var dy = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
      b.style.transition = "transform .18s linear, background .35s, color .35s, border-color .35s";
      b.style.transform = "translate(" + (dx * pull).toFixed(1) + "px," + (dy * pull * 0.6).toFixed(1) + "px)";
    });
    b.addEventListener("pointerleave", function () {
      b.style.transition = "";
      b.style.transform = "";
    });
  });

  /* ---- pages hand off to each other instead of blinking -------------------------- */
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a");
    if (!a) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    if (a.target === "_blank" || a.hasAttribute("download") || a.hasAttribute("data-sheet")) return;
    var href = a.getAttribute("href") || "";
    if (!href || href.charAt(0) === "#" || /^(mailto|tel|https?):/.test(href)) return;
    if (a.origin && a.origin !== location.origin) return;
    e.preventDefault();
    document.documentElement.classList.add("is-leaving");
    setTimeout(function () { location.href = a.href; }, 300);
  });
  window.addEventListener("pageshow", function () {
    document.documentElement.classList.remove("is-leaving");
  });

  /* ---- every framed photograph opens full size; the cursor says so ------------------ */
  var SELECTORS = [".split__img", ".split__media > picture > img", ".split__media > img", ".exp__img",
                   ".rail__shot", ".add__img", ".sw__stage", ".shw__stage", ".vmap__shot", ".band__bg"];
  var zoomables = [];
  SELECTORS.forEach(function (sel) {
    document.querySelectorAll(sel).forEach(function (el) {
      var im = el.tagName === "IMG" ? el : el.querySelector("img");
      if (!im || el.closest(".lbox")) return;
      if (el.closest("a,button")) return;   /* it already does something on click */
      var box = el.tagName === "IMG" ? el.closest(".split__media") || el : el;
      box.setAttribute("data-zoom", "");
      zoomables.push({ box: box, img: im });
    });
  });
  document.querySelectorAll(".mos__cell").forEach(function (cell) {
    var im = cell.querySelector("img");
    if (im) zoomables.push({ box: cell, img: im, onlyWhenOpen: true });
  });
  var cursorBoxes = zoomables.map(function (z) { return z.box; });
  document.querySelectorAll(".grid figure").forEach(function (f) {
    cursorBoxes.push(f);
    f.setAttribute("data-zoom", "");
  });

  var base = (document.currentScript && document.currentScript.src.replace(/assets\/js\/.*$/, "")) || "";
  if (cursorBoxes.length) {
    var mark = document.createElement("div");
    mark.className = "gcursor";
    mark.setAttribute("aria-hidden", "true");
    mark.innerHTML = '<img src="' + base + 'assets/img/overlook-mark.png" alt="">';
    document.body.appendChild(mark);
    var move = function (e) { mark.style.left = e.clientX + "px"; mark.style.top = e.clientY + "px"; };
    var drop = function () { mark.classList.remove("is-on"); document.removeEventListener("pointermove", move); };
    cursorBoxes.forEach(function (box) {
      box.addEventListener("pointerenter", function (e) {
        if (box.classList.contains("mos__cell") && !box.classList.contains("is-on")) return;
        move(e);
        mark.classList.add("is-on");
        document.addEventListener("pointermove", move);
      });
      box.addEventListener("pointerleave", drop);
      box.addEventListener("pointermove", function (e) {
        if (!box.classList.contains("mos__cell")) return;
        if (box.classList.contains("is-on") && !mark.classList.contains("is-on")) {
          mark.classList.add("is-on");
          document.addEventListener("pointermove", move);
        }
        move(e);
      });
    });
    window.addEventListener("scroll", drop, { passive: true });
    document.addEventListener("pointerleave", drop);
  }

  /* open them in the shared lightbox that core.js owns; the gallery page runs
     its own filtered list, so leave that one alone */
  var lb = document.querySelector(".lbox");
  if (lb && lb.__set && zoomables.length && !document.querySelector(".grid figure")) {
    var at = 0;
    var stemOf = function (im) {
      var m = (im.getAttribute("src") || "").match(/assets\/img\/([^/]+)\.jpe?g$/i);
      return m ? m[1] : "";
    };
    var show = function (i) {
      at = (i + zoomables.length) % zoomables.length;
      var z = zoomables[at];
      lb.__set(z.img.getAttribute("src"), stemOf(z.img), z.img.alt,
               "<b>" + (z.img.alt || "") + "</b>" + (at + 1) + " of " + zoomables.length);
    };
    lb.__prev = function () { show(at - 1); };
    lb.__next = function () { show(at + 1); };
    zoomables.forEach(function (z, i) {
      if (z.onlyWhenOpen) {
        z.box.addEventListener("pointerdown", function () { z.wasOpen = z.box.classList.contains("is-on"); });
      }
      z.box.addEventListener("click", function (e) {
        if (z.onlyWhenOpen) { if (!z.wasOpen) return; }
        else if (e.target.closest("button,a")) return;
        show(i);
        lb.__open();
      });
    });
  }

  /* ---- photographs drift inside their frame as you scroll ---------------------------- */
  var movers = [];
  zoomables.forEach(function (z) {
    if (z.box.closest(".hero,.lbox,.shw__stage,.sw__stage")) return;
    if (z.box.hasAttribute("data-drift")) return;
    z.box.classList.add("imove");
    z.img.style.height = "112%";
    z.img.style.width = "100%";
    z.img.style.objectFit = "cover";
    z.img.style.position = "relative";
    movers.push(z.img);
  });
  if (movers.length) {
    var drift = function () {
      var vh = window.innerHeight;
      movers.forEach(function (im) {
        var r = (im.closest(".imove") || im.parentNode).getBoundingClientRect();
        if (r.bottom < -100 || r.top > vh + 100) return;
        var p = (r.top + r.height / 2 - vh / 2) / vh;
        im.style.transform = "translate3d(0," + (p * -5).toFixed(2) + "%,0)";
      });
    };
    onFrame(drift);
    window.addEventListener("resize", drift);
    drift();
  }
})();
