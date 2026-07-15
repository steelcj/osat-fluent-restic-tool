# Backing up your computer with restic

Version: 0.1.0
Status: Draft
Style Guide: plain-language, 7th-grade reading level

## Why restic

A backup program you cannot trust is worse than no backup at all, because it makes you feel safe when you are not. Some older backup tools store backups as a long chain. If one link in the chain breaks, everything after it is lost — and you find out on the worst possible day, when you need your files back.

Restic works differently. Every backup stands on its own. If something ever goes wrong, restic can tell you *right away* when you ask it to check. It also locks your backups with a password so nobody else can read them.

## Step 1 — Install restic

We install restic with our own installer tool. The installer checks that the download is genuine and that the program runs before it accepts it. It also keeps a spare copy, so you can reinstall later even without internet.

```bash
python3 install-restic.py --install
restic version
```

If the second command prints a version number, restic is ready.

## Step 2 — Get the drive ready

Backups will live on an external drive. The drive should use the Linux format called ext4. Formatting erases the drive, so make sure it is the right one:

```bash
lsblk -f                                    # find the drive
sudo mkfs.ext4 -L bravo-backup /dev/sdX1    # format it (replace sdX1!)
```

Give it a clear label like `bravo-backup` so you always know what it is.

## Step 3 — Make a password and never lose it

Restic locks every backup with a password. Make a strong one and save it into a protected folder:

```bash
( umask 077 && openssl rand -base64 32 > ~/.private/restic-tool/password.txt )
```

Now write that password down in two more places: your password manager, and somewhere offline, like a paper note in a safe spot. **This is the most important step in this whole guide.** If you lose the password, nobody on Earth can open your backups. Not even you.

## Step 4 — Tell restic where things are

Create a small settings file at `~/.config/restic-tool/env` with these two lines:

```sh
export RESTIC_REPOSITORY="/media/user/bravo-backup/restic-repo"
export RESTIC_PASSWORD_FILE="$HOME/.private/restic-tool/password.txt"
```

The first line says where the backups go. The second says where the password lives. After this, restic finds both on its own every time.

## Step 5 — Start the backup vault and test it

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

## Step 6 — Prove you can get files back

A backup only counts if you can restore from it. Try it now with one file:

```bash
restic restore latest --target /tmp/restore-test --include ~/Documents/somefile
```

Open the restored file. If it works, your safety net is real.

## Step 7 — Keep it healthy

Backups pile up over time. Once in a while, tell restic to keep the recent ones and clear out the very old ones:

```bash
restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune
```

That keeps a backup a day for a week, one a week for a month, and one a month for a year.

Also put two reminders in your calendar:

1. **Once a month:** run `restic check`.
2. **Every three months:** restore a file or two, and open them.

These two habits are what make this setup better than the old tools. Problems get caught early, while they are still small.

## Step 8 — Keep a copy away from home

One drive sitting next to your computer can be lost in the same fire, flood, or theft as the computer. So keep a second copy of your backups somewhere else — in online storage, for example. Restic can back up straight to online storage through a helper program called rclone. Your backups stay locked the whole way; the storage company only ever sees scrambled data.

With your files, a local backup drive, and an offsite copy, you have three copies in two kinds of places with one away from home. That is the classic 3-2-1 rule, and it is the finish line.

## License

This document, *Backing up your computer with restic*, by **Christopher Steel**, with AI assistance from **Claude (Anthropic)**, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.1.0 | Draft | First plain-language version of the restic backup guide |
