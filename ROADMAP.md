# ROADMAP and known issues

Version: 0.1.0
Status: Draft

## Potential Issues

Items to open as tracked issues against [osat-fluent-restic-tool](https://github.com/steelcj/osat-fluent-restic-tool) (or feed back into the osat-fluent template):

1. **`--install` success message is misleading.** After running `python3 install-restic.py --install 0.18.1`, the tool prints `restic 0.18.1 installed and active` and tells the user to verify with `restic version`. Running `restic version` immediately after still reports the *previously active* version, not 0.18.1. Installing a version does not activate it — only `--switch` does. Fix: either change the `--install` output to not claim the version is "active," or have `--install` prompt/offer to switch automatically.
2. **Drive mount point may not match the label.** `e2label` sets the filesystem label, but the desktop automounter doesn't always pick it up for the mount path — some setups keep mounting under the UUID, and reconnecting the same drive later can land it under a different mount path than the one originally recorded (label one time, UUID the next). The backup guide now has readers confirm the actual path with `lsblk -f` rather than assuming the label or a previously recorded path. Worth checking whether `install-restic.py` (or a small helper script) could detect and report this automatically.
3. **Multi-target config schema is new and untested end-to-end.** This version introduces `~/.config/restic-tool/env/<host>/<target>/{env,excludes,retention}` as the convention for running more than one backup target from the same machine. It hasn't yet been run through a full second-target setup (e.g. adding an offsite target) to confirm the pattern holds up in practice.
4. **`--install` fails with an unhelpful 404 for some explicit versions.**

       python3 install-restic.py --install 0.3.0

   output example:

       [RESTIC-TOOL] installing restic v0.3.0
       [RESTIC-TOOL] downloading https://github.com/restic/restic/releases/download/v0.3.0/restic_0.3.0_linux_amd64.bz2
       [RESTIC-TOOL ERROR] download failed for https://github.com/restic/restic/releases/download/v0.3.0/restic_0.3.0_linux_amd64.bz2: HTTP Error 404: Not Found

   Not yet confirmed whether this is a tool defect or simply an early restic release (0.3.0 predates restic's current asset-naming and platform-binary scheme) that was never published in the form `ASSET_PLATFORMS` expects. Either way, the error should distinguish "this version was never published for this platform" from a genuine download failure, rather than surfacing the raw HTTP error.

## Near term

- **macOS validation.** Both Intel and Apple Silicon are mapped in `ASSET_PLATFORMS` and the asset naming is confirmed against upstream releases, but neither has been exercised on hardware under this manager.
- **Windows hardware validation.** The simulated-Windows harness (`validate-windows.py`) covers path resolution, CRLF env writing, wrapper rendering with the header convention, active-version round-trip, and idempotency detection. Remaining items require a Windows machine: `restic.exe` execution through both wrappers, env file call/source behaviour in both `.cmd` and `.ps1` shells, NTFS ACL verification (the Windows analogue of the nix `700` check — POSIX modes are advisory; ACLs currently inherit owner-only from the profile, and how far explicit verification on subsequent runs should go is still undecided), and `%LOCALAPPDATA%\Programs\` PATH guidance. Because restic ships a native Windows binary, this tool — not sat-tool, which is blocked upstream — is where the fluent collection's Windows conventions get proven; findings feed back to sat-tool's `scripts/windows/README.md` decision.
- **Optional GPG verification.** SHA-256 verification against SHA256SUMS is unconditional. When a `gpg` binary is present, additionally verify the SHA256SUMS signature against a key fingerprint pinned in this repository, and record the verification in PROVENANCE. Absence of `gpg` must not block installation.
- **bump-version.py: decide `--release`'s scope.** This repo's `bump-version.py` bumps `VERSION` and the version lines in `README.md`/`docs/en/README.md`, and `--release` additionally inserts a changelog row and runs the commit → guard → tag → guard ceremony. The sat-doc-automa repository's `bump-version.py` is deliberately narrower — it bumps `VERSION` and nothing else, with commit/tag/push left fully manual, on the principle that a single-purpose script cannot half-update a repository. Two ways to reconcile: (1) adopt automa's script as-is, dropping `--release` and its ceremony entirely; or (2) keep the `--release` ceremony but strip the README-touching and changelog-insertion steps out of it, so it only ever commits `VERSION`. Affects the Governance write-back item below, which currently assumes this repo's *current* `bump-version.py --release` is the version to promote; that assumption does not hold until this is decided.

## Later

- **Governance write-back.** Feed back into the governance specification: the synthesis of archetype 5 acquisition with the fluent manager lifecycle (install/switch/status/remove, env-pointer activation, archive surviving removal); the verified-binaries-only archive admission rule; the source/generates/generated header convention across all three wrapper syntaxes; the CRLF-explicit writing rule for Windows-rendered files; and the release pipeline (`bump-version.py --release`), now proven in a second repository per the sat-tool ROADMAP item — alongside the equivalent write-back items noted in osat-fluent-myrepos-tool and sat-tool. Blocked on the bump-version.py scope decision above — which version of the release pipeline gets promoted depends on how that's resolved.
- **Archive pruning command.** The archive is a permanent record by design, but binaries are ~25 MB per version; a deliberate `--purge-archive VERSION` (refusing the active and only-archived-copy cases) may be worth adding once the archive holds many versions.
- **Companion configuration layer.** Backup policy — repositories, excludes, schedule, retention, integrity-check timers — is deliberately outside this manager's ownership. A separate configuration layer (script plus systemd user units or Task Scheduler tasks, or an Ansible capability layer) should own it; this manager only guarantees which restic binary answers.
