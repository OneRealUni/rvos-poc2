"""
Regression tests for rvos_poc.py, per the plan in README.md's
"Next stage: TDD, not more manual runs" section.

These run the real two-agent pipeline (live Anthropic + OpenAlex calls)
against the two known test papers and check the same two properties that
were originally verified by hand:
- Bocken.txt is a near-duplicate of a published paper -> verdict must
  flag overlap, not conclude novelty.
- The ISPIM paper is the author's own unpublished work -> verdict must
  not flag direct overlap with retrieved work.
- Any overlap claim, in either verdict, must cite a specific numbered
  source -- no vague unattributed claims.

Requires ANTHROPIC_API_KEY in the environment (.env). Each run costs a
small amount (see README.md) and results can vary between runs since
they depend on live model output -- that's the tradeoff this suite
accepts in exchange for testing real behavior instead of mocks.
"""

import os
import re
from pathlib import Path

import pytest

from rvos_poc import extract_claim, judge_novelty, search_openalex

BASE_DIR = Path(__file__).parent / "Docs" / "Test"
BOCKEN_PATH = BASE_DIR / "Bocken.txt"
ISPIM_PATH = BASE_DIR / "Radha Tucci ISPIM25.txt"

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set -- these tests call the live Anthropic API",
)


def _read_paper(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1252")


def _run_pipeline(path: Path) -> str:
    paper_text = _read_paper(path)
    extracted = extract_claim(paper_text)
    related = search_openalex(extracted["keywords"])
    return judge_novelty(extracted, related)


def _paragraphs(text: str):
    return [p for p in re.split(r"\n\s*\n", text) if p.strip()]


def _sentences(text: str):
    return re.split(r"(?<=[.!?])\s+", text)


_HEDGE_WORDS = re.compile(
    r"\b(no|not|n't|without|insufficient|rather than|thin|tangential|"
    r"unclear|unlikely|lack(?:s|ing)?|minimal|little|none|nothing|"
    r"absen(?:ce|t))\b",
    re.IGNORECASE,
)


def _asserts_overlap(sentence: str) -> bool:
    """True for a sentence that affirmatively claims overlap, as opposed to
    one that raises and then rules overlap out (e.g. "thin and tangential
    rather than directly overlapping", "insufficient evidence of overlap")."""
    return "overlap" in sentence.lower() and not _HEDGE_WORDS.search(sentence)


@pytest.fixture(scope="module")
def bocken_verdict():
    return _run_pipeline(BOCKEN_PATH)


@pytest.fixture(scope="module")
def ispim_verdict():
    return _run_pipeline(ISPIM_PATH)


def test_bocken_flags_overlap_not_novel(bocken_verdict):
    verdict_lower = bocken_verdict.lower()
    assert "overlap" in verdict_lower, (
        f"Expected Bocken verdict to flag overlap, got: {bocken_verdict!r}"
    )
    assert not re.search(r"\b(appears|is)\s+novel\b", verdict_lower), (
        f"Bocken verdict should not conclude novelty, got: {bocken_verdict!r}"
    )


def test_ispim_does_not_flag_direct_overlap(ispim_verdict):
    verdict_lower = ispim_verdict.lower()
    assert not re.search(r"overlaps?\s+(significantly|directly)\b", verdict_lower), (
        f"ISPIM verdict should not flag direct overlap, got: {ispim_verdict!r}"
    )


def test_overlap_claims_cite_a_numbered_source(bocken_verdict, ispim_verdict):
    # Checked per-paragraph rather than per-sentence: a paragraph often
    # elaborates on one overlap claim across several sentences, citing the
    # numbered source once and then referring back to it. Sentences that
    # raise and then rule out overlap (hedge words like "insufficient",
    # "rather than", "thin") don't need a citation -- only affirmative
    # overlap claims do.
    for verdict in (bocken_verdict, ispim_verdict):
        for paragraph in _paragraphs(verdict):
            if any(_asserts_overlap(s) for s in _sentences(paragraph)):
                assert re.search(r"\[\d+\]", paragraph), (
                    f"Overlap claim without a numbered source citation: {paragraph!r}"
                )
