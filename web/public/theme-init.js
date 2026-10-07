// Applies a saved light or dark choice before the page paints, so there is no flash of the wrong
// theme. It is a small external file (not inline) so the Content Security Policy can stay strict.
(function () {
  try {
    var t = localStorage.getItem('theme');
    if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t;
  } catch (e) {}
})();
