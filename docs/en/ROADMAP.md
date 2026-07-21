# ROADMAP and known issues

Version: 0.1.0
Status: Draft

## Potential Issues

Items to open as tracked issues against [osat-fluent-restic-tool](https://github.com/steelcj/osat-fluent-restic-tool) (or feed back into the osat-fluent template):

1. **`--install` success message is misleading.** After running `python3 install-restic.py --install 0.18.1`, the tool prints `restic 0.18.1 installed and active` and tells the user to verify with `restic version`. Running `restic version` immediately after still reports the *previously active* version, not 0.18.1. Installing a version does not activate it — only `--switch` does. Fix: either change the `--install` output to not claim the version is "active," or have `--install` prompt/offer to switch automatically.
2. **Drive mount point may not match the label.** `e2label` sets the filesystem label, but the desktop automounter doesn't always pick it up for the mount path — some setups keep mounting under the UUID. The guide now has readers confirm the actual path with `lsblk -f` rather than assuming the label. Worth checking whether `install-restic.py` (or a small helper script) could detect and report this automatically.
3. **Multi-target config schema is new and untested end-to-end.** This version introduces `~/.config/restic-tool/env/<host>/<target>/{env,excludes,retention}` as the convention for running more than one backup target from the same machine. It hasn't yet been run through a full second-target setup (e.g. adding an offsite target) to confirm the pattern holds up in practice.

## Near term

- **macOS validation.** Both Intel and Apple Silicon are mapped in `ASSET_PLATFORMS` and the asset naming is confirmed against upstream releases, but neither has been exercised on hardware under this manager.
- **Windows bringup.** The binary path (download, verify, archive, place) and the `.cmd`/`.ps1` wrapper rendering are implemented but not validated end to end on Windows. Includes: confirming `%LOCALAPPDATA%\Programs\` PATH guidance, env file call/source behaviour in both shells, and deciding how far ACL verification should go (creation inherits owner-only profile ACLs today; explicit verification on subsequent runs, the Windows analogue of the nix `700` check, is unimplemented).
- **Optional GPG verification.** SHA-256 verification against SHA256SUMS is unconditional. When a `gpg` binary is present, additionally verify the SHA256SUMS signature against a key fingerprint pinned in this repository, and record the verification in PROVENANCE. Absence of `gpg` must not block installation.

## Later

- **Governance write-back.** Feed the synthesis of archetype 5 acquisition with the fluent manager lifecycle (install/switch/status/remove, env-pointer activation, archive surviving removal) back into the governance specification, alongside the equivalent write-back items noted in osat-fluent-myrepos-tool and sat-tool.
- **Archive pruning command.** The archive is a permanent record by design, but binaries are ~25 MB per version; a deliberate `--purge-archive VERSION` (refusing the active and only-archived-copy cases) may be worth adding once the archive holds many versions.
- **Companion configuration layer.** Backup policy — repositories, excludes, schedule, retention, integrity-check timers — is deliberately outside this manager's ownership. A separate configuration layer (script plus systemd user units, or an Ansible capability layer) should own it; this manager only guarantees which restic binary answers.
