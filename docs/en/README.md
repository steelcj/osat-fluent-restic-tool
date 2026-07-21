# osat-fluent-restic-tool

Version: 0.3.0
Status: Draft
Style Guide: style-guide--technical-documentation-for-technologists v0.2.0

## Abstract

This document describes `osat-fluent-restic-tool`, the OSAT Fluent manager for [restic](https://restic.net/), the encrypted, deduplicating backup program by Alexander Neumann and the restic contributors. restic is a canonical Archetype 5 tool — a single statically linked Go binary distributed via GitHub Releases with published SHA-256 checksums — so acquisition follows the archetype without deviation. The manager combines that acquisition pattern with the fluent lifecycle (install, switch, status, remove) and archive-first resolution, and it supersedes the pre-fluent [restic-tool](https://github.com/steelcj/restic-tool).

## What this manager does

`install-restic.py` owns the full installation lifecycle: acquire, verify, place, archive, activate, switch, inspect, remove. It is a manager, not an installer. The artifact is a single restic binary accompanied by a `PROVENANCE` file recording the release asset name, its SHA-256, the source it came from, and the install time. Versions sit side by side; exactly one is active at a time, selected by an env file the wrapper sources at runtime.

The manager never touches restic's own runtime domain: `~/.config/restic/`, `~/.cache/restic/`, repositories, password files, or any operator configuration. Backup policy — what to back up, where, on what schedule, with what retention — is deliberately outside this manager's ownership and belongs to a separate configuration layer.

## Filesystem layout

```text
~/.local/share/restic-tool/
  0.19.1/                   installed binary and PROVENANCE
  0.18.1/                   versions sit side by side
  archive/
    0.19.1/restic           verified binaries, permanent local archive
    0.18.1/restic

~/.config/restic-tool/
  restic-tool.env           RESTIC_TOOL_ROOT="$HOME/.local/share/restic-tool/0.19.1"
  env                       operator environment — never touched by the manager

~/.local/state/restic-tool/ manager state
~/.private/restic-tool/     credential directory, created 700, never populated
~/.local/bin/
  restic                    generated wrapper
```

All manager-owned paths carry the `restic-tool` management identifier per the collection's ownership convention (specification section 10.8). The plain name `restic` is reserved for the tool's own runtime domain and the wrapper command. Every manager-owned path is owner-only — `700` for directories and executables, `600` for files — set on creation and verified on every subsequent run; a pre-existing path found broader than specified fails the run explicitly.

On Windows the same layout translates to `%LOCALAPPDATA%\restic-tool\`, `%APPDATA%\restic-tool\`, `%LOCALAPPDATA%\Programs\restic.cmd` and `restic.ps1`, and `%USERPROFILE%\.private\restic-tool\`, per the platform translation table in the installation specification.

## Acquisition and verification

Upstream publishes single-binary release assets named `restic_<version>_<os>_<arch>.bz2` on Linux and macOS (a compressed single file, not a tarball) and `.zip` on Windows, with a two-column `SHA256SUMS` file alongside each release. Acquisition downloads the asset and the checksums file, verifies the asset's SHA-256 against the published value before anything touches the filesystem, extracts the binary, and — no claim without a verification behind it — proves the extracted binary executes and reports the requested version *before* it enters the archive or the install root. A placed artifact that fails its health check is removed, never left where a later `--switch` could activate it (the refuse-and-remove rule, adopted from osat-fluent-sat-tool's declared-versus-actual tripwire).

`--install` with no argument queries the GitHub Releases API for the latest stable version. `--install VERSION` constructs the download URL directly and never touches the API — pinned installs work even when the API is rate-limited or unreachable, which suits both sovereignty and the reality of shared egress addresses.

## Archive-first resolution

After verification, every binary is copied to `~/.local/share/restic-tool/archive/<version>/` before being placed at the versioned install path. The archive is not a cache; it is a permanent record of every verified install. On any subsequent `--install` of an archived version, the manager restores from the archive with no network request. `--remove` deletes an installed version but leaves its archive copy, so rollback remains possible offline indefinitely.

For a backup tool this property is not cosmetic. A restic repository must be read by a restic version that understands the repository format that wrote it, and the moment you most need to reinstall a specific version is a bare-metal recovery — precisely when assuming network access, a live GitHub, or an intact package mirror is unwise. The archive directory is itself a worthwhile item to include in what gets backed up.

## The two env files

The wrapper sources two files from `~/.config/restic-tool/`, in order, skipping either silently if absent:

`restic-tool.env` is the manager's. It contains one value, `RESTIC_TOOL_ROOT`, pointing at the active version. It is regenerated on every `--install` and `--switch` and should never be edited by hand.

`env` is the operator's. It is never created, read, or modified by the manager, and it is where restic's own environment belongs:

```sh
export RESTIC_REPOSITORY="/media/user/backup-drive/restic-repo"
export RESTIC_PASSWORD_FILE="$HOME/.private/restic-tool/password.txt"
```

The split exists because the myrepos-tool single-env-file design and the specification's user-created env file (section 6) are answering different questions — "which version is active" versus "how is the tool configured" — and merging them would force the manager to preserve operator content through regeneration. Two files with two owners is simpler and keeps the ownership boundary legible: the manager regenerates its file freely; the operator's file is sovereign territory.

The wrapper additionally exports `RESTIC_TOOL_ROOT`, so scripts and scheduled jobs can reference a version-stable path to the active binary if they need to bypass the wrapper.

## Provenance headers

Templates and the files rendered from them carry the file-identity convention established in osat-fluent-sat-tool: a template declares its own `source` (project and path) and what it `generates`; the written wrapper records `generated` with concrete values only, stamped with its maker (`by: install-restic.py`). An operator inspecting `~/.local/bin/restic` — or `%LOCALAPPDATA%\Programs\restic.cmd` — reads directly what made the file, from which template, and that hand edits will not survive. The convention is carried in all three wrapper syntaxes (`#` for sh and PowerShell, `rem` for cmd).

## Platform support

Linux (x86_64, aarch64) and macOS (Intel x86_64, Apple Silicon arm64) use the POSIX wrapper; Linux x86_64 is validated end to end. Windows (x86_64) is mapped in `ASSET_PLATFORMS` and, unlike sat-tool — whose Windows path is blocked upstream on bash dispatchers — restic ships a native `restic.exe`, making this the collection's natural vehicle for proving the fluent conventions on Windows.

Everything on the Windows path that does not require a Windows kernel is validated by `validate-windows.py`, a simulated-Windows harness that monkeypatches the platform and exercises path resolution (`%LOCALAPPDATA%`, `%APPDATA%`, `Programs`, `.private`), env file writing with correct CRLF line endings, the `generates → generated` header transformation in both cmd and PowerShell syntax, the active-version round-trip through `restic-tool.env.cmd`, idempotency detection, and version listing. The harness caught a real defect on first use: v0.1.0 embedded `\r\n` in text-mode writes, which Windows would have rendered as `\r\r\n`. What remains is hardware-only: `restic.exe` execution through the wrappers, NTFS ACL verification (POSIX modes are advisory on Windows; ACLs currently inherit owner-only from the profile), and PATH resolution semantics for `%LOCALAPPDATA%\Programs\`.

## Usage

```bash
python3 install-restic.py --install            # install the latest stable release
python3 install-restic.py --install 0.19.1     # install a pinned version (no API call)
python3 install-restic.py --switch 0.18.1      # activate an installed version
python3 install-restic.py --status             # show installed, archived, and active versions
python3 install-restic.py --remove 0.18.1      # remove a non-active version (archive kept)
python3 install-restic.py --version            # show this manager's version
```

`--install` of an already-installed version activates it; of an archived version, restores it offline. `--remove` refuses to remove the active version; switch first. The manager refuses to run as root and warns when the wrapper directory is not on `PATH` or when another restic installation shadows the wrapper.

## Migrating from restic-tool

The superseded restic-tool installed to the pre-fluent layout: binary at `~/bin/restic-tool/<version>/restic`, wrapper at `~/bin/restic` with the version baked in. Migration is an install-then-remove, per the collection's migration guide:

1. Run `python3 install-restic.py --install <version>` for each version worth keeping — the same binaries download and verify identically, or copy is unnecessary if re-downloading is acceptable.
2. Confirm `restic version` resolves through `~/.local/bin/restic` (check with `command -v restic`; remove or reorder `~/bin` in `PATH` if it wins).
3. Delete `~/bin/restic` and `~/bin/restic-tool/`.

Nothing in restic's runtime domain — repositories, `~/.config/restic/`, cache, credentials — is affected by the migration; only the manager's own artifacts move.

## Decisions and rationale

**Why the fluent lifecycle plus archetype 5 acquisition.** The archetype 5 pattern document defines acquisition, verification, extraction, health check, and archive for GitHub-released binaries but predates the manager lifecycle established in osat-fluent-myrepos-tool (install, switch, status, remove, env-pointer activation). This tool synthesises the two: archetype 5 supplies how binaries are acquired and trusted; the fluent lifecycle supplies how versions are owned and activated. Feeding this synthesis back into the governance specification is a ROADMAP item, alongside the equivalent note in myrepos-tool.

**Why the env-pointer wrapper rather than a version-baked wrapper.** The superseded restic-tool baked the version into the wrapper at render time, so changing versions meant rewriting the wrapper. The fluent env-pointer makes `--switch` a one-file write, keeps the wrapper static and legible, and gives scheduled jobs a stable sourcing point. A symlink was rejected for the reasons recorded in the archetype document: it cannot source an env file and does not behave uniformly on Windows.

**Why the archive survives --remove.** Removal expresses "I do not want this version active or occupying the install root," not "destroy the evidence this version was ever verified." The archive is the resilience layer and the provenance record; deleting it should be a deliberate manual act, not a side effect.

**Why pinned installs skip the API.** The GitHub Releases API is rate-limited per source address and is a availability dependency the download URLs themselves do not share. Since the asset URL is fully determined by the version string, requiring the API for pinned installs would add a failure mode for no information gained. Only "what is the latest version" genuinely requires the API.

**Why the archive holds only proven binaries.** v0.1.0 archived after checksum verification but before execution; v0.2.0 moves the health check ahead of archiving. The archive is the layer trusted during a bare-metal recovery, so its admission standard must be the strictest in the pipeline: checksum-verified *and* proven to execute and report its version. A checksum match on a binary that cannot run is provenance without utility.

**Why this repo carries the release pipeline.** `bump-version.py` here is the sat `--release` ceremony (bump → changelog row → surgical commit → HEAD guard → annotated tag → tag guard, push kept deliberate), adapted only in its repository-configuration block: the `Version:` line pattern, the two versioned documents, and the three-column changelog row. The sat-tool ROADMAP promotes the pipeline to governance "once proven across tools"; this adoption is that proof in progress. The v0.2.0 release of this repository was itself cut with the pipeline.

**Why GPG verification is deferred.** Upstream signs releases, but verifying signatures requires a `gpg` binary and trusted-key management that a stdlib-only, no-prerequisite installer cannot assume. SHA-256 verification against the published SHA256SUMS is performed unconditionally; optional GPG verification when `gpg` is present, with a pinned key fingerprint in this repository, is a ROADMAP item.

## License

This document, *osat-fluent-restic-tool*, by **Christopher Steel**, with AI assistance from **Claude (Anthropic)**, is licensed under the [GNU General Public License v3.0 or later](https://www.gnu.org/licenses/gpl-3.0.html).

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.3.0 | Draft | updated and tested guide and dev docs, testing automated release|
| 0.2.1 | Draft | Shared wrapper directory (~/.local/bin, %LOCALAPPDATA%\Programs) exempted from owner-only enforcement — the manager owns the wrapper file, never the shared directory; failure reported on first production install against a 775 ~/.local/bin. Share-dir permission verification extended to the activation path |
| 0.2.0 | Draft | Adopted the proven sat-tool approaches: source/generates/generated provenance headers in all three wrapper syntaxes with by: stamp; refuse-and-remove for artifacts failing their health check; archive admission tightened to checksum-verified and execution-proven binaries only; CRLF-explicit writing for all Windows-rendered files (fixing a v0.1.0 defect that would have produced CRCRLF); sat-style release pipeline adopted as bump-version.py; simulated-Windows harness (validate-windows.py) validating every kernel-independent Windows code path, 25 checks passing |
| 0.1.0 | Draft | Initial scaffold: fluent manager with install, switch, status, remove lifecycle; archetype 5 acquisition with SHA-256 verification; archive-first resolution; PROVENANCE recording; two-env-file split (manager pointer, operator environment); owner-only permissions set on creation and verified thereafter; validated on Linux x86_64 against restic 0.19.1 and 0.18.1 including offline archive restore |
