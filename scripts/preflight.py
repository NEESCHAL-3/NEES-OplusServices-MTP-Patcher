#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import sys

jar = Path(sys.argv[1])
try:
    with ZipFile(jar) as z:
        names = set(z.namelist())
except BadZipFile:
    raise SystemExit("ERROR: input is not a valid zip/jar")

required = {"classes.dex", "classes2.dex"}
missing = sorted(required - names)
if missing:
    raise SystemExit(f"ERROR: missing required dex entries: {missing}")

print("PREFLIGHT_OK")
print("Dex entries:", ", ".join(x for x in ("classes.dex","classes2.dex","classes3.dex","classes4.dex") if x in names))
