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


class TestResearch(unittest.TestCase):
    """Documentation lookup uses an injected fetcher, so the suite stays offline."""

    def _fake(self, url):
        if "registry.npmjs.org/next" in url:
            return {"version": "16.4.5",
                    "repository": {"type": "git", "url": "git+https://github.com/vercel/next.js.git"},
                    "homepage": "https://nextjs.org"}
        if "api.github.com/repos/vercel/next.js/releases" in url:
            return [{"tag_name": "v16.4.5", "name": "16.4.5", "published_at": "2026-11-01T00:00:00Z",
                     "body": "### Fixed\n- cache bug", "html_url": "https://github.com/vercel/next.js/releases/tag/v16.4.5"}]
        if "pypi.org/pypi/pydantic" in url:
            return {"info": {"version": "2.14.3",
                             "project_urls": {"Source": "https://github.com/pydantic/pydantic",
                                              "Documentation": "https://docs.pydantic.dev",
                                              "Changelog": "https://docs.pydantic.dev/changelog"}}}
        return None

    def test_finds_repository_and_docs_for_npm(self):
        from kairos_recon import research_package
        info = research_package("npm", "next", fetcher=self._fake)
        self.assertEqual(info["version"], "16.4.5")
        self.assertEqual(info["github"], "https://github.com/vercel/next.js")
        self.assertEqual(info["docs"], "https://nextjs.org")

    def test_finds_changelog_for_pypi(self):
        from kairos_recon import research_package
        info = research_package("pypi", "pydantic", fetcher=self._fake)
        self.assertEqual(info["changelog"], "https://docs.pydantic.dev/changelog")

    def test_pulls_release_notes(self):
        from kairos_recon import research_package
        info = research_package("npm", "next", fetcher=self._fake)
        self.assertEqual(len(info["releases"]), 1)
        self.assertIn("cache bug", info["releases"][0]["notes_excerpt"])

    def test_missing_metadata_is_reported_not_hidden(self):
        from kairos_recon import research_package, format_research
        info = research_package("npm", "no-such-pkg", fetcher=lambda u: None)
        text = format_research(info)
        self.assertIn("not declared", text)
        self.assertIn("none found", text)

    def test_repo_slug_handles_common_url_shapes(self):
        from kairos_recon import _repo_slug
        for url in ("git+https://github.com/vercel/next.js.git",
                    "https://github.com/vercel/next.js",
                    "git://github.com/vercel/next.js.git"):
            self.assertEqual(_repo_slug(url), ("vercel", "next.js"), url)
        self.assertIsNone(_repo_slug(""))
        self.assertIsNone(_repo_slug("https://gitlab.com/a/b"))


class TestMonorepo(unittest.TestCase):
    """The first real project was a monorepo with manifests in backend/ and
    frontend/. Scanning only the root reported 'no manifest', which reads as
    'nothing to check' when there were 128 packages across three subprojects."""

    def _tree(self, tmp):
        root = Path(tmp)
        (root / "backend").mkdir()
        (root / "frontend").mkdir()
        (root / "node_modules" / "junk").mkdir(parents=True)
        (root / "backend" / "package.json").write_text(
            json.dumps({"dependencies": {"express": "^4.0.0"}}), encoding="utf-8")
        (root / "frontend" / "package.json").write_text(
            json.dumps({"dependencies": {"vue": "^3.0.0"}}), encoding="utf-8")
        (root / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
        (root / "node_modules" / "junk" / "package.json").write_text(
            json.dumps({"dependencies": {"should-not-appear": "1.0.0"}}), encoding="utf-8")
        return root

    def test_finds_manifests_in_subprojects(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp)
            items = parse_manifest(root)
            names = {i[1] for i in items}
            self.assertIn("express", names)
            self.assertIn("vue", names)
            self.assertIn("requests", names)

    def test_skips_node_modules(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp)
            names = {i[1] for i in parse_manifest(root)}
            self.assertNotIn("should-not-appear", names)

    def test_source_shows_which_subproject(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(tmp)
            sources = {i[1]: i[3] for i in parse_manifest(root)}
            self.assertEqual(sources["express"], "backend/package.json")
            self.assertEqual(sources["vue"], "frontend/package.json")


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
