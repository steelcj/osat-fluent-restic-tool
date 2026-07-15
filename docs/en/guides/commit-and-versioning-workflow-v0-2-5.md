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
python3 install-sat.py --install 0.2.2
```

output example:

```bash
[SAT-TOOL] Installing SAT Tools v0.7.0
  downloading:      https://github.com/steelcj/sat/archive/refs/tags/v0.7.0.tar.gz
  artifact placed:  ~/.local/share/sat-tool/0.7.0  ✓
  version verified: artifact declares v0.7.0  ✓
  creating venv:    ~/.local/share/sat-tool/0.7.0/.venv
  installing satlib and pinned dependencies ...
  satlib import verified  ✓
  env file written: ~/.config/sat-tool/sat-tool.env  ✓
  wrapper written:  ~/.local/bin/sat  ✓
  wrapper written:  ~/.local/bin/collection  ✓

[SAT-TOOL] SAT Tools v0.7.0 installed and active.
  Verify with:  sat init --version
```

Confirm new version installed

```bash
sat init --version
```

output

```bash
sat-tools 0.7.0
```

### Release Verification

The installed artifact should reflect the new released version:

```bash
cat ~/.local/share/sat-tool/0.7.0/VERSION    # must print 0.7.0
```

Output example:

```bash
0.7.0
```

Any disagreement between the requested version, the artifact's `VERSION`, and the tool's report means a mislabelled release. Do not use it: remove the artifact, find the break in the release sequence above, and fix forward with the next version number.

## Testing new version

Remove any previous test(s)

```bash
rm -R /tmp/sat-scratch
```

Init test

```bash
sat init --language en --language fr /tmp/sat-scratch
```

Output examples:

Attempting to install over an existing test in the same location`/tmp/sat-scratch`

```bash
[SAT ERROR] REFUSED: /tmp/sat-scratch/.sat-scratch.assets/identity.yml exists. An instance is instantiated once (ADR-021); its identity is written at creation and never modified. No records were written.
```

Clean install output example:

```bash
registry:  fresh (File-Date: 2026-06-14)
INSTANTIATED: SAT instance at /tmp/sat-scratch
  en: [unresolved: dc:creator, dc:publisher, dc:rights]
  fr: [unresolved: dc:creator, dc:publisher, dc:rights]
  collections/test-collection/  seeded
