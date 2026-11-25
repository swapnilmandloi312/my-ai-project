# Swapnil AI Labs — Research preview 001
25 November 2026. Not peer reviewed. Local synthetic experiments, not external-model benchmarks.
| Experiment | Baseline | Candidate |
|---|---|---|
| Policy: 144 labelled cases | Name allowlist accepted 89/137 invalid, 7/7 valid | Gateway accepted 0/137 invalid, 7/7 valid |
| Context: 120 tasks | Full 120/120, 11280 words; first 4: 27/120 | Lexical top 4: 118/120, 2644 whitespace words |
| Memory: 120 cases | Unfiltered latest 0/120 | Scoped filter 120/120 including 24 abstentions |
| Intent: 120 test strings | Keywords 110/120, majority 40/120 | Learned classifier 70/120; negative result |
| Routing: 200 simulated tasks | Cheap 149/200 at 200 units; strong 191/200 at 1000 units | Heuristic 184/200 at 572 units |

The complete local experiment package contains the generator and raw evidence; the present branch is the core software preview. All five experiment outcomes were reproduced locally on 25 November 2026 (Python 3.13.5, scikit-learn 1.8.0, seed 20261125). Runtime timing varies. No real API calls. Synthetic labels and intentionally simple baselines do not establish real-world security, savings or novelty.
Prior art: [LMQL](https://lmql.ai/docs/language/reference.html), [OPA](https://www.openpolicyagent.org/docs/agent-tool-calling), [AgentDojo integration](https://github.com/microsoft/agent-governance-toolkit/blob/main/policy-engine/benchmarks/agentdojo/README.md), [LongLLMLingua](https://arxiv.org/abs/2310.06839), [LongMemEval](https://github.com/xiaowu0162/LongMemEval), [RouteLLM](https://arxiv.org/abs/2406.18665). No direct empirical comparisons with these systems yet.
