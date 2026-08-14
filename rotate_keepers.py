#!/usr/bin/env python3
"""
Daily Keeper portrait rotation for lime-web/index.html.

Runs once a day as a step inside the existing Harbor Now cron (fba558d0).
Rotates WHICH of the 9 real Keepers appears at each of the 9 Wicket Gate
door cards, and which one anchors the Part A hero portrait -- but each
Keeper's portrait file, name, and card-fire sentence always travel together
as a single fixed unit, so there is never a name/sentence/portrait mismatch.
Door themes (num, href, h3 title, p description) never change -- only the
Keeper "storyteller" assigned to that door for the day.

Deterministic per calendar date (seeded by YYYY-MM-DD), so re-running this
script multiple times on the same day produces the same result -- only
changes once a day, unlike the old client-side JS rotation which cycled
every 5-30 seconds through all 46 Keepers (37 of which have no portrait
file, causing blank portraits). Restricted to the 9 Keepers who currently
have real portrait files on disk.

Usage: python3 rotate_keepers.py [--date YYYY-MM-DD]
  (--date is optional, defaults to today; used for testing/backfill only)
"""
import argparse
import random
import re
import sys
from pathlib import Path

INDEX_HTML = Path(__file__).parent / "index.html"

# The 9 real Keepers. Each unit is fixed together: file + name + the
# fire-sentence written specifically for that person. These never get
# split apart or recombined with a different Keeper's sentence.
KEEPER_UNITS = [
    {
        "file": "01_peter.webp",
        "name": "Peter",
        "fire": "Peter's fire was forged in failure. He carried the flame back from his worst moment and held the gate anyway — that is the spirit that opens this door.",
    },
    {
        "file": "02_solomon.webp",
        "name": "Solomon",
        "fire": "Solomon's fire was the audacity to ask for wisdom when he could have asked for anything else. That single ask is the spirit behind every honest explanation of what this system is built to do.",
    },
    {
        "file": "03_mary_magdalene.webp",
        "name": "Mary Magdalene",
        "fire": "Mary Magdalene carried the signal before anyone else believed there was one to carry. Her fire is the courage to pass the word before the world confirms it.",
    },
    {
        "file": "04_mary_of_bethany.webp",
        "name": "Mary of Bethany",
        "fire": "Mary of Bethany's fire was stillness chosen on purpose — sitting at the feet when the room demanded she get up. That deliberate quiet is the whole inner rail.",
    },
    {
        "file": "05_daniel.webp",
        "name": "Daniel",
        "fire": "Daniel's fire was the refusal to adjust the report to please the room. He read what was there and said it plainly. That is the only acceptable posture for a situation report.",
    },
    {
        "file": "06_esther.webp",
        "name": "Esther",
        "fire": "Esther's fire was timing — she held the position until the room was ready, then moved without hesitation. The offer stands the same way: not a pitch, a door opened at the right moment.",
    },
    {
        "file": "07_ruth.webp",
        "name": "Ruth",
        "fire": "Ruth's fire was loyal presence — she stayed on the field when leaving was the easier, more reasonable choice. This watch runs the same way: it does not leave the position.",
    },
    {
        "file": "08_david.webp",
        "name": "David",
        "fire": "David's fire burned in caves, in grief, in battle, and in celebration equally. He wrote songs in the dark before the light arrived. Laughter held in that same frequency is not a distraction — it is a form of praise.",
    },
    {
        "file": "09_adam.webp",
        "name": "Adam",
        "fire": "Adam's fire was carrying a promise forward without any proof it would hold. That is the same posture this teaching layer asks of you — learn to trust the pattern before you can see how it resolves.",
    },
]

