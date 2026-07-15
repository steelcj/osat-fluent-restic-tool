# ROADMAP

Version: 0.1.0
Status: Draft

## Near term

- **Add Change log section** to all README.md documents in this project and example projects
- **Windows hardware validation.** The simulated-Windows harness (`validate-windows.py`) covers path resolution, CRLF env writing, wrapper rendering with the header convention, active-version round-trip, and idempotency detection. Remaining items require a Windows machine: `restic.exe` execution through both wrappers, NTFS ACL verification (the Windows analogue of the nix `700` check — POSIX modes are advisory; ACLs currently inherit owner-only from the profile), and `%LOCALAPPDATA%\Programs\` PATH guidance. Because restic ships a native Windows binary, this tool — not sat-tool, which is blocked upstream — is where the fluent collection's Windows conventions get proven; findings feed back to sat-tool's `scripts/windows/README.md` decision.
- **macOS validation.** Both Intel and Apple Silicon are mapped in `ASSET_PLATFORMS` and the asset naming is confirmed against upstream releases, but neither has been exercised on hardware under this manager.
- **Optional GPG verification.** SHA-256 verification against SHA256SUMS is unconditional. When a `gpg` binary is present, additionally verify the SHA256SUMS signature against a key fingerprint pinned in this repository, and record the verification in PROVENANCE. Absence of `gpg` must not block installation.

## Later

- **Governance write-back.** Feed back into the governance specification: the synthesis of archetype 5 acquisition with the fluent manager lifecycle; the verified-binaries-only archive admission rule; the source/generates/generated header convention across all three wrapper syntaxes; the CRLF-explicit writing rule for Windows-rendered files; and the release pipeline (`bump-version.py --release`), now proven in a second repository per the sat-tool ROADMAP item.
- **Archive pruning command.** The archive is a permanent record by design, but binaries are ~25 MB per version; a deliberate `--purge-archive VERSION` (refusing the active and only-archived-copy cases) may be worth adding once the archive holds many versions.
- **Companion configuration layer.** Backup policy — repositories, excludes, schedule, retention, integrity-check timers — is deliberately outside this manager's ownership. A separate configuration layer (script plus systemd user units or Task Scheduler tasks, or an Ansible capability layer) should own it; this manager only guarantees which restic binary answers.
