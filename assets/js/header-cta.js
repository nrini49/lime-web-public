/* Shared "Rosie x IBKR" header CTA click behavior.
 * Added 2026-07-19 per Noal: button text no longer says "coming soon" --
 * it reads "Rosie + IBKR -- Live Data Demo". Clicking it still opens the
 * live-preview link (target="_blank", unchanged), but also shows a brief
 * toast disclosing "coming soon" -- so the caveat lands after the click,
 * not on the button itself. */
(function () {
  var toastEl = null;
  function toast(text) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'cta-toast';
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = text;
    toastEl.classList.add('cta-toast-show');
    clearTimeout(toastEl._hideTimer);
    toastEl._hideTimer = setTimeout(function () {
      toastEl.classList.remove('cta-toast-show');
    }, 2600);
  }

  document.querySelectorAll('.ibkr-demo-cta').forEach(function (cta) {
    if (cta.dataset.ctaToastWired) return;
    cta.dataset.ctaToastWired = '1';
    cta.addEventListener('click', function () {
      toast('Live data demo — coming soon');
    });
  });
})();
