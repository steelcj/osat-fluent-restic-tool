# ROADMAP

Version: 0.1.0
Status: Draft

## Near term

- **macOS validation.** Both Intel and Apple Silicon are mapped in `ASSET_PLATFORMS` and the asset naming is confirmed against upstream releases, but neither has been exercised on hardware under this manager.
- **Windows bringup.** The binary path (download, verify, archive, place) and the `.cmd`/`.ps1` wrapper rendering are implemented but not validated end to end on Windows. Includes: confirming `%LOCALAPPDATA%\Programs\` PATH guidance, env file call/source behaviour in both shells, and deciding how far ACL verification should go (creation inherits owner-only profile ACLs today; explicit verification on subsequent runs, the Windows analogue of the nix `700` check, is unimplemented).
- **Optional GPG verification.** SHA-256 verification against SHA256SUMS is unconditional. When a `gpg` binary is present, additionally verify the SHA256SUMS signature against a key fingerprint pinned in this repository, and record the verification in PROVENANCE. Absence of `gpg` must not block installation.

## Later

- **Governance write-back.** Feed the synthesis of archetype 5 acquisition with the fluent manager lifecycle (install/switch/status/remove, env-pointer activation, archive surviving removal) back into the governance specification, alongside the equivalent write-back items noted in osat-fluent-myrepos-tool and sat-tool.
- **Archive pruning command.** The archive is a permanent record by design, but binaries are ~25 MB per version; a deliberate `--purge-archive VERSION` (refusing the active and only-archived-copy cases) may be worth adding once the archive holds many versions.
- **Companion configuration layer.** Backup policy — repositories, excludes, schedule, retention, integrity-check timers — is deliberately outside this manager's ownership. A separate configuration layer (script plus systemd user units, or an Ansible capability layer) should own it; this manager only guarantees which restic binary answers.
