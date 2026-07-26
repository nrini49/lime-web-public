#!/usr/bin/env python3
"""Scenario tests for check_freshness.py.

Runs the checker against synthetic homepage fixtures written to a temp file,
covering the passing case and the failure modes the scheduled publisher must
catch. Run: python3 harbor-now/test_check_freshness.py
"""
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
CHECKER = HERE / "check_freshness.py"

# Newest real archive under harbor-now/archive is 2026-07-17, so a homepage
# as-of of 2026-07-22 is correctly ahead of the archive.
GOOD = """<section id="harbor-now" class="harbor-now" data-harbor-asof="2026-07-22">
  <h2 class="hn-heading"><span class="hn-heading-label">Most recent harbor read</span>
    — <time class="hn-heading-date" datetime="2026-07-22">Wednesday, July 22, 2026</time></h2>
  <p class="hn-asof">As of close · <time datetime="2026-07-22">Wednesday, July 22, 2026</time></p>
</section>"""

# Heading <time> disagrees with the machine date (the original stale-date bug).
MISMATCH = GOOD.replace(
    '<time class="hn-heading-date" datetime="2026-07-22">Wednesday, July 22, 2026</time>',
    '<time class="hn-heading-date" datetime="2026-07-16">Thursday, July 16, 2026</time>',
)

# As-of is older than the newest archived report (homepage lagging behind).
BEHIND = """<section id="harbor-now" class="harbor-now" data-harbor-asof="2026-07-10">
  <h2 class="hn-heading"><time datetime="2026-07-10">Friday, July 10, 2026</time></h2>
  <p class="hn-asof">As of close · <time datetime="2026-07-10">Friday, July 10, 2026</time></p>
</section>"""

# No machine-readable date at all.
NO_MACHINE = """<section id="harbor-now" class="harbor-now">
  <p class="hn-asof">As of close · Wednesday, July 22, 2026</p>
</section>"""

# Static markup still claims "Today's harbor" while the read is stale.
STALE_TODAY = """<section id="harbor-now" class="harbor-now" data-harbor-asof="2026-07-22">
  <h2 class="hn-heading"><span class="hn-heading-label">Today’s harbor</span>
    — <time datetime="2026-07-22">Wednesday, July 22, 2026</time></h2>
  <p class="hn-asof">As of close · <time datetime="2026-07-22">Wednesday, July 22, 2026</time></p>
</section>"""


def run(markup, today):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html><body>" + markup + "</body></html>")
        path = f.name
    try:
        r = subprocess.run(
            [sys.executable, str(CHECKER), "--homepage", path, "--today", today],
            capture_output=True, text=True,
        )
    finally:
        pathlib.Path(path).unlink(missing_ok=True)
    return r.returncode, (r.stdout + r.stderr).strip()


CASES = [
    ("good / fresh", GOOD, "2026-07-23", 0),
    ("good / stale but honest label", GOOD, "2026-08-05", 0),
    ("mismatched visible date", MISMATCH, "2026-07-23", 1),
    ("as-of behind newest archive", BEHIND, "2026-07-23", 1),
    ("missing machine date", NO_MACHINE, "2026-07-23", 1),
    ("stale while claiming Today", STALE_TODAY, "2026-08-05", 1),
]


def main():
    failures = 0
    for name, markup, today, expected in CASES:
        code, out = run(markup, today)
        ok = code == expected
        print(f"[{'PASS' if ok else 'XFAIL'}] {name}: exit={code} (expected {expected}) :: {out}")
        if not ok:
            failures += 1
    if failures:
        print(f"\n{failures} scenario(s) did not behave as expected")
        sys.exit(1)
    print("\nAll freshness scenarios behaved as expected")


if __name__ == "__main__":
    main()
