#!/usr/bin/env python3
"""
Live dependency reconnaissance.

Why this exists, and why it is not a list of known-breaking packages: a hardcoded
list of "packages with breaking changes" rots exactly like the model's training
data it is supposed to correct. This project shipped one. It named a major
release as current that was already two majors behind the registry.

So this module asks the registries, at the moment you run it, and reports the gap
between what your manifest declares and what actually exists now. No memory.

Sources, all public and unauthenticated:
  npm     https://registry.npmjs.org/<name>/latest
  PyPI    https://pypi.org/pypi/<name>/json
  crates  https://crates.io/api/v1/crates/<name>

A MAJOR gap is the one that breaks code: that is where removed APIs live. MINOR
and PATCH are reported as information, not as risk.
"""

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

TIMEOUT = 8
UA = {"User-Agent": "kairos-scout/1.0 (+https://github.com/ismaelsoilet/kairos-framework)"}


def _fetch_json(url):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            return json.loads(res.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
        return None


def _clean_version(spec):
    """'^15.2.0' / '>=2.0,<3' / '~1.4' -> '15.2.0' (first concrete version)."""
    if not spec:
        return None
    m = re.search(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(spec))
    if not m:
        return None
    return ".".join(g for g in m.groups() if g is not None)


def _semver(v):
    if not v:
        return None
    m = re.match(r"(\d+)\.(\d+)\.(\d+)", v)
    if m:
        return tuple(int(x) for x in m.groups())
    m = re.match(r"(\d+)\.(\d+)", v)
    if m:
        return (int(m.group(1)), int(m.group(2)), 0)
    m = re.match(r"(\d+)", v)
    return (int(m.group(1)), 0, 0) if m else None


def _gap(declared, latest):
    d, l = _semver(declared), _semver(latest)
    if not d or not l:
        return "unknown"
    if l[0] > d[0]:
        return "MAJOR"
    if l[1] > d[1]:
        return "MINOR"
    if l[2] > d[2]:
        return "PATCH"
    return "current"


def parse_manifest(root):
    """Return [(ecosystem, name, declared_version, source_file)]."""
    out = []
    root = Path(root)

    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                for name, ver in (data.get(section) or {}).items():
                    out.append(("npm", name, _clean_version(ver), "package.json"))
        except (ValueError, OSError):
            pass

    for fname in ("requirements.txt", "requirements-dev.txt"):
        req = root / fname
        if req.is_file():
            for line in req.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                m = re.match(r"^([A-Za-z0-9_.\-]+)\s*(?:[=<>!~]=?\s*([^;#\s]+))?", line)
                if m:
                    out.append(("pypi", m.group(1), _clean_version(m.group(2)), fname))

    pyproj = root / "pyproject.toml"
    if pyproj.is_file():
        text = pyproj.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'["\']([A-Za-z0-9_.\-]+)\s*(?:[=<>!~]=?\s*([^"\']+))?["\']', text):
            name = m.group(1)
            if name.lower() in ("python", "readme", "license"):
                continue
            out.append(("pypi", name, _clean_version(m.group(2)), "pyproject.toml"))

    cargo = root / "Cargo.toml"
    if cargo.is_file():
        text = cargo.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'^([A-Za-z0-9_\-]+)\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE):
            if m.group(1) in ("name", "version", "edition", "license", "edition"):
                continue
            out.append(("crates", m.group(1), _clean_version(m.group(2)), "Cargo.toml"))

    # De-duplicate, keeping the first declaration seen.
    seen, unique = set(), []
    for item in out:
        key = (item[0], item[1])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _repo_slug(url):
    """'git+https://github.com/vercel/next.js.git' -> ('vercel', 'next.js')."""
    if not url:
        return None
    m = re.search(r"github\.com[:/]+([^/]+)/([^/#?]+?)(?:\.git)?(?:[/#?].*)?$", str(url))
    return (m.group(1), m.group(2)) if m else None


def research_package(ecosystem, name, fetcher=_fetch_json):
    """Pull the documentation and recent release notes that actually exist.

    What this can do: find the registry entry, the repository, the documented
    docs and changelog URLs, and the last few GitHub releases with their notes.

    What this cannot do: judge whether a library is a good architectural fit,
    notice that an approach has fallen out of favour, or discover a better
    alternative nobody told it about. Those need reading and judgement. A script
    that claimed to detect trends would be guessing with extra steps.
    """
    out = {"ecosystem": ecosystem, "name": name}

    if ecosystem == "npm":
        meta = fetcher(f"https://registry.npmjs.org/{name}/latest") or {}
        out["version"] = meta.get("version")
        repo = meta.get("repository") or {}
        out["repository"] = repo.get("url") if isinstance(repo, dict) else repo
        out["homepage"] = meta.get("homepage")
        urls = meta.get("bugs") or {}
        out["docs"] = meta.get("homepage")
        out["changelog"] = None
    elif ecosystem == "pypi":
        meta = fetcher(f"https://pypi.org/pypi/{name}/json") or {}
        info = meta.get("info") or {}
        out["version"] = info.get("version")
        urls = info.get("project_urls") or {}
        out["repository"] = urls.get("Source") or urls.get("Homepage") or urls.get("Repository")
        out["docs"] = urls.get("Documentation") or urls.get("Docs") or info.get("home_page")
        out["changelog"] = urls.get("Changelog") or urls.get("Changes") or urls.get("Release Notes")
        out["homepage"] = urls.get("Homepage")
    elif ecosystem == "crates":
        meta = fetcher(f"https://crates.io/api/v1/crates/{name}") or {}
        crate = meta.get("crate") or {}
        out["version"] = crate.get("max_stable_version") or crate.get("max_version")
        out["repository"] = crate.get("repository")
        out["docs"] = crate.get("documentation")
        out["homepage"] = crate.get("homepage")
        out["changelog"] = None
    else:
        return None

    slug = _repo_slug(out.get("repository"))
    if slug:
        out["github"] = f"https://github.com/{slug[0]}/{slug[1]}"
        releases = fetcher(f"https://api.github.com/repos/{slug[0]}/{slug[1]}/releases?per_page=3")
        if isinstance(releases, list):
            out["releases"] = [{
                "tag": r.get("tag_name"),
                "name": (r.get("name") or "")[:80],
                "published": (r.get("published_at") or "")[:10],
                "notes_excerpt": (r.get("body") or "")[:400].strip(),
                "url": r.get("html_url"),
            } for r in releases]
    return out


