# Restic backup guide

Version: 0.1.0
Status: Draft
Style Guide: style-guide--technical-documentation-for-technologists v0.2.0

## Abstract

This guide establishes encrypted, deduplicating, verifiable backups on a Linux desktop using restic, installed through `osat-fluent-restic-tool`, with a primary repository on a local ext4 external drive and an offsite second repository reached through rclone. It replaces chain-based tools such as Déjà Dup, whose incremental design allows one corrupt increment to poison every backup after it. restic's content-addressed model has no chains: every snapshot is independently restorable, and corruption is detectable on demand with `restic check` rather than discovered on restore day.

## Install the tool

Install restic through the fluent manager, which verifies every download against upstream's published SHA-256 checksums, proves the binary executes before accepting it, and archives every verified binary for offline reinstall:

```bash
python3 install-restic.py --install
restic version
```

Version pinning matters more for a backup tool than for almost anything else: a repository must be read by a restic version compatible with the format that wrote it. The manager's side-by-side versions, explicit `--switch`, and permanent archive keep that choice yours, not a package manager's.

## Prepare the drive

Format the external drive as a proper Linux filesystem — ext4, clearly labelled (`sudo mkfs.ext4 -L bravo-backup /dev/sdX1`, confirming the device against `lsblk -f` first; the operation is destructive). Avoid exFAT and NTFS: case-insensitive or foreign filesystems under a backup repository trade away robustness for nothing.

## Create the password, then the repository

Every restic repository is encrypted; there is no unencrypted option. Generate the password into the credential directory the manager created:

```bash
( umask 077 && openssl rand -base64 32 > ~/.private/restic-tool/password.txt )
```

Immediately record the passphrase in a password manager *and* an offline location. A repository without its password is cryptographically excellent garbage — this is the one unrecoverable failure in the whole design.

## The operator env file

Write `~/.config/restic-tool/env` — operator territory, never touched by the manager:

```sh
export RESTIC_REPOSITORY="/media/user/bravo-backup/restic-repo"
export RESTIC_PASSWORD_FILE="$HOME/.private/restic-tool/password.txt"
```

The generated wrapper sources this at runtime, so every restic invocation — interactive shell or systemd timer — resolves the repository and password identically, with no flags.

## Initialise and prove

```bash
restic init
restic backup ~/.config/restic-tool     # small first snapshot as a smoke test
restic snapshots
restic check
```

A clean `check` earns the first real backup: the home directory, excluding noise —

```bash
restic backup ~ --exclude ~/.cache --exclude "$HOME/.local/share/Trash" \
       --exclude /media
```

Add VM images, container storage, and any rclone staging directories to the excludes. Exclude the backup drive's own mount point to prevent recursion. Then prove restorability, which is the only proof that counts:

```bash
restic restore latest --target /tmp/restore-test --include ~/Documents/somefile
```

## Retention

Unbounded snapshot growth is managed with a forget-and-prune policy, run periodically rather than after every backup:

```bash
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune
```

## The verification habit

The structural difference from the Déjà Dup failure mode is that corruption in a restic repository is detectable on demand — but only if asked. Calendar two recurring items: monthly `restic check` (quarterly, add `--read-data-subset=10%` for a deeper sample), and a quarterly test restore of a few real files. A backup system's track record is only as good as the last restore proven.

## The offsite leg

A single drive beside the machine shares the machine's fate in theft, fire, and power events. restic speaks rclone natively, so the second repository is a first-class target rather than a synchronised copy:

```bash
restic -r rclone:remote:bravo-backup init      # once
restic -r rclone:remote:bravo-backup backup ~  # or restic copy between repos
```

The repository is encrypted at rest; the provider sees only ciphertext. Local drive plus offsite repository plus the live data completes a 3-2-1 arrangement.

## Scheduling

Policy — paths, excludes, schedule, retention, check timers — belongs to a configuration layer outside the tool manager: a backup script under version control plus systemd user units (`backup.service`/`.timer`, `check.service`/`.timer`), with `ConditionPathIsMountPoint=` guarding against runs while the drive is absent. That layer is specified in its own repository; this guide ends where policy begins.

## License

This document, *Restic backup guide*, by **Christopher Steel**, with AI assistance from **Claude (Anthropic)**, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.1.0 | Draft | Initial guide: fluent-manager install, ext4 drive, credential and operator-env conventions, init and proof, retention, verification habit, rclone offsite leg |
