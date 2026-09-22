# Technical notes

## Original failure

On the tested port, the device could establish a real PC/MTP connection while the Oplus battery UI broadcasts still exposed the connection as AC (`chargeplugged = 1`). Oplus SystemUI uses that UI-facing value when deciding whether its USB service considers the device USB-connected.

The important distinction is that the patch does **not** rewrite the real internal battery plug type. It only changes the value written into the two Oplus UI battery intents when the existing Oplus USB-state logic has already confirmed a real configured data connection.

## Stock signal used

The patch hooks the existing `OplusUsbDeviceFeature` USB-state receiver. That receiver already computes the stock Oplus USB status from the framework USB-state broadcast.

The relevant state is effectively:

```text
connected && configured
```

When that stock state becomes true, the patch calls:

```text
OplusBatteryService.neesUsbStateChanged(true)
```

When the receiver is in a host-connected path, the patch clears the data-device state.

## Battery-service side

The patch stores:

```text
sNeesUsbDataConnected
sNeesInstance
```

The final V9 correction stores the long-lived `OplusBatteryService` instance from its constructor rather than relying on `onStart()`.

For the two Oplus UI-facing `chargeplugged` extras only:

```text
real mPlugType != 1
    -> leave unchanged

real mPlugType == 1 and sNeesUsbDataConnected == false
    -> UI remains 1 (AC)

real mPlugType == 1 and sNeesUsbDataConnected == true
    -> UI becomes 2 (USB)
```

The patch then immediately refreshes:

```text
android.intent.action.UI_BATTERY_CHANGED
android.intent.action.ADDITIONAL_BATTERY_CHANGED
```

through the existing private OplusBatteryService send methods.

## Why this solved both tested symptoms

### PC

A real PC data connection reaches the stock Oplus `connected && configured` state. The patch therefore promotes only the UI-facing plug type to USB and SystemUI's native USB service sees the connection.

### Wall charger

A normal wall charger does not become a configured USB data-device connection in this stock Oplus path, so the promotion never occurs. The UI battery state stays AC.

## What is intentionally untouched

- real `mPlugType`
- charging HAL logic
- SystemUI APK
- `services.jar`
- `framework.jar`
- Settings APK
- protected later DEX files
- wired reverse-charging feature declaration

## Known verified hashes

Tested input:

```text
22f99bfdc5e9c1cab73c92ce787944c93f511e4637022c1e7a229b77d1ec3c9b
```

Historical device-tested V9 output:

```text
7df50700f7460970f434954d67b832774c38fecd66a3696eaedcdb039d9999fe
```

Binary rebuild hashes can differ across smali/baksmali toolchains even when post-disassembly smali is identical. For this reason the repository treats exact semantic-smali comparison against a locally owned proven reference as stronger than a rebuilt JAR binary hash alone.
