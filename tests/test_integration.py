"""Integration test of wikidiff: runs it against the real English Wikipedia (needs network)."""
import io
import unittest
from contextlib import redirect_stdout

from wikidiff import api_get, main

TITLE = "Minimum bactericidal concentration"
FIRST_REVID = 124651778  # the creation of the page, in 2007
# In May 2016, an administrator hid the text of four revisions (a copyright violation):
# the API still lists them, but without their content.
HIDDEN_REVIDS = [721990679, 721990787, 721993366, 722017526]
BEFORE_HIDDEN, AFTER_HIDDEN = 698274901, 722665403  # the visible revisions around them


class TestIntegration(unittest.TestCase):

    def test_whole_history(self) -> None:
        """The output goes from the creation of the page to its latest revision.

        A revision whose text is hidden gets a header marked '(content hidden)' and no
        diff; the next visible revision is diffed against the last visible one.
        """
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["minimum bactericidal concentration"])
        self.assertEqual(code, 0)
        output = out.getvalue()
        headers = [line for line in output.splitlines() if line.startswith("=== ")]

        self.assertTrue(headers[0].startswith(f"=== r{FIRST_REVID} "))
        page = api_get("en", action="query", prop="info", titles=TITLE)["query"]["pages"][0]
        self.assertTrue(headers[-1].startswith(f"=== r{page['lastrevid']} "))

        for revid in HIDDEN_REVIDS:
            header = next(h for h in headers if h.startswith(f"=== r{revid} "))
            self.assertIn("(content hidden)", header)
        self.assertIn(f"--- r{BEFORE_HIDDEN}\n+++ r{AFTER_HIDDEN}\n", output)


if __name__ == "__main__":
    unittest.main()
