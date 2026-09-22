# Security and safety

This project modifies a framework JAR used by Android system services. A bad or incompatible patch can cause boot failure or system-server instability.

- Keep a known-good copy of the original JAR.
- Test unknown builds with a reversible method before permanently baking changes.
- Do not disable platform integrity or verification features merely to make an incompatible patch boot.
- Do not report or upload proprietary firmware binaries to this repository.

For a security-sensitive problem in the patcher source itself, open a GitHub issue without attaching proprietary files or device secrets.
