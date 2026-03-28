/* GIGO — Shared JS */

(function () {
  'use strict';

  /* --- Dark/Light Theme Toggle --- */
  var toggle = document.getElementById('theme-toggle');
  var root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem('gigo-theme', theme);
    if (toggle) toggle.textContent = theme === 'dark' ? 'Light' : 'Dark';
  }

  var saved = localStorage.getItem('gigo-theme');
  applyTheme(saved || 'dark');

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
      navMenu.classList.toggle('open');
    });
  }
})();
