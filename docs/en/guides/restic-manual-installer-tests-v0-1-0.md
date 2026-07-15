# restic-manual-installer-tests-v0-1-0

Version: 0.1.0
Status: Draft
Style Guide: plain-language, 7th-grade reading level

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

## Step 1- Install restic

We install restic with our own installer tool. The installer checks that the download is genuine and that the program runs before it accepts it. It also keeps a spare copy, so you can reinstall later even without internet.

```bash
python3 install-restic.py --install
restic version
```

If the second command prints a version number, restic is ready.

## Step 2- Get the drive ready

Backups will live on an external drive. The drive should use the Linux format called ext4. Formatting erases the drive, so make sure it is the right one:

```bash
lsblk -f                                    # find the drive
sudo mkfs.ext4 -L bravo-backup /dev/sdX1    # format it (replace sdX1!)
```

Give it a clear label like `bravo-backup` so you always know what it is.

## Step 3 - Make a password and never lose it

Restic locks every backup with a password. Make a strong one and save it into a protected folder:

```bash
( umask 077 && openssl rand -base64 32 > ~/.private/restic-tool/password.txt )
```

Confirm:

password.txt content

```bash
cat ~/.private/restic-tool/password.txt

```

### Permissions

```bash
ls -al ~/.private/ | grep restic
```

output example:

```bash
drwxr-xr-x  2 root    root      4096 Jun 24 20:28 restic
drwx------  2 initial initial   4096 Jul 15 10:22 restic-tool
```

the file:

```bash
ls -al ~/.private/restic
```

output:

```bash
-rw-------  1 root    root      26 Jun 24 20:28 password.txt
```

#### Results

***WARNING*** Notice in the above output that the owner of our password.txt file root! Depending on your setup and what areas of your system you are going to backing up (allowing access tot) you may or may not want to be running things as root...

### Record your password in a secure password manager

 **This is the most important step in this whole guide.**

**second most important thing** - the command below has a space at the beginning of our cat command in order to avoid recording 

```bash
 cat ~/.private/restic-tool/password.txt
```

Now write that password down in two more places: your password manager, and somewhere offline, like a paper note in a safe spot. If you lose the password, nobody on Earth can open your backups. Not even you.

## Step 4 - Tell restic where things are

Create a small settings file at `~/.config/restic-tool/env` with these two lines:

```sh
export RESTIC_REPOSITORY="/media/user/bravo-backup/restic-repo"
export RESTIC_PASSWORD_FILE="$HOME/.private/restic-tool/password.txt"
```

The first line says where the backups go. The second says where the password lives. After this, restic finds both on its own every time.

## Step 5 - Start the backup vault and test it

```bash
restic init
```

This creates the vault (restic calls it a repository). Now do a tiny test backup, look at it, and check it:

```bash
restic backup ~/.config/restic-tool
restic snapshots
restic check
```

If `check` says everything is fine, do your first real backup:

```bash
restic backup ~ --exclude ~/.cache
```

The `--exclude` part skips junk folders that nobody needs to keep.

## Step 6 - Prove you can get files back

A backup only counts if you can restore from it. Try it now with one file:

```bash
restic restore latest --target /tmp/restore-test --include ~/Documents/somefile
```

Open the restored file. If it works, your safety net is real.

## Step 7 - Keep it healthy

Backups pile up over time. Once in a while, tell restic to keep the recent ones and clear out the very old ones:

```bash
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune
```

That keeps a backup a day for a week, one a week for a month, and one a month for a year.

Also put two reminders in your calendar:

1. **Once a month:** run `restic check`.
2. **Every three months:** restore a file or two, and open them.

These two habits are what make this setup better than the old tools. Problems get caught early, while they are still small.

## Step 8 - Keep a copy away from home

One drive sitting next to your computer can be lost in the same fire, flood, or theft as the computer. So keep a second copy of your backups somewhere else, in online storage, for example. Restic can back up straight to online storage through a helper program called rclone. Your backups stay locked the whole way; the storage company only ever sees scrambled data.

With your files, a local backup drive, and an offsite copy, you have three copies in two kinds of places with one away from home. That is the classic 3-2-1 rule, and it is the finish line.

## License

This document, *Backing up your computer with restic*, by **Christopher Steel**, with AI assistance from **Claude (Anthropic)**, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.1.0 | Draft | First plain-language version of the restic backup guide |
