# v1.0.0 — Initial verified release

First public source release of the NEES OplusServices MTP / USB UI patcher.

Highlights:

- Uses the stock `OplusUsbDeviceFeature` configured-data signal.
- Changes only UI-facing Oplus `chargeplugged` values when appropriate.
- Keeps the real internal battery plug type untouched.
- Immediately refreshes the native Oplus battery UI broadcasts.
- Does not patch SystemUI, `services.jar`, `framework.jar`, or Settings.
- Preserves `classes3.dex` and `classes4.dex` byte-for-byte when present.
- Rejects unknown input hashes by default.
- Supports optional exact semantic-smali comparison against a locally supplied known-good V9 JAR.

Known tested input SHA-256:

`22f99bfdc5e9c1cab73c92ce787944c93f511e4637022c1e7a229b77d1ec3c9b`

Historical device-tested V9 SHA-256:

`7df50700f7460970f434954d67b832774c38fecd66a3696eaedcdb039d9999fe`

No proprietary Oplus/ColorOS binaries are included in this release.
