#!/usr/bin/env python3
"""Tests for new.py's page-patching, holding the 2026-09-21 defect closed.

Run: python3 harbor-now/test_publish.py

THE DEFECT
----------
new.py published a Harbor Now edition by writing an archive page, patching the
homepage, and inserting one <li> into harbor-now/index.html's archive list. It
never rewrote that page's featured <div class="report"> block, which had been
hand-written in July. For two months the public page announced
"Latest - July 23, 2026" directly above a list of far newer reports.

A second, quieter defect made the first one invisible: patch_homepage refreshed
the visible date with a regex over <time datetime=...>. The homepage later lost
its <time> stamps, so that substitution matched nothing -- and re.sub reports no
error when it matches nothing. The publisher printed "updated homepage Harbor
as-of" every day while changing no visible date at all.

These tests assert the fixes for both: the featured block is generated from the
edition data, and every structural rewrite now refuses to silently no-op.
"""
import datetime as dt
import importlib.util
import pathlib
import re
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("hn_new", HERE / "new.py")
hn = importlib.util.module_from_spec(spec)
sys.modules["hn_new"] = hn
spec.loader.exec_module(hn)

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print(f"[PASS] {name}")
    else:
        print(f"[FAIL] {name} :: {detail}")
        FAILURES.append(name)


def raises(name, fn, needle=""):
    try:
        fn()
    except SystemExit as e:
        msg = str(e)
        if needle and needle not in msg:
            check(name, False, f"raised, but message lacked {needle!r}: {msg[:160]}")
        else:
            check(name, True)
        return
    except Exception as e:  # noqa: BLE001
        check(name, False, f"raised {type(e).__name__}, expected SystemExit: {e}")
        return
    check(name, False, "did not raise")


DAY = {
    "title": "QQQ leads a broad green close — volatility stays calm",
    "tag": "QQQ gained 2.77% and led all tracked funds.",
    "weather": {
        "sentiment": {"label": "CONSTRUCTIVE", "qualifier": "all four higher"},
        "volatility": "VIX 14.80, down 0.07%",
        "tone": "Broad participation, concentrated leadership",
    },
    "body_muted": "A broad green close is information, not permission.",
}

OLD_INDEX = """<!DOCTYPE html><html><body><main>
    <div class="report">
      <p class="meta">Latest · July 23, 2026</p>
      <h2>Broad risk-off close — QQQ leads lower as VIX spikes.</h2>
      <p class="weather">Market weather: <strong>bearish</strong>.</p>
      <p class="body">All four majors closed red.</p>
      <p class="body">Today is a protect-first day. <a href="archive/2026-07-23.html">Read the full Harbor Now →</a></p>
    </div>
    <h2 class="archive-h">Past Harbor Nows</h2>
    <ul class="list">
      <li><a href="archive/2026-07-23.html"><span class="date">Jul 23, 2026</span></a></li>
    </ul>
</main></body></html>"""

HOMEPAGE = """<!DOCTYPE html><html><body>
<section id="harbor-now" class="harbor-now" data-harbor-asof="2026-07-23">
  <p class="hn-asof">As of close · <time datetime="2026-07-23">Thursday, July 23, 2026</time></p>
  <div class="hn-body"><p><a href="harbor-now/archive/2026-07-23.html">Read the full →</a></p></div>
  <ul class="hn-list">
  </ul>
</section></body></html>"""

# Same homepage, but with the <time> stamp replaced by vague prose -- the exact
# regression that silently disabled the date rewrite on the real site.
HOMEPAGE_NO_TIME = HOMEPAGE.replace(
    '<p class="hn-asof">As of close · <time datetime="2026-07-23">Thursday, July 23, 2026</time></p>',
    '<p class="hn-asof">As of last close</p>',
)

D = dt.date(2026, 9, 21)


def tmpfile(text):
    f = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    return pathlib.Path(f.name)


def featured(text):
    m = re.search(r'<div class="report">.*?</div>', text, re.S)
    return m.group(0) if m else ""


# ── the featured block is generated, and therefore cannot rot ───────────────

blk = hn.featured_block(D, DAY)
check("featured block carries a machine-readable date",
      '<time datetime="2026-09-21">' in blk, blk[:200])
check("featured block shows the human date",
      "September 21, 2026" in blk)
check("featured block uses the edition title",
      "QQQ leads a broad green close" in blk)
