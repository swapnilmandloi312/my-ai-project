# Integration guide — mock only
A trusted host reads product.agent, creates Gateway.from_contract, and dispatches only predefined mock actions. The model (if added later) proposes actions; the host owns identity, evidence registration and approval tokens. Never expose approve or register_evidence to an untrusted agent.

```python
from pathlib import Path
from gateway import Gateway
g = Gateway.from_contract(Path("product.agent").read_text())
print(g.dispatch("lookup_invoice", {"tenant":"demo","invoice_id":"INV-001"}))
```

Target n8n and MCP integration: insert the gateway between tool proposals and actual API calls; derive tenant identity from authenticated host, not model arguments. A production system needs isolated execution, actual authentication, durable approval expiry/replay protection, audit integrity, metered costs, independently verified evidence and adversarial evaluation. This prototype is not that system.
