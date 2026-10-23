// Applies a saved light or dark choice before the page paints, so there is no flash of the wrong
// theme. It is a small external file (not inline), so a strict Content Security Policy can be
// added later without allowing inline scripts.
(function () {
  try {
    var t = localStorage.getItem('theme');
    if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t;
  } catch {}
})();
