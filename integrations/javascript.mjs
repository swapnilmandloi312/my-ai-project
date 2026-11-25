// Node 18+ loopback-only synthetic pilot client; not a production SDK.
export async function lookupInvoice(invoiceId, {tenant="demo", port=8765}={}) {
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error("Invalid port");
  const response=await fetch("http://127.0.0.1:"+port+"/propose", {
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({action:"lookup_invoice",args:{tenant,invoice_id:invoiceId}}),
    signal:AbortSignal.timeout(5000),redirect:"error"
  });
  if(!response.ok) throw new Error("Pilot HTTP error "+response.status);
  return await response.json();
}
