#!/usr/bin/env python3
"""Scaffold a new Harbor Now edition — full canonical template.

Carries the complete daily structure from harbor_now_template.md: Market
Weather (tape + SPY/QQQ/DIA/IWM + sentiment + volatility + tone), Cluster
Behavior, Account & Behavior Stance, and the Operations Checklist. The
static Rosie Canon Rules reference is baked into the page template itself
(same every day) and rendered in a second, collapsed-by-default section —
always present, never re-typed.

Usage:
  python3 new.py --date 2026-07-15 --data day.json

day.json shape (all fields required unless noted "optional"):
{
  "title": "The harbor is behaving as designed",
  "tag": "Range-bound chop, thin breadth, no clean leader",
  "weather": {
    "spy": {"price": "753.28", "change": "+0.35%", "high52": "761.40", "read": "Holding above the 20-day, no breakout yet"},
    "qqq": {"price": "715.81", "change": "-0.54%", "read": "Lagging SPY, tech giving back"},
    "dia": {"price": "525.41", "change": "+0.14%", "read": "Steady, value holding the tape up"},
    "iwm": {"price": "295.37", "change": "+0.29%", "read": "Small caps firm but thin volume"},
    "sentiment": {"label": "NEUTRAL", "qualifier": "no conviction either direction"},
    "volatility": "VIX quiet, no fear premium showing",
    "tone": "Waiting, not deciding"
  },
  "cluster": [
    "Leadership lane: none clear, rotation without a leader",
    "Key catalyst today: none scheduled",
    "Secondary catalyst: none",
    "Small cap vs large cap: roughly in line, no divergence",
    "Broad participation: thin, low conviction",
    "Rotation note: money sitting in cash, not rotating",
    "Behavior rule: do not chase a range, wait for the break"
  ],
  "account": [
    "Mission for today: observe only, no new risk",
    "Broker status: IB sandbox active, Schwab pending",
    "Elevated event risk: none flagged"
  ],
  "checklist": [
    "Data flow, broker connections, overnight positions, stop logic: confirmed",
    "Core universe glance: mostly cloudy, no storm flags",
    "Day-specific catalyst note #1: none",
    "Day-specific catalyst note #2: none"
  ],
  "body_muted": "optional closing line, renders muted"
}

The "account" and "checklist" lists only need the day-specific lines — the
fixed canon lines (Rosie is the pilot..., no trade without a reason...,
etc.) are baked into the template and always render alongside them.

Creates harbor-now/archive/<date>.html, then prints the list-entry HTML to
prepend to harbor-now/index.html and the homepage's Past Harbor Nows list.
"""
import argparse, html, json, pathlib, re, sys, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parent
ARCHIVE = ROOT / "archive"
ARCHIVE.mkdir(exist_ok=True)

# Fixed canon lines that always appear alongside the day-specific account/checklist entries.
ACCOUNT_FIXED = [
    "Rosie is the pilot; you are the admiral — Rosie proposes missions, you approve or decline.",
    "No new trade goes on without a written reason, a target range, and a pre-named exit or trim rule.",
    "Cash is safety and optionality at highs — a high-cash stance near ATH is valid, not a failure.",
    "Harbor gets updated after any significant execution today, not only at day end.",
]
CHECKLIST_FIXED = [
    "No stories, no drama, no romance — only states.",
    "Pick the single symbol and single scenario that earns attention at the open.",
    "Everything else is background weather unless it triggers a named alert or rule.",
]