def format_research(info):
    """Plain-text report. Says what it could not find instead of omitting it."""
    if not info:
        return "unknown ecosystem"
    lines = [
        f"{info['name']}  ({info['ecosystem']})",
        f"  version:    {info.get('version') or 'unknown'}",
        f"  repository: {info.get('repository') or 'not declared'}",
        f"  docs:       {info.get('docs') or 'not declared'}",
        f"  changelog:  {info.get('changelog') or 'not declared'}",
    ]
    for r in info.get("releases") or []:
        lines.append(f"  release {r['tag']} ({r['published']})")
        if r["notes_excerpt"]:
            for line in r["notes_excerpt"].splitlines()[:6]:
                lines.append(f"    {line[:100]}")
        if r["url"]:
            lines.append(f"    {r['url']}")
    if not info.get("releases"):
        lines.append("  releases:   none found (no GitHub repo, or no release objects)")
    return "\n".join(lines)


def latest_version(ecosystem, name):
    if ecosystem == "npm":
        data = _fetch_json(f"https://registry.npmjs.org/{name}/latest")
        return (data or {}).get("version")
    if ecosystem == "pypi":
        data = _fetch_json(f"https://pypi.org/pypi/{name}/json")
        return ((data or {}).get("info") or {}).get("version")
    if ecosystem == "crates":
        data = _fetch_json(f"https://crates.io/api/v1/crates/{name}")
        versions = ((data or {}).get("crate") or {}).get("max_stable_version")
        return versions or ((data or {}).get("crate") or {}).get("max_version")
    return None


def check(declared_items, fetcher=latest_version):
    """Compare declared versions against the live registries.

    `fetcher` is injectable so the tests never touch the network.
    """
    results = []
    for ecosystem, name, declared, source in declared_items:
        latest = fetcher(ecosystem, name)
        results.append({
            "ecosystem": ecosystem,
            "name": name,
            "declared": declared or "unpinned",
            "latest": latest or "lookup failed",
            "gap": _gap(declared, latest) if (declared and latest) else "unknown",
            "source": source,
        })
    return results


def summarize(results):
    majors = [r for r in results if r["gap"] == "MAJOR"]
    unknown = [r for r in results if r["gap"] in ("unknown", "lookup failed")]
    return {
        "total": len(results),
        "major": len(majors),
        "minor": sum(1 for r in results if r["gap"] == "MINOR"),
        "patch": sum(1 for r in results if r["gap"] == "PATCH"),
        "current": sum(1 for r in results if r["gap"] == "current"),
        "unknown": len(unknown),
        "major_items": majors,
    }


def main():  # pragma: no cover - thin CLI wrapper
    import argparse
    ap = argparse.ArgumentParser(description="Live dependency reconnaissance")
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--offline", action="store_true", help="parse only, no network")
    args = ap.parse_args()

    items = parse_manifest(args.root)
    if not items:
        print("No manifest found (package.json, requirements*.txt, pyproject.toml, Cargo.toml).")
        return 1

    results = check(items, fetcher=(lambda e, n: None) if args.offline else latest_version)
    stats = summarize(results)

    if args.json:
        print(json.dumps({"summary": stats, "dependencies": results}, indent=2))
        return 0

    print("=" * 72)
    print(f"LIVE DEPENDENCY CHECK — {stats['total']} packages")
    print("=" * 72)
    if args.offline:
        print("  (offline: versions were not looked up)")
    for r in results:
        if r["gap"] in ("MAJOR", "lookup failed", "unknown"):
            print(f"  {r['gap']:<8} {r['name']:<28} declared {r['declared']:<12} "
                  f"latest {r['latest']}")
    print("-" * 72)
    print(f"  MAJOR gaps: {stats['major']}   MINOR: {stats['minor']}   "
          f"PATCH: {stats['patch']}   current: {stats['current']}   "
          f"unknown: {stats['unknown']}")
    if stats["major"]:
        print()
        print("  A MAJOR gap is where removed and renamed APIs live. Before writing")
        print("  code against these, read the migration guide for the jump. Your")
        print("  training memory almost certainly predates it.")
    print("=" * 72)
    return 0 if stats["major"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
