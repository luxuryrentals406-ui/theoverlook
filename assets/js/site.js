/* The Overlook — progressive enhancement only. Everything works without it. */
(function () {
  "use strict";

  /* ---- sticky header ------------------------------------------------- */
  var hdr = document.querySelector(".hdr");
  if (hdr) {
    var onScroll = function () {
      hdr.classList.toggle("is-stuck", window.scrollY > 40);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---- mobile menu --------------------------------------------------- */
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
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    document.body.classList.remove("menu-open");
    if (burger) burger.setAttribute("aria-expanded", "false");
    closeLightbox();
  });

  /* ---- accordions ---------------------------------------------------- */
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

  /* ---- reveal on scroll ---------------------------------------------- */
  var rv = document.querySelectorAll(".rv");
  if (rv.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.classList.add("is-in");
        io.unobserve(en.target);
      });
      /* threshold 0, not 0.06: a wipe box whose lazy image has not loaded yet
         has no height, and a zero-area target never reaches a ratio at all. */
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

  /* ---- gallery filter ------------------------------------------------ */
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
      visible = null; /* invalidate lightbox cache */
    });
  }

  /* ---- lightbox ------------------------------------------------------ */
  var lb = document.querySelector(".lbox");
  var lbImg = lb && lb.querySelector("img");
  var visible = null;
  var idx = 0;

  function shown() {
    if (!visible) {
      visible = Array.prototype.filter.call(
        document.querySelectorAll(".grid figure"),
        function (f) { return !f.hidden; }
      );
    }
    return visible;
  }
  function show(i) {
    var list = shown();
    if (!list.length) return;
    idx = (i + list.length) % list.length;
    var f = list[idx];
    var full = f.dataset.full || f.querySelector("img").src;
    lbImg.src = full;
    lbImg.alt = f.querySelector("img").alt || "";
    var meta = lb.querySelector(".lbox__meta");
    if (meta) {
      meta.innerHTML = "<b>" + (f.querySelector("img").alt || "") + "</b>" +
                       (idx + 1) + " of " + list.length;
    }
    /* quietly warm the neighbours so arrowing through never stalls */
    [list[(idx + 1) % list.length], list[(idx - 1 + list.length) % list.length]]
      .forEach(function (n) {
        if (!n) return;
        var im = new Image();
        im.src = n.dataset.full || n.querySelector("img").src;
      });
  }
  function closeLightbox() {
    if (lb) lb.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  if (lb) {
    document.querySelectorAll(".grid figure").forEach(function (fig) {
      fig.addEventListener("click", function () {
        visible = null;
        show(shown().indexOf(fig));
        lb.classList.add("is-open");
        document.body.style.overflow = "hidden";
      });
    });
    lb.querySelector(".lbox__x").addEventListener("click", closeLightbox);
    lb.querySelector(".lbox__p").addEventListener("click", function (e) { e.stopPropagation(); show(idx - 1); });
    lb.querySelector(".lbox__n").addEventListener("click", function (e) { e.stopPropagation(); show(idx + 1); });
    lb.addEventListener("click", function (e) { if (e.target === lb) closeLightbox(); });
    document.addEventListener("keydown", function (e) {
      if (!lb.classList.contains("is-open")) return;
      if (e.key === "ArrowLeft") show(idx - 1);
      if (e.key === "ArrowRight") show(idx + 1);
    });
  }

  /* ---- inquiry form -------------------------------------------------- */
  /* Prefill event type from ?type=corporate / ?type=wedding */
  var params = new URLSearchParams(window.location.search);
  var typeSel = document.getElementById("eventType");
  if (typeSel && params.get("type")) {
    var want = params.get("type").toLowerCase();
    Array.prototype.forEach.call(typeSel.options, function (o) {
      if (o.value.toLowerCase().indexOf(want) > -1) typeSel.value = o.value;
    });
  }

  var form = document.getElementById("inquiry");
  if (form) {
    form.addEventListener("submit", function (e) {
      /* WEBHOOK: set data-endpoint on the <form> to POST as JSON instead of
         falling through to the plain mailto/Formspree action. */
      var endpoint = form.dataset.endpoint;
      if (!endpoint) return; /* let the native action handle it */
      e.preventDefault();
      var status = form.querySelector(".formstatus");
      var data = Object.fromEntries(new FormData(form).entries());
      data.source = "theoverlookatflatheadlake.com";
      data.submittedAt = new Date().toISOString();
      fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      }).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        form.reset();
        status.textContent = "Thank you — your inquiry is in. You'll hear back personally, usually within one business day.";
        status.classList.add("is-on");
      }).catch(function () {
        status.textContent = "Something went wrong sending that. Please email us directly and we'll pick it up from there.";
        status.classList.add("is-on");
      });
    });
  }
})();


