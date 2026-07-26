/* Drop-cap + small-caps-rest heading/label style, site-wide.
   Per Noal, 2026-07-20 ~6:23pm: he pointed at the "AI-Assisted Investing
   Strategies and Tactics" subtitle link (hand-marked-up with individual
   <span class="drop-cap"> letters) and asked for that same look --
   first letter of each word sized up -- on all headings and subheadings.

   Extended per Noal, 2026-07-20 ~8:49pm: every word's FIRST letter gets
   the enlarged .drop-cap treatment (unchanged from the original ask), and
   now the REST of each word also gets wrapped in .small-caps-rest, which
   renders it capitalized but one size step down -- matching the pattern
   he hand-built on the "Leave a Memory, a Thought or a Feeling, Before
   You Leave..." heading and asked to have applied everywhere else on the
   page (that one heading itself is the reference example and is left
   alone -- it's already fully hand-marked-up, so this script's own
   "already has content" checks skip it naturally, no special-casing
   needed).

   Rather than hand-wrapping every heading's letters in markup (what a
   few elements on the page still do by hand, for full control over
   punctuation/hyphenation edge cases), this walks the DOM once on load
   and wraps them automatically, so any current or future heading/label
   gets the treatment for free.

   Deliberately conservative about what it touches:
   - Only elements matching TARGET_SELECTOR below.
   - Per-text-node, not per-element: only transforms this element's own
     direct text-node children, leaving any existing child ELEMENTS
     (icons, links, already-hand-marked-up spans, nested hint text like
     the signup teaser's "(hover to open)") completely untouched. This
     means it can safely run on mixed-content elements too, not just
     fully-plain ones -- e.g. it will drop-cap the plain-text lead-in of
     a heading that also contains a nested interactive tooltip, without
     disturbing that tooltip.
   - Splits on whitespace only, not hyphens -- so a compound like
     "AI-Assisted" gets one enlarged letter (the "A"), not two.
   - Tokens that don't start with a letter (bare numbers, punctuation)
     are left as plain text -- no drop-cap on a digit or symbol.
   - Marks processed elements with data-drop-cap="done" so re-running
     (e.g. after other scripts touch the DOM) never double-wraps.
   - .chapter-num intentionally excluded from TARGET_SELECTOR: its text
     is things like "Part I" / "Chapter III" -- literal repeated Roman
     numerals where a per-word first-letter-enlarge pass would enlarge
     only the leading "I" of "III" and leave the other two small, a
     mismatched-size bug already diagnosed and fixed by hand elsewhere
     on this page. Left as its own plain uppercase-via-CSS treatment.
   - h1 excluded on purpose: the page's only h1 is an 11-word full-sentence
     tagline ("Lime Harbor is where inner posture merges with disciplined
     action."), not a short heading -- drop-capping every word in a run-on
     sentence looked busy rather than elegant. */
(function () {
  var TARGET_SELECTOR = 'h2, h3, .part-title, .part-tagline, .form-card-teaser, .interp-note-kicker';

  // Bare Roman numerals (I, II, III, IV, IX, X, ...), with or without a
  // trailing comma/period, are left completely untouched -- splitting a
  // repeated-letter token like "III" into an enlarged first "I" plus a
  // smaller "II" reproduces a mismatched-size bug already diagnosed and
  // hand-fixed elsewhere on this page (same root cause as the earlier
  // "AI" drop-cap fix: a token made of repeated identical letters only
  // gets its very first occurrence enlarged, leaving the rest visibly
  // smaller even though every letter is nominally capital).
  var ROMAN_NUMERAL = /^[IVXLCDM]+[.,;:]?$/i;

  function wrapWord(tok, frag) {
    var punctStripped = tok.replace(/[.,;:]+$/, '');
    if (punctStripped.length > 1 && ROMAN_NUMERAL.test(tok)) {
      frag.appendChild(document.createTextNode(tok));
      return;
    }
    var m = tok.match(/^([A-Za-z])([\s\S]*)$/);
    if (!m) { frag.appendChild(document.createTextNode(tok)); return; }
    var first = document.createElement('span');
    first.className = 'drop-cap';
    first.textContent = m[1];
    frag.appendChild(first);
    if (m[2]) {
      var rest = document.createElement('span');
      rest.className = 'small-caps-rest';
      rest.textContent = m[2];
      frag.appendChild(rest);
    }
  }

  function dropCapifyElement(el) {
    if (el.getAttribute('data-drop-cap') === 'done') return;
    var childNodes = Array.prototype.slice.call(el.childNodes);
    var hasOwnText = childNodes.some(function (n) { return n.nodeType === 3 && n.textContent.trim(); });
    if (!hasOwnText) return; // nothing but existing child elements -- leave alone

    childNodes.forEach(function (node) {
      if (node.nodeType !== 3) return; // only replace text nodes, never touch existing elements
      var text = node.textContent;
      if (!text.trim()) return;

      var tokens = text.split(/(\s+)/); // keep whitespace runs as their own tokens
      var frag = document.createDocumentFragment();
      tokens.forEach(function (tok) {
        if (tok === '') return;
        if (/^\s+$/.test(tok)) { frag.appendChild(document.createTextNode(tok)); return; }
        wrapWord(tok, frag);
      });
      el.replaceChild(frag, node);
    });

    el.setAttribute('data-drop-cap', 'done');
  }

  function run() {
    document.querySelectorAll(TARGET_SELECTOR).forEach(dropCapifyElement);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
