"""Hash committed evidence, code and contract schema with the tested Git revision."""
import hashlib,json,platform,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
paths=["research/raw-results.jsonl","research/REPORT.md","research/opa_compare.py","research/real_model_eval.py","intelligence/benchmark.py","schemas/proposal-v1.json","swapnil_ai_labs/platform.py","swapnil_ai_labs/contracts.py"]
files=[]
for name in paths:
    data=(ROOT/name).read_bytes();files.append({"path":name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
manifest={"schema_version":"1.0","commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"python":platform.python_version(),"scope":"integrity inventory of repository files; hashes are not independent validation, signatures or proof of novelty","files":files}
(ROOT/"evidence-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
print(f"Manifest created for {len(files)} files at {manifest['commit']}")
