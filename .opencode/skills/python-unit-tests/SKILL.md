---
name: python-unit-tests
description: Run the Python unit tests of the project and use the failures to fix the code. Use it whenever you write, test, check, debug or fix Python code.
compatibility: opencode
---

# Running Python unit tests

## 1. Run the tests
From the root of the project, run with the `bash` tool:
`python .opencode/skills/python-unit-tests/scripts/run_tests.py`
It runs every `test_*.py` file under `tests/`.
To run a single test file, pass it as argument:
`python .opencode/skills/python-unit-tests/scripts/run_tests.py test_units.py`

The last line of the output is always a summary:
`SUMMARY: <run> run, <failed> failed, <errors> errors`.
If `<run>` is 0, there is no test yet: write them first (in a `tests/test_*.py` file, with unittest).
If failed and errors are both 0, stop: the task is done.

## 2. Understand each failure
For every `FAIL` or `ERROR` in the output:
- read the test with the `read` tool, to know the *expected* behaviour;
- read the function under test with the `read` tool;
- explain in one sentence why the code does not match the test.

## 3. Fix the code, not the tests
- Change the **code under test** with the `edit` tool, keeping the rest of the file unchanged.
- **Never weaken or delete an existing test to make it pass.** The tests are the
  specification: making them pass by editing them is cheating.
- Change a test only if it contradicts what the user asked, and say so in your report.

## 4. Re-run until green
Go back to step 1. Stop after 3 unsuccessful fixing rounds and report what is still failing.

## 5. Report
Answer with: the final SUMMARY line, and one line per fixed bug (file, function, what was wrong).
