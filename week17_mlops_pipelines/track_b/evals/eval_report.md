# 📊 Agentic AI Assistant - Evaluation Harness Report (Week 16)

*Generated from custom scratch-built evaluation harness.*

**Total Benchmark Queries:** 10 | **Evaluated Architectures:** Single-Agent ReAct vs. Multi-Agent (Researcher + Verifier)

## 1. Executive Summary & Comparative Metrics

| Metric | Single-Agent ReAct | Multi-Agent (Researcher + Verifier) | Delta / Overhead |
| :--- | :---: | :---: | :---: |
| **Task Completion Rate** | **100.0%** | **100.0%** | +0.0% |
| **Tool-Call Correctness** | **100.0%** | **100.0%** | +0.0% |
| **Avg Trajectory Length (steps)** | 1.8 | 1.8 | +0.0 steps |
| **Avg Tokens Per Query** | 1249 | 1629 | **+30.4% coordination cost** |
| **Total Suite Cost (USD)** | $0.002490 | $0.003358 | +$0.000868 |

## 2. Token & Cost Accounting Analysis
The Multi-Agent architecture introduces an average of **30.4% token overhead** (1629 vs 1249 tokens). This overhead is strictly attributable to:
1. **Context Isolation Transfer**: Passing draft answers and cited snippets to the independent Verifier agent.
2. **Critic Evaluation & Critique**: Token generation for rigorous factual verification.
3. **Self-Correction Refinement**: The additional reasoning step when the Verifier requests revision.

## 3. Detailed Per-Query Evaluation Log

| ID | Query Summary | Architecture | Steps | Tools Called | Tokens | Status | Failure Taxonomy |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :--- |
| TC-01 | Calculate sqrt(144) + 2**8 and round t... | Single-Agent | 2 | `calculate, finish` | 1359 | ✅ Pass | None |
| TC-01 | Calculate sqrt(144) + 2**8 and round t... | Multi-Agent | 2 | `calculate, finish` | 1763 | ✅ Pass | None |
| TC-02 | What is today's current date and time?... | Single-Agent | 2 | `get_current_datetime, finish` | 1318 | ✅ Pass | None |
| TC-02 | What is today's current date and time?... | Multi-Agent | 2 | `get_current_datetime, finish` | 1717 | ✅ Pass | None |
| TC-03 | What vector database and embedding mod... | Single-Agent | 2 | `query_knowledge_base, finish` | 1428 | ✅ Pass | None |
| TC-03 | What vector database and embedding mod... | Multi-Agent | 2 | `query_knowledge_base, finish` | 1862 | ✅ Pass | None |
| TC-04 | Search the web for vLLM high-throughpu... | Single-Agent | 2 | `search_web, finish` | 1418 | ✅ Pass | None |
| TC-04 | Search the web for vLLM high-throughpu... | Multi-Agent | 2 | `search_web, finish` | 1838 | ✅ Pass | None |
| TC-05 | What web framework powers the API, and... | Single-Agent | 2 | `calculate, finish` | 1352 | ✅ Pass | None |
| TC-05 | What web framework powers the API, and... | Multi-Agent | 2 | `calculate, finish` | 1759 | ✅ Pass | None |
| TC-06 | Load and apply the cross_source_fact_c... | Single-Agent | 2 | `load_skill_instructions, finish` | 1446 | ✅ Pass | None |
| TC-06 | Load and apply the cross_source_fact_c... | Multi-Agent | 2 | `load_skill_instructions, finish` | 1869 | ✅ Pass | None |
| TC-07 | Explain the thing we talked about yest... | Single-Agent | 1 | `ask_user_clarification` | 656 | ✅ Pass | None |
| TC-07 | Explain the thing we talked about yest... | Multi-Agent | 1 | `ask_user_clarification` | 656 | ✅ Pass | None |
| TC-08 | Why is asynchronous concurrency benefi... | Single-Agent | 1 | `finish` | 704 | ✅ Pass | None |
| TC-08 | Why is asynchronous concurrency benefi... | Multi-Agent | 1 | `finish` | 1151 | ✅ Pass | None |
| TC-09 | Search web for latest AI news and upda... | Single-Agent | 2 | `search_web, finish` | 1390 | ✅ Pass | None |
| TC-09 | Search web for latest AI news and upda... | Multi-Agent | 2 | `search_web, finish` | 1822 | ✅ Pass | None |
| TC-10 | Query internal knowledge base for depl... | Single-Agent | 2 | `query_knowledge_base, finish` | 1420 | ✅ Pass | None |
| TC-10 | Query internal knowledge base for depl... | Multi-Agent | 2 | `query_knowledge_base, finish` | 1854 | ✅ Pass | None |

## 4. Failure Taxonomy & Failure Injection Results

### Classification Taxonomy (per course framework):
- **Hard Failure**: Unhandled exceptions, infinite iteration loops, or unparseable tool signatures.
- **Soft Failure**: Syntactically valid completion that lacks factual grounding or hallucinates.
- **Cascading Soft Failure**: Early retrieval/tool mistake that misleads subsequent reasoning steps.

### Failure Injection Observations:
- **[TC-09] (Search web for latest AI news and u...)**: System detected fault (`Failure successfully recognized and handled gracefully.`). Gracefully reported limitation without hallucinating.
- **[TC-10] (Query internal knowledge base for d...)**: System detected fault (`Failure successfully recognized and handled gracefully.`). Gracefully reported limitation without hallucinating.