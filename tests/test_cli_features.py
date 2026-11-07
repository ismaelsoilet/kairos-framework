import unittest
import sys
import os
import subprocess
from pathlib import Path

# Add scripts directory to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from kairos_cli import cmd_status, cmd_rollback, cmd_mutate

class TestKairosNewFeatures(unittest.TestCase):

    def test_visual_dashboard_flag_exists(self):
        """Test that --dashboard can be called on status."""
        class MockArgs:
            header_only = False
            dashboard = True
        # Should not raise exception
        exit_code = cmd_status(MockArgs())
        self.assertEqual(exit_code, 0)

    def test_mutation_engine_safely_restores_file(self):
        """Test that kairos mutate tests mutants and restores original source perfectly."""
        sample_file = REPO_ROOT / "tests" / "_temp_target.py"
        sample_code = "def calc(a, b):\n    return a + b\n"
        sample_file.write_text(sample_code, encoding="utf-8")

        test_file = REPO_ROOT / "tests" / "_temp_test.py"
        test_code = "from _temp_target import calc\nassert calc(2, 2) == 4\n"
        test_file.write_text(test_code, encoding="utf-8")

        class MockMutateArgs:
            target = str(sample_file)
            test = f"python3 {test_file}"
            max_mutants = 3

        try:
            exit_code = cmd_mutate(MockMutateArgs())
            self.assertEqual(exit_code, 0)
            # Verify file was 100% restored!
            self.assertEqual(sample_file.read_text(encoding="utf-8"), sample_code)
        finally:
            if sample_file.exists():
                sample_file.unlink()
            if test_file.exists():
                test_file.unlink()

if __name__ == "__main__":
    unittest.main()
