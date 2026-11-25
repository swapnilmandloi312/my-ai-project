"""Bounded local provider transport for trusted POSIX workers; not an OS security sandbox."""
from pathlib import Path
import json,math,os,selectors,signal,subprocess,tempfile,time

class ProviderError(Exception):
    reason="provider_worker_failure"
class ProviderTimeout(ProviderError):
    reason="provider_timeout"
class ProviderOutputLimit(ProviderError):
    reason="provider_output_limit"

class IsolatedJSONProvider:
    """Fixed host configuration, one process per request. stdout is the proposal only.

    Worker receives JSON on stdin and returns UTF-8 JSON on stdout. No inherited
    environment, shell, stderr logging or caller-controlled command line. A trusted
    worker still has the host's filesystem/network privileges; deploy it under
    separate OS identity/container controls for untrusted code or sensitive data.
    """
    def __init__(self,argv,*,cwd,timeout=10.0,max_bytes=4096):
        if os.name!="posix":raise ValueError("POSIX worker required")
        if not isinstance(argv,(tuple,list)) or not argv or not all(type(s) is str and s and "\x00" not in s for s in argv):raise ValueError("invalid command")
        if not Path(argv[0]).is_absolute() or not Path(argv[0]).is_file():raise ValueError("absolute executable required")
        if not Path(cwd).is_absolute() or not Path(cwd).is_dir():raise ValueError("absolute working directory required")
        if type(timeout) not in (int,float) or not math.isfinite(timeout) or not .05<=timeout<=120:raise ValueError("invalid timeout")
        if type(max_bytes) is not int or not 1<=max_bytes<=4096:raise ValueError("invalid output limit")
        self.argv=tuple(argv);self.cwd=str(cwd);self.timeout=timeout;self.max_bytes=max_bytes
    def __call__(self,expected,intent):
        payload=json.dumps({"expected":expected,"intent":intent},ensure_ascii=True,allow_nan=False,separators=(",",":")).encode("utf-8")
        if len(payload)>16000:raise ProviderError("input limit")
        deadline=time.monotonic()+self.timeout
        with tempfile.TemporaryFile(mode="w+b") as source:
            source.write(payload);source.seek(0)
            try:
                proc=subprocess.Popen(self.argv,stdin=source,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,cwd=self.cwd,env={},shell=False,close_fds=True,start_new_session=True)
            except OSError as exc:raise ProviderError("worker unavailable") from exc
            try:
                data=bytearray()
                with selectors.DefaultSelector() as sel:
                    os.set_blocking(proc.stdout.fileno(),False)
                    sel.register(proc.stdout,selectors.EVENT_READ)
                    while True:
                        remaining=deadline-time.monotonic()
                        if remaining<=0 or not sel.select(remaining):raise ProviderTimeout()
                        try:chunk=os.read(proc.stdout.fileno(),min(4096,self.max_bytes+1-len(data)))
                        except BlockingIOError:continue
                        if not chunk:break
                        data.extend(chunk)
                        if len(data)>self.max_bytes:raise ProviderOutputLimit()
                remaining=deadline-time.monotonic()
                if remaining<=0:raise ProviderTimeout()
                try:code=proc.wait(timeout=remaining)
                except subprocess.TimeoutExpired as exc:raise ProviderTimeout() from exc
                if code!=0:raise ProviderError("worker failed")
                try:return data.decode("utf-8",errors="strict")
                except UnicodeError as exc:raise ProviderError("invalid UTF-8") from exc
            finally:
                # A process group is a lifecycle mechanism, not containment for
                # workers that intentionally escape the group.
                try:os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                proc.stdout.close()
                proc.wait()
