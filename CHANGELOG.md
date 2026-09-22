# Changelog

All notable changes to the public patcher source are documented here.

## [1.0.0] - 2026-09-22

### Added
- Public source-only patcher for the verified Oplus MTP / USB UI fix.
- Trusted-input SHA gate.
- Two-stage V8 -> V9 source transformation matching the device-tested logic.
- Structural verification that only `classes.dex` and `classes2.dex` change.
- Byte-preservation checks for `classes3.dex` and `classes4.dex` when present.
- Optional exact semantic-smali comparison against a locally owned proven V9 JAR.
- GitHub repository hygiene workflow preventing accidental proprietary Android binary commits.

### Verified
- Known tested input SHA-256: `22f99bfdc5e9c1cab73c92ce787944c93f511e4637022c1e7a229b77d1ec3c9b`.
- Historical device-tested V9 SHA-256: `7df50700f7460970f434954d67b832774c38fecd66a3696eaedcdb039d9999fe`.
- Locally generated output confirmed `SEMANTIC_REFERENCE_MATCH_OK` against the proven V9.
