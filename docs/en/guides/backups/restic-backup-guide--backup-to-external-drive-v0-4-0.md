---
title: "Backing up your computer with restic"
creator: "Christopher Steel"
contributor: "Claude (Anthropic) — drafting assistance"
subject: "Backup; restic; USB-attached storage; multi-target configuration; osat-fluent-restic-tool"
description: "A plain-language, 7th-grade reading level guide to setting up restic backups to a USB-attached SSD, supporting multiple backup targets, with installer testing notes and known tooling issues kept separate."
date: 2026-07-18
type: "Guide"
format: "text/markdown"
identifier: "restic-backup-guide--backup-to-external-drive"
language: "en-CA"
rights: "CC BY 4.0"
relation: "https://github.com/steelcj/osat-fluent-restic-tool"
version: 0.2.0
status: Draft
style_guide: "plain-language, easy reading"
---

# Backing up your computer with restic

Version: 0.2.0
Status: Draft

## Overview

This guide walks through setting up restic backups to a USB-attached SSD, installed and managed with the [osat-fluent-restic-tool](https://github.com/steelcj/osat-fluent-restic-tool). It covers installing restic, preparing the drive, securing a passphrase, configuring one or more backup targets, running your first backup, proving you can restore, and keeping an offsite copy for the 3-2-1 rule.

Testing notes for the installer tool itself, and known issues, are kept separate in the appendices so the main procedure stays clean and easy to follow.

## Requirements

* `git`
* `python3`
* [osat-fluent-restic-tool](https://github.com/steelcj/osat-fluent-restic-tool)
* A USB-attached SSD, ready to be formatted (formatting erases the drive — confirm you have the right one before proceeding)

## Install restic

Clone the installer tool:

```bash
mkdir ~/projects/installers
cd ~/projects/installers
git clone https://github.com/steelcj/osat-fluent-restic-tool.git
```

Install restic with the tool. The installer checks that the download is genuine and that the program runs before it accepts it. It also keeps a spare copy, so you can reinstall later even without internet.

```bash
python3 install-restic.py --install
restic version
```

If the second command prints a version number, restic is ready.

## Get the drive ready

Backups will live on an external drive. The drive should use the Linux format called ext4. Formatting erases the drive, so make sure it is the right one:

```bash
lsblk -f                                    # find the drive
sudo mkfs.ext4 -L bravo-backup /dev/sdX1    # format it (replace sdX1!)
```

Give the drive a clear label:

```bash
sudo e2label /dev/sdX1 newlabel
```

Real-world example:

```bash
sudo e2label /dev/sda1 512GB
```

### Find the drive's mount path

Unplug and reconnect the drive (or reboot), then look up its label and UUID:

```bash
sudo blkid /dev/sda1
```

```
/dev/sda1: LABEL="512GB" UUID="52b79ff7-a6ae-408b-b601-e6cfcb7b3aa7" BLOCK_SIZE="4096" TYPE="ext4"
```

Then confirm where it actually mounted:

```bash
lsblk -f
```

Check the `MOUNTPOINT` column. Desktop automounters don't always use the label — some keep mounting under the UUID instead, especially if the drive was plugged in once before the label was set. Either is fine; just use whatever path `lsblk -f` actually shows you from here on. In the example above, that's:

```
/media/initial/52b79ff7-a6ae-408b-b601-e6cfcb7b3aa7
```

### Create the backup directory

Put backups in a `backups` folder, with one subfolder per computer being backed up — useful if this drive will ever hold backups from more than one machine:

```bash
sudo mkdir -p /media/initial/52b79ff7-a6ae-408b-b601-e6cfcb7b3aa7/backups/flow
sudo chown -R "${USER}:${USER}" /media/initial/52b79ff7-a6ae-408b-b601-e6cfcb7b3aa7/backups
```

`mkfs.ext4` leaves a freshly formatted drive owned by `root`, so the `chown` step above isn't optional — skip it and `restic init` later will fail with `permission denied`.

## Set a backup passphrase

Restic locks every backup with a password. Make one and save it into a protected folder:

```bash
( umask 077 && openssl rand -base64 32 > ~/.private/restic-tool/password.txt )
```

**This is the most important step in this whole guide.**

Confirm and record your passphrase in a secure password manager. Notice the space at the start of the command below — it keeps the passphrase out of your `bash_history` file:

```bash
 cat ~/.private/restic-tool/password.txt
```

Now write that password down in two more places: your password manager, and somewhere offline, like a paper note in a safe spot. If you lose the password, nobody on Earth can open your backups. Not even you.

If you set up more than one backup target later, you can point them all at this same passphrase file, or give each target its own — see [Configure a backup target](#configure-a-backup-target) below.

### Check the passphrase file's permissions

```bash
ls -al ~/.private/ | grep restic
```

Output example:

```
drwx------  2 initial initial   4096 Jul 15 10:22 restic-tool
```

```bash
ls -al ~/.private/restic-tool
```

Output example:

```
-rw-------  1 root    root      26 Jun 24 20:28 password.txt
```

## Configure a backup target

A "target" is one combination of a repository location and a passphrase — a computer with an SSD backup and an offsite backup, for example, is two targets. Give each one its own settings folder, named by computer and drive, so they never collide:

```bash
mkdir -p ~/.config/restic-tool/env/flow/512GB
nano ~/.config/restic-tool/env/flow/512GB/env
```

With these two lines, using the drive path you confirmed above:

```sh
export RESTIC_REPOSITORY="/media/initial/52b79ff7-a6ae-408b-b601-e6cfcb7b3aa7/backups/flow"
export RESTIC_PASSWORD_FILE="${HOME}/.private/restic-tool/password.txt"
```

The first line says where the backups go. The second says where the passphrase lives.

Two more files in the same folder round this target out:

```bash
nano ~/.config/restic-tool/env/flow/512GB/excludes
```

One pattern per line — folders nobody needs backed up:

```
.cache
.local/share/Trash
```

```bash
nano ~/.config/restic-tool/env/flow/512GB/retention
```

The keep-and-clean policy for this target (see [Keep it healthy](#keep-it-healthy) below):

```sh
export RESTIC_FORGET_OPTS="--keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune"
```

### Activate a target before running restic

Unlike restic's own binary version (managed separately by `install-restic.py --switch`), a target is activated just by sourcing its `env` file in your current shell:

```bash
source ~/.config/restic-tool/env/flow/512GB/env
```

Every `restic` command below assumes you've done this first. If you ever see restic complain it can't find a repository or password file, this is the first thing to check.

**Optional shortcut:** add a small function to `~/.bashrc` so you don't have to type the full path each time:

```bash
resticenv() { source "$HOME/.config/restic-tool/env/$1/$2/env"; }
```

Used as `resticenv flow 512GB`.

## Start the backup vault and test it

### Create your backup config

```bash
restic init
```

Output example

```bash
created restic repository b93a0b7ef6 at /media/initial/52b79ff7-a6ae-408b-b601-e6cfcb7b3aa7/backups/flow

Please note that knowledge of your password is required to access
the repository. Losing your password means that your data is
irrecoverably lost.
```

Or, if the config file already exists:

```bash
Fatal: Fatal: create repository at /media/initial/52b79ff7-a6ae-408b-b601-e6cfcb7b3aa7/backups/flow failed: config file already exists
```

### Run a small backup test

This creates the vault (restic calls it a repository). Now do a tiny test backup, look at it, and check it:

```bash
restic backup ~/.config/restic-tool
```

Output example

```bash
repository b93a0b7e opened (version 2, compression level auto)
using parent snapshot d846dc21
[0:00] 100.00%  12 / 12 index files loaded

Files:           0 new,     0 changed,     4 unmodified
Dirs:            0 new,     7 changed,     0 unmodified
Added to the repository: 2.976 KiB (2.141 KiB stored)

processed 4 files, 552 B in 0:01
snapshot 38340bc3 saved
```

### Snapshots

```bash
restic snapshots
```

Output:

```bash
repository b93a0b7e opened (version 2, compression level auto)
ID        Time                 Host        Tags        Paths                              Size
-----------------------------------------------------------------------------------------------------
d846dc21  2026-07-18 14:27:17  flow                    /home/initial/.config/restic-tool  552 B
cfec250e  2026-07-18 14:30:21  flow                    /home/initial                      243.304 GiB
38340bc3  2026-07-21 08:02:25  flow                    /home/initial/.config/restic-tool  552 B
-----------------------------------------------------------------------------------------------------
Timestamps shown in local time
3 snapshots
```

### Restic check

```bash
restic check
```

Output example

```bash
using temporary cache in /tmp/restic-check-cache-3588666014
create exclusive lock for repository
repository b93a0b7e opened (version 2, compression level auto)
created new cache in /tmp/restic-check-cache-3588666014
load indexes
[0:00] 100.00%  13 / 13 index files loaded
check all packs
117 additional files were found in the repo, which likely contain duplicate data.
This is non-critical, you can run `restic prune` to correct this.
check snapshots, trees and blobs
[0:02] 100.00%  3 / 3 snapshots
no errors were found
```

Notice this part of the message:

```bash
117 additional files were found in the repo, which likely contain duplicate data.
This is non-critical, you can run `restic prune` to correct this.
```

### Reatic prune

```
restic prune --dry-run
```

```bash
restic prune
```

Output example:

```bash
repository b93a0b7e opened (version 2, compression level auto)
[0:00] 100.00%  13 / 13 index files loaded
loading all snapshots...
finding data that is still in use for 3 snapshots
[0:02] 100.00%  3 / 3 snapshots
searching used packs...
collecting packs for deletion and repacking
[0:00] 100.00%  8827 / 8827 packs processed

to repack:             0 blobs / 0 B
this removes:          0 blobs / 0 B
to delete:             0 blobs / 1.870 GiB
total prune:           0 blobs / 1.870 GiB
remaining:        524860 blobs / 146.256 GiB
unused size after prune: 0 B (0.00% of remaining size)

deleting unreferenced packs
[0:00] 100.00%  117 / 117 files deleted
done
```

### restic check after prune

```bash
restic check
```

Output example:

```bash
using temporary cache in /tmp/restic-check-cache-982999797
create exclusive lock for repository
repository b93a0b7e opened (version 2, compression level auto)
created new cache in /tmp/restic-check-cache-982999797
load indexes
[0:00] 100.00%  13 / 13 index files loaded
check all packs
check snapshots, trees and blobs
[0:02] 100.00%  3 / 3 snapshots
no errors were found
```

### restic backup

If `check` says everything is fine, do your first real backup, using the exclude list from your target's folder:

```bash
restic backup ~ --exclude-file ~/.config/restic-tool/env/flow/512GB/excludes
```

Output example

```bash
repository b93a0b7e opened (version 2, compression level auto)
no parent snapshot found, will read all files
error: open /home/initial/.private/something/secret.txt: permission denied
[[h:39] 8.79% 260240 files 21.389 GiB, total 847223 files 243.304 GiB, 1 errors ETA 17:12
/home/initial/2-areas/friends-and-family/Zooms/2024-05-12 19-23-10.mkv
/home/initial/2-areas/me/cv/applications/archived/®. Penega/2023-04-24 10-01-13.mkv
```

**Notice**: Because of the restricted permissions on our `/home/initial/.private/something/secret.txt`this is not backed up.

#### Results output

```bash
repository b93a0b7e opened (version 2, compression level auto)
no parent snapshot found, will read all files
error: open /home/initial/.private/something/secret.txt: permission denied

Files:       847225 new,     0 changed,     0 unmodified
Dirs:        125734 new,     0 changed,     0 unmodified
Added to the repository: 157.077 GiB (146.277 GiB stored)

processed 847225 files, 243.304 GiB in 15:57
snapshot cfec250e saved
Warning: at least one source file could not be read
```

### Second restic backup

After the first full backup is created , later backups are much faster as only the changes are backed up

```bash
restic backup
```

Output example:

```bash
repository b93a0b7e opened (version 2, compression level auto)
using parent snapshot 20546195
[0:00] 100.00%  14 / 14 index files loaded
error: open /home/initial/.private/restic/password.txt: permission denied

Files:           0 new,     1 changed, 851174 unmodified
Dirs:            0 new,     5 changed, 126351 unmodified
Added to the repository: 690.354 KiB (67.050 KiB stored)

processed 851175 files, 218.590 GiB in 0:22
snapshot aca6ca4c saved
Warning: at least one source file could not be read
```

## Prove you can get files back

A backup only counts if you can restore from it. Try it now with one file:

```bash
restic restore latest --target /tmp/restore-test --include ~/Documents/output.pdf
```

Confirm

```bash
ls -al /tmp/restore-test/home/initial/Documents/
```

output:

```bash
total 132
drwxr-xr-x 2 initial initial   4096 May 13 08:19 .
drwxr-xr-x 3 initial initial   4096 Jul 21 00:15 ..
-rw-rw-r-- 1 initial initial 125597 Mar  6 09:40 output.pdf
```

Open and check the restored file. If it works, your safety net is functioning as it should and is real.

## Keeping your backups healthy

Backups pile up over time. Once in a while, tell restic to keep the recent ones and clear out the very old ones, using the retention policy set for this target:

```bash
source ~/.config/restic-tool/env/flow/512GB/retention
restic forget ${RESTIC_FORGET_OPTS}
```

That default policy keeps a backup a day for a week, one a week for a month, and one a month for a year.

Also put two reminders in your calendar:

1. **Once a month:** run `restic check`.
2. **Every three months:** restore a file or two, and open them.

These two habits are what make this setup better than the old tools. Problems get caught early, while they are still small.

## Keeping a copy away from home

One drive sitting next to your computer can be lost in the same fire, flood, or theft as the computer. So keep a second copy of your backups somewhere else, in online storage, for example. Restic can back up straight to online storage through a helper program called rclone. Your backups stay locked the whole way; the storage company only ever sees scrambled data.

An offsite copy is just another target — give it its own folder under `~/.config/restic-tool/env/`, for example `env/flow/offsite/`, following the same pattern above.

With your files, a local backup drive, and an offsite copy, you have three copies in two kinds of places with one away from home. That is the classic 3-2-1 rule, and it is the finish line.

## Licence

This document, *Backing up your computer with restic*, by **Christopher Steel**, with AI assistance from **Claude (Anthropic)**, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.4.0 | Draft | moved roadmap and installer testing documentation out of document |
| 0.3.0 | Draft | Added details and support for multiple host backup configurations and settings |
| 0.1.0 | Draft | First plain-language version of the restic backup guide |
| 0.1.1 | Draft | Reordered into a working document: main procedure separated from installer-tool testing notes (Appendix A); added Dublin Core frontmatter; captured open issues as a Roadmap section |
| 0.1.2 | Draft | Added drive-mount verification (label vs. UUID) and a `chown` step, after a real-world `restic init` failure (`permission denied`) traced to root-owned freshly formatted drives |
| 0.2.0 | Draft | Removed section numbering throughout. Introduced multi-target config schema (`env/<host>/<target>/{env,excludes,retention}`), replacing the single hardcoded `~/.config/restic-tool/env` file. Fixed a path mismatch between the backup-directory creation step and the repository path in the env file. Added an explicit target-activation step (`source .../env`) ahead of every restic command. Removed a duplicated directory-creation section. Backup and retention commands now reference the target's `excludes` and `retention` files instead of inline flags. |
