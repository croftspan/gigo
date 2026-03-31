/* GIGO — Shared JS */

(function () {
  'use strict';

  /* --- Prevent transition flash on load --- */
  document.body.classList.add('no-transition');

  /* --- Dark/Light Theme Toggle --- */
  var toggle = document.getElementById('theme-toggle');
  var root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem('gigo-theme', theme);
    if (toggle) {
      var sun = toggle.querySelector('.icon-sun');
      var moon = toggle.querySelector('.icon-moon');
      if (sun && moon) {
        sun.style.display = theme === 'dark' ? 'block' : 'none';
        moon.style.display = theme === 'dark' ? 'none' : 'block';
      }
    }
  }

  var saved = localStorage.getItem('gigo-theme');
  applyTheme(saved || 'dark');

  /* Re-enable transitions after first paint */
  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      document.body.classList.remove('no-transition');
    });
  });

  if (toggle) {
    toggle.addEventListener('click', function () {
      var current = root.getAttribute('data-theme');
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  /* --- Footer Version (from GitHub latest tag, cached 1hr) --- */
  (function setVersion() {
    var cached = localStorage.getItem('gigo-version');
    var cacheTime = localStorage.getItem('gigo-version-time');
    var oneHour = 3600000;

    function apply(ver) {
      document.querySelectorAll('.site-footer .container > span').forEach(function (el) {
        el.childNodes.forEach(function (node) {
          if (node.nodeType === 3 && /v[\d.]+/.test(node.textContent)) {
            node.textContent = node.textContent.replace(/v[\d.]+/, ver);
          }
        });
      });
    }

    if (cached && cacheTime && Date.now() - Number(cacheTime) < oneHour) {
      apply(cached);
      return;
    }

    fetch('https://api.github.com/repos/croftspan/gigo/tags?per_page=1')
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (tags) {
        if (tags && tags[0] && tags[0].name) {
          localStorage.setItem('gigo-version', tags[0].name);
          localStorage.setItem('gigo-version-time', String(Date.now()));
          apply(tags[0].name);
        }
      })
      .catch(function () {});
  })();

  /* --- Mobile Nav Toggle --- */
  var navToggle = document.getElementById('nav-toggle');
  var navMenu = document.getElementById('nav-menu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', function () {
      var isOpen = navMenu.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
  }
})();
