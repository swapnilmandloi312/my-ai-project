"""Small explicit Work Relay HTTP client; no automatic retries or external actions."""
import json,urllib.request,urllib.error,urllib.parse,math
from secure_service.service import valid_id
class ClientError(Exception):
    def __init__(self,status,reason):self.status=status;self.reason=reason;super().__init__(str(status)+": "+reason)
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
class RelayClient:
    def __init__(self,base_url,token,*,timeout=5):
        u=urllib.parse.urlsplit(base_url)
        if not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in ("","/") or not (u.scheme=="https" or u.scheme=="http" and u.hostname in ("127.0.0.1","::1","localhost")):raise ValueError("HTTPS or loopback HTTP origin required")
        if not isinstance(token,str) or not 32<=len(token)<=256 or not token.isascii() or any(ord(c)<33 or ord(c)>126 for c in token):raise ValueError("invalid token")
        if type(timeout) not in (int,float) or not math.isfinite(timeout) or not .1<=timeout<=60:raise ValueError("invalid timeout")
        self.base=base_url.rstrip("/");self._token=token;self.timeout=timeout
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    def _call(self,path,body=None):
        headers={"Authorization":"Bearer "+self._token,"Accept":"application/json"}
        raw=None
        if body is not None:
            raw=json.dumps(body,allow_nan=False,separators=(",",":")).encode()
            if len(raw)>8192:raise ValueError("request exceeds 8192 bytes")
            headers["Content-Type"]="application/json"
        req=urllib.request.Request(self.base+path,data=raw,headers=headers)
        try:
            with self.opener.open(req,timeout=self.timeout) as response:
                data=response.read(65537)
                if len(data)>65536:raise ClientError(502,"response_too_large")
                return json.loads(data)
        except urllib.error.HTTPError as exc:
            try:reason=json.loads(exc.read(4096)).get("reason","http_error")
            except (ValueError,AttributeError):reason="http_error"
            raise ClientError(exc.code,reason) from None
        except (OSError,ValueError) as exc:raise ClientError(0,"transport_or_decode_failure") from exc
    def get(self,item_id):
        if not valid_id(item_id):raise ValueError("invalid item id")
        return self._call("/v1/relay/items/"+item_id)
    def command(self,command_id,item_id,action,revision,data=None):
        if not valid_id(command_id) or not valid_id(item_id):raise ValueError("invalid identifier")
        return self._call("/v1/relay/commands",{"command_id":command_id,"item_id":item_id,"action":action,"revision":revision,"data":{} if data is None else data})