/* ==================================================================
   Interactive layer. Everything below is enhancement — with JS off the
   map panels stack, the bar never shows, the counters read their final
   numbers, and the site still works end to end.
   ================================================================== */
(function () {
  "use strict";
  var reduced = window.matchMedia &&
                window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- scroll progress ----------------------------------------------- */
  var bar = document.querySelector(".prog i");
  if (bar) {
    var tick = function () {
      var d = document.documentElement;
      var max = d.scrollHeight - d.clientHeight;
      bar.style.width = (max > 0 ? (d.scrollTop / max) * 100 : 0) + "%";
    };
    tick();
    window.addEventListener("scroll", tick, { passive: true });
    window.addEventListener("resize", tick);
  }

  /* ---- count-up stats ------------------------------------------------ */
  var nums = document.querySelectorAll("[data-count]");
  if (nums.length && "IntersectionObserver" in window && !reduced) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var el = en.target, target = parseInt(el.dataset.count, 10), t0 = null;
        var step = function (ts) {
          if (!t0) t0 = ts;
          var p = Math.min((ts - t0) / 1100, 1);
          var eased = 1 - Math.pow(1 - p, 3);          /* ease-out cubic */
          el.textContent = Math.round(target * eased);
          if (p < 1) requestAnimationFrame(step);
          else el.textContent = target;
        };
        requestAnimationFrame(step);
        cio.unobserve(el);
      });
    }, { threshold: 0.6 });
    nums.forEach(function (n) { cio.observe(n); });
  }

  /* ---- property map -------------------------------------------------- */
  var map = document.querySelector(".vmap");
  if (map) {
    var pins = Array.prototype.slice.call(map.querySelectorAll(".vmap__pin"));
    var panels = Array.prototype.slice.call(map.querySelectorAll(".vmap__panel"));

    var select = function (i) {
      map.classList.add("is-touched");        /* stops the idle pulse for good */
      pins.forEach(function (p, n) {
        p.setAttribute("aria-selected", n === i ? "true" : "false");
        p.tabIndex = n === i ? 0 : -1;
      });
      panels.forEach(function (p, n) { p.hidden = n !== i; });
    };

    pins.forEach(function (pin, i) {
      pin.tabIndex = i === 0 ? 0 : -1;
      pin.addEventListener("click", function () { select(i); });
      /* hovering is enough on a mouse; on touch the tap does it */
      pin.addEventListener("mouseenter", function () {
        if (window.matchMedia("(hover: hover)").matches) select(i);
      });
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

  /* ---- sticky inquiry bar -------------------------------------------- */
  var sbar = document.querySelector(".sbar");
  if (sbar && !/contact\.html/.test(location.pathname)) {
    var dismissed = false;
    try { dismissed = sessionStorage.getItem("sbar-off") === "1"; } catch (e) {}
    if (!dismissed) {
      sbar.hidden = false;
      var watch = function () {
        var d = document.documentElement;
        var max = d.scrollHeight - d.clientHeight;
        var pct = max > 0 ? d.scrollTop / max : 0;
        /* show once they are invested, hide again at the footer's own CTA */
        sbar.classList.toggle("is-up", pct > 0.42 && pct < 0.93);
      };
      watch();
      window.addEventListener("scroll", watch, { passive: true });
      sbar.querySelector(".sbar__x").addEventListener("click", function () {
        sbar.classList.remove("is-up");
        window.removeEventListener("scroll", watch);
        try { sessionStorage.setItem("sbar-off", "1"); } catch (e) {}
      });
    }
  }

  /* ---- swipe the lightbox on touch ----------------------------------- */
  var lb2 = document.querySelector(".lbox");
  if (lb2 && window.PointerEvent) {
    var x0 = null;
    lb2.addEventListener("pointerdown", function (e) { x0 = e.clientX; });
    lb2.addEventListener("pointerup", function (e) {
      if (x0 === null) return;
      var dx = e.clientX - x0;
      x0 = null;
      if (Math.abs(dx) < 45) return;
      var btn = lb2.querySelector(dx < 0 ? ".lbox__n" : ".lbox__p");
      if (btn) btn.click();
    });
  }
})();


/* ==================================================================
   Motion layer. Added 2026-09-18. Cinematic hero, scroll parallax,
   magnetic buttons, gallery cursor, page transitions. All of it is
   enhancement — none of it gates content.
   ================================================================== */
(function () {
  "use strict";

  var reduced = window.matchMedia &&
                window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var fine = !window.matchMedia || window.matchMedia("(hover: hover)").matches;

  /* ---- rAF-batched scroll bus, so every effect shares one listener --- */
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

  /* ---- hero: cross-fade the frames, Ken Burns each one --------------- */
  var stack = document.querySelector(".hero__bg--multi");
  if (stack && !reduced) {
    var frames = Array.prototype.slice.call(stack.querySelectorAll(".hero__frame"));
    var dots = Array.prototype.slice.call(document.querySelectorAll(".hero__dot"));
    var cur = 0, timer = null;

    var goTo = function (n) {
      cur = (n + frames.length) % frames.length;
      frames.forEach(function (f, i) {
        f.classList.toggle("is-on", i === cur);
        /* restart the zoom so each frame gets the whole move, not the tail */
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

    /* warm the next frame so the cross-fade never shows a blank */
    frames.slice(1).forEach(function (f) {
      var im = new Image();
      im.src = f.querySelector("img").getAttribute("src");
    });

    dots.forEach(function (d, i) {
      d.addEventListener("click", function () { pause(); goTo(i); play(); });
    });
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) pause(); else if (!timer) play();
    });
    play();
  }

  /* ---- hero parallax: background lags, copy lifts and dissolves ------ */
  /* Phones get inset:0 on the hero background (see site.css), so there is no
     headroom to slide into — and parallax on a touch scroll is jittery anyway. */
  var wideEnough = !window.matchMedia || window.matchMedia("(min-width:641px)").matches;
  var heroes = document.querySelectorAll(".hero[data-parallax]");
  if (heroes.length && !reduced && wideEnough) {
    heroes.forEach(function (h) {
      var bg = h.querySelector(".hero__bg");
      var copy = h.querySelector(".hero__in");
      var was = null;
      onFrame(function (y) {
        var height = h.offsetHeight;
        /* clamp rather than bail, or scrolling past freezes it mid-slide */
        var t = y < height ? y : height;
        if (t === was) return;                  /* off screen, stop paying for it */
        was = t;
        /* 0.16 keeps the shift inside the 20% of headroom the box was given */
        if (bg) bg.style.transform = "translate3d(0," + (t * 0.16).toFixed(1) + "px,0)";
        if (copy) {
          /* the copy lifts away rather than sinking, so it is never clipped */
          copy.style.transform = "translate3d(0," + (-t * 0.12).toFixed(1) + "px,0)";
          copy.style.opacity = Math.max(0, 1 - (t / (height * 0.58)));
        }
        h.classList.toggle("is-scrolled", y > 90);
      });
    });
  }

  /* ---- slow drift on full-bleed band backgrounds --------------------- */
  var drifts = document.querySelectorAll("[data-drift]");
  if (drifts.length && !reduced) {
    drifts.forEach(function (el) {
      var im = el.querySelector("img");
      if (!im) return;
      im.style.willChange = "transform";
      im.style.height = "116%";
      im.style.top = "-8%";
      im.style.position = "absolute";
      onFrame(function (y) {
        var r = el.getBoundingClientRect();
        if (r.bottom < 0 || r.top > window.innerHeight) return;
        /* -1 at the top of the viewport, +1 at the bottom */
        var p = (r.top + r.height / 2 - window.innerHeight / 2) / window.innerHeight;
        im.style.transform = "translate3d(0," + (p * 7).toFixed(2) + "%,0)";
      });
    });
  }

  /* ---- header steps out of the way going down ------------------------ */
  var hdr2 = document.querySelector(".hdr");
  if (hdr2) {
    var last = window.pageYOffset;
    onFrame(function (y) {
      if (document.body.classList.contains("menu-open")) return;
      var down = y > last && y > 260;
      hdr2.classList.toggle("is-away", down);
      last = y;
    });
  }

  /* ---- reveal anything else that draws itself in --------------------- */
  var extras = document.querySelectorAll(".rule");
  if (extras.length && "IntersectionObserver" in window) {
    var rio = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add("is-in");
        rio.unobserve(e.target);
      });
    }, { threshold: 0.4 });
    extras.forEach(function (el) { rio.observe(el); });
  }

  /* ---- stagger containers deeper than the CSS ladder ----------------- */
  document.querySelectorAll(".rv--stagger").forEach(function (box) {
    var kids = box.children;
    for (var i = 6; i < kids.length; i++) {
      kids[i].style.transitionDelay = Math.min(i * 0.09, 0.8) + "s";
    }
  });

  /* ---- buttons lean toward the cursor -------------------------------- */
  if (fine && !reduced) {
    document.querySelectorAll(".btn").forEach(function (b) {
      var pull = 5;
      b.addEventListener("pointermove", function (e) {
        var r = b.getBoundingClientRect();
        var dx = (e.clientX - (r.left + r.width / 2)) / (r.width / 2);
        var dy = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
        b.style.transition = "transform .18s linear, background .35s, color .35s, border-color .35s";
        b.style.transform = "translate(" + (dx * pull).toFixed(1) + "px," +
                                           (dy * pull * 0.6).toFixed(1) + "px)";
      });
      b.addEventListener("pointerleave", function () {
        b.style.transition = "";
        b.style.transform = "";
      });
    });
  }

  /* ---- pages hand off to each other instead of blinking -------------- */
  if (!reduced) {
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a");
      if (!a) return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
      if (a.target === "_blank" || a.hasAttribute("download")) return;
      var href = a.getAttribute("href") || "";
      if (!href || href.charAt(0) === "#" || /^(mailto|tel|https?):/.test(href)) return;
      if (a.origin && a.origin !== location.origin) return;
      e.preventDefault();
      document.documentElement.classList.add("is-leaving");
      setTimeout(function () { location.href = a.href; }, 300);
    });
    /* coming back via the back button must not land on a faded-out page */
    window.addEventListener("pageshow", function () {
      document.documentElement.classList.remove("is-leaving");
    });
  }
})();


