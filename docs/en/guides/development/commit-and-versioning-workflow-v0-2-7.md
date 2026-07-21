# Commit and versioning workflow

```yaml
version: 0.2.3
status: Draft
file: commit-and-versioning-workflow-v0-2-3.md
```

## Status Confirmation

Examine the current state of the repository. Do any required cleanup and adjust .gitignore if required

```bash
git status
```

## Committing work

Work commits and release commits are different acts. Work commits carry content changes and never touch `VERSION`. The release commit (below) carries `VERSION` and the changelog and nothing else. If `git status` shows `VERSION` as modified during a work commit, a previous release was left half-done — finish the release first.

```bash
git add .
git status
```

git status output example

```bash
	modified:   README.md
	new file:   en/lib/satlib/satlib/archive.py
	new file:   en/lib/satlib/tests/test_archive.py
```

Reuse the `git status` output directly in the commit body rather than paraphrasing:

```bash
git commit -m "	renamed:    docs/en/notes/ROADMAP.md -> docs/en/ROADMAP.md
	deleted:    docs/en/guides/alpha-bravo-pre-rebuild-sync-guide-v0-1-0.md
	renamed:    docs/en/guides/alpha-bravo-pre-rebuild-sync-guide--plain-language-v0-1-0.md -> docs/en/guides/backups/alpha-bravo-pre-rebuild-sync-guide--plain-language-v0-1-0.md
	new file:   docs/en/guides/backups/restic-backup-guide--backup-to-external-drive-v0-4-0.md
	new file:   docs/en/guides/development/appendix-a-testing-the-osat-fluent-restic-tool-installer.md
	renamed:    docs/en/guides/commit-and-versioning-workflow-v0-2-5.md -> docs/en/guides/development/commit-and-versioning-workflow-v0-2-5.md
	renamed:    docs/en/guides/commit-and-versioning-workflow-v0-2-6.md -> docs/en/guides/development/commit-and-versioning-workflow-v0-2-6.md
	renamed:    docs/en/guides/restic-manual-installer-tests-v0-1-0.md -> docs/en/guides/development/restic-manual-installer-tests-v0-1-0.md
	deleted:    docs/en/guides/restic-backup-guide--plain-language-mashup-v0-1-0.md
	deleted:    docs/en/guides/restic-backup-guide--plain-language-v0-1-0.md
	deleted:    docs/en/guides/restic-backup-guide-v0-1-0.md
"
```

First push of the branch:

```bash
git push -u origin main
```

Subsequent pushes:

```bash
git push
```

## Releasing

A release is one uninterrupted sequence: bump, changelog, surgical commit, guard, tag, guard, push. Every step is a command. Do not interleave other work.

### Bump Release

Confirm current version

```bash
cat VERSION
```

Output example:

```bash
0.6.0
```

Bump the version using one of these patterns:

```bash
python3 bump-version.py 0.6.0      #    set an explicit version
python3 bump-version.py patch      #    patch bump example 0.1.0 -> 0.1.1
python3 bump-version.py minor      #    minor bump example 0.1.1 -> 0.2.0
python3 bump-version.py major      #    major bump example 0.2.0 -> 1.0.0
```

Realworld example

```bash
python3 python3 bump-version.py minor
```

Output example:

```bash
VERSION: 0.2.2 -> 0.3.0
README.md: version line -> 0.3.0
docs/en/README.md: version line -> 0.3.0

Bump only: nothing committed. For the full ceremony use --release,
or add a changelog row in docs/en/README.md and commit by hand (surgical).
```

## Automated Release (test)

```bash
python3 bump-version.py minor --release
```

output example:

