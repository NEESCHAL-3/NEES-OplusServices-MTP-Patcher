# NEES OplusServices MTP / USB UI Patcher

[![Repo checks](https://github.com/NEESCHAL-3/NEES-OplusServices-MTP-Patcher/actions/workflows/repo-checks.yml/badge.svg)](https://github.com/NEESCHAL-3/NEES-OplusServices-MTP-Patcher/actions/workflows/repo-checks.yml)
![Platform](https://img.shields.io/badge/platform-Android-green)
![Target](https://img.shields.io/badge/target-oplus--services.jar-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A source-only patcher for a specific compatible `oplus-services.jar` that fixes the native ColorOS/Oplus MTP / USB UI path on a tested POCO X7 Pro (`rodin`) ColorOS port.

The patch makes a real configured PC data connection appear as USB to the **UI-facing Oplus battery broadcasts** while keeping normal wall charging classified as AC. It does **not** change the real internal battery plug type.

> [!IMPORTANT]
> This is **not a universal ColorOS patcher**. The only fully verified input is the exact JAR SHA-256 listed below. Unknown builds are rejected by default.

## What it fixes

On the tested ROM, MTP itself worked, but the native Oplus USB notification/dialog could disappear because SystemUI received `chargeplugged = 1` (AC) even when the phone was connected to a PC as a data device.

This patch hooks the existing Oplus USB-state path and changes only the UI-facing value when the stock Oplus USB state reports a configured data connection.

### Result on the tested build

- PC data connection: native USB/MTP notification and dialog work.
- Repeated unplug/replug: works consistently.
- Wall charger: remains AC and does not trigger the bogus USB/reverse popup observed before the fix.
- 90 W charging path remains intact on the tested build.

## Design

The proven patch flow is:

```text
OplusUsbDeviceFeature stock USB-state receiver
        |
        | connected && configured
        v
OplusBatteryService.neesUsbStateChanged(true)
        |
        v
UI-only chargeplugged: 1 (AC) -> 2 (USB)
        |
        v
Immediate Oplus battery UI broadcast refresh
        |
        v
Native ColorOS/Oplus USB UI sees a real USB connection
```

The patch intentionally does **not** use:

- SystemUI modifications
- `services.jar` modifications
- `framework.jar` modifications
- Settings APK modifications
- sysfs polling
- `UsbManager.getPorts()` polling
- delayed timer retries
- permanent root-module runtime hooks

The actual internal `mPlugType` remains unchanged.

## Tested input

Known tested input SHA-256:

```text
22f99bfdc5e9c1cab73c92ce787944c93f511e4637022c1e7a229b77d1ec3c9b
```

Historical proven device-tested V9 JAR SHA-256:

```text
7df50700f7460970f434954d67b832774c38fecd66a3696eaedcdb039d9999fe
```

A locally rebuilt output can have a different binary SHA because smali/baksmali may emit semantically identical DEX files with different binary ordering/layout. The patcher therefore validates structural invariants and optionally performs an exact post-disassembly semantic comparison against a locally supplied proven V9 JAR.

## Requirements

Linux / WSL with:

```text
bash
python3
unzip
sha256sum
smali
baksmali
```

Check the tools first:

```bash
python3 --version
smali --version
baksmali --version
```

## Usage

Clone the repo:

```bash
git clone https://github.com/NEESCHAL-3/NEES-OplusServices-MTP-Patcher.git
cd NEES-OplusServices-MTP-Patcher
```

Place your original file at:

```text
input/oplus-services.jar
```

Then run:

```bash
chmod +x patch.sh
./patch.sh
```

Output:

```text
output/oplus-services-patched.jar
output/SHA256.txt
output/PATCH-INFO.txt
```

## Strongest local verification

If you personally own the already device-tested V9 JAR, place it at:

```text
reference/oplus-services-proven-v9.jar
```

Then run:

```bash
./patch.sh
```

For the tested base, the strongest successful result is:

```text
classes.dex SEMANTIC_SMALI_EXACT
classes2.dex SEMANTIC_SMALI_EXACT
SEMANTIC_REFERENCE_MATCH_OK
```

The reference JAR is deliberately ignored by Git and is **not distributed by this repository**.

## Experimental use on another build

By default an unknown input hash is rejected. To deliberately test another compatible build:

```bash
ALLOW_UNTESTED=1 ./patch.sh
```

This only bypasses the known-input SHA gate. Exact smali anchors and structural validation still have to pass.

> [!WARNING]
> `ALLOW_UNTESTED=1` does not mean the output is known safe for your ROM. Back up the original JAR and test carefully. A framework JAR mismatch can cause boot failure or system-server instability.

## Verification performed by the patcher

The patcher checks that:

- the input is a valid JAR/ZIP;
- `classes.dex` and `classes2.dex` exist;
- exact expected smali anchors exist before patching;
- only `classes.dex` and `classes2.dex` change;
- `classes3.dex` and `classes4.dex` remain byte-for-byte unchanged when present;
- the final JAR remains readable;
- an optional local proven-V9 comparison produces identical disassembled smali for target DEX files.

## Why there are two patch stages

The final tested fix evolved through a V8 -> V9 correction. The patcher intentionally reproduces that source transformation in two stages so the public patch source follows the same logic that was device-tested.

See [docs/TECHNICAL.md](docs/TECHNICAL.md) for the technical explanation.

## Repository policy

This repository contains **patching source only**. It does not distribute Oplus/ColorOS proprietary framework JARs.

Do not commit:

- `input/oplus-services.jar`
- generated output JARs
- the local proven reference JAR
- extracted DEX files

## License

The patcher source is released under the [MIT License](LICENSE).

Android, ColorOS, Oplus/OPPO, POCO, Xiaomi and other names/trademarks belong to their respective owners. This project is an independent community modification and is not affiliated with or endorsed by those companies.