CANON_RULES_HTML = """
<div class="canon-block">
  <h3>Operator Logic</h3>
  <ul>
    <li>Rosie operates in this order: observe, classify, rank, propose, then execute only if allowed.</li>
    <li>Rosie's core verdict states are Enter, Watch, and Avoid.</li>
    <li>Rosie judges each symbol relative to SPY market weather, not in isolation.</li>
    <li>Symbols equal to or slightly stronger than SPY lean favorable for entry; weaker-than-SPY setups are lower quality.</li>
  </ul>
  <h3>Entry Rules</h3>
  <ul>
    <li>Blue progression is light blue to medium blue to dark blue. Weakness progression is yellow to orange to red-orange to red.</li>
    <li>Rosie uses the 1-hour chart range tool workflow with recurring 1% or 2% structure bands where relevant.</li>
    <li>About 0.5% is treated as the conservative seed-entry strike zone near support.</li>
    <li>Rosie prefers entries near a recent low with K line crossing above its signal line, rather than chasing extended price.</li>
    <li>If price leaves the entry band, the verdict downgrades from Enter to Watch or Avoid.</li>
  </ul>
  <h3>Operator Chart Tools</h3>
  <ul>
    <li>Range Tool 1: maroon arrows, anchored at the left-side peak, expanded to 0.5%.</li>
    <li>Range Tool 2: prior high down to the low, color bar set to light blue.</li>
    <li>These tools define the safe strike zone and pullback structure, not a blind trigger.</li>
  </ul>
  <h3>Risk Rules</h3>
  <ul>
    <li>Rosie remains approval-based first, even if fuller automation becomes available later.</li>
    <li>No trade is sent unless the route is intentionally armed by the operator.</li>
    <li>After each buy, Rosie creates or requires protective stop logic immediately, not as an afterthought.</li>
    <li>Stop placement respects structure and the last qualified support area, not an arbitrary fixed percent.</li>
    <li>Rosie helps prevent revenge behavior by locking out low-quality re-entries after failed setups until conditions improve.</li>
    <li>Near-ATH tape means stops must be respected faster — extended distance to support is lower here.</li>
  </ul>
  <h3>Alert &amp; Control Rules</h3>
  <ul>
    <li>Rosie surfaces clear operator-facing controls for relevant trading and analysis modes.</li>
    <li>Alarm or sound cue with on/off control is active for important triggers.</li>
    <li>In focused alert mode, alerts may be narrowed to SPY-only when needed.</li>
  </ul>
  <h3>Performance Rules</h3>
  <ul>
    <li>Rosie maintains a journal and performance review trail so rules can be tuned over time.</li>
    <li>Canon and tactics stay distinct — doctrine governs what Rosie is allowed to do, tactics govern how Rosie interprets setups inside those bounds.</li>
  </ul>
  <h3>Behavior Language</h3>
  <ul>
    <li>Today's win is clean state, clean log, and no trades made from boredom, fear, revenge, or make-it-back thinking.</li>
    <li>P/L is a downstream result, not the mission.</li>
    <li>Harbor by 9:30 and Harbor after any major move is non-negotiable.</li>
    <li>A calm account with defined stops and clear posture is a win, not a problem to fix by adding risk.</li>
    <li>We do not chase. We wait for clean, aligned clusters across our LIME tools before adding risk.</li>
    <li>Near highs is when discipline earns its money — patience is the position.</li>
  </ul>
  <h3>Canon vs. Tactics</h3>
  <ul>
    <li>Harbor Now canon defines sea-state reading and account posture — the top-level doctrine that constrains what Rosie is allowed to do.</li>
    <li>Tactics live underneath and may evolve, as long as they remain inside canon.</li>
    <li>Changes to canon are rare, deliberate edits, not session-by-session adjustments.</li>
  </ul>
</div>
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Harbor Now — {pretty} | Lime Signalworks</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<link href="https://api.fontshare.com/v2/css?f[]=general-sans@300,400,500,600,700&display=swap" rel="stylesheet">
<style>
:root{{--text-xs:clamp(.75rem,.7rem+.25vw,.875rem);--text-sm:clamp(.875rem,.8rem+.35vw,1rem);--text-base:clamp(1rem,.95rem+.25vw,1.125rem);--text-lg:clamp(1.125rem,1rem+.75vw,1.5rem);--text-xl:clamp(1.5rem,1.2rem+1.25vw,2.25rem);--space-2:.5rem;--space-3:.75rem;--space-4:1rem;--space-5:1.25rem;--space-6:1.5rem;--space-8:2rem;--space-12:3rem;--space-16:4rem;--space-20:5rem;--space-24:6rem;--radius-md:.5rem;--radius-xl:1rem;--radius-full:9999px;--transition:180ms cubic-bezier(.16,1,.3,1);--font-display:'Instrument Serif',Georgia,serif;--font-body:'General Sans','Helvetica Neue',sans-serif;}}
:root,[data-theme="dark"]{{--color-bg:#0a131c;--color-surface:#0f1c28;--color-surface-2:#132433;--color-border:#1f3346;--color-divider:#1a2c3c;--color-text:#e6edf2;--color-text-muted:#8fa3b3;--color-text-faint:#5d7286;--color-primary:#9ad14a;--color-primary-hover:#b4e06a;--color-beam:#e8b659;--shadow-md:0 4px 24px rgba(0,0,0,.35);}}
[data-theme="light"]{{--color-bg:#f4f7f5;--color-surface:#fff;--color-surface-2:#eef3ef;--color-border:#dbe4dd;--color-divider:#e4ece6;--color-text:#15241c;--color-text-muted:#56685e;--color-text-faint:#8a9c92;--color-primary:#4f7a1f;--color-primary-hover:#3d6017;--color-beam:#b07d1f;--shadow-md:0 4px 24px rgba(20,40,28,.08);}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html{{-webkit-font-smoothing:antialiased;scroll-behavior:smooth;}}
body{{min-height:100dvh;line-height:1.6;font-family:var(--font-body);font-size:var(--text-base);color:var(--color-text);background:var(--color-bg);}}
a,button{{transition:color var(--transition),background var(--transition),border-color var(--transition);}}
h1,h2,h3{{text-wrap:balance;line-height:1.15;font-family:var(--font-display);font-weight:400;letter-spacing:-.01em;}}
p{{text-wrap:pretty;max-width:70ch;}}
:focus-visible{{outline:2px solid var(--color-primary);outline-offset:3px;border-radius:var(--radius-md);}}
.wrap{{max-width:780px;margin:0 auto;padding:0 var(--space-6);}}
header{{position:sticky;top:0;z-index:10;backdrop-filter:blur(12px);background:color-mix(in oklab,var(--color-bg) 82%,transparent);border-bottom:1px solid var(--color-divider);}}
.hdr{{display:flex;align-items:center;justify-content:space-between;padding:var(--space-4) 0;gap:var(--space-4);}}
.back{{display:inline-flex;align-items:center;gap:var(--space-2);text-decoration:none;color:var(--color-text-muted);font-size:var(--text-sm);font-weight:500;}}
.back:hover{{color:var(--color-primary);}}
.brand{{font-family:var(--font-body);font-weight:600;font-size:var(--text-base);color:var(--color-text);text-decoration:none;}} .brand b{{font-weight:700;color:var(--color-primary);}}
.icon-btn{{display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:var(--radius-full);border:1px solid var(--color-border);color:var(--color-text-muted);background:var(--color-surface);cursor:pointer;}}
main{{padding:clamp(var(--space-16),8vw,var(--space-24)) 0 var(--space-24);}}
.kicker{{font-size:var(--text-xs);letter-spacing:.22em;text-transform:uppercase;color:var(--color-primary);font-weight:600;margin-bottom:var(--space-5);}}
.report{{background:var(--color-surface);border:1px solid var(--color-border);border-radius:var(--radius-xl);padding:clamp(var(--space-6),4vw,var(--space-8));box-shadow:var(--shadow-md);position:relative;overflow:hidden;}}
.report::before{{content:"";position:absolute;inset:0 auto 0 0;width:3px;background:linear-gradient(in oklab,var(--color-primary),var(--color-beam));}}
.report h1{{font-size:var(--text-xl);margin-bottom:var(--space-3);}}
.tag{{color:var(--color-text-muted);font-style:italic;margin-bottom:var(--space-6);}}
p.body{{color:var(--color-text);margin-bottom:var(--space-5);}} p.body.muted{{color:var(--color-text-muted);margin-bottom:0;}}
details.section{{border-top:1px solid var(--color-divider);padding:var(--space-5) 0;}}
details.section:first-of-type{{border-top:1px solid var(--color-divider);margin-top:var(--space-2);}}
details.section summary{{cursor:pointer;list-style:none;display:flex;align-items:center;gap:var(--space-3);font-family:var(--font-display);font-size:var(--text-lg);color:var(--color-text);-webkit-tap-highlight-color:transparent;}}
details.section summary::-webkit-details-marker{{display:none;}}
details.section summary::before{{content:"+";color:var(--color-primary);font-family:var(--font-body);font-weight:600;font-size:var(--text-base);width:1.2em;flex-shrink:0;}}
details.section[open] summary::before{{content:"–";}}
details.section .inner{{padding-top:var(--space-4);}}
.sym-row{{display:grid;grid-template-columns:64px 1fr auto;gap:var(--space-3);align-items:baseline;padding:var(--space-2) 0;border-bottom:1px solid var(--color-divider);}}
.sym-row:last-child{{border-bottom:none;}}
.sym-row .sym{{font-weight:700;color:var(--color-primary);}}
.sym-row .read{{color:var(--color-text-muted);font-size:var(--text-sm);}}
.sym-row .nums{{text-align:right;font-size:var(--text-sm);}}
.sym-row .nums .chg-up{{color:var(--color-primary);}} .sym-row .nums .chg-down{{color:#e05d5d;}}
@media (max-width:480px){{
  .sym-row{{grid-template-columns:1fr;gap:var(--space-1,.25rem);}}
  .sym-row .nums{{text-align:left;}}
}}
.field-list{{list-style:none;display:flex;flex-direction:column;gap:var(--space-3);}}
.field-list li{{position:relative;padding-left:var(--space-5);color:var(--color-text);}}
.field-list li::before{{content:"□";position:absolute;left:0;color:var(--color-text-faint);}}
.wx-line{{display:flex;flex-wrap:wrap;gap:var(--space-2);align-items:baseline;margin-top:var(--space-4);color:var(--color-text);}}
.wx-line b{{color:var(--color-primary);font-weight:600;}}
.canon-block h3{{font-size:var(--text-base);font-family:var(--font-body);font-weight:700;color:var(--color-primary);margin:var(--space-5) 0 var(--space-2);}}
.canon-block h3:first-child{{margin-top:0;}}
.canon-block ul{{list-style:none;display:flex;flex-direction:column;gap:var(--space-2);}}
.canon-block li{{position:relative;padding-left:var(--space-5);color:var(--color-text-muted);font-size:var(--text-sm);}}
.canon-block li::before{{content:"□";position:absolute;left:0;color:var(--color-text-faint);}}
footer{{border-top:1px solid var(--color-divider);padding:var(--space-12) 0;background:var(--color-surface);text-align:center;font-size:var(--text-sm);color:var(--color-text-muted);}}
footer a{{color:var(--color-text-muted);text-decoration:none;border-bottom:1px solid var(--color-border);}} footer a:hover{{color:var(--color-primary);border-color:var(--color-primary);}}
</style>
</head>
<body>
<header><div class="wrap hdr">
  <a class="back" href="../index.html">&larr; <span>Back to Harbor Now</span></a>
  <a class="brand" href="../../index.html">Lime <b>Signalworks</b></a>
  <button class="icon-btn" data-translate aria-label="Translate this page"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></button>
  <button class="icon-btn" data-theme-toggle aria-label="Switch theme"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg></button>
</div></header>
<script>(function(){{var tr=document.querySelector("[data-translate]");if(tr){{tr.addEventListener("click",function(){{window.open('https://translate.google.com/translate?sl=auto&tl=auto&u='+encodeURIComponent(window.location.href),"_blank","noopener");}});}}}})();</script>
<main><div class="wrap">
  <p class="kicker">Harbor Now &middot; {pretty}</p>
  <div class="report">
    <h1>{title}</h1>
    <p class="tag">{tag}</p>

    <details class="section" open>
      <summary>Market Weather</summary>
      <div class="inner">
        <div class="sym-rows">{sym_rows}</div>
        <p class="wx-line"><b>Market sentiment:</b> {sentiment_label} &mdash; {sentiment_qualifier}</p>
        <p class="wx-line"><b>Volatility:</b> {volatility}</p>
        <p class="wx-line"><b>Today's language:</b> {tone}</p>
      </div>
    </details>

    <details class="section" open>
      <summary>Cluster Behavior</summary>
      <div class="inner"><ul class="field-list">{cluster_items}</ul></div>
    </details>

    <details class="section" open>
      <summary>Account &amp; Behavior Stance</summary>
      <div class="inner"><ul class="field-list">{account_items}</ul></div>
    </details>

    <details class="section" open>
      <summary>Operations Checklist &mdash; Before the Open</summary>
      <div class="inner"><ul class="field-list">{checklist_items}</ul></div>
    </details>

    {body_muted_html}

    <details class="section">
      <summary>Rosie Canon Rules (reference — unchanged day to day)</summary>
      <div class="inner">{canon_rules}</div>
    </details>
  </div>
</div></main>
<footer><div class="wrap"><a href="../index.html">&larr; All Harbor Nows</a> &nbsp;&middot;&nbsp; <a href="../../index.html">Return to the harbor</a></div></footer>
<script>
(function(){{var t=document.querySelector('[data-theme-toggle]'),r=document.documentElement;var d=matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light';r.setAttribute('data-theme',d);function ic(k){{return k?'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>':'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';}}if(t){{t.innerHTML=ic(d==='dark');t.addEventListener('click',function(){{d=d==='dark'?'light':'dark';r.setAttribute('data-theme',d);t.innerHTML=ic(d==='dark');}});}}}})();
</script>
</body>
</html>
"""


