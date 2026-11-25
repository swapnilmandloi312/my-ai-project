"""Build only public static assets. No secrets, model artifacts or test files."""
from pathlib import Path
import shutil,sys
ROOT=Path(__file__).resolve().parents[1]
FILES=("index.html","research.css","playground.html","playground.js","apps/index.html","apps/tools.html","apps/app.mjs","apps/catalog.mjs","apps/engine.mjs","apps/experience.css","apps/experience.mjs","apps/journeys.mjs","apps/style.css","apps/pwa.mjs","apps/sw.js","apps/manifest.webmanifest","apps/icon-192.png","apps/icon-512.png")
out=ROOT/"dist-public"
if out.is_symlink():raise RuntimeError("Refuse symlink output")
if out.exists():shutil.rmtree(out)
out.mkdir()
for name in FILES:
    src=ROOT/"website"/name;dest=out/name
    if not src.is_file() or src.is_symlink():raise RuntimeError("Missing or invalid public asset: "+name)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
for name in ("LICENSE","THIRD_PARTY_NOTICES.md"):shutil.copyfile(ROOT/name,out/name)
print("Built",len(FILES)+2,"allowlisted public files in dist-public")
