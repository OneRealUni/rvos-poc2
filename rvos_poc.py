"""
RVOS Proof of Concept -- core reasoning test.

Two-agent pipeline: extract the paper's claim, then judge its novelty
against related work retrieved from OpenAlex. Deliberately no UI, no
database, no orchestration framework -- see RVOS_POC_Week1_Spec.md
for why those are out of scope this week.

Usage:
    python rvos_poc.py path/to/paper.txt

Requires ANTHROPIC_API_KEY in the environment (see .env.example).
"""

import json
import os
import sys
import time

import requests
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
MODEL = "claude-sonnet-5"  # cheap and sufficient for this step; only escalate if judgment quality is weak in your reading


def _response_text(resp) -> str:
    """Sonnet 5 can prepend a ThinkingBlock before the text block, so
    content[0] isn't reliably the answer -- find the first text block."""
    for block in resp.content:
        if block.type == "text":
            return block.text.strip()
    raise ValueError(f"No text block in response: {resp.content!r}")


def extract_claim(paper_text: str) -> dict:
    """Agent 1: pull out the core claim, method, and result.

    Occasionally returns a malformed JSON string (e.g. an invalid escape
    like \\' inside a value) -- retry a couple of times rather than fail
    the whole pipeline on a single bad sample."""
    prompt = f"""Read this research paper text and extract, in your own words:
1. The core claim (one or two sentences)
2. The method used (one or two sentences)
3. The key stated result (one or two sentences)
4. Three to five search-friendly keyword phrases for finding related work

Return ONLY valid JSON with keys: claim, method, result, keywords (a list of strings).
No markdown fences, no commentary, no escaped quotes inside string values --
just the JSON object.

PAPER TEXT:
{paper_text[:12000]}
"""
    last_error = None
    for attempt in range(3):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        text = _response_text(resp)
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            last_error = e
            continue
    raise last_error


def _reconstruct_abstract(inverted_index):
    """OpenAlex stores abstracts as an inverted index -- rebuild plain text."""
    if not inverted_index:
        return ""
    positions = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def search_openalex(keywords: list, limit: int = 8) -> list:
    """Evidence retrieval: query OpenAlex for related work. Not an LLM call --
    OpenAlex already does the search; we just ask it."""
    query = " ".join(keywords)
    url = "https://api.openalex.org/works"
    params = {"search": query, "per-page": limit, "sort": "relevance_score:desc"}
    mailto = os.environ.get("OPENALEX_MAILTO")
    if mailto:
        params["mailto"] = mailto

    for attempt in range(3):
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 429 and attempt < 2:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        break
    results = []
    for w in r.json().get("results", []):
        results.append({
            "title": w.get("title"),
            "year": w.get("publication_year"),
            "id": w.get("id"),
            "abstract": _reconstruct_abstract(w.get("abstract_inverted_index")),
        })
    return results


def judge_novelty(extracted: dict, related_works: list) -> str:
    """Agent 2: the core reasoning step -- compare the claim against retrieved evidence.
    This is the step the whole POC exists to test."""
    evidence_block = "\n\n".join(
        f"[{i+1}] {w['title']} ({w['year']})\n{w['abstract'][:500]}"
        for i, w in enumerate(related_works) if w["abstract"]
    )
    prompt = f"""You are assessing the novelty of a research claim against related published work.

CLAIM: {extracted['claim']}
METHOD: {extracted['method']}
RESULT: {extracted['result']}

RELATED WORK RETRIEVED FROM OPENALEX:
{evidence_block if evidence_block else "(No abstracts were retrievable for the top matches.)"}

Instructions:
- Judge whether the claim appears novel, overlaps significantly with specific retrieved work, or whether there is insufficient evidence to judge.
- If you say something overlaps, name the SPECIFIC numbered source it overlaps with. Never make a vague claim without pointing to a numbered source.
- If the retrieved evidence is thin, unrelated, or abstracts are empty, say "insufficient evidence" explicitly rather than guessing. This is the single most important instruction in this prompt -- do not fabricate a confident verdict from weak evidence.
- Write 150-250 words of plain prose, not JSON.
"""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return _response_text(resp)

def run(paper_path: str):
    try:
        with open(paper_path, "r", encoding="utf-8") as f:
            paper_text = f.read()
    except UnicodeDecodeError:
        with open(paper_path, "r", encoding="cp1252") as f:
            paper_text = f.read()

    print("Extracting claim...")
    extracted = extract_claim(paper_text)

    print("Searching OpenAlex for related work...")
    related = search_openalex(extracted["keywords"])

    print("Judging novelty...")
    verdict = judge_novelty(extracted, related)

    related_lines = "\n".join(f"- {w['title']} ({w['year']})" for w in related)
    report = f"""# RVOS POC report -- {os.path.basename(paper_path)}

## Extracted claim
{extracted['claim']}

## Method
{extracted['method']}

## Stated result
{extracted['result']}

## Related work retrieved ({len(related)} results)
{related_lines}

## Novelty verdict
{verdict}
"""
    out_path = paper_path.rsplit(".", 1)[0] + "_report.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nDone. Report written to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rvos_poc.py path/to/paper.txt")
        sys.exit(1)
    run(sys.argv[1])
