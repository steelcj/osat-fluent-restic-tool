---
dc:title: "Proposed Changes: Better Repository Support for Backup Automation"
dcterms:version: "0.1.0"
dc:creator: "Christopher Steel"
dc:contributor: "Claude (Anthropic) — drafting assistance"
dc:description: "Reviews release v0.4.1, which added and then tested an 'Automating backups' section in the backup guide, and proposes changes to the osat-fluent-restic-tool repository so backup automation is supported by the tool itself rather than hand-authored three times over in documentation."
dcterms:created: "2026-08-11"
dcterms:modified: "2026-08-11"
dc:format: "text/markdown"
dc:language: "en"
sat:language_bcp47: "en"
dc:identifier: "proposed-changes--backup-automation-support"
dcterms:rightsHolder: "Christopher Steel"
dc:rights: >
  Copyright 2026 Christopher Steel.
  SPDX-License-Identifier: AGPL-3.0-or-later
dc:relation: "https://github.com/steelcj/osat-fluent-restic-tool/releases/tag/v0.4.1"
sat:uuid: ""
sat:version_at_creation: "0.4.1"
sat:migration_status: pre-sat
sat:changelog:
  - version: "0.1.0"
    date: "2026-08-11"
    author: "Christopher Steel"
    notes: "Initial draft, written against release v0.4.1 and the testing notes left in restic-backup-guide--backup-to-external-drive-v0-6-1.md."
---

# Proposed Changes: Better Repository Support for Backup Automation

Version: 0.1.0
Status: Draft
Style Guide: style-guide--versioned-documents-in-unrendered-markdown

## Context

