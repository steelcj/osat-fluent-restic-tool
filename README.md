# osat-fluent-restic-tool

Version: 0.2.1
Status: Draft

A user-space manager for [restic](https://restic.net/), the encrypted, deduplicating backup program, part of the OS Sovereign Autonomous Tools (OSAT) Fluent collection.

This manager installs versioned, self-contained restic binaries to `~/.local/share/restic-tool/<version>/`, verified against upstream's published SHA-256 checksums, activated through a single env file and a generated wrapper script, and archived locally so reinstall and rollback work offline. Full documentation lives in [docs/en/README.md](docs/en/README.md).

It supersedes the earlier [restic-tool](https://github.com/steelcj/restic-tool), which used the pre-fluent `~/bin/` layout; see the migration section in the full documentation.

## Quick start

```bash
python3 install-restic.py --install
restic version
```

## Platform support

Linux (x86_64, aarch64) and macOS (Intel, Apple Silicon) use the POSIX wrapper; Linux x86_64 is validated end to end. Windows (x86_64) has every kernel-independent code path validated by the simulated-Windows harness (`validate-windows.py`): path resolution, CRLF-correct env files, both wrapper syntaxes, and the version lifecycle. Hardware validation of `restic.exe` execution, NTFS ACLs, and PATH semantics remains; see ROADMAP.md. restic ships a native Windows binary, so full Windows fluency is planned, not excluded.

## Why version pinning matters for a backup tool

A restic repository must be read by a restic version that understands the repository format that wrote it. Side-by-side versioned installs, explicit activation, and a local archive of every verified binary mean the version standing between you and a restore is always the one you chose, switchable and reinstallable without network access. Pinned installs (`--install 0.19.1`) never query the GitHub API at all.

## Verification

Every download is verified against the `SHA256SUMS` file upstream publishes alongside each release before anything touches the filesystem. Each installed version carries a `PROVENANCE` file recording the asset name, its SHA-256, the source, and the install time. All manager-owned paths are owner-only (`700`/`600`), set on creation and verified on every subsequent run.

## License

This software, *osat-fluent-restic-tool*, by **Christopher Steel**, is licensed under the [GNU General Public License v3.0 or later (GPL-3.0-or-later)](https://www.gnu.org/licenses/gpl-3.0.html).

You may redistribute and/or modify this software under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See the `LICENSE` file included with this project for the full license text. restic itself is by Alexander Neumann and the restic contributors and is licensed under the BSD 2-Clause License; this manager installs it unmodified.

[![License: GPL v3+](https://img.shields.io/badge/License-GPLv3%2B-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