/* ==================================================================
   Interactive components — added 2026-09-19.
   Building picker, drag rail, hover mosaic. Each already renders its
   full contents in HTML; this only turns them into controls.
   ================================================================== */
(function () {
  "use strict";
  var fine = !window.matchMedia || window.matchMedia("(hover: hover)").matches;

  /* ---- building picker ----------------------------------------------- */
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

    /* thumbnails swap the big photograph within their own panel */
    panels.forEach(function (panel) {
      var stage = panel.querySelector(".sw__stage");
      var big = panel.querySelector(".sw__big");
      var thumbs = [].slice.call(panel.querySelectorAll(".sw__thumb"));
      thumbs.forEach(function (th) {
        th.addEventListener("click", function () {
          if (th.classList.contains("is-on")) return;
          thumbs.forEach(function (o) { o.classList.toggle("is-on", o === th); });
          var next = new Image();
          next.onload = function () {
            big.src = th.dataset.src;
            big.alt = th.dataset.alt || "";
            stage.classList.remove("is-swapping");
          };
          /* fade out first, but only actually swap once the file is here */
          stage.classList.add("is-swapping");
          next.src = th.dataset.src;
          if (next.complete) next.onload();
        });
      });
    });
  });

  /* ---- drag rail ------------------------------------------------------ */
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
        down = true; moved = 0;
        x0 = e.clientX; left0 = track.scrollLeft;
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
      /* a drag must not also register as a click on whatever is underneath */
      track.addEventListener("click", function (e) {
        if (moved > 8) { e.preventDefault(); e.stopPropagation(); }
      }, true);
    }
  });

  /* ---- hover mosaic --------------------------------------------------- */
  document.querySelectorAll(".mos").forEach(function (mos) {
    var cells = [].slice.call(mos.querySelectorAll(".mos__cell"));
    var open = function (i) {
      cells.forEach(function (c, n) { c.classList.toggle("is-on", n === i); });
    };
    cells.forEach(function (c, i) {
      /* pointer on a mouse, tap on a touch screen, focus for the keyboard */
      if (fine) c.addEventListener("pointerenter", function () { open(i); });
      c.addEventListener("click", function () { open(i); });
      c.addEventListener("focus", function () { open(i); });
    });
  });
})();


