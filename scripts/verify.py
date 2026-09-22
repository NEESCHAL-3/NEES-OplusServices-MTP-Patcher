#!/usr/bin/env python3
from zipfile import ZipFile, BadZipFile
from pathlib import Path
import hashlib
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: verify.py original.jar patched.jar")

orig = Path(sys.argv[1])
out = Path(sys.argv[2])

try:
    with ZipFile(orig) as a, ZipFile(out) as b:
        an = a.namelist()
        bn = b.namelist()
        if an != bn:
            raise SystemExit("ERROR: jar entry list/order changed")

        changed = []
        for n in an:
            ha = hashlib.sha256(a.read(n)).digest()
            hb = hashlib.sha256(b.read(n)).digest()
            if ha != hb:
                changed.append(n)

        print("CHANGED_ENTRIES =", changed)
        if changed != ["classes.dex", "classes2.dex"]:
            raise SystemExit("ERROR: expected only classes.dex and classes2.dex to change")

        for dex in ("classes3.dex", "classes4.dex"):
            if dex in an:
                if a.read(dex) != b.read(dex):
                    raise SystemExit(f"ERROR: protected {dex} changed")
                print(f"{dex} EXACT")
except BadZipFile:
    raise SystemExit("ERROR: output is not a valid jar")

print("VERIFY_OK")
