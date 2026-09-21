#!/usr/bin/env python3
"""Scenario tests for check_freshness.py.

Runs the checker against synthetic fixtures written to temp files, covering the
passing case and every failure mode the scheduled publisher must catch.
Run: python3 harbor-now/test_check_freshness.py

WHY THE FIXTURE DATES ARE COMPUTED, NOT WRITTEN DOWN
----------------------------------------------------
They used to be hardcoded, above a comment reading "Newest real archive under
harbor-now/archive is 2026-07-17, so a homepage as-of of 2026-07-22 is correctly
ahead of the archive." That stopped being true the next time a report was
published. By 2026-09-21 the newest archive was two months past the fixture, so
the checker correctly reported the fixture as lagging and two scenarios failed
every run -- which is exactly how this suite came to be ignored, and part of why
a real two-month staleness bug on harbor-now/index.html went unnoticed.

The checker deliberately reads the REAL archive directory (that is the thing it
exists to compare against), so the fixtures now derive their dates from it. A
fresh fixture stays fresh forever without anyone editing this file.
"""
import datetime as dt
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
CHECKER = HERE / "check_freshness.py"
ARCHIVE = HERE / "archive"


def newest_archive_date():
    dates = []
    for p in ARCHIVE.glob("*.html"):
        m = re.search(r"(\d{4}-\d{2}-\d{2})", p.stem)
        if m:
            try:
                dates.append(dt.datetime.strptime(m.group(1), "%Y-%m-%d").date())
            except ValueError:
                pass
    if not dates:
        print("ERROR: no archive reports found; cannot build fixtures")
        sys.exit(2)
    return max(dates)


NEWEST = newest_archive_date()
ISO = NEWEST.isoformat()
LONG = NEWEST.strftime("%A, %B %-d, %Y")
PRETTY = NEWEST.strftime("%B %-d, %Y")
OLDER = (NEWEST - dt.timedelta(days=30)).isoformat()

# "today" values relative to the newest report, so staleness is deterministic.
SAME_DAY = ISO
MUCH_LATER = (NEWEST + dt.timedelta(days=20)).isoformat()


# ── homepage fixtures ──────────────────────────────────────────────────────

GOOD = f"""<section id="harbor-now" class="harbor-now" data-harbor-asof="{ISO}">
  <h2 class="hn-heading"><span class="hn-heading-label">Most recent harbor read</span>
    — <time class="hn-heading-date" datetime="{ISO}">{LONG}</time></h2>
  <p class="hn-asof">As of close · <time datetime="{ISO}">{LONG}</time></p>
  <div class="hn-body"><p><a href="harbor-now/archive/{ISO}.html">Read the full Harbor Now →</a></p></div>
</section>"""

# Heading <time> disagrees with the machine date (the original stale-date bug).
MISMATCH = GOOD.replace(
    f'<time class="hn-heading-date" datetime="{ISO}">{LONG}</time>',
    f'<time class="hn-heading-date" datetime="{OLDER}">an older day</time>',
)

# As-of is older than the newest archived report (homepage lagging behind).
BEHIND = f"""<section id="harbor-now" class="harbor-now" data-harbor-asof="{OLDER}">
  <h2 class="hn-heading"><time datetime="{OLDER}">an older day</time></h2>
  <p class="hn-asof">As of close · <time datetime="{OLDER}">an older day</time></p>
</section>"""

# No machine-readable date at all.
NO_MACHINE = f"""<section id="harbor-now" class="harbor-now">
  <p class="hn-asof">As of close · {LONG}</p>
</section>"""

# No visible <time> stamp -- the homepage regression that blinded the checker.
# The real homepage looked like this for weeks: a vague "As of last close" with
# no date, which silently disabled both this check and new.py's date rewrite.
NO_VISIBLE_DATE = f"""<section id="harbor-now" class="harbor-now" data-harbor-asof="{ISO}">
  <p class="hn-asof">As of last close</p>
</section>"""

# Static markup still claims "Today's harbor" while the read is stale.
#
# The archive link MUST be present here. Without it this fixture exited 1 on the
# missing-link check and never reached the staleness logic it exists to prove --
# a test passing for the wrong reason, which is worse than a failing one because
# it reports coverage it does not have.
STALE_TODAY = f"""<section id="harbor-now" class="harbor-now" data-harbor-asof="{ISO}">
  <h2 class="hn-heading"><span class="hn-heading-label">Today’s harbor</span>
    — <time datetime="{ISO}">{LONG}</time></h2>
  <p class="hn-asof">As of close · <time datetime="{ISO}">{LONG}</time></p>
  <div class="hn-body"><p><a href="harbor-now/archive/{ISO}.html">Read the full Harbor Now →</a></p></div>
</section>"""


