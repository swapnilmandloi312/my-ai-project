import asyncio, sys, json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
    params=StdioServerParameters(command=sys.executable,args=["-m","integrations.mcp_server"])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            tools=await session.list_tools()
            assert any(t.name=='lookup_invoice' for t in tools.tools)
            for tenant,expected in [('demo','executed_read_only'),('other','blocked')]:
                result=await session.call_tool('lookup_invoice',{'invoice_id':'INV-001','tenant':tenant})
                assert not result.isError
                payload=result.structuredContent or json.loads(result.content[0].text)
                assert payload['status']==expected,payload
                print(tenant,expected)
asyncio.run(main())
