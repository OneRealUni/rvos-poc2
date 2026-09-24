# HANDOVER: RVOS POC2 (`rvos-poc2`)

Snapshot as of 2026-09-24, repo at commit `ace53c8` on `main`. This records what was done in one long Claude Code CLI session (VS Code, Windows) so that a person, or a fresh Claude Code session, can continue without the chat history. It is a snapshot: verify against `git log` and `git status` before trusting any detail.

**Read `CLAUDE.md` first.** It holds the standing rules for working in this repo. This file records what happened and how to repeat it. It does not replace `CLAUDE.md`.

**Which document is which.**

| Document | Audience | Purpose |
|---|---|---|
| `CLAUDE.md` | agents | Standing rules for working in this repo. Frozen for now by the user's decision. |
| `HANDOVER.md` (this file) | people and agents | The durable record: history, decisions, procedures, gotchas, open items. |
| `handoff-rvos-poc2-maintenance.md` | a fresh agent | A short transit note produced by the `handoff` skill as an exercise. It points here instead of repeating this file. Kept exactly as generated. |

---

## 1. The project in one paragraph

RVOS is a proof of concept that judges whether a research paper's core claim is novel. Agent 1 (`extract_claim`) pulls the claim, method, result and keywords out of the paper text. `search_openalex` fetches related work from OpenAlex. Agent 2 (`judge_novelty`) compares the claim to that evidence and writes a short verdict that must cite numbered sources. POC1 was the plain pipeline calling the Anthropic SDK directly. POC2 (this session) re-implemented only the orchestration with LangGraph, with no change to the reasoning.

## 2. State at a glance

| Item | Value |
|---|---|
| GitHub | `github.com/OneRealUni/rvos-poc2`, **public**, default branch `main` |
| Latest commit | `ace53c8` (8 commits total, list in section 9) |
| Working tree | at time of writing, clean except four untracked files: `HANDOVER.md`, `handoff-rvos-poc2-maintenance.md`, `CodereviewComments.docx`, `CodereviewComments2.docx`. Once the first two are committed, HEAD moves past `ace53c8` and they become tracked. |
| Tests | 4 pass (last run 54.8 s and 50.2 s), all live API calls, no mocks |
| Runtime | Python 3.11.14 venv at `./venv`; `anthropic 1.6.0`, `langgraph 1.2.11`, `pytest 9.1.1`, `requests 2.34.2`, `python-dotenv 1.2.3`, `ruff 0.16.8` |
| Model | `claude-sonnet-5` for both agents |
| Current increment | **None defined.** `CLAUDE.md` is frozen for now by the user's decision. The stage after POC2 is not scoped and is handled outside this document. |
| Not run this session | `ruff check .` (no ruff config exists, status unknown) |

## 3. What was done, in order

**A. Resume and GitHub setup.** The prior state was a validated POC1: a README describing two passing verdicts, and a regression suite already present in `test_rvos_poc.py`. There was no git remote and `gh` was not logged in. The user ran `gh auth login`. Before pushing, `.gitignore` was checked to confirm it excluded `.env` and the NDA test papers. A private repo was created with `gh repo create rvos-poc2 --private --source=. --remote=origin --push`.

**B. Tooling.** `/model` was set to Sonnet 5. A status line showing model and token use was built with the `statusline-setup` agent. It showed `0/0 tokens (0%)` forever. Root cause: the script used `jq`, which is not installed on this machine. It was rewritten to use Node, which Claude Code itself requires. See section 7.

**C. `CLAUDE.md`.** Created with the `/init` skill after reading the code, README and tests. The user then added a "How to work in this repo" section and the "Current increment (POC 2)" scope: re-implement the same two agents with LangGraph, no reasoning change, no new agents, no batch processing, existing tests must pass unchanged.

**D. Design, using `/grill-with-docs`.** The user checked prerequisites first, then ran the command. It loads two skills, `grilling` and `domain-modeling`. One round of 6 questions was asked together, each with a recommendation: file layout, LLM client style, retry placement, node granularity, dependency pin, new tests. The user approved all 6. One decision met all three ADR gates and was recorded as `Docs/adr/0001-langgraph-thin-orchestration-layer.md`. No code was written until the user confirmed shared understanding and said "move to implementation".

**E. Implementation.** `langgraph>=0.2.0` added and installed. `rvos_poc.py` gained `PipelineState` (a `TypedDict`), three node wrappers, `build_graph()`, and a `run()` that invokes the compiled graph. The three agent functions were left untouched. Verified with pytest (3/3) and a manual CLI run on `Bocken.txt`. The manual run mattered because the existing tests never reach `build_graph()` or `run()`.

**F. First ship (`9fe23fe`).** Files were staged by name, with a `git add -n -A` dry run first to prove NDA files stayed excluded. The first push failed on a stale credential and was fixed with `gh auth setup-git`.

