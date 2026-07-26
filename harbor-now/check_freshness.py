#!/usr/bin/env python3
"""Deterministic Harbor freshness check for the scheduled publisher.

Run this before committing a Harbor update and again after a live deploy. It
reads the homepage Harbor section and the archive, then exits non-zero if any
of these hold:

  1. The homepage is missing its machine-readable as-of date
     (``data-harbor-asof`` on ``#harbor-now``).
  2. The machine-readable date and the two visible ``<time>`` stamps (the
     heading date and the "As of close" line) disagree with each other. This
     is what stops a stale visible date from lingering behind the real data.
  3. The homepage as-of date is *older* than the newest completed archive
     report under ``harbor-now/archive/``. The homepage must never lag the
     archive.
  4. An archive page exists for the homepage's own as-of date but the homepage
     "Read the full Harbor Now" link / newest "Past Harbor Nows" entry do not
     point at it.
  5. The read is stale: more than ``--max-business-days`` business days
     (weekend tolerant) have elapsed between the reference "today" and the
     as-of date. In that case the homepage must not be labelling the read
     "Today's harbor" in its static markup.

The reference "today" defaults to the system date; pass ``--today YYYY-MM-DD``
to make the staleness check deterministic (used by the intentional-fail
fixture and by CI). Exit code 0 means fresh and consistent; 1 means a problem
was found; 2 means the check could not run (bad paths / parse failure).
"""
import argparse
import datetime as dt
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
DEFAULT_HOMEPAGE = REPO / "index.html"
ARCHIVE = ROOT / "archive"

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def error(msg):
    print(f"ERROR: {msg}")
    sys.exit(2)


def parse_iso(s):
    return dt.datetime.strptime(s, "%Y-%m-%d").date()


def business_gap(today, asof):
    """Calendar days between asof and today, minus weekend days in between.

    Tolerates weekends (and, loosely, short holiday closures) so a Monday
    reading of Friday's close is not treated as stale.
    """
    cal = (today - asof).days
    if cal <= 0:
        return cal
    weekend = 0
    d = asof + dt.timedelta(days=1)
    while d <= today:
        if d.weekday() >= 5:  # Sat=5, Sun=6
            weekend += 1
        d += dt.timedelta(days=1)
    return cal - weekend


def newest_archive_date():
    if not ARCHIVE.is_dir():
        return None
    dates = []
    for p in ARCHIVE.glob("*.html"):
        m = DATE_RE.search(p.stem)
        if m:
            try:
                dates.append(parse_iso(m.group(1)))
            except ValueError:
                pass
    return max(dates) if dates else None


def extract_section(html):
    """Return the markup of the #harbor-now section (best effort)."""
    m = re.search(r'<section[^>]*id="harbor-now".*?</section>', html, re.S)
    return m.group(0) if m else html


def main():
    ap = argparse.ArgumentParser(description="Check homepage Harbor freshness.")
    ap.add_argument("--homepage", default=str(DEFAULT_HOMEPAGE),
                    help="Path to the homepage index.html (default: repo root index.html)")
    ap.add_argument("--today", default=None,
                    help="Reference date YYYY-MM-DD for the staleness check (default: system date)")
    ap.add_argument("--max-business-days", type=int, default=4,
                    help="Staleness threshold in business days, weekend tolerant (default: 4)")
    args = ap.parse_args()

    home_path = pathlib.Path(args.homepage)
    if not home_path.is_file():
        error(f"homepage not found: {home_path}")
    html = home_path.read_text(encoding="utf-8")

    today = parse_iso(args.today) if args.today else dt.date.today()

    section = extract_section(html)

    # 1. machine-readable as-of
    m = re.search(r'id="harbor-now"[^>]*\bdata-harbor-asof="(\d{4}-\d{2}-\d{2})"', section)
    if not m:
        fail("homepage #harbor-now is missing a machine-readable data-harbor-asof date")
    asof = parse_iso(m.group(1))

    # 2. visible <time> stamps must agree with the machine date
    times = re.findall(r'<time[^>]*\bdatetime="(\d{4}-\d{2}-\d{2})"', section)
    if not times:
        fail("homepage Harbor section has no <time datetime=...> stamp to verify")
    mismatched = sorted({t for t in times if parse_iso(t) != asof})
    if mismatched:
        fail(f"visible <time> date(s) {mismatched} disagree with data-harbor-asof {asof.isoformat()}")

    # 3. homepage must not lag the newest archived report
    newest = newest_archive_date()
    if newest and asof < newest:
        fail(f"homepage as-of {asof.isoformat()} is older than newest archive {newest.isoformat()}")

    # 4. if an archive exists for the homepage date, the links must point at it
    dated_archive = ARCHIVE / f"{asof.isoformat()}.html"
    if dated_archive.is_file():
        rel = f"harbor-now/archive/{asof.isoformat()}.html"
        if rel not in section:
            fail(f"archive {rel} exists but the homepage Harbor links do not reference it")

    # 5. staleness threshold
    gap = business_gap(today, asof)
    stale = gap > args.max_business_days
    claims_today = bool(re.search(r'>\s*Today[’\']s harbor\s*<', section))
    if stale and claims_today:
        fail(f"read is stale ({gap} business days old as of {today.isoformat()}) "
             f"but static markup still labels it “Today’s harbor”")

    label = "stale" if stale else "fresh"
    print(f"OK: homepage Harbor as-of {asof.isoformat()} "
          f"(newest archive {newest.isoformat() if newest else 'none'}, "
          f"{gap} business day(s) vs today {today.isoformat()}, {label})")
    sys.exit(0)


if __name__ == "__main__":
    main()