def parse_date(s: str) -> dt.date:
    return dt.datetime.strptime(s, "%Y-%m-%d").date()


def pretty(d: dt.date) -> str:
    return d.strftime("%B %-d, %Y")


def short(d: dt.date) -> str:
    return d.strftime("%b %-d, %Y")


def long_date(d: dt.date) -> str:
    """Weekday + month + day + year, matching the homepage <time> text."""
    return d.strftime("%A, %B %-d, %Y")


def li(items):
    return "\n        ".join(f"<li>{html.escape(x)}</li>" for x in items)


def sym_row(sym, data, extra_prefix=""):
    price = html.escape(str(data.get("price", "—")))
    change = str(data.get("change", ""))
    chg_cls = "chg-up" if change.strip().startswith("+") else ("chg-down" if change.strip().startswith("-") else "")
    read = html.escape(str(data.get("read", "")))
    high52 = data.get("high52")
    nums = f'${price} <span class="{chg_cls}">{html.escape(change)}</span>'
    if high52:
        nums += f' <span style="color:var(--color-text-faint)">&middot; 52w hi ${html.escape(str(high52))}</span>'
    return (
        f'<div class="sym-row"><span class="sym">{html.escape(sym)}</span>'
        f'<span class="read">{read}</span><span class="nums">{nums}</span></div>'
    )


