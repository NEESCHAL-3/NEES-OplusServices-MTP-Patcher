# Changelog

All notable changes to the public patcher source are documented here.

## [1.1.0] - 2026-10-11

### Added
- GitHub Pages MTP Patcher with codename input, public JAR links, automatic code compatibility checks, request tracking, and release downloads.
- GitHub issue-driven Actions pipeline with a separate read-only patch job and release publisher.
- Device-named ZIPs, archive and JAR checksums, and patch provenance reports.
- HTTPS downloader with public-address pinning, redirect validation, and size limits.
- Public-sharing confirmation, request limits, and clear failure reports.

### Changed
- Source tree remains binary-free; successful user-authorized patch service outputs are published as public GitHub Release assets.

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
