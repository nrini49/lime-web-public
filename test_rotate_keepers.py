import contextlib
import io
import random
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import rotate_keepers


class RotateKeepersTests(unittest.TestCase):
    def run_rotation(self, html, date_str):
        with tempfile.TemporaryDirectory() as tmp:
            index_path = Path(tmp) / "index.html"
            index_path.write_text(html, encoding="utf-8")
            stderr = io.StringIO()
            stdout = io.StringIO()
            with (
                mock.patch.object(rotate_keepers, "INDEX_HTML", index_path),
                mock.patch.object(sys, "argv", ["rotate_keepers.py", "--date", date_str]),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                try:
                    rotate_keepers.main()
                    exit_code = 0
                except SystemExit as exc:
                    exit_code = int(exc.code)
            return exit_code, index_path.read_text(encoding="utf-8"), stdout.getvalue(), stderr.getvalue()

    def test_updates_nine_cards_and_part_a_hero_deterministically(self):
        original = Path("index.html").read_text(encoding="utf-8")
        date_str = "2026-08-12"

        exit_code, updated, stdout, stderr = self.run_rotation(original, date_str)

        expected_hero = random.Random(date_str + "-hero").choice(rotate_keepers.KEEPER_UNITS)
        expected_line = (
            f"var LOCKED_KEEPER = {{ file: '{expected_hero['file']}', "
            f"name: '{expected_hero['name']}' }};"
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertIn(expected_line, updated)
        self.assertIn(f"Part A hero: {expected_hero['name']}", stdout)
        self.assertEqual(updated.count('class="keeper-portrait"'), 9)
        self.assertEqual(updated.count('class="keeper-name"'), 9)

    def test_missing_hero_contract_aborts_without_writing_partial_card_changes(self):
        original = Path("index.html").read_text(encoding="utf-8")
        without_marker = original.replace("var LOCKED_KEEPER =", "var REMOVED_KEEPER =", 1)

        exit_code, after, stdout, stderr = self.run_rotation(without_marker, "2026-08-13")

        self.assertEqual(exit_code, 1)
        self.assertEqual(after, without_marker)
        self.assertEqual(stdout, "")
        self.assertIn("LOCKED_KEEPER line not found", stderr)

    def test_client_roster_carries_the_same_fire_as_keeper_units(self):
        """The homepage JS swaps portrait+name every 5s; the fire sentence names
        its Keeper, so it must swap with them. Every JS roster entry must match
        KEEPER_UNITS exactly (file, name, fire), and the rotation must write
        .card-fire. Regression for 2026-09-23 ("David" above Daniel's fire)."""
        import json, re
        html = Path("index.html").read_text(encoding="utf-8")
        start = html.index("var MEN = [")
        block = html[start:html.index("var slots = document.querySelectorAll('.keeper-portrait');")]
        entries = re.findall(r"\{ file: '([^']+)', name: '([^']+)', fire: (\"(?:[^\"\\\\]|\\\\.)*\") \}", block)
        js = {f: (n, json.loads(fire)) for f, n, fire in entries}
        units = {k["file"]: (k["name"], k["fire"]) for k in rotate_keepers.KEEPER_UNITS}
        self.assertEqual(js, units)
        self.assertIn("fireEl.textContent = k.fire", html)

if __name__ == "__main__":
    unittest.main()