def patch_homepage(home_path: pathlib.Path, d: dt.date, title: str) -> str:
    """Update the homepage Harbor section's machine-readable date and latest
    markers so future editions never leave a stale "today" claim behind.

    Updates, scoped to the #harbor-now section:
      * data-harbor-asof  -> the new ISO date
      * every <time datetime=...> stamp (heading + "As of close") -> new date
        and matching visible text
      * the "Read the full Harbor Now" link -> this edition's archive page
      * prepends a new entry to the "Past Harbor Nows" list

    The editorial weather/body prose is intentionally left untouched (it is a
    human paste — see the printed snippet); only dates, links and the latest
    marker are rewritten here.
    """
    iso = d.isoformat()
    html_text = home_path.read_text(encoding="utf-8")

    sec_re = re.compile(r'(<section[^>]*id="harbor-now".*?</section>)', re.S)
    m = sec_re.search(html_text)
    if not m:
        raise SystemExit(f"could not find #harbor-now section in {home_path}")
    section = m.group(1)

    # Machine-readable as-of.
    section = re.sub(r'(data-harbor-asof=")\d{4}-\d{2}-\d{2}(")', rf'\g<1>{iso}\g<2>', section)
    # <time> stamps: datetime attribute + visible label.
    section = re.sub(r'(<time[^>]*\bdatetime=")\d{4}-\d{2}-\d{2}("[^>]*>)[^<]*(</time>)',
                     rf'\g<1>{iso}\g<2>{long_date(d)}\g<3>', section)
    # "Read the full Harbor Now" link -> this edition's archive page.
    section = re.sub(r'(<div class="hn-body"[^>]*>.*?href=")harbor-now/(?:index\.html|archive/\d{4}-\d{2}-\d{2}\.html)(")',
                     rf'\g<1>harbor-now/archive/{iso}.html\g<2>', section, flags=re.S)
    # Prepend the latest entry to the Past Harbor Nows list.
    entry = (f'\n            <li><a href="harbor-now/archive/{iso}.html">'
             f'<span class="date">{short(d)}</span>'
             f'<span class="title">{html.escape(title)}</span>'
             f'<span class="arr">&rarr;</span></a></li>')
    section = re.sub(r'(<ul class="hn-list">)', rf'\g<1>{entry}', section, count=1)

    html_text = html_text[:m.start()] + section + html_text[m.end():]
    home_path.write_text(html_text, encoding="utf-8")
    return iso


