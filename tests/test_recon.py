"""Tests for live dependency reconnaissance.

Every test injects a fetcher. None of them touch the network, so the suite stays
deterministic offline — the same standard applied to the rest of this repo.
"""

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_recon import (parse_manifest, check, summarize, _gap,
                          _clean_version)


FAKE_REGISTRY = {
    ("npm", "next"): "16.4.5",
    ("npm", "react"): "19.2.0",
    ("npm", "left-pad"): "1.3.0",
    ("pypi", "pydantic"): "2.14.3",
    ("pypi", "requests"): "2.32.3",
    ("crates", "serde"): "1.0.219",
}


def fake_fetcher(ecosystem, name):
    return FAKE_REGISTRY.get((ecosystem, name))


class TestVersionParsing(unittest.TestCase):
    def test_strips_range_operators(self):
        self.assertEqual(_clean_version("^15.2.0"), "15.2.0")
        self.assertEqual(_clean_version(">=2.0.0"), "2.0.0")
        self.assertEqual(_clean_version("~1.4"), "1.4")

    def test_handles_none(self):
        self.assertIsNone(_clean_version(None))
        self.assertIsNone(_clean_version(""))


class TestGap(unittest.TestCase):
    def test_major_is_detected(self):
        self.assertEqual(_gap("15.0.0", "16.4.5"), "MAJOR")

    def test_minor_and_patch(self):
        self.assertEqual(_gap("2.1.0", "2.14.3"), "MINOR")
        self.assertEqual(_gap("2.14.0", "2.14.3"), "PATCH")

    def test_current(self):
        self.assertEqual(_gap("2.14.3", "2.14.3"), "current")

    def test_unknown_when_unparseable(self):
        self.assertEqual(_gap("latest", "2.0.0"), "unknown")


class TestManifestParsing(unittest.TestCase):
    def test_package_json(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "package.json").write_text(json.dumps({
                "dependencies": {"next": "^15.0.0", "react": "19.0.0"},
                "devDependencies": {"left-pad": "1.2.0"},
            }), encoding="utf-8")
            items = parse_manifest(tmp)
            names = {i[1] for i in items}
            self.assertEqual(names, {"next", "react", "left-pad"})
            self.assertTrue(all(i[0] == "npm" for i in items))

    def test_requirements_txt(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "requirements.txt").write_text(
                "# comment\npydantic>=2.0.0\nrequests==2.31.0\n", encoding="utf-8")
            items = parse_manifest(tmp)
            found = {i[1]: i[2] for i in items}
            self.assertIn("pydantic", found)
            self.assertEqual(found["pydantic"], "2.0.0")
            self.assertNotIn("comment", found)

    def test_no_manifest_returns_empty(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(parse_manifest(tmp), [])


class TestCheckAndSummarize(unittest.TestCase):
    def test_major_gap_is_flagged(self):
        items = [("npm", "next", "15.0.0", "package.json")]
        results = check(items, fetcher=fake_fetcher)
        self.assertEqual(results[0]["gap"], "MAJOR")
        stats = summarize(results)
        self.assertEqual(stats["major"], 1)
        self.assertEqual(stats["major_items"][0]["name"], "next")

    def test_lookup_failure_is_visible_not_silent(self):
        """A registry that does not answer must not look like 'up to date'."""
        items = [("npm", "not-a-real-package-xyz", "1.0.0", "package.json")]
        results = check(items, fetcher=lambda e, n: None)
        self.assertEqual(results[0]["latest"], "lookup failed")
        self.assertEqual(results[0]["gap"], "unknown")
        stats = summarize(results)
        self.assertEqual(stats["unknown"], 1)
        self.assertEqual(stats["current"], 0)

    def test_current_is_not_a_major(self):
        items = [("npm", "left-pad", "1.3.0", "package.json")]
        results = check(items, fetcher=fake_fetcher)
        self.assertEqual(results[0]["gap"], "current")
        self.assertEqual(summarize(results)["major"], 0)


class TestNoHardcodedKnowledge(unittest.TestCase):
    """The previous scout shipped a list of 'known breaking changes'. It already
    said Next 15 while the registry said 16.4.x. This asserts the module has no
    such list, so it cannot rot the same way."""

    def test_module_contains_no_package_version_claims(self):
        src = (REPO_ROOT / "scripts" / "kairos_recon.py").read_text(encoding="utf-8")
        # Any literal like "next 15" or "version 16" in prose would be a claim.
        self.assertNotRegex(src.lower(), r"\bnext\s+1[0-9]\b")
        self.assertNotRegex(src.lower(), r"\breact\s+1[0-9]\b")
        self.assertIn("registry.npmjs.org", src)
        self.assertIn("pypi.org", src)


if __name__ == "__main__":
    unittest.main()
