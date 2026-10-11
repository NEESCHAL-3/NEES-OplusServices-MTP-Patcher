# Security and safety

This project modifies a framework JAR used by Android system services. A bad or incompatible patch can cause boot failure or system-server instability.

- Keep a known-good copy of the original JAR.
- Test unknown builds with a reversible method before permanently baking changes.
- Do not disable platform integrity or verification features merely to make an incompatible patch boot.
- Do not commit firmware binaries or attach them to security reports. The patch service accepts public download links only from users who confirm they can share the input and output publicly.

For a security-sensitive problem in the patcher source itself, open a GitHub issue without attaching proprietary files or device secrets.

## Hosted patch service

- All request fields and generated releases are public. Do not submit credentials, signed private links, device identifiers, or other secrets.
- Download URLs are HTTPS-only, DNS results must be public, and every redirect is checked. Connections pin a validated address while retaining TLS hostname verification.
- Downloads are limited to 100 MB, expanded archives to 512 MB, and archive entries to 10,000. Inputs are parsed as data, never executed.
- The processing job has read-only repository permissions and no persisted Git credentials. Publication happens in a separate job after structural checks pass.
- Three requests per account in 24 hours and twenty open requests bound ordinary usage. These are abuse deterrents, not a comprehensive defense against coordinated accounts; disable the Patch request workflow if necessary.
- Maintainers can close unwanted issues, delete release assets, or disable the workflow. Treat codename labels and successful builds as distinct from on-device validation.
