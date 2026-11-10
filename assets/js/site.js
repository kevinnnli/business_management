/* Navigation behaviour: mobile drawer, collapsible unit groups, topic filter. */
(function () {
  "use strict";
  var body = document.body;
  var menuBtn = document.querySelector(".menu-btn");
  var sidebar = document.getElementById("sidebar");
  var scrim = document.querySelector(".scrim");
  var mobile = window.matchMedia("(max-width: 960px)");

  function setDrawer(open) {
    body.classList.toggle("nav-open", open);
    menuBtn.setAttribute("aria-expanded", String(open));
    scrim.hidden = !open;
    if (open) {
      var current = sidebar.querySelector('[aria-current="page"]') || sidebar.querySelector("input, a");
      if (current) current.focus();
    }
  }

  if (menuBtn && sidebar && scrim) {
    menuBtn.addEventListener("click", function () {
      setDrawer(!body.classList.contains("nav-open"));
    });
    scrim.addEventListener("click", function () { setDrawer(false); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && body.classList.contains("nav-open")) {
        setDrawer(false);
        menuBtn.focus();
      }
    });
    mobile.addEventListener && mobile.addEventListener("change", function (e) {
      if (!e.matches) setDrawer(false);
    });
  }

  // If a hosted image cannot load, replace the broken icon with a plain link to it.
  function imageFallback(img) {
    var fig = img.closest(".figure");
    if (!fig || fig.classList.contains("figure--missing")) return;
    fig.classList.add("figure--missing");
    var a = document.createElement("a");
    a.href = img.currentSrc || img.src;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = "View image: " + (img.alt || "figure");
    fig.innerHTML = "";
    fig.appendChild(a);
  }
  document.querySelectorAll(".figure img").forEach(function (img) {
    if (img.complete && img.naturalWidth === 0 && img.src) imageFallback(img);
    else img.addEventListener("error", function () { imageFallback(img); });
  });

  // Unit groups
  document.querySelectorAll(".nav__toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var group = btn.closest(".nav__group");
      var open = btn.getAttribute("aria-expanded") !== "true";
      btn.setAttribute("aria-expanded", String(open));
      group.setAttribute("data-open", String(open));
    });
  });

  // Keep the current page visible in a long sidebar
  var cur = sidebar && sidebar.querySelector('[aria-current="page"]');
  if (cur && !mobile.matches && cur.scrollIntoView) {
    var r = cur.getBoundingClientRect();
    if (r.bottom > window.innerHeight) cur.scrollIntoView({ block: "center" });
  }

  // Topic filter
  var input = document.getElementById("nav-filter");
  if (!input) return;
  var groups = Array.prototype.slice.call(document.querySelectorAll(".nav__list > li"));
  var empty = document.createElement("p");
  empty.className = "nav__empty";
  empty.setAttribute("role", "status");
  empty.hidden = true;
  empty.textContent = "No matching topics.";
  document.querySelector(".nav").appendChild(empty);

  function norm(s) { return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }

  input.addEventListener("input", function () {
    var q = norm(input.value.trim());
    var any = false;
    groups.forEach(function (li) {
      var top = li.querySelector(".nav__row a");
      var topHit = !q || norm(top.textContent).indexOf(q) !== -1;
      var subs = li.querySelectorAll(".nav__sub li");
      var subHit = false;
      subs.forEach(function (s) {
        var hit = !q || topHit || norm(s.textContent).indexOf(q) !== -1;
        s.hidden = !hit;
        if (hit && q) subHit = true;
      });
      var show = topHit || subHit;
      li.hidden = !show;
      if (show) any = true;
      var btn = li.querySelector(".nav__toggle");
      if (btn) {
        if (q && subHit) {
          li.setAttribute("data-open", "true");
          btn.setAttribute("aria-expanded", "true");
        } else if (!q) {
          var keep = !!li.querySelector('[aria-current="page"]');
          li.setAttribute("data-open", String(keep));
          btn.setAttribute("aria-expanded", String(keep));
        }
      }
    });
    empty.hidden = any;
  });
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      var first = sidebar.querySelector(".nav__list li:not([hidden]) .nav__sub li:not([hidden]) a, .nav__list > li:not([hidden]) a");
      if (first) first.click();
    }
  });
})();
