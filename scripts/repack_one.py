#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile
import sys
if len(sys.argv) != 4:
    raise SystemExit("usage: repack_one.py input.jar output.jar classes.dex")
src = Path(sys.argv[1]); out = Path(sys.argv[2]); dex = Path(sys.argv[3]).read_bytes()
if out.exists(): out.unlink()
with ZipFile(src, "r") as zin, ZipFile(out, "w") as zout:
    for info in zin.infolist():
        data = dex if info.filename == "classes.dex" else zin.read(info.filename)
        zout.writestr(info, data)
print("REPACK_ONE_OK")
