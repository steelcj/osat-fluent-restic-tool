# restic-manual-installer-tests-v0-3-0

Version: 0.3.0
Status: Draft
Style Guide: plain-language, 7th-grade reading level

## Scope

This document covers manual testing of `install-restic.py` only — installing, switching, and removing versions of the `restic` binary itself. It does not cover repository/target configuration, backups, or restores. For that, see [restic-backup-guide--backup-to-external-drive](./restic-backup-guide--backup-to-external-drive-v0-5-0.md), which is the authoritative walkthrough and reflects the current multi-target env schema (`~/.config/restic-tool/env/<host>/<target>/{env,excludes,retention}`).

`install-restic.py` writes and owns `~/.config/restic-tool/restic-tool.env` (tracks `RESTIC_TOOL_ROOT`, the active binary version) — separate from, and never touching, the operator-owned target config under `~/.config/restic-tool/env/`.

## TODO

* Reorder this file
* Create ROADMAP items for this that are not working as desired
* Feed updates back to the osat-fluent project (could be template?) at https://github.com/steelcj/osat-fluent

## Testing osat-fluent-restic-tool

### Test plain installation

```bash
python3 install-restic.py --install
```

First time installation output

```bash
python3 install-restic.py 
usage: install-restic.py [-h] [--install [VERSION]] [--switch VERSION] [--status] [--remove VERSION] [--version]

Manage user-space installations of restic.

options:
  -h, --help           show this help message and exit
  --install [VERSION]  Install VERSION (default: latest stable from GitHub).
  --switch VERSION     Point the env file at an already-installed version.
  --status             Show installed, archived, and active versions.
  --remove VERSION     Remove an installed version (its archive copy is kept).
  --version            Show this manager's version and exit.

Examples:
  install-restic.py --install            install the latest stable release
  install-restic.py --install 0.19.1     install a pinned version (no API call)
  install-restic.py --switch 0.18.1      activate an installed version
  install-restic.py --status             show installed, archived, active
  install-restic.py --remove 0.18.1      remove a non-active version

```

Output example when tool is already installed

```bash
[RESTIC-TOOL] querying GitHub for the latest stable release
[RESTIC-TOOL] latest stable version is v0.19.1
[RESTIC-TOOL] v0.19.1 is already installed at ~/.local/share/restic-tool/0.19.1; activating it
  env file written: ~/.config/restic-tool/restic-tool.env  ✓
  wrapper written:  ~/.local/bin/restic  ✓
  Verify with:  restic version
```

### Install another restic different version

```bash
python3 install-restic.py --install 0.18.1
```

Output example

```bash
[RESTIC-TOOL] installing restic v0.18.1
[RESTIC-TOOL] downloading https://github.com/restic/restic/releases/download/v0.18.1/restic_0.18.1_linux_amd64.bz2
[RESTIC-TOOL] downloading SHA256SUMS
[RESTIC-TOOL] verifying SHA-256 checksum against the published SHA256SUMS
[RESTIC-TOOL] extracting restic
  binary verified:  executes and reports v0.18.1  ✓
  archived:         ~/.local/share/restic-tool/archive/0.18.1/restic  ✓
  binary placed:    ~/.local/share/restic-tool/0.18.1/restic  ✓  (restic v0.18.1)
  env file written: ~/.config/restic-tool/restic-tool.env  ✓
  wrapper written:  ~/.local/bin/restic  ✓

[RESTIC-TOOL] restic 0.18.1 installed and active.
  Verify with:  restic version
```

### Verify

```bash
restic version
```

Output example:

```bash
restic 0.19.1 compiled with go1.26.4 on linux/amd64
```

Notice here we see the version that was previously installed, indicating that when we installed v0.18.1 the output lied when it said:

```bash
[RESTIC-TOOL] restic 0.18.1 installed and active.
  Verify with:  restic version
```

This is a tooling documentation issue. In order to activate the new version we actually need to run the switch command, like this:

### activate an different installed restic version

```bash
python3 install-restic.py --switch 0.18.1
```

Expected output:

```bash
  env file written: ~/.config/restic-tool/restic-tool.env  ✓
  wrapper written:  ~/.local/bin/restic  ✓
[RESTIC-TOOL] Active version is now 0.18.1.
```

### Switch back to the latest version

```bash
python3 install-restic.py --switch 0.19.1
```

Expected output:

```bash
  env file written: ~/.config/restic-tool/restic-tool.env  ✓
  wrapper written:  ~/.local/bin/restic  ✓
[RESTIC-TOOL] Active version is now 0.19.1.
```

### Remove older restic version

In this case we never used restiv version 0.18.1 so we will simply remove it since we are never going to use it and our test is over.

```bash
python3 install-restic.py --remove 0.18.1
```

Output example:

```bash
[RESTIC-TOOL] 0.18.1 removed.
  The verified binary remains in the archive; reinstall offline
  at any time with:  --install 0.18.1
```

Once the tool is installed 

## Restic Installer Requirements

* git
* python3
* https://github.com/steelcj/osat-fluent-restic-tool

### Restic Tool Installation

#### Using a repository clone

```bash
mkdir ~/projects/installers
cd ~/projects/installers
git clone https://github.com/steelcj/osat-fluent-restic-tool.git
```

## Using restic day-to-day

Repository/target setup, backups, restores, retention, and the offsite copy are all covered — with the current multi-target env schema — in [restic-backup-guide--backup-to-external-drive](./restic-backup-guide--backup-to-external-drive-v0-4-0.md). Steps 1 through 8 previously duplicated here have been removed: they described a single flat `~/.config/restic-tool/env` file, which is no longer accurate now that the tool supports multiple targets under `~/.config/restic-tool/env/<host>/<target>/`. Keeping one canonical copy of that walkthrough avoids the two docs drifting out of sync again.

## License

This document, *Backing up your computer with restic*, by **Christopher Steel**, with AI assistance from **Claude (Anthropic)**, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.3.0 | Draft | Added a note under Scope distinguishing manager-owned `restic-tool.env` (active binary version) from operator-owned target config under `env/`; updated cross-reference to backup guide v0.5.0. |
| 0.2.0 | Draft | Removed the stale single-target Step 1-8 walkthrough (flat `~/.config/restic-tool/env` file), which had drifted out of sync with the multi-target `env/<host>/<target>/{env,excludes,retention}` schema now documented in the backup guide. Scoped this document to `install-restic.py` testing only and pointed to the backup guide for setup/usage. |
| 0.1.0 | Draft | First plain-language version of the restic backup guide |