check("featured block links its own archive page",
      'href="archive/2026-09-21.html"' in blk)
check("featured block keeps no trace of the old July report",
      "July 23" not in blk and "risk-off" not in blk)
check("featured block has exactly one anchor",
      len(re.findall(r"<a ", blk)) == 1)

# HTML in edition data must not become markup.
hostile = dict(DAY, title='Tape <script>alert(1)</script> & "quotes"')
hblk = hn.featured_block(D, hostile)
check("edition title is HTML-escaped",
      "&lt;script&gt;" in hblk and "<script>" not in hblk)
check("ampersand in title is escaped", "&amp;" in hblk)

# Optional fields absent must not crash or emit empty furniture.
minimal = hn.featured_block(D, {"title": "Bare"})
check("missing weather/tag/body_muted degrades cleanly",
      "Bare" in minimal and 'class="weather"' not in minimal, minimal)


# ── patch_harbor_index replaces the block AND adds the list entry ───────────

p = tmpfile(OLD_INDEX)
hn.patch_harbor_index(p, D, DAY)
out = p.read_text(encoding="utf-8")
p.unlink(missing_ok=True)

check("THE DEFECT: featured block is rewritten to the new edition",
      '<time datetime="2026-09-21">' in featured(out), featured(out)[:200])
check("the stale July featured report is gone from the page",
      "Broad risk-off close" not in out)
check("the new edition is prepended to the archive list",
      'archive/2026-09-21.html' in out.split('<ul class="list">')[1])
check("the previous archive entry is preserved, not replaced",
      out.count('archive/2026-07-23.html') == 1,
      "the old <li> must survive; only the featured block is overwritten")
check("exactly one featured block remains",
      len(re.findall(r'<div class="report">', out)) == 1)

# Publishing twice must not accumulate featured blocks.
p = tmpfile(OLD_INDEX)
hn.patch_harbor_index(p, D, DAY)
hn.patch_harbor_index(p, dt.date(2026, 9, 22), dict(DAY, title="Next day"))
out2 = p.read_text(encoding="utf-8")
p.unlink(missing_ok=True)
check("republishing does not duplicate the featured block",
      len(re.findall(r'<div class="report">', out2)) == 1)
check("republishing leaves the newest edition featured",
      '<time datetime="2026-09-22">' in featured(out2))


# ── a rewrite that matches nothing must stop the publish ───────────────────

raises("sub_once refuses a no-op rewrite",
       lambda: hn.sub_once(r"NOTHING_MATCHES_THIS", "x", "some text", "a test rewrite"),
       "REFUSING TO PUBLISH")

raises("sub_once refuses an unexpected match count",
       lambda: hn.sub_once(r"dup", "x", "dup dup", "a duplicated marker"),
       "expected 1")

no_block = tmpfile('<html><body><ul class="list">\n</ul></body></html>')
raises("publishing stops when the featured block is missing",
       lambda: hn.patch_harbor_index(no_block, D, DAY),
       "featured report block")
no_block.unlink(missing_ok=True)

no_list = tmpfile('<html><body><div class="report"><p class="meta">x</p></div></body></html>')
raises("publishing stops when the archive list is missing",
       lambda: hn.patch_harbor_index(no_list, D, DAY),
       "archive")
no_list.unlink(missing_ok=True)


# ── the homepage regression that hid everything ────────────────────────────

hp = tmpfile(HOMEPAGE)
hn.patch_homepage(hp, D, DAY["title"])
htxt = hp.read_text(encoding="utf-8")
hp.unlink(missing_ok=True)
check("homepage as-of is rewritten",
      'data-harbor-asof="2026-09-21"' in htxt)
check("homepage visible <time> is rewritten to match",
      '<time datetime="2026-09-21">Monday, September 21, 2026</time>' in htxt, htxt[:400])
check("homepage archive link is repointed",
      'harbor-now/archive/2026-09-21.html' in htxt)

hp = tmpfile(HOMEPAGE_NO_TIME)
raises("THE HIDDEN DEFECT: a homepage with no visible date stops the publish",
       lambda: hn.patch_homepage(hp, D, DAY["title"]),
       "visible <time>")
hp.unlink(missing_ok=True)


if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed: {', '.join(FAILURES)}")
    sys.exit(1)
print("\nAll publish checks passed")
