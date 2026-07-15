# Alpha–Bravo pre-rebuild synchronisation guide

Version: 0.1.0
Status: Draft
Style Guide: style-guide--technical-documentation-for-technologists v0.2.0

## Abstract

This guide describes the reconciliation of user files held on two systems — Alpha, due for rebuild, and Bravo, the surviving system — where the two have drifted apart in directory structure and contents. The outcome is a single canonical, checksum-verified file set on Bravo, backed up before Alpha is wiped. The guiding question throughout: what does this process leave out, and at what cost?

## Preconditions

Both systems run a Unix-like operating system with shell access and can reach each other over SSH or a common intermediate (external drive, NAS, or cloud remote). Bravo runs restic with a verified repository (see the companion restic backup guide); the first full Bravo backup exists before this process begins, so the consolidation lands on a system already protected. Editing is frozen on both systems for the duration — a moving target defeats checksum comparison.

## Step 1 — Safety snapshot

Take a read-only snapshot on any snapshot-capable filesystem (`zfs snapshot tank/home@pre-rebuild`), or make a one-time raw copy of the most irreplaceable directories to external media. On Bravo, a fresh restic snapshot serves. This is the undo button; every later step assumes it exists.

## Step 2 — Inventory

Produce comparable listings from both systems, capturing relative path, size, and modification time:

```bash
find /home/user -type f -printf '%P\t%s\t%T@\n' | sort > $(hostname)-inventory.tsv
```

`%P` yields paths relative to the starting point, keeping the inventories comparable despite differing absolute layouts. Prune cache and ephemeral directories early. Store both inventories off the systems being compared.

## Step 3 — Checksum manifests

Sizes and timestamps identify candidates; checksums settle arguments:

```bash
cd /home/user
find . -type f -print0 | xargs -0 sha256sum > /tmp/$(hostname)-manifest.sha256
```

For very large collections, hash the size-matched subset first — that is where the conflicts live.

## Step 4 — Classification

Every file across both systems falls into exactly one of four classes: identical content in either location (keep one copy); only on Alpha (must transfer or it dies with the rebuild); only on Bravo (already safe); and same path or name with different content — the conflict class, which requires human judgement.

```bash
cut -d' ' -f1 alpha-manifest.sha256 | sort > alpha-hashes.txt
cut -d' ' -f1 bravo-manifest.sha256 | sort > bravo-hashes.txt
comm -23 alpha-hashes.txt bravo-hashes.txt > only-on-alpha-hashes.txt
```

Resolve conflicts by modification time where edits are clearly forward progress, by keeping both versions (loser renamed `filename.alpha-2026-07-15.ext`) where authority is unclear, or by merging text under version control. Never let a sync tool resolve the conflict class automatically in one direction.

## Step 5 — Canonical structure

Choose the surviving layout before moving anything: adopt Bravo's structure (least movement), a fresh structure (reorganise only *after* the sync verifies, never during), or Alpha's (only if clearly superior). Record the decision as a mapping table (`Alpha:~/docs/projects → Bravo:~/Projects/active`); it drives the sync commands and becomes provenance.

## Step 6 — Dry run

Express the plan as rsync commands and rehearse:

```bash
rsync --archive --itemize-changes --dry-run \
      --backup --backup-dir=/home/user/.sync-conflicts/ \
      alpha:/home/user/docs/projects/ /home/user/Projects/active/
```

Read the itemised output line by line. No `--delete` — deletion has no place in a consolidation. Any update not consciously decided in step 4 stops the process until resolved.

## Step 7 — Execute and verify

Run the rehearsed commands without `--dry-run`, then verify independently: re-hash the canonical set on Bravo and confirm every checksum in `only-on-alpha-hashes.txt` appears in the post-sync manifest. This single check proves nothing unique to Alpha was left behind. Spot-check a sample of transferred files by opening them — checksums prove bit-identity, not usability. Any missing hash is traced (`grep <hash> alpha-manifest.sha256`), explained, and re-synced.

## Step 8 — System-level extras

Capture what a rebuild erases cheaply: package selections, dotfiles not under version control, crontabs and systemd units, SSH and GPG keys (handled with care), and a copy of the mapping table and manifests — the provenance record of the consolidated set. Store off Alpha.

## Step 9 — The gate

Alpha becomes safe to wipe only when every item holds: the step 7 verification passed in full; conflict resolutions were reviewed by a human; the safety snapshot still exists and is readable; system extras are captured off Alpha; Bravo has been backed up *after* the sync (a restic snapshot, giving the consolidated set its second copy); and Alpha has sat untouched through a cooling-off period of normal work on Bravo — a day or two often surfaces the directory everyone forgot.

## Failure modes to watch

Hidden directories skipped by glob patterns; hard links and sparse files without `--hard-links --sparse`; filename encoding differences masquerading as missing files (byte-level tools are resilient, visual diffing is not); clock skew making the stale copy look newer (checksums beat timestamps); and case-insensitive intermediate filesystems silently collapsing `Notes.md` and `notes.md`.

## License

This document, *Alpha–Bravo pre-rebuild synchronisation guide*, by **Christopher Steel**, with AI assistance from **Claude (Anthropic)**, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.1.0 | Draft | Initial guide, adapted from the standalone pre-rebuild sync document; preconditions updated to assume a verified restic repository on Bravo |
