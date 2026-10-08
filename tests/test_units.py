"""Unit tests of wikidiff: no network needed."""
import unittest

from wikidiff import Revision, diff_revisions, history_diff, parse_revision


def revision(revid: int, parentid: int, content: str | None) -> Revision:
    """Build a revision with the given ids and content, and dummy metadata."""
    return Revision(revid, parentid, f"2020-01-0{revid}T00:00:00Z", "Alice", f"edit {revid}", content)


class TestWikidiff(unittest.TestCase):

    def test_parse_revision(self) -> None:
        rev = parse_revision({
            "revid": 2, "parentid": 1, "timestamp": "2020-01-02T00:00:00Z",
            "user": "Alice", "comment": "typo",
            "slots": {"main": {"contentmodel": "wikitext", "content": "Hello\n"}},
        })
        self.assertEqual(rev, Revision(2, 1, "2020-01-02T00:00:00Z", "Alice", "typo", "Hello\n"))

    def test_creation_is_diffed_against_nothing(self) -> None:
        diff = diff_revisions(None, revision(1, 0, "a\nb\n"))
        self.assertEqual(diff, "--- /dev/null\n+++ r1\n@@ -0,0 +1,2 @@\n+a\n+b\n")

    def test_last_line_without_newline(self) -> None:
        diff = diff_revisions(revision(1, 0, "a\nb"), revision(2, 1, "a\nc"))
        self.assertTrue(diff.endswith("-b\n+c\n"))

    def test_history_diff_chains_revisions(self) -> None:
        revisions = [revision(1, 0, "a\n"), revision(2, 1, "a\nb\n"), revision(3, 2, "b\n")]
        chunks = list(history_diff(revisions))
        self.assertEqual(len(chunks), 3)
        self.assertTrue(chunks[0].startswith("=== r1 | 2020-01-01T00:00:00Z | Alice | edit 1\n--- /dev/null\n"))
        self.assertIn("--- r1\n+++ r2\n", chunks[1])
        self.assertIn("+b\n", chunks[1])
        self.assertIn("--- r2\n+++ r3\n", chunks[2])
        self.assertIn("-a\n", chunks[2])

    def test_history_diff_skips_hidden_revisions(self) -> None:
        revisions = [revision(1, 0, "a\n"), revision(2, 1, None), revision(3, 2, "a\nb\n")]
        chunks = list(history_diff(revisions))
        self.assertEqual(chunks[1], "=== r2 | 2020-01-02T00:00:00Z | Alice | edit 2 (content hidden)\n")
        self.assertIn("--- r1\n+++ r3\n", chunks[2])


if __name__ == "__main__":
    unittest.main()
