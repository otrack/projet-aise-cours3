"""Run the unittest suite of the current directory and print a one-line summary.

Usage: python run_tests.py [test_file.py]
"""
import sys
import unittest

pattern = sys.argv[1] if len(sys.argv) > 1 else "test*.py"
suite = unittest.TestLoader().discover(".", pattern=pattern)
result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)

# A fixed, easy-to-parse last line: the SKILL.md tells the model to look for it.
print(f"SUMMARY: {result.testsRun} run, {len(result.failures)} failed, "
      f"{len(result.errors)} errors")
sys.exit(0 if result.wasSuccessful() else 1)