# Fixed door themes, in on-page order (num, href, h3, p). Never rotated.
DOOR_THEMES = [
    {"num": "01", "href": "https://limesignalworks.pplx.app", "target_attrs": ' target="_blank" rel="noopener"', "h3": "System Access", "p": "Authorized? Unlock your personalized Rosie sandbox and Fire Spirit materials here."},
    {"num": "02", "href": "seed/index.html", "target_attrs": "", "h3": "What LIME Is", "p": "LIME in plain language — the problem it solves and how it works."},
    {"num": "03", "href": "invite/index.html", "target_attrs": "", "h3": "Bring Someone", "p": "Bring someone you care about to the harbor. A personal welcome."},
    {"num": "04", "href": "fire-spirit/index.html", "target_attrs": "", "h3": "Inner Rail", "p": "The Fire Spirit — inner work that turns posture into disciplined action."},
    # href=None renders a non-navigating card: the Situation Report route was
    # withdrawn from public publication, but the door keeps its slot so the
    # nine-box grid geometry is unchanged.
    {"num": "05", "href": None, "target_attrs": "", "h3": "Situation Report", "p": "Today's market weather — regime, fidelity, condition. Read before you act."},
    {"num": "06", "href": "offer/index.html", "target_attrs": "", "h3": "The Offer", "p": "What you get, what it costs, how to join. Loss-prevention-first AI assistance."},
    {"num": "07", "href": "https://spy-pipeline-rosie.pplx.app", "target_attrs": ' target="_blank" rel="noopener"', "h3": "SPY Harbor Watch", "p": "Live SPY tracking since Rosie's first trade — price, alerts, and the 90-day dashboard."},
    {"num": "08", "href": "laugh-lounge/index.html", "target_attrs": "", "h3": "The Laugh Lounge", "p": "A lighter door. Harbor and lighthouse humor, and a library you can browse at your own pace."},
    {"num": "09", "href": "metaphor-gate/index.html", "target_attrs": "", "h3": "The Metaphor Gate", "p": "The teaching layer. Learn to hear what is actually being said — in markets, in leadership, in scripture."},
]


def build_card_html(theme, keeper, slot_index):
    linked = theme["href"] is not None
    open_tag = (
        f'<a class="card" href="{theme["href"]}"{theme["target_attrs"]}>'
        if linked else '<div class="card">'
    )
    arrow = f'<span class="arrow" aria-hidden="true">\u2192</span>' if linked else ''
    return (
        f'{open_tag}'
        f'<div class="num">{theme["num"]}</div>'
        f'{arrow}'
        f'<div class="keeper-portrait" role="img" aria-label="Keeper portrait \u2014 {keeper["name"]}" '
        f'style="background-image:url(\'assets/keepers/{keeper["file"]}\')"></div>'
        f'<div class="keeper-name" data-slot="{slot_index}">{keeper["name"]}</div>'
        f'<h3>{theme["h3"]}</h3>'
        f'<p>{theme["p"]}</p>'
        f'<p class="card-fire">{keeper["fire"]}</p>'
        f'{"</a>" if linked else "</div>"}'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="YYYY-MM-DD, defaults to today (testing/backfill only)")
    args = parser.parse_args()

    if args.date:
        date_str = args.date
    else:
        import datetime
        date_str = datetime.date.today().isoformat()

    rng = random.Random(date_str)  # deterministic per calendar day
    door_order = KEEPER_UNITS[:]
    rng.shuffle(door_order)

    # Independent-but-deterministic pick for the Part A hero (offset seed
    # so it doesn't always match door slot 0's pick).
    hero_rng = random.Random(date_str + "-hero")
    hero_keeper = hero_rng.choice(KEEPER_UNITS)

    text = INDEX_HTML.read_text(encoding="utf-8")

    card_pattern = re.compile(
        r'<a class="card" href="[^"]*"(?: target="_blank" rel="noopener")?>.*?</a>'
        r'|<div class="card">.*?</div>(?=\s*(?:<a class="card"|</div>))'
    )
    cards = card_pattern.findall(text)
    if len(cards) != 9:
        print(f"ERROR: expected 9 door cards, found {len(cards)}. Aborting -- no changes made.", file=sys.stderr)
        sys.exit(1)

    new_cards = [build_card_html(DOOR_THEMES[i], door_order[i], i) for i in range(9)]

    for old, new in zip(cards, new_cards):
        text = text.replace(old, new, 1)

    hero_pattern = re.compile(r"var LOCKED_KEEPER = \{ file: '[^']*', name: '[^']*' \};")
    hero_replacement = f"var LOCKED_KEEPER = {{ file: '{hero_keeper['file']}', name: '{hero_keeper['name']}' }};"
    if not hero_pattern.search(text):
        print("ERROR: LOCKED_KEEPER line not found. Aborting -- no changes made.", file=sys.stderr)
        sys.exit(1)
    text = hero_pattern.sub(hero_replacement, text, count=1)

    INDEX_HTML.write_text(text, encoding="utf-8")

    order_summary = ", ".join(f"{DOOR_THEMES[i]['num']}={door_order[i]['name']}" for i in range(9))
    print(f"Rotated for {date_str}: {order_summary}")
    print(f"Part A hero: {hero_keeper['name']}")


if __name__ == "__main__":
    main()
