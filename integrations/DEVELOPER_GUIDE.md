# Developer integrations — Swapnil AI Labs
All examples use synthetic invoices. Do not expose this unauthenticated local demo or connect it to production.
- Python: `python -m integrations.pilot`
- HTTP: `python -m integrations.http_pilot`, POST /propose on localhost:8765.
- JavaScript: import lookupInvoice from javascript.mjs; Node 18+.
- n8n: import n8n-workflow.json, run on same host/network namespace as local service. Docker/cloud require a different secure connectivity design; do not expose the demo publicly. Workflow structure is tested, n8n application execution is not.
- MCP: `pip install mcp==1.30.0`, then `python -m integrations.mcp_server` using stdio. Only the synthetic lookup tool is exposed.
- CI runs a real HTTP and Node client test and an MCP client/server stdio round trip. Each request creates a fresh synthetic session; budgets are not persistent across calls.
No claims of production readiness, customer data security or compatibility with every client.
