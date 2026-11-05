"""Print the chronological diff of every revision of a Wikipedia page.

Usage: python wikidiff.py [--lang LANG] <search>

The page is the first result of a Wikipedia search for <search>. Its revisions are
downloaded one batch after the other with the MediaWiki Action API
(https://www.mediawiki.org/wiki/API:Main_page), then printed as unified diffs,
from the creation of the page to its latest revision.
"""
import argparse
import difflib
import json
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterator

API_URL = "https://{lang}.wikipedia.org/w/api.php"
# Wikimedia asks every client for a descriptive User-Agent, and blocks the generic ones
USER_AGENT = "wikidiff/0.1 (Telecom SudParis teaching project; https://github.com/otrack/projet-aise-cours3)"
BATCH_SIZE = 50  # the most revisions, with their content, that the API returns per request


@dataclass
class Revision:
    """One version of a page."""
    revid: int
    parentid: int
    timestamp: str
    user: str
    comment: str
    content: str | None  # None when an administrator hid the text of the revision


def api_get(lang: str, **params: str | int) -> dict:
    """Call the Action API of the Wikipedia in language lang, and return the decoded JSON answer."""
    params.update(format="json", formatversion=2)
    url = API_URL.format(lang=lang) + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if "error" in data:
        raise RuntimeError(f"API error: {data['error'].get('info', data['error'])}")
    return data


def search_title(query: str, lang: str = "en") -> str | None:
    """Return the title of the first page found by a Wikipedia search for query, or None."""
    data = api_get(lang, action="query", list="search", srsearch=query, srlimit=1)
    results = data["query"]["search"]
    return results[0]["title"] if results else None


def parse_revision(rev: dict) -> Revision:
    """Build a Revision from one entry of the 'revisions' list of the API."""
    return Revision(
        revid=rev["revid"],
        parentid=rev["parentid"],
        timestamp=rev["timestamp"],
        user=rev.get("user", ""),
        comment=rev.get("comment", ""),
        content=rev["slots"]["main"]["content"],
    )


def list_revision_ids(title: str, lang: str = "en") -> list[int]:
    """Return the ids of every revision of the page title, oldest first."""
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvprop": "ids",
        "rvlimit": "max",  # 500 ids per request
        "rvdir": "newer",  # oldest first
    }
    ids = []
    while True:
        data = api_get(lang, **params)
        page = data["query"]["pages"][0]
        if page.get("missing"):
            raise LookupError(f"no page titled {title!r}")
        ids += [rev["revid"] for rev in page["revisions"]]
        # The API says where the next request starts in 'continue'; no 'continue' means we are done
        if "continue" not in data:
            return ids
        params.update(data["continue"])


def fetch_batch(revids: list[int], lang: str = "en") -> list[Revision]:
    """Download the revisions whose ids are revids (at most BATCH_SIZE), with their content, in that order."""
    data = api_get(
        lang,
        action="query",
        prop="revisions",
        revids="|".join(str(revid) for revid in revids),
        rvprop="ids|timestamp|user|comment|content",
        rvslots="main",
    )
    by_id = {rev["revid"]: parse_revision(rev) for rev in data["query"]["pages"][0]["revisions"]}
    return [by_id[revid] for revid in revids]


def fetch_revisions(title: str, lang: str = "en") -> list[Revision]:
    """Download every revision of the page title, oldest first, one batch after the other."""
    ids = list_revision_ids(title, lang)
    revisions = []
    for start in range(0, len(ids), BATCH_SIZE):
        revisions += fetch_batch(ids[start:start + BATCH_SIZE], lang)
    return revisions


def diff_revisions(old: Revision | None, new: Revision) -> str:
    """Return the unified diff that turns old (None for the creation of the page) into new."""
    old_lines = old.content.splitlines(keepends=True) if old else []
    new_lines = new.content.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f"r{old.revid}" if old else "/dev/null",
        tofile=f"r{new.revid}",
    )
    # A diff line ends without newline when the last line of a revision has none
    return "".join(line if line.endswith("\n") else line + "\n" for line in diff)


def format_header(rev: Revision) -> str:
    """Return the line that introduces the diff of rev."""
    hidden = " (content hidden)" if rev.content is None else ""
    return f"=== r{rev.revid} | {rev.timestamp} | {rev.user} | {rev.comment}{hidden}\n"


def history_diff(revisions: list[Revision]) -> Iterator[str]:
    """Yield, for each revision in turn, its header followed by its diff with the previous one.

    A revision whose content is hidden gets no diff: the next one is diffed against the last
    revision whose content is visible.
    """
    previous = None
    for rev in revisions:
        if rev.content is None:
            yield format_header(rev)
            continue
        yield format_header(rev) + diff_revisions(previous, rev)
        previous = rev


def main(argv: list[str] | None = None) -> int:
    """Run the command line tool, and return its exit code."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("query", nargs="+", help="the search, e.g. 'Alan Turing'")
    parser.add_argument("--lang", default="en", help="the language of the Wikipedia (default: en)")
    args = parser.parse_args(argv)

    query = " ".join(args.query)
    title = search_title(query, args.lang)
    if title is None:
        print(f"no page found for {query!r}", file=sys.stderr)
        return 1
    for chunk in history_diff(fetch_revisions(title, args.lang)):
        sys.stdout.write(chunk)
    return 0


if __name__ == "__main__":
    sys.exit(main())