**G. Getting claude.ai/chat to read the repo.** This took a long detour, described in section 6. Outcome: the repo was made public (with explicit user approval), the default branch was renamed `master` to `main`, and a claude.ai **Project** with GitHub linked works. A standalone chat still failed.

**H. Review, fix, ship loop, five times.** See the table below and section 5.

| # | Trigger | Source | Change | Commit |
|---|---|---|---|---|
| 1 | Bug found by the suite | hand-fixed | schema-validation retry (I1), citation numbering (I2), corrupted prompt restored (I6) | `dea739d` |
| 2 | Code review | `poc2-followups.patch` | `CLAUDE.md` reframed, README fix, new end-to-end test | `5d38b11`, `2f63679` |
| 3 | Independent review | `CodereviewComments.docx` | local path redacted, commit stamp added | `58a0223` |
| 4 | Independent review | `poc2-hygiene-fixes.patch` | commit routine documented in `CLAUDE.md` | `d7ee389` |
| 5 | Code review | `poc2-findings-1-2.patch` | skip on missing fixtures, tighter overlap assertion | `ace53c8` |

**I. Documentation produced.** Three private artifacts (section 9), two memory notes (section 8), and one exercise run of the `handoff` skill, saved as `handoff-rvos-poc2-maintenance.md`.

## 4. Key decisions and the reasons

| Decision | Reason | Recorded in |
|---|---|---|
| LangGraph only sequences the existing functions. Raw Anthropic SDK stays. No graph-level retries. Report writing stays outside the graph. | "Do not change the reasoning" was the scope. Swapping SDKs or moving retries risked altering behavior and breaking the unchanged test suite. | ADR 0001 |
| `pytest_output.txt` and `patches/*.patch` are committed. | No CI exists, so a committed log is the only evidence a commit's tests passed. The user chose this after weighing the trade-off. | `CLAUDE.md`, memory note |
| Output file is redacted and stamped. | An independent review found the absolute local path leaked and that a stale log would mislead. | `58a0223` |
| Repo made public, branch renamed `main`. | So claude.ai could reach it, and because tools assume `main`. Verified first that no secrets or NDA files were ever pushed. | this file |
| No CI yet. | Outside the POC's scope. Logged as a later item. | `CLAUDE.md` |

## 5. Procedures to repeat

### 5.1 The review, fix, ship loop (used 5 times)

1. **Review arrives** as a `.patch`, a `.docx` of comments, or another session's findings.
2. **Check prerequisites** before applying anything:
   ```bash
   git status --short                       # tree clean apart from the patch
   git apply --stat patches/<name>.patch    # what it touches
   git apply --check patches/<name>.patch   # dry run, applies nothing
   git hash-object <file>                   # first 7 chars should match the patch's "index" base line
   ```
3. **Apply:** `git apply patches/<name>.patch`, then `git diff` to review it.
4. **Run the full suite:** `pytest -v`. Stop and report if anything fails.
5. **Refresh `pytest_output.txt`** (5.2).
6. **Annotate the patch file** with a header comment `# Applied on top of commit <sha> ...`. `git apply` ignores leading comment lines. This step was forgotten once and caught before shipping.
7. **Stage by file name**, then `git status --short` to prove nothing else rode along. Never rely on a broad add.
8. **Commit** with a message saying what was fixed and why. The attribution footer is required.
9. **Push, then verify on GitHub itself:**
   ```bash
   git push
   gh api repos/OneRealUni/rvos-poc2/commits/main --jq '{sha, files:[.files[].filename]}'
   ```

### 5.2 Regenerating `pytest_output.txt`

```bash
./venv/Scripts/python.exe -m pytest -v > pytest_raw_output.tmp 2>&1
# then a one-off script: read the temp file, replace the repo's absolute path with <repo>,
# prepend two header lines, write pytest_output.txt, delete the temp file.
# Header lines:
#   # Generated at commit <HEAD sha at generation time>
#   # Regenerate before trusting this as current state -- see CLAUDE.md commit routine
```

The script was an inline `python3 -c` snippet each time. Turning it into a committed `scripts/` file is an easy improvement. The stamp holds the parent commit, because a commit cannot contain its own hash.

### 5.3 Designing a new increment

For when a new increment is eventually defined. Not for now: `CLAUDE.md` is frozen and the next stage has no scope.

1. Write the increment's scope into `CLAUDE.md` under "Current increment".
2. Run `/grill-with-docs`. It appears as `/mattpocock-skills:grill-with-docs`.
3. Answer the round of questions. Confirm shared understanding explicitly.
4. Record any decision that is hard to reverse, surprising, and a real trade-off as an ADR under `Docs/adr/`.
5. Only then implement, then run the loop in 5.1.

