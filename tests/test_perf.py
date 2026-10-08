"""Measure how long wikidiff takes to download the history of a page.

Usage, from the root of the project: python -m tests.test_perf [title]
It is a benchmark, not a unit test: python -m unittest does not run it.

Prints the time spent in fetch_revisions, the number of revisions, and a hash of the
output of wikidiff: an optimisation must keep the hash unchanged (unless someone edited
the page in the meantime, in which case its last revision changed too).
"""
import hashlib
import sys
import time

import wikidiff

TITLE = "Consistent hashing"  # some 340 revisions, none hidden


def main() -> None:
    """Run the benchmark on the page given on the command line, or on TITLE."""
    title = sys.argv[1] if len(sys.argv) > 1 else TITLE
    start = time.perf_counter()
    revisions = wikidiff.fetch_revisions(title)
    elapsed = time.perf_counter() - start
    output = "".join(wikidiff.history_diff(revisions))
    print(f"page:      {title}")
    print(f"revisions: {len(revisions)} (last: r{revisions[-1].revid})")
    print(f"output:    sha256 {hashlib.sha256(output.encode()).hexdigest()[:16]}")
    print(f"time:      {elapsed:.1f} s")


if __name__ == "__main__":
    main()
