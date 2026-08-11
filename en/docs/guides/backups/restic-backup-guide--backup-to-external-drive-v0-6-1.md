---
title: "Backing up your computer with restic"
creator: "Christopher Steel"
contributor: "Claude (Anthropic) — drafting assistance"
subject: "Backup; restic; USB-attached storage; multi-target configuration; osat-fluent-restic-tool"
description: "A plain-language, 7th-grade reading level guide to setting up restic backups to a USB-attached SSD, supporting multiple backup targets, with installer testing notes and known tooling issues kept separate."
date: 2026-08-11
type: "Guide"
format: "text/markdown"
identifier: "restic-backup-guide--backup-to-external-drive"
language: "en-CA"
rights: "CC BY 4.0"
relation: "https://github.com/steelcj/osat-fluent-restic-tool"
version: 0.6.0
status: Draft
style_guide: "plain-language, easy reading"
---

# Backing up your computer with restic

Version: 0.6.0
Status: Draft

## Overview

This guide walks through setting up restic backups to a USB-attached SSD, installed and managed with the [osat-fluent-restic-tool](https://github.com/steelcj/osat-fluent-restic-tool). It covers installing restic, preparing the drive, securing a passphrase, configuring one or more backup targets, running your first backup, proving you can restore, automating backups on Linux, macOS, and Windows, and keeping an offsite copy for the 3-2-1 rule.

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

> **Note:** everything under `~/.config/restic-tool/env/` is operator-owned target config — this is the only place `RESTIC_REPOSITORY`, `RESTIC_PASSWORD_FILE`, and retention settings belong. It's separate from `~/.config/restic-tool/restic-tool.env`, a file `install-restic.py` generates and owns to track which installed `restic` binary is active (`RESTIC_TOOL_ROOT`). The manager never writes into `env/`, and nothing you put in `env/` affects which restic version runs.

```bash
mkdir -p ~/.config/restic-tool/env/flow/512GB
nano ~/.config/restic-tool/env/flow/512GB/env
```

With these two lines, using the drive path you confirmed above:

Label Based Example

```bash
export RESTIC_REPOSITORY="/media/initial/512GB/backups/flow"
export RESTIC_PASSWORD_FILE="${HOME}/.private/restic-tool/password.txt"
```

UUID Based example

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

### Setup a Keep and Clean Policy

The keep-and-clean policy for this target (see [Keeping your backups healthy](#keeping-your-backups-healthy) below):

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

#### Prune dry run

```bash
restic prune --dry-run
```

Output example:

```bash
repository b93a0b7e opened (version 2, compression level auto)
[0:00] 100.00%  18 / 18 index files loaded
loading all snapshots...
finding data that is still in use for 8 snapshots
[0:03] 100.00%  8 / 8 snapshots
searching used packs...
collecting packs for deletion and repacking
[0:00] 100.00%  8860 / 8860 packs processed

Would have made the following changes:

to repack:         15663 blobs / 26.557 MiB
this removes:          0 blobs / 0 B
to delete:             0 blobs / 0 B
total prune:           0 blobs / 0 B
remaining:        531659 blobs / 146.668 GiB
unused size after prune: 0 B (0.00% of remaining size)
```

#### Running the prune

```bash
restic prune
```

Output example:

```bash
repository b93a0b7e opened (version 2, compression level auto)
[0:00] 100.00%  18 / 18 index files loaded
loading all snapshots...
finding data that is still in use for 8 snapshots
[0:03] 100.00%  8 / 8 snapshots
searching used packs...
collecting packs for deletion and repacking
[0:00] 100.00%  8860 / 8860 packs processed

to repack:         15663 blobs / 26.557 MiB
this removes:          0 blobs / 0 B
to delete:             0 blobs / 0 B
total prune:           0 blobs / 0 B
remaining:        531659 blobs / 146.668 GiB
unused size after prune: 0 B (0.00% of remaining size)

repacking packs
[0:01] 100.00%  13 / 13 packs repacked
rebuilding index
[0:00] 100.00%  19 / 19 indexes processed
[0:00] 100.00%  10 / 10 old indexes deleted
removing 13 old packs
[0:00] 100.00%  13 / 13 files deleted
done
initial@flow:~/2-areas/developm
```

### restic check after prune

```bash
restic check
```

Output example

```bash
using temporary cache in /tmp/restic-check-cache-4221204645
create exclusive lock for repository
repository b93a0b7e opened (version 2, compression level auto)
created new cache in /tmp/restic-check-cache-4221204645
load indexes
[0:00] 100.00%  11 / 11 index files loaded
check all packs
check snapshots, trees and blobs
[0:02] 100.00%  8 / 8 snapshots
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
/home/initial/2-areas/me/cv/applications/archived/Penega/2023-04-24 10-01-13.mkv
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
using parent snapshot 976e96fc
[0:00] 100.00%  11 / 11 index files loaded
error: open /home/initial/.private/restic/password.txt: permission denied

Files:       73121 new, 10881 changed, 833548 unmodified
Dirs:         6455 new,  1621 changed, 124436 unmodified
Added to the repository: 46.168 GiB (45.117 GiB stored)

processed 917550 files, 272.093 GiB in 3:22
snapshot d853935b saved
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

Backups pile up over time. Once in a while, tell restic to keep the recent ones and clear out the very old ones.

### Creating a backup policy

The policy implemented here keeps a backup a day for a week, one a week for a month, and one a month for a year.

Also put two reminders in your calendar or create and automation to confirm that everything is working as it should:

1. **Once a month:** run `restic check`.
2. **Every three months:** restore a file or two, and open them.

These two practices are what make this setup better than some other older backup tools. Problems get caught early, while they are still small and easier to recover from.

### export RESTIC_REPOSITORY and RESTIC_PASSWORD_FILE

First, ensure that that paths for the RESTIC_REPOSITORY and RESTIC_PASSWORD_FILE are set:

```bash
source ~/.config/restic-tool/env/flow/512GB/env
```

### export RESTIC_FORGET_OPTS

Then, export your RESTIC_FORGET_OPTS values and run `restic forget`:

```bash
source ~/.config/restic-tool/env/flow/512GB/retention
restic forget ${RESTIC_FORGET_OPTS}
```

Output Example:

### First run output example

```bash
repository b93a0b7e opened (version 2, compression level auto)
Applying Policy: keep 7 daily, 4 weekly, 12 monthly snapshots
keep 7 snapshots:
ID        Time                 Host        Tags        Reasons                  Paths          Size
----------------------------------------------------------------------------------------------------------
cfec250e  2026-07-18 14:30:21  flow                    daily snapshot           /home/initial  243.304 GiB
                                                       weekly snapshot
                                                       oldest monthly snapshot
a54a86f9  2026-07-21 23:14:40  flow                    daily snapshot           /home/initial  218.546 GiB
976e96fc  2026-07-22 00:07:49  flow                    daily snapshot           /home/initial  218.546 GiB
                                                       weekly snapshot
d853935b  2026-07-28 17:27:52  flow                    daily snapshot           /home/initial  272.093 GiB
f647986f  2026-07-30 13:42:32  flow                    daily snapshot           /home/initial  272.262 GiB
                                                       weekly snapshot
                                                       monthly snapshot
1e660b7b  2026-08-05 17:41:24  flow                    daily snapshot           /home/initial  273.153 GiB
155aac8e  2026-08-07 00:31:11  flow                    daily snapshot           /home/initial  275.278 GiB
                                                       weekly snapshot
                                                       monthly snapshot
----------------------------------------------------------------------------------------------------------
Timestamps shown in local time
7 snapshots

remove 2 snapshots:
ID        Time                 Host        Tags        Paths          Size
---------------------------------------------------------------------------------
0ce82b1c  2026-08-05 17:39:35  flow                    /home/initial  273.153 GiB
28b68070  2026-08-07 00:06:41  flow                    /home/initial  274.962 GiB
---------------------------------------------------------------------------------
Timestamps shown in local time
2 snapshots

keep 5 snapshots:
ID        Time                 Host        Tags        Reasons                  Paths                              Size
------------------------------------------------------------------------------------------------------------------------
d846dc21  2026-07-18 14:27:17  flow                    daily snapshot           /home/initial/.config/restic-tool  552 B
                                                       weekly snapshot
                                                       oldest monthly snapshot
38340bc3  2026-07-21 08:02:25  flow                    daily snapshot           /home/initial/.config/restic-tool  552 B
                                                       weekly snapshot
929fed05  2026-07-28 17:24:41  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
cecc7f98  2026-07-30 13:41:17  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
                                                       weekly snapshot
                                                       monthly snapshot
e90edb6d  2026-08-05 17:34:44  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
                                                       weekly snapshot
                                                       monthly snapshot
------------------------------------------------------------------------------------------------------------------------
Timestamps shown in local time
5 snapshots

[0:00] 100.00%  2 / 2 files deleted
2 snapshots have been removed, running prune
[0:00] 100.00%  17 / 17 index files loaded
loading all snapshots...
finding data that is still in use for 12 snapshots
[0:04] 100.00%  12 / 12 snapshots
searching used packs...
collecting packs for deletion and repacking
[0:00] 100.00%  11744 / 11744 packs processed

to repack:         25813 blobs / 92.757 MiB
this removes:        238 blobs / 3.587 MiB
to delete:             0 blobs / 0 B
total prune:         238 blobs / 3.587 MiB
remaining:        738390 blobs / 194.083 GiB
unused size after prune: 116.472 MiB (0.06% of remaining size)

repacking packs
[0:02] 100.00%  16 / 16 packs repacked
rebuilding index
[0:00] 100.00%  18 / 18 indexes processed
[0:00] 100.00%  7 / 7 old indexes deleted
removing 16 old packs
[0:00] 100.00%  16 / 16 files deleted
done

```

### Second run output example

```bash
repository b93a0b7e opened (version 2, compression level auto)
Applying Policy: keep 7 daily, 4 weekly, 12 monthly snapshots
keep 7 snapshots:
ID        Time                 Host        Tags        Reasons                  Paths          Size
----------------------------------------------------------------------------------------------------------
cfec250e  2026-07-18 14:30:21  flow                    daily snapshot           /home/initial  243.304 GiB
                                                       weekly snapshot
                                                       oldest monthly snapshot
a54a86f9  2026-07-21 23:14:40  flow                    daily snapshot           /home/initial  218.546 GiB
976e96fc  2026-07-22 00:07:49  flow                    daily snapshot           /home/initial  218.546 GiB
                                                       weekly snapshot
d853935b  2026-07-28 17:27:52  flow                    daily snapshot           /home/initial  272.093 GiB
f647986f  2026-07-30 13:42:32  flow                    daily snapshot           /home/initial  272.262 GiB
                                                       weekly snapshot
                                                       monthly snapshot
1e660b7b  2026-08-05 17:41:24  flow                    daily snapshot           /home/initial  273.153 GiB
155aac8e  2026-08-07 00:31:11  flow                    daily snapshot           /home/initial  275.278 GiB
                                                       weekly snapshot
                                                       monthly snapshot
----------------------------------------------------------------------------------------------------------
Timestamps shown in local time
7 snapshots

keep 5 snapshots:
ID        Time                 Host        Tags        Reasons                  Paths                              Size
------------------------------------------------------------------------------------------------------------------------
d846dc21  2026-07-18 14:27:17  flow                    daily snapshot           /home/initial/.config/restic-tool  552 B
                                                       weekly snapshot
                                                       oldest monthly snapshot
38340bc3  2026-07-21 08:02:25  flow                    daily snapshot           /home/initial/.config/restic-tool  552 B
                                                       weekly snapshot
929fed05  2026-07-28 17:24:41  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
cecc7f98  2026-07-30 13:41:17  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
                                                       weekly snapshot
                                                       monthly snapshot
e90edb6d  2026-08-05 17:34:44  flow                    daily snapshot           /home/initial/.config/restic-tool  526 B
                                                       weekly snapshot
                                                       monthly snapshot
------------------------------------------------------------------------------------------------------------------------
Timestamps shown in local time
5 snapshots
```

[Return to the Setup a Keep and Clean Policy section](#setup-a-keep-and-clean-policy)

## Automating backups

Everything above can also happen on its own, on a schedule, with no one at the keyboard. This section sets that up for Linux, macOS, and Windows.

A few things to know before you start:

* **The drive has to actually be there.** An external drive isn't always plugged in, so every scheduled script below checks first and quietly skips the run — instead of failing loudly — if the drive is missing.
* **The drive sometimes needs a nudge.** USB-attached drives can go to sleep or suspend to save power. A quick read of the drive's folder before the backup — what this guide calls "waking it up" — is enough to bring it back before restic tries to use it.
* **One target, one script.** The examples below automate the `flow` / `512GB` target from earlier in this guide. If you back up more than one computer to more than one drive, each machine gets its own copy of the script, pointed at its own target.
* **Backups only cover drives formatted as ext4**, which is Linux-only. If macOS or Windows machines back up to their own external drives, format those drives the way that operating system expects, and build separate targets for them under `~/.config/restic-tool/env/` (or that machine's equivalent config location) — the automation pattern is the same either way.

### Linux: a cron job

#### TO DO

* Confirm and test bin directory location(s) on Linux platforms. Do they consistently use $XDG_BIN_HOME, should this be incorporated into the restic manager tool
* Log location review

#### Create the script:

This script wakes the drive, runs the backup, writes everything to a log in your home directory, and does its weekly housekeeping (`forget` and `check`) — all in one script.

#### 

##### Classic location

The classic location for user script is in ~/bin

```bash
mkdir -p ~/bin
nano ~/bin/restic-auto-backup.sh
```

##### New location

On some (newer) Linux versions the **XDG Base Directory Specification** defines **`$HOME/.local/bin`** as the default location for **user-specific executable files** (when the **`$XDG_BIN_HOME`** environment variable is unset.) 

All this means that  systems and applications that are closely following these changes may place user scripts here

```bash
mkdir -p ~/.local/bin/
nano ~/.local/bin/restic-auto-backup.sh
```

content example

```bash
#!/bin/bash
# Wakes the drive, backs it up, and runs weekly maintenance.
# Logs every run to ~/restic-backup.log

set -uo pipefail

TARGET_ENV="$HOME/.config/restic-tool/env/flow/512GB/env"
EXCLUDES="$HOME/.config/restic-tool/env/flow/512GB/excludes"
RETENTION="$HOME/.config/restic-tool/env/flow/512GB/retention"
MOUNT_PATH="/media/initial/512GB"
LOG="$HOME/restic-backup.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG"
}

log "=== Backup run starting ==="

# Skip quietly if the drive isn't plugged in right now
if [ ! -d "$MOUNT_PATH" ]; then
    log "Drive not found at $MOUNT_PATH — skipping this run."
    exit 0
fi

# Wake the drive up before restic needs it
ls "$MOUNT_PATH" > /dev/null 2>&1

source "$TARGET_ENV"

log "Running backup..."
if restic backup ~ --exclude-file "$EXCLUDES" >> "$LOG" 2>&1; then
    log "Backup finished OK."
else
    log "BACKUP FAILED — see restic's output above for details."
fi

# Housekeeping once a week, on Sundays
if [ "$(date +%u)" -eq 7 ]; then
    log "Sunday — running weekly maintenance..."
    source "$RETENTION"

    if restic forget ${RESTIC_FORGET_OPTS} >> "$LOG" 2>&1; then
        log "Forget/prune finished OK."
    else
        log "FORGET/PRUNE FAILED."
    fi

    if restic check >> "$LOG" 2>&1; then
        log "Check finished OK."
    else
        log "CHECK FAILED."
    fi
fi

log "=== Backup run finished ==="
```

Make it runnable:

```bash
chmod +x ~/bin/restic-auto-backup.sh
```

or 

```bash
chmod +x ~/.local/bin/restic-auto-backup.sh
```

#### Testing

##### Test run

```bash
~/.local/bin/restic-auto-backup.sh
```

##### Log creation confirmation

Have a peek at the log

```bash
cat ~/restic-backup.log
```

###### log content example 

```bash
2026-08-11 08:23:54 === Backup run starting ===
2026-08-11 08:23:54 Running backup...
using parent snapshot 155aac8e
error: open /home/initial/.private/restic/password.txt: permission denied

Files:       23046 new, 11090 changed, 1052649 unmodified
Dirs:         3037 new,  1622 changed, 146903 unmodified
Added to the repository: 1.715 GiB (1.013 GiB stored)

processed 1086785 files, 276.308 GiB in 0:42
snapshot 045726ab saved
Warning: at least one source file could not be read
2026-08-11 08:24:37 BACKUP FAILED — see restic's output above for details.
2026-08-11 08:24:37 === Backup run finished ===
```

#### Add to your crontab

Add it to your crontab, to run every night at 2 AM:

```bash
crontab -e
```

```cron
0 2 * * * /home/initial/bin/restic-auto-backup.sh
```

or

```cron
0 2 * * * /home/initial/.local/bin/bin/restic-auto-backup.sh
```

**Getting notified of problems:** the script writes `BACKUP FAILED`, `FORGET/PRUNE FAILED`, or `CHECK FAILED` into the log whenever something goes wrong, so a quick way to check in is:

```bash
grep FAILED ~/restic-backup.log
```

If your system already has mail set up, cron will email you the script's output on its own once you add a `MAILTO` line above the job in your crontab:

```cron
MAILTO=you@example.com
0 2 * * * /home/initial/bin/restic-auto-backup.sh
```

or

```cron
MAILTO=you@example.com
0 2 * * * /home/initial/.local/bin/restic-auto-backup.sh
```

Without that, get in the habit of glancing at `~/restic-backup.log` — or the monthly `restic check` reminder from [Keeping your backups healthy](#keeping-your-backups-healthy) is a natural time to check it.

### macOS: a launchd agent

#### TO DO

* testing
* directory confirmations  `.local/bin/` or some other directory

#### Create your backup script

macOS can run cron jobs, but Apple's own scheduler, `launchd`, is the supported way — it copes better with the computer sleeping, and it's what `launchctl` is built to manage. External drives on macOS mount under `/Volumes/` instead of `/media/`, so the script only needs that one path changed:

```bash
mkdir -p ~/bin
nano ~/bin/restic-auto-backup.sh
```

```bash
#!/bin/bash
# Wakes the drive, backs it up, and runs weekly maintenance.
# Logs every run to ~/restic-backup.log

set -uo pipefail

TARGET_ENV="$HOME/.config/restic-tool/env/flow/512GB/env"
EXCLUDES="$HOME/.config/restic-tool/env/flow/512GB/excludes"
RETENTION="$HOME/.config/restic-tool/env/flow/512GB/retention"
MOUNT_PATH="/Volumes/512GB"
LOG="$HOME/restic-backup.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG"
}

log "=== Backup run starting ==="

if [ ! -d "$MOUNT_PATH" ]; then
    log "Drive not found at $MOUNT_PATH — skipping this run."
    exit 0
fi

ls "$MOUNT_PATH" > /dev/null 2>&1

source "$TARGET_ENV"

log "Running backup..."
if restic backup ~ --exclude-file "$EXCLUDES" >> "$LOG" 2>&1; then
    log "Backup finished OK."
else
    log "BACKUP FAILED — see restic's output above for details."
fi

if [ "$(date +%u)" -eq 7 ]; then
    log "Sunday — running weekly maintenance..."
    source "$RETENTION"

    if restic forget ${RESTIC_FORGET_OPTS} >> "$LOG" 2>&1; then
        log "Forget/prune finished OK."
    else
        log "FORGET/PRUNE FAILED."
    fi

    if restic check >> "$LOG" 2>&1; then
        log "Check finished OK."
    else
        log "CHECK FAILED."
    fi
fi

log "=== Backup run finished ==="
```

```bash
chmod +x ~/bin/restic-auto-backup.sh
```

Create a launch agent that runs it every day at 2 AM:

```bash
nano ~/Library/LaunchAgents/com.restic-tool.autobackup.plist
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.restic-tool.autobackup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/initial/bin/restic-auto-backup.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/initial/restic-backup-launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/initial/restic-backup-launchd.log</string>
</dict>
</plist>
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.restic-tool.autobackup.plist
```

If the Mac is asleep at 2 AM, `launchd` simply runs the job at the next opportunity rather than catching up a missed run — good enough for a nightly backup, but worth knowing. Check in the same way as Linux:

```bash
grep FAILED ~/restic-backup.log
```

### Windows: Task Scheduler

#### Windows TODO

* Test and confirm documentation

#### Creating the Windows script

On Windows, restic backs up to a drive letter (for example `E:\`) instead of a mount path, and PowerShell stands in for the bash script.

Create the script:

```powershell
notepad $HOME\restic-auto-backup.ps1
```

```powershell
# Wakes the drive, backs it up, and runs weekly maintenance.
# Logs every run to %USERPROFILE%\restic-backup.log

$TargetEnv  = "$HOME\.config\restic-tool\env\flow\512GB\env.ps1"
$Excludes   = "$HOME\.config\restic-tool\env\flow\512GB\excludes.txt"
$Retention  = "$HOME\.config\restic-tool\env\flow\512GB\retention.ps1"
$DriveLetter = "E:\"
$Log        = "$HOME\restic-backup.log"

function Write-Log($msg) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Out-File -Append $Log
}

