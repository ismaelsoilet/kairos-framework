# Implementation Tasks (TDD Breakdown): Engine Expansion

- [ ] 1. Test Setup (Red Phase)
  - **Target:** `tests/test_cli_features.py`
  - **Command:** `python3 -m unittest tests/test_cli_features.py`
  - **Expected Failure:** `AttributeError` or missing commands for mutate, dashboard, rollback.
- [ ] 2. Implementation: Visual Dashboard (`status --dashboard`)
  - **Target:** `scripts/kairos_cli.py` (`cmd_status`)
  - **Code:** Add ANSI stage progress bar and token gauge.
- [ ] 3. Implementation: Rollback (`kairos rollback`)
  - **Target:** `scripts/kairos_cli.py` (`cmd_rollback`)
  - **Code:** Git hard reset and status update.
- [ ] 4. Implementation: Mutation Testing Engine (`kairos mutate`)
  - **Target:** `scripts/kairos_cli.py` (`cmd_mutate`)
  - **Code:** Synthesizes mutations, executes test runner, tracks killed vs survived, safely restores file.
- [ ] 5. Verification Check (Green Phase)
  - **Command:** `python3 -m unittest tests/test_cli_features.py` -> All passing.
- [ ] 6. Adversarial Audit & Archive
  - **Command:** `python3 scripts/kairos_cli.py audit` and `python3 scripts/kairos_cli.py archive`
