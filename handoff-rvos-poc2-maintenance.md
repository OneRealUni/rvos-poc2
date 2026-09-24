# Handoff: RVOS POC2 maintenance

Written for a fresh agent. Focus of the next session: **resume POC2 maintenance**.

## Hard constraints from the user (do not break these)
- **Do not edit `CLAUDE.md`.** This includes the "Current increment" section and the stale lines described in `HANDOVER.md` section 10.
- **POC3 scope is not defined.** Do not define it, plan it, or start it. Do not run `/grill-with-docs` for it.
- Do not commit or push anything unless the user says so in the current turn.

## Where things stand
- Repo: the `origin` remote of the current directory (see `git remote -v`). Branch `main`, HEAD `ace53c8`, pushed and in sync.
- Working tree: clean except three untracked files: `HANDOVER.md`, `CodereviewComments.docx`, `CodereviewComments2.docx`. Nothing is in flight.
- Tests: 4 pass (`pytest -v`), all live API calls.
- The user has not yet decided whether to commit `HANDOVER.md` or the two `.docx` files. Leave them alone.

## Read these instead of asking the user to re-explain
| Need | Where |
|---|---|
| Rules for working in this repo | `CLAUDE.md` |
| Full history, decisions, gotchas, environment, open items | `HANDOVER.md` (untracked, local) |
| The design decision behind the LangGraph refactor | `Docs/adr/0001-langgraph-thin-orchestration-layer.md` |
| Latest test evidence | `pytest_output.txt` (its stamp is the parent commit by design) |
| Applied review patches | `patches/` |
| Process diagrams (private, owner-only unless shared) | https://claude.ai/artifact/4sT2bGd8WNi9EJGDQwWKWo (delivery), https://claude.ai/artifact/HZbo72NX9A8BcBMNGPDNn7 (testing) |

The repeatable procedure for any new review patch is `HANDOVER.md` section 5.1. The `pytest_output.txt` refresh is section 5.2. Do not restate them; follow them.

## How this user wants to work
- Explain the exact git/GitHub command sequence before running it, and pause for approval between steps when asked.
- Prefer a short diagram or picture over long prose, sized to the question. Keep answers concise.
- Verify every push on GitHub afterwards with the API, not just local output.
- Ask before changing repo visibility, publishing artifacts, or pushing.
- Stage files by name. Never sweep in untracked files.
- Give honest, direct assessments, including pushback when a reviewer's or the user's premise is off.

## Things learned the hard way (short list; detail is in HANDOVER.md section 7)
- If `git push` says "Invalid username or token" while `gh` is logged in, run `gh auth setup-git`.
- The NDA test papers are gitignored by exact filename. If a fixture is renamed, update `.gitignore` in the same change.
- `jq`, `pandoc`, `python-docx` and LibreOffice are not installed. Read `.docx` files by unzipping and extracting `word/document.xml` text.
- Tests 1 to 3 do not exercise the LangGraph wiring. Only the end-to-end test does.

## Unverified, so do not treat as fact
- Whether `ruff check .` passes. It was never run.
- Whether the standalone claude.ai chat can now fetch the repo. It failed last time it was tried. A claude.ai Project with GitHub linked did work.
- Who ran the pipeline on the third local fixture and why. Its purpose is undocumented.
- How the original test file was written. It predates the session.
- The suite has not shown flakiness, but it depends on live model output. Rerun once before blaming code for a surprising failure.

## Suggested skills
Call the Skill tool for these when the situation fits:
- `mattpocock-skills:diagnosing-bugs`: if a test fails or the pipeline misbehaves.
- `mattpocock-skills:code-review`: to review a diff or a newly delivered patch before applying it.
- `anthropic-skills:docx`: only if a new `.docx` review arrives. Its `pandoc` path will fail here, so use the fallback above.
- `mattpocock-skills:tdd`: only if the user asks for a test-first fix.

Not for this session: `init` (would rewrite `CLAUDE.md`), `mattpocock-skills:grill-with-docs` (POC3 scoping), and `mattpocock-skills:handoff`.

## First moves
1. `git status --short`, `git log --oneline -3`, `gh auth status`.
2. Read `CLAUDE.md`, then `HANDOVER.md`.
3. Ask the user what maintenance task they want. Do not assume one.