Write-Log "=== Backup run starting ==="

if (-not (Test-Path $DriveLetter)) {
    Write-Log "Drive not found at $DriveLetter — skipping this run."
    exit 0
}

# Wake the drive up before restic needs it
Get-ChildItem $DriveLetter | Out-Null

. $TargetEnv

Write-Log "Running backup..."
restic backup $HOME --exclude-file $Excludes *>> $Log
if ($LASTEXITCODE -eq 0) {
    Write-Log "Backup finished OK."
} else {
    Write-Log "BACKUP FAILED — see restic's output above for details."
}

# Housekeeping once a week, on Sundays
if ((Get-Date).DayOfWeek -eq 'Sunday') {
    Write-Log "Sunday — running weekly maintenance..."
    . $Retention

    restic forget $env:RESTIC_FORGET_OPTS *>> $Log
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Forget/prune finished OK."
    } else {
        Write-Log "FORGET/PRUNE FAILED."
    }

    restic check *>> $Log
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Check finished OK."
    } else {
        Write-Log "CHECK FAILED."
    }
}

Write-Log "=== Backup run finished ==="
```

`env.ps1` and `retention.ps1` follow the same idea as the Linux `env` and `retention` files, just written as PowerShell (`$env:RESTIC_REPOSITORY = "E:\backups\flow"` and so on) instead of `export` lines.

Then schedule it in Task Scheduler:

1. Open **Task Scheduler** and choose **Create Task…** (not "Basic Task" — it hides the options below).
2. On the **General** tab, tick **Run whether user is logged on or not**.
3. On the **Triggers** tab, add a new trigger: **Daily**, at 2:00 AM.
4. On the **Actions** tab, add **Start a program**:
   * Program: `powershell.exe`
   * Arguments: `-ExecutionPolicy Bypass -File "%USERPROFILE%\restic-auto-backup.ps1"`
5. On the **Conditions** tab, tick **Wake the computer to run this task**.
6. On the **Settings** tab, tick **Run task as soon as possible after a scheduled start is missed** — this covers the laptop-was-off case.

Check in the same way as the other two:

```powershell
Select-String FAILED $HOME\restic-backup.log
```

## Keeping a copy away from home

### Offsite copy

One drive sitting next to your computer can be lost in the same fire, flood, or theft as the computer. So keep a second copy of your backups somewhere else, in online storage, for example. Restic can back up straight to online storage through a helper program called rclone. Your backups stay locked the whole way; the storage company only ever sees scrambled data.

An offsite copy is just another target — give it its own folder under `~/.config/restic-tool/env/`, for example `env/flow/offsite/`, following the same pattern above.

With your files, a local backup drive, and an offsite copy, you have three copies in two kinds of places with one away from home. That is the classic 3-2-1 rule, and it is the finish line.

## Licence

This document, *Backing up your computer with restic*, by **Christopher Steel**, with AI assistance from **Claude (Anthropic)**, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.6.1 | Draft | Tested and detailed Linux cron automated backups and logging. Added To Do section to Linux, macOS and Windows automated backup sections. |
| 0.6.0 | Draft | Added "Automating backups" section, covering scheduled backups and weekly maintenance (forget/check) with logging, for Linux (cron), macOS (launchd), and Windows (Task Scheduler). Each script checks the drive is present and "wakes" it before backing up, and writes a log to the home directory that can be grepped for failures. |
| 0.5.0 | Draft | Added a note under "Configure a backup target" distinguishing operator-owned `env/<host>/<target>/` config from the manager-owned `~/.config/restic-tool/restic-tool.env` (tracks active restic version; never touched by target config). |
| 0.4.0 | Draft | moved roadmap and installer testing documentation out of document |
| 0.3.0 | Draft | Added details and support for multiple host backup configurations and settings |
| 0.1.0 | Draft | First plain-language version of the restic backup guide |
| 0.1.1 | Draft | Reordered into a working document: main procedure separated from installer-tool testing notes (Appendix A); added Dublin Core frontmatter; captured open issues as a Roadmap section |
| 0.1.2 | Draft | Added drive-mount verification (label vs. UUID) and a `chown` step, after a real-world `restic init` failure (`permission denied`) traced to root-owned freshly formatted drives |
| 0.2.0 | Draft | Removed section numbering throughout. Introduced multi-target config schema (`env/<host>/<target>/{env,excludes,retention}`), replacing the single hardcoded `~/.config/restic-tool/env` file. Fixed a path mismatch between the backup-directory creation step and the repository path in the env file. Added an explicit target-activation step (`source .../env`) ahead of every restic command. Removed a duplicated directory-creation section. Backup and retention commands now reference the target's `excludes` and `retention` files instead of inline flags. |
