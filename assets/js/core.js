/* The Overlook — core. Every device gets this file; it is the controls.
   Progressive enhancement only: with JS off the menu is a list, the map
   panels stack, the pickers show everything, and the site still works. */
(function () {
  "use strict";
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var fine = !window.matchMedia || window.matchMedia("(hover: hover)").matches;

  /* ---- one rAF-batched scroll bus for everything that watches scroll --- */
  var subs = [], queued = false;
  function onScroll(fn) { subs.push(fn); }
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

  /* ---- header: sticks after 40px, steps away going down ---------------- */
  var hdr = document.querySelector(".hdr");
  if (hdr) {
    var last = window.pageYOffset;
    var head = function (y) {
      hdr.classList.toggle("is-stuck", y > 40);
      if (!document.body.classList.contains("menu-open")) {
        hdr.classList.toggle("is-away", y > last && y > 260);
      }
      last = y;
    };
    head(last);
    onScroll(head);
  }

  /* ---- mobile menu ------------------------------------------------------ */
  var burger = document.querySelector(".burger");
  if (burger) {
    burger.addEventListener("click", function () {
      var open = document.body.classList.toggle("menu-open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.querySelectorAll(".mobnav a").forEach(function (a) {
      a.addEventListener("click", function () {
        document.body.classList.remove("menu-open");
        burger.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ---- accordions ------------------------------------------------------- */
  document.querySelectorAll(".acc__q").forEach(function (q) {
    q.addEventListener("click", function () {
      var item = q.closest(".acc__item");
      var panel = item.querySelector(".acc__a");
      var open = item.classList.toggle("is-open");
      q.setAttribute("aria-expanded", open ? "true" : "false");
      panel.style.maxHeight = open ? panel.scrollHeight + "px" : "0px";
    });
  });
  window.addEventListener("resize", function () {
    document.querySelectorAll(".acc__item.is-open .acc__a").forEach(function (p) {
      p.style.maxHeight = p.scrollHeight + "px";
    });
  });

  /* ---- reveal on scroll ------------------------------------------------- */
  var rv = document.querySelectorAll(".rv,.rule");
  if (rv.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.classList.add("is-in");
        io.unobserve(en.target);
      });
      /* threshold 0: a wipe box whose lazy image has not loaded yet has no
         height, and a zero-area target never reaches a ratio at all */
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0 });
    rv.forEach(function (el) { io.observe(el); });
  } else {
    rv.forEach(function (el) { el.classList.add("is-in"); });
  }
  /* a reveal that somehow never fired must not leave a hole in the page */
  window.addEventListener("load", function () {
    document.querySelectorAll(".rv:not(.is-in)").forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < window.innerHeight && r.bottom > 0) el.classList.add("is-in");
    });
  });
  /* stagger containers deeper than the CSS ladder */
  document.querySelectorAll(".rv--stagger").forEach(function (box) {
    var kids = box.children;
    for (var i = 6; i < kids.length; i++) {
      kids[i].style.transitionDelay = Math.min(i * 0.09, 0.8) + "s";
    }
  });

  /* ---- count-up stats --------------------------------------------------- */
  var nums = document.querySelectorAll("[data-count]");
  if (nums.length && "IntersectionObserver" in window && !reduced) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target, target = parseInt(el.dataset.count, 10), t0 = null;
        var step = function (ts) {
          if (!t0) t0 = ts;
          var p = Math.min((ts - t0) / 1100, 1);
          el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
          if (p < 1) requestAnimationFrame(step); else el.textContent = target;
        };
        requestAnimationFrame(step);
        cio.unobserve(el);
      });
    }, { threshold: 0.6 });
    nums.forEach(function (n) { cio.observe(n); });
  }

  /* ---- lightbox (gallery) ----------------------------------------------- */
  /* Pictures come from the derivative set: assets/img/x.jpg -> assets/i/x-1200.avif.
     The <picture> in the lightbox has two empty <source>s waiting for srcsets. */
  var lb = document.querySelector(".lbox");
  var lbImg = lb && lb.querySelector("img");
  var visible = null, idx = 0;

  function shown() {
    if (!visible) {
      visible = Array.prototype.filter.call(
        document.querySelectorAll(".grid figure"), function (f) { return !f.hidden; });
    }
    return visible;
  }
  function setLightbox(full, stem, alt, metaHtml) {
    var avif = lb.querySelector("source[type='image/avif']");
    var webp = lb.querySelector("source[type='image/webp']");
    if (stem && avif && webp) {
      var dir = full.replace(/assets\/img\/.*$/, "assets/i/") + stem;
      avif.srcset = dir + "-1200.avif 1200w, " + dir + "-1920.avif 1920w";
      webp.srcset = dir + "-1200.webp 1200w";
    } else if (avif && webp) {
      avif.removeAttribute("srcset");
      webp.removeAttribute("srcset");
    }
    lbImg.src = full;
    lbImg.alt = alt || "";
    var meta = lb.querySelector(".lbox__meta");
    if (meta) meta.innerHTML = metaHtml || "";
  }
  function show(i) {
    var list = shown();
    if (!list.length) return;
    idx = (i + list.length) % list.length;
    var f = list[idx];
    var im = f.querySelector("img");
    setLightbox(f.dataset.full || im.src, f.dataset.stem, im.alt,
                "<b>" + (im.alt || "") + "</b>" + (idx + 1) + " of " + list.length);
  }
  function openLightbox() {
    lb.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }
  function closeLightbox() {
    if (lb) lb.classList.remove("is-open");
    document.body.style.overflow = "";
  }
  if (lb) {
    var figs = document.querySelectorAll(".grid figure");
    figs.forEach(function (fig) {
      fig.addEventListener("click", function () {
        visible = null;
        show(shown().indexOf(fig));
        openLightbox();
      });
    });
    lb.querySelector(".lbox__x").addEventListener("click", closeLightbox);
    lb.querySelector(".lbox__p").addEventListener("click", function (e) { e.stopPropagation(); lb.__prev(); });
    lb.querySelector(".lbox__n").addEventListener("click", function (e) { e.stopPropagation(); lb.__next(); });
    lb.addEventListener("click", function (e) { if (e.target === lb) closeLightbox(); });
    /* the gallery drives prev/next by filtered index; other pages (cinema.js)
       swap these two functions for their own list of framed photographs */
    lb.__prev = function () { show(idx - 1); };
    lb.__next = function () { show(idx + 1); };
    lb.__set = setLightbox;
    lb.__open = openLightbox;
    lb.__close = closeLightbox;
    /* swipe on touch */
    if (window.PointerEvent) {
      var x0 = null;
      lb.addEventListener("pointerdown", function (e) { x0 = e.clientX; });
      lb.addEventListener("pointerup", function (e) {
        if (x0 === null) return;
        var dx = e.clientX - x0;
        x0 = null;
        if (Math.abs(dx) < 45) return;
        if (dx < 0) lb.__next(); else lb.__prev();
      });
    }
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      document.body.classList.remove("menu-open");
      if (burger) burger.setAttribute("aria-expanded", "false");
      closeLightbox();
    }
    if (!lb || !lb.classList.contains("is-open")) return;
    if (e.key === "ArrowLeft") lb.__prev();
    if (e.key === "ArrowRight") lb.__next();
  });

  /* ---- gallery filter --------------------------------------------------- */
  var filterBar = document.querySelector(".gfilter");
  if (filterBar) {
    filterBar.addEventListener("click", function (e) {
      var btn = e.target.closest("button");
      if (!btn) return;
      var cat = btn.dataset.filter;
      filterBar.querySelectorAll("button").forEach(function (b) {
        b.setAttribute("aria-pressed", b === btn ? "true" : "false");
      });
      document.querySelectorAll(".grid figure").forEach(function (fig) {
        fig.hidden = !(cat === "all" || fig.dataset.cat === cat);
      });
      visible = null;
    });
  }

  /* ---- property map ----------------------------------------------------- */
  var map = document.querySelector(".vmap");
  if (map) {
    var pins = [].slice.call(map.querySelectorAll(".vmap__pin"));
    var panels = [].slice.call(map.querySelectorAll(".vmap__panel"));
    var select = function (i) {
      map.classList.add("is-touched");
      pins.forEach(function (p, n) {
        p.setAttribute("aria-selected", n === i ? "true" : "false");
        p.tabIndex = n === i ? 0 : -1;
      });
      panels.forEach(function (p, n) { p.hidden = n !== i; });
    };
    pins.forEach(function (pin, i) {
      pin.tabIndex = i === 0 ? 0 : -1;
      pin.addEventListener("click", function () { select(i); });
      pin.addEventListener("mouseenter", function () { if (fine) select(i); });
      pin.addEventListener("keydown", function (e) {
        var j = null;
        if (e.key === "ArrowRight" || e.key === "ArrowDown") j = (i + 1) % pins.length;
        if (e.key === "ArrowLeft" || e.key === "ArrowUp") j = (i - 1 + pins.length) % pins.length;
        if (j === null) return;
        e.preventDefault();
        select(j);
        pins[j].focus();
      });
    });
  }

  /* ---- sticky inquiry bar ----------------------------------------------- */
  var sbar = document.querySelector(".sbar");
  if (sbar && !/contact\.html/.test(location.pathname)) {
    var dismissed = false;
    try { dismissed = sessionStorage.getItem("sbar-off") === "1"; } catch (e) {}
    if (!dismissed) {
      sbar.hidden = false;
      var watching = true;
      var watch = function () {
        if (!watching) return;
        var d = document.documentElement;
        var max = d.scrollHeight - d.clientHeight;
        var pct = max > 0 ? d.scrollTop / max : 0;
        /* show once they are invested, hide again at the footer's own CTA */
        sbar.classList.toggle("is-up", pct > 0.42 && pct < 0.93);
      };
      watch();
      onScroll(watch);
      sbar.querySelector(".sbar__x").addEventListener("click", function () {
        sbar.classList.remove("is-up");
        watching = false;
        try { sessionStorage.setItem("sbar-off", "1"); } catch (e) {}
      });
    }
  }

  /* ---- building picker -------------------------------------------------- */
  document.querySelectorAll(".sw").forEach(function (sw) {
    var tabs = [].slice.call(sw.querySelectorAll(".sw__tab"));
    var panels = [].slice.call(sw.querySelectorAll(".sw__panel"));
    var select = function (i) {
      tabs.forEach(function (t, n) {
        t.classList.toggle("is-on", n === i);
        t.setAttribute("aria-selected", n === i ? "true" : "false");
        t.tabIndex = n === i ? 0 : -1;
      });
      panels.forEach(function (p, n) { p.hidden = n !== i; });
    };
    tabs.forEach(function (tab, i) {
      tab.tabIndex = i === 0 ? 0 : -1;
      tab.addEventListener("click", function () { select(i); });
      tab.addEventListener("keydown", function (e) {
        var j = null;
        if (e.key === "ArrowDown" || e.key === "ArrowRight") j = (i + 1) % tabs.length;
        if (e.key === "ArrowUp" || e.key === "ArrowLeft") j = (i - 1 + tabs.length) % tabs.length;
        if (j === null) return;
        e.preventDefault();
        select(j);
        tabs[j].focus();
      });
    });
    /* thumbnails reveal one of the stacked <picture>s; the browser fetches
       it, at the right size, the moment it is shown */
    panels.forEach(function (panel) {
      var stage = panel.querySelector(".sw__stage");
      var shots = [].slice.call(panel.querySelectorAll(".sw__shot"));
      var thumbs = [].slice.call(panel.querySelectorAll(".sw__thumb"));
      thumbs.forEach(function (th) {
        th.addEventListener("click", function () {
          if (th.classList.contains("is-on")) return;
          var j = +th.dataset.j;
          thumbs.forEach(function (o) { o.classList.toggle("is-on", o === th); });
          stage.classList.add("is-swapping");
          setTimeout(function () {
            shots.forEach(function (s, n) { s.hidden = n !== j; s.classList.toggle("is-on", n === j); });
            var im = shots[j] && shots[j].querySelector("img");
            var done = function () { stage.classList.remove("is-swapping"); };
            if (im && !im.complete) {
              im.loading = "eager";
              im.addEventListener("load", done, { once: true });
              im.addEventListener("error", done, { once: true });
            } else { done(); }
          }, 180);
        });
      });
    });
  });

  /* ---- drag rail ---------------------------------------------------------- */
  document.querySelectorAll(".rail").forEach(function (rail) {
    var track = rail.querySelector(".rail__track");
    var bar = rail.querySelector(".rail__bar i");
    var btns = [].slice.call(rail.querySelectorAll(".rail__btn"));
    if (!track) return;
    var step = function () {
      var item = track.querySelector(".rail__item");
      return item ? item.getBoundingClientRect().width + 16 : 320;
    };
    var sync = function () {
      var max = track.scrollWidth - track.clientWidth;
      var p = max > 0 ? track.scrollLeft / max : 0;
      if (bar) bar.style.transform = "translateX(" + (p * (100 / 0.22 - 100)) + "%)";
      btns.forEach(function (b) {
        var dir = +b.dataset.dir;
        b.disabled = dir < 0 ? track.scrollLeft < 4 : track.scrollLeft > max - 4;
      });
    };
    btns.forEach(function (b) {
      b.addEventListener("click", function () {
        track.scrollBy({ left: +b.dataset.dir * step(), behavior: "smooth" });
      });
    });
    track.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync);
    sync();
    /* grab and throw, the way a physical rail of prints would move */
    if (fine && window.PointerEvent) {
      var down = false, x0 = 0, left0 = 0, moved = 0;
      track.addEventListener("pointerdown", function (e) {
        if (e.button !== 0) return;
        down = true; moved = 0; x0 = e.clientX; left0 = track.scrollLeft;
        track.classList.add("is-dragging");
      });
      track.addEventListener("pointermove", function (e) {
        if (!down) return;
        var dx = e.clientX - x0;
        moved = Math.max(moved, Math.abs(dx));
        track.scrollLeft = left0 - dx;
      });
      var release = function () {
        if (!down) return;
        down = false;
        track.classList.remove("is-dragging");
      };
      track.addEventListener("pointerup", release);
      track.addEventListener("pointercancel", release);
      track.addEventListener("pointerleave", release);
      track.addEventListener("click", function (e) {
        if (moved > 8) { e.preventDefault(); e.stopPropagation(); }
      }, true);
    }
  });

  /* ---- hover mosaic --------------------------------------------------------- */
  document.querySelectorAll(".mos").forEach(function (mos) {
    var cells = [].slice.call(mos.querySelectorAll(".mos__cell"));
    var open = function (i) {
      cells.forEach(function (c, n) { c.classList.toggle("is-on", n === i); });
    };
    cells.forEach(function (c, i) {
      if (fine) c.addEventListener("pointerenter", function () { open(i); });
      c.addEventListener("click", function () { open(i); });
      c.addEventListener("focus", function () { open(i); });
    });
  });

  /* ---- slide-through gallery (The Driftwood) --------------------------------- */
  document.querySelectorAll(".shw").forEach(function (shw) {
    var caps = (shw.dataset.caps || "").split("|");
    var slides = [].slice.call(shw.querySelectorAll(".shw__slide"));
    var thumbs = [].slice.call(shw.querySelectorAll(".shw__thumb"));
    var cats = [].slice.call(shw.querySelectorAll(".shw__cat"));
    var cap = shw.querySelector(".shw__cap");
    var cnt = shw.querySelector(".shw__count");
    if (!slides.length) return;
    var live = slides.map(function (_, i) { return i; });
    var pos = 0;
    function pad(n) { return (n < 10 ? "0" : "") + n; }
    /* a hidden slide's <picture> waits until shown; ask the neighbours early */
    function warm(i) {
      var im = slides[i] && slides[i].querySelector("img");
      if (im && im.loading === "lazy") im.loading = "eager";
    }
    function show(p) {
      if (!live.length) return;
      pos = (p + live.length) % live.length;
      var i = live[pos];
      warm(i); warm(live[(pos + 1) % live.length]); warm(live[(pos - 1 + live.length) % live.length]);
      slides.forEach(function (s, n) { s.classList.toggle("is-on", n === i); });
      thumbs.forEach(function (t, n) { t.classList.toggle("is-on", n === i); });
      if (cap) cap.textContent = caps[i] || "";
      if (cnt) cnt.textContent = pad(pos + 1) + " / " + pad(live.length);
      var t = thumbs[i];
      if (t) t.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "smooth" });
    }
    function filter(key) {
      live = [];
      slides.forEach(function (s, i) {
        var on = key === "all" || s.dataset.cat === key;
        s.hidden = !on;
        thumbs[i].hidden = !on;
        if (on) live.push(i);
      });
      cats.forEach(function (c) {
        var on = c.dataset.cat === key;
        c.classList.toggle("is-on", on);
        c.setAttribute("aria-pressed", on ? "true" : "false");
      });
      show(0);
    }
    cats.forEach(function (c) { c.addEventListener("click", function () { filter(c.dataset.cat); }); });
    thumbs.forEach(function (t, i) {
      t.addEventListener("click", function () { var p = live.indexOf(i); if (p > -1) show(p); });
    });
    shw.querySelectorAll(".shw__arrow").forEach(function (b) {
      b.addEventListener("click", function () { show(pos + (+b.dataset.dir)); });
    });
    shw.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); show(pos - 1); }
      if (e.key === "ArrowRight") { e.preventDefault(); show(pos + 1); }
    });
    var sx = null, stage = shw.querySelector(".shw__stage");
    if (stage && window.PointerEvent) {
      stage.addEventListener("pointerdown", function (e) { sx = e.clientX; });
      stage.addEventListener("pointerup", function (e) {
        if (sx === null) return;
        var dx = e.clientX - sx;
        sx = null;
        if (Math.abs(dx) > 45) show(pos + (dx < 0 ? 1 : -1));
      });
    }
    show(0);
  });

  /* ---- spec groups fold on a phone; the heading opens them ------------------------ */
  document.querySelectorAll(".spec__t").forEach(function (t) {
    t.addEventListener("click", function () {
      var g = t.closest(".spec__g");
      var open = g.classList.toggle("is-open");
      t.setAttribute("aria-expanded", open ? "true" : "false");
    });
  });

  /* ---- section nav: the link for the section on screen is lit ---------------------- */
  var snav = document.querySelector(".snav");
  if (snav && "IntersectionObserver" in window) {
    var links = [].slice.call(snav.querySelectorAll("a[href^='#']"));
    var targets = links.map(function (a) { return document.getElementById(a.getAttribute("href").slice(1)); });
    var light = function (i) {
      links.forEach(function (a, n) { a.classList.toggle("is-on", n === i); });
      var a = links[i];
      if (a && a.scrollIntoView) a.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
    };
    var sio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        light(targets.indexOf(en.target));
      });
    }, { rootMargin: "-45% 0px -50% 0px", threshold: 0 });
    targets.forEach(function (t) { if (t) sio.observe(t); });
  }

  /* ---- the other two files ---------------------------------------------------- */
  /* inquire.js on the first tap of any inquiry control, or when the page is
     idle; cinema.js only where a mouse and a wide screen make it worth it. */
  var v = document.currentScript && document.currentScript.dataset;
  var base = (v && v.base) || "";
  var loaded = {};
  function load(name) {
    if (loaded[name]) return;
    loaded[name] = true;
    var s = document.createElement("script");
    s.src = base + "assets/js/" + name + ".js?v=" + ((v && v[name]) || "1");
    s.defer = true;
    document.head.appendChild(s);
  }
  window.__loadInquire = function () { load("inquire"); };
  if (document.getElementById("inquiry") || document.querySelector("[data-sheet]")) {
    var idle = window.requestIdleCallback || function (fn) { setTimeout(fn, 1200); };
    idle(function () { load("inquire"); });
    document.addEventListener("pointerdown", function (e) {
      if (e.target.closest && e.target.closest("[data-sheet]")) load("inquire");
    }, { passive: true });
  }
  if (!reduced && window.matchMedia && window.matchMedia("(hover: hover) and (min-width: 861px)").matches) {
    load("cinema");
  }
})();
