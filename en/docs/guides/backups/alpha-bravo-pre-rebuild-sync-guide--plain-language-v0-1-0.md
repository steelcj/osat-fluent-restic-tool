# Moving your files safely before wiping a computer

Version: 0.1.0
Status: Draft
Style Guide: plain-language, 7th-grade reading level

## What this guide is for

You have two computers. We call them Alpha and Bravo. Alpha is going to be wiped and rebuilt. Bravo will keep going. Both computers have files on them. Some files are the same. Some are different. Some only live on one computer.

Before you wipe Alpha, every file worth keeping must be safe on Bravo. This guide shows you how to do that without losing anything. One question guides every step: **what could this leave out, and what would that cost?**

## Before you start

Bravo should already have working backups. If it does not, set those up first (see the backup guide). Also, stop editing files on both computers until this job is done. If files keep changing, you cannot check your work.

## Step 1 — Make a safety copy

Before touching anything, make one extra copy of your most important folders. Put it on an external drive. On Bravo, running a fresh backup also works. This copy is your undo button. If anything goes wrong later, you can always come back to it.

## Step 2 — Make a list of every file

On each computer, make a list of all the files. The list should show each file's name, size, and the date it was last changed. The command below does this:

```bash
find /home/user -type f -printf '%P\t%s\t%T@\n' | sort > my-file-list.tsv
```

Save both lists somewhere safe, off both computers.

## Step 3 — Give every file a fingerprint

A checksum is like a fingerprint for a file. Two files with the same fingerprint have exactly the same content, even if their names are different. This command makes a fingerprint for every file:

```bash
cd /home/user
find . -type f -print0 | xargs -0 sha256sum > my-fingerprints.txt
```

Run it on both computers. This can take a while if you have a lot of files. That is normal.

## Step 4 — Sort every file into four groups

Compare the fingerprint lists. Every file lands in one of four groups:

1. **Same on both computers.** Keep one copy. Done.
2. **Only on Alpha.** These must move to Bravo, or they are gone forever when Alpha is wiped.
3. **Only on Bravo.** Already safe. Leave them alone.
4. **Same name, different content.** These are the tricky ones. A person — you — must look at each one and decide which version to keep.

For group 4, the newer file usually wins. If you are not sure, keep both. Rename the extra one so you know where it came from, like `report.alpha-copy.txt`. Never let a program pick the winner for you. That is how the good copy of something gets replaced by the old one.

## Step 5 — Pick one way to organise the files

The two computers organise their folders differently. Pick one layout before you move anything. Using Bravo's layout is usually easiest, because Bravo is the computer that stays. Write down where each Alpha folder will land on Bravo. That list is your map for the next step.

## Step 6 — Practise the move first

The `rsync` program can copy files between computers. It has a practise mode called a dry run. It shows what *would* happen without moving anything:

```bash
rsync --archive --itemize-changes --dry-run \
      alpha:/home/user/docs/ /home/user/Documents/
```

Read the output carefully. If you see a change you did not plan in step 4, stop and figure it out first. Never use the delete option. This job is about gathering files, not removing them.

## Step 7 — Do the move, then check it

Run the same commands without `--dry-run`. Then check your work. Make new fingerprints on Bravo. Every fingerprint that was "only on Alpha" must now show up on Bravo. If one is missing, find that file and copy it again. Also open a few of the moved files to make sure they work.

## Step 8 — Save the small stuff

A rebuild also erases things that are easy to forget: your list of installed programs, settings files, scheduled tasks, and passwords or keys. Save copies of these too, somewhere off Alpha.

## Step 9 — The final checklist

Only wipe Alpha when every box is ticked:

- [ ] Every "only on Alpha" fingerprint now shows up on Bravo
- [ ] You personally decided every group 4 conflict
- [ ] Your step 1 safety copy still exists and opens
- [ ] The small stuff from step 8 is saved off Alpha
- [ ] Bravo was backed up again *after* the move
- [ ] You worked normally on Bravo for a day or two and nothing turned up missing

That waiting period matters. A day of normal work often reminds you of the one folder everyone forgot.

## Common mistakes

Hidden folders (names starting with a dot) get skipped easily — make sure they are in your lists. Do not trust file dates alone; computer clocks can disagree, and fingerprints do not lie. And watch out for drives formatted for Windows or Mac: some of them treat `Notes.txt` and `notes.txt` as the same file and quietly overwrite one with the other.

## License

This document, *Moving your files safely before wiping a computer*, by **Christopher Steel**, with AI assistance from **Claude (Anthropic)**, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.1.0 | Draft | First plain-language version of the Alpha–Bravo sync guide |
