# Evidence and reproduction
Raw fixture outputs for the five local synthetic experiments are published in raw-results.jsonl (1,344 lines). The generator is in the earlier downloadable launch package; these rows are not independent evaluation data. The core gateway is separately tested in GitHub Actions.

## Next comparison: Open Policy Agent
Use Rego v1 to encode identical tenant, action, exact argument, step, budget and host-approval policies. Compare both on held-out labelled fixtures. Measure policy-only latency separately from transport and database latency. Approval-token issuance, replay and evidence trust must be provided by the same trusted host in both arms. No OPA executable was available in the current environment; do not claim any measured OPA result. Official docs: https://www.openpolicyagent.org/docs/policy-testing

## Pilot
Run python -m unittest discover -v -s tests. The new finance pilot uses a real in-memory SQLite database with synthetic invoices, parameterized lookup, read-only DB mode and a mocked HTTP model transport. It is not an externally validated product. No live LLM run or customer data.
