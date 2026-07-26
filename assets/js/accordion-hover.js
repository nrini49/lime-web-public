/* LIME site-wide accordion behavior. STANDING RULE, confirmed multiple
 * times in-thread by Noal, most recently 2026-07-19:
 *
 * .part-label headings ("Precision Accurate AI Assisted Investing
 * Platform" under Part A, "3 Readers and 1 Door" under Part B, "The LIME
 * Universe Bridge" under Part C) have NO hover behavior whatsoever --
 * they never open or reveal anything. All subheadings (Introduction,
 * Chapter I/II/III, Conclusion) are permanently visible across every
 * part -- no hide/reveal wrapper of any kind.
 *
 * The only hover effect anywhere is: hovering a subheading's own summary
 * bar directly turns it green (CSS below, details.collapsible >
 * summary:hover). Content only ever opens via an explicit click on that
 * summary -- this has never changed. Viewers should never lose track of
 * the homepage: everything opens in place, nothing navigates away.
 *
 * Do NOT add any mouseenter/hover-opens-a-section or hover-reveals-a-
 * section logic anywhere in this file without Noal confirming directly,
 * in-thread, after this note -- this exact behavior has been added and
 * removed multiple times today.
 *
 * NAMED EXCEPTION: #part-i-block ("AI Pilot Trading and Investing..." /
 * "Read Introduction, And Chapters...") DOES hover-reveal, via a
 * dedicated mouseenter/mouseleave block further down index.html (search
 * "openPiViaHover") -- NOT through this file's generic wire(). Rolling
 * over the "Part I" chapter-num tag or the "AI Pilot Trading..." line
 * sets pi.open = true; moving the mouse off the whole block sets it
 * back to false. The "Read Introduction..." heading text (index.html,
 * search "stays invisible until") is pure CSS keyed off that same
 * [open] attribute, so heading and body always move together. Per
 * Noal's direct in-thread request, 2026-07-20 ~9:55pm (heading-visibility
 * refinement) on top of an earlier same-day request that added the
 * open/close mouseenter logic itself. #part-i-block keeps
 * data-stay-open="true", which makes wire() below skip it entirely --
 * the dedicated block owns 100% of its open/close behavior instead.
 * No other Part, and no other collapsible on the site, has any
 * hover-reveal -- they remain exactly as described above.
 *
 * Touch/no-hover devices (phones, tablets) keep plain native <details>
 * click-to-open / click-to-close behavior untouched -- no change there.
 * The dedicated Part I block above is itself gated on the same
 * hover-media-query and no-ops on touch, so touch users just get plain
 * click-to-open there too.
 *
 * SINGLE NAMED EXCEPTION, per Noal's direct in-thread confirmation,
 * 2026-07-19 ~5:51pm: the Part III part-label heading ("The LIME Universe
 * Bridge") is now itself a <details class="part-label bridge-reveal">
 * that gates its bridge-scene + triptych images -- click opens, mouseleave
 * closes, same as everything else (this file needed no changes for it --
 * wire() already applies to every <details> uniformly). No other
 * part-label on the site has been changed; they remain non-interactive.
 */
(function () {
  if (!window.matchMedia || !window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    return; // touch device: leave native <details> click behavior alone
  }

  function wire(details) {
    if (details.dataset.rolloverWired) return;
    details.dataset.rolloverWired = '1';
    // Opt-out, per Noal 2026-07-19 ~6:10pm: elements marked
    // data-stay-open stay open once clicked -- no mouseleave auto-close.
    // Currently only #cw-details ("Leave a Memory") uses this.
    if (details.dataset.stayOpen) return;
    // Opening is click-only (native <details>/<summary>). Closing on
    // mouse-leave is the only automatic behavior here.
    details.addEventListener('mouseleave', function () { details.open = false; });
  }

  function wireAll() {
    document.querySelectorAll('details').forEach(wire);
  }

  wireAll();

  // Pages that build cards/sections dynamically (e.g. rotating Keeper
  // content) may add <details> after load -- catch those too.
  if (window.MutationObserver) {
    new MutationObserver(wireAll).observe(document.body, { childList: true, subtree: true });
  }

  // .part-label headings intentionally have zero JS wiring -- see the file
  // header note above. Nothing left to do here for them.
})();