# ── harbor-now/index.html fixtures ─────────────────────────────────────────

def harbor_index(date_iso, *, link_iso=None, with_time=True, duplicate=False):
    """Build a minimal harbor-now/index.html around a featured report block."""
    link_iso = link_iso or date_iso
    pretty = dt.datetime.strptime(date_iso, "%Y-%m-%d").date().strftime("%B %-d, %Y")
    meta = (f'<time datetime="{date_iso}">{pretty}</time>' if with_time else pretty)
    block = (
        '<div class="report">\n'
        f'      <p class="meta">Latest &middot; {meta}</p>\n'
        '      <h2>A headline</h2>\n'
        f'      <p class="body"><a href="archive/{link_iso}.html">Read the full Harbor Now &rarr;</a></p>\n'
        '    </div>'
    )
    body = block + ("\n" + block if duplicate else "")
    return f"<!DOCTYPE html><html><body><main>{body}\n<ul class=\"list\">\n</ul></main></body></html>"


HIDX_GOOD = harbor_index(ISO)
HIDX_STALE = harbor_index(OLDER)                      # the real two-month defect
HIDX_NO_TIME = harbor_index(ISO, with_time=False)     # "Latest" with no verifiable date
HIDX_BAD_LINK = harbor_index(ISO, link_iso=OLDER)     # date and link disagree
HIDX_DUPLICATE = harbor_index(ISO, duplicate=True)    # two blocks, one will rot


def run(markup, today, harbor_index_markup=None):
    """Run the checker. Homepage-only scenarios skip the harbor-index checks."""
    paths = []

    def tmp(text, suffix=".html"):
        with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as f:
            f.write(text)
            paths.append(f.name)
            return f.name

    home = tmp("<!DOCTYPE html><html><body>" + markup + "</body></html>")
    hidx = tmp(harbor_index_markup) if harbor_index_markup is not None else ""
    try:
        r = subprocess.run(
            [sys.executable, str(CHECKER), "--homepage", home,
             "--harbor-index", hidx, "--today", today],
            capture_output=True, text=True,
        )
    finally:
        for p in paths:
            pathlib.Path(p).unlink(missing_ok=True)
    return r.returncode, (r.stdout + r.stderr).strip()


CASES = [
    # name, homepage, today, harbor index (None = skip), expected exit
    ("good / fresh",                     GOOD,            SAME_DAY,    None,           0),
    ("good / stale but honest label",    GOOD,            MUCH_LATER,  None,           0),
    ("mismatched visible date",          MISMATCH,        SAME_DAY,    None,           1),
    ("as-of behind newest archive",      BEHIND,          SAME_DAY,    None,           1),
    ("missing machine date",             NO_MACHINE,      SAME_DAY,    None,           1),
    ("homepage has no visible <time>",   NO_VISIBLE_DATE, SAME_DAY,    None,           1),
    ("stale while claiming Today",       STALE_TODAY,     MUCH_LATER,  None,           1),
    # harbor-now/index.html featured block
    ("harbor index / fresh",             GOOD,            SAME_DAY,    HIDX_GOOD,      0),
    ("harbor index features old report", GOOD,            SAME_DAY,    HIDX_STALE,     1),
    ("harbor index 'Latest' undated",    GOOD,            SAME_DAY,    HIDX_NO_TIME,   1),
    ("harbor index date != its link",    GOOD,            SAME_DAY,    HIDX_BAD_LINK,  1),
    ("harbor index duplicate blocks",    GOOD,            SAME_DAY,    HIDX_DUPLICATE, 1),
]


def main():
    print(f"fixtures anchored to newest archive report: {ISO}\n")
    failures = 0
    for name, markup, today, hidx, expected in CASES:
        code, out = run(markup, today, hidx)
        ok = code == expected
        print(f"[{'PASS' if ok else 'XFAIL'}] {name}: exit={code} (expected {expected}) :: {out}")
        if not ok:
            failures += 1
    if failures:
        print(f"\n{failures} scenario(s) did not behave as expected")
        sys.exit(1)
    print(f"\nAll {len(CASES)} freshness scenarios behaved as expected")


if __name__ == "__main__":
    main()