/* ==================================================================
   Slide-through gallery (The Driftwood). Added 2026-09-19.
   Arrows, thumbnails, category filter, keyboard and swipe. Captions
   ride on data-caps so the markup stays the single source of truth.
   ================================================================== */
(function () {
  "use strict";
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

    /* A native lazy <img> inside a hidden slide has not loaded by the time we
       reveal it, so load the current frame and both neighbours by hand. */
    function load(i) {
      var im = slides[i] && slides[i].querySelector("img");
      if (im && !im.getAttribute("src") && im.dataset.src) im.src = im.dataset.src;
    }

    function show(p) {
      if (!live.length) return;
      pos = (p + live.length) % live.length;
      var idx = live[pos];
      load(idx);
      load(live[(pos + 1) % live.length]);
      load(live[(pos - 1 + live.length) % live.length]);
      slides.forEach(function (s, i) { s.classList.toggle("is-on", i === idx); });
      thumbs.forEach(function (t, i) { t.classList.toggle("is-on", i === idx); });
      if (cap) cap.textContent = caps[idx] || "";
      if (cnt) cnt.textContent = pad(pos + 1) + " / " + pad(live.length);
      var t = thumbs[idx];
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

    cats.forEach(function (c) {
      c.addEventListener("click", function () { filter(c.dataset.cat); });
    });
    thumbs.forEach(function (t, i) {
      t.addEventListener("click", function () {
        var p = live.indexOf(i);
        if (p > -1) show(p);
      });
    });
    shw.querySelectorAll(".shw__arrow").forEach(function (b) {
      b.addEventListener("click", function () { show(pos + (+b.dataset.dir)); });
    });
    shw.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); show(pos - 1); }
      if (e.key === "ArrowRight") { e.preventDefault(); show(pos + 1); }
    });
    var x0 = null, stage = shw.querySelector(".shw__stage");
    if (stage && window.PointerEvent) {
      stage.addEventListener("pointerdown", function (e) { x0 = e.clientX; });
      stage.addEventListener("pointerup", function (e) {
        if (x0 === null) return;
        var dx = e.clientX - x0;
        x0 = null;
        if (Math.abs(dx) > 45) show(pos + (dx < 0 ? 1 : -1));
      });
    }
    show(0);
  });
})();