registry File-Date: 2026-06-14
NOTE: <calculated> fields remain; set instance defaults in /tmp/sat-scratch/.sat-scratch.assets/sat/dc.yml
```

Notice the unresolved message:

```bash
[unresolved: dc:creator, dc:publisher, dc:rights]
```

This tells us that our development tripwire is working and that dc:creator, dc:publisher, dc:rights metadata has not been set for our project

Notice the Note:

```bash
NOTE: <calculated> fields remain; set instance defaults in /tmp/sat-scratch/.sat-scratch.assets/dc.yml
```

### Dublin Core Defaults

SAT defaults to using Dublin Core metadata and in order to make things easier an more consistent you can set these defaults for you SAT instance in this file by replacing the <calcualted> field with defaults that make sense for your sat content

```bash
nano /tmp/sat-scratch/.sat-scratch.assets/dc.yml
```

Example:

```bash
dc:creator: "Christopher Steel"
dc:publisher: "SAT – Source Archive Tools v0.7.0"
dc:rights: "CC BY-SA 4.0"
dc:description: 'This is a testing instance of SAT'
```

## Verifying the SAT out of box configuration

When you init SAT a number of files are generated in order to support your SAT instance and to make it easier to work with your content in SAT

### SAT identity and provenance

Lets take a look at the files generated to establish identity and provenance.

```bash
find /tmp/sat-scratch -name "identity.yml" -o -name "provenance.yml"
```

In a multilingual SAT, in this case English and French you will find the following identity and provenance defaults:

```bash
/tmp/sat-scratch/.sat-scratch.assets/provenance.yml
/tmp/sat-scratch/.sat-scratch.assets/identity.yml
/tmp/sat-scratch/fr/.fr.assets/provenance.yml
/tmp/sat-scratch/fr/.fr.assets/identity.yml
/tmp/sat-scratch/en/.en.assets/provenance.yml
/tmp/sat-scratch/en/.en.assets/identity.yml
```

In the expected output we see three `identity.yml`and `provenance.yml` pairs. These correspond to our SAT instance, and each language archive that we created.

### SAT instance provenance

#### .sat-scratch.assets/provenance.yml example

```bash
cat /tmp/sat-scratch/.sat-scratch.assets/provenance.yml
```

Output example:

```bash
created: '2026-07-13T15:25:53-04:00'
tool: sat-tools
tool_version: 0.7.0
registry_file_date: '2026-06-14'
```

##### Description

This file is the provenance record. Provenance means "where something came from." The identity record (`identity.yml`) says what this thing *is*; the provenance record says how it *came to exist*. SAT keeps those two questions in separate files on purpose.

SAT writes this file once, at the moment of creation, and never touches it again. It belongs to SAT, not to you. If you try to create an instance where one already exists, SAT refuses — this record is the proof that the creation already happened.

The four fields answer four small questions about that one moment in time when the SAT instance was created:

###### created

When it happened. The exact date and time the instance was instantiated, with the timezone (`-04:00` here). Think of it as the record's birth certificate date — except SAT retired the word "birth," so: the timestamp of instantiation.

###### tool

What did the creating. `sat-tools` is the name of the SAT toolset. Today there is only one tool that can instantiate, so this line looks obvious — but a record that names its maker stays honest even if other tools exist someday.

###### tool_version

Which version of the tool did it. `0.7.0` means this instance was made by SAT Tools release 0.7.0. If a bug is ever found in some version's creation code, this line tells you instantly whether this instance was made by the affected version.

###### registry_file_date

Which version of the language word list was in use. Remember the IANA registry from the language record? This was the big file of real language tags, with a `File-Date` stamp. This field records that stamp: the language tags in this instance were checked against the registry as it stood on `2026-06-14`. Languages get added to the registry over time, so knowing *which* revision did the checking is part of telling the whole truth about the creation.

Put together, the record reads as one sentence: *this instance was created at this moment, by this version of this tool, with its languages checked against this revision of the registry.* Every tier gets the same record — the instance root, each archive — and what makes the instance's record special is what it says, not what it is called. One record name, every tier, distinguished by content.

#### .sat-scratch.assets/identity.yml

```bash
cat /tmp/sat-scratch/.sat-scratch.assets/identity.yml
```

Output example:

This shows us the Universally unique identifier (UUID) generated for this SAT instance

```bash
dc:identifier: urn:uuid:3ac4921c-1ba4-4172-8a72-b9fc26cc290e
```

Expected: cat should show one line — `dc:identifier: urn:uuid:...`.

### Generated files describing our English archive

The hidden directory at `/tmp/sat-scratch/en/.en.assets/` contains the assets of our English archive which currently includes the following four files:

#### sat-scratch/en/.en.assets/dc.yml

```bash
cat /tmp/sat-scratch/en/.en.assets/dc.yml
```

Output example:

```bash
dc:title: SAT Documentation (en)
dc:creator: <calculated>
dc:publisher: <calculated>
dc:date: '2026-07-13'
dc:language: eng
dc:language_bcp47: en
dc:rights: <calculated>
dc:description: ''
```

##### Description

These three Dublin Core metadata values are currently set to the value  <calculated>.

**<calcualted>** is a built in tripwire value that that serves two purposes:

1. It creates a developers tripwire for troubleshooting our metadata cascade.
2. It reminds developers that the value <calcualted> indicates the metadata resolution has not taken place at a is used to aid in resolving our metadata cascade where content, inherits metadata values from the structure above it. In this case the English archive defaults have not been set. When set those defaults will automatically be applied to the content below this configuration by default.

###### dc:creator: <calculated>



###### dc:publisher: <calculated>



###### dc:rights: <calculated>

#### sat-scratch/en/.en.assets/identity.yml

```bash
cat /tmp/sat-scratch/en/.en.assets/identity.yml
```

Content example:

```bash
dc:identifier: urn:uuid:6a777438-19e0-492e-ac59-d803f0fb4e4a
```

##### Description

This is the English archives [Universally unique identifier](https://en.wikipedia.org/wiki/Universally_unique_identifier) (UUID). Meaning that SAT can never confuse it with another archive collection that has same name (in this case "en").

#### sat-scratch/en/.en.assets/language.yml

```bash
cat /tmp/sat-scratch/en/.en.assets/language.yml
```

Content example:

```yaml
dc:language: eng
dc:language_bcp47: en
sat:authority: external
```

##### Description

This file is the archive's language record. It answers two questions in three lines: what language does this archive hold, and who checked that the language tag is real?

SAT writes this file when the archive is created. It belongs to SAT, not to you — you never edit it by hand.

Before the three fields make sense, you need to know about two things that work together: a rulebook and a word list.

**BCP 47 is the rulebook.** It is an internet standard that says how language tags are built. `en` means English. `fr-CA` means French as used in Canada. The rulebook says what order the parts go in and what a well-formed tag looks like.

**The IANA registry is the word list.** IANA (the Internet Assigned Numbers Authority) keeps one big text file listing every real language tag part. The rulebook alone can't tell you whether `xq` is a real language — only the word list can. The file has a date stamp called `File-Date`, so you always know which version of the list you are looking at.

SAT downloads this word list, saves a copy on your computer, and checks every language tag against it. Almost everything on the internet — browsers, web pages, screen readers — uses this same rulebook and word list. SAT uses them too, instead of inventing its own, so anything SAT labels is understood everywhere. For a project where accessibility comes first, the language label was the one thing to borrow, not invent.

Now the three fields.

###### dc:language: eng

The language written the way Dublin Core expects: a three-letter code from a standard called ISO 639. `eng` is the three-letter code for English, `fra` for French. Tools outside SAT that read Dublin Core metadata look for this form, so SAT writes it for them.

###### dc:language_bcp47: en

The same language, written as a BCP 47 tag. This is the form SAT itself lives by: the archive's folder is literally named `en/`, because in SAT the folder names are the language tags.

Why write the same language twice? Because two groups of readers speak two dialects. `dc:language: eng` is for Dublin Core tools. `dc:language_bcp47: en` is for SAT's own tools and for the rest of the internet. Both are written when the archive is created, so no tool ever has to convert one into the other. One language, one fact, two spellings.

###### sat:authority: external

Who vouched for the tag. `external` means an outside authority — the IANA word list — confirmed this tag is real. SAT checked the tag against its saved copy of the list, and the archive's provenance record notes the list's `File-Date`, so you know exactly which version did the checking.

Here is the important part: **this field describes, it never forbids.** Some languages are not in IANA's list yet — a small community language, an invented language, a private vocabulary a team uses. SAT lets you create archives for those too. And if your computer is offline with no saved list, you can tell SAT to go ahead anyway. In all of those cases the archive is created just the same. The only thing that changes is what this field says: instead of `external`, it records the different basis of trust — for example, `none` when you chose to proceed without any check.

So when a tool reads this record later, the field tells it what it may assume. `external` means: this tag works everywhere the internet speaks language tags. Anything else means: check what the operator intended before assuming that.

Why does SAT work this way? Because the alternative would lock people out. If SAT refused every language the registry has not caught up with, the communities that most need their language respected would be the first ones turned away. SAT admits the language and is honest in the record about who checked it. That is the golden rule at work: include more people, and tell the truth about what was verified.

#### sat-scratch/en/.en.assets/provenance.yml

```bash
cat /tmp/sat-scratch/en/.en.assets/provenance.yml
```

Output example:

```bash
created: '2026-07-13T15:25:53-04:00'
tool: sat-tools
tool_version: 0.7.0
registry_file_date: '2026-06-14'
```

#### sat-scratch/en/.en.assets/identity.yml

## Testing ADR-022

**Unblock today (manual preseed, modeled on the shipped example):**

quick fix

```bash
mkdir -p ~/.config/sat/collection
cp ~/.local/share/sat-tool/0.7.0/en/bin/collection/examples/collection-preseed.yml.example \
   ~/.config/sat/collection/collection-preseed.yml
