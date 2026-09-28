/* The Overlook — the inquiry form. Loaded by core.js when the page is idle
   or on the first tap of an inquiry control, never in the critical path. */
(function () {
  "use strict";

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
      /* data-endpoint on the <form> posts JSON to the relay; without it the
         native action handles the submit */
      var endpoint = form.dataset.endpoint;
      if (!endpoint) return;
      e.preventDefault();
      var status = form.querySelector(".formstatus");
      var data = Object.fromEntries(new FormData(form).entries());
      data.source = location.pathname;
      data.submittedAt = new Date().toISOString();
      fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      }).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        form.reset();
        status.textContent = "Thank you — your inquiry is in. You'll hear back, usually within one business day.";
        status.classList.add("is-on");
      }).catch(function () {
        status.textContent = "Something went wrong sending that. Please email us directly and we'll pick it up from there.";
        status.classList.add("is-on");
      });
    });
  }
})();
