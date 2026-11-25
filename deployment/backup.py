"""Consistent SQLite backup; restore and HMAC audit verification are separate checks."""
import sqlite3,sys
from pathlib import Path
from contextlib import closing
def backup(source,dest):
    a,b=Path(source).resolve(),Path(dest).resolve()
    if not a.is_file() or b.exists() or a==b:raise ValueError("source must exist, destination must be new")
    with closing(sqlite3.connect(a.as_uri()+"?mode=ro",uri=True)) as src, closing(sqlite3.connect(b)) as dst:
        src.backup(dst)
        if dst.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise RuntimeError("backup integrity check failed")
    print("SQLite backup and integrity check passed")
if __name__=="__main__":backup(sys.argv[1],sys.argv[2])
