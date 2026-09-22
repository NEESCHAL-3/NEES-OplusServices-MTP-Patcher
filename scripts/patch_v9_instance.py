#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_v9_instance.py OplusBatteryService.smali")

p = Path(sys.argv[1])
s = p.read_text()
field = "Lcom/android/server/OplusBatteryService;->sNeesInstance:Lcom/android/server/OplusBatteryService;"

# Exact historical V9 delta from V8: remove onStart assignment...
old = f'''.method public onStart()V
    .registers 4

    sput-object p0, {field}

'''
new = '''.method public onStart()V
    .registers 4

'''
if s.count(old) != 1:
    raise SystemExit(f"ERROR: expected exact V8 onStart assignment once, found {s.count(old)}")
s = s.replace(old, new, 1)

# ...and place it after Object.<init>() in constructor.
ctor = '''.method public constructor <init>(Landroid/content/Context;Landroid/app/ActivityManagerInternal;)V
    .registers 8
'''
if s.count(ctor) != 1:
    raise SystemExit(f"ERROR: expected target constructor once, found {s.count(ctor)}")
obj_init = '''    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
'''
if s.count(obj_init) != 1:
    raise SystemExit(f"ERROR: Object.<init> anchor is not unique ({s.count(obj_init)})")
s = s.replace(obj_init, obj_init + f'''\n    sput-object p0, {field}\n''', 1)

assignment = f"sput-object p0, {field}"
if s.count(assignment) != 1:
    raise SystemExit(f"ERROR: expected exactly one final instance assignment, found {s.count(assignment)}")

for marker in (
    "OplusUsbDeviceFeature callback: DATA READY",
    "Oplus USB ready -> immediate battery UI refresh",
    "UI plug AC->USB: stock Oplus USB_STATE=true",
    "neesUsbStateChanged",
    "sNeesUsbDataConnected",
):
    if marker not in s:
        raise SystemExit(f"ERROR: V8 marker missing before V9 stage: {marker}")

p.write_text(s)
print("V9_INSTANCE_STAGE_OK")
