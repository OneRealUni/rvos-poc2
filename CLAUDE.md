# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## How to work in this repo
- State assumptions explicitly; if uncertain, ask rather than guess.
- Minimum code that solves the problem — nothing speculative, no unrequested flexibility.
- Touch only what the task requires; match existing style; don't "improve" unrelated code.
- Turn every task into a verifiable goal (write a test, then make it pass) rather than "make it work."

## Current state
This repo implements a validated 2-agent research-novelty POC (extract_claim,
then judge_novelty). Both directions of the core reasoning test pass — see
README.md and test_rvos_poc.py for how it works and how to run it.

## Completed increments
- POC 1: the two-agent pipeline (extract_claim, judge_novelty) itself.
- POC 2: re-implemented the same two agents' orchestration with LangGraph,
  with no change to reasoning, no new agents, no batch/multi-paper
  processing. The pre-existing test suite passed unchanged, and a
  follow-up review fixed two defects found in that increment (missing
  schema validation on `extract_claim`'s response, and the report's
  related-work list not matching the verdict's citation numbers) -- see
  "Known gotchas already fixed once" below and
  `test_report_citation_numbers_match_related_work_list` in
  `test_rvos_poc.py`.

## Current increment
None defined yet. Agree the next increment's scope here before starting
new work -- the constraints above (no new agents, no batch processing)
were specific to POC 2 and no longer automatically apply once a new
increment is defined.

## What this is

RVOS POC: a two-agent novelty checker for research papers. Given a paper as plain text, it judges whether the paper's
core claim is novel or overlaps with existing published work. Deliberately
no UI, no database, no orchestration framework — see `rvos_poc.py`'s module
docstring.

## Commands

```bash
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then paste a real ANTHROPIC_API_KEY into .env
```

Run the pipeline on a paper:
```bash
python rvos_poc.py "Docs/Test/Bocken.txt"
```
Writes `<input>_report.md` next to the input file. Costs well under $0.05/run
at current Sonnet 5 pricing.

Run the regression suite:
```bash
pytest test_rvos_poc.py
```
These tests call the live Anthropic + OpenAlex APIs (no mocks) and are
skipped automatically if `ANTHROPIC_API_KEY` isn't set. Run a single test with
`pytest test_rvos_poc.py::test_bocken_flags_overlap_not_novel`. Since verdicts
depend on live model output, run this suite after every prompt change, every
model swap, and before adding any new agent — it's the only thing standing
between you and quietly breaking a verdict that used to be correct.

Lint (ruff is in requirements.txt but has no repo config yet, so it runs with
ruff's defaults):
```bash
ruff check .
```

## Architecture

Everything lives in `rvos_poc.py` as a straight-line pipeline, no classes:

1. `extract_claim(paper_text)` — Agent 1. One Claude call that reads the raw
   paper text (truncated to the first 12k chars) and returns JSON: `claim`,
   `method`, `result`, `keywords`. Retries up to 3 times on `JSONDecodeError`
   since the model occasionally returns malformed JSON (e.g. a bad escape),
   and also retries if the parsed JSON is well-formed but missing one of
   the required keys (`REQUIRED_KEYS`) -- without this check a missing
   `keywords` key crashed `_search_node` with a raw `KeyError` instead of
   retrying.
2. `search_openalex(keywords)` — not an LLM call. Queries the free OpenAlex
   API for related work using the extracted keywords, with retry/backoff on
   HTTP 429. Abstracts come back as an inverted index and are reconstructed
   into plain text by `_reconstruct_abstract`.
3. `judge_novelty(extracted, related_works)` — Agent 2, the step the whole
   POC exists to test. One Claude call that compares the claim against the
   retrieved evidence and returns 150-250 words of plain prose (not JSON).
   The prompt requires every overlap claim to cite a specific numbered
   source (`[1]`, `[2]`, ...) and requires an explicit "insufficient
   evidence" verdict rather than a fabricated confident one when evidence is
   thin.
4. `run(paper_path)` wires the three steps together and writes the
   `_report.md` output file.

`_response_text(resp)` exists because Sonnet 5 can prepend a `ThinkingBlock`
before the text block, so `resp.content[0]` isn't reliably the answer — it
finds the first block with `type == "text"`.

Both Claude calls use `MODEL = "claude-sonnet-5"`, chosen for cost; only
escalate if judgment quality is weak in your own reading of the verdicts.

## Test fixtures and their purpose

`Docs/Test/` holds two paired examples used as the project's regression
baseline (see `test_rvos_poc.py`):
- `Bocken.txt` — known near-duplicate of a published paper. The verdict must
  flag overlap, not conclude novelty.
- `Radha Tucci ISPIM25.txt` — the author's own unpublished work. The verdict
  must not flag direct overlap with retrieved work.

**Known limitation:** the "novel" verdict on the ISPIM paper has no
independent confirmation yet — the only people who've read it (the author
and their supervisor) can't give unbiased judgment on their own idea, which
is the exact problem RVOS exists to solve. Treat that verdict as plausible,
not validated.

`Docs/Test/*.txt` and their generated `*_report.md` files are NDA content and
are excluded from git via `.gitignore` — do not remove that exclusion, and do
not delete the files locally; they are the only regression fixtures that
exist for this project.

## Known gotchas already fixed once — don't reintroduce them

- `.env` must be loaded explicitly (`load_dotenv()`) — it isn't automatic.
- OpenAlex rate-limits (HTTP 429) occasionally; `search_openalex` already
  retries with backoff. Set `OPENALEX_MAILTO` in `.env` for a friendlier
  rate-limit tier.
- Some source paper files aren't UTF-8; both `rvos_poc.run` and the test
  suite's `_read_paper` fall back to `cp1252` on `UnicodeDecodeError`.
- `extract_claim` can return valid JSON that's still missing a required
  key -- `REQUIRED_KEYS` must stay checked after `json.loads`, or a
  missing key crashes `_search_node` instead of triggering a retry.
- The report's related-work list and the verdict's `[n]` citations must
  use the same index (both come from `enumerate(related_works)` in
  `judge_novelty` and `run` respectively) -- don't reformat one without
  the other, or the citations stop pointing at anything in the report.
