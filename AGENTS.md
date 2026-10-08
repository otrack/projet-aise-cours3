# AGENTS.md

## Project
- `wikidiff.py`: prints the chronological diff of all the revisions of a Wikipedia page,
  downloaded with the MediaWiki Action API
- `tests/test_units.py`: unit tests (offline); `tests/test_integration.py`: integration test
  (calls Wikipedia); `tests/test_perf.py`: a benchmark, which times the download of the
  revisions of a page (not a unit test)
- `debug/trace.py`: a proxy that prints the exchanges between opencode and the model
- new code in `<module>.py` at the root, with its unit tests (unittest, offline) in `tests/`

## Commands
- run: `python wikidiff.py "<search>"`
- test: use the skill `python-unit-tests` (or `python -m unittest -v`)
- benchmark: `python -m tests.test_perf`
- run every command from the root of the project

## Conventions
- Python standard library only
- type hints and a one-line docstring on every function
- every new function comes with unit tests
- be polite with Wikipedia: keep the `User-Agent`, at most 4 requests in parallel

## Do not
- edit `AGENTS.md`, `tests/test_perf.py`, anything under `debug/` or `.opencode/`