def prepend_index_entry(index_path: pathlib.Path, d: dt.date, title: str) -> bool:
    """Prepend the latest edition to harbor-now/index.html's list, if present."""
    if not index_path.is_file():
        return False
    text = index_path.read_text(encoding="utf-8")
    entry = (f'      <li><a href="archive/{d.isoformat()}.html">'
             f'<span class="date">{short(d)}</span>'
             f'<span class="title">{html.escape(title)}</span>'
             f'<span class="arr">&rarr;</span></a></li>\n')
    m = re.search(r'(<ul[^>]*class="(?:[^"]*\b)?(?:list|hn-list)\b[^"]*"[^>]*>[ \t]*\n)', text)
    if not m:
        return False
    text = text[:m.end()] + entry + text[m.end():]
    index_path.write_text(text, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser(description="Scaffold a full Harbor Now edition.")
    ap.add_argument("--date", required=True, help="ISO date, e.g. 2026-07-15")
    ap.add_argument("--data", required=True, help="Path to a JSON file matching the shape documented at the top of this script")
    ap.add_argument("--homepage", default=str(ROOT.parent / "index.html"),
                    help="Homepage to update (default: repo root index.html); pass '' to skip")
    ap.add_argument("--index", default=str(ROOT / "index.html"),
                    help="Harbor Now index to update (default: harbor-now/index.html); pass '' to skip")
    args = ap.parse_args()

    d = parse_date(args.date)
    day = json.loads(pathlib.Path(args.data).read_text(encoding="utf-8"))

    wx = day["weather"]
    sym_rows = "\n      ".join([
        sym_row("SPY", wx["spy"]),
        sym_row("QQQ", wx["qqq"]),
        sym_row("DIA", wx["dia"]),
        sym_row("IWM", wx["iwm"]),
    ])

    account_items = li(day.get("account", []) + ACCOUNT_FIXED)
    checklist_items = li(day.get("checklist", []) + CHECKLIST_FIXED)

    body_muted_html = ""
    if day.get("body_muted"):
        body_muted_html = f'<p class="body muted">{html.escape(day["body_muted"])}</p>'

    page = TEMPLATE.format(
        pretty=pretty(d), short=short(d), date=d.isoformat(),
        title=html.escape(day["title"]),
        tag=html.escape(day["tag"]),
        sym_rows=sym_rows,
        sentiment_label=html.escape(wx["sentiment"]["label"]),
        sentiment_qualifier=html.escape(wx["sentiment"]["qualifier"]),
        volatility=html.escape(wx["volatility"]),
        tone=html.escape(wx["tone"]),
        cluster_items=li(day.get("cluster", [])),
        account_items=account_items,
        checklist_items=checklist_items,
        body_muted_html=body_muted_html,
        canon_rules=CANON_RULES_HTML,
    )
    out = ARCHIVE / f"{d.isoformat()}.html"
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")

    # Machine-readable companion for the checker and future tooling.
    data_out = ARCHIVE / f"{d.isoformat()}.data.json"
    data_out.write_text(json.dumps(day, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {data_out.relative_to(ROOT)}")

    title = day["title"]

    # Update the homepage's machine-readable date + latest markers.
    if args.homepage:
        iso = patch_homepage(pathlib.Path(args.homepage), d, title)
        print(f"updated homepage Harbor as-of -> {iso} ({args.homepage})")

    # Prepend the edition to the Harbor Now index list.
    if args.index:
        if prepend_index_entry(pathlib.Path(args.index), d, title):
            print(f"prepended edition to {args.index}")
        else:
            print(f"note: could not auto-update {args.index}; add the entry manually")

    entry = (
        f'      <li><a href="archive/{d.isoformat()}.html">'
        f'<span class="date">{short(d)}</span>'
        f'<span class="title">{html.escape(title)}</span>'
        f'<span class="arr">&rarr;</span></a></li>'
    )
    print("\n--- editorial paste: refresh the homepage weather/body prose by hand ---")
    print("    (dates, links and the latest marker were updated automatically above)")
    print("\n--- list entry (already applied to homepage + index if paths were writable) ---")
    print(entry)


if __name__ == "__main__":
    main()
