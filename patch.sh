#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="$ROOT/input/oplus-services.jar"
REFERENCE="$ROOT/reference/oplus-services-proven-v9.jar"
OUTPUT_DIR="$ROOT/output"
OUTPUT="$OUTPUT_DIR/oplus-services-patched.jar"
WORK="$ROOT/.work"

TESTED_BASE_SHA256="22f99bfdc5e9c1cab73c92ce787944c93f511e4637022c1e7a229b77d1ec3c9b"
REFERENCE_V8_SHA256="b447d51e4ae7be3325d48537e690ce519334dbfbcc619cc9f51a9dde096a787e"
REFERENCE_V9_SHA256="7df50700f7460970f434954d67b832774c38fecd66a3696eaedcdb039d9999fe"

BAKSMALI="${BAKSMALI:-baksmali}"
SMALI="${SMALI:-smali}"
ALLOW_UNTESTED="${ALLOW_UNTESTED:-0}"

need() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "ERROR: '$1' not found in PATH" >&2
        exit 1
    }
}

for x in python3 unzip sha256sum "$BAKSMALI" "$SMALI"; do
    need "$x"
done

[[ -f "$INPUT" ]] || {
    echo "ERROR: missing input/oplus-services.jar" >&2
    exit 1
}

mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT" "$OUTPUT_DIR/SHA256.txt" "$OUTPUT_DIR/PATCH-INFO.txt"
rm -rf "$WORK"
mkdir -p "$WORK/v8-smali1" "$WORK/v8-smali2" "$WORK/v9-smali1"

INPUT_SHA="$(sha256sum "$INPUT" | awk '{print $1}')"

echo "===== INPUT ====="
echo "SHA256: $INPUT_SHA"

if [[ "$INPUT_SHA" != "$TESTED_BASE_SHA256" ]]; then
    echo "WARNING: input is not the tested base: $TESTED_BASE_SHA256"
    if [[ "$ALLOW_UNTESTED" != 1 ]]; then
        echo "Refusing. Use ALLOW_UNTESTED=1 only deliberately."
        exit 2
    fi
fi

python3 "$ROOT/scripts/preflight.py" "$INPUT"

# ------------------------------------------------------------
# Stage 1: historical V8 source transformation.
# IMPORTANT: DEX/JAR byte hashes can vary between smali builds
# even when the disassembled smali is identical. Therefore V8
# reference SHA is informational, not a hard success condition.
# ------------------------------------------------------------

echo "===== STAGE 1: BUILD V8 LOGIC ====="
unzip -p "$INPUT" classes.dex > "$WORK/v8-classes.dex.before"
unzip -p "$INPUT" classes2.dex > "$WORK/v8-classes2.dex.before"

"$BAKSMALI" d "$WORK/v8-classes.dex.before" -o "$WORK/v8-smali1"
"$BAKSMALI" d "$WORK/v8-classes2.dex.before" -o "$WORK/v8-smali2"

python3 "$ROOT/scripts/patch_v8_smali.py" \
    "$WORK/v8-smali1/com/android/server/OplusBatteryService.smali" \
    "$WORK/v8-smali2/com/android/server/usb/OplusUsbDeviceFeature\$1.smali"

"$SMALI" a "$WORK/v8-smali1" -o "$WORK/v8-classes.dex.after"
"$SMALI" a "$WORK/v8-smali2" -o "$WORK/v8-classes2.dex.after"

python3 "$ROOT/scripts/repack.py" \
    "$INPUT" "$WORK/v8.jar" \
    "$WORK/v8-classes.dex.after" "$WORK/v8-classes2.dex.after"

V8_SHA="$(sha256sum "$WORK/v8.jar" | awk '{print $1}')"
echo "V8 SHA256:       $V8_SHA"
echo "Historical V8:   $REFERENCE_V8_SHA256"
if [[ "$V8_SHA" == "$REFERENCE_V8_SHA256" ]]; then
    echo "V8_BINARY_REFERENCE_MATCH"
else
    echo "NOTE: V8 binary hash differs. This alone is NOT treated as a patch failure."
fi

# ------------------------------------------------------------
# Stage 2: historical V9 constructor-instance correction.
# ------------------------------------------------------------

