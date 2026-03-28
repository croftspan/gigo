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
    if (toggle) toggle.textContent = theme === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
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
