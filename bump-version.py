#!/usr/bin/env python3
#
# source
#   project: osat-fluent-restic-tool
#   path: bump-version.py
#
"""
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
"""
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# ── Repository configuration ──────────────────────────────────────────────────
# The only section that differs between OSAT Fluent repositories.

VERSION_FILE = _HERE / "VERSION"

# Documents carrying a version field that tracks the repo version.
VERSIONED_DOCS = [
    _HERE / "README.md",
    _HERE / "docs" / "en" / "README.md",
]

# The line pattern those documents carry.
VERSION_LINE = re.compile(
    r"^(Version:\s*)(\d+\.\d+\.\d+)(\s*)$",
    re.MULTILINE,
)

# Where the changelog table lives, its heading, and the row shape.
CHANGELOG_FILE = _HERE / "docs" / "en" / "README.md"
CHANGELOG_HEADING = "## Changelog"
CHANGELOG_ROW = "| {new} | Draft | {message} |"

# ── Helpers ────────────────────────────────────────────────────────────────────

def fail(msg: str) -> None:
    print(f"[BUMP ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def git(*args: str, capture: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], cwd=_HERE,
        capture_output=capture, text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or "").strip() if capture else ""
        fail(f"git {' '.join(args)} failed" + (f": {detail}" if detail else ""))
    return (result.stdout or "").strip()


def read_current() -> str:
    try:
        text = VERSION_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        fail(f"VERSION file not found at {VERSION_FILE}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", text):
        fail(f"VERSION file does not contain a semantic version: {text!r}")
    return text


def next_version(current: str, arg: str) -> str:
    if re.fullmatch(r"\d+\.\d+\.\d+", arg):
        return arg
    major, minor, patch = (int(p) for p in current.split("."))
    if arg == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if arg == "minor":
        return f"{major}.{minor + 1}.0"
    if arg == "major":
        return f"{major + 1}.0.0"
    fail(f"Expected patch, minor, major, or an explicit x.y.z, got {arg!r}")


def check_doc(path: Path) -> None:
    """Verify a document contains exactly one matchable version field."""
    if not path.exists():
        fail(f"Versioned document not found: {path}")
    matches = VERSION_LINE.findall(path.read_text(encoding="utf-8"))
    if len(matches) != 1:
        fail(f"Expected exactly one version line in {path}, found {len(matches)}")


def write_bump(current: str, new: str) -> None:
    """The original all-or-nothing bump: validate everything, then write."""
    for doc in VERSIONED_DOCS:
        check_doc(doc)
    VERSION_FILE.write_text(new + "\n", encoding="utf-8")
    print(f"VERSION: {current} -> {new}")
    for doc in VERSIONED_DOCS:
        text = doc.read_text(encoding="utf-8")
        doc.write_text(VERSION_LINE.sub(rf"\g<1>{new}\g<3>", text, count=1),
                       encoding="utf-8")
        print(f"{doc.relative_to(_HERE)}: version line -> {new}")


# ── Release ceremony ───────────────────────────────────────────────────────────

def release_files() -> list:
    files = [VERSION_FILE, *VERSIONED_DOCS, CHANGELOG_FILE]
    seen, ordered = set(), []
    for f in files:
        if f not in seen:
            seen.add(f)
            ordered.append(f)
    return ordered


def refuse_if_dirty() -> None:
    """A release starts from clean release files. A dirty VERSION means a
    half-done release: finish it by hand, do not stack another on top."""
    dirty = git("status", "--porcelain", "--",
                *(str(f.relative_to(_HERE)) for f in release_files()))
    if dirty:
        fail("Release files have uncommitted changes:\n" + dirty +
             "\n  A half-done release is finished, not built upon.")


def refuse_if_tagged(new: str) -> None:
    if git("tag", "--list", f"v{new}"):
        fail(f"Tag v{new} already exists. Tags are never reused; fix forward "
             f"with the next version number.")


def add_changelog_row(new: str, message: str) -> None:
    text = CHANGELOG_FILE.read_text(encoding="utf-8")
    heading_at = text.find(CHANGELOG_HEADING)
    if heading_at == -1:
        fail(f"No '{CHANGELOG_HEADING}' section in {CHANGELOG_FILE}")
    # Insert the new row directly after the table's header separator line.
    separator = re.compile(r"^\|[\s:-]+\|.*$", re.MULTILINE)
    match = separator.search(text, heading_at)
    if not match:
        fail(f"No changelog table found under '{CHANGELOG_HEADING}' in {CHANGELOG_FILE}")
    row = CHANGELOG_ROW.format(new=new, message=message)
    text = text[: match.end()] + "\n" + row + text[match.end():]
    CHANGELOG_FILE.write_text(text, encoding="utf-8")
    print(f"{CHANGELOG_FILE.relative_to(_HERE)}: changelog row added")


def cmd_release(arg: str, message: str) -> int:
    refuse_if_dirty()
    current = read_current()
    new = next_version(current, arg)
    refuse_if_tagged(new)

    write_bump(current, new)
    add_changelog_row(new, message)

    paths = [str(f.relative_to(_HERE)) for f in release_files()]
    git("add", "--", *paths)
    git("commit", "-m", f"release {new}")
    print(f"committed: release {new}  (surgical: {', '.join(paths)})")

    head_version = git("show", "HEAD:VERSION")
    if head_version != new:
        fail(f"GUARD FAILED: HEAD:VERSION is {head_version!r}, expected {new!r}. "
             f"Not tagging.")
    print(f"guard: HEAD:VERSION = {new}  \u2713")

    git("tag", "-a", f"v{new}", "-m", f"version {new}")
    tag_version = git("show", f"v{new}:VERSION")
    if tag_version != new:
        git("tag", "-d", f"v{new}")
        fail(f"GUARD FAILED: v{new}:VERSION is {tag_version!r}, expected {new!r}. "
             f"Local tag deleted; nothing pushed.")
    print(f"guard: v{new}:VERSION = {new}  \u2713")

    print()
    print(f"[RELEASE] {current} -> {new} committed and tagged ({date.today().isoformat()}).")
    print("  Pushing stays a deliberate act:")
    print(f"    git push && git push origin v{new}")
    return 0


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> int:
    args = sys.argv[1:]

    if args and args[0] == "--release":
        if len(args) >= 4 and args[2] == "-m":
            return cmd_release(args[1], " ".join(args[3:]))
        if len(args) == 2:
            return cmd_release(args[1], "Release")
        print(__doc__)
        return 1

    if len(args) != 1:
        print(__doc__)
        return 1

    current = read_current()
    new = next_version(current, args[0])
    write_bump(current, new)
    print()
    print("Bump only: nothing committed. For the full ceremony use --release,")
    print("or add a changelog row in docs/en/README.md and commit by hand (surgical).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