```bash
bump-version.py — Bump this repository's version, optionally as a release.

Adapted from sat's bump-sat-version.py (the --release ceremony), proving the
pipeline across tools ahead of its promotion to the governance repository.

Bump only (writes files, commits nothing):
    bump-version.py patch            0.1.0 -> 0.1.1
    bump-version.py minor            0.1.1 -> 0.2.0
    bump-version.py major            0.2.0 -> 1.0.0
    bump-version.py 0.3.2            set an explicit version

Release (the full ceremony, one uninvertible command):
    bump-version.py --release patch -m "what changed"

A release performs: bump -> changelog row -> surgical commit (release files
only, never `git add .`) -> guard (HEAD:VERSION) -> annotated tag -> guard
(tag:VERSION) -> report. It stops before push; pushing stays a deliberate act:

    git push && git push origin vX.Y.Z

Refusals: a dirty VERSION or versioned doc (a half-done release is finished,
not built upon), or an existing tag for the target version (fix forward).
```

```bash
python3 bump-version.py --release minor -m "cleaned up guides and tested instructions"
```

output

```bash
[BUMP ERROR] Release files have uncommitted changes:
M README.md
 M VERSION
 M docs/en/README.md
  A half-done release is finished, not built upon.
```



Add a changelog entry in `docs/en/README.md`, then commit the release surgically. Never `git add .` here: the release commit carries `VERSION` and the changelog and nothing else, so the tag has an unambiguous target.

```bash
git status
```

output example:

```bash
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   README.md
	modified:   VERSION
	modified:   docs/en/README.md
	modified:   docs/en/guides/development/commit-and-versioning-workflow-v0-2-6.md

no changes added to commit (use "git add" and/or "git commit -a")
```

Confirm VERSIOn

```bash
cat VERSION
```

output

```bash
0.3.0
```

Add your four changes

```bash
git add VERSION README.md docs/en/README.md docs/en/guides/development/commit-and-versioning-workflow-v0-2-6.md
git commit -m "release 0.7.0"
```

Guard before tagging — the commit must contain the version the tag will claim:

```bash
git show HEAD:VERSION          # must print 0.7.0; if not, STOP — do not tag
```

Tag, guard the tag itself, then push. Tag pushes are one-time acts per version: a pushed tag is permanent. A wrong tag is never moved or reused — fix forward by releasing the next number and leaving the wrong tag stranded.

```bash
git tag -a v0.7.0 -m "version 0.7.0"
git show v0.7.0:VERSION        # must print 0.7.0; if not, delete the local tag and STOP
git push && git push origin v0.7.0
```

### Install latest version to local system

```bash
python3 install-restic.py --install 0.2.2
```

output example:

```bash
python3 install-restic.py --install 0.2.2
[RESTIC-TOOL] installing restic v0.2.2
[RESTIC-TOOL] downloading https://github.com/restic/restic/releases/download/v0.2.2/restic_0.2.2_linux_amd64.bz2
[RESTIC-TOOL ERROR] download failed for https://github.com/restic/restic/releases/download/v0.2.2/restic_0.2.2_linux_amd64.bz2: HTTP Error 404: Not Found
```

Confirm new version installed

```bash
restic version
```

### Release Verification

#### Provinance

```bash
cat ~/.local/share/restic-tool/0.19.1/PROVENANCE
```

VERSION

> Creators Note: VERSION not found

The installed artifact should reflect the new released version:

```bash
cat ~/.local/share/sat-tool/0.7.0/VERSION
```

Output example:

```bash
0.7.0
```

Any disagreement between the requested version, the artifact's `VERSION`, and the tool's report means a mislabelled release. Do not use it: remove the artifact, find the break in the release sequence above, and fix forward with the next version number.

## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.2.6 | Draft | Customized for osat-fluent-restic-tool |
| 0.2.4 | Draft | Minor edits for more detailed understanding of generated SAT files |
| 0.2.3 | Draft | Minor edits for clarity, added testing release section |
| 0.2.2 | Draft | Returned to functioning 0.2.1 version with minor updates |
| 0.2.1 | Draft | Minor changes for clarity |
| 0.2.0 | Draft | Release sequence made fully executable: surgical release commit added as a command block (previously prose only, the root cause of tags capturing pre-bump VERSION); two guards added before tag push; Committing and Releasing separated with the rule that VERSION never appears in work commits; fix-forward rule for wrong tags; verification extended to compare artifact and runtime |
| 0.1.0 | Draft | Initial draft |
