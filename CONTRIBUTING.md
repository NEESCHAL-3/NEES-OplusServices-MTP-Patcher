# Contributing

Contributions are welcome, especially compatibility reports for additional Oplus/ColorOS builds.

## Before opening a pull request

1. Do not include proprietary JARs, APKs, DEX files, firmware images, or extracted vendor files.
2. Keep the default path fail-closed for unknown inputs.
3. Preserve the existing protected-DEX verification.
4. Run the repository checks locally:

```bash
bash -n patch.sh
python3 -m py_compile scripts/*.py
```

5. If changing patch logic, describe:
   - the input build/device tested;
   - the exact behavior before/after;
   - which classes/methods are modified;
   - whether a semantic comparison against a known-good local reference was performed.

## Compatibility reports

Please include hashes and textual logs, not proprietary binaries.
