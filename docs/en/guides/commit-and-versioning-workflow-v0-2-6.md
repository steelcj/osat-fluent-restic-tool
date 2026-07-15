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
git commit -m "	modified:   README.md
	new file:   en/lib/satlib/satlib/archive.py
	new file:   en/lib/satlib/tests/test_archive.py
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
bump-sat-version.py 0.6.0      #    set an explicit version
bump-sat-version.py patch      #    patch bump example 0.1.0 -> 0.1.1
bump-sat-version.py minor      #    minor bump example 0.1.1 -> 0.2.0
bump-sat-version.py major      #    major bump example 0.2.0 -> 1.0.0
```

Realworld example

```bash
python3 bump-sat-version.py minor
```

Output example:

```bash
VERSION: 0.6.0 -> 0.7.0
README.md: sat_version -> 0.7.0

Remember to add a changelog entry in docs/en/README.md before committing.
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
```

Add your two changes

```bash
git add VERSION README.md
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
