"""Opt-in OpenAI-compatible HTTP proposal adapter, no real model verified."""
import json, urllib.request, urllib.parse, os
def propose(prompt, model, base_url='http://127.0.0.1:11434/v1', api_key=None):
    url=urllib.parse.urlparse(base_url)
    if url.scheme not in ('http','https') or url.hostname is None or url.username or url.password or url.query or url.fragment: raise ValueError('invalid endpoint')
    if url.scheme=='http' and url.hostname not in ('127.0.0.1','localhost','::1'): raise ValueError('remote endpoint requires HTTPS')
    data={'model':model,'messages':[{'role':'system','content':'Return only a JSON object with action lookup_invoice and args tenant, invoice_id. Do not invent approvals.'},{'role':'user','content':prompt}],'stream':False}
    headers={'Content-Type':'application/json'}
    if api_key: headers['Authorization']='Bearer '+api_key
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs): return None
    req=urllib.request.Request(base_url.rstrip('/')+'/chat/completions',json.dumps(data).encode(),headers)
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=30) as res:
        body=res.read(262145)
    if len(body)>262144: raise ValueError('oversize response')
    result=json.loads(body)['choices'][0]['message']['content']
    if type(result) is not str: raise ValueError('invalid model output')
    return result