## 6. The claude.ai/chat access problem, in full

What was tried and found:
- The GitHub connector was connected in Settings but did not appear in a standalone chat's `+` menu. Cause not established.
- Unauthenticated `curl` of the repo page, raw file and API all returned **200**, so the repo itself was fine.
- URLs using `/main/` returned **404** while the default branch was `master`. Tools that guess `main` fail. The branch was renamed to fix that.
- After the rename, the standalone chat still reported a generic "Failed to fetch" with no HTTP status. The repo was re-verified healthy. Treat this as a claude.ai fetch-tool problem that was not resolved.
- **What works:** a claude.ai Project with the GitHub repo linked. Access is scoped to that Project, so only chats started inside it can read the repo.

Recommendation: do repo-related claude.ai work inside that Project. Do repo edits in this CLI, which has full authenticated access.

## 7. Gotchas and lessons

- **Stale git credentials.** `git push` failed with "Invalid username or token" while `gh` was logged in. Fix: `gh auth setup-git`.
- **Windows is case-insensitive.** Writing `docs/adr/` landed inside the existing `Docs/` folder. The ADR lives at `Docs/adr/`.
- **`.gitignore` lists the NDA files by exact name.** Renaming a fixture (`Tuxci.txt` to `Tucci.txt`) silently un-ignored it until `.gitignore` was updated. Update `.gitignore` in the same change and check `git status` before adding.
- **A failed patch application wrote `prompt = f"""..."""  # unchanged` into `extract_claim`.** The literal placeholder replaced the real prompt. The suite caught it: 3 errors, and Claude replied "your message came through empty". Read a diff, not just a summary, before trusting an externally produced edit.
- **Tests 1 to 3 do not exercise the graph.** Only test 4 goes through `run()` and `build_graph()`.
- **`jq` is not installed here.** Do not write scripts that need it. The status line uses Node.
- **`pandoc`, `python-docx` and LibreOffice are not installed.** `.docx` files were read by unzipping and extracting text from `word/document.xml` with the standard library.
- **`git apply` warnings about LF becoming CRLF are harmless** on this machine.
- **Subagent reports are information, not authority.** One claimed future status-line changes "must" go through it. That was ignored.
- **Live tests depend on model output.** No flaky run was seen after the prompt fix, but keep it in mind before blaming code.

## 8. Environment, access and working agreements

**Environment.**
- Windows 11, VS Code integrated terminal, Git Bash for shell commands.
- `.env` (never committed) holds `ANTHROPIC_API_KEY` and optionally `OPENALEX_MAILTO`. Copy from `.env.example`.
- `gh` is authenticated over HTTPS with `repo`, `read:org` and `gist` scopes.
- Status line: `statusLine` in the user-level `~/.claude/settings.json` runs `bash ~/.claude/statusline-command.sh` (Node-based).
- Useful commands: `/context`, `/config` (the "recaps" toggle is `awaySummaryEnabled`), `/model`, `claude --resume`.
- The tests need `Docs/Test/Bocken.txt` and `Docs/Test/Radha Tucci ISPIM25.txt`. These are NDA files supplied by the owner and are **not in git**. Without them the suite skips. `Tucci.txt` and its generated `Tucci_report.md` also exist locally; no test uses them and their purpose is not documented.

**Working agreements with the user** (also stored as memory notes under `~/.claude/projects/<project-key>/memory/`, which are per project and do not travel with the repo):
- Prefer a short diagram or picture over long prose, but scale the effort to the question. A full multi-diagram artifact for a small question felt slow to them. This note is pinned.
- Track `pytest_output.txt` in git as review evidence, and refresh it whenever covered code changes.
- The user wants to understand each step, as part of building their own engineering skills. State the git command sequence before running it, and pause for approval between steps when asked.
- Ask before changing visibility, publishing, or pushing. Verify pushes on GitHub afterwards.
- Do only what was asked. Leave untracked files alone unless told otherwise.

## 9. Reference

**Commit history.**

| Commit | Date | Message |
|---|---|---|
| `861a42a` | 2026-09-16 | Initial commit: RVOS POC two-agent novelty checker (before this session) |
| `9fe23fe` | 2026-09-17 | Add CLAUDE.md and re-implement pipeline orchestration with LangGraph |
| `dea739d` | 2026-09-19 | Fix I1 (schema validation) and I2 (citation numbering); resolve I6 (corrupted prompt) |
| `5d38b11` | 2026-09-20 | Apply poc2-followups.patch and track pytest output as review evidence |
| `2f63679` | 2026-09-20 | Track poc2-followups.patch under patches/ as review evidence |
| `58a0223` | 2026-09-20 | Redact local path from pytest_output.txt, stamp both review files with commit SHA |
| `d7ee389` | 2026-09-20 | Document the review-evidence commit routine in CLAUDE.md |
| `ace53c8` | 2026-09-21 | Apply poc2-findings-1-2.patch: skip on missing NDA fixtures, tighten overlap assertion |