echo "===== STAGE 2: V8 -> V9 INSTANCE FIX ====="
unzip -p "$WORK/v8.jar" classes.dex > "$WORK/v9-classes.dex.before"
"$BAKSMALI" d "$WORK/v9-classes.dex.before" -o "$WORK/v9-smali1"
python3 "$ROOT/scripts/patch_v9_instance.py" \
    "$WORK/v9-smali1/com/android/server/OplusBatteryService.smali"
"$SMALI" a "$WORK/v9-smali1" -o "$WORK/v9-classes.dex.after"
python3 "$ROOT/scripts/repack_one.py" \
    "$WORK/v8.jar" "$OUTPUT" "$WORK/v9-classes.dex.after"

# Core invariants: only target DEX entries changed; protected DEX unchanged.
python3 "$ROOT/scripts/verify.py" "$INPUT" "$OUTPUT"

OUTPUT_SHA="$(sha256sum "$OUTPUT" | awk '{print $1}')"
printf '%s  %s\n' "$OUTPUT_SHA" "oplus-services-patched.jar" > "$OUTPUT_DIR/SHA256.txt"

echo "===== OUTPUT ====="
echo "SHA256:          $OUTPUT_SHA"
echo "Historical V9:   $REFERENCE_V9_SHA256"

BINARY_STATUS="DIFFERS_FROM_HISTORICAL_V9"
if [[ "$OUTPUT_SHA" == "$REFERENCE_V9_SHA256" ]]; then
    BINARY_STATUS="BYTE_FOR_BYTE_HISTORICAL_V9"
    echo "BYTE_FOR_BYTE_HISTORICAL_V9"
else
    echo "NOTE: output binary hash differs from historical V9."
    echo "      This can be caused by DEX layout/order from smali assembly."
fi

SEMANTIC_STATUS="NOT_RUN"
if [[ -f "$REFERENCE" ]]; then
    echo "===== LOCAL PROVEN-V9 SEMANTIC COMPARISON ====="
    REF_SHA="$(sha256sum "$REFERENCE" | awk '{print $1}')"
    echo "Reference file SHA256: $REF_SHA"
    if [[ "$REF_SHA" != "$REFERENCE_V9_SHA256" ]]; then
        echo "ERROR: reference/oplus-services-proven-v9.jar is not the expected proven V9."
        exit 5
    fi
    python3 "$ROOT/scripts/semantic_compare.py" "$OUTPUT" "$REFERENCE" "$BAKSMALI"
    SEMANTIC_STATUS="SEMANTIC_REFERENCE_MATCH_OK"
else
    echo "===== REFERENCE CHECK SKIPPED ====="
    echo "For the strongest local test, copy your proven V9 to:"
    echo "  reference/oplus-services-proven-v9.jar"
    echo "and run ./patch.sh again."
fi

cat > "$OUTPUT_DIR/PATCH-INFO.txt" <<EOF
NEES OplusServices MTP / USB UI patcher v3
Input SHA256:          $INPUT_SHA
Intermediate V8 SHA:   $V8_SHA
Output SHA256:         $OUTPUT_SHA
Historical V8 SHA:     $REFERENCE_V8_SHA256
Historical V9 SHA:     $REFERENCE_V9_SHA256
Binary status:         $BINARY_STATUS
Semantic ref status:   $SEMANTIC_STATUS
Protected DEX:         classes3.dex/classes4.dex exact when present
EOF

echo "===== DONE ====="
echo "Output: $OUTPUT"
echo "Structural verification: PASS"
echo "Binary status: $BINARY_STATUS"
echo "Semantic reference status: $SEMANTIC_STATUS"

if [[ "$INPUT_SHA" == "$TESTED_BASE_SHA256" && "$SEMANTIC_STATUS" == "NOT_RUN" && "$BINARY_STATUS" != "BYTE_FOR_BYTE_HISTORICAL_V9" ]]; then
    echo
    echo "IMPORTANT: tested-base output is structurally correct but not byte-identical."
    echo "Do NOT call it proven V9 until either:"
    echo "  1) local semantic comparison against the proven V9 passes, or"
    echo "  2) you device-test this generated output."
fi
