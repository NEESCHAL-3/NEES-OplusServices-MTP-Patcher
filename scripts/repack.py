#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile
import sys

if len(sys.argv) != 5:
    raise SystemExit("usage: repack.py input.jar output.jar classes.dex classes2.dex")

src = Path(sys.argv[1])
out = Path(sys.argv[2])
repl = {
    "classes.dex": Path(sys.argv[3]).read_bytes(),
    "classes2.dex": Path(sys.argv[4]).read_bytes(),
}

if out.exists():
    out.unlink()

with ZipFile(src, "r") as zin, ZipFile(out, "w") as zout:
    for info in zin.infolist():
        data = repl.get(info.filename, zin.read(info.filename))
        zout.writestr(info, data)

print("REPACK_OK")
