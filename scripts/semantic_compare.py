#!/usr/bin/env python3
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

if len(sys.argv) != 4:
    raise SystemExit("usage: semantic_compare.py generated.jar reference.jar baksmali_cmd")

generated = Path(sys.argv[1]).resolve()
reference = Path(sys.argv[2]).resolve()
baksmali = sys.argv[3]

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def read_entry(jar: Path, name: str) -> bytes:
    try:
        with ZipFile(jar) as z:
            return z.read(name)
    except (BadZipFile, KeyError) as e:
        raise SystemExit(f"ERROR: cannot read {name} from {jar}: {e}")

def file_map(root: Path):
    out = {}
    for p in sorted(root.rglob('*.smali')):
        rel = p.relative_to(root).as_posix()
        out[rel] = p.read_bytes()
    return out

with tempfile.TemporaryDirectory(prefix='nees-semantic-') as td:
    td = Path(td)
    for label, jar in (("generated", generated), ("reference", reference)):
        for dex in ("classes.dex", "classes2.dex"):
            dex_path = td / f"{label}-{dex}"
            dex_path.write_bytes(read_entry(jar, dex))
            out_dir = td / f"{label}-{dex}.smali"
            subprocess.run([baksmali, 'd', str(dex_path), '-o', str(out_dir)], check=True)

    for dex in ("classes.dex", "classes2.dex"):
        aroot = td / f"generated-{dex}.smali"
        broot = td / f"reference-{dex}.smali"
        a = file_map(aroot)
        b = file_map(broot)
        if set(a) != set(b):
            only_a = sorted(set(a) - set(b))[:20]
            only_b = sorted(set(b) - set(a))[:20]
            print(f"ERROR: {dex} smali file set differs")
            if only_a: print("Only generated:", *only_a, sep='\n  ')
            if only_b: print("Only reference:", *only_b, sep='\n  ')
            raise SystemExit(10)
        diffs = [k for k in a if a[k] != b[k]]
        if diffs:
            print(f"ERROR: {dex} semantic smali differs in {len(diffs)} file(s)")
            for k in diffs[:30]:
                print("  ", k)
            raise SystemExit(11)
        print(f"{dex} SEMANTIC_SMALI_EXACT")

print("SEMANTIC_REFERENCE_MATCH_OK")
print("Generated SHA256:", sha256(generated))
print("Reference SHA256:", sha256(reference))
