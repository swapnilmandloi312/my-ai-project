"""Experimental MCP stdio server for synthetic invoice data only."""
import json
from mcp.server.fastmcp import FastMCP
from integrations.pilot import InvoicePilot
mcp=FastMCP("Swapnil AI Labs read-only pilot")
@mcp.tool()
def lookup_invoice(invoice_id: str, tenant: str="demo") -> dict:
    """Look up a synthetic invoice; only the demo tenant is authorized."""
    pilot=InvoicePilot()
    try: return pilot.propose(json.dumps({"action":"lookup_invoice","args":{"tenant":tenant,"invoice_id":invoice_id}}))
    finally: pilot.close()
if __name__=='__main__': mcp.run(transport='stdio')