/* ==================================================================
   Zoom + image motion. Added 2026-09-19.
   Every framed photograph opens full size, the hover cue is the
   estate's mark, and images drift a little as they pass the viewport.
   ================================================================== */
(function () {
  "use strict";
  var reduced = window.matchMedia &&
                window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var fine = !window.matchMedia ||
             (window.matchMedia("(hover: hover)").matches && window.innerWidth > 860);

  /* ---- mark every framed photograph as zoomable ---------------------- */
  var SELECTORS = [".split__img", ".split__media > img", ".exp__img", ".rail__shot",
                   ".add__img", ".sw__stage", ".shw__stage", ".vmap__shot",
                   ".band__bg"];
  var zoomables = [];
  SELECTORS.forEach(function (sel) {
    document.querySelectorAll(sel).forEach(function (el) {
      var im = el.tagName === "IMG" ? el : el.querySelector("img");
      if (!im || el.closest(".lbox")) return;
      /* a photograph inside a link or a button already does something when you
         click it — promising "enlarge" there would be a lie */
      if (el.closest("a,button")) return;
      el.setAttribute("data-zoom", "");
      zoomables.push({ box: el, img: im });
    });
  });

  document.querySelectorAll(".mos__cell").forEach(function (cell) {
    var im = cell.querySelector("img");
    if (im) zoomables.push({ box: cell, img: im, onlyWhenOpen: true });
  });

  /* The gallery runs its own filtered lightbox, so it is not in `zoomables`,
     but its tiles enlarge too and should carry the same cue. */
  var cursorBoxes = zoomables.map(function (z) { return z.box; });
  document.querySelectorAll(".grid figure").forEach(function (f) {
    cursorBoxes.push(f);
    f.setAttribute("data-zoom", "");
  });

  /* ---- the mark that follows the cursor ------------------------------ */
  if (cursorBoxes.length && fine) {
    var cur = document.createElement("div");
    cur.className = "gcursor";
    cur.setAttribute("aria-hidden", "true");
    cur.innerHTML = '<img src="assets/img/overlook-mark.png" alt="">';
    document.body.appendChild(cur);
    var move = function (e) {
      cur.style.left = e.clientX + "px";
      cur.style.top = e.clientY + "px";
    };
    var drop = function () {
      cur.classList.remove("is-on");
      document.removeEventListener("pointermove", move);
    };
    cursorBoxes.forEach(function (box) {
      box.addEventListener("pointerenter", function (e) {
        if (box.classList.contains("mos__cell") && !box.classList.contains("is-on")) return;
        move(e);
        cur.classList.add("is-on");
        document.addEventListener("pointermove", move);
      });
      box.addEventListener("pointerleave", drop);
      box.addEventListener("pointermove", function (e) {
        if (!box.classList.contains("mos__cell")) return;
        if (box.classList.contains("is-on") && !cur.classList.contains("is-on")) {
          cur.classList.add("is-on");
          document.addEventListener("pointermove", move);
        }
        move(e);
      });
    });
    window.addEventListener("scroll", drop, { passive: true });
    document.addEventListener("pointerleave", drop);
  }

  /* ---- open any of them in the shared lightbox ----------------------- */
  var lb = document.querySelector(".lbox");
  if (lb && zoomables.length) {
    var lbImg = lb.querySelector("img");
    var meta = lb.querySelector(".lbox__meta");
    var onGallery = !!document.querySelector(".grid figure");
    var at = 0;

    /* the gallery page already runs its own filtered lightbox; leave it alone */
    if (!onGallery) {
      var show = function (i) {
        at = (i + zoomables.length) % zoomables.length;
        var z = zoomables[at];
        lbImg.src = z.img.currentSrc || z.img.src;
        lbImg.alt = z.img.alt || "";
        if (meta) meta.innerHTML = "<b>" + (z.img.alt || "") + "</b>" +
                                   (at + 1) + " of " + zoomables.length;
      };
      var close = function () {
        lb.classList.remove("is-open");
        document.body.style.overflow = "";
      };
      zoomables.forEach(function (z, i) {
        /* the mosaic's own handler opens the cell on click, and it is registered
           first — so read the state before that runs, not after */
        if (z.onlyWhenOpen) {
          z.box.addEventListener("pointerdown", function () {
            z.wasOpen = z.box.classList.contains("is-on");
          });
        }
        z.box.addEventListener("click", function (e) {
          /* a mosaic cell has to be open before it is only a photograph */
          if (z.onlyWhenOpen) {
            if (!z.wasOpen) return;
          } else if (e.target.closest("button,a")) {
            /* don't hijack a control that happens to sit on a photograph */
            return;
          }
          show(i);
          lb.classList.add("is-open");
          document.body.style.overflow = "hidden";
        });
      });
      lb.querySelector(".lbox__x").addEventListener("click", close);
      lb.querySelector(".lbox__p").addEventListener("click", function (e) {
        e.stopPropagation(); show(at - 1);
      });
      lb.querySelector(".lbox__n").addEventListener("click", function (e) {
        e.stopPropagation(); show(at + 1);
      });
      lb.addEventListener("click", function (e) { if (e.target === lb) close(); });
      document.addEventListener("keydown", function (e) {
        if (!lb.classList.contains("is-open")) return;
        if (e.key === "Escape") close();
        if (e.key === "ArrowLeft") show(at - 1);
        if (e.key === "ArrowRight") show(at + 1);
      });
    }
  }

  /* ---- photographs drift inside their frame as you scroll ------------ */
  if (!reduced) {
    var movers = [];
    zoomables.forEach(function (z) {
      /* skip the ones that already have their own motion */
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
      var queued = false;
      var tick = function () {
        queued = false;
        var vh = window.innerHeight;
        movers.forEach(function (im) {
          var r = im.parentNode.getBoundingClientRect();
          if (r.bottom < -100 || r.top > vh + 100) return;
          /* -1 entering from the bottom, +1 leaving at the top */
          var p = (r.top + r.height / 2 - vh / 2) / vh;
          im.style.transform = "translate3d(0," + (p * -5).toFixed(2) + "%,0)";
        });
      };
      window.addEventListener("scroll", function () {
        if (queued) return;
        queued = true;
        requestAnimationFrame(tick);
      }, { passive: true });
      window.addEventListener("resize", tick);
      tick();
    }
  }
})();