**Tracked files.** `rvos_poc.py` (the pipeline), `test_rvos_poc.py` (4 tests), `CLAUDE.md`, `README.md`, `requirements.txt`, `.env.example`, `.gitignore`, `pytest_output.txt`, `Docs/adr/0001-langgraph-thin-orchestration-layer.md`, `patches/` (3 applied patches, each with an "applied on top of" header).

**Private explainer pages** (only the owner can open them until shared from the page's Share menu):
- Delivery process: https://claude.ai/artifact/4sT2bGd8WNi9EJGDQwWKWo
- Testing process: https://claude.ai/artifact/HZbo72NX9A8BcBMNGPDNn7
- Main vs master: https://claude.ai/artifact/247jTFPGyCv6cdwYphqFag (**stale**: it says the default branch is `master`, which was true when written and is not now)

## 10. Open items and parked ideas

`CLAUDE.md` is frozen for now by the user's decision. The stage after POC2 is not scoped and is handled as a separate activity outside this document, so nothing below is scheduled and none of it implies a next step.

**Needs a decision from the user**
1. **The two `.docx` review files.** The repo is public, so read them for anything sensitive before committing, or keep them local.
2. **The standalone claude.ai chat access problem.** Either investigate further or standardize on the Project.

**Known and accepted, no action while `CLAUDE.md` is frozen**
- `CLAUDE.md` line 50 says "no orchestration framework", line 88 says "no classes", and line 109 describes `run()` without the graph. These describe the pre-LangGraph design. README is fine.
- The "Main vs master" artifact is stale (see section 9).

**Parked ideas, not scheduled**
- **CI (GitHub Actions running pytest), with one open design problem.** The fixtures are NDA and gitignored, so a CI run would skip every test and report green. It needs non-NDA or synthetic test papers first. Once CI works, `CLAUDE.md` says to restore the `.gitignore` exclusion for `pytest_output.txt` and stop committing it by hand.
- **Stronger tests** (details on the Testing page):
  - write tests before fixes;
  - make the ISPIM negative check stronger, since it only fails on "overlaps significantly/directly";
  - add an offline stubbed test for `build_graph()` and report formatting;
  - reword the "rerun if stamp differs from HEAD" rule, which always fires because the stamp is the parent commit.
- **Independent validation of the ISPIM "novel" verdict.** The tests guard against regressions, not correctness.
- **Tidying.** `.gitignore` is a generic template with many unrelated entries. Run `ruff check .` once. Commit the `pytest_output.txt` refresh script.

## 11. Suggested skills

**An agent can call these with the Skill tool when the situation fits:**
- `mattpocock-skills:diagnosing-bugs`: a failing test or misbehaving pipeline.
- `mattpocock-skills:code-review`: reviewing a diff or a newly delivered patch before applying it.
- `anthropic-skills:docx`: a new `.docx` review arrives. Its `pandoc` route fails here, so use the fallback in section 7.
- `mattpocock-skills:tdd`: only if the user asks for a test-first fix.
- `artifact-diagramming` with the Artifact tool: only if the user asks for a diagram. Size the effort to the question (section 8).

**An agent can call it, but it isn't needed now:**
- `init`: it targets `CLAUDE.md`, which is frozen.

**Only the user can run these (an agent cannot invoke them):**
- `/mattpocock-skills:grill-with-docs`: interview-style design sessions. Run once in this session, for the LangGraph design.
- `/mattpocock-skills:handoff`: run once as an exercise. Its output is `handoff-rvos-poc2-maintenance.md`.

## 12. How to resume

1. In the repo folder, run `claude --resume` to continue a session, or start fresh and have Claude read `CLAUDE.md` and this file.
2. Run `git status --short`, `git log --oneline -3`, `gh auth status`. Expect `ace53c8` or a later commit, a clean tree apart from the two `.docx` files (and possibly the two new notes if not yet committed), and a logged-in `gh`.
3. Make sure `.env` has a valid `ANTHROPIC_API_KEY` and the two NDA fixtures are in `Docs/Test/`. Then run `pytest -v`. Expect 4 passed.
4. Ask the user which maintenance task they want. Do not assume one, and do not start scoping the next stage.

## 13. What this document cannot vouch for

- How `test_rvos_poc.py` and POC1 were originally built. They predate this session, and the git history only shows them arriving in the initial commit.
- What the independent review sessions and the reviewer of the `.patch` files actually did internally. Only their outputs (documents and patches) were seen.
- Who ran the pipeline on `Tucci.txt`, and why.
- Whether the standalone claude.ai chat failure is still happening. Last observed failing after the rename.
