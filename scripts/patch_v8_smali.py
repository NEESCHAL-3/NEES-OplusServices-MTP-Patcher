#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_v8_smali.py OplusBatteryService.smali OplusUsbDeviceFeature$1.smali")

bp = Path(sys.argv[1])
up = Path(sys.argv[2])
bs = bp.read_text()
us = up.read_text()

for marker in (
    "sNeesUsbDataConnected",
    "sNeesInstance",
    "neesUsbStateChanged",
    "UI plug AC->USB: stock Oplus USB_STATE=true",
):
    if marker in bs:
        raise SystemExit(f"ERROR: BatteryService already appears patched ({marker})")
if "->neesUsbStateChanged(Z)V" in us:
    raise SystemExit("ERROR: OplusUsbDeviceFeature receiver already appears patched")

# Exact historical V8 stage.
anchor = "# static fields\n"
assert bs.count(anchor) == 1
bs = bs.replace(
    anchor,
    anchor
    + ".field private static volatile sNeesUsbDataConnected:Z\n\n"
    + ".field private static volatile sNeesInstance:Lcom/android/server/OplusBatteryService;\n\n",
    1,
)

old = '''    const-string v1, "chargeplugged"

    iget v2, p0, Lcom/android/server/OplusBatteryService;->mPlugType:I

    invoke-virtual {v0, v1, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;
'''
new = '''    const-string v1, "chargeplugged"

    invoke-direct {p0}, Lcom/android/server/OplusBatteryService;->neesGetUiPlugType()I

    move-result v2

    invoke-virtual {v0, v1, v2}, Landroid/content/Intent;->putExtra(Ljava/lang/String;I)Landroid/content/Intent;
'''
count = bs.count(old)
if count != 2:
    raise SystemExit(f"ERROR: expected exactly 2 raw chargeplugged blocks, found {count}")
bs = bs.replace(old, new)

# IMPORTANT: V8 originally saved the instance in onStart().
needle = '''.method public onStart()V
    .registers 4

'''
replace = '''.method public onStart()V
    .registers 4

    sput-object p0, Lcom/android/server/OplusBatteryService;->sNeesInstance:Lcom/android/server/OplusBatteryService;

'''
if bs.count(needle) != 1:
    raise SystemExit(f"ERROR: expected one onStart anchor, found {bs.count(needle)}")
bs = bs.replace(needle, replace, 1)

helpers = r'''

.method private neesGetUiPlugType()I
    .registers 4

    iget v0, p0, Lcom/android/server/OplusBatteryService;->mPlugType:I

    const/4 v1, 0x1

    if-ne v0, v1, :nees_ui_return

    sget-boolean v1, Lcom/android/server/OplusBatteryService;->sNeesUsbDataConnected:Z

    if-eqz v1, :nees_ui_return

    const/4 v0, 0x2

    const-string v1, "NeesUsb"

    const-string v2, "UI plug AC->USB: stock Oplus USB_STATE=true"

    invoke-static {v1, v2}, Landroid/util/Slog;->i(Ljava/lang/String;Ljava/lang/String;)I

    :nees_ui_return
    return v0
.end method


.method public static neesUsbStateChanged(Z)V
    .registers 4

    sput-boolean p0, Lcom/android/server/OplusBatteryService;->sNeesUsbDataConnected:Z

    if-eqz p0, :nees_usb_callback_return

    const-string v0, "NeesUsb"

    const-string v1, "OplusUsbDeviceFeature callback: DATA READY"

    invoke-static {v0, v1}, Landroid/util/Slog;->i(Ljava/lang/String;Ljava/lang/String;)I

    sget-object v0, Lcom/android/server/OplusBatteryService;->sNeesInstance:Lcom/android/server/OplusBatteryService;

    if-eqz v0, :nees_usb_callback_return

    invoke-direct {v0}, Lcom/android/server/OplusBatteryService;->neesRefreshUsbUi()V

    :nees_usb_callback_return
    return-void
.end method


.method private neesRefreshUsbUi()V
    .registers 4

    invoke-direct {p0}, Lcom/android/server/OplusBatteryService;->neesGetUiPlugType()I

    move-result v0

    const/4 v1, 0x2

    if-ne v0, v1, :nees_refresh_return

    const-string v0, "NeesUsb"

    const-string v1, "Oplus USB ready -> immediate battery UI refresh"

    invoke-static {v0, v1}, Landroid/util/Slog;->i(Ljava/lang/String;Ljava/lang/String;)I

    invoke-direct {p0}, Lcom/android/server/OplusBatteryService;->sendUiBatteryIntentLocked()V

    invoke-direct {p0}, Lcom/android/server/OplusBatteryService;->sendAdditionalIntentLocked()V

    :nees_refresh_return
    return-void
.end method
'''
bs = bs.rstrip() + helpers + "\n"

needle = '''    invoke-static {v5, v1}, Lcom/android/server/usb/OplusUsbDeviceFeature;->-$$Nest$fputmUsbstatus(Lcom/android/server/usb/OplusUsbDeviceFeature;Z)V
'''
replacement = needle + '''
    invoke-static {v1}, Lcom/android/server/OplusBatteryService;->neesUsbStateChanged(Z)V
'''
if us.count(needle) != 1:
    raise SystemExit(f"ERROR: expected one mUsbstatus write, found {us.count(needle)}")
us = us.replace(needle, replacement, 1)

host = '''    const-string v0, "host_connected"

    invoke-virtual {p2, v0, v3}, Landroid/content/Intent;->getBooleanExtra(Ljava/lang/String;Z)Z

    move-result v0

    if-nez v0, :cond_51
'''
host_new = '''    const-string v0, "host_connected"

    invoke-virtual {p2, v0, v3}, Landroid/content/Intent;->getBooleanExtra(Ljava/lang/String;Z)Z

    move-result v0

    if-eqz v0, :nees_not_host

    invoke-static {v3}, Lcom/android/server/OplusBatteryService;->neesUsbStateChanged(Z)V

    :nees_not_host
    if-nez v0, :cond_51
'''
if us.count(host) != 1:
    raise SystemExit(f"ERROR: expected one host_connected block, found {us.count(host)}")
us = us.replace(host, host_new, 1)

assert bs.count(".method private neesGetUiPlugType()I") == 1
assert bs.count(".method private neesRefreshUsbUi()V") == 1
assert bs.count(".method public static neesUsbStateChanged(Z)V") == 1
assert bs.count("->neesGetUiPlugType()I") == 3
assert us.count("->neesUsbStateChanged(Z)V") == 2

bp.write_text(bs)
up.write_text(us)
print("V8_STAGE_PATCH_OK")