nano ~/.config/sat/collection/collection-preseed.yml   # fill in per its comments
```

collection-preseed.yml content

```bash
path: /home/initial/.config/sat/collection/collection-preseed.yml
```

content:

```yaml
# en/bin/collection/examples/collection-preseed.yml.example
# Example collection preseed generated by sat init.
# Copy to ~/.config/sat/collection/collection-preseed.yml and customise,
# or run collection init to generate it interactively.
# SAT Tools: https://github.com/steelcj/sat-tools

collections:
  default_parent: ~/projects/sat
```

### collection init

```bash
collection init -h
usage: collection init [-h] [--language [TAG]] [--version]

Initialise a SAT collection.

options:
  -h, --help        show this help message and exit
  --language [TAG]  Without TAG: show current language. With TAG: set language.
  --version         Show SAT Tools version and exit.

Examples:
  collection init                     interactive wizard
  collection init --language          show current language
  collection init --language en-CA    set language
  collection init --version           show version
```



```bash
collection init
```

output:

```bash
[COLLECTION] All collections in preseed are already initialised.
  Edit /home/initial/.config/sat/collection/collection-preseed.yml to add new collections.
```



(If the installed layout differs, the same example ships at `en/bin/sat/examples/collection-preseed.yml.example`.) That gets `collection init`'s wizard running and lets you test the explicit-collection path — including where the work index lands when a *real* collection exists, which feeds directly into the implicit-collection question from my last message.

```bash
#cd <your-sat-instance>/<a-collection>
cd /tmp/sat-scratch/