Release [v0.4.1](https://github.com/steelcj/osat-fluent-restic-tool/releases/tag/v0.4.1) added an "Automating backups" section to the backup guide (v0.6.0), then tested and refined the Linux path against a real machine (v0.6.1). That testing pass is valuable on its own, and it also did what testing is supposed to do, it surfaced real friction that a documentation fix alone will not close. This document proposes changes to the repository itself, not just the guide, so that backup automation is something the tool supports, rather than something three parallel hand-written shell scripts approximate.

ROADMAP.md already names this gap under "Later": a "Companion configuration layer" for backup policy, schedule, and retention, kept deliberately outside the manager's own ownership of which restic binary is active. This proposal does not challenge that boundary. It argues that the shape of the companion layer is now known well enough, from lived testing rather than speculation, to move it up the roadmap and start scoping it concretely.

## What testing surfaced

The v0.6.1 changes and TO DO notes point at five concrete problems, all of which live in the guide today because the tool has nowhere for them to live instead.

**Restic's partial-success exit code is reported as a hard failure.** The v0.6.1 test run log shows a backup that read most files, hit a permission-denied error on one excluded path, and still completed and saved a snapshot, then the wrapping script logged it as `BACKUP FAILED`. Restic's own exit codes distinguish a fully clean run, a fatal error, and a completed run with some unreadable source files, but the guide's script (copied identically across Linux, macOS, and Windows) treats any non-zero exit the same way. Left as is, this trains whoever reads the log to expect `FAILED` on a routine, correctly-excluded permission error, which is exactly the alarm-fatigue failure mode that makes real failures easy to miss.

**Script location is ambiguous, and the ambiguity already produced a bug.** The Linux section now documents two locations, the "classic" `~/bin` and the newer XDG `~/.local/bin`, and asks whether `install-restic.py` should standardize on one. The manager already answers this question for its own wrapper, which lives at `~/.local/bin/restic` per the Filesystem layout in README.md, but the guide does not point at that precedent. One of the two crontab examples added in this pass reads `/home/initial/.local/bin/bin/restic-auto-backup.sh`, a doubled `bin` segment, which is the kind of copy-paste error that having one documented location would have prevented.

**The same automation logic is now hand-authored three times and already drifting.** The Linux, macOS, and Windows scripts in the guide share their shape, wake the drive, source the target, back up, run weekly maintenance, log every step, but they are three independent documents, not one implementation. The Windows script dot-sources `retention.ps1` and then reads `$env:RESTIC_FORGET_OPTS`, but nothing in the guide has `retention.ps1` write to `$env:`, so on Windows that variable will not survive the dot-source the way the equivalent `source` does in bash. That is a real bug, introduced by maintaining parity across three files by hand rather than generating three outputs from one description.

**Nothing bounds the log the scripts write.** Every script appends full restic output, including a line per unreadable file, to `~/restic-backup.log` forever. For a large home directory backed up nightly, that file grows without limit. Automation that quietly grows an unbounded file in the home directory is not a finished feature.

**"Waking the drive" is a documentation heuristic, not something the tool can help with.** The guide's `ls "$MOUNT_PATH"` nudge is a reasonable default, but it only works once the operating system has already remounted the drive; it cannot detect a drive that is present but genuinely suspended at the block level, and there is no way for a reader to know whether it worked short of trying a backup and watching the log.

## Proposed changes

**Add a companion automation script that the manager generates, not one the guide asks the reader to type.** A single implementation, parameterized by host and target the way `env`, `excludes`, and `retention` already are, removes the three-way drift described above by construction. This is the concrete shape of the "Companion configuration layer" ROADMAP item, and matches the manager's existing pattern: it does not own backup policy, it generates the plumbing that reads the operator's existing `env/<host>/<target>/` files and runs them on a schedule.

**Fix the exit-code handling as its own change, ahead of the companion script.** Restic's exit codes already distinguish a clean run from a run that completed with some source files unreadable from a fatal error; the fix is to log those cases distinctly, for example `Backup finished OK`, `Backup finished with warnings (see restic output above)`, and `BACKUP FAILED`, and to reserve `FAILED` for the case that actually needs attention. This is small enough to land in the guide immediately, independent of when the companion script exists, and worth confirming against the exit codes of each restic version this tool currently manages, since the meaning of exit code 3 is a relatively recent addition upstream.

**Standardize automation scripts on `~/.local/bin`, matching the wrapper's own location.** The manager already made this choice for `restic` itself; extending the same answer to operator automation scripts removes a documented ambiguity and the class of error it already produced, and needs no new convention, only consistency with one that exists.

**Fix the Windows retention-sourcing bug directly.** `retention.ps1` needs to set `$env:RESTIC_FORGET_OPTS`, not a plain script-scoped `$RESTIC_FORGET_OPTS`, for the value to be visible after dot-sourcing. Worth flagging as a general pattern: any PowerShell equivalent of the Linux `export` files needs to write to `$env:`, not a bare variable, or it will silently fail to cross the same boundary the Linux scripts cross for free.

**Bound the automation log.** Either rotate `~/restic-backup.log` on size or date, or move it under `~/.local/state/restic-tool/`, the state directory the manager's own filesystem layout already reserves, with a simple retained-lines or retained-days cap. Either is a small addition once a companion script exists to own the logging in one place instead of three.

**Promote "Companion configuration layer" from ROADMAP's "Later" section to "Near term."** The item was written before this repository had exercised backup automation on real hardware. It now has, and the exit-code bug, the location ambiguity, and the Windows scoping bug are concrete evidence that hand-authored, per-reader automation is not a durable substitute for a generated one.

## Out of scope for this proposal

Hardware validation of macOS and Windows automation, already tracked in ROADMAP.md's "Near term" section, is unaffected by this proposal and should continue on its own schedule. Unrelated ROADMAP items, optional GPG verification and archive pruning among them, are not addressed here.

## Suggested sequencing

The exit-code fix and the `~/.local/bin` standardization are documentation-only changes and can land in the guide immediately, ahead of any code work. The Windows retention-sourcing bug should be corrected in the guide at the same time, since it is currently the only place that bug exists. The companion automation script is the larger piece of work and depends on deciding its exact interface, likely a new `install-restic.py` mode or a small sibling script, which is a design discussion of its own rather than something to settle inside this proposal.

## License

This document, *Proposed Changes: Better Repository Support for Backup Automation*, by **Christopher Steel**, with AI assistance from **Claude (Anthropic)**, is licensed under the [GNU Affero General Public License v3.0 or later](https://www.gnu.org/licenses/agpl-3.0.html).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.1.0 | Draft | Initial draft, written against release v0.4.1 and the testing notes left in restic-backup-guide--backup-to-external-drive-v0-6-1.md. |
