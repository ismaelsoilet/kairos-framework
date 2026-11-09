"""Tests for the brainstorm brief checker.

The checker exists because a spec is a commitment to one design, and a commitment
with no recorded alternatives is just the first idea that survived the chat.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_brainstorm import check_brief, parse_alternatives, MIN_ALTERNATIVES

GOOD = """# Brainstorm: dark mode

## Problem
Users cannot view the app comfortably at night.

## Alternatives considered

1. **CSS variables plus a class on the root**
   - Mechanism: toggle a class, variables resolve per theme
   - Why rejected: does not work with the existing inline styles

2. **Separate stylesheet per theme**
   - Mechanism: swap the `href` of a link tag
   - Why rejected: flash of unstyled content on load

3. **Theme context in React**
   - Mechanism: provider holds the theme, components read it
   - Chosen, because it works with inline styles and has no flash

## Chosen approach
React context. Trade-off: every component must consume it.

## Assumptions
- The app is already React
- Users have localStorage

## Open questions
- How does the server render the initial theme? Answered by reading the SSR entry.

## What would make this wrong
If more than 30% of components are plain HTML outside React, the context cannot
reach them and the approach fails.

## Live versions checked
`kairos scout` reported no MAJOR gaps for react.
"""

TOO_FEW = """# Brainstorm
## Problem
Something.
## Alternatives considered

1. **Only option**
   - Chosen
## Chosen approach
It.
## Assumptions
None.
## Open questions
None.
## What would make this wrong
It does not work.
"""

NO_REASONS = """# Brainstorm
## Problem
Something.
## Alternatives considered

1. **First idea**
   - Mechanism: do it
2. **Second idea**
   - Mechanism: do it differently
3. **Third idea**
   - Mechanism: do it another way
## Chosen approach
The first.
## Assumptions
None.
## Open questions
None.
## What would make this wrong
Anything.
"""

NO_FALSIFICATION = """# Brainstorm
## Problem
Something.
## Alternatives considered

1. **A**
   - Why rejected: too slow
2. **B**
   - Why rejected: too complex
3. **C**
   - Chosen
## Chosen approach
C.
## Assumptions
None.
## Open questions
None.
"""


class TestAlternatives(unittest.TestCase):
    def test_parses_numbered_entries(self):
        alts = parse_alternatives(GOOD)
        self.assertEqual(len(alts), 3)

    def test_marks_chosen(self):
        alts = parse_alternatives(GOOD)
        self.assertTrue(any(a["chosen"] for a in alts))

    def test_entries_without_reason_are_flagged(self):
        alts = parse_alternatives(NO_REASONS)
        self.assertEqual(len(alts), 3)
        self.assertTrue(all(not a["has_reason"] for a in alts),
                        f"reasons were invented: {alts}")

    def test_returns_empty_when_no_section(self):
        self.assertEqual(parse_alternatives("# Nothing\njust prose.\n"), [])


class TestCheckBrief(unittest.TestCase):
    def test_good_brief_passes(self):
        result = check_brief(GOOD)
        self.assertTrue(result["ok"], f"problems: {result['problems']}")
        self.assertGreaterEqual(result["alternatives"], MIN_ALTERNATIVES)

    def test_too_few_alternatives_fails(self):
        result = check_brief(TOO_FEW)
        self.assertFalse(result["ok"])
        self.assertTrue(any("alternative" in p for p in result["problems"]))

    def test_missing_reasons_fails(self):
        result = check_brief(NO_REASONS)
        self.assertFalse(result["ok"])
        self.assertTrue(any("rejection reason" in p for p in result["problems"]))

    def test_missing_falsification_fails(self):
        result = check_brief(NO_FALSIFICATION)
        self.assertFalse(result["ok"])
        self.assertIn("falsification", result["sections_missing"])

    def test_empty_brief_fails_loudly(self):
        result = check_brief("")
        self.assertFalse(result["ok"])
        self.assertEqual(result["alternatives"], 0)


if __name__ == "__main__":
    unittest.main()