# two docs, en + fr, identity assigned fresh (via however the session wired assignment)
collection work join fr/<doc> --expression-of en/<doc>     # dry-run: PLAN prints, nothing written
collection work join fr/<doc> --expression-of en/<doc> --apply
cat fr/.<doc>.assets/sat/identity.yml                      # sat:work moved; sat:work_retired has {uuid, retired, by}
collection work index --rebuild
head -8 .<collection>.assets/sat/work-index.yml            # header: path line, remedy, generated_by mapping
mv fr/<doc> fr/<doc-renamed>  # plus its assets dir
collection work index --check                              # stale-path finding, nonzero exit
collection work index --rebuild && collection work index --check   # clean
```

That last triplet — break it, detect it, repair it — is the canonical/derived contract proven in your real instance, which is the whole point of the release.

One caveat to carry: if the handoff session deferred or reshaped anything (the `collection work find` title search was allowed to be cheap; suggestion machinery was explicitly deferrable), the release changelog should say what shipped versus what's still owed, so 0.7.0's claims match its contents.

Report the verification and we resume the paper trail: ADR-023 review, then vocabulary v0.4.0, then phase two — `content ingest` with cataloging — gets built on top of a verified 0.7.0.

### Clean up when testing is completed

Scratch test cleanup:

```bash
rm -rf /tmp/sat-scratch
```





## Changelog

| Version | Status | Notes |
|---------|--------|-------|
| 0.2.4 | Draft | Minor edits for more detailed understanding of generated SAT files |
| 0.2.3 | Draft | Minor edits for clarity, added testing release section |
| 0.2.2 | Draft | Returned to functioning 0.2.1 version with minor updates |
| 0.2.1 | Draft | Minor changes for clarity |
| 0.2.0 | Draft | Release sequence made fully executable: surgical release commit added as a command block (previously prose only, the root cause of tags capturing pre-bump VERSION); two guards added before tag push; Committing and Releasing separated with the rule that VERSION never appears in work commits; fix-forward rule for wrong tags; verification extended to compare artifact and runtime |
| 0.1.0 | Draft | Initial draft |
