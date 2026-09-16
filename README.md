# RVOS POC -- status and how to run it

## Status (updated after first real runs)

Two-direction test result:

| Test paper | Expected verdict | Actual verdict | Confirmed by |
|---|---|---|---|
| ISPIM CSBMI paper (own work) | Novel | Novel | Not yet -- see limitation below |
| Bocken "Marketing in the Anthropocene" | Overlaps existing work | Correctly flagged near-total overlap with the exact published paper | Verified -- paper fetched and confirmed genuine |

**Known limitation:** the CSBMI "novel" verdict has no independent
confirmation yet. The only people who've read it (the author and their
supervisor) can't give unbiased judgment on their own idea -- which is
itself the exact problem RVOS exists to solve. Treat this verdict as
plausible, not validated, until either ISPIM's peer review comes back
or an external rubric panel weighs in (see the deep analysis document,
Section 3.3).

Both test files (`Docs/Test/Radha Tucci ISPIM25.txt` and
`Docs/Test/Bocken.txt`, and their generated reports) are kept in
`Docs/Test/` -- do not delete them. They are now the project's first
regression test cases. (`Docs/Test/Tuxci.txt` also lives there; all
three are NDA content and excluded from git via `.gitignore`.)

## Corrections made since the original version

Claude Code CLI fixed three real gaps in the first draft:
- `.env` wasn't being loaded automatically -- added `load_dotenv()`
- OpenAlex occasionally rate-limits (HTTP 429) -- added retry with backoff
  and an optional `OPENALEX_MAILTO` for a better rate-limit tier
- Some source files aren't UTF-8 -- added a `cp1252` fallback on read

## Setup (about 5 minutes)

```bash
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and paste in your real Anthropic API key from
https://console.anthropic.com/settings/keys

## Run it

```bash
python rvos_poc.py "Docs/Test/Bocken.txt"
```

This will:
1. Call Claude once to extract the claim, method, and result
2. Query OpenAlex (free, no key needed) for 5-10 related works
3. Call Claude again to judge novelty against that evidence, with citations
4. Write `paper1_report.md` next to your input file

Total cost: well under $0.05 per run at current Sonnet 5 pricing
($2 / $10 per million input / output tokens).

## Next stage: TDD, not more manual runs

The two existing test papers become a permanent regression test before
anything else gets built:

```bash
pip install pytest
```

Create `test_rvos_poc.py` asserting:
- Running on `Bocken.txt` produces a verdict containing "overlap" (or
  equivalent language), not "novel"
- Running on the ISPIM paper produces a verdict that does NOT flag
  direct overlap
- Every overlap claim in any verdict cites a specific numbered source
  (no vague unattributed claims)

Run this test suite after every prompt change, every model swap, and
before adding any new agent. It is the only thing standing between you
and quietly breaking a verdict that used to be correct.

## If something breaks

- `JSONDecodeError` in `extract_claim` -- the model didn't return clean
  JSON. Print `resp.content[0].text` before the `.replace()` calls to see
  what came back, and adjust the prompt if it's consistently misbehaving.
- Empty `related` list -- your keywords might be too narrow or too
  jargon-heavy for OpenAlex's search. Try printing `extracted['keywords']`
  and testing a couple manually against https://openalex.org
- HTTP 429 from OpenAlex -- already retried automatically; set
  `OPENALEX_MAILTO=you@example.com` in `.env` for friendlier rate limits.

None of this requires going back through Claude Code CLI's grill/spec/ticket
flow for changes this small. Return to that only once you're expanding past
two agents into something that genuinely needs the ceremony.
