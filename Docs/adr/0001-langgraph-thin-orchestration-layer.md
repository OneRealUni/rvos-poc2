# LangGraph as a thin orchestration layer over existing functions

For the POC2 increment (re-implementing the two-agent pipeline's orchestration
in LangGraph), we decided LangGraph's `StateGraph` wires the existing
`extract_claim`, `search_openalex`, and `judge_novelty` functions as three
linear nodes, and nothing more. It does not replace the raw `anthropic.Anthropic()`
client calls with `langchain_anthropic`, does not take over the retry/backoff
logic already inside those functions (JSON retry in `extract_claim`, 429
backoff in `search_openalex`), and does not include report-file writing as a
node — that stays in `run()`, after the graph finishes.

We picked this over the more idiomatic LangGraph style (LangChain model
wrappers, retries as conditional edges) because the POC2 scope explicitly
says "do not change the reasoning," and swapping SDKs or moving control flow
into graph edges risks changing response handling or retry behavior in ways
that could break the existing regression suite, which must keep passing
unchanged with its current imports from `rvos_poc`.
